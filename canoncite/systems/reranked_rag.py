"""System C — reranked RAG: hybrid retrieve (wide) -> cross-encoder rerank -> reader.

Pipeline:  hybrid BM25+dense RRF over a WIDE candidate pool (cand=50, where recall is
           93-99%) -> BGE-reranker-v2-m3 re-scores every candidate -> keep top-k=5 ->
           LLM reader. The reranker's job is to move the gold verse from its deep hybrid
           rank (median 7-13 cross-lingually) into the top-5 the reader actually reads.

This is the ranking fix the k-sweep motivated: recall is already there at depth; the
problem is order. Feeds the same reader as B, and the same verify/repair as E (E-on-C).
"""
from __future__ import annotations
import argparse

from .. import eval as ceval
from . import bm25 as bm25mod
from . import corpus_text
from . import dense
from . import hybrid_rag
from . import naive_rag
from . import rerank as rrk
from . import reader as rdr

ROOT = naive_rag.ROOT


def rerank_retrieve(q, bm, dr, id_to_text, k=5, cand=50):
    """Wide hybrid recall -> cross-encoder rerank -> top-k [(id, score)].

    Shared by System C (this module) and System E-on-C (verified_rag, retrieval='rerank').
    """
    fused = hybrid_rag.rrf_fuse([bm.search(q, k=cand), dr.search(q, k=cand)], top=cand)
    candidates = [(rid, id_to_text.get(rid, "")) for rid, _ in fused]
    return rrk.rerank(q, candidates, top=k)


def run(corpus: str, reader: str = "llm", k: int = 5, qlang: str = "en",
        limit: int | None = None, cand: int = 50) -> dict:
    docs, id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    bm = bm25mod.BM25(docs)
    dr = dense.DenseRetriever(ROOT, corpus, docs)
    items = naive_rag.load_items(corpus, limit)

    results = []
    for it in items:
        q = naive_rag._question(it, qlang)
        retrieved = rerank_retrieve(q, bm, dr, id_to_text, k=k, cand=cand)

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
        "corpus": corpus, "system": "C-reranked", "reader": reader, "qlang": qlang,
        "k": k, "cand": cand, "n_items": len(items), "n_units": len(U), "agg": agg,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--reader", default="llm", choices=["top1", "topk", "llm"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--cand", type=int, default=50, help="wide pool reranked down to k")
    ap.add_argument("--qlang", default="en")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    res = run(a.corpus, reader=a.reader, k=a.k, qlang=a.qlang, limit=a.limit, cand=a.cand)
    print(f"\nSystem C (reranked RAG) — {res['corpus']}  reader={res['reader']}  "
          f"qlang={res['qlang']}  k={res['k']}  cand={res['cand']}  items={res['n_items']}")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
