"""Shared helpers: config loading, robust JSON parsing, sentence splitting, IO."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def load_config(path: str | os.PathLike | None = None) -> dict:
    """Load config.yaml. Model names are never hard-coded in the source."""
    cfg_path = Path(path) if path else REPO_ROOT / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["_root"] = str(REPO_ROOT)
    return cfg


def resolve_path(cfg: dict, relative: str) -> Path:
    p = Path(relative)
    return p if p.is_absolute() else Path(cfg.get("_root", REPO_ROOT)) / p


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------
_ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "st.", "jr.", "sr.", "vs.", "etc.",
    "e.g.", "i.e.", "approx.", "no.", "fig.", "al.", "u.s.", "u.k.",
}


def sentence_split(text: str) -> list[str]:
    """Split into sentences, keeping it dependency-light and deterministic.

    nltk's punkt is used when its data is already present; otherwise a regex
    fallback keeps the pipeline runnable with zero downloads.
    """
    text = (text or "").strip()
    if not text:
        return []
    try:  # pragma: no cover - depends on local nltk data
        import nltk

        nltk.data.find("tokenizers/punkt_tab")
        return [s.strip() for s in nltk.sent_tokenize(text) if s.strip()]
    except Exception:
        pass

    parts: list[str] = []
    buf: list[str] = []
    tokens = re.split(r"(\s+)", text)
    for token in tokens:
        buf.append(token)
        stripped = token.strip()
        if not stripped:
            continue
        if stripped[-1] in ".!?" and stripped.lower() not in _ABBREVIATIONS:
            # Avoid splitting on decimals such as "20.5" or initials "J.".
            if re.search(r"\d\.$", stripped) or re.fullmatch(r"[A-Z]\.", stripped):
                continue
            parts.append("".join(buf).strip())
            buf = []
    if buf and "".join(buf).strip():
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def normalize_for_match(text: str) -> str:
    """Case/whitespace/line-break normalisation used by matching helpers.

    Note: word_mapping.py keeps its own index-preserving normalisation so that
    character offsets into the ORIGINAL response remain valid.
    """
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "of",
    "to", "in", "on", "for", "with", "and", "or", "that", "this", "these",
    "those", "it", "its", "as", "at", "by", "from", "can", "could", "would",
    "will", "may", "might", "has", "have", "had", "do", "does", "did", "than",
    "then", "there", "their", "them", "they", "which", "who", "but", "if",
    "not", "no", "more", "most", "also", "such", "about", "into", "over",
}


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize_for_match(text))


def content_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in _STOPWORDS]


def jaccard(a: str, b: str) -> float:
    ta, tb = set(content_tokens(a)), set(content_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def token_overlap_recall(claim: str, text: str) -> float:
    """Fraction of the claim's content tokens that occur in `text`."""
    tc = content_tokens(claim)
    if not tc:
        return 0.0
    tt = set(content_tokens(text))
    return sum(1 for t in tc if t in tt) / len(tc)


def word_count(text: str) -> int:
    return len((text or "").split())


# ---------------------------------------------------------------------------
# Robust parsing of model output
# ---------------------------------------------------------------------------
def extract_first_code_block(text: str) -> str:
    """Extract the first markdown code block, mirroring the official repo."""
    if not text:
        return ""
    match = re.search(r"```(?:[A-Za-z0-9_+-]*\n)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip(" \n")
    # Unterminated fence: take everything after the opening fence.
    match = re.search(r"```(?:[A-Za-z0-9_+-]*\n)?(.*)", text, re.DOTALL)
    return match.group(1).strip(" \n") if match else ""


def _balanced_json_candidates(text: str) -> Iterable[str]:
    """Yield substrings that look like balanced JSON objects or arrays."""
    opens = {"{": "}", "[": "]"}
    for i, ch in enumerate(text):
        if ch not in opens:
            continue
        closer = opens[ch]
        depth = 0
        in_str = False
        escape = False
        for j in range(i, len(text)):
            c = text[j]
            if in_str:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == ch:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    yield text[i : j + 1]
                    break


def _repair_json(blob: str) -> str:
    blob = re.sub(r"^\s*```(?:json)?", "", blob).strip()
    blob = re.sub(r"```\s*$", "", blob).strip()
    blob = blob.replace("“", '"').replace("”", '"')
    blob = blob.replace("‘", "'").replace("’", "'")
    blob = re.sub(r",\s*([}\]])", r"\1", blob)          # trailing commas
    blob = re.sub(r"\bTrue\b", "true", blob)
    blob = re.sub(r"\bFalse\b", "false", blob)
    blob = re.sub(r"\bNone\b", "null", blob)
    blob = re.sub(r"//[^\n]*", "", blob)                 # // comments
    return blob


def parse_json_loose(text: str, default: Any = None) -> Any:
    """Parse JSON out of noisy LLM output.

    Tries, in order: the raw string, the first fenced code block, every
    balanced {...}/[...] span, and a light repair pass on each candidate.
    Returns `default` when nothing parses; never raises.
    """
    if text is None:
        return default
    if isinstance(text, (dict, list)):
        return text

    candidates: list[str] = [text.strip()]
    block = extract_first_code_block(text)
    if block:
        candidates.append(block)
    candidates.extend(_balanced_json_candidates(text))
    if block:
        candidates.extend(_balanced_json_candidates(block))

    for cand in candidates:
        if not cand:
            continue
        for attempt in (cand, _repair_json(cand)):
            try:
                return json.loads(attempt)
            except Exception:
                continue
    return default


def parse_bullet_list(text: str) -> list[str]:
    """Fallback extraction of '- item' / '1. item' lines."""
    items: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(?:[-*•]|\d+[.)])\s+(.*)$", line)
        if m:
            cleaned = m.group(1).strip().strip("`").strip()
            if cleaned:
                items.append(cleaned)
    return items


def first_label(text: str, labels: Iterable[str]) -> str | None:
    """Return the first label from `labels` that appears in `text`."""
    if not text:
        return None
    upper = text.upper()
    best: tuple[int, str] | None = None
    for label in labels:
        idx = upper.find(label.upper())
        if idx >= 0 and (best is None or idx < best[0]):
            best = (idx, label)
    return best[1] if best else None


def yes_no(text: str, default: bool = False) -> bool:
    """Interpret a YES/NO answer, honouring the first occurrence."""
    if not text:
        return default
    label = first_label(text, ["YES", "NO"])
    if label is None:
        return default
    return label == "YES"


def hash_key(*parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------
def read_jsonl(path: str | os.PathLike) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | os.PathLike, rows: Iterable[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str | os.PathLike, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def read_json(path: str | os.PathLike, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Data classes shared across the pipeline
# ---------------------------------------------------------------------------
@dataclass
class Fact:
    """A single extracted (and possibly refined or added) fact."""

    id: str
    text: str
    original_text: str = ""
    source_sentence: str = ""
    status: str = "unchanged"        # unchanged | refined | added
    incomplete: bool = False
    incomplete_type: str = ""
    incomplete_reason: str = ""
    relation_type: str = ""
    judge_votes: dict = field(default_factory=dict)
    ensemble: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Evidence:
    id: str
    source: str
    title: str
    url: str
    snippet: str
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
