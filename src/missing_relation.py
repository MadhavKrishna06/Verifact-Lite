"""STEP 2C - missing relation detection over the uncovered spans of STEP 2B.

For each candidate span the judges answer two questions, following the paper:
1. does the span express a PDTB level-1 relation (VERIFACT targets temporal and
   contingency)?
2. is that relation already captured by a single existing fact?
A missing relation is declared only when relation_detected AND NOT already_covered.
Judge decisions are combined with the same ensemble strategy as STEP 2A.
"""

from __future__ import annotations

import re

from .model_client import BaseClient
from . import prompts
from .utils import parse_json_loose, first_label, normalize_for_match
from .word_mapping import MissingSpan

TEMPORAL_CUES = [
    "before", "after", "later", "previously", "subsequently", "during", "while",
    "simultaneously", "then", "until", "once", "meanwhile", "afterward",
    "since", "when",
]
CONTINGENCY_CUES = [
    "because", "therefore", "so that", "so ", "due to", "if ", "unless",
    "leading to", "resulting in", "results in", "making", "causing", "cause",
    "in order to", "thus", "hence", "as a result", "allowing", "enabling",
    "which means", "consequently", "owing to", "provided that",
]


def rule_based_relation(span: str) -> str | None:
    """Deterministic cue-word signal (proposed improvement 6, opt-in)."""
    text = " " + normalize_for_match(span) + " "
    for cue in CONTINGENCY_CUES:
        if cue.strip() and cue in text:
            return "contingency"
    for cue in TEMPORAL_CUES:
        if re.search(rf"\b{re.escape(cue.strip())}\b", text):
            return "temporal"
    return None


def _coerce_relation(value: str | None) -> str:
    if not value:
        return "none"
    v = str(value).strip().lower()
    for name in ("temporal", "contingency", "comparison", "expansion"):
        if name in v:
            return name
    return "none"


class MissingRelationDetector:
    """One judge's view of one candidate span."""

    def __init__(self, judge: BaseClient, cfg: dict):
        self.judge = judge
        mr = cfg.get("missing_relation") or {}
        self.targets = [t.lower() for t in (mr.get("target_relations") or ["temporal", "contingency"])]
        self.coverage_check = bool(mr.get("coverage_check", True))
        self.rule_prefilter = bool(mr.get("rule_prefilter", False))

    def detect_relation(self, response: str, span: MissingSpan) -> dict:
        prompt = prompts.RELATION_DETECT_PROMPT.format(
            pdtb=prompts.PDTB_DEFINITION, response=response, span=span.text
        )
        raw = self.judge.chat(
            [{"role": "user", "content": prompt}], temperature=0.0, tag="relation"
        )
        parsed = parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            relation = _coerce_relation(parsed.get("relation_type"))
            flag = bool(parsed.get("is_missing_relation"))
            reason = str(parsed.get("reason", "")).strip()[:300]
            parse_ok = True
        else:
            # Recovery: look for a level-1 relation name in free text.
            label = first_label(raw or "", ["Temporal", "Contingency", "Comparison", "Expansion"])
            relation = _coerce_relation(label)
            flag = relation in self.targets
            reason = (raw or "").strip()[:300]
            parse_ok = False

        if relation not in self.targets:
            flag = False
        elif relation in self.targets:
            flag = True  # a targeted relation is present in this span
        return {
            "judge": self.judge.alias,
            "relation_type": relation,
            "is_missing_relation": flag,
            "reason": reason,
            "parse_ok": parse_ok,
        }

    def check_coverage(self, span: MissingSpan, facts: list) -> dict:
        if not self.coverage_check:
            return {"judge": self.judge.alias, "already_covered": False, "supporting_fact": None}
        fact_list = "\n".join(f"{f.id}: {f.text}" for f in facts) or "(no facts)"
        prompt = prompts.RELATION_COVERAGE_PROMPT.format(fact_list=fact_list, span=span.text)
        raw = self.judge.chat(
            [{"role": "user", "content": prompt}], temperature=0.0, tag="relation_coverage"
        )
        parsed = parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            covered = bool(parsed.get("already_covered"))
            support = parsed.get("supporting_fact")
        else:
            covered = first_label(raw or "", ["YES", "NO"]) == "YES"
            support = None
        return {
            "judge": self.judge.alias,
            "already_covered": covered,
            "supporting_fact": support if isinstance(support, str) else None,
        }

    def detect_all(
        self, response: str, spans: list[MissingSpan], facts: list
    ) -> dict[tuple, dict]:
        """Judge every candidate span with this one judge.

        The coverage check only runs for spans this judge flagged, which is both
        cheaper and what the paper's two-stage procedure describes.
        """
        out: dict[tuple, dict] = {}
        for span in spans:
            key = (span.text, span.start)
            if self.rule_prefilter and rule_based_relation(span.text) is None:
                out[key] = {
                    "judge": self.judge.alias,
                    "relation_type": "none",
                    "is_missing_relation": False,
                    "reason": "",
                    "parse_ok": True,
                    "skipped_by_rule_prefilter": True,
                    "coverage": None,
                }
                continue
            record = self.detect_relation(response, span)
            record["skipped_by_rule_prefilter"] = False
            record["coverage"] = (
                self.check_coverage(span, facts) if record["is_missing_relation"] else None
            )
            out[key] = record
        return out


