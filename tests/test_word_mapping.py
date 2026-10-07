"""Tests for the STEP 2B word-mapping algorithm (paper Algorithm 1)."""

from src.word_mapping import (
    coverage_indicator,
    coverage_ratio,
    find_missing_spans,
    longest_common_substring,
    normalize_preserving_index,
    uncovered_spans,
)

GOLD_RESPONSE = (
    "If the demand for gold as jewelry were to disappear, the price of gold could drop by "
    "20-50% or more, making it more competitive with other materials like copper and silver."
)

SAFE_FACTS = [
    "There is a demand for gold as jewelry.",
    "The price of gold could drop by 20-50% or more.",
    "Copper and silver are competitive with gold in terms of price.",
]


def test_normalization_preserves_length_and_offsets():
    text = "If  demand\ndisappeared—prices FELL."
    norm = normalize_preserving_index(text)
    assert len(norm) == len(text)
    assert norm.islower() or not norm.isalpha()
    assert "\n" not in norm


def test_longest_common_substring_basic():
    sub, start, end = longest_common_substring("the price of gold", "price of gold could drop")
    assert sub == "price of gold"
    assert "the price of gold"[start:end] == sub


def test_longest_common_substring_empty():
    assert longest_common_substring("", "abc") == ("", 0, 0)
    assert longest_common_substring("abc", "") == ("", 0, 0)
    assert longest_common_substring("abc", "xyz")[0] == ""


def test_coverage_indicator_marks_matched_region():
    text = "alpha beta gamma delta"
    indicator = coverage_indicator(text, ["beta gamma"])
    covered = "".join(c for c, flag in zip(text, indicator) if flag)
    assert covered == "beta gamma"
    assert sum(indicator) == len("beta gamma")


def test_uncovered_spans_offsets_point_into_original_text():
    spans = uncovered_spans(GOLD_RESPONSE, SAFE_FACTS, min_chars=8, min_words=2)
    assert spans, "expected at least one uncovered span"
    for span in spans:
        assert GOLD_RESPONSE[span.start : span.end] == span.text


def test_word_mapping_finds_the_contingency_cue_from_the_paper():
    """'making' signals the causal relation SAFE misses (paper Figure 1)."""
    spans = uncovered_spans(GOLD_RESPONSE, SAFE_FACTS, min_chars=8, min_words=2)
    joined = " ".join(s.text.lower() for s in spans)
    assert "making" in joined


def test_fully_covered_text_has_no_missing_spans():
    text = "Aluminium is the most abundant metal in the Earth's crust."
    assert uncovered_spans(text, [text]) == []
    assert coverage_ratio(text, [text]) == 1.0


def test_small_punctuation_spans_are_filtered():
    text = "Gold is a metal, and it conducts electricity."
    facts = ["Gold is a metal", "it conducts electricity"]
    spans = uncovered_spans(text, facts, min_chars=12, min_words=3)
    assert all(len(s.text) >= 12 for s in spans)


def test_find_missing_spans_per_sentence_mode():
    response = "Gold is a metal. If jewelry demand vanished, the gold price could fall sharply."
    grouped = [["Gold is a metal."], ["The gold price could fall sharply."]]
    spans = find_missing_spans(response, sum(grouped, []), sentence_facts=grouped, min_chars=10, min_words=3)
    assert spans
    for span in spans:
        assert response[span.start : span.end] == span.text
    assert any("jewelry demand" in s.text for s in spans)


def test_find_missing_spans_handles_empty_input():
    assert find_missing_spans("", ["anything"]) == []
    assert find_missing_spans("Some text here.", []) != []
