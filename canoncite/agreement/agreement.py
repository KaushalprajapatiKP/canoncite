"""Inter-annotator agreement for CANONCITE verdicts (BENCHMARK_DESIGN.md §4).

Two families of agreement, computed from the raw `verdicts` rows:

  * Citation-set agreement -> Krippendorff's alpha with the **MASI distance**
    (Passonneau 2006), the correct statistic for overlapping set-valued labels.
    The "value" a reviewer assigns to an item is the *effective gold set*:
        approve -> the item's original gold_citations
        edit    -> edits.gold_citations
        reject  -> the empty set (a rejected item asserts "no correct citation")

  * Categorical agreement -> Cohen's kappa (exactly 2 raters) or Fleiss' kappa
    (>2, or an uneven number of raters per item) on the `status` label and on the
    edited `question_type` / `ambiguity` labels.

All statistics are implemented here from first principles (no numpy/scipy/nltk).
Reported per corpus and per question_type; items with <2 reviewers are skipped
(they cannot contribute to any pairwise agreement) rather than crashing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from itertools import combinations
from typing import Callable, Hashable, Optional, Sequence

# Work whether invoked as a module (python -m canoncite.agreement.agreement) or
# as a plain script (python canoncite/agreement/agreement.py).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from canoncite.agreement import ALPHA_TARGET, KAPPA_TARGET  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REVIEWS_DIR = os.path.join(ROOT, "canoncite", "data", "reviews")
ITEMS_DIR = os.path.join(ROOT, "canoncite", "data", "items")


# ---------------------------------------------------------------------------
# MASI distance (Passonneau 2006) over sets
# ---------------------------------------------------------------------------

def jaccard(a: set, b: set) -> float:
    """|a ∩ b| / |a ∪ b|. Two empty sets are identical -> 1.0."""
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def masi_monotonicity(a: set, b: set) -> float:
    """Passonneau's monotonicity factor M:
        1     identical sets
        2/3   one is a proper subset of the other
        1/3   they intersect but neither contains the other
        0     disjoint
    """
    a, b = set(a), set(b)
    if a == b:
        return 1.0
    inter = a & b
    if not inter:
        return 0.0
    if a <= b or b <= a:      # proper subset (a == b already handled)
        return 2.0 / 3.0
    return 1.0 / 3.0          # they overlap, each has unique members


def masi_similarity(a: set, b: set) -> float:
    """MASI similarity = Jaccard * monotonicity, in [0, 1]. 1.0 == identical."""
    return jaccard(a, b) * masi_monotonicity(a, b)


def masi_distance(a: set, b: set) -> float:
    """MASI *distance* = 1 - similarity, in [0, 1]. Used as Krippendorff's delta."""
    return 1.0 - masi_similarity(a, b)


# ---------------------------------------------------------------------------
# Krippendorff's alpha for an arbitrary distance function
# ---------------------------------------------------------------------------

def krippendorff_alpha(units: Sequence[Sequence], distance: Callable) -> Optional[float]:
    """Krippendorff's alpha for reliability data with a custom distance metric.

    `units` is a list of units; each unit is the list of values assigned to it by
    the coders (missing values simply omitted). `distance(x, y)` is the pairwise
    disagreement metric (0 == identical). Works for any value type — nominal
    labels (with a 0/1 distance) or sets (with MASI distance).

        alpha = 1 - Do / De

    Do (observed disagreement) is the mean within-unit pairwise distance, each
    unit weighted by 1/(m_u - 1); De (expected disagreement) is the mean distance
    over every ordered pair of values in the whole (pairable) dataset. Returns
    None when there is nothing to measure (fewer than 2 total pairable values, or
    De == 0, i.e. every coder used a single value everywhere).
    """
    pairable = [list(u) for u in units if len(u) >= 2]
    n = sum(len(u) for u in pairable)
    if n < 2:
        return None

    # Observed disagreement: within-unit ordered pairs, weighted by 1/(m_u - 1).
    do_sum = 0.0
    for u in pairable:
        m = len(u)
        s = 0.0
        for x, y in combinations(u, 2):
            s += 2.0 * distance(x, y)      # ordered pairs = 2 * unordered
        do_sum += s / (m - 1)
    Do = do_sum / n

    # Expected disagreement: ordered pairs over the pooled bag of all values.
    pool = [v for u in pairable for v in u]
    de_sum = 0.0
    for x, y in combinations(pool, 2):
        de_sum += 2.0 * distance(x, y)
    De = de_sum / (n * (n - 1))

    if De == 0:
        return None
    return 1.0 - Do / De


