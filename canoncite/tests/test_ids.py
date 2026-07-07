"""Tests for per-corpus span/adjacency matching (ids.ids_match)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite.ids import ids_match


def test_dotted_chapter_verse():
    assert ids_match("2.47", "2.48", "dhammapada")          # same chapter, adjacent
    assert not ids_match("2.47", "3.47", "dhammapada")      # different chapter
    assert ids_match("1.2", "1.3", "yoga_sutras")


def test_dotted_three_level():
    assert ids_match("1.1.1", "1.1.2", "ramayana")          # same kanda.sarga
    assert not ids_match("1.1.1", "1.2.1", "ramayana")      # different sarga
    assert ids_match("6.23.1", "6.23.2", "mahabharata")


def test_flat_number_thirukkural():
    assert ids_match("47", "48", "thirukkural")
    assert not ids_match("47", "60", "thirukkural")


def test_bible():
    assert ids_match("John 3:16", "John 3:17", "bible")     # same book+chapter
    assert not ids_match("John 3:16", "John 4:16", "bible") # different chapter
    assert not ids_match("John 3:16", "Mark 3:16", "bible") # different book
    assert ids_match("1 Corinthians 13:4", "1 Corinthians 13:5", "bible")


def test_exact_only_corpora():
    # heterogeneous IDs fall back to exact match
    assert ids_match("Art. 21", "Art. 21", "constitution_india")
    assert not ids_match("Art. 21", "Art. 22", "constitution_india")
    assert not ids_match("isha.1", "isha.2", "upanishads")
    assert ids_match("isha.1", "isha.1", "upanishads")


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
