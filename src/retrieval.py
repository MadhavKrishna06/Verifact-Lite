"""STEP 4a - free evidence retrieval.

The paper queries Google Search through Serper. That dependency is replaced by
the public Wikipedia/Wikimedia API, which needs no key and no payment:

    claim -> local LLM query generation -> Wikipedia search -> page extracts
          -> paragraph split -> BM25/TF-IDF ranking -> top-k evidence

Every network response is cached under data/evidence/, so a run can be repeated
offline (``retrieval.offline_only: true`` forbids the network entirely).
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from pathlib import Path

import requests

from .model_client import BaseClient
from . import prompts
from .utils import (
    Evidence,
    content_tokens,
    hash_key,
    parse_json_loose,
    read_json,
    resolve_path,
    write_json,
)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
def bm25_scores(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    q_terms = content_tokens(query)
    if not q_terms or not docs:
        return [0.0] * len(docs)
    doc_tokens = [content_tokens(d) for d in docs]
    lengths = [len(t) or 1 for t in doc_tokens]
    avgdl = sum(lengths) / len(lengths)
    n_docs = len(docs)
    df = Counter()
    for tokens in doc_tokens:
        for term in set(tokens):
            df[term] += 1

    scores = []
    for tokens, length in zip(doc_tokens, lengths):
        tf = Counter(tokens)
        score = 0.0
        for term in q_terms:
            if term not in tf:
                continue
            idf = math.log(1 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
            freq = tf[term]
            score += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * length / avgdl))
        scores.append(score)
    return scores


def tfidf_scores(query: str, docs: list[str]) -> list[float]:
    """TF-IDF + cosine similarity, implemented locally (no paid embeddings)."""
    q_terms = content_tokens(query)
    if not q_terms or not docs:
        return [0.0] * len(docs)
    doc_tokens = [content_tokens(d) for d in docs]
    n_docs = len(docs)
    df = Counter()
    for tokens in doc_tokens:
        for term in set(tokens):
            df[term] += 1
    idf = {t: math.log((1 + n_docs) / (1 + df.get(t, 0))) + 1.0 for t in set(sum(doc_tokens, [])) | set(q_terms)}

    def vec(tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        v = {t: (1 + math.log(c)) * idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    qv = vec(q_terms)
    out = []
    for tokens in doc_tokens:
        dv = vec(tokens)
        out.append(sum(qv.get(t, 0.0) * dv.get(t, 0.0) for t in qv))
    return out


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------
class WikipediaRetriever:
    def __init__(self, cfg: dict, client: BaseClient | None = None):
        r = cfg.get("retrieval") or {}
        self.cfg = r
        self.client = client
        self.api_url = r.get("api_url", "https://en.wikipedia.org/w/api.php")
        self.user_agent = r.get("user_agent", "VERIFACT-Lite/0.1 (research)")
        self.queries_per_fact = int(r.get("queries_per_fact", 3))
        self.pages_per_query = int(r.get("pages_per_query", 3))
        self.max_pages = int(r.get("max_pages_per_fact", 6))
        self.top_k = int(r.get("top_k", 5))
        self.ranker = str(r.get("ranker", "bm25")).lower()
        self.min_chars = int(r.get("min_paragraph_chars", 120))
        self.delay = float(r.get("request_delay_s", 0.2))
        self.offline_only = bool(r.get("offline_only", False))
        self.cache_dir = resolve_path(cfg, r.get("cache_dir", "data/evidence"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.network_calls = 0
        self.cache_hits = 0

    # -- caching ------------------------------------------------------------
    def _cache_path(self, kind: str, key: str) -> Path:
        return self.cache_dir / kind / f"{hash_key(kind, key)}.json"

    def _cached(self, kind: str, key: str):
        return read_json(self._cache_path(kind, key))

    def _store(self, kind: str, key: str, payload) -> None:
        write_json(self._cache_path(kind, key), payload)

    # -- query generation ---------------------------------------------------
    def generate_queries(self, claim: str) -> list[str]:
        queries: list[str] = []
        if self.client is not None:
            prompt = prompts.QUERY_GEN_PROMPT.format(claim=claim, n=self.queries_per_fact)
            raw = self.client.complete(prompt, temperature=0.2, tag="query_gen")
            parsed = parse_json_loose(raw)
            if isinstance(parsed, dict):
                parsed = parsed.get("queries")
            if isinstance(parsed, list):
                for q in parsed:
                    if isinstance(q, str) and 2 <= len(q.split()) <= 14:
                        q = q.strip().strip('"').rstrip("?")
                        if q and q.lower() not in {x.lower() for x in queries}:
                            queries.append(q)

        # Deterministic fallbacks keep the queries diverse even if parsing failed.
        if len(queries) < self.queries_per_fact:
            terms = content_tokens(claim)
            if terms:
                keyword = " ".join(terms[:6])
                if keyword.lower() not in {q.lower() for q in queries}:
                    queries.append(keyword)
            if len(terms) > 3:
                entity = " ".join(terms[:3])
                if entity.lower() not in {q.lower() for q in queries}:
                    queries.append(entity)
        return queries[: self.queries_per_fact] or [claim[:200]]

    # -- Wikipedia API ------------------------------------------------------
    def search(self, query: str) -> list[dict]:
        cached = self._cached("search", f"{query}|{self.pages_per_query}")
        if cached is not None:
            self.cache_hits += 1
            return cached
        if self.offline_only:
            return []
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": self.pages_per_query,
            "format": "json",
        }
        try:
            resp = requests.get(
                self.api_url,
                params=params,
                headers={"User-Agent": self.user_agent},
                timeout=30,
            )
            self.network_calls += 1
            time.sleep(self.delay)
            if resp.status_code != 200:
                return []
            hits = resp.json().get("query", {}).get("search", [])
            results = [{"title": h.get("title", ""), "pageid": h.get("pageid")} for h in hits]
        except requests.RequestException as exc:
            print(f"[warn] wikipedia search failed for {query!r}: {exc}")
            return []
        self._store("search", f"{query}|{self.pages_per_query}", results)
        return results

    def fetch_page(self, title: str) -> dict:
        cached = self._cached("page", title)
        if cached is not None:
            self.cache_hits += 1
            return cached
        if self.offline_only:
            return {}
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "titles": title,
            "format": "json",
            "redirects": 1,
        }
        try:
            resp = requests.get(
                self.api_url,
                params=params,
                headers={"User-Agent": self.user_agent},
                timeout=30,
            )
            self.network_calls += 1
            time.sleep(self.delay)
            if resp.status_code != 200:
                return {}
            pages = resp.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                if "extract" not in page:
                    continue
                payload = {
                    "title": page.get("title", title),
                    "url": "https://en.wikipedia.org/wiki/"
                    + page.get("title", title).replace(" ", "_"),
                    "extract": page.get("extract", ""),
                }
                self._store("page", title, payload)
                return payload
        except requests.RequestException as exc:
            print(f"[warn] wikipedia fetch failed for {title!r}: {exc}")
        return {}

    # -- paragraphs ---------------------------------------------------------
    def paragraphs(self, page: dict) -> list[dict]:
        out = []
        for block in re.split(r"\n{2,}", page.get("extract", "")):
            block = re.sub(r"\s+", " ", block).strip()
            if block.startswith("==") or len(block) < self.min_chars:
                continue
            out.append({"title": page.get("title", ""), "url": page.get("url", ""), "text": block})
        return out

    # -- public API ---------------------------------------------------------
    def retrieve(self, claim: str) -> tuple[list[Evidence], list[str]]:
        queries = self.generate_queries(claim)
        seen_titles: list[str] = []
        candidates: list[dict] = []
        for query in queries:
            for hit in self.search(query):
                title = hit["title"]
                if title in seen_titles or len(seen_titles) >= self.max_pages:
                    continue
                seen_titles.append(title)
                page = self.fetch_page(title)
                if page:
                    candidates.extend(self.paragraphs(page))

        if not candidates:
            return [], queries

        texts = [c["text"] for c in candidates]
        scorer = tfidf_scores if self.ranker == "tfidf" else bm25_scores
        scores = scorer(claim, texts)
        # Blend in the queries so condition/relation wording also drives ranking.
        for query in queries:
            qs = scorer(query, texts)
            scores = [s + 0.5 * q for s, q in zip(scores, qs)]

        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        evidence: list[Evidence] = []
        for idx, (cand, score) in enumerate(ranked[: self.top_k], start=1):
            evidence.append(
                Evidence(
                    id=f"E{idx}",
                    source="Wikipedia",
                    title=cand["title"],
                    url=cand["url"],
                    snippet=cand["text"][:900],
                    score=round(float(score), 4),
                )
            )
        return evidence, queries

    def stats(self) -> dict:
        return {
            "network_calls": self.network_calls,
            "cache_hits": self.cache_hits,
            "offline_only": self.offline_only,
            "ranker": self.ranker,
        }


def build_retriever(cfg: dict, client: BaseClient | None = None) -> WikipediaRetriever:
    return WikipediaRetriever(cfg, client)
