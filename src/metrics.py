"""Metrics: precision, recall, F1, extraction statistics and label-change rates.

Precision follows the paper (Eq. 1): the share of extracted facts verified as
supported. UNDECIDED is kept separate and is never counted as support;
``decided_precision`` reports the alternative denominator explicitly.
"""

from __future__ import annotations

from collections import Counter


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------
def precision_from_labels(labels: list[str]) -> dict:
    counts = Counter(l.upper() for l in labels)
    supported = counts.get("SUPPORTED", 0)
    contradicted = counts.get("CONTRADICTED", 0)
    undecided = counts.get("UNDECIDED", 0)
    total = supported + contradicted + undecided
    decided = supported + contradicted
    return {
        "supported": supported,
        "contradicted": contradicted,
        "undecided": undecided,
        "total": total,
        "precision": supported / total if total else 0.0,
        "decided_precision": supported / decided if decided else 0.0,
    }


def recall_from_coverage(flags: list[bool]) -> dict:
    total = len(flags)
    covered = sum(1 for f in flags if f)
    return {
        "reference_facts": total,
        "covered_reference_facts": covered,
        "recall": covered / total if total else 0.0,
    }


def f1(precision: float, recall: float) -> float:
    if precision + recall <= 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Extraction statistics
# ---------------------------------------------------------------------------
def extraction_stats(facts: list[dict], relations: list[dict]) -> dict:
    total = len(facts)
    incomplete = sum(1 for f in facts if f.get("incomplete"))
    refined = sum(1 for f in facts if f.get("status") == "refined")
    added = sum(1 for f in facts if f.get("status") == "added")
    missing = sum(1 for r in relations if r.get("is_missing_relation"))
    types = Counter(
        f.get("incomplete_type") for f in facts if f.get("incomplete") and f.get("incomplete_type")
    )
    rel_types = Counter(
        r.get("relation_type") for r in relations if r.get("is_missing_relation")
    )
    return {
        "num_facts": total,
        "incomplete_facts": incomplete,
        "incomplete_rate": incomplete / total if total else 0.0,
        "candidate_spans": len(relations),
        "missing_relations": missing,
        "refined_facts": refined,
        "added_facts": added,
        "incomplete_types": dict(types),
        "missing_relation_types": dict(rel_types),
    }


def aggregate(per_question: list[dict]) -> dict:
    """Average per-question metrics the way the paper reports them (macro)."""
    if not per_question:
        return {}

    def mean(key: str, default: float = 0.0) -> float:
        vals = [q.get(key, default) for q in per_question if q.get(key) is not None]
        return sum(vals) / len(vals) if vals else default

    def total(key: str) -> int:
        return sum(int(q.get(key, 0) or 0) for q in per_question)

    labels: list[str] = []
    for q in per_question:
        labels.extend(q.get("labels", []))
    pooled = precision_from_labels(labels)

    coverage: list[bool] = []
    for q in per_question:
        coverage.extend(q.get("coverage_flags", []))
    pooled_recall = recall_from_coverage(coverage)

    macro_precision = mean("precision")
    macro_recall = mean("recall")

    return {
        "questions": len(per_question),
        "avg_facts": mean("num_facts"),
        "incomplete_facts": total("incomplete_facts"),
        "incomplete_rate": (
            total("incomplete_facts") / total("num_facts") if total("num_facts") else 0.0
        ),
        "missing_relations": total("missing_relations"),
        "avg_missing_relations": mean("missing_relations"),
        "candidate_spans": total("candidate_spans"),
        "refined_facts": total("refined_facts"),
        "added_facts": total("added_facts"),
        "supported": pooled["supported"],
        "contradicted": pooled["contradicted"],
        "undecided": pooled["undecided"],
        "precision": macro_precision,
        "decided_precision": pooled["decided_precision"],
        "pooled_precision": pooled["precision"],
        "recall": macro_recall,
        "pooled_recall": pooled_recall["recall"],
        "reference_facts": pooled_recall["reference_facts"],
        "covered_reference_facts": pooled_recall["covered_reference_facts"],
        "f1": f1(macro_precision, macro_recall),
    }


