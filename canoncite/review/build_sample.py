"""Select the human-verification sample (BENCHMARK_DESIGN.md §4, Step 2).

Full verification of all 622 items is not reachable before the v1 deadline, so we
verify a *stratified sample* and report agreement on it, stating the coverage
plainly in the paper. This script picks that sample deterministically so the
selection is reproducible from the repo alone.

Scope: only corpora whose items can be read by the available reviewers
(English / Hindi / Devanagari Sanskrit). Thirukkural (Tamil), Guru Granth Sahib
(Gurmukhi) and Dhammapada (Pali) are excluded for lack of a script-competent
reviewer; that exclusion is a stated limitation, not a silent omission.

Allocation: proportional across corpora by item count, stratified within each
corpus by question_type, with floors on the two label classes the benchmark
turns on -- `unanswerable` items (abstention axis) and items carrying
near-miss distractors (the near-miss discrimination axis).

Run:
    PYTHONPATH=. python canoncite/review/build_sample.py [--n 120] [--out PATH]

Output: canoncite/data/items/_review_sample_v1.json
    {"version", "seed", "n_requested", "n_selected", "criteria",
     "excluded_corpora", "by_corpus": {corpus: [item_id, ...]}}
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ITEMS_DIR = os.path.join(ROOT, "canoncite", "data", "items")
DEFAULT_OUT = os.path.join(ITEMS_DIR, "_review_sample_v1.json")

# Corpora reviewable with English / Hindi / Devanagari-Sanskrit competence.
REVIEWABLE = (
    "bhagavad_gita", "bible", "constitution_india", "mahabharata",
    "ramayana", "upanishads", "yoga_sutras",
)
EXCLUDED = {
    "thirukkural": "Tamil script -- no script-competent reviewer available",
    "guru_granth_sahib": "Gurmukhi script -- no script-competent reviewer available",
    "dhammapada": "Pali -- no script-competent reviewer available",
}

SEED = 20260824  # the date the sample was drawn; fixed so the draw is reproducible
MIN_UNANSWERABLE = 12  # abstention axis needs enough must-abstain items to be read
MIN_NEAR_MISS = 24     # near-miss discrimination is the paper's core claim


def _load(corpus: str) -> list[dict]:
    path = os.path.join(ITEMS_DIR, corpus, "seed_candidates.jsonl")
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def _is_unanswerable(it: dict) -> bool:
    return bool(it.get("must_abstain")) or not it.get("gold_citations")


def _has_near_miss(it: dict) -> bool:
    return bool(it.get("near_miss_distractors"))


def _quota(pool_sizes: dict[str, int], n: int) -> dict[str, int]:
    """Proportional allocation with largest-remainder rounding, >=1 per corpus."""
    total = sum(pool_sizes.values())
    exact = {c: n * size / total for c, size in pool_sizes.items()}
    base = {c: max(1, int(v)) for c, v in exact.items()}
    # largest remainder distributes the rounding slack
    slack = n - sum(base.values())
    order = sorted(exact, key=lambda c: exact[c] - int(exact[c]), reverse=True)
    i = 0
    while slack > 0 and order:
        c = order[i % len(order)]
        if base[c] < pool_sizes[c]:
            base[c] += 1
            slack -= 1
        i += 1
        if i > 10_000:  # pools exhausted
            break
    return base


def build(n: int = 120) -> dict:
    rng = random.Random(SEED)
    pools = {c: _load(c) for c in REVIEWABLE}
    quota = _quota({c: len(v) for c, v in pools.items()}, n)

    selected: dict[str, list[str]] = {}
    for corpus, items in pools.items():
        want = quota[corpus]
        # stratify by question_type; sort by id first so the draw is order-independent
        by_type: dict[str, list[dict]] = defaultdict(list)
        for it in sorted(items, key=lambda x: x["id"]):
            by_type[it.get("question_type") or "unknown"].append(it)
        for bucket in by_type.values():
            rng.shuffle(bucket)

        picked: list[dict] = []
        types = sorted(by_type)
        # round-robin across question types -> even coverage of the taxonomy
        while len(picked) < want and any(by_type[t] for t in types):
            for t in types:
                if len(picked) >= want:
                    break
                if by_type[t]:
                    picked.append(by_type[t].pop())
        selected[corpus] = sorted(it["id"] for it in picked)

    # --- enforce the label floors by swapping, never by growing past n ----------
    index = {it["id"]: it for items in pools.values() for it in items}
    chosen = {i for ids in selected.values() for i in ids}

    def _top_up(predicate, floor: int, label: str):
        have = sum(1 for i in chosen if predicate(index[i]))
        if have >= floor:
            return have
        candidates = sorted(
            (it["id"] for it in index.values()
             if it["id"] not in chosen and predicate(it)
             and it["corpus"] in selected),
        )
        rng.shuffle(candidates)
        # drop the most over-represented plain items to make room
        droppable = sorted(
            (i for i in chosen
             if not _is_unanswerable(index[i]) and not _has_near_miss(index[i])),
        )
        rng.shuffle(droppable)
        while have < floor and candidates and droppable:
            add, rm = candidates.pop(), droppable.pop()
            c_add, c_rm = index[add]["corpus"], index[rm]["corpus"]
            selected[c_rm].remove(rm)
            chosen.discard(rm)
            selected[c_add].append(add)
            chosen.add(add)
            have += 1
        if have < floor:
            print(f"  ! could not reach {label} floor {floor}: only {have}")
        return have

    n_unans = _top_up(_is_unanswerable, MIN_UNANSWERABLE, "unanswerable")
    n_near = _top_up(_has_near_miss, MIN_NEAR_MISS, "near-miss")

    for c in selected:
        selected[c] = sorted(selected[c])

    return {
        "version": "v1",
        "seed": SEED,
        "n_requested": n,
        "n_selected": sum(len(v) for v in selected.values()),
        "criteria": {
            "reviewable_scope": "English / Hindi / Devanagari-Sanskrit only",
            "allocation": "proportional by corpus size, stratified by question_type",
            "min_unanswerable": MIN_UNANSWERABLE,
            "n_unanswerable": n_unans,
            "min_near_miss": MIN_NEAR_MISS,
            "n_near_miss": n_near,
            "double_annotated": True,
        },
        "excluded_corpora": EXCLUDED,
        "by_corpus": selected,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=120, help="sample size (default 120)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)

    sample = build(a.n)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(sample, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"CANONCITE human-verification sample -> {os.path.relpath(a.out, ROOT)}")
    print(f"  requested {sample['n_requested']}, selected {sample['n_selected']}  "
          f"(seed {sample['seed']})")
    for c, ids in sorted(sample["by_corpus"].items()):
        print(f"    {c:22} {len(ids):3d}")
    crit = sample["criteria"]
    print(f"  unanswerable: {crit['n_unanswerable']} (floor {crit['min_unanswerable']})")
    print(f"  near-miss:    {crit['n_near_miss']} (floor {crit['min_near_miss']})")
    print(f"  excluded: {', '.join(sorted(sample['excluded_corpora']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
