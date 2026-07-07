"""Export the review data as static JSON for the Vercel-hosted app.

Produces `canoncite/review/webapp/data/`:
  - corpora.json          : [{corpus, n_items, native}]
  - <corpus>.json         : the items, each enriched with the ACTUAL verse text
                            for its gold + near-miss citations (from corpus_index),
                            so the static frontend needs no backend to show sources.

Run: PYTHONPATH=. python canoncite/review/export_web.py
"""
from __future__ import annotations

import glob
import json
import os

from canoncite.corpus_io import load_corpus_index
from canoncite.items import CORPUS_NATIVE

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ITEMS = os.path.join(ROOT, "canoncite", "data", "items")
CORPORA = os.path.join(ROOT, "canoncite", "data", "corpora")
OUT = os.path.join(os.path.dirname(__file__), "webapp", "data")


def index_map(corpus: str) -> dict[str, dict]:
    return {r["id"]: r for r in load_corpus_index(os.path.join(CORPORA, corpus, "corpus_index.jsonl"))}


def src(idx: dict, cid: str) -> dict:
    r = idx.get(cid, {})
    return {"id": cid, "text_en": r.get("text_en"),
            "original": r.get("original") or r.get("sanskrit"),
            "translit": r.get("transliteration"), "heading": r.get("heading")}


def main():
    os.makedirs(OUT, exist_ok=True)
    catalog = []
    for path in sorted(glob.glob(os.path.join(ITEMS, "*", "seed_candidates.jsonl"))):
        corpus = os.path.basename(os.path.dirname(path))
        idx = index_map(corpus)
        items = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
        for it in items:
            it["_gold_src"] = [src(idx, c) for c in it.get("gold_citations", [])]
            it["_nearmiss_src"] = [src(idx, c) for c in it.get("near_miss_distractors", [])]
        with open(os.path.join(OUT, f"{corpus}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
        catalog.append({"corpus": corpus, "n_items": len(items), "native": CORPUS_NATIVE[corpus]})
        print(f"  {corpus}: {len(items)} items")
    with open(os.path.join(OUT, "corpora.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False)
    total = sum(c["n_items"] for c in catalog)
    print(f"wrote {len(catalog)} corpora, {total} items -> {OUT}")


if __name__ == "__main__":
    main()
