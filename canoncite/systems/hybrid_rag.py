"""System B — hybrid RAG: BM25 (lexical) + BGE-M3 (dense) fused by Reciprocal Rank
Fusion, then the LLM reader. Same scoring path as System A.

Why hybrid: BM25 is strong for same-language exact-term queries but blind cross-lingually;
dense (BGE-M3) is strong cross-lingually but fuzzier on exact terms. RRF combines the two
rank lists without tuning score scales — a robust default that should lift the correct
verse into the top-k under Hindi/native queries, which is exactly what System A's naive
BM25 failed to do (and what starved System E's repair step of correct candidates).

  PYTHONPATH=. python -m canoncite.systems.hybrid_rag --corpus bhagavad_gita --qlang hi --reader llm
"""
from __future__ import annotations
import argparse

from .. import eval as ceval
from . import bm25 as bm25mod
from . import corpus_text
from . import dense
from . import naive_rag
from . import reader as rdr

ROOT = naive_rag.ROOT


def rrf_fuse(rank_lists: list[list[tuple[str, float]]], k_rrf: int = 60,
             top: int = 5) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: score(id) = sum 1/(k_rrf + rank) over each ranked list."""
    scores: dict[str, float] = {}
    for ranks in rank_lists:
        for rank, (rid, _) in enumerate(ranks):
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k_rrf + rank + 1)
    fused = sorted(scores.items(), key=lambda x: -x[1])
    return fused[:top]


def run(corpus: str, reader: str = "llm", k: int = 5, qlang: str = "en",
        limit: int | None = None, cand: int = 10) -> dict:
    docs, id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    bm = bm25mod.BM25(docs)
    dr = dense.DenseRetriever(ROOT, corpus, docs)  # embeds once, then cached
    items = naive_rag.load_items(corpus, limit)

    results = []
    for it in items:
        q = naive_rag._question(it, qlang)
        bm_hits = bm.search(q, k=cand)
        dn_hits = dr.search(q, k=cand)
        retrieved = rrf_fuse([bm_hits, dn_hits], top=k)

        if reader == "top1":
            r = rdr.read_top1(q, retrieved, U, corpus)
        elif reader == "topk":
            r = rdr.read_topk(q, retrieved, U, corpus, k=k)
        elif reader == "llm":
            r = rdr.read_llm(q, retrieved, U, corpus, id_to_text)
        else:
            raise ValueError(f"unknown reader {reader!r}")

        gold = ceval.GoldItem(
            id=it["id"], corpus=corpus,
            gold_citations=set(it.get("gold_citations", [])),
            near_miss_distractors=set(it.get("near_miss_distractors", [])),
            must_abstain=bool(it.get("must_abstain", False)),
            answerable=bool(it.get("answerable", True)),
        )
        out = ceval.SystemOutput(
            item_id=it["id"], abstained=r["abstained"],
            cited_ids=set(r["cited_ids"]),
            retrieved_ids={rid for rid, _ in retrieved},
        )
        results.append(ceval.score_item(gold, out, U))

    agg = ceval.aggregate(results)
    return {
        "corpus": corpus, "system": "B-hybrid", "reader": reader, "qlang": qlang,
        "k": k, "cand": cand, "n_items": len(items), "n_units": len(U), "agg": agg,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--reader", default="llm", choices=["top1", "topk", "llm"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--cand", type=int, default=10, help="candidates from each retriever before RRF")
    ap.add_argument("--qlang", default="en")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    res = run(a.corpus, reader=a.reader, k=a.k, qlang=a.qlang, limit=a.limit, cand=a.cand)
    print(f"\nSystem B (hybrid RAG) — {res['corpus']}  reader={res['reader']}  "
          f"qlang={res['qlang']}  k={res['k']}  items={res['n_items']}  units={res['n_units']}")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
