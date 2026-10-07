"""STEP 2B - word-mapping algorithm (paper Appendix A.4, Algorithm 1).

For every extracted fact, find its longest common substring with the original
response, mark those response characters as covered, and return the contiguous
uncovered spans. Character offsets always refer to the ORIGINAL response, so
normalisation (case, whitespace, line breaks) is index-preserving.

The official implementation runs the algorithm per response sentence, matching
each sentence against the facts derived from it; ``find_missing_spans`` does the
same when sentence-to-fact alignment is available, and falls back to
whole-response mapping when it is not.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict

from .utils import sentence_split


@dataclass
class MissingSpan:
    text: str
    start: int
    end: int
    sentence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Index-preserving normalisation
# ---------------------------------------------------------------------------
_CHAR_MAP = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "−": "-", " ": " ",
    "\n": " ", "\r": " ", "\t": " ",
}


def normalize_preserving_index(text: str) -> str:
    """Lower-case and flatten whitespace WITHOUT changing string length.

    Every transformation is 1 character -> 1 character, so position i in the
    result corresponds to position i in the input.
    """
    out = []
    for ch in text:
        ch = _CHAR_MAP.get(ch, ch)
        if unicodedata.category(ch) == "Zs":
            ch = " "
        out.append(ch.lower())
    return "".join(out)


# ---------------------------------------------------------------------------
# Longest common substring
# ---------------------------------------------------------------------------
def longest_common_substring(a: str, b: str) -> tuple[str, int, int]:
    """Return (substring, start, end) of the LCS, as offsets into `a`.

    Mirrors ``longestCommonSubstring`` in the official repo but with O(min)
    memory. ``end`` is exclusive.
    """
    if not a or not b:
        return "", 0, 0
    prev = [0] * (len(b) + 1)
    best_len = 0
    best_end = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best_len:
                    best_len = cur[j]
                    best_end = i
        prev = cur
    return a[best_end - best_len : best_end], best_end - best_len, best_end


# ---------------------------------------------------------------------------
# Coverage + uncovered spans
# ---------------------------------------------------------------------------
def coverage_indicator(text: str, facts: list[str]) -> list[int]:
    """Binary coverage array over `text`, one entry per character."""
    norm_text = normalize_preserving_index(text)
    indicator = [0] * len(text)
    for fact in facts:
        if not fact or not fact.strip():
            continue
        norm_fact = normalize_preserving_index(fact)
        _, start, end = longest_common_substring(norm_text, norm_fact)
        if end > start:
            for i in range(start, end):
                indicator[i] = 1
    return indicator


def uncovered_spans(
    text: str,
    facts: list[str],
    min_chars: int = 12,
    min_words: int = 3,
    offset: int = 0,
) -> list[MissingSpan]:
    """Contiguous runs of uncovered characters, filtered to meaningful spans."""
    indicator = coverage_indicator(text, facts)
    spans: list[MissingSpan] = []
    start = -1
    for i, flag in enumerate(indicator):
        if flag == 0:
            if start == -1:
                start = i
        elif start != -1:
            spans.append(MissingSpan(text[start:i], start + offset, i + offset, text))
            start = -1
    if start != -1:
        spans.append(MissingSpan(text[start:], start + offset, len(text) + offset, text))

    kept: list[MissingSpan] = []
    norm_facts = [normalize_preserving_index(f) for f in facts if f]
    for span in spans:
        trimmed, lead = _trim(span.text)
        if not _is_meaningful(trimmed, min_chars, min_words):
            continue
        norm_trimmed = normalize_preserving_index(trimmed)
        # The official code drops a trailing span that already appears verbatim
        # inside some fact; apply that check to every span.
        if any(norm_trimmed in nf for nf in norm_facts):
            continue
        kept.append(
            MissingSpan(
                text=trimmed,
                start=span.start + lead,
                end=span.start + lead + len(trimmed),
                sentence=span.sentence,
            )
        )
    return kept


def _trim(text: str) -> tuple[str, int]:
    """Strip surrounding whitespace/punctuation, returning the left shift."""
    match = re.match(r"^[\s,;:.\-–—\(\)\"']*", text)
    lead = match.end() if match else 0
    body = text[lead:]
    body = re.sub(r"[\s,;:.\-–—\(\)\"']*$", "", body)
    return body, lead


def _is_meaningful(text: str, min_chars: int, min_words: int) -> bool:
    if len(text) < min_chars:
        return False
    words = [w for w in re.split(r"\s+", text) if w]
    if len(words) < min_words:
        return False
    return bool(re.search(r"[A-Za-z]", text))


def find_missing_spans(
    response: str,
    facts: list[str],
    sentence_facts: list[list[str]] | None = None,
    min_chars: int = 12,
    min_words: int = 3,
) -> list[MissingSpan]:
    """Public entry point for STEP 2B.

    When ``sentence_facts`` is given (facts grouped by the response sentence
    they came from), the mapping runs per sentence as in the official repo.
    Otherwise the whole response is mapped against all facts.
    """
    response = response or ""
    if not response.strip():
        return []

    if sentence_facts is None:
        return uncovered_spans(response, facts, min_chars, min_words)

    sentences = sentence_split(response)
    spans: list[MissingSpan] = []
    cursor = 0
    for idx, sentence in enumerate(sentences):
        found = response.find(sentence, cursor)
        if found < 0:
            found = response.find(sentence)
        base = found if found >= 0 else cursor
        cursor = base + len(sentence)
        group = sentence_facts[idx] if idx < len(sentence_facts) else []
        spans.extend(uncovered_spans(sentence, group, min_chars, min_words, offset=base))
    return spans


def coverage_ratio(response: str, facts: list[str]) -> float:
    """Share of response characters covered by at least one fact."""
    if not response:
        return 0.0
    indicator = coverage_indicator(response, facts)
    return sum(indicator) / len(indicator)
