"""STEP 4b - fact verification and reference-fact coverage.

Verification labels a claim SUPPORTED / CONTRADICTED / UNDECIDED against the
retrieved evidence. "No evidence found" is never treated as support: it is
UNDECIDED, which is reported separately from precision.
"""

from __future__ import annotations

from .model_client import BaseClient
from .retrieval import WikipediaRetriever
from . import prompts
from .utils import (
    Evidence,
    first_label,
    parse_json_loose,
    token_overlap_recall,
)

LABELS = ("SUPPORTED", "CONTRADICTED", "UNDECIDED")


def format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "(no evidence retrieved)"
    return "\n\n".join(f"[{e.id}] ({e.title}) {e.snippet}" for e in evidence)


class FactVerifier:
    def __init__(self, client: BaseClient, retriever: WikipediaRetriever, cfg: dict):
        self.client = client
        self.retriever = retriever
        v = cfg.get("verification") or {}
        self.max_snippets = int(v.get("evidence_snippets", 5))

    def verify(self, claim: str) -> dict:
        evidence, queries = self.retriever.retrieve(claim)
        evidence = evidence[: self.max_snippets]
        if not evidence:
            return {
                "claim": claim,
                "label": "UNDECIDED",
                "confidence": 0.0,
                "evidence_ids": [],
                "reason": "No evidence retrieved; absence of evidence is not support.",
                "queries": queries,
                "evidence": [],
            }

        prompt = prompts.VERIFY_PROMPT.format(claim=claim, evidence=format_evidence(evidence))
        raw = self.client.complete(prompt, temperature=0.0, tag="verify")
        parsed = parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]

        if isinstance(parsed, dict):
            label = str(parsed.get("label", "")).strip().upper()
            label = label if label in LABELS else (first_label(raw, LABELS) or "UNDECIDED")
            try:
                confidence = float(parsed.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            ids = parsed.get("evidence_ids") or []
            ids = [str(i) for i in ids if isinstance(i, (str, int))]
            reason = str(parsed.get("reason", "")).strip()[:300]
        else:
            label = first_label(raw, LABELS) or "UNDECIDED"
            confidence = 0.0
            ids = []
            reason = (raw or "").strip()[:300]

        valid_ids = {e.id for e in evidence}
        ids = [i for i in ids if i in valid_ids]
        if label == "SUPPORTED" and not ids:
            # A SUPPORTED verdict must point at evidence; otherwise it is not grounded.
            best = max(evidence, key=lambda e: token_overlap_recall(claim, e.snippet))
            if token_overlap_recall(claim, best.snippet) >= 0.4:
                ids = [best.id]
            else:
                label = "UNDECIDED"
                reason = (reason + " | downgraded: no grounded evidence id").strip()

        return {
            "claim": claim,
            "label": label,
            "confidence": max(0.0, min(1.0, confidence)),
            "evidence_ids": ids,
            "reason": reason,
            "queries": queries,
            "evidence": [e.to_dict() for e in evidence],
        }


class RecallChecker:
    """Checks whether the response entails each reference fact (paper Eq. 2)."""

    def __init__(self, client: BaseClient, cfg: dict):
        self.client = client
        r = cfg.get("recall") or {}
        self.threshold = float(r.get("similarity_threshold", 0.18))
        self.llm_confirmation = bool(r.get("llm_confirmation", True))

    def check(self, reference_fact: str, response: str) -> dict:
        similarity = token_overlap_recall(reference_fact, response)
        if similarity < self.threshold:
            # Lexically unrelated: not covered, and no LLM call needed.
            return {
                "reference_fact": reference_fact,
                "covered": False,
                "supporting_text": None,
                "similarity": round(similarity, 3),
                "method": "lexical_gate",
            }
        if not self.llm_confirmation:
            return {
                "reference_fact": reference_fact,
                "covered": similarity >= 0.6,
                "supporting_text": None,
                "similarity": round(similarity, 3),
                "method": "lexical_only",
            }

        prompt = prompts.RECALL_ENTAILMENT_PROMPT.format(
            claim=reference_fact, paragraph=response
        )
        raw = self.client.complete(prompt, temperature=0.0, tag="recall")
        parsed = parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            covered = bool(parsed.get("covered"))
            support = parsed.get("supporting_text")
            support = support if isinstance(support, str) and support.strip() else None
        else:
            covered = first_label(raw or "", ["YES", "NO"]) == "YES"
            support = None
        return {
            "reference_fact": reference_fact,
            "covered": covered,
            "supporting_text": support,
            "similarity": round(similarity, 3),
            "method": "lexical+llm",
        }
