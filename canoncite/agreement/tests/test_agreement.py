"""Unit tests for CANONCITE agreement + adjudication.

Every asserted metric value below is worked out by hand on the synthetic data in
the test, so a regression in the math is caught immediately.

    PYTHONPATH=. python canoncite/agreement/tests/test_agreement.py
    PYTHONPATH=. python -m pytest canoncite/agreement/tests -q
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from canoncite.agreement.adjudicate import adjudicate_item
from canoncite.agreement.agreement import (
    categorical_kappa,
    cohen_kappa,
    effective_labels,
    fleiss_kappa,
    krippendorff_alpha,
    masi_distance,
    masi_similarity,
)


def approx(a, b, tol=1e-9):
    assert a is not None, "expected a number, got None"
    assert abs(a - b) <= tol, f"{a} != {b} (tol {tol})"


# ---- MASI distance --------------------------------------------------------

def test_masi_identical():
    approx(masi_distance({1, 2}, {1, 2}), 0.0)
    approx(masi_similarity({1, 2}, {1, 2}), 1.0)


def test_masi_subset():
    # J=1/2, M=2/3 -> sim=1/3 -> dist=2/3
    approx(masi_distance({1, 2}, {1}), 2.0 / 3.0)


def test_masi_overlap_nonsubset():
    # J=1/3, M=1/3 -> sim=1/9 -> dist=8/9
    approx(masi_distance({1, 2}, {2, 3}), 8.0 / 9.0)


def test_masi_disjoint():
    approx(masi_distance({1}, {2}), 1.0)


def test_masi_empty_sets():
    approx(masi_distance(set(), set()), 0.0)          # both empty == identical
    approx(masi_distance(set(), {1}), 1.0)            # empty vs non-empty == disjoint


# ---- Krippendorff's alpha -------------------------------------------------

def _nominal(x, y):
    return 0.0 if x == y else 1.0


def test_alpha_perfect_nominal():
    units = [["A", "A"], ["B", "B"]]
    approx(krippendorff_alpha(units, _nominal), 1.0)


def test_alpha_systematic_disagreement():
    # Two raters disagree the same way on every item -> alpha = -0.5.
    units = [["A", "B"], ["A", "B"]]
    approx(krippendorff_alpha(units, _nominal), -0.5)


def test_alpha_single_unit_is_zero():
    # One unit -> Do == De -> alpha 0.
    approx(krippendorff_alpha([[{1, 2}, {1}]], masi_distance), 0.0)


def test_alpha_masi_worked_example():
    # units: [{1,2} vs {1}] and [{3} vs {3,4}] -> Do=2/3, De=8/9 -> alpha=1/4.
    units = [[{1, 2}, {1}], [{3}, {3, 4}]]
    approx(krippendorff_alpha(units, masi_distance), 0.25)


def test_alpha_none_when_insufficient():
    assert krippendorff_alpha([["A"]], _nominal) is None       # no pairable unit
    assert krippendorff_alpha([["A", "A"]], _nominal) is None   # De == 0


# ---- Cohen's / Fleiss' kappa ----------------------------------------------

def test_cohen_kappa():
    # 3x(y,y), (y,n), (n,y), (n,n): po=4/6, pe=5/9 -> kappa=0.25
    pairs = [("y", "y"), ("y", "y"), ("y", "y"), ("y", "n"), ("n", "y"), ("n", "n")]
    approx(cohen_kappa(pairs), 0.25)


def test_cohen_perfect():
    approx(cohen_kappa([("a", "a"), ("b", "b"), ("a", "a"), ("b", "b")]), 1.0)


def test_fleiss_kappa():
    # 3 raters; items aaa / aab / bbb -> kappa = 22/40 = 0.55
    items = [["a", "a", "a"], ["a", "a", "b"], ["b", "b", "b"]]
    approx(fleiss_kappa(items), 0.55)


def test_categorical_dispatch():
    two = [["a", "b"], ["a", "a"], ["b", "b"]]
    _, method = categorical_kappa(two)
    assert method == "cohen"
    mixed = [["a", "b", "b"], ["a", "a"], ["b", "b", "a"]]
    _, method = categorical_kappa(mixed)
    assert method == "fleiss"


# ---- effective_labels -----------------------------------------------------

def test_effective_labels_reject_is_empty():
    item = {"gold_citations": ["2.47"], "question_type": "factual", "ambiguity": "low"}
    e = effective_labels({"status": "reject"}, item)
    assert e["gold"] == set() and e["status"] == "reject"


def test_effective_labels_edit_overrides():
    item = {"gold_citations": ["2.47"], "question_type": "factual", "ambiguity": "low"}
    e = effective_labels(
        {"status": "edit", "edits": {"gold_citations": ["2.48"], "ambiguity": "high"}}, item)
    assert e["gold"] == {"2.48"}
    assert e["question_type"] == "factual"   # not edited -> original
    assert e["ambiguity"] == "high"


def test_effective_labels_approve_uses_item():
    item = {"gold_citations": ["2.47"], "question_type": "factual", "ambiguity": "low"}
    e = effective_labels({"status": "approve"}, item)
    assert e["gold"] == {"2.47"} and e["question_type"] == "factual"


# ---- adjudication ---------------------------------------------------------

BASE = {"id": "x", "corpus": "c", "gold_citations": ["2.47"],
        "question_type": "factual", "ambiguity": "low",
        "answerable": True, "must_abstain": False}


def test_adjudicate_two_approves_verified():
    v = [{"reviewer": "a", "status": "approve"}, {"reviewer": "b", "status": "approve"}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "verified"
    assert gold["verified"] is True and gold["needs_adjudication"] is False
    assert gold["gold_citations"] == ["2.47"] and dec["edited"] is False


def test_adjudicate_agreed_edit_applied():
    v = [{"reviewer": "a", "status": "edit", "edits": {"gold_citations": ["2.48"]}},
         {"reviewer": "b", "status": "edit", "edits": {"gold_citations": ["2.48"]}}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "verified" and dec["edited"] is True
    assert gold["gold_citations"] == ["2.48"] and gold["adjudicated"] is True


def test_adjudicate_edit_conflict():
    v = [{"reviewer": "a", "status": "edit", "edits": {"gold_citations": ["2.48"]}},
         {"reviewer": "b", "status": "edit", "edits": {"gold_citations": ["3.19"]}}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "needs_adjudication"
    assert "gold_citations" in dec["conflicting_fields"]
    assert gold["needs_adjudication"] is True
    assert len(gold["disagreement"]["reviewer_labels"]) == 2


def test_adjudicate_reject_approve_split():
    v = [{"reviewer": "a", "status": "approve"}, {"reviewer": "b", "status": "reject"}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "needs_adjudication"
    assert dec["reason"] == "reject_approve_split"


def test_adjudicate_all_reject():
    v = [{"reviewer": "a", "status": "reject"}, {"reviewer": "b", "status": "reject"}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "needs_adjudication" and dec["reason"] == "all_reject"


def test_adjudicate_insufficient():
    gold, dec = adjudicate_item(BASE, [{"reviewer": "a", "status": "approve"}])
    assert dec["resolution"] == "insufficient_reviews"
    assert gold["verified"] is False


def test_adjudicate_unreviewed():
    gold, dec = adjudicate_item(BASE, [])
    assert dec["resolution"] == "unreviewed"


def test_adjudicate_edit_to_unanswerable_sets_flags():
    v = [{"reviewer": "a", "status": "edit",
          "edits": {"gold_citations": [], "question_type": "unanswerable"}},
         {"reviewer": "b", "status": "edit",
          "edits": {"gold_citations": [], "question_type": "unanswerable"}}]
    gold, dec = adjudicate_item(BASE, v)
    assert dec["resolution"] == "verified"
    assert gold["question_type"] == "unanswerable"
    assert gold["answerable"] is False and gold["must_abstain"] is True
    assert gold["gold_citations"] == []


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
