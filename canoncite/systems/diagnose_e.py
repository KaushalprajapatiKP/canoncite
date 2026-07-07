"""Diagnose System E over-abstention: per-item trace of verify/repair/abstain.

Decomposes E's abstentions cross-lingually to find the cause. The key question:
when E abstains on an ANSWERABLE item whose GOLD verse WAS retrieved, did the base
reader already cite that gold verse only for the grounding VERIFIER to reject it?
That is a verifier false-negative — the real driver of over-abstention.

Usage (on the GPU box, LLM required):
  PYTHONPATH=. python3 -m canoncite.systems.diagnose_e --corpus bhagavad_gita --qlang hi
"""
from __future__ import annotations
import argparse
import json

from . import bm25 as bm25mod
from . import corpus_text
from . import dense
from . import hybrid_rag
from . import naive_rag
from . import reader as rdr
from . import verified_rag as E


def diagnose(corpus: str, qlang: str, k: int = 5, cand: int = 10,
             retrieval: str = "hybrid", limit: int | None = None):
    docs, id_to_text, U = corpus_text.load_corpus(E.ROOT, corpus)
    index = bm25mod.BM25(docs)
    dr = dense.DenseRetriever(E.ROOT, corpus, docs) if retrieval == "hybrid" else None
    items = naive_rag.load_items(corpus, limit)

    rows = []
    for it in items:
        q = naive_rag._question(it, qlang)
        if retrieval == "hybrid":
            retrieved = hybrid_rag.rrf_fuse(
                [index.search(q, k=cand), dr.search(q, k=cand)], top=k)
        else:
            retrieved = index.search(q, k=k)
        rids = [rid for rid, _ in retrieved]
        gold = set(it.get("gold_citations", []))
        answerable = bool(it.get("answerable", True))
        gold_retrieved = bool(gold & set(rids))

        base = rdr.read_llm(q, retrieved, U, corpus, id_to_text)
        base_cited = list(base["cited_ids"])
        base_cited_gold = bool(gold & set(base_cited))

        # verifier verdict on the base-cited gold id(s), in isolation
        verify_gold = None
        for c in base_cited:
            if c in gold:
                verify_gold = E._verify(q, base["answer"], c, id_to_text.get(c, ""))
                break

        # full E decision
        r = E.read_verified(q, retrieved, U, corpus, id_to_text)
        final_cited = list(r["cited_ids"])
        cited_gold = bool(gold & set(final_cited))

        rows.append({
            "id": it["id"], "answerable": answerable, "gold_retrieved": gold_retrieved,
            "base_abstained": base["abstained"], "base_cited_gold": base_cited_gold,
            "verify_gold": verify_gold,            # verifier's verdict on the gold id
            "e_abstained": r["abstained"], "e_repaired": bool(r.get("repaired")),
            "cited_gold": cited_gold,
        })
    return rows


def summarize(rows):
    n = len(rows)
    ans = [r for r in rows if r["answerable"]]
    gr = [r for r in ans if r["gold_retrieved"]]
    # over-abstention: answerable + gold retrieved, yet E abstained
    over = [r for r in gr if r["e_abstained"]]
    # smoking gun: base cited the gold, verifier rejected it -> forced away from gold
    verifier_fn = [r for r in gr if r["base_cited_gold"] and r["verify_gold"] is False]
    # base cited gold and E still lost it (abstain or repaired away)
    lost_gold = [r for r in gr if r["base_cited_gold"] and not r["cited_gold"]]
    print(f"N={n}  answerable={len(ans)}  gold_retrieved(answerable)={len(gr)}")
    print(f"  base_abstained            : {sum(r['base_abstained'] for r in ans)}")
    print(f"  E_abstained (all)         : {sum(r['e_abstained'] for r in rows)}")
    print(f"  OVER-ABSTAIN (ans+goldret): {len(over)}  <- E threw away a recoverable item")
    print(f"  base CITED gold but verifier REJECTED it : {len(verifier_fn)}  <- verifier false-neg")
    print(f"  base cited gold but E LOST it (final)    : {len(lost_gold)}")
    print()
    print("  --- items where base cited gold but E lost it ---")
    for r in lost_gold:
        print(f"    {r['id']:>10}  verify_gold={r['verify_gold']}  "
              f"e_abstained={r['e_abstained']}  e_repaired={r['e_repaired']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--qlang", default="hi")
    ap.add_argument("--retrieval", default="hybrid")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dump", default=None, help="write per-item rows as jsonl")
    a = ap.parse_args()
    rows = diagnose(a.corpus, a.qlang, retrieval=a.retrieval, limit=a.limit)
    if a.dump:
        with open(a.dump, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n=== System E diagnosis: {a.corpus} qlang={a.qlang} retrieval={a.retrieval} ===")
    summarize(rows)


if __name__ == "__main__":
    main()
