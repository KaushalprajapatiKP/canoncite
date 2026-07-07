"""Tests for the item schema, IO, and validator.

    PYTHONPATH=. python canoncite/tests/test_items.py
    PYTHONPATH=. python -m pytest canoncite/tests -q
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite.ids import parse_gita_id
from canoncite.items import Item, validate_item, validate_items
from canoncite.corpus_io import load_id_space

U_TEST = {"2.47", "2.48", "5.18", "3.19", "18.66"}
_GITA_INDEX = os.path.join(
    os.path.dirname(__file__), "..", "data", "corpora", "bhagavad_gita", "corpus_index.jsonl"
)


def _levels(issues):
    return {lvl for lvl, _ in issues}


def test_valid_factual_item():
    it = Item("g1", "bhagavad_gita", "Which verse teaches action without attachment to fruits?",
              "factual", gold_citations=["2.47"], near_miss_distractors=["5.18", "3.19"])
    assert "error" not in _levels(validate_item(it, U_TEST, parse_gita_id))


def test_gold_not_in_U_is_error():
    it = Item("g2", "bhagavad_gita", "q", "factual", gold_citations=["2.99"],
              near_miss_distractors=["5.18", "3.19"])
    iss = validate_item(it, U_TEST, parse_gita_id)
    assert any(lvl == "error" and "not in corpus ID space" in m for lvl, m in iss)


def test_near_miss_overlaps_gold_is_error():
    it = Item("g3", "bhagavad_gita", "q", "factual", gold_citations=["2.47"],
              near_miss_distractors=["2.47", "5.18"])
    assert any("overlap gold" in m for lvl, m in validate_item(it, U_TEST, parse_gita_id) if lvl == "error")


def test_unanswerable_consistency():
    bad = Item("u1", "bhagavad_gita", "What does the Gita say about cryptocurrency?",
               "unanswerable", gold_citations=["2.47"], must_abstain=True, answerable=False)
    assert any("empty gold" in m for lvl, m in validate_item(bad, U_TEST) if lvl == "error")
    good = Item("u2", "bhagavad_gita", "What does the Gita say about cryptocurrency?",
                "unanswerable", gold_citations=[], must_abstain=True, answerable=False,
                abstain_reason="topic_not_in_corpus")
    assert "error" not in _levels(validate_item(good, U_TEST))


def test_bad_question_type_is_error():
    it = Item("g4", "bhagavad_gita", "q", "lookup", gold_citations=["2.47"])
    assert any("invalid question_type" in m for lvl, m in validate_item(it, U_TEST) if lvl == "error")


def test_factual_few_distractors_warns():
    it = Item("g5", "bhagavad_gita", "q", "factual", gold_citations=["2.47"], near_miss_distractors=["5.18"])
    iss = validate_item(it, U_TEST, parse_gita_id)
    assert "error" not in _levels(iss) and "warn" in _levels(iss)


def test_validate_items_dupe_detection():
    items = [Item("dup", "bhagavad_gita", "q", "factual", gold_citations=["2.47"], near_miss_distractors=["5.18", "3.19"]),
             Item("dup", "bhagavad_gita", "q2", "factual", gold_citations=["2.48"], near_miss_distractors=["5.18", "3.19"])]
    rep = validate_items(items, U_TEST, parse_gita_id)
    assert rep["duplicate_item_ids"] == ["dup"] and rep["ok"] is False


def test_integration_against_real_gita_corpus():
    """If the built corpus is present, gold '2.47'/'18.66' must validate against real U."""
    if not os.path.exists(_GITA_INDEX):
        print("  (skip: corpus_index.jsonl not found)")
        return
    U = load_id_space(_GITA_INDEX)
    assert len(U) == 701 and "2.47" in U and "18.66" in U
    it = Item("gita-real-1", "bhagavad_gita",
              "Which verse states one's right is to action, not to its fruits?",
              "factual", gold_citations=["2.47"], near_miss_distractors=["5.18", "3.19"],
              gold_answer="2.47.")
    assert "error" not in _levels(validate_item(it, U, parse_gita_id))
    # a non-existent id must be rejected against the real space
    bad = Item("gita-real-2", "bhagavad_gita", "q", "factual", gold_citations=["19.1"])
    assert any(lvl == "error" for lvl, _ in validate_item(bad, U, parse_gita_id))


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