# ---------------------------------------------------------------------------
# Before/after verification (section 28 of the brief; paper section 6.4)
# ---------------------------------------------------------------------------
def label_change_stats(pairs: list[dict]) -> dict:
    """``pairs`` entries need ``before`` and ``after`` label keys."""
    transitions = Counter()
    changed = 0
    for pair in pairs:
        before = str(pair.get("before", "")).upper()
        after = str(pair.get("after", "")).upper()
        transitions[f"{before}->{after}"] += 1
        if before != after:
            changed += 1
    total = len(pairs)
    return {
        "refined_facts_verified": total,
        "label_changes": changed,
        "label_change_rate": changed / total if total else 0.0,
        "transitions": dict(transitions),
        "before": precision_from_labels([p.get("before", "") for p in pairs]),
        "after": precision_from_labels([p.get("after", "") for p in pairs]),
    }


# ---------------------------------------------------------------------------
# Improvement deltas (section 25 of the brief)
# ---------------------------------------------------------------------------
def improvement(baseline: dict, verifact: dict) -> dict:
    def delta(key: str) -> float:
        return float(verifact.get(key, 0.0) or 0.0) - float(baseline.get(key, 0.0) or 0.0)

    base_rate = float(baseline.get("incomplete_rate", 0.0) or 0.0)
    new_rate = float(verifact.get("incomplete_rate", 0.0) or 0.0)
    base_missing = float(baseline.get("missing_relations", 0.0) or 0.0)
    new_missing = float(verifact.get("missing_relations", 0.0) or 0.0)
    return {
        "incomplete_rate_baseline": base_rate,
        "incomplete_rate_verifact": new_rate,
        "incomplete_fact_reduction_pct": (
            100.0 * (base_rate - new_rate) / base_rate if base_rate else 0.0
        ),
        "missing_relations_baseline": base_missing,
        "missing_relations_verifact": new_missing,
        "missing_relation_reduction_pct": (
            100.0 * (base_missing - new_missing) / base_missing if base_missing else 0.0
        ),
        "precision_change": delta("precision"),
        "recall_change": delta("recall"),
        "f1_change": delta("f1"),
        "undecided_change": delta("undecided"),
    }


# ---------------------------------------------------------------------------
# Judge ablation (section 27 of the brief)
# ---------------------------------------------------------------------------
def judge_ablation(detections: list[dict], relations: list[dict], aliases: list[str]) -> dict:
    """Compare each single judge against the ensemble on the same inputs.

    The ensemble union is the reference set of positives (the paper's recall-first
    choice), so per-judge "recall" is the share of ensemble positives that judge
    found, and "precision" is the share of that judge's positives the ensemble kept.
    """
    out: dict[str, dict] = {}
    ens_incomplete = {d["fact_id"] for d in detections if d.get("ensemble")}
    ens_relation = {
        (r.get("span"), r.get("start")) for r in relations if r.get("is_missing_relation")
    }

    for alias in aliases:
        judge_incomplete = {
            d["fact_id"] for d in detections if (d.get("judges") or {}).get(alias)
        }
        judge_relation = {
            (r.get("span"), r.get("start"))
            for r in relations
            if (r.get("judges") or {}).get(alias) and not r.get("already_covered")
        }
        inc_hit = len(judge_incomplete & ens_incomplete)
        rel_hit = len(judge_relation & ens_relation)
        problems_judge = judge_incomplete | judge_relation
        problems_ens = ens_incomplete | ens_relation
        out[alias] = {
            "incomplete_detected": len(judge_incomplete),
            "incomplete_recall_vs_ensemble": (
                inc_hit / len(ens_incomplete) if ens_incomplete else 0.0
            ),
            "missing_relation_detected": len(judge_relation),
            "missing_relation_recall_vs_ensemble": (
                rel_hit / len(ens_relation) if ens_relation else 0.0
            ),
            "problem_detection_recall": (
                len(problems_judge & problems_ens) / len(problems_ens) if problems_ens else 0.0
            ),
            "precision_vs_ensemble": (
                len(problems_judge & problems_ens) / len(problems_judge) if problems_judge else 0.0
            ),
        }

    out["ensemble"] = {
        "incomplete_detected": len(ens_incomplete),
        "incomplete_recall_vs_ensemble": 1.0 if ens_incomplete else 0.0,
        "missing_relation_detected": len(ens_relation),
        "missing_relation_recall_vs_ensemble": 1.0 if ens_relation else 0.0,
        "problem_detection_recall": 1.0 if (ens_incomplete or ens_relation) else 0.0,
        "precision_vs_ensemble": 1.0 if (ens_incomplete or ens_relation) else 0.0,
    }
    return out
