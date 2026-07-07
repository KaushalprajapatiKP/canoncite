"""System D (SOTA baseline) — Self-RAG + CRAG, inference-time (prompted) formulation.

D is the strong published baseline System E2 must beat. Self-RAG (Asai et al. 2023) and
CRAG (Yan et al. 2024) both add a *reflection/correction* layer on top of retrieve-then-read:

  CRAG   : a retrieval evaluator labels each retrieved passage Correct / Ambiguous /
           Incorrect; incorrect passages are discarded and (in open-domain CRAG) a web
           search is triggered. We run over a CLOSED corpus, so the corrective fallback
           when nothing is relevant is to ABSTAIN (there is no external source to fetch).
  Self-RAG: the model reflects with ISREL (passage relevant?), ISSUP (answer supported by
           the passage?), ISUSE (answer useful?) tokens. Self-RAG's tokens are trained;
           when you cannot fine-tune, the standard baseline is to elicit the same
           judgments by PROMPTING the reader LLM — that is what we do here.

Pipeline:  retrieve top-k (reranked, same as E2 for a fair gate)
           -> ISREL/CRAG: keep passages judged relevant (Correct/Ambiguous)
           -> Self-RAG generate: read over kept passages -> (answer, cited id)
           -> ISSUP: critique whether the cited passage supports the answer;
              if not, switch to the best relevant passage that IS supported;
              else ABSTAIN (corrective: nothing grounded in the closed corpus).

Contrast with E2 (ours): D reflects on each passage INDIVIDUALLY (relevance, then support),
so like E v1's binary check it accepts the first plausible passage and cannot separate a
near-miss neighbour (BG 2.47) from the exact source (2.48). E2's JOINT discriminative
selection can. The D-vs-E2 gap on Misattribution Rate is the paper's central result.
"""
from __future__ import annotations
import argparse

from .. import eval as ceval
from . import bm25 as bm25mod
from . import corpus_text
from . import dense
from . import hybrid_rag
from . import naive_rag
from . import reader as rdr
from . import reranked_rag

ROOT = naive_rag.ROOT

_ISREL_PROMPT = (
    "You are judging whether a retrieved passage is relevant to a question about the "
    "canonical text '{corpus}'.\n"
    "Question: {q}\n"
    "Passage [{cid}]: {ctext}\n\n"
    "Label the passage's relevance to answering the question:\n"
    '  "correct"   = directly relevant, likely contains the answer\n'
    '  "ambiguous" = topically related but may not contain the answer\n'
    '  "incorrect" = not relevant\n'
    'Return strict JSON: {{"rel": "correct"|"ambiguous"|"incorrect"}}'
)

_ISSUP_PROMPT = (
    "Judge whether the answer is supported by the cited passage.\n"
    "Question: {q}\n"
    "Answer: {a}\n"
    "Cited passage [{cid}]: {ctext}\n\n"
    "How well does the passage support the answer?\n"
    '  "full"    = the passage states/entails the answer\n'
    '  "partial" = the passage partially supports it\n'
    '  "no"      = the passage does not support it\n'
    'Return strict JSON: {{"sup": "full"|"partial"|"no"}}'
)


def _isrel(q, cid, ctext, corpus):
    from ..seed import llm
    if not ctext.strip():
        return "incorrect"
    obj = llm.chat_json(_ISREL_PROMPT.format(corpus=corpus, q=q, cid=cid, ctext=ctext),
                        temperature=0.0) or {}
    rel = str(obj.get("rel", "")).lower()
    return rel if rel in ("correct", "ambiguous", "incorrect") else "ambiguous"


def _issup(q, a, cid, ctext):
    from ..seed import llm
    if not ctext.strip():
        return "no"
    obj = llm.chat_json(_ISSUP_PROMPT.format(q=q, a=a or "(the cited verse)", cid=cid,
                                             ctext=ctext), temperature=0.0) or {}
    sup = str(obj.get("sup", "")).lower()
    return sup if sup in ("full", "partial", "no") else "no"


