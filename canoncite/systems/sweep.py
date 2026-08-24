"""Run a system across the (corpus x query-language) grid and emit a results table.

Preliminary use: the no-LLM `top1` reader gives a reproducible, GPU-free lower-bound
picture of the cross-lingual citation-attribution gap across all corpora — the first
real CANONCITE numbers and a paper artifact. Swap --reader llm (+ dense retrieval,
later) for the full System-A run.

  PYTHONPATH=. python -m canoncite.systems.sweep --reader top1 --out results/preliminary_top1.md
"""
from __future__ import annotations
import argparse
import json
import os

from . import closed_book
from . import naive_rag
from . import verified_rag
from . import verified_rag2
from . import self_rag
from . import hybrid_rag
from . import reranked_rag

ROOT = naive_rag.ROOT

# corpus -> native language code (matches CORPUS_NATIVE in items.py); en+hi always tried
NATIVE = {
    "bhagavad_gita": "sa", "upanishads": "sa", "yoga_sutras": "sa", "ramayana": "sa",
    "mahabharata": "sa", "thirukkural": "ta", "guru_granth_sahib": "pa",
    "dhammapada": "pi", "constitution_india": None, "bible": None,
}


def _has_items(corpus: str) -> bool:
    p = naive_rag._items_path(corpus)
    return os.path.exists(p) and os.path.getsize(p) > 0


def _load_checkpoint(path: str | None) -> tuple[list[dict], set]:
    """Load rows already computed in a prior run so a flaky-box crash resumes."""
    if not path or not os.path.exists(path):
        return [], set()
    rows, done = [], set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows.append(r)
            done.add((r["corpus"], r["qlang"]))
    return rows, done


