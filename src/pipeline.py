"""VERIFACT-Lite pipeline orchestration.

    Question + long-form answer
      -> STEP 1  baseline fact extraction
      -> STEP 2A incomplete fact detection          (judge ensemble)
      -> STEP 2B word mapping -> uncovered spans
      -> STEP 2C missing relation detection          (judge ensemble + coverage check)
      -> STEP 3  refinement of incomplete facts
      -> STEP 3B added relational facts
      -> STEP 4  evidence retrieval + verification
      -> precision / recall / F1

The answer under evaluation is generated exactly once per question and shared by
every variant, so baseline and VERIFACT-Lite are compared under identical
conditions. Variants:

    A  baseline                      - no refinement at all
    B  baseline + incomplete refine  - STEP 3 only
    C  baseline + missing relation   - STEP 3B only
    D  full VERIFACT-Lite            - STEP 3 and STEP 3B
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import metrics as M
from .completeness import DetectionEnsemble
from .extractor import BaselineExtractor
from .missing_relation import MissingRelationEnsemble
from .model_client import (
    BaseClient,
    build_cache,
    build_generator,
    build_primary,
    available_judges,
)
from .refinement import Refiner, assemble_final_facts
from .retrieval import build_retriever
from .verifier import FactVerifier, RecallChecker
from . import prompts
from .utils import Fact, read_jsonl, resolve_path, word_count
from .word_mapping import find_missing_spans, coverage_ratio

VARIANTS = {
    "A": {"key": "baseline", "label": "Baseline", "refine_incomplete": False, "add_relations": False},
    "B": {"key": "incomplete_only", "label": "+ Incomplete Refine", "refine_incomplete": True, "add_relations": False},
    "C": {"key": "relation_only", "label": "+ Missing Relation", "refine_incomplete": False, "add_relations": True},
    "D": {"key": "verifact", "label": "Full VERIFACT-Lite", "refine_incomplete": True, "add_relations": True},
}


@dataclass
class QuestionResult:
    question_id: str
    question: str
    answer: str
    detections: list[dict] = field(default_factory=list)
    spans: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    variants: dict = field(default_factory=dict)
    before_after: list[dict] = field(default_factory=list)
    reference_facts: list[str] = field(default_factory=list)
    coverage: list[dict] = field(default_factory=list)


class VerifactLitePipeline:
    def __init__(self, cfg: dict, verbose: bool = True):
        self.cfg = cfg
        self.verbose = verbose
        self.cache = build_cache(cfg)
        self.primary: BaseClient = build_primary(cfg, self.cache)
        self.generator: BaseClient = build_generator(cfg, self.cache)
        self.judges = available_judges(cfg, self.cache)
        if not self.judges:
            raise RuntimeError(
                "no judge model is reachable; start the backend (e.g. `ollama serve`) "
                "or adjust judges/backends in config.yaml"
            )
        self.extractor = BaselineExtractor(self.primary, cfg)
        self.completeness = DetectionEnsemble(self.judges, cfg)
        self.relations = MissingRelationEnsemble(self.judges, cfg)
        self.refiner = Refiner(self.primary, cfg)
        self.retriever = build_retriever(cfg, self.primary)
        self.verifier = FactVerifier(self.primary, self.retriever, cfg)
        self.recall_checker = RecallChecker(self.primary, cfg)
        self._verify_cache: dict[str, dict] = {}
        # With several judges on one small GPU, release each judge's weights
        # after its stages so the next model can load immediately.
        self.unload_between_judges = bool(
            (cfg.get("run") or {}).get("unload_between_judges", True)
        )
        # The judge whose labels are REPORTED as the incomplete-fact rate. The
        # paper measures that rate with a single model (GPT-4o) while refining on
        # the union of three judges; reporting the union would score the facts
        # with the very ensemble that selected them.
        configured = (cfg.get("measurement") or {}).get("incomplete_judge")
        aliases = [j.alias for j in self.judges]
        self.measurement_judge = configured if configured in aliases else aliases[0]

    # -- logging ------------------------------------------------------------
    def log(self, *parts) -> None:
        if self.verbose:
            print(*parts, flush=True)

    # -- answer generation (exactly once per question) ----------------------
    def generate_answer(self, question: str) -> str:
        gen = self.cfg.get("generation") or {}
        messages = [
            {"role": "system", "content": prompts.ANSWER_SYSTEM},
            {
                "role": "user",
                "content": prompts.ANSWER_USER.format(
                    question=question, max_words=int(gen.get("max_words", 130))
                ),
            },
        ]
        answer = self.generator.chat(
            messages,
            temperature=float(gen.get("temperature", 0.7)),
            max_tokens=int(gen.get("max_tokens", 400)),
            tag="generate",
        )
        return " ".join((answer or "").split())

    # -- re-detection of incompleteness on refined/added facts --------------
    def _recheck_incomplete(
        self, question: str, answer: str, facts: list[Fact]
    ) -> dict[str, bool]:
        """Re-run STEP 2A on facts the refinement stage produced.

        Only the measurement judge runs here, for the same reason the paper
        measures Incomplete Facts (%) with one model (GPT-4o) while refining on
        the union of three: scoring with the union that selected the facts for
        refinement would not be an independent measurement. Calls go through the
        LLM cache, so variants sharing a refined fact pay for it once.
        """
        detector = self._measurement_detector()
        by_fact = detector.detect_all(question, answer, facts)
        return {fid: bool(rec["is_incomplete"]) for fid, rec in by_fact.items()}

    def _measurement_detector(self):
        """The single judge used to report incompleteness, not to drive refinement."""
        alias = self.measurement_judge
        for detector in self.completeness.detectors:
            if detector.judge.alias == alias:
                return detector
        return self.completeness.detectors[0]

    # -- verification with per-run memoisation ------------------------------
    def verify_claim(self, claim: str) -> dict:
        if claim not in self._verify_cache:
            self._verify_cache[claim] = self.verifier.verify(claim)
        return self._verify_cache[claim]

    # -- one question -------------------------------------------------------
    def run_question(
        self,
        question_id: str,
        question: str,
        answer: str,
        reference_facts: list[str] | None = None,
        variant_keys: tuple[str, ...] = ("A", "D"),
    ) -> QuestionResult:
        result = QuestionResult(
            question_id=question_id,
            question=question,
            answer=answer,
            reference_facts=list(reference_facts or []),
        )

        # STEP 1 -----------------------------------------------------------
        facts, grouped = self.extractor.extract(question, answer)
        self.log(f"  STEP 1: {len(facts)} baseline facts")

        # STEP 2B ----------------------------------------------------------
        # Word mapping needs no model, so it runs before the judges and lets
        # each judge handle both detection stages in a single residency.
        wm = self.cfg.get("word_mapping") or {}
        spans = find_missing_spans(
            answer,
            [f.text for f in facts],
            sentence_facts=grouped,
            min_chars=int(wm.get("min_span_chars", 12)),
            min_words=int(wm.get("min_span_words", 3)),
        )
        result.spans = [s.to_dict() for s in spans]
        self.log(
            f"  STEP 2B: {len(spans)} uncovered spans "
            f"(coverage {coverage_ratio(answer, [f.text for f in facts]):.2f})"
        )

        # STEP 2A + 2C -----------------------------------------------------
        # One judge at a time, both stages, so a backend that keeps a single
        # model resident swaps once per judge instead of once per call.
        per_judge_completeness: dict[str, dict] = {}
        per_judge_relations: dict[str, dict] = {}
        for detector, rel_detector in zip(
            self.completeness.detectors, self.relations.detectors
        ):
            alias = detector.judge.alias
            per_judge_completeness[alias] = detector.detect_all(question, answer, facts)
            per_judge_relations[alias] = rel_detector.detect_all(answer, spans, facts)
            self.log(f"  judge {alias}: {detector.judge.calls} calls so far")
            if self.unload_between_judges and len(self.judges) > 1:
                detector.judge.unload()

        detections = self.completeness.run(
            question, answer, facts, per_judge=per_judge_completeness
        )
        result.detections = detections
        n_incomplete = sum(1 for d in detections if d["ensemble"])
        measured = per_judge_completeness.get(self.measurement_judge, {})
        baseline_measured = {
            fid: bool(rec["is_incomplete"]) for fid, rec in measured.items()
        }
        n_measured = sum(1 for v in baseline_measured.values() if v)
        self.log(
            f"  STEP 2A: {n_incomplete} incomplete facts flagged for refinement "
            f"(ensemble: {self.completeness.strategy}); {n_measured} measured as "
            f"incomplete by judge '{self.measurement_judge}'"
        )

        relation_records = self.relations.run(
            answer, spans, facts, per_judge=per_judge_relations
        )
        result.relations = relation_records
        missing = [r for r in relation_records if r["is_missing_relation"]]
        self.log(f"  STEP 2C: {len(missing)} missing relations")

        # STEP 3 / 3B + STEP 4 per variant ---------------------------------
        refinements_cache: list[dict] | None = None
        added_cache: list[dict] | None = None

        for vkey in variant_keys:
            spec = VARIANTS[vkey]
            refinements: list[dict] = []
            added: list[dict] = []

            if spec["refine_incomplete"]:
                if refinements_cache is None:
                    refinements_cache = [
                        self.refiner.refine_fact(question, answer, f) for f in facts if f.incomplete
                    ]
                refinements = refinements_cache

            if spec["add_relations"]:
                if added_cache is None:
                    added_cache = []
                    for i, record in enumerate(missing, start=1):
                        new_fact = self.refiner.add_relation_fact(
                            question, answer, record, facts, f"M{i}"
                        )
                        if new_fact:
                            added_cache.append(new_fact)
                added = added_cache

            final_facts = assemble_final_facts(facts, refinements, added)
            self.log(
                f"  variant {vkey} ({spec['label']}): {len(final_facts)} final facts "
                f"[{sum(1 for f in final_facts if f.status == 'refined')} refined, "
                f"{sum(1 for f in final_facts if f.status == 'added')} added]"
            )

            # STEP 4: verification
            verifications = []
            for fact in final_facts:
                v = self.verify_claim(fact.text)
                verifications.append(
                    {
                        "fact_id": fact.id,
                        "status": fact.status,
                        "claim": fact.text,
                        "original": fact.original_text,
                        "label": v["label"],
                        "confidence": v["confidence"],
                        "evidence_ids": v["evidence_ids"],
                        "reason": v["reason"],
                        "queries": v["queries"],
                        "evidence": v["evidence"],
                    }
                )

            # recall against the mini reference benchmark
            coverage = [self.recall_checker.check(rf, answer) for rf in result.reference_facts]
            if not result.coverage:
                result.coverage = coverage

            fact_dicts = [f.to_dict() for f in final_facts]
            ext = M.extraction_stats(fact_dicts, relation_records)
            if not spec["add_relations"]:
                # Variants without STEP 3B leave every detected relation missing.
                ext["missing_relations"] = len(missing)
            else:
                ext["missing_relations"] = max(0, len(missing) - len(added))
            # The incomplete rate of a variant is measured on that variant's own
            # output facts, as the paper does: facts the refinement stage did not
            # touch keep their STEP 2A label, and every fact it produced is sent
            # back through the judges rather than assumed to be fixed.
            recheck = [f for f in final_facts if f.status in ("refined", "added")]
            rechecked = self._recheck_incomplete(question, answer, recheck) if recheck else {}
            still = 0
            for fact in final_facts:
                if fact.status in ("refined", "added"):
                    flagged = rechecked.get(fact.id, False)
                else:
                    flagged = baseline_measured.get(fact.id, fact.incomplete)
                if flagged:
                    still += 1
                for entry in fact_dicts:
                    if entry["id"] == fact.id:
                        entry["incomplete_after_refinement"] = bool(flagged)
            ext["incomplete_facts"] = still
            ext["incomplete_rate"] = still / len(final_facts) if final_facts else 0.0

            labels = [v["label"] for v in verifications]
            prec = M.precision_from_labels(labels)
            cov_flags = [c["covered"] for c in coverage]
            rec = M.recall_from_coverage(cov_flags)

            result.variants[vkey] = {
                "variant": vkey,
                "key": spec["key"],
                "label": spec["label"],
                "facts": fact_dicts,
                "refinements": refinements,
                "added": added,
                "verifications": verifications,
                "coverage": coverage,
                "labels": labels,
                "coverage_flags": cov_flags,
                **ext,
                **prec,
                **rec,
                "f1": M.f1(prec["precision"], rec["recall"]),
            }

        # before/after verification of refined facts (section 28) ----------
        if refinements_cache:
            for record in refinements_cache:
                if record["status"] != "refined":
                    continue
                before = self.verify_claim(record["original"])
                after = self.verify_claim(record["refined"])
                result.before_after.append(
                    {
                        "fact_id": record["fact_id"],
                        "original": record["original"],
                        "refined": record["refined"],
                        "error_type": record["error_type"],
                        "before": before["label"],
                        "after": after["label"],
                        "before_reason": before["reason"],
                        "after_reason": after["reason"],
                    }
                )

        return result

    # -- dataset ------------------------------------------------------------
    def load_dataset(self) -> list[dict]:
        paths = self.cfg.get("paths") or {}
        questions = read_jsonl(resolve_path(self.cfg, paths["challenge_set"]))
        refs = {}
        ref_path = resolve_path(self.cfg, paths["mini_reference"])
        if ref_path.exists():
            for row in read_jsonl(ref_path):
                refs[row["id"]] = row.get("reference_facts", [])
        limit = (self.cfg.get("run") or {}).get("limit")
        if limit:
            questions = questions[: int(limit)]
        for row in questions:
            row["reference_facts"] = refs.get(row["id"], [])
        return questions

    def run_dataset(
        self,
        variant_keys: tuple[str, ...] = ("A", "D"),
        answers: dict[str, str] | None = None,
    ) -> tuple[list[QuestionResult], dict[str, str]]:
        """Run the pipeline over the challenge set.

        ``answers`` lets a caller reuse answers generated by an earlier run, which
        guarantees baseline and VERIFACT-Lite see byte-identical answers.
        """
        dataset = self.load_dataset()
        answers = dict(answers or {})
        results: list[QuestionResult] = []

        for i, row in enumerate(dataset, start=1):
            qid = row["id"]
            question = row["question"]
            if qid not in answers:
                answers[qid] = self.generate_answer(question)
            answer = answers[qid]
            self.log(f"[{i}/{len(dataset)}] {qid}: {question}")
            self.log(f"  answer ({word_count(answer)} words): {answer[:160]}...")
            results.append(
                self.run_question(
                    qid, question, answer, row.get("reference_facts"), variant_keys
                )
            )
        return results, answers

    # -- reporting ----------------------------------------------------------
    def summarise(self, results: list[QuestionResult], vkey: str) -> dict:
        return M.aggregate([r.variants[vkey] for r in results if vkey in r.variants])

    def stats(self) -> dict:
        return {
            "primary": self.primary.stats(),
            "generator": self.generator.stats(),
            "judges": [j.stats() for j in self.judges],
            "cache": self.cache.stats(),
            "retrieval": self.retriever.stats(),
        }


def result_to_dict(result: QuestionResult) -> dict:
    return {
        "question_id": result.question_id,
        "question": result.question,
        "answer": result.answer,
        "reference_facts": result.reference_facts,
        "detections": result.detections,
        "spans": result.spans,
        "relations": result.relations,
        "coverage": result.coverage,
        "before_after": result.before_after,
        "variants": result.variants,
    }