def read_self_rag(question, retrieved, U, corpus, id_to_text):
    """System D reader: CRAG relevance filter -> Self-RAG generate -> ISSUP critique."""
    # 1) ISREL / CRAG: keep passages judged relevant (Correct or Ambiguous), in rank order.
    kept = []
    for cid, _ in retrieved:
        rel = _isrel(question, cid, id_to_text.get(cid, ""), corpus)
        if rel in ("correct", "ambiguous"):
            kept.append((cid, id_to_text.get(cid, "")))
    if not kept:
        # CRAG corrective fallback (no web over a closed corpus) -> abstain.
        return {"answer": "", "cited_ids": [], "abstained": True,
                "base_cited": [], "repaired": False}

    # 2) Self-RAG generate over the kept (relevant) passages.
    kept_ranked = [(cid, 0.0) for cid, _ in kept]
    base = rdr.read_llm(question, kept_ranked, U, corpus, id_to_text)
    if base["abstained"] or not base["answer"].strip():
        return {"answer": base["answer"], "cited_ids": [], "abstained": True,
                "base_cited": base["cited_ids"], "repaired": False}
    answer = base["answer"]
    proposed = list(base["cited_ids"])

    # 3) ISSUP: keep a proposed citation only if the passage supports the answer.
    for c in proposed:
        if _issup(question, answer, c, id_to_text.get(c, "")) in ("full", "partial"):
            return {"answer": answer, "cited_ids": [c], "abstained": False,
                    "base_cited": proposed, "repaired": False}

    # 4) Corrective: switch to the best relevant passage that IS supported.
    tried = set(proposed)
    for cid, ctext in kept:
        if cid in tried:
            continue
        tried.add(cid)
        if _issup(question, answer, cid, ctext) in ("full", "partial"):
            return {"answer": answer, "cited_ids": [cid], "abstained": False,
                    "base_cited": proposed, "repaired": True}

    # 5) Nothing supported -> abstain.
    return {"answer": answer, "cited_ids": [], "abstained": True,
            "base_cited": proposed, "repaired": True}


def run(corpus: str, k: int = 8, qlang: str = "en", limit: int | None = None,
        retrieval: str = "rerank", cand: int = 50) -> dict:
    docs, id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    index = bm25mod.BM25(docs)
    dr = dense.DenseRetriever(ROOT, corpus, docs) if retrieval in ("hybrid", "rerank") else None
    items = naive_rag.load_items(corpus, limit)

    results, n_repaired, n_abstain = [], 0, 0
    for it in items:
        q = naive_rag._question(it, qlang)
        if retrieval == "rerank":
            retrieved = reranked_rag.rerank_retrieve(q, index, dr, id_to_text, k=k, cand=cand)
        elif retrieval == "hybrid":
            retrieved = hybrid_rag.rrf_fuse([index.search(q, k=cand), dr.search(q, k=cand)], top=k)
        else:
            retrieved = index.search(q, k=k)
        r = read_self_rag(q, retrieved, U, corpus, id_to_text)
        n_repaired += bool(r.get("repaired"))
        n_abstain += bool(r["abstained"])

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
        "corpus": corpus, "system": "D-selfrag-crag", "reader": "llm", "qlang": qlang,
        "retrieval": retrieval, "k": k, "n_items": len(items), "n_units": len(U),
        "n_repaired": n_repaired, "n_abstained": n_abstain, "agg": agg,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--qlang", default="en")
    ap.add_argument("--retrieval", default="rerank", choices=["bm25", "hybrid", "rerank"])
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    res = run(a.corpus, k=a.k, qlang=a.qlang, limit=a.limit, retrieval=a.retrieval)
    print(f"\nSystem D (Self-RAG+CRAG) — {res['corpus']}  qlang={res['qlang']}  "
          f"k={res['k']}  items={res['n_items']}  repaired={res['n_repaired']}  "
          f"abstained={res['n_abstained']}")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