class MissingRelationEnsemble:
    def __init__(self, judges: list[BaseClient], cfg: dict):
        self.detectors = [MissingRelationDetector(j, cfg) for j in judges]
        ens = cfg.get("ensemble") or {}
        self.strategy = str(ens.get("strategy", "union")).lower()
        self.threshold = float(ens.get("weighted_threshold", 0.5))
        self.weights = {j.alias: float(getattr(j, "weight", 1.0)) for j in judges}
        mr = cfg.get("missing_relation") or {}
        self.rule_prefilter = bool(mr.get("rule_prefilter", False))
        self.targets = [t.lower() for t in (mr.get("target_relations") or ["temporal", "contingency"])]

    def _combine(self, votes: dict[str, bool]) -> bool:
        if not votes:
            return False
        if self.strategy == "majority":
            return sum(1 for v in votes.values() if v) * 2 > len(votes)
        if self.strategy == "weighted":
            total = sum(self.weights.get(a, 1.0) for a in votes) or 1.0
            score = sum(self.weights.get(a, 1.0) for a, v in votes.items() if v) / total
            return score >= self.threshold
        return any(votes.values())  # union

    def collect(
        self, response: str, spans: list[MissingSpan], facts: list
    ) -> dict[str, dict]:
        """Run every judge, one judge at a time, over the whole span list."""
        return {d.judge.alias: d.detect_all(response, spans, facts) for d in self.detectors}

    def run(
        self,
        response: str,
        spans: list[MissingSpan],
        facts: list,
        per_judge: dict[str, dict] | None = None,
    ) -> list[dict]:
        if per_judge is None:
            per_judge = self.collect(response, spans, facts)

        records: list[dict] = []
        for span in spans:
            key = (span.text, span.start)
            rule_hint = rule_based_relation(span.text)
            if self.rule_prefilter and rule_hint is None:
                records.append(
                    {
                        "span": span.text,
                        "start": span.start,
                        "end": span.end,
                        "relation_type": "none",
                        "judges": {},
                        "relation_detected": False,
                        "already_covered": False,
                        "is_missing_relation": False,
                        "rule_hint": None,
                        "skipped_by_rule_prefilter": True,
                    }
                )
                continue

            rel_votes: dict[str, bool] = {}
            rel_types: dict[str, str] = {}
            coverage_records: dict[str, dict] = {}
            for alias, by_span in per_judge.items():
                result = by_span.get(key)
                if result is None:
                    continue
                rel_votes[alias] = bool(result["is_missing_relation"])
                rel_types[alias] = result["relation_type"]
                if result.get("coverage"):
                    coverage_records[alias] = result["coverage"]
            relation_detected = self._combine(rel_votes)

            relation_type = "none"
            for alias, flag in rel_votes.items():
                if flag and rel_types.get(alias) in self.targets:
                    relation_type = rel_types[alias]
                    break
            if relation_type == "none" and rule_hint and relation_detected:
                relation_type = rule_hint

            cov_votes: dict[str, bool] = {}
            support: str | None = None
            if relation_detected:
                for alias, result in coverage_records.items():
                    cov_votes[alias] = bool(result["already_covered"])
                    if result["already_covered"] and support is None:
                        support = result["supporting_fact"]
            # A span counts as covered only if the judges agree enough; use the
            # same combiner so union does not force everything to "covered".
            already_covered = self._combine(cov_votes) if cov_votes else False

            records.append(
                {
                    "span": span.text,
                    "start": span.start,
                    "end": span.end,
                    "relation_type": relation_type,
                    "judges": rel_votes,
                    "judge_relation_types": rel_types,
                    "coverage_judges": cov_votes,
                    "relation_detected": relation_detected,
                    "already_covered": already_covered,
                    "supporting_fact": support,
                    "is_missing_relation": bool(relation_detected and not already_covered),
                    "rule_hint": rule_hint,
                    "skipped_by_rule_prefilter": False,
                }
            )
        return records
