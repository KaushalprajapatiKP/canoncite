"""Retrieval-only recall@k for the gold verse — sizes E's repair headroom.

No LLM: just BM25+dense(RRF) vs the gold citation. Tells us, for answerable items,
what fraction have the gold verse within the top-k candidates at k in {5,10,20,50}.
If recall jumps from k=5 to k=20, widening E's candidate pool (so repair can reach
the gold) is the fix — not the verifier.

Usage (box): PYTHONPATH=. python3 -m canoncite.systems.recall_probe --corpus bhagavad_gita --qlang hi
"""
from __future__ import annotations
import argparse

from . import bm25 as bm25mod
from . import corpus_text
from . import dense
from . import hybrid_rag
from . import naive_rag
from . import verified_rag as E

KS = [5, 10, 20, 50]


def probe(corpus: str, qlang: str, retrieval: str = "hybrid", cand: int = 50):
    docs, id_to_text, U = corpus_text.load_corpus(E.ROOT, corpus)
    index = bm25mod.BM25(docs)
    dr = dense.DenseRetriever(E.ROOT, corpus, docs) if retrieval == "hybrid" else None
    items = naive_rag.load_items(corpus, None)

    ans = 0
    hits = {k: 0 for k in KS}
    ranks = []  # rank of gold when found (1-based), else None
    for it in items:
        if not bool(it.get("answerable", True)):
            continue
        gold = set(it.get("gold_citations", []))
        if not gold:
            continue
        ans += 1
        q = naive_rag._question(it, qlang)
        if retrieval == "hybrid":
            fused = hybrid_rag.rrf_fuse(
                [index.search(q, k=cand), dr.search(q, k=cand)], top=max(KS))
        else:
            fused = index.search(q, k=max(KS))
        rids = [rid for rid, _ in fused]
        rank = next((i + 1 for i, rid in enumerate(rids) if rid in gold), None)
        ranks.append(rank)
        for k in KS:
            if rank is not None and rank <= k:
                hits[k] += 1
    return ans, hits, ranks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--qlang", default="hi")
    ap.add_argument("--retrieval", default="hybrid")
    a = ap.parse_args()
    ans, hits, ranks = probe(a.corpus, a.qlang, retrieval=a.retrieval)
    print(f"\n=== recall@k (gold verse) — {a.corpus} qlang={a.qlang} {a.retrieval} ===")
    print(f"answerable items with gold: {ans}")
    for k in KS:
        print(f"  recall@{k:<2}: {hits[k]}/{ans} = {hits[k]/ans:.3f}")
    found = [r for r in ranks if r is not None]
    never = sum(1 for r in ranks if r is None)
    print(f"  gold never in top-{max(KS)}: {never}/{ans} = {never/ans:.3f}  (hard retrieval floor)")
    if found:
        found.sort()
        print(f"  median gold rank when found: {found[len(found)//2]}")


if __name__ == "__main__":
    main()
