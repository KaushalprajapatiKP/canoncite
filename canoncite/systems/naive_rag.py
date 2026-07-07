"""System A — naive RAG — end-to-end, scored by the CANONCITE harness.

Pipeline:  question -> retrieve top-k (BM25) -> reader emits cited ids -> score.

Runs at three compute budgets via --reader:
  top1 / topk : NO LLM. Pure-retrieval baselines — validate the whole scoring path
                with zero deps (great for a first real "does retrieval find the verse?"
                number before any GPU/LLM is wired up).
  llm         : the real reader (Ollama by default; any OpenAI-compatible endpoint via
                canoncite/seed/.llm.env). This is System A proper.

Query language: --qlang en|hi|<native> picks which translation of the question is asked
(the gold citations are language-independent), so we get the cross-lingual breakdown
the paper needs.

Usage:
  PYTHONPATH=. python -m canoncite.systems.naive_rag --corpus bhagavad_gita --limit 20 --reader top1
  PYTHONPATH=. python -m canoncite.systems.naive_rag --corpus bhagavad_gita --reader llm --qlang hi
"""
from __future__ import annotations
import argparse
import json
import os

from .. import eval as ceval
from . import bm25 as bm25mod
from . import corpus_text
from . import reader as rdr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _items_path(corpus: str) -> str:
    return os.path.join(ROOT, "canoncite", "data", "items", corpus, "seed_candidates.jsonl")


def load_items(corpus: str, limit: int | None = None) -> list[dict]:
    out = []
    with open(_items_path(corpus), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
            if limit and len(out) >= limit:
                break
    return out


def _question(item: dict, qlang: str) -> str:
    if qlang == "en":
        return item["question"]
    tr = (item.get("translations") or {}).get(qlang) or {}
    return tr.get("question") or item["question"]  # fall back to en if missing


def run(corpus: str, reader: str = "top1", k: int = 5, qlang: str = "en",
        limit: int | None = None) -> dict:
    docs, id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    index = bm25mod.BM25(docs)
    items = load_items(corpus, limit)

    results, missing_q = [], 0
    for it in items:
        q = _question(it, qlang)
        if qlang != "en" and (not (it.get("translations") or {}).get(qlang)):
            missing_q += 1
        retrieved = index.search(q, k=k)
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
        "corpus": corpus, "system": "A-naive", "reader": reader, "qlang": qlang,
        "k": k, "n_items": len(items), "n_units": len(U),
        "missing_translations": missing_q, "agg": agg,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--reader", default="top1", choices=["top1", "topk", "llm"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--qlang", default="en")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    res = run(a.corpus, reader=a.reader, k=a.k, qlang=a.qlang, limit=a.limit)
    print(f"\nSystem A (naive RAG) — {res['corpus']}  reader={res['reader']}  "
          f"qlang={res['qlang']}  k={res['k']}  items={res['n_items']}  units={res['n_units']}")
    if res["missing_translations"]:
        print(f"  (note: {res['missing_translations']} items had no {res['qlang']} question; fell back to en)")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