# ---------------------------------------------------------------------------
# Cohen's kappa (2 raters) and Fleiss' kappa (>=2, possibly uneven)
# ---------------------------------------------------------------------------

def cohen_kappa(pairs: Sequence[tuple[Hashable, Hashable]]) -> Optional[float]:
    """Cohen's kappa for two raters. `pairs` = [(rater_a_label, rater_b_label), ...]
    over the commonly-rated items. Returns None if <2 items or pe == 1."""
    pairs = [p for p in pairs if p[0] is not None and p[1] is not None]
    n = len(pairs)
    if n < 2:
        return None
    cats = {c for p in pairs for c in p}
    po = sum(1 for a, b in pairs if a == b) / n
    marg_a = {c: sum(1 for a, _ in pairs if a == c) / n for c in cats}
    marg_b = {c: sum(1 for _, b in pairs if b == c) / n for c in cats}
    pe = sum(marg_a[c] * marg_b[c] for c in cats)
    if pe >= 1.0:
        return None
    return (po - pe) / (1.0 - pe)


def fleiss_kappa(item_ratings: Sequence[Sequence[Hashable]]) -> Optional[float]:
    """Fleiss' kappa, generalized to an uneven number of raters per item.

    `item_ratings` is a list of items, each a list of category labels (one per
    rater who rated that item; raters need not be the same across items). Items
    with fewer than 2 ratings are dropped. Reduces to standard Fleiss' kappa when
    every item has the same number of raters.
    """
    rated = [list(r) for r in item_ratings if len(r) >= 2]
    if len(rated) < 1:
        return None
    cats = sorted({c for r in rated for c in r}, key=str)
    if len(cats) < 2:
        return None  # only one category used -> agreement undefined / trivially 1

    # counts[i][cat] = # raters putting item i in cat; n_i = raters on item i
    counts = [{c: r.count(c) for c in cats} for r in rated]
    n_i = [sum(cnt.values()) for cnt in counts]

    # Per-item observed agreement P_i.
    P = []
    for cnt, ni in zip(counts, n_i):
        ss = sum(v * v for v in cnt.values())
        P.append((ss - ni) / (ni * (ni - 1)))
    P_bar = sum(P) / len(P)

    # Overall category proportions p_j (share of all assignments).
    total = sum(n_i)
    p_j = {c: sum(cnt[c] for cnt in counts) / total for c in cats}
    P_e = sum(v * v for v in p_j.values())

    if P_e >= 1.0:
        return None
    return (P_bar - P_e) / (1.0 - P_e)


def categorical_kappa(item_ratings: Sequence[Sequence[Hashable]]) -> tuple[Optional[float], str]:
    """Pick the right statistic: Cohen's kappa when every rated item has exactly
    two ratings, else generalized Fleiss' kappa. Returns (value, method)."""
    rated = [list(r) for r in item_ratings if len(r) >= 2]
    if not rated:
        return None, "none"
    if all(len(r) == 2 for r in rated):
        return cohen_kappa([(r[0], r[1]) for r in rated]), "cohen"
    return fleiss_kappa(rated), "fleiss"


# ---------------------------------------------------------------------------
# Turning verdict rows into agreement inputs
# ---------------------------------------------------------------------------

