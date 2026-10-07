"""Offline tests of the detection / refinement / assembly logic.

A scripted fake client stands in for the local LLM, so these tests need no model
server and no network.
"""

import json

import pytest

from src.completeness import DetectionEnsemble, _coerce_type
from src.missing_relation import MissingRelationEnsemble, rule_based_relation
from src.model_client import BaseClient, CallCache
from src.refinement import Refiner, assemble_final_facts, deduplicate
from src.retrieval import bm25_scores, tfidf_scores
from src.utils import Fact
from src.word_mapping import MissingSpan


class FakeClient(BaseClient):
    """Returns canned output based on the tag of the call."""

    def __init__(self, alias, responses, cache=None):
        super().__init__(
            {"alias": alias, "name": alias, "model_id": f"fake-{alias}", "backend": "fake"},
            cache or CallCache("", enabled=False),
        )
        self.responses = responses
        self.seen = []

    def chat(self, messages, temperature=None, max_tokens=None, tag=""):
        self.seen.append((tag, messages[-1]["content"][:60]))
        value = self.responses.get(tag, "")
        return value(messages) if callable(value) else value


BASE_CFG = {
    "ensemble": {"strategy": "union", "weighted_threshold": 0.5},
    "missing_relation": {
        "target_relations": ["temporal", "contingency"],
        "coverage_check": True,
        "rule_prefilter": False,
    },
}


def incomplete_json(flag, itype="omitted_condition_or_source"):
    return json.dumps(
        {"is_incomplete": flag, "type": itype if flag else "none", "reason": "test"}
    )


# ---------------------------------------------------------------------------
# STEP 2A ensemble
# ---------------------------------------------------------------------------
def test_union_ensemble_takes_any_positive_detection():
    facts = [Fact(id="F1", text="The price of gold could drop by 20-50%.")]
    judge_a = FakeClient("qwen", {"completeness": incomplete_json(True)})
    judge_b = FakeClient("llama", {"completeness": incomplete_json(False)})
    records = DetectionEnsemble([judge_a, judge_b], BASE_CFG).run("q", "answer", facts)
    assert records[0]["judges"] == {"qwen": True, "llama": False}
    assert records[0]["ensemble"] is True
    assert facts[0].incomplete is True
    assert facts[0].incomplete_type == "omitted_condition_or_source"


def test_majority_ensemble_needs_more_than_half():
    facts = [Fact(id="F1", text="Processor A is faster.")]
    cfg = {"ensemble": {"strategy": "majority"}}
    judges = [
        FakeClient("a", {"completeness": incomplete_json(True)}),
        FakeClient("b", {"completeness": incomplete_json(False)}),
    ]
    assert DetectionEnsemble(judges, cfg).run("q", "a", facts)[0]["ensemble"] is False


def test_weighted_ensemble_uses_judge_weights():
    facts = [Fact(id="F1", text="They reduced costs.")]
    cfg = {"ensemble": {"strategy": "weighted", "weighted_threshold": 0.5}}
    heavy = FakeClient("heavy", {"completeness": incomplete_json(True)})
    heavy.weight = 0.7
    light = FakeClient("light", {"completeness": incomplete_json(False)})
    light.weight = 0.3
    assert DetectionEnsemble([heavy, light], cfg).run("q", "a", facts)[0]["ensemble"] is True


def test_detection_recovers_from_malformed_output():
    facts = [Fact(id="F1", text="They reduced costs.")]
    judge = FakeClient("qwen", {"completeness": "* Classification: Dependent\n* Type: pronoun"})
    record = DetectionEnsemble([judge], BASE_CFG).run("q", "a", facts)[0]
    assert record["ensemble"] is True
    assert record["details"]["qwen"]["parse_ok"] is False


def test_type_coercion_maps_free_text_onto_paper_subtypes():
    assert _coerce_type("Missing Comparison") == "missing_comparison"
    assert _coerce_type("Ambiguous Concepts/Pronouns") == "ambiguous_concept_or_pronoun"
    assert _coerce_type("Lack of Condition/Sources") == "omitted_condition_or_source"
    assert _coerce_type("something else") == "other"
    assert _coerce_type("none") == "none"


# ---------------------------------------------------------------------------
# STEP 2C missing relations
# ---------------------------------------------------------------------------
def test_rule_based_relation_cues():
    assert rule_based_relation("making it more competitive") == "contingency"
    assert rule_based_relation("because demand fell") == "contingency"
    assert rule_based_relation("after the merger closed") == "temporal"
    assert rule_based_relation("and other materials") is None


