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

# `\w` excludes Unicode categories Mn and Mc, which is what Indic vowel signs and
# viramas are, so a bare \w+ shatters every Devanagari, Gurmukhi or Tamil word at
# each matra: तपःस्वाध्यायनिरतं tokenised as ["तप","स","व","ध","य","यन","रत"].
# Combining marks must stay attached to the letter they modify.
_MARKS = (
    "\u0300-\u036F"          # combining diacriticals (IAST transliteration)
    "\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962-\u0963"   # Devanagari
    "\u0981-\u0983\u09BC\u09BE-\u09CD\u09D7\u09E2-\u09E3"     # Bengali
    "\u0A01-\u0A03\u0A3C\u0A3E-\u0A4D\u0A51\u0A70-\u0A71\u0A75"  # Gurmukhi
    "\u0A81-\u0A83\u0ABC\u0ABE-\u0ACD"                       # Gujarati
    "\u0B01-\u0B03\u0B3C\u0B3E-\u0B57"                       # Oriya
    "\u0B82\u0BBE-\u0BCD\u0BD7"                               # Tamil
    "\u0C00-\u0C04\u0C3E-\u0C56"                             # Telugu
    "\u0C81-\u0C83\u0CBC-\u0CD6"                             # Kannada
    "\u0D00-\u0D03\u0D3B-\u0D57"                             # Malayalam
)
_TOKEN = re.compile(rf"[\w{_MARKS}]+", re.UNICODE)


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
