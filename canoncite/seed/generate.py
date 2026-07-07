"""Generate ID-grounded seed candidate items for a corpus.

Pipeline (BENCHMARK_DESIGN.md §4 step 1):
  1. SAMPLE the gold verse(s) from the frozen corpus_index -> gold is correct by
     construction (the LLM never chooses citations).
  2. Pick near-miss distractors = real, topically-adjacent ids (same container).
  3. Ask the LLM ONLY to write the question text, conditioned on the real verse.
  4. Build an Item (provenance=llm_proposed, verified=false), validate against U.
  5. Write draft candidates for human annotation.

Usage:
  PYTHONPATH=. python canoncite/seed/generate.py --corpus bhagavad_gita \\
      --counts factual=20,retrieval=20,conceptual=20,interpretive=15,unanswerable=15 \\
      --seed 13 --out canoncite/data/items/bhagavad_gita/seed_candidates.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite.corpus_io import load_corpus_index, id_space
from canoncite.items import Item, validate_item
from canoncite.seed import llm

CORPUS_LABEL = {
    "bhagavad_gita": "the Bhagavad Gita", "bible": "the Bible",
    "dhammapada": "the Dhammapada", "thirukkural": "the Thirukkural",
    "yoga_sutras": "the Yoga Sutras of Patanjali", "upanishads": "the Upanishads",
    "constitution_india": "the Constitution of India",
}


def container(cid: str) -> str:
    """Strip the trailing number (and its separator): '2.47'->'2', '1.1.1'->'1.1',
    'Genesis 1:1'->'Genesis 1', 'isha.1'->'isha', '47'->''."""
    return re.sub(r"[.: ]?\d+$", "", cid)


def text_of(rec: dict) -> str:
    return rec.get("text_en") or rec.get("original") or rec.get("sanskrit") or ""


def near_miss(gold_id: str, by_container: dict, all_ids: list, rng, k: int = 3) -> list:
    cont = container(gold_id)
    pool = [i for i in by_container.get(cont, []) if i != gold_id]
    rng.shuffle(pool)
    picks = pool[:k]
    if len(picks) < k:  # top up with random real ids
        extra = [i for i in all_ids if i != gold_id and i not in picks]
        rng.shuffle(extra)
        picks += extra[: k - len(picks)]
    return picks


# ---- per-type prompt builders (LLM writes ONLY the question) ----------------

SYS = ("You write precise question-answering benchmark questions about canonical texts. "
       "You are given the real source text. Return STRICT JSON only, no commentary.")


def p_factual(label, rec):
    return (f"Source — {label}, verse {rec['id']}:\n\"{text_of(rec)}\"\n\n"
            "Write ONE specific factual question whose precise and complete answer is "
            "exactly this verse (and no other). Do not mention the verse number in the question. "
            'Return JSON: {"question": "...", "answer": "..."}')


def p_retrieval(label, rec):
    return (f"Source — {label}, verse {rec['id']}:\n\"{text_of(rec)}\"\n\n"
            "Write ONE 'which verse/passage…' locator question that asks where this idea is "
            "stated. Do not reveal the verse number. "
            'Return JSON: {"question": "Which verse ...?", "answer": "..."}')


def p_conceptual(label, recs):
    block = "\n".join(f"- {r['id']}: \"{text_of(r)}\"" for r in recs)
    return (f"Source — {label}, these verses:\n{block}\n\n"
            "Write ONE conceptual question that requires synthesizing across THESE verses. "
            "Do not mention verse numbers. "
            'Return JSON: {"question": "...", "answer": "..."}')


def p_interpretive(label, rec):
    return (f"Source — {label}, verse {rec['id']}:\n\"{text_of(rec)}\"\n\n"
            "Write ONE open, interpretive question a thoughtful reader might ask about the theme "
            "of this verse — one that has more than one defensible answer. No verse numbers. "
            'Return JSON: {"question": "...", "answer": "..."}')


def p_unanswerable(label, rec):
    return (f"Context — {label} discusses themes like that in: \"{text_of(rec)[:160]}\".\n\n"
            f"Write ONE question that sounds like it belongs to {label} but whose answer is NOT "
            f"contained anywhere in {label} (e.g. a modern topic, or a fact from a different text). "
            "A good system should ABSTAIN rather than cite a verse. "
            'Return JSON: {"question": "...", "why_unanswerable": "..."}')


def gen_one(qtype, label, corpus, recs_with_text, by_container, all_ids, rng, idx):
    gold_rec = rng.choice(recs_with_text)
    if qtype == "conceptual":
        cont = container(gold_rec["id"])
        sibs = [r for r in recs_with_text if container(r["id"]) == cont]
        rng.shuffle(sibs)
        gold_recs = sibs[:3] if len(sibs) >= 2 else [gold_rec]
        gold = [r["id"] for r in gold_recs]
        prompt = p_conceptual(label, gold_recs)
        amb = "medium"
    elif qtype == "factual":
        gold, prompt, amb = [gold_rec["id"]], p_factual(label, gold_rec), "low"
    elif qtype == "retrieval":
        gold, prompt, amb = [gold_rec["id"]], p_retrieval(label, gold_rec), "low"
    elif qtype == "interpretive":
        gold, prompt, amb = [gold_rec["id"]], p_interpretive(label, gold_rec), "high"
    else:  # unanswerable
        gold, prompt, amb = [], p_unanswerable(label, gold_rec), "low"

    obj = llm.chat_json(prompt, system=SYS, temperature=0.7)
    if not obj or not obj.get("question"):
        return None
    must_abstain = qtype == "unanswerable"
    nm = [] if must_abstain else near_miss(gold[0], by_container, all_ids, rng, k=3)
    item = Item(
        id=f"{corpus}-seed-{idx:04d}",
        corpus=corpus,
        question=obj["question"].strip(),
        question_type=qtype,
        gold_citations=gold,
        answerable=not must_abstain,
        ambiguity=amb,
        near_miss_distractors=nm,
        gold_answer=(obj.get("answer") or "").strip(),
        must_abstain=must_abstain,
        abstain_reason=("topic_not_in_corpus" if must_abstain else None),
        provenance={"seed": "llm_proposed", "seed_model": llm.get_config()["model"], "verified": False},
        adjudicated=False,
    )
    return item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--counts", default="factual=5,retrieval=5,conceptual=5,interpretive=3,unanswerable=3")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    counts = dict((k, int(v)) for k, v in (kv.split("=") for kv in args.counts.split(",")))
    rng = random.Random(args.seed)
    label = CORPUS_LABEL.get(args.corpus, f"the {args.corpus}")

    path = f"canoncite/data/corpora/{args.corpus}/corpus_index.jsonl"
    recs = load_corpus_index(path)
    U = id_space(recs)
    all_ids = sorted(U)
    by_container: dict = {}
    for i in all_ids:
        by_container.setdefault(container(i), []).append(i)
    recs_with_text = [r for r in recs if text_of(r).strip()]

    print(f"# {args.corpus}: |U|={len(U)}, with-text={len(recs_with_text)} | {llm.describe()}", file=sys.stderr)

    out_path = args.out or f"canoncite/data/items/{args.corpus}/seed_candidates.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    kept, errs, idx = [], 0, 1
    for qtype, n in counts.items():
        made = 0
        attempts = 0
        while made < n and attempts < n * 3:
            attempts += 1
            it = gen_one(qtype, label, args.corpus, recs_with_text, by_container, all_ids, rng, idx)
            if it is None:
                continue
            issues = validate_item(it, U)
            if any(lvl == "error" for lvl, _ in issues):
                errs += 1
                continue
            kept.append(it)
            idx += 1
            made += 1
            print(f"  [{qtype}] {it.id}: {it.question[:70]}", file=sys.stderr)
        print(f"# {qtype}: kept {made}/{n}", file=sys.stderr)

    with open(out_path, "w", encoding="utf-8") as f:
        for it in kept:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\n# wrote {len(kept)} candidates to {out_path} ({errs} rejected by validator)", file=sys.stderr)


if __name__ == "__main__":
    main()
