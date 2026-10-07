"""Tests for precision / recall / F1 and the derived statistics."""

import pytest

from src.metrics import (
    aggregate,
    extraction_stats,
    f1,
    improvement,
    judge_ablation,
    label_change_stats,
    precision_from_labels,
    recall_from_coverage,
)


def test_precision_known_value():
    labels = ["SUPPORTED"] * 6 + ["CONTRADICTED"] * 2 + ["UNDECIDED"] * 2
    stats = precision_from_labels(labels)
    assert stats["total"] == 10
    assert stats["precision"] == pytest.approx(0.6)
    assert stats["decided_precision"] == pytest.approx(0.75)
    assert stats["undecided"] == 2


def test_undecided_is_never_counted_as_support():
    stats = precision_from_labels(["UNDECIDED"] * 4)
    assert stats["precision"] == 0.0
    assert stats["decided_precision"] == 0.0


def test_precision_empty_is_zero_not_error():
    stats = precision_from_labels([])
    assert stats["precision"] == 0.0 and stats["total"] == 0


def test_recall_known_value():
    stats = recall_from_coverage([True, True, False, False, True])
    assert stats["recall"] == pytest.approx(0.6)
    assert stats["covered_reference_facts"] == 3


def test_f1_known_values():
    assert f1(0.6, 0.6) == pytest.approx(0.6)
    assert f1(1.0, 0.5) == pytest.approx(2 / 3)
    assert f1(0.0, 0.9) == 0.0
    assert f1(0.0, 0.0) == 0.0


def test_f1_matches_manual_formula():
    p, r = 0.8333, 0.5242
    assert f1(p, r) == pytest.approx(2 * p * r / (p + r))


def test_extraction_stats_counts_statuses():
    facts = [
        {"incomplete": True, "incomplete_type": "omitted_condition_or_source", "status": "refined"},
        {"incomplete": False, "incomplete_type": "", "status": "unchanged"},
        {"incomplete": True, "incomplete_type": "missing_comparison", "status": "refined"},
        {"incomplete": False, "incomplete_type": "", "status": "added"},
    ]
    relations = [
        {"is_missing_relation": True, "relation_type": "contingency"},
        {"is_missing_relation": False, "relation_type": "none"},
    ]
    stats = extraction_stats(facts, relations)
    assert stats["num_facts"] == 4
    assert stats["incomplete_facts"] == 2
    assert stats["incomplete_rate"] == pytest.approx(0.5)
    assert stats["refined_facts"] == 2
    assert stats["added_facts"] == 1
    assert stats["missing_relations"] == 1
    assert stats["incomplete_types"]["missing_comparison"] == 1


def test_aggregate_macro_averages_and_pools_labels():
    per_question = [
        {
            "num_facts": 4,
            "incomplete_facts": 2,
            "missing_relations": 1,
            "refined_facts": 2,
            "added_facts": 0,
            "candidate_spans": 3,
            "labels": ["SUPPORTED", "SUPPORTED", "UNDECIDED", "CONTRADICTED"],
            "coverage_flags": [True, False],
            "precision": 0.5,
            "recall": 0.5,
        },
        {
            "num_facts": 2,
            "incomplete_facts": 0,
            "missing_relations": 0,
            "refined_facts": 0,
            "added_facts": 1,
            "candidate_spans": 1,
            "labels": ["SUPPORTED", "SUPPORTED"],
            "coverage_flags": [True, True],
            "precision": 1.0,
            "recall": 1.0,
        },
    ]
    agg = aggregate(per_question)
    assert agg["questions"] == 2
    assert agg["avg_facts"] == pytest.approx(3.0)
    assert agg["precision"] == pytest.approx(0.75)
    assert agg["recall"] == pytest.approx(0.75)
    assert agg["f1"] == pytest.approx(0.75)
    assert agg["supported"] == 4
    assert agg["incomplete_rate"] == pytest.approx(2 / 6)
    assert agg["pooled_recall"] == pytest.approx(0.75)


def test_label_change_stats():
    pairs = [
        {"before": "SUPPORTED", "after": "CONTRADICTED"},
        {"before": "SUPPORTED", "after": "SUPPORTED"},
        {"before": "UNDECIDED", "after": "SUPPORTED"},
        {"before": "SUPPORTED", "after": "UNDECIDED"},
    ]
    stats = label_change_stats(pairs)
    assert stats["label_changes"] == 3
    assert stats["label_change_rate"] == pytest.approx(0.75)
    assert stats["transitions"]["SUPPORTED->CONTRADICTED"] == 1
    assert stats["before"]["supported"] == 3
    assert stats["after"]["supported"] == 2


def test_improvement_percentages():
    baseline = {"incomplete_rate": 0.4, "missing_relations": 10, "precision": 0.5, "recall": 0.4, "f1": 0.444}
    verifact = {"incomplete_rate": 0.1, "missing_relations": 4, "precision": 0.6, "recall": 0.5, "f1": 0.545}
    imp = improvement(baseline, verifact)
    assert imp["incomplete_fact_reduction_pct"] == pytest.approx(75.0)
    assert imp["missing_relation_reduction_pct"] == pytest.approx(60.0)
    assert imp["precision_change"] == pytest.approx(0.1)
    assert imp["f1_change"] == pytest.approx(0.101, abs=1e-3)


def test_improvement_handles_zero_baseline():
    imp = improvement({"incomplete_rate": 0.0, "missing_relations": 0}, {"incomplete_rate": 0.0, "missing_relations": 0})
    assert imp["incomplete_fact_reduction_pct"] == 0.0
    assert imp["missing_relation_reduction_pct"] == 0.0


def test_judge_ablation_union_recall():
    detections = [
        {"fact_id": "F1", "judges": {"qwen": True, "llama": False}, "ensemble": True},
        {"fact_id": "F2", "judges": {"qwen": False, "llama": True}, "ensemble": True},
        {"fact_id": "F3", "judges": {"qwen": False, "llama": False}, "ensemble": False},
    ]
    relations = [
        {
            "span": "making it cheaper",
            "start": 10,
            "judges": {"qwen": True, "llama": True},
            "already_covered": False,
            "is_missing_relation": True,
        }
    ]
    out = judge_ablation(detections, relations, ["qwen", "llama"])
    assert out["qwen"]["incomplete_detected"] == 1
    assert out["qwen"]["incomplete_recall_vs_ensemble"] == pytest.approx(0.5)
    assert out["llama"]["incomplete_recall_vs_ensemble"] == pytest.approx(0.5)
    assert out["ensemble"]["incomplete_detected"] == 2
    assert out["ensemble"]["problem_detection_recall"] == 1.0
    # Each single judge misses one incomplete fact the union catches.
    assert out["qwen"]["problem_detection_recall"] < 1.0