def effective_labels(verdict: dict, item: Optional[dict]) -> dict:
    """The (gold_set, status, question_type, ambiguity) a reviewer effectively
    asserts for an item, resolving edits against the item's original values.

    A `reject` asserts the empty gold set; question_type/ambiguity fall back to
    the item's originals for approve, and to the edit payload for edit.
    """
    item = item or {}
    status = verdict.get("status")
    edits = verdict.get("edits") or {}
    if status == "reject":
        gold: set = set()
    elif status == "edit" and "gold_citations" in edits and edits["gold_citations"] is not None:
        gold = set(edits["gold_citations"])
    else:  # approve, or an edit that did not touch the citations
        gold = set(item.get("gold_citations", []))
    qtype = (edits.get("question_type") if status == "edit" else None) or item.get("question_type")
    amb = (edits.get("ambiguity") if status == "edit" else None) or item.get("ambiguity")
    return {"gold": gold, "status": status, "question_type": qtype, "ambiguity": amb}


def group_verdicts(rows: Sequence[dict]) -> dict[tuple[str, str], dict[str, dict]]:
    """{(corpus, item_id): {reviewer: verdict}}. Later rows for the same
    reviewer×item win (they are re-reviews)."""
    grouped: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for r in rows:
        key = (r.get("corpus"), r.get("item_id"))
        rv = r.get("reviewer", "anon")
        prev = grouped[key].get(rv)
        if prev is None or r.get("ts", 0) >= prev.get("ts", 0):
            grouped[key][rv] = r
    return grouped


def _agreement_for_group(
    keys: Sequence[tuple[str, str]],
    grouped: dict[tuple[str, str], dict[str, dict]],
    items_by_id: dict[str, dict],
) -> dict:
    """Compute the full agreement bundle for a set of item keys."""
    cite_units: list[list[frozenset]] = []
    status_units: list[list[str]] = []
    qtype_units: list[list[str]] = []
    amb_units: list[list[str]] = []
    n_double = 0
    for (corpus, item_id) in keys:
        reviewers = grouped[(corpus, item_id)]
        if len(reviewers) < 2:
            continue
        n_double += 1
        item = items_by_id.get(item_id)
        eff = [effective_labels(v, item) for v in reviewers.values()]
        cite_units.append([frozenset(e["gold"]) for e in eff])
        status_units.append([e["status"] for e in eff])
        qtype_units.append([e["question_type"] for e in eff if e["question_type"]])
        amb_units.append([e["ambiguity"] for e in eff if e["ambiguity"]])

    max_raters = max((len(grouped[k]) for k in keys), default=0)
    status_k, status_method = categorical_kappa(status_units)
    qtype_k, qtype_method = categorical_kappa(qtype_units)
    amb_k, amb_method = categorical_kappa(amb_units)
    return {
        "n_items_total": len(keys),
        "n_items_double_reviewed": n_double,
        "max_raters_per_item": max_raters,
        "citation_alpha_masi": krippendorff_alpha(cite_units, masi_distance),
        "status_kappa": status_k,
        "status_kappa_method": status_method,
        "question_type_kappa": qtype_k,
        "question_type_kappa_method": qtype_method,
        "ambiguity_kappa": amb_k,
        "ambiguity_kappa_method": amb_method,
    }


def compute_agreement(rows: Sequence[dict], items_by_id: dict[str, dict]) -> dict:
    """Full agreement report: overall, per corpus, and per (original) question_type."""
    grouped = group_verdicts(rows)
    keys = list(grouped.keys())

    report: dict = {"overall": _agreement_for_group(keys, grouped, items_by_id)}

    by_corpus: dict[str, list] = defaultdict(list)
    by_qtype: dict[str, list] = defaultdict(list)
    for key in keys:
        corpus, item_id = key
        by_corpus[corpus].append(key)
        item = items_by_id.get(item_id) or {}
        by_qtype[item.get("question_type", "unknown")].append(key)

    report["by_corpus"] = {
        c: _agreement_for_group(ks, grouped, items_by_id) for c, ks in sorted(by_corpus.items())
    }
    report["by_question_type"] = {
        q: _agreement_for_group(ks, grouped, items_by_id) for q, ks in sorted(by_qtype.items())
    }
    return report


