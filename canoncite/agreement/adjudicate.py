"""Fold reviewer verdicts into a gold item set (BENCHMARK_DESIGN.md §4, Step 3).

For each reviewed item we look at every reviewer's effective decision (see
`agreement.effective_labels`) and decide:

  * verified            >= 2 reviewers, none reject, and they agree on the
                        effective (gold_citations, question_type, ambiguity).
                        The agreed values become gold; `adjudicated`/`verified`
                        are set true. (An agreed *edit* is applied.)
  * needs_adjudication  a reject/approve split, an all-reject, or conflicting
                        edits -> a human adjudicator must resolve. The
                        disagreement is recorded on the item.
  * insufficient_reviews  exactly one reviewer.
  * unreviewed          no verdicts (item is not written to gold.jsonl).

Output: data/items/<corpus>/gold.jsonl (each item validated via
canoncite.items.validate_item against the corpus ID space U) plus a printed
summary. `needs_adjudication` items are kept in gold.jsonl (flagged) so the
adjudicator can find them; only truly unreviewed items are dropped.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Optional, Sequence

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from canoncite.corpus_io import load_id_space  # noqa: E402
from canoncite.items import Item, validate_item  # noqa: E402
from canoncite.agreement.agreement import (  # noqa: E402
    ROOT,
    effective_labels,
    group_verdicts,
    load_items_by_id,
    load_verdicts,
)

CORPORA_DIR = os.path.join(ROOT, "canoncite", "data", "corpora")
ITEMS_DIR = os.path.join(ROOT, "canoncite", "data", "items")


def adjudicate_item(item: dict, verdicts: Sequence[dict]) -> tuple[dict, dict]:
    """Resolve one item against its verdicts (order-independent).

    Returns (gold_item, decision). `gold_item` is a copy of `item` with agreed
    edits applied and adjudication flags set; `decision` summarizes the outcome.
    """
    item = dict(item)  # shallow copy; we only replace top-level scalar/list fields
    decision: dict = {"item_id": item.get("id"), "n_reviewers": len(verdicts)}

    if not verdicts:
        decision["resolution"] = "unreviewed"
        item["verified"] = False
        item["needs_adjudication"] = False
        return item, decision

    eff = [effective_labels(v, item) for v in verdicts]
    statuses = [e["status"] for e in eff]
    decision["statuses"] = dict(Counter(statuses))

    if len(verdicts) < 2:
        decision["resolution"] = "insufficient_reviews"
        item["verified"] = False
        item["needs_adjudication"] = False
        return item, decision

    n_reject = statuses.count("reject")
    non_reject = [e for e in eff if e["status"] != "reject"]

    # A reject/approve split, or unanimous rejection, is a disagreement to adjudicate.
    if n_reject and non_reject:
        return _needs_adj(item, decision, eff, reason="reject_approve_split")
    if n_reject and not non_reject:
        return _needs_adj(item, decision, eff, reason="all_reject")

    # No rejects: do the surviving reviewers agree on every effective field?
    gold_sets = {frozenset(e["gold"]) for e in non_reject}
    qtypes = {e["question_type"] for e in non_reject}
    ambs = {e["ambiguity"] for e in non_reject}
    conflicts = []
    if len(gold_sets) > 1:
        conflicts.append("gold_citations")
    if len(qtypes) > 1:
        conflicts.append("question_type")
    if len(ambs) > 1:
        conflicts.append("ambiguity")
    if conflicts:
        return _needs_adj(item, decision, eff, reason="edit_conflict", conflicts=conflicts)

    # Consensus. Apply the agreed values (an agreed edit differs from the original).
    agreed_gold = sorted(next(iter(gold_sets)))
    agreed_qtype = next(iter(qtypes))
    agreed_amb = next(iter(ambs))
    changed = (agreed_gold != sorted(item.get("gold_citations", []))
               or agreed_qtype != item.get("question_type")
               or agreed_amb != item.get("ambiguity"))
    item["gold_citations"] = agreed_gold
    item["question_type"] = agreed_qtype
    item["ambiguity"] = agreed_amb
    # keep answerable / must_abstain consistent with an edited-to-unanswerable label
    if agreed_qtype == "unanswerable":
        item["answerable"] = False
        item["must_abstain"] = True
    item["verified"] = True
    item["needs_adjudication"] = False
    item["adjudicated"] = True
    item.setdefault("provenance", {})
    if isinstance(item["provenance"], dict):
        item["provenance"] = {**item["provenance"], "verified": True}
    decision["resolution"] = "verified"
    decision["edited"] = changed
    decision["gold_citations"] = agreed_gold
    return item, decision


def _needs_adj(item: dict, decision: dict, eff, reason: str, conflicts=None) -> tuple[dict, dict]:
    item["verified"] = False
    item["needs_adjudication"] = True
    item["adjudicated"] = False
    disagreement = {
        "reason": reason,
        "reviewer_labels": [
            {"status": e["status"], "gold_citations": sorted(e["gold"]),
             "question_type": e["question_type"], "ambiguity": e["ambiguity"]}
            for e in eff
        ],
    }
    if conflicts:
        disagreement["conflicting_fields"] = conflicts
    item["disagreement"] = disagreement
    decision["resolution"] = "needs_adjudication"
    decision["reason"] = reason
    if conflicts:
        decision["conflicting_fields"] = conflicts
    return item, decision


def adjudicate_corpus(corpus: str) -> dict:
    """Adjudicate every reviewed item in a corpus, write gold.jsonl, return a summary."""
    items_by_id = load_items_by_id(corpus)
    rows = load_verdicts(corpus)
    grouped = group_verdicts(rows)

    U = None
    idx = os.path.join(CORPORA_DIR, corpus, "corpus_index.jsonl")
    if os.path.isfile(idx):
        U = load_id_space(idx)

    gold_items: list[dict] = []
    decisions: list[dict] = []
    validation_errors = 0
    for (c, item_id), reviewers in grouped.items():
        if c != corpus:
            continue
        item = items_by_id.get(item_id)
        if item is None:
            decisions.append({"item_id": item_id, "resolution": "orphan_verdict"})
            continue
        gold_item, decision = adjudicate_item(item, list(reviewers.values()))
        if decision["resolution"] == "unreviewed":
            continue
        gold_items.append(gold_item)
        if U is not None:
            issues = validate_item(Item.from_dict(gold_item), U)
            errs = [m for lvl, m in issues if lvl == "error"]
            if errs:
                validation_errors += 1
                decision["validation_errors"] = errs
        decisions.append(decision)

    gold_items.sort(key=lambda d: d.get("id", ""))
    out_path = os.path.join(ITEMS_DIR, corpus, "gold.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for it in gold_items:
            f.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")

    res_counts = Counter(d["resolution"] for d in decisions)
    summary = {
        "corpus": corpus,
        "gold_path": out_path,
        "n_items_written": len(gold_items),
        "resolutions": dict(res_counts),
        "n_validation_errors": validation_errors,
        "needs_adjudication": [d["item_id"] for d in decisions
                               if d.get("resolution") == "needs_adjudication"],
    }
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Adjudicate CANONCITE verdicts into gold.jsonl.")
    ap.add_argument("--corpus", help="corpus to adjudicate (default: all with verdicts)")
    args = ap.parse_args(argv)

    if args.corpus:
        corpora = [args.corpus]
    else:
        rdir = os.path.join(ROOT, "canoncite", "data", "reviews")
        corpora = sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []
    if not corpora:
        print("No corpora with verdicts found. Run agreement/fetch.py first.")
        return 1

    for corpus in corpora:
        summary = adjudicate_corpus(corpus)
        print(f"\n[{corpus}] -> {summary['gold_path']}")
        print(f"  wrote {summary['n_items_written']} items; "
              f"resolutions: {summary['resolutions']}")
        if summary["n_validation_errors"]:
            print(f"  WARNING: {summary['n_validation_errors']} items have validation errors")
        if summary["needs_adjudication"]:
            print(f"  needs adjudication: {len(summary['needs_adjudication'])} items "
                  f"({', '.join(summary['needs_adjudication'][:8])}"
                  f"{'...' if len(summary['needs_adjudication']) > 8 else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
