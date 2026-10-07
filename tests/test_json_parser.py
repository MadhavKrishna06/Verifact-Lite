"""Tests for robust parsing and recovery from malformed model output."""

from src.utils import (
    extract_first_code_block,
    first_label,
    parse_bullet_list,
    parse_json_loose,
    yes_no,
)


def test_parses_clean_json():
    assert parse_json_loose('{"is_incomplete": true, "type": "other"}')["is_incomplete"] is True


def test_parses_json_inside_fenced_block_with_prose():
    raw = 'Sure! Here is the result:\n```json\n{"label": "SUPPORTED", "confidence": 0.8}\n```\nHope that helps.'
    parsed = parse_json_loose(raw)
    assert parsed["label"] == "SUPPORTED"
    assert parsed["confidence"] == 0.8


def test_parses_json_with_trailing_commas_and_python_literals():
    raw = '{"covered": True, "supporting_text": None,}'
    parsed = parse_json_loose(raw)
    assert parsed["covered"] is True
    assert parsed["supporting_text"] is None


def test_parses_json_with_smart_quotes():
    raw = '{“label”: “CONTRADICTED”}'
    assert parse_json_loose(raw)["label"] == "CONTRADICTED"


def test_parses_json_surrounded_by_reasoning_text():
    raw = 'The claim omits a condition. {"is_incomplete": true, "type": "omitted_condition_or_source", "reason": "no if"} Done.'
    parsed = parse_json_loose(raw)
    assert parsed["type"] == "omitted_condition_or_source"


def test_parses_nested_json_object():
    raw = '{"outer": {"inner": [1, 2, 3]}}'
    assert parse_json_loose(raw)["outer"]["inner"] == [1, 2, 3]


def test_parses_json_list():
    assert parse_json_loose('[{"a": 1}, {"a": 2}]')[1]["a"] == 2


def test_returns_default_on_unparseable_text():
    assert parse_json_loose("I cannot answer that.", default={"fallback": True}) == {"fallback": True}
    assert parse_json_loose("", default=None) is None
    assert parse_json_loose(None, default=[]) == []


def test_json_with_comment_line():
    raw = '{\n  // thinking\n  "label": "UNDECIDED"\n}'
    assert parse_json_loose(raw)["label"] == "UNDECIDED"


def test_code_block_extraction_and_unterminated_fence():
    assert extract_first_code_block("text\n```\nthe fact.\n```") == "the fact."
    assert extract_first_code_block("```\nunterminated fact.") == "unterminated fact."
    assert extract_first_code_block("no block here") == ""


def test_bullet_list_parsing_handles_dashes_and_numbers():
    raw = "- Gold is a metal.\n* Silver conducts well.\n1. Copper is cheap.\n\nrandom trailing line"
    items = parse_bullet_list(raw)
    assert items == ["Gold is a metal.", "Silver conducts well.", "Copper is cheap."]


def test_first_label_and_yes_no():
    assert first_label("The claim is DEPENDENT on context", ["INDEPENDENT", "DEPENDENT"]) == "DEPENDENT"
    # "INDEPENDENT" contains "DEPENDENT", so position decides.
    assert first_label("INDEPENDENT", ["INDEPENDENT", "DEPENDENT"]) == "INDEPENDENT"
    assert yes_no("YES, fact F3 covers it") is True
    assert yes_no("NO, nothing covers it") is False
    assert yes_no("unclear", default=False) is False