def test_missing_relation_requires_detected_and_not_covered():
    spans = [MissingSpan("making it more competitive", 10, 36, "sentence")]
    facts = [Fact(id="F1", text="Copper and silver are competitive with gold.")]
    judge = FakeClient(
        "qwen",
        {
            "relation": json.dumps(
                {"is_missing_relation": True, "relation_type": "contingency", "reason": "cause"}
            ),
            "relation_coverage": json.dumps({"already_covered": False, "supporting_fact": None}),
        },
    )
    record = MissingRelationEnsemble([judge], BASE_CFG).run("response", spans, facts)[0]
    assert record["relation_detected"] is True
    assert record["already_covered"] is False
    assert record["is_missing_relation"] is True
    assert record["relation_type"] == "contingency"


def test_relation_already_covered_is_not_missing():
    spans = [MissingSpan("because demand fell", 0, 19, "s")]
    facts = [Fact(id="F4", text="Gold prices fell because demand fell.")]
    judge = FakeClient(
        "qwen",
        {
            "relation": json.dumps({"is_missing_relation": True, "relation_type": "contingency"}),
            "relation_coverage": json.dumps({"already_covered": True, "supporting_fact": "F4"}),
        },
    )
    record = MissingRelationEnsemble([judge], BASE_CFG).run("r", spans, facts)[0]
    assert record["already_covered"] is True
    assert record["is_missing_relation"] is False
    assert record["supporting_fact"] == "F4"


def test_non_target_relation_is_ignored():
    spans = [MissingSpan("and other materials like copper", 0, 31, "s")]
    judge = FakeClient(
        "qwen",
        {"relation": json.dumps({"is_missing_relation": True, "relation_type": "expansion"})},
    )
    record = MissingRelationEnsemble([judge], BASE_CFG).run("r", spans, [])[0]
    assert record["is_missing_relation"] is False
    assert record["relation_type"] == "none"


def test_rule_prefilter_skips_spans_without_cues():
    cfg = {
        "ensemble": {"strategy": "union"},
        "missing_relation": {
            "target_relations": ["temporal", "contingency"],
            "coverage_check": True,
            "rule_prefilter": True,
        },
    }
    spans = [MissingSpan("other materials like copper", 0, 27, "s")]
    judge = FakeClient("qwen", {"relation": json.dumps({"is_missing_relation": True, "relation_type": "contingency"})})
    record = MissingRelationEnsemble([judge], cfg).run("r", spans, [])[0]
    assert record["skipped_by_rule_prefilter"] is True
    assert record["is_missing_relation"] is False
    assert judge.seen == []


def test_duplicate_missing_relations_collapse_after_refinement():
    """Two spans expressing the same relation must not yield two identical facts."""
    client = FakeClient(
        "primary",
        {"add_relation": "```\nIf jewelry demand disappeared, the gold price could fall.\n```"},
    )
    refiner = Refiner(client, {})
    records = [
        {"span": "making it more competitive", "relation_type": "contingency"},
        {"span": "making gold cheaper", "relation_type": "contingency"},
    ]
    added = []
    for i, record in enumerate(records, start=1):
        new = refiner.add_relation_fact("q", "answer", record, [], f"M{i}")
        if new:
            added.append(new)
    assert len(added) == 2
    final = assemble_final_facts([], [], added)
    assert len(final) == 1


# ---------------------------------------------------------------------------
# STEP 3 refinement
# ---------------------------------------------------------------------------
def test_refinement_changes_an_incomplete_claim():
    fact = Fact(
        id="F2",
        text="The price of gold could fall by 20-50%.",
        incomplete=True,
        incomplete_type="omitted_condition_or_source",
        incomplete_reason="omits the condition",
    )
    client = FakeClient(
        "primary",
        {
            "refine": "```\nIf jewelry demand disappeared, the price of gold could fall by 20-50%.\n```"
        },
    )
    record = Refiner(client, {}).refine_fact("q", "answer", fact)
    assert record["status"] == "refined"
    assert record["refined"] != record["original"]
    assert record["refined"].lower().startswith("if jewelry demand")


def test_refinement_without_code_block_is_recovered():
    fact = Fact(id="F1", text="Processor A is faster.", incomplete=True, incomplete_type="missing_comparison")
    client = FakeClient("primary", {"refine": "Here is the refined claim:\nProcessor A is faster than Processor B."})
    record = Refiner(client, {}).refine_fact("q", "answer", fact)
    assert record["status"] == "refined"
    assert "than Processor B" in record["refined"]


