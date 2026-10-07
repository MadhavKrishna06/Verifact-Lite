"""STEP 3 - refine incomplete facts and add missing relational facts.

Refinement is a separate stage from detection: it consumes the detection record
(error type + explanation) exactly as the paper's self-reflection step does.
"""

from __future__ import annotations

from .model_client import BaseClient
from . import prompts
from .utils import Fact, extract_first_code_block, jaccard, word_count, normalize_for_match


class Refiner:
    def __init__(self, client: BaseClient, cfg: dict):
        self.client = client
        self.cfg = cfg

    # -- STEP 3: incomplete facts ------------------------------------------
    def refine_fact(self, question: str, answer: str, fact: Fact) -> dict:
        prompt = prompts.REFINE_INCOMPLETE_PROMPT.format(
            question=question,
            response=answer,
            claim=fact.text,
            error_type=fact.incomplete_type or "dependent",
            reason=fact.incomplete_reason or "The claim needs context from the answer.",
        )
        raw = self.client.complete(prompt, temperature=0.0, tag="refine")
        refined = extract_first_code_block(raw)
        if not refined:
            refined = _first_sentence_fallback(raw)
        refined = (refined or "").replace("\n", " ").strip().strip('"')

        status = "refined"
        if not refined or word_count(refined) < 3:
            refined, status = fact.text, "unchanged"
        elif word_count(refined) > 4 * max(word_count(fact.text), 6) + 15:
            # Over-long rewrite: the model drifted, keep the original.
            refined, status = fact.text, "unchanged"
        elif normalize_for_match(refined) == normalize_for_match(fact.text):
            status = "unchanged"

        return {
            "fact_id": fact.id,
            "original": fact.text,
            "refined": refined,
            "status": status,
            "error_type": fact.incomplete_type,
            "reason": fact.incomplete_reason,
        }

    # -- STEP 3B: missing relational facts ---------------------------------
    def add_relation_fact(
        self, question: str, answer: str, record: dict, facts: list[Fact], new_id: str
    ) -> dict | None:
        fact_list = "\n".join(f"- {f.text}" for f in facts) or "(none)"
        prompt = prompts.ADD_RELATION_FACT_PROMPT.format(
            question=question,
            response=answer,
            span=record["span"],
            relation_type=record.get("relation_type") or "contingency",
            fact_list=fact_list,
        )
        raw = self.client.complete(prompt, temperature=0.0, tag="add_relation")
        text = extract_first_code_block(raw) or _first_sentence_fallback(raw)
        text = (text or "").replace("\n", " ").strip().strip('"')
        if not text or word_count(text) < 4:
            return None
        if not text.endswith((".", "!", "?")):
            text += "."
        return {
            "fact_id": new_id,
            "text": text,
            "relation_type": record.get("relation_type", ""),
            "span": record["span"],
            "status": "added",
        }


def _first_sentence_fallback(raw: str) -> str:
    """Recover a claim when the model forgot the code block."""
    for line in (raw or "").splitlines():
        line = line.strip().strip("`").strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith(("here", "sure", "refined claim", "new fact", "output", "#", "*")):
            continue
        if word_count(line) >= 4:
            return line
    return ""


# ---------------------------------------------------------------------------
# Final fact set assembly (section 15 of the brief)
# ---------------------------------------------------------------------------
def assemble_final_facts(
    facts: list[Fact],
    refinements: list[dict],
    added: list[dict],
    dedup_threshold: float = 0.9,
) -> list[Fact]:
    """Combine unchanged + refined + added facts, dropping near-duplicates."""
    by_id = {r["fact_id"]: r for r in refinements}
    final: list[Fact] = []

    for fact in facts:
        record = by_id.get(fact.id)
        if record and record["status"] == "refined":
            final.append(
                Fact(
                    id=fact.id,
                    text=record["refined"],
                    original_text=record["original"],
                    source_sentence=fact.source_sentence,
                    status="refined",
                    incomplete=fact.incomplete,
                    incomplete_type=fact.incomplete_type,
                    incomplete_reason=fact.incomplete_reason,
                    judge_votes=fact.judge_votes,
                    ensemble=fact.ensemble,
                )
            )
        else:
            final.append(
                Fact(
                    id=fact.id,
                    text=fact.text,
                    original_text=fact.original_text or fact.text,
                    source_sentence=fact.source_sentence,
                    status="unchanged",
                    incomplete=fact.incomplete,
                    incomplete_type=fact.incomplete_type,
                    incomplete_reason=fact.incomplete_reason,
                    judge_votes=fact.judge_votes,
                    ensemble=fact.ensemble,
                )
            )

    for record in added:
        final.append(
            Fact(
                id=record["fact_id"],
                text=record["text"],
                original_text="",
                source_sentence=record.get("span", ""),
                status="added",
                relation_type=record.get("relation_type", ""),
            )
        )

    return deduplicate(final, dedup_threshold)


def deduplicate(facts: list[Fact], threshold: float = 0.9) -> list[Fact]:
    """Drop near-identical claims, keeping the first occurrence.

    Added relational facts are never allowed to displace an original fact.
    """
    kept: list[Fact] = []
    for fact in facts:
        norm = normalize_for_match(fact.text)
        duplicate = False
        for existing in kept:
            if normalize_for_match(existing.text) == norm:
                duplicate = True
                break
            if jaccard(existing.text, fact.text) >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(fact)
    return kept
