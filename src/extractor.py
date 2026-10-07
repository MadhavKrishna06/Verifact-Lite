"""STEP 1 - baseline fact extraction (SAFE-style decompose + decontextualize).

This is deliberately the weak baseline the paper measures against: sentences are
decomposed independently, and decontextualization resolves vague references only.
Conditions, comparison targets and inter-sentence relations are therefore lost -
exactly the failure modes VERIFACT-Lite detects and repairs later.
"""

from __future__ import annotations

from .model_client import BaseClient
from . import prompts
from .utils import Fact, parse_bullet_list, extract_first_code_block, sentence_split, word_count


class BaselineExtractor:
    def __init__(self, client: BaseClient, cfg: dict):
        self.client = client
        ex = cfg.get("extraction") or {}
        self.decontextualize = bool(ex.get("decontextualize", True))
        self.max_per_sentence = int(ex.get("max_facts_per_sentence", 8))

    # -- decomposition ------------------------------------------------------
    def decompose_sentence(self, sentence: str) -> list[str]:
        messages = list(prompts.BREAKDOWN_DEMOS)
        messages.append(
            {"role": "user", "content": prompts.BREAKDOWN_USER.format(sentence=sentence)}
        )
        raw = self.client.chat(messages, temperature=0.0, tag="extract")
        facts = parse_bullet_list(raw)
        if not facts:
            # Recovery path: treat non-empty, non-preamble lines as facts.
            for line in (raw or "").splitlines():
                line = line.strip().strip("`")
                if len(line.split()) >= 3 and not line.lower().startswith(
                    ("here", "sure", "the atomic", "atomic facts", "output")
                ):
                    facts.append(line)
        cleaned = []
        for fact in facts:
            fact = fact.strip().rstrip(";")
            if not fact.endswith((".", "!", "?")):
                fact += "."
            if word_count(fact) >= 3:
                cleaned.append(fact)
        return cleaned[: self.max_per_sentence]

    # -- decontextualization ------------------------------------------------
    def decontextualize_fact(self, fact: str, response: str) -> str:
        if not self.decontextualize:
            return fact
        prompt = prompts.DECONTEXTUALIZE_PROMPT.format(statement=fact, response=response)
        raw = self.client.complete(prompt, temperature=0.0, tag="decontext")
        revised = extract_first_code_block(raw)
        if not revised or word_count(revised) < 3 or word_count(revised) > 3 * word_count(fact) + 12:
            return fact
        return revised.replace("\n", " ").strip()

    # -- public API ---------------------------------------------------------
    def extract(self, question: str, answer: str) -> tuple[list[Fact], list[list[str]]]:
        """Return (facts, facts grouped by source sentence).

        The grouping feeds the per-sentence word-mapping of STEP 2B.
        """
        sentences = sentence_split(answer)
        facts: list[Fact] = []
        grouped: list[list[str]] = []
        counter = 1
        for sentence in sentences:
            atomic = self.decompose_sentence(sentence)
            group: list[str] = []
            for raw_fact in atomic:
                text = self.decontextualize_fact(raw_fact, answer)
                facts.append(
                    Fact(
                        id=f"F{counter}",
                        text=text,
                        original_text=text,
                        source_sentence=sentence,
                    )
                )
                group.append(text)
                counter += 1
            grouped.append(group)
        return facts, grouped
