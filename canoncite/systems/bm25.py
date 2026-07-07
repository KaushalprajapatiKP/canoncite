"""Okapi BM25 over a corpus — pure stdlib, no GPU, no external deps.

This is the lexical retriever behind System A (naive RAG) and one half of System B
(hybrid). It ranks corpus units by BM25 score against a query. Works out-of-the-box
for same-language (English query -> English verse text) retrieval; cross-lingual
retrieval (Hindi query -> English verse) is where dense embeddings (BGE-M3) are
needed and will plug in alongside this.
"""
from __future__ import annotations
import math
import re
from collections import Counter

_TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(s: str) -> list[str]:
    return _TOKEN.findall((s or "").lower())


class BM25:
    def __init__(self, docs: list[tuple[str, str]], k1: float = 1.5, b: float = 0.75):
        """docs: list of (unit_id, text)."""
        self.ids = [d[0] for d in docs]
        self.toks = [tokenize(d[1]) for d in docs]
        self.N = len(docs)
        self.avgdl = (sum(len(t) for t in self.toks) / self.N) if self.N else 0.0
        df: Counter = Counter()
        for t in self.toks:
            df.update(set(t))
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        self.tf = [Counter(t) for t in self.toks]
        self.k1, self.b = k1, b

    def search(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        q = tokenize(query)
        scores = [0.0] * self.N
        for i in range(self.N):
            dl = len(self.toks[i])
            tf = self.tf[i]
            s = 0.0
            for w in q:
                f = tf.get(w)
                if not f:
                    continue
                idf = self.idf.get(w, 0.0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1)))
            scores[i] = s
        order = sorted(range(self.N), key=lambda i: -scores[i])[:k]
        return [(self.ids[i], scores[i]) for i in order]
