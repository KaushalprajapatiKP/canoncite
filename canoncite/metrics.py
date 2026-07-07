"""CANONCITE metric primitives (pure functions). See BENCHMARK_DESIGN.md §5.

Notation per answer: G = gold citation set, C = model-cited set, R = retrieved-ID
set, U = corpus ID space. `supp` maps a cited id -> content-support label in
{full, partial, none} (from an NLI/LLM-judge at eval time, calibrated against the
benchmark's human `answer_support` labels). A citation is *valid* iff it exists in
U AND its content-support != none.

These functions are deterministic and dependency-free so they can be unit-tested
without any model. CER, CG, exact P/R/F1, MAR-exist and NMR are fully
deterministic; MAR-support depends on the provided `supp` labels.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .ids import ids_match

SupportMap = Optional[dict]  # id -> "full" | "partial" | "none"


def _s(x: Iterable[str]) -> set:
    return set(x)


# ---- 1. Citation Existence Rate -------------------------------------------

def citation_existence_rate(C: Iterable[str], U: set) -> Optional[float]:
    """Fraction of cited ids that actually exist in the corpus ID space.

    Returns None when nothing is cited (flagged separately, not folded into the
    mean as 1.0 — see BENCHMARK_DESIGN.md §5.1).
    """
    C = _s(C)
    if not C:
        return None
    return sum(1 for c in C if c in U) / len(C)


# ---- 2. Citation Groundedness ---------------------------------------------

def citation_groundedness(C: Iterable[str], R: Iterable[str]) -> Optional[float]:
    """Fraction of cited ids that were in the retrieved set."""
    C, R = _s(C), _s(R)
    if not C:
        return None
    return sum(1 for c in C if c in R) / len(C)


# ---- 3. Attribution P/R/F1 (exact id) -------------------------------------

def _prf(matched_c: int, matched_g: int, nc: int, ng: int) -> dict:
    P = matched_c / nc if nc else (1.0 if ng == 0 else 0.0)
    R = matched_g / ng if ng else (1.0 if nc == 0 else 0.0)
    F1 = 2 * P * R / (P + R) if (P + R) else 0.0
    return {"precision": P, "recall": R, "f1": F1}


def attribution_prf_exact(C: Iterable[str], G: Iterable[str]) -> dict:
    C, G = _s(C), _s(G)
    inter = len(C & G)
    return _prf(inter, inter, len(C), len(G))


# ---- 4. Attribution P/R/F1 (span / adjacency) -----------------------------

def attribution_prf_span(C: Iterable[str], G: Iterable[str], corpus: str, tol: int = 1) -> dict:
    """Credits near-but-not-exact citations within a corpus tolerance window."""
    C, G = list(_s(C)), list(_s(G))
    matched_c = sum(1 for c in C if any(ids_match(c, g, corpus, tol) for g in G))
    matched_g = sum(1 for g in G if any(ids_match(c, g, corpus, tol) for c in C))
    return _prf(matched_c, matched_g, len(C), len(G))


# ---- 5/6. Misattribution & near-miss --------------------------------------

def support_for(cid: str, G: set, supp: SupportMap) -> str:
    """Content-support label for a cited id. Defaults: ids in G -> 'full',
    otherwise 'none' (used when no judge labels are supplied)."""
    if supp is not None and cid in supp:
        return supp[cid]
    return "full" if cid in G else "none"


def answer_misattribution(C: Iterable[str], U: set, G: Iterable[str], supp: SupportMap = None):
    """Per-answer (misattributed, exist_error, support_error) booleans.

    exist_error: a cited id does not exist in U (clean, NLI-free signal).
    support_error: a cited id exists but its content does not support the claim.
    """
    C, G = _s(C), _s(G)
    exist_error = any(c not in U for c in C)
    support_error = any((c in U) and support_for(c, G, supp) == "none" for c in C)
    return (exist_error or support_error, exist_error, support_error)


def near_miss(C: Iterable[str], G: Iterable[str], near_miss_distractors: Iterable[str]):
    """(# wrong cites that are near-miss distractors, # wrong cites).

    'wrong' = cited ids not in gold. NMR aggregates these across answers.
    """
    C, G, nm = _s(C), _s(G), _s(near_miss_distractors)
    wrong = C - G
    return len(wrong & nm), len(wrong)
