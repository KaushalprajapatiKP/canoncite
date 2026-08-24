"""Automatic second-pass annotation of the verification sample (NOT a human).

Purpose: with one human annotator we cannot report inter-annotator agreement,
which needs two *independent people*. What we can report -- and what is useful
in its own right -- is whether an automatic checker tracks human judgement on
the same items. That is a **human--model agreement** measurement, and it is only
honest if the machine verdicts can never be mistaken for, or counted as, a
second human.

Three safeguards enforce that, deliberately redundantly:

  1. Output goes to `canoncite/data/reviews_auto/`, a directory
     `agreement.load_verdicts()` does not read. Machine verdicts are therefore
     invisible to the human agreement and adjudication paths by default.
  2. Every verdict carries `reviewer = "auto:<model>"` and
     `annotator_type = "model"`, so it is self-identifying wherever it surfaces.
  3. `adjudicate.py` skips any reviewer whose id begins `auto:` when counting
     reviewers, so even a misplaced file cannot promote an item to `verified`.

Run (needs an OpenAI-compatible endpoint via canoncite/seed/.llm.env*):
    PYTHONPATH=. python canoncite/agreement/auto_annotate.py [--corpus X] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ITEMS_DIR = os.path.join(ROOT, "canoncite", "data", "items")
CORPORA_DIR = os.path.join(ROOT, "canoncite", "data", "corpora")
AUTO_DIR = os.path.join(ROOT, "canoncite", "data", "reviews_auto")
SAMPLE = os.path.join(ITEMS_DIR, "_review_sample_v1.json")

_PROMPT = """You are checking a benchmark item for a citation-attribution dataset built \
over the canonical text '{corpus}'.

The item claims that the question below is answered by a specific unit of the text.
Your job is to check whether the GOLD CITATION is the correct unit for that question.

Question (English): {q_en}
{q_other}
Question type: {qtype}

GOLD CITATION: {gold}
Text of the gold unit:
{gold_text}

Other nearby units that were flagged as plausible-but-wrong (near-miss distractors):
{nearmiss}

Decide ONE of:
  "approve" -- the gold citation is the correct unit for this question.
  "edit"    -- a different unit in the list above is the correct one; give its ID.
  "reject"  -- the item is broken (question unanswerable from this text, or no
               listed unit is correct).

An item whose question type is "unanswerable" SHOULD have no gold citation; approve \
it if it correctly has none.

Return strict JSON only:
{{"status": "approve"|"edit"|"reject", "gold_citations": ["ID", ...], "reason": "one sentence"}}"""


def _load_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def _corpus_index(corpus: str) -> dict:
    path = os.path.join(CORPORA_DIR, corpus, "corpus_index.jsonl")
    return {r["id"]: r for r in _load_jsonl(path)}


def _unit_text(rec: dict) -> str:
    parts = [rec.get("text_en"), rec.get("original") or rec.get("sanskrit"),
             rec.get("transliteration")]
    return " / ".join(p for p in parts if p) or "(no text)"


def annotate_item(item: dict, idx: dict, model_label: str) -> dict:
    from canoncite.seed import llm

    gold = item.get("gold_citations") or []
    gold_text = "\n".join(f"[{g}] {_unit_text(idx.get(g, {}))}" for g in gold) or "(none -- unanswerable item)"
    nm = item.get("near_miss_distractors") or []
    nearmiss = "\n".join(f"[{n}] {_unit_text(idx.get(n, {}))}" for n in nm) or "(none)"
    tr = item.get("translations") or {}
    q_other = "\n".join(
        f"Question ({lang}): {(tr.get(lang) or {}).get('question')}"
        for lang in tr if (tr.get(lang) or {}).get("question")
    )

    prompt = _PROMPT.format(
        corpus=item.get("corpus", "?"), q_en=item.get("question", ""),
        q_other=q_other, qtype=item.get("question_type", "?"),
        gold=", ".join(gold) or "(none)", gold_text=gold_text, nearmiss=nearmiss,
    )
    obj = llm.chat_json(prompt, temperature=0.0) or {}

    status = str(obj.get("status", "")).strip().lower()
    if status not in ("approve", "edit", "reject"):
        status = "reject"  # unparseable -> conservative, and visible in the reason
    v = {
        "reviewer": f"auto:{model_label}",
        "annotator_type": "model",          # never a human; see module docstring
        "corpus": item["corpus"],
        "item_id": item["id"],
        "status": status,
        "notes": str(obj.get("reason", ""))[:400],
        "ts": int(time.time()),
    }
    if status == "edit":
        ids = obj.get("gold_citations") or []
        if isinstance(ids, str):
            ids = [ids]
        v["edits"] = {"gold_citations": [str(i).strip() for i in ids]}
    return v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model-label", default=os.environ.get("CANONCITE_LLM_MODEL", "model"))
    a = ap.parse_args(argv)

    with open(SAMPLE, encoding="utf-8") as fh:
        sample = json.load(fh)["by_corpus"]
    corpora = [a.corpus] if a.corpus else sorted(sample)

    total = done = 0
    for corpus in corpora:
        keep = set(sample.get(corpus, []))
        if not keep:
            continue
        idx = _corpus_index(corpus)
        items = [i for i in _load_jsonl(os.path.join(ITEMS_DIR, corpus, "seed_candidates.jsonl"))
                 if i["id"] in keep]
        outdir = os.path.join(AUTO_DIR, corpus)
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, f"{a.model_label.replace('/', '_')}.jsonl")

        existing = {v["item_id"]: v for v in (_load_jsonl(outfile) if os.path.exists(outfile) else [])}
        for it in items:
            total += 1
            if it["id"] in existing:      # resumable: re-running skips completed items
                continue
            if a.limit and done >= a.limit:
                break
            existing[it["id"]] = annotate_item(it, idx, a.model_label)
            done += 1
            with open(outfile, "w", encoding="utf-8") as fh:   # durable after each item
                for k in sorted(existing):
                    fh.write(json.dumps(existing[k], ensure_ascii=False, sort_keys=True) + "\n")
            print(f"[auto] {corpus:20s} {it['id']:20s} {existing[it['id']]['status']}")

    print(f"\nannotated {done} new item(s); {total} in sample scope -> {AUTO_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
