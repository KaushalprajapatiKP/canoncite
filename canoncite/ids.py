"""Canonical citation ID parsing and span/adjacency matching, per corpus.

The benchmark scores attribution against a *closed* canonical ID space per corpus
(BENCHMARK_DESIGN.md §1). Exact-ID matching is corpus-agnostic (string equality);
span/adjacency matching (the "credit near-but-not-exact" variant, §5.4) is
corpus-specific and lives here.
"""
from __future__ import annotations

import re
from typing import Callable, Optional, Tuple

# ---- Bhagavad Gita: "chapter.verse" e.g. "2.47" ----------------------------

_GITA_RE = re.compile(r"\s*(\d+)\.(\d+)\s*\Z")


def parse_gita_id(cid: str) -> Optional[Tuple[int, int]]:
    """'2.47' -> (2, 47); None if not a Gita id."""
    m = _GITA_RE.match(cid)
    return (int(m.group(1)), int(m.group(2))) if m else None


def gita_adjacent(a: str, b: str, tol: int = 1) -> bool:
    """True if a and b are the same chapter and within `tol` verses."""
    pa, pb = parse_gita_id(a), parse_gita_id(b)
    if pa is None or pb is None:
        return a == b
    return pa[0] == pb[0] and abs(pa[1] - pb[1]) <= tol


# ---- Guru Granth Sahib: "ang.<ang>.<line>" e.g. "ang.1.1" ------------------

_GGS_RE = re.compile(r"\s*ang\.(\d+)\.(\d+)\s*\Z")


def parse_ggs_id(cid: str) -> Optional[Tuple[int, int]]:
    """'ang.1.1' -> (1, 1) i.e. (ang, line); None if not a GGS id."""
    m = _GGS_RE.match(cid)
    return (int(m.group(1)), int(m.group(2))) if m else None


def ggs_adjacent(a: str, b: str, tol: int = 1) -> bool:
    """True if a and b are on the same Ang and within `tol` lines."""
    pa, pb = parse_ggs_id(a), parse_ggs_id(b)
    if pa is None or pb is None:
        return a == b
    return pa[0] == pb[0] and abs(pa[1] - pb[1]) <= tol


# ---- generic helpers for the remaining corpora ----------------------------

def dotted_adjacent(a: str, b: str, tol: int = 1) -> bool:
    """For dotted numeric ids ('a.b.c'): same prefix, last component within tol.
    Covers chapter.verse / pada.sutra / kanda.sarga.shloka / parva.adhyaya.shloka.
    """
    pa, pb = a.split("."), b.split(".")
    if len(pa) != len(pb) or len(pa) < 2 or pa[:-1] != pb[:-1]:
        return a == b
    try:
        return abs(int(pa[-1]) - int(pb[-1])) <= tol
    except ValueError:
        return a == b


def flat_num_adjacent(a: str, b: str, tol: int = 1) -> bool:
    """For flat integer ids (Thirukkural kural 1..1330)."""
    try:
        return abs(int(a) - int(b)) <= tol
    except ValueError:
        return a == b


_BIBLE_RE = re.compile(r"\s*(.+?)\s+(\d+):(\d+)\s*\Z")


def bible_adjacent(a: str, b: str, tol: int = 1) -> bool:
    """'BOOK c:v': same book and chapter, verse within tol."""
    ma, mb = _BIBLE_RE.match(a), _BIBLE_RE.match(b)
    if not (ma and mb):
        return a == b
    return (ma.group(1) == mb.group(1) and ma.group(2) == mb.group(2)
            and abs(int(ma.group(3)) - int(mb.group(3))) <= tol)


# ---- registry: per-corpus span/adjacency rules ----------------------------
# Corpora with heterogeneous/clause IDs (constitution_india, upanishads) use
# exact-ID matching only (no rule registered) — conservative by design.

ADJACENCY: dict[str, Callable[[str, str, int], bool]] = {
    "bhagavad_gita": gita_adjacent,
    "guru_granth_sahib": ggs_adjacent,
    "dhammapada": dotted_adjacent,
    "yoga_sutras": dotted_adjacent,
    "ramayana": dotted_adjacent,
    "mahabharata": dotted_adjacent,
    "thirukkural": flat_num_adjacent,
    "bible": bible_adjacent,
}


def ids_match(c: str, g: str, corpus: str, tol: int = 1) -> bool:
    """Span/adjacency match used by the span-overlap P/R/F1 variant (§5.4).

    Exact string equality always matches; otherwise fall back to the corpus's
    adjacency rule within `tol`. Corpora without a registered rule match
    exactly only (conservative).
    """
    if c == g:
        return True
    fn = ADJACENCY.get(corpus)
    return bool(fn and fn(c, g, tol))
