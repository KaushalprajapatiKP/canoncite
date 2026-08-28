"""Base rate for NMR (paper 5.4): given a WRONG citation drawn from the reranked
candidate set, what is the chance it lands on a declared near-miss distractor by
chance alone? Observed NMR only means something against this number."""
import json, os, sys, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
from canoncite.systems import bm25 as bm25mod, dense, corpus_text, naive_rag
from canoncite.systems.reranked_rag import rerank_retrieve

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
K = 8
tot_slots = tot_hits = 0
per_item = []
for corpus in ["bhagavad_gita", "yoga_sutras"]:
    docs, id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    bm = bm25mod.BM25(docs); dr = dense.DenseRetriever(ROOT, corpus, docs)
    items = naive_rag.load_items(corpus)
    for lang in ["hi", "sa"]:
        for it in items:
            gold = set(it.get("gold_citations") or [])
            dis  = set(it.get("near_miss_distractors") or [])
            if not gold or not dis: continue
            q = naive_rag._question(it, lang)
            top = [c for c, _ in rerank_retrieve(q, bm, dr, id_to_text, k=K)]
            slots = [c for c in top if c not in gold]     # what a wrong pick could land on
            if not slots: continue
            h = sum(1 for c in slots if c in dis)
            tot_slots += len(slots); tot_hits += h
            per_item.append(h/len(slots))
print(f"items scored        : {len(per_item)}")
print(f"pooled base rate    : {tot_hits}/{tot_slots} = {tot_hits/tot_slots:.4f}")
print(f"mean per-item base  : {statistics.mean(per_item):.4f}")
print(f"observed NMR (E2 XL): 0.129   (C 0.082, D 0.115)")