# ---------------------------------------------------------------------------
# IO helpers + CLI
# ---------------------------------------------------------------------------

def _load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_verdicts(corpus: Optional[str] = None) -> list[dict]:
    """Read fetched verdicts from data/reviews/<corpus>/verdicts.jsonl (all corpora
    if `corpus` is None). Falls back to per-reviewer <reviewer>.jsonl files written
    by the local review server when no aggregated verdicts.jsonl exists."""
    corpora = [corpus] if corpus else (
        sorted(os.listdir(REVIEWS_DIR)) if os.path.isdir(REVIEWS_DIR) else []
    )
    rows: list[dict] = []
    for c in corpora:
        cdir = os.path.join(REVIEWS_DIR, c)
        if not os.path.isdir(cdir):
            continue
        agg = os.path.join(cdir, "verdicts.jsonl")
        if os.path.isfile(agg):
            rows.extend(_load_jsonl(agg))
        else:
            for fn in sorted(os.listdir(cdir)):
                if fn.endswith(".jsonl"):
                    rows.extend(_load_jsonl(os.path.join(cdir, fn)))
    return rows


def load_items_by_id(corpus: Optional[str] = None) -> dict[str, dict]:
    corpora = [corpus] if corpus else (
        sorted(os.listdir(ITEMS_DIR)) if os.path.isdir(ITEMS_DIR) else []
    )
    out: dict[str, dict] = {}
    for c in corpora:
        p = os.path.join(ITEMS_DIR, c, "seed_candidates.jsonl")
        if os.path.isfile(p):
            for it in _load_jsonl(p):
                out[it["id"]] = it
    return out


def _fmt(v: Optional[float]) -> str:
    return "  n/a" if v is None else f"{v:6.3f}"


def _gate(v: Optional[float], target: float) -> str:
    if v is None:
        return " "
    return "PASS" if v >= target else "FAIL"


def _print_block(name: str, b: dict) -> None:
    a = b["citation_alpha_masi"]
    print(f"\n[{name}]  items={b['n_items_total']} double-reviewed={b['n_items_double_reviewed']} "
          f"max_raters={b['max_raters_per_item']}")
    print(f"    citation-set   Krippendorff alpha (MASI) = {_fmt(a)}   "
          f"target>={ALPHA_TARGET:.2f}  [{_gate(a, ALPHA_TARGET)}]")
    for label, kkey, mkey in (
        ("status        ", "status_kappa", "status_kappa_method"),
        ("question_type ", "question_type_kappa", "question_type_kappa_method"),
        ("ambiguity     ", "ambiguity_kappa", "ambiguity_kappa_method"),
    ):
        k = b[kkey]
        print(f"    {label} {b[mkey]:>6} kappa            = {_fmt(k)}   "
              f"target>={KAPPA_TARGET:.2f}  [{_gate(k, KAPPA_TARGET)}]")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Compute inter-annotator agreement for CANONCITE verdicts.")
    ap.add_argument("--corpus", help="restrict to one corpus (default: all)")
    ap.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = ap.parse_args(argv)

    rows = load_verdicts(args.corpus)
    items = load_items_by_id(args.corpus)
    if not rows:
        print("No verdicts found. Run agreement/fetch.py first.")
        return 1
    report = compute_agreement(rows, items)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"CANONCITE inter-annotator agreement  ({len(rows)} verdict rows)")
    _print_block("OVERALL", report["overall"])
    print("\n=== per corpus ===")
    for c, b in report["by_corpus"].items():
        _print_block(c, b)
    print("\n=== per question_type ===")
    for q, b in report["by_question_type"].items():
        _print_block(q, b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