def sweep(reader: str, k: int, limit: int | None, corpora: list[str],
          checkpoint: str | None = None, model: str | None = None,
          system: str = "A", retrieval: str = "bm25") -> list[dict]:
    rows, done = _load_checkpoint(checkpoint)
    if done:
        print(f"[resume] {len(done)} (corpus,lang) cells already done — skipping them")
    for corpus in corpora:
        if not _has_items(corpus):
            continue
        langs = ["en", "hi"] + ([NATIVE[corpus]] if NATIVE.get(corpus) else [])
        for lang in langs:
            if (corpus, lang) in done:
                continue
            if system == "CB":  # closed-book control: no retrieval at all (Table 5.3)
                res = closed_book.run(corpus, reader=reader, qlang=lang, limit=limit)
            elif system == "E":  # System E (ours): verify + repair on top of retrieve->read
                res = verified_rag.run(corpus, k=k, qlang=lang, limit=limit, retrieval=retrieval)
            elif system == "E2":  # System E2 (ours v2): joint discriminative exact-ID select
                res = verified_rag2.run(corpus, k=k, qlang=lang, limit=limit, retrieval=retrieval)
            elif system == "D":  # System D (SOTA baseline): Self-RAG + CRAG (prompted)
                res = self_rag.run(corpus, k=k, qlang=lang, limit=limit, retrieval=retrieval)
            elif system == "C":  # System C: hybrid retrieve -> cross-encoder rerank -> reader
                res = reranked_rag.run(corpus, reader=reader, k=k, qlang=lang, limit=limit)
            elif system == "B":  # System B: hybrid BM25+dense (RRF) -> reader
                res = hybrid_rag.run(corpus, reader=reader, k=k, qlang=lang, limit=limit)
            else:              # System A (naive RAG)
                res = naive_rag.run(corpus, reader=reader, k=k, qlang=lang, limit=limit)
            a = res["agg"]
            row = {
                "corpus": corpus, "qlang": lang, "n": res["n_items"],
                "system": system, "reader": reader, "model": model,
                "n_repaired": res.get("n_repaired"), "n_abstained": res.get("n_abstained"),
                "f1_exact": a.get("attr_f1_exact"),
                "mar": a.get("mar"),
                "cer": a.get("cer"),
                "nmr": a.get("nmr"),
                "agg": a,  # full metric block, so we never re-run for a missing column
            }
            rows.append(row)
            if checkpoint:  # durable append the instant a cell finishes
                with open(checkpoint, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[done] {corpus:20s} {lang:3s}  F1={row['f1_exact']}  MAR={row['mar']}")
    return rows


SYSTEM_NAMES = {
    "CB": "closed-book control (no retrieval)",
    "A": "naive RAG (BM25)",
    "B": "hybrid BM25+dense RRF",
    "C": "hybrid + cross-encoder rerank",
    "D": "Self-RAG/CRAG SOTA baseline",
    "E": "exact-ID verify + repair",
    "E2": "joint discriminative exact-ID selector (ours)",
}

# Corpora whose *released* text is native-script only (copyrighted English excluded),
# so an English query has nothing lexical to match under a BM25-only system.
_NATIVE_ONLY = ("ramayana", "mahabharata", "guru_granth_sahib")


def to_markdown(rows: list[dict], reader: str, system: str | None = None,
                k: int | None = None, retrieval: str | None = None) -> str:
    """Render a run's cells as markdown. Header and commentary are derived from
    the run itself -- never hardcoded to one system (that produced reports titled
    "System A ... reader=top1" for every system we ever ran)."""
    first = rows[0] if rows else {}
    system = system or first.get("system") or "?"
    model = first.get("model")
    label = SYSTEM_NAMES.get(system, system)
    reader_desc = f"reader=`{reader}`" + (f", model=`{model}`" if model else "")
    cfg = ", ".join(x for x in (
        f"k={k}" if k else None,
        f"retrieval={retrieval}" if retrieval else None,
    ) if x)

    out = [f"# CANONCITE — System {system}: {label}", "",
           f"{reader_desc}" + (f" · {cfg}" if cfg else ""), "",
           "| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |",
           "|---|---|---:|---:|---:|"]
    for r in rows:
        f1 = "—" if r["f1_exact"] is None else f"{r['f1_exact']:.3f}"
        mar = "—" if r["mar"] is None else f"{r['mar']:.3f}"
        out.append(f"| {r['corpus']} | {r['qlang']} | {r['n']} | {f1} | {mar} |")

    def _avg(field, pred):
        xs = [r[field] for r in rows if pred(r) and r.get(field) is not None]
        return sum(xs) / len(xs) if xs else 0.0
    en_avg = _avg("f1_exact", lambda r: r["qlang"] == "en")
    xl_avg = _avg("f1_exact", lambda r: r["qlang"] != "en")
    en_mar = _avg("mar", lambda r: r["qlang"] == "en")
    xl_mar = _avg("mar", lambda r: r["qlang"] != "en")

    out += ["", "## Summary", "",
            f"- **Cells:** {len(rows)}",
            f"- **English-query mean Attribution F1 (exact):** {en_avg:.3f}  ·  MAR {en_mar:.3f}",
            f"- **Cross-lingual (hi/native) mean Attribution F1 (exact):** {xl_avg:.3f}"
            f"  ·  MAR {xl_mar:.3f}"]
    if en_avg:
        out.append(f"- **Cross-lingual attribution gap:** {en_avg - xl_avg:.3f} absolute "
                   f"({(1 - xl_avg / en_avg) * 100:.0f}% relative drop)")

    notes = []
    if reader == "top1":
        notes.append(
            "- This is a **lexical-only, no-LLM lower bound** (`reader=top1`): it measures only "
            "*does retrieval rank the exact correct unit id first?* An LLM reader goes on top.")
    if system == "A" and reader == "top1" and any(
            r["corpus"] in _NATIVE_ONLY and r["qlang"] == "en" for r in rows):
        notes.append(
            "- **F1 = 0.000 for the native-script-only corpora under English queries** "
            "(Rāmāyaṇa / Mahābhārata / Guru Granth Sahib): by design their *released* text is "
            "native-script only (copyrighted English excluded), so an English query has nothing "
            "lexical to match. These corpora *require* dense/cross-lingual retrieval. An honest "
            "artifact, not a bug.")
    n_rep = sum(r.get("n_repaired") or 0 for r in rows)
    n_abs = sum(r.get("n_abstained") or 0 for r in rows)
    if n_rep or n_abs:
        notes.append(f"- **Verifier activity:** {n_rep} repairs, {n_abs} abstentions across "
                     f"{len(rows)} cells.")
    if notes:
        out += ["", "## How to read this", ""] + notes
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", default="top1", choices=["top1", "topk", "llm"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--checkpoint", default=None,
                    help="JSONL path; append each (corpus,lang) cell as it finishes, resume on restart")
    ap.add_argument("--model", default=None, help="label the reader model in saved rows")
    ap.add_argument("--system", default="A", choices=["A", "B", "C", "D", "E", "E2", "CB"],
                    help="A=naive RAG, B=hybrid BM25+dense (RRF), C=hybrid+cross-encoder rerank, "
                         "D=Self-RAG+CRAG (SOTA baseline), E=verified RAG (binary verify+repair), "
                         "E2=discriminative exact-ID select, CB=closed-book control (no retrieval)")
    ap.add_argument("--retrieval", default="bm25", choices=["bm25", "hybrid", "rerank"],
                    help="retrieval backend for System E (hybrid=E-on-B, rerank=E-on-C)")
    # small corpora first -> paper-usable numbers land fast; huge ones (GGS/Mahabharata) last
    _ORDER = ["yoga_sutras", "bhagavad_gita", "dhammapada", "upanishads", "thirukkural",
              "constitution_india", "ramayana", "bible", "guru_granth_sahib", "mahabharata"]
    ap.add_argument("--corpora", nargs="*", default=_ORDER)
    a = ap.parse_args()
    rows = sweep(a.reader, a.k, a.limit, a.corpora, checkpoint=a.checkpoint,
                 model=a.model, system=a.system, retrieval=a.retrieval)
    md = to_markdown(rows, a.reader, system=a.system, k=a.k, retrieval=a.retrieval)
    print(md)
    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(path.replace(".md", ".json"), "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
        print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