def test_refinement_keeps_original_when_model_returns_nothing_useful():
    fact = Fact(id="F1", text="Gold is a metal.", incomplete=True)
    client = FakeClient("primary", {"refine": "  "})
    record = Refiner(client, {}).refine_fact("q", "answer", fact)
    assert record["status"] == "unchanged"
    assert record["refined"] == "Gold is a metal."


def test_refinement_rejects_runaway_rewrite():
    fact = Fact(id="F1", text="Gold is a metal.", incomplete=True)
    long_text = "```\n" + " ".join(["word"] * 200) + "\n```"
    client = FakeClient("primary", {"refine": long_text})
    record = Refiner(client, {}).refine_fact("q", "answer", fact)
    assert record["status"] == "unchanged"


def test_add_relation_fact_rejects_too_short_output():
    client = FakeClient("primary", {"add_relation": "```\nyes\n```"})
    out = Refiner(client, {}).add_relation_fact("q", "a", {"span": "making", "relation_type": "contingency"}, [], "M1")
    assert out is None


# ---------------------------------------------------------------------------
# Final assembly and dedup
# ---------------------------------------------------------------------------
def test_assemble_marks_statuses_and_keeps_originals():
    facts = [
        Fact(id="F1", text="There is a demand for gold as jewelry."),
        Fact(id="F2", text="The price of gold could drop by 20-50%.", incomplete=True),
    ]
    refinements = [
        {
            "fact_id": "F2",
            "original": "The price of gold could drop by 20-50%.",
            "refined": "If jewelry demand disappeared, the price of gold could drop by 20-50%.",
            "status": "refined",
            "error_type": "omitted_condition_or_source",
            "reason": "r",
        }
    ]
    added = [
        {
            "fact_id": "M1",
            "text": "A drop in the gold price could make copper and silver competitive with gold.",
            "relation_type": "contingency",
            "span": "making it more competitive",
            "status": "added",
        }
    ]
    final = assemble_final_facts(facts, refinements, added)
    by_id = {f.id: f for f in final}
    assert by_id["F1"].status == "unchanged"
    assert by_id["F2"].status == "refined"
    assert by_id["F2"].original_text == "The price of gold could drop by 20-50%."
    assert by_id["M1"].status == "added"
    assert by_id["M1"].relation_type == "contingency"


def test_deduplicate_drops_near_identical_claims():
    facts = [
        Fact(id="F1", text="Gold prices declined substantially."),
        Fact(id="F2", text="Gold prices declined substantially!"),
        Fact(id="F3", text="Copper conducts electricity better than gold."),
    ]
    kept = deduplicate(facts, threshold=0.9)
    assert [f.id for f in kept] == ["F1", "F3"]


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def test_cache_roundtrip(tmp_path):
    cache = CallCache(tmp_path, enabled=True)
    assert cache.get("abc123") is None
    cache.put("abc123", "hello", meta={"tag": "t"})
    assert cache.get("abc123") == "hello"
    assert cache.stats()["hits"] == 1


def test_disabled_cache_never_stores(tmp_path):
    cache = CallCache(tmp_path, enabled=False)
    cache.put("k", "v")
    assert cache.get("k") is None


# ---------------------------------------------------------------------------
# Retrieval ranking
# ---------------------------------------------------------------------------
def test_bm25_ranks_the_relevant_paragraph_first():
    docs = [
        "Gold is used in electronics because it resists corrosion and conducts electricity.",
        "The Panama Canal opened in 1914 and shortened shipping routes.",
    ]
    scores = bm25_scores("gold electronics corrosion conductivity", docs)
    assert scores[0] > scores[1]


def test_tfidf_ranks_the_relevant_paragraph_first():
    docs = [
        "Jewellery is the largest source of annual gold demand.",
        "Lithium-ion batteries store more energy per kilogram than lead-acid batteries.",
    ]
    scores = tfidf_scores("gold jewellery demand", docs)
    assert scores[0] > scores[1]


def test_rankers_handle_empty_input():
    assert bm25_scores("", ["abc"]) == [0.0]
    assert tfidf_scores("gold", []) == []


@pytest.mark.parametrize("ranker", [bm25_scores, tfidf_scores])
def test_rankers_return_one_score_per_document(ranker):
    docs = ["alpha beta", "gamma delta", "beta gamma"]
    assert len(ranker("beta", docs)) == len(docs)
