"""Worked-example tests for the CANONCITE metric harness.

Runnable two ways:
    PYTHONPATH=. python -m pytest canoncite/tests -q
    PYTHONPATH=. python canoncite/tests/test_metrics.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite import metrics
from canoncite.eval import GoldItem, SystemOutput, aggregate, score_item

# A small Gita ID space for tests.
U = {"2.47", "2.48", "2.49", "3.19", "3.33", "5.18", "4.7"}


def approx(a, b):
    return a is not None and math.isclose(a, b, abs_tol=1e-9)


def test_exact_perfect_attribution():
    r = metrics.attribution_prf_exact({"2.47", "2.48"}, {"2.47", "2.48"})
    assert approx(r["precision"], 1.0) and approx(r["recall"], 1.0) and approx(r["f1"], 1.0)


def test_near_miss_citation():
    G = {"2.47", "2.48"}
    C = {"2.47", "5.18"}  # 5.18 exists, wrong, is a near-miss distractor
    ex = metrics.attribution_prf_exact(C, G)
    assert approx(ex["precision"], 0.5) and approx(ex["recall"], 0.5)
    assert approx(metrics.citation_existence_rate(C, U), 1.0)  # both exist
    mis, exist_err, supp_err = metrics.answer_misattribution(C, U, G)
    assert mis and not exist_err and supp_err  # real id, unsupported content
    nm_hits, wrong = metrics.near_miss(C, G, {"5.18", "3.19"})
    assert nm_hits == 1 and wrong == 1


def test_nonexistent_citation():
    C = {"2.99"}  # not in U
    assert approx(metrics.citation_existence_rate(C, U), 0.0)
    mis, exist_err, supp_err = metrics.answer_misattribution(C, U, {"2.47"})
    assert mis and exist_err and not supp_err


def test_span_credits_adjacent():
    # gold span 2.47-2.48; model cites only 2.47
    G, C = {"2.47", "2.48"}, {"2.47"}
    ex = metrics.attribution_prf_exact(C, G)
    assert approx(ex["recall"], 0.5)  # exact misses 2.48
    sp = metrics.attribution_prf_span(C, G, "bhagavad_gita", tol=1)
    assert approx(sp["precision"], 1.0) and approx(sp["recall"], 1.0)  # 2.47 adjacent to 2.48


def test_span_does_not_credit_far_or_other_chapter():
    sp = metrics.attribution_prf_span({"3.19"}, {"2.48"}, "bhagavad_gita", tol=1)
    assert approx(sp["recall"], 0.0)  # different chapter -> no credit


def test_groundedness():
    assert approx(metrics.citation_groundedness({"2.47", "2.48"}, {"2.47", "2.48", "3.19"}), 1.0)
    assert approx(metrics.citation_groundedness({"2.47", "5.18"}, {"2.47"}), 0.5)
    assert metrics.citation_existence_rate(set(), U) is None  # empty cite -> flagged


def test_abstention_and_aggregate():
    gold = [
        GoldItem("g1", "bhagavad_gita", {"2.47", "2.48"}, {"5.18"}),          # answerable
        GoldItem("g2", "bhagavad_gita", {"2.47", "2.48"}, {"5.18", "3.19"}),  # answerable
        GoldItem("u1", "bhagavad_gita", set(), {"4.7"}, must_abstain=True, answerable=False),
        GoldItem("u2", "bhagavad_gita", set(), {"3.33"}, must_abstain=True, answerable=False),
    ]
    out = {
        "g1": SystemOutput("g1", cited_ids={"2.47", "2.48"}, retrieved_ids={"2.47", "2.48", "3.19"}),
        "g2": SystemOutput("g2", cited_ids={"2.47", "5.18"}, retrieved_ids={"2.47", "5.18"}),  # near-miss error
        "u1": SystemOutput("u1", abstained=True, cited_ids=set()),                              # correct abstain
        "u2": SystemOutput("u2", cited_ids={"3.33"}),                                            # over-cited
    }
    results = [score_item(g, out[g.id], U) for g in gold]
    agg = aggregate(results)

    assert agg["n"] == 4 and agg["n_citing"] == 3 and agg["n_unanswerable"] == 2
    # g1 clean, g2 misattributed (5.18 unsupported); u2 over-cited counts as misattribution too
    assert approx(agg["mar"], 2 / 3)            # g2 + u2 among 3 citing answers
    assert approx(agg["mar_exist"], 0.0)        # no non-existent ids cited
    assert approx(agg["nmr"], 1.0)              # both wrong cites (5.18, 3.33) are near-miss distractors
    assert approx(agg["abstention_accuracy"], 0.5)   # u1 correct, u2 wrong
    assert approx(agg["over_citation_rate"], 0.5)    # u2 over-cited
    assert approx(agg["cer"], 1.0)              # everything cited exists


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
