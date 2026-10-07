"""STEP 2A + 2C ensemble - incomplete fact detection across local judges.

Detection and refinement stay strictly separate: this module only labels facts,
it never rewrites them. Judge-level decisions are stored so the single-judge vs
ensemble ablation can be run afterwards from the saved results.
"""

from __future__ import annotations

from .model_client import BaseClient
from . import prompts
from .utils import Fact, parse_json_loose, first_label

VALID_TYPES = set(prompts.INCOMPLETE_TYPES)


def _coerce_type(value: str | None) -> str:
    """Map a judge's free-form type string onto the paper's four subtypes."""
    if not value:
        return "other"
    v = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if v in VALID_TYPES:
        return v
    if "ambig" in v or "pronoun" in v or "concept" in v:
        return "ambiguous_concept_or_pronoun"
    if "compar" in v:
        return "missing_comparison"
    if "condition" in v or "source" in v or "temporal" in v or "hypothetic" in v:
        return "omitted_condition_or_source"
    if v in {"none", "null", "independent"}:
        return "none"
    return "other"


class CompletenessDetector:
    """Runs one judge's STEP 2A classification over a fact list."""

    def __init__(self, judge: BaseClient):
        self.judge = judge

    def detect(self, question: str, answer: str, fact: Fact) -> dict:
        prompt = prompts.COMPLETENESS_PROMPT.format(
            question=question, context=answer, claim=fact.text
        )
        raw = self.judge.chat(
            [{"role": "user", "content": prompt}], temperature=0.0, tag="completeness"
        )
        parsed = parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if not isinstance(parsed, dict):
            # Recovery: fall back to the DEPENDENT/INDEPENDENT keyword, as the
            # official repo's line-based parser does.
            label = first_label(raw or "", ["INDEPENDENT", "DEPENDENT"])
            is_incomplete = label == "DEPENDENT"
            return {
                "fact_id": fact.id,
                "is_incomplete": is_incomplete,
                "type": "other" if is_incomplete else "none",
                "reason": (raw or "").strip()[:300],
                "parse_ok": False,
                "judge": self.judge.alias,
            }

        is_incomplete = bool(parsed.get("is_incomplete"))
        itype = _coerce_type(parsed.get("type"))
        if is_incomplete and itype == "none":
            itype = "other"
        if not is_incomplete:
            itype = "none"
        return {
            "fact_id": fact.id,
            "is_incomplete": is_incomplete,
            "type": itype,
            "reason": str(parsed.get("reason", "")).strip()[:300],
            "parse_ok": True,
            "judge": self.judge.alias,
        }

    def detect_all(self, question: str, answer: str, facts: list[Fact]) -> dict[str, dict]:
        """Label every fact with this one judge.

        Judges are driven one at a time over the whole fact list rather than
        alternating per fact. With a local backend that keeps a single model
        resident, alternating would force a model swap on every call.
        """
        return {f.id: self.detect(question, answer, f) for f in facts}


# ---------------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------------
class DetectionEnsemble:
    """Combines per-judge detections.

    ``union`` reproduces the paper: any positive detection makes the fact
    incomplete, prioritising recall. ``majority`` and ``weighted`` are the
    alternative strategies discussed as future work; all three are selectable
    from config.yaml so they can be compared.
    """

    def __init__(self, judges: list[BaseClient], cfg: dict):
        self.detectors = [CompletenessDetector(j) for j in judges]
        ens = cfg.get("ensemble") or {}
        self.strategy = str(ens.get("strategy", "union")).lower()
        self.threshold = float(ens.get("weighted_threshold", 0.5))
        self.weights = {j.alias: float(getattr(j, "weight", 1.0)) for j in judges}

    @property
    def judge_aliases(self) -> list[str]:
        return [d.judge.alias for d in self.detectors]

    def combine(self, votes: dict[str, bool]) -> bool:
        if not votes:
            return False
        if self.strategy == "majority":
            return sum(1 for v in votes.values() if v) * 2 > len(votes)
        if self.strategy == "weighted":
            total = sum(self.weights.get(a, 1.0) for a in votes) or 1.0
            score = sum(self.weights.get(a, 1.0) for a, v in votes.items() if v) / total
            return score >= self.threshold
        return any(votes.values())  # union (paper default)

    def collect(self, question: str, answer: str, facts: list[Fact]) -> dict[str, dict]:
        """Run every judge, one judge at a time, over the whole fact list."""
        return {
            d.judge.alias: d.detect_all(question, answer, facts) for d in self.detectors
        }

    def run(
        self,
        question: str,
        answer: str,
        facts: list[Fact],
        per_judge: dict[str, dict] | None = None,
    ) -> list[dict]:
        """Annotate each fact in place and return the per-fact detection record.

        ``per_judge`` accepts results already collected by ``collect`` (or by the
        pipeline, which interleaves the two detection stages per judge to keep
        model swaps to a minimum).
        """
        if per_judge is None:
            per_judge = self.collect(question, answer, facts)

        records: list[dict] = []
        for fact in facts:
            votes: dict[str, bool] = {}
            details: dict[str, dict] = {}
            for alias, by_fact in per_judge.items():
                result = by_fact.get(fact.id)
                if result is None:
                    continue
                votes[alias] = bool(result["is_incomplete"])
                details[alias] = result

            ensemble_flag = self.combine(votes)
            chosen = None
            for alias, result in details.items():
                if result["is_incomplete"]:
                    chosen = result
                    break
            fact.incomplete = ensemble_flag
            fact.incomplete_type = (chosen or {}).get("type", "none") if ensemble_flag else ""
            fact.incomplete_reason = (chosen or {}).get("reason", "") if ensemble_flag else ""
            fact.judge_votes = votes
            fact.ensemble = ensemble_flag
            records.append(
                {
                    "fact_id": fact.id,
                    "fact": fact.text,
                    "judges": votes,
                    "ensemble": ensemble_flag,
                    "type": fact.incomplete_type,
                    "reason": fact.incomplete_reason,
                    "details": details,
                }
            )
        return records
