"""Stage 0: is the residual failure a query-language problem or a missing-text problem?

The paper's headline is that cross-lingual attribution collapses because retrieval
ranks the gold unit outside the reader's window. That is true of System A. It is not
the whole story by E2, and the per-cell numbers say so plainly:

    ramayana          en  MAR 0.875      guru_granth_sahib  en  MAR 0.900
    ramayana          hi  MAR 0.889      guru_granth_sahib  hi  MAR 0.842
    ramayana          sa  MAR 0.929      guru_granth_sahib  pa  MAR 0.833
    mahabharata       en  MAR 0.667

Those cells fail *in English*. A cross-lingual explanation cannot account for an
English query failing, so something else is going on, and the obvious candidate is
that copyright forced the English translations out of exactly those three corpora
(`canoncite/data/corpora/{ramayana,mahabharata}` are Sanskrit-only, guru_granth_sahib
is Gurmukhi-only). `corpus_text._row_text` concatenates whatever text fields exist,
so for those corpora the retrievable text is native-script only, and an English
question has nothing to lexically match no matter how good the ranker is.

Two hypotheses, and they imply completely different follow-up work:

  H1 QUERY SIDE. The query is in the wrong language. Fix: translate the query.
     Predicts that asking in English rescues the cell.
  H2 DOCUMENT SIDE. The index holds no text in any language the query can reach.
     Fix: machine-translate the corpus. Predicts that asking in English changes
     nothing, and that adding MT English to the index rescues the cell.

This measures both, retrieval-only, no reader, so it is cheap.

The first half costs nothing at all. Every item already stores its original English
question (`item["question"]`), and the non-English variants were produced from it.
So the English question *is* the oracle for query translation: the ceiling any real
MT system could reach. If the oracle does not rescue a cell, no query-side fix will,
and H1 is dead for that cell before a single token is translated.

Usage:
  # free, minutes: does a perfect query translation help at all?
  PYTHONPATH=. python3 -m canoncite.experiments.stage0_translation --oracle

  # one cell, verbose
  PYTHONPATH=. python3 -m canoncite.experiments.stage0_translation --oracle \\
      --corpora ramayana,guru_granth_sahib,mahabharata

Reading the output: `med` is the median rank of the gold unit (lower is better; the
reader sees the top 5). `delta` is oracle-English minus native-query median rank. A
large negative delta means query translation helps and H1 holds. A delta near zero
on a failing cell means H1 is dead there and the problem is missing text.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics

from ..systems import bm25 as bm25mod
from ..systems import corpus_text, dense, hybrid_rag, naive_rag

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KS = [1, 5, 20, 50]
CAND = 50

# Corpora whose released text carries no English, because the only usable English
# rendering is under copyright. These are the cells H2 predicts are unfixable by any
# amount of ranking work.
NO_ENGLISH = ("ramayana", "mahabharata", "guru_granth_sahib")


def _cells(corpora: list[str] | None) -> list[tuple[str, str]]:
    """Every (corpus, qlang) pair that has items, in a stable order."""
    base = os.path.join(ROOT, "canoncite", "data", "items")
    names = corpora or sorted(
        d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
    )
    out = []
    for c in names:
        if not os.path.exists(os.path.join(base, c, "seed_candidates.jsonl")):
            continue
        langs = {"en"}
        for it in naive_rag.load_items(c, None):
            langs |= set((it.get("translations") or {}).keys())
        for l in sorted(langs):
            out.append((c, l))
    return out


def _retriever(corpus: str, docs, retrieval: str):
    """(bm25, dense_or_None). Dense needs faiss + the embedding model, which live on
    the GPU boxes; on a laptop we fall back to BM25 so the diagnostic still runs.
    The fallback is reported, never silent, because BM25-only ranks are not
    comparable to the hybrid ranks the paper quotes."""
    index = bm25mod.BM25(docs)
    if retrieval == "bm25":
        return index, None
    try:
        return index, dense.DenseRetriever(ROOT, corpus, docs)
    except (ImportError, ModuleNotFoundError, OSError) as e:
        print(f"  ! dense retrieval unavailable ({type(e).__name__}: {e}); "
              f"falling back to BM25-only. Ranks are NOT comparable to the "
              f"paper's hybrid figures. Run on the GPU box for those.")
        return index, None


def ranks_for(corpus: str, qlang: str, oracle_en: bool,
              retrieval: str = "hybrid") -> list[int | None]:
    """1-based rank of the gold unit per answerable item, None if outside CAND.

    `oracle_en` swaps the query for the item's original English question while
    leaving the cell's identity alone, which is what makes it a ceiling rather
    than just re-running the English cell.
    """
    docs, _, _ = corpus_text.load_corpus(ROOT, corpus)
    index, dr = _retriever(corpus, docs, retrieval)

    out: list[int | None] = []
    for it in naive_rag.load_items(corpus, None):
        if not bool(it.get("answerable", True)):
            continue
        gold = set(it.get("gold_citations", []))
        if not gold:
            continue
        q = it["question"] if oracle_en else naive_rag._question(it, qlang)
        if dr is not None:
            fused = hybrid_rag.rrf_fuse(
                [index.search(q, k=CAND), dr.search(q, k=CAND)], top=CAND)
        else:
            fused = index.search(q, k=CAND)
        rids = [rid for rid, _ in fused]
        out.append(next((i + 1 for i, rid in enumerate(rids) if rid in gold), None))
    return out


def summarise(ranks: list[int | None]) -> dict:
    found = [r for r in ranks if r is not None]
    return {
        "n": len(ranks),
        "median": statistics.median(found) if found else None,
        **{f"r@{k}": (sum(1 for r in found if r <= k) / len(ranks) if ranks else None)
           for k in KS},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oracle", action="store_true",
                    help="also run the English-question ceiling for every cell")
    ap.add_argument("--corpora", default=None,
                    help="comma-separated subset, default all")
    ap.add_argument("--retrieval", default="hybrid", choices=["hybrid","bm25"],
                    help="hybrid matches the paper; bm25 runs without faiss")
    ap.add_argument("--out", default="results/stage0_translation.jsonl")
    a = ap.parse_args(argv)

    cells = _cells(a.corpora.split(",") if a.corpora else None)
    rows = []
    print(f"  {'corpus':22} {'lang':5} {'n':>4} {'med':>5} {'R@1':>6} {'R@5':>6} "
          f"{'R@50':>6}   {'oracle med':>10} {'delta':>7}")
    for corpus, qlang in cells:
        nat = summarise(ranks_for(corpus, qlang, False, a.retrieval))
        rec = {"corpus": corpus, "qlang": qlang, "retrieval": a.retrieval, "native": nat}
        line = (f"  {corpus:22} {qlang:5} {nat['n']:>4} "
                f"{_f(nat['median']):>5} {_p(nat['r@1']):>6} {_p(nat['r@5']):>6} "
                f"{_p(nat['r@50']):>6}")
        if a.oracle:
            orc = summarise(ranks_for(corpus, qlang, True, a.retrieval))
            rec["oracle_en"] = orc
            d = (None if (orc["median"] is None or nat["median"] is None)
                 else orc["median"] - nat["median"])
            rec["delta_median"] = d
            line += f"   {_f(orc['median']):>10} {_f(d, sign=True):>7}"
        print(line)
        rows.append(rec)

    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n  wrote {a.out}")

    if a.oracle:
        _verdict(rows)
    return 0


def _f(v, sign=False):
    if v is None:
        return "n/a"
    return f"{v:+g}" if sign else f"{v:g}"


def _p(v):
    return "n/a" if v is None else f"{v:.2f}"


def _verdict(rows: list[dict]) -> None:
    """State what the numbers imply, so the decision gate is not left to vibes."""
    print("\n  " + "-" * 64)
    hopeless, rescued = [], []
    for r in rows:
        nat, orc = r["native"], r.get("oracle_en") or {}
        if nat["median"] is None or nat["median"] <= 5:
            continue  # this cell is not failing on rank
        if orc.get("median") is not None and orc["median"] <= 5:
            rescued.append(f"{r['corpus']}/{r['qlang']}")
        else:
            hopeless.append(f"{r['corpus']}/{r['qlang']}")

    print(f"  cells where a PERFECT query translation fixes ranking: {len(rescued)}")
    for c in rescued:
        print(f"      {c}")
    print(f"  cells it does NOT fix: {len(hopeless)}")
    for c in hopeless:
        mark = "  (no English in the released text)" if c.split("/")[0] in NO_ENGLISH else ""
        print(f"      {c}{mark}")

    print("\n  How to read this:")
    print("    Mostly 'rescued'  -> H1. The gap is query language. A query-translation")
    print("                         step is the fix, and it is cheap. A trained")
    print("                         reranker is then hard to justify as novel.")
    print("    Mostly 'not fixed' and concentrated in the no-English corpora -> H2.")
    print("                         The gap is missing text, not ranking. The next")
    print("                         experiment is machine-translating those corpora")
    print("                         into the index, not training a ranker.")


if __name__ == "__main__":
    raise SystemExit(main())
