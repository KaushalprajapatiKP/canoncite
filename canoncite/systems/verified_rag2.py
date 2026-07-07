"""System E2 (OURS, v2) — discriminative exact-ID attribution + repair.

Motivation (from the C error analysis): once retrieval RANKING is fixed (System C =
cross-encoder rerank), the residual misattributions are dominated by NEAR-MISSES — the
system cites a verse adjacent to / on the same theme as the gold (BG 2.47 vs 2.48). A
cross-encoder reranker cannot fix this: it scores neighboring verses as almost equally
relevant. And System E (v1) cannot either: its verifier is a *binary, per-candidate*
grounded check taken in rank order, so it accepts the first topically-plausible verse
and stops — exactly the near-miss it should reject.

E2's fix is the paper's actual claim — *exact-ID* attribution: replace the binary check
with a JOINT DISCRIMINATIVE selection. Show the reader ALL top candidates side by side
and force a single choice — "which ONE verse *precisely states* the answer; verses merely
on the same theme are NOT the exact source; or none." Seeing 2.47 and 2.48 together is
what lets the model pick the exact one. This is a discrimination a topical reranker
(and a lenient binary verifier) structurally cannot make.

Pipeline:  question -> retrieve top-k (reranked) -> base reader proposes (answer)
           -> DISCRIMINATIVE SELECT the single exact-source id among candidates
           -> cite it / REPAIR (if it differs from the reader's cite) / ABSTAIN (none).

One LLM selection call (vs up to k binary calls in E v1) — cheaper and more precise.
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

_SELECT_PROMPT = (
    "You are precisely attributing an answer to its EXACT source passage in the "
    "canonical text '{corpus}'.\n"
    "Question: {q}\n"
    "Answer: {a}\n\n"
    "Candidate passages:\n{candidates}\n\n"
    "Exactly ONE of these passages — or NONE — is the precise source that actually "
    "STATES the answer. Neighboring passages may share the same theme or vocabulary but "
    "are NOT the exact source. Compare them against each other and choose the single "
    "passage whose text most directly and specifically states the answer. If no passage "
    "specifically states it, choose null (do not settle for a merely on-topic passage).\n"
    'Return strict JSON: {{"best_id": "<ID>" or null}}'
)


def _select(question, answer, candidates, U, corpus, temperature=0.0):
    """Joint discriminative selection of the single exact-source id (or None)."""
    from ..seed import llm
    block = "\n".join(f"[{cid}] {text}" for cid, text in candidates if text.strip())
    if not block:
        return None
    prompt = _SELECT_PROMPT.format(corpus=corpus, q=question,
                                   a=answer or "(the cited verse)", candidates=block)
    obj = llm.chat_json(prompt, temperature=temperature) or {}
    best = obj.get("best_id")
    if best is None:
        return None
    best = str(best).strip().strip("[]")
    cand_ids = {cid for cid, _ in candidates}
    return best if (best in U and best in cand_ids) else None


def read_verified2(question, retrieved, U, corpus, id_to_text):
    """System E2 reader: base propose -> joint discriminative select -> repair/abstain."""
    base = rdr.read_llm(question, retrieved, U, corpus, id_to_text)
    if base["abstained"] or not base["answer"].strip():
        return {"answer": base["answer"], "cited_ids": [], "abstained": True,
                "base_cited": base["cited_ids"], "repaired": False}

    candidates = [(cid, id_to_text.get(cid, "")) for cid, _ in retrieved]
    best = _select(question, base["answer"], candidates, U, corpus)
    if best is None:
        # No candidate precisely states the answer -> abstain rather than misattribute.
        return {"answer": base["answer"], "cited_ids": [], "abstained": True,
                "base_cited": base["cited_ids"], "repaired": True}
    return {"answer": base["answer"], "cited_ids": [best], "abstained": False,
            "base_cited": base["cited_ids"], "repaired": [best] != list(base["cited_ids"])}


def run(corpus: str, k: int = 8, qlang: str = "en", limit: int | None = None,
        retrieval: str = "rerank", cand: int = 50) -> dict:
    # k=8 (not 5): give the discriminator the gold's NEIGHBORHOOD (gold + adjacent
    # near-misses) to compare against; retrieval defaults to 'rerank' (E2-on-C).
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
        r = read_verified2(q, retrieved, U, corpus, id_to_text)
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
        "corpus": corpus, "system": "E2-discriminative", "reader": "llm", "qlang": qlang,
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
    print(f"\nSystem E2 (discriminative) — {res['corpus']}  qlang={res['qlang']}  "
          f"k={res['k']}  items={res['n_items']}  repaired={res['n_repaired']}  "
          f"abstained={res['n_abstained']}")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
