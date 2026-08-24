"""Closed-book base-competence control (paper Table 5.3).

The retrieval-augmented numbers in §5.4 only mean something if we know how much
the reader could already do *without* the corpus. Two distinct confounds need
separating, and a closed-book run separates both:

  1. **Parametric leakage.** These are famous public-domain texts. A reader may
     recall "Gita 2.47" from pretraining, in which case a high RAG score is not
     evidence that retrieval worked. Closed-book accuracy upper-bounds how much
     of the RAG result could be memory rather than retrieval.
  2. **Base language competence.** A model that cannot read a Tamil or Gurmukhi
     question will fail whatever we retrieve. Closed-book per-language accuracy
     tells us whether a cross-lingual drop is a *ranking* failure (our claim,
     §5.4.3) or simply the reader not understanding the query.

No retrieval, no passages: the question is asked directly, and the reader must
cite an ID from the closed ID space or abstain. Scored by the same harness, so
the numbers are directly comparable to Systems A-E2 -- and `retrieved_ids` is
empty by construction, which is what makes MAR-exist interpretable here (any
cited ID had to come from the model's own memory).

Usage:
  PYTHONPATH=. python -m canoncite.systems.closed_book --corpus bhagavad_gita --qlang hi
  PYTHONPATH=. python -m canoncite.systems.sweep --system CB --reader llm ...
"""
from __future__ import annotations
import argparse
import os

from .. import eval as ceval
from . import corpus_text
from .naive_rag import _question, load_items

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# The reader gets the ID *format* (one real example) but never the corpus text.
# Without a format hint a wrong-format answer scores as an abstention, which would
# understate parametric knowledge and flatter our retrieval numbers.
_PROMPT = (
    "You are asked about the canonical text '{corpus}'. Answer from your own knowledge "
    "ONLY -- no passages are provided.\n\n"
    "Cite the exact canonical unit ID your answer relies on, using this corpus's ID "
    "format (for example: '{example_id}'). If you do not know the specific unit, or the "
    "question cannot be answered from this text, set answerable=false and cite nothing. "
    "Do NOT guess an ID you are not confident in -- an abstention is scored better than "
    "a wrong citation.\n\n"
    "Question: {q}\n\n"
    'Return strict JSON: {{"answerable": true|false, "answer": "...", "citations": ["ID", ...]}}'
)


def read_closed_book(question: str, U: set, corpus: str, example_id: str,
                     temperature: float = 0.0) -> dict:
    from ..seed import llm
    from .reader import _as_text, _extract_ids
    prompt = _PROMPT.format(corpus=corpus, q=question, example_id=example_id)
    obj = llm.chat_json(prompt, temperature=temperature) or {}
    answerable = obj.get("answerable", True)
    cited = _extract_ids(obj, U)
    answer = _as_text(obj.get("answer"))
    abstained = (answerable is False) or (not cited and not answer.strip())
    if abstained:
        cited = []
    return {"answer": answer, "cited_ids": cited, "abstained": abstained}


def run(corpus: str, reader: str = "llm", qlang: str = "en",
        limit: int | None = None, **_ignored) -> dict:
    """`reader` is accepted for interface parity with the other systems; only the
    `llm` reader is meaningful closed-book (there is nothing to retrieve, so the
    top1/topk retrieval baselines have no analogue)."""
    if reader != "llm":
        raise ValueError("closed-book control requires --reader llm (no retrieval to rank)")

    _docs, _id_to_text, U = corpus_text.load_corpus(ROOT, corpus)
    items = load_items(corpus, limit)
    example_id = sorted(U)[0] if U else "1.1"

    results, missing_q = [], 0
    for it in items:
        q = _question(it, qlang)
        if qlang != "en" and not (it.get("translations") or {}).get(qlang):
            missing_q += 1
        r = read_closed_book(q, U, corpus, example_id)

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
            retrieved_ids=set(),  # closed book: nothing was retrieved, by construction
        )
        results.append(ceval.score_item(gold, out, U))

    return {
        "corpus": corpus, "system": "CB-closed-book", "reader": reader, "qlang": qlang,
        "k": 0, "n_items": len(items), "n_units": len(U),
        "missing_translations": missing_q, "agg": ceval.aggregate(results),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--reader", default="llm", choices=["llm"])
    ap.add_argument("--qlang", default="en")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    res = run(a.corpus, reader=a.reader, qlang=a.qlang, limit=a.limit)
    print(f"\nClosed-book control — {res['corpus']}  qlang={res['qlang']}  "
          f"items={res['n_items']}  units={res['n_units']}")
    if res["missing_translations"]:
        print(f"  (note: {res['missing_translations']} items had no {res['qlang']} "
              f"question; fell back to en)")
    print(ceval.format_table(res["agg"]))


if __name__ == "__main__":
    main()
