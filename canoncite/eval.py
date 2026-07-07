"""Scoring orchestration: per-item scoring + corpus-level aggregation.

A *gold item* carries the adjudicated benchmark labels; a *system output* carries
one model's (cited_ids, retrieved_ids, abstained, supp) for that item. The harness
ingests these and emits the full metric table (BENCHMARK_DESIGN.md §5/§8).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import metrics


@dataclass
class GoldItem:
    id: str
    corpus: str
    gold_citations: set = field(default_factory=set)
    near_miss_distractors: set = field(default_factory=set)
    must_abstain: bool = False
    answerable: bool = True


@dataclass
class SystemOutput:
    item_id: str
    abstained: bool = False
    cited_ids: set = field(default_factory=set)
    retrieved_ids: set = field(default_factory=set)
    supp: Optional[dict] = None  # id -> full|partial|none (judge labels; optional)


def score_item(gold: GoldItem, out: SystemOutput, U: set, tol: int = 1) -> dict:
    C = set(out.cited_ids)
    mis, exist_err, supp_err = metrics.answer_misattribution(C, U, gold.gold_citations, out.supp)
    nm_hits, wrong = metrics.near_miss(C, gold.gold_citations, gold.near_miss_distractors)
    r = {
        "item_id": gold.id,
        "corpus": gold.corpus,
        "cites": len(C) > 0,
        "abstained": out.abstained,
        "unanswerable": gold.must_abstain,
        "cer": metrics.citation_existence_rate(C, U),
        "cg": metrics.citation_groundedness(C, out.retrieved_ids),
        "exact": metrics.attribution_prf_exact(C, gold.gold_citations),
        "span": metrics.attribution_prf_span(C, gold.gold_citations, gold.corpus, tol),
        "misattributed": mis,
        "mar_exist": exist_err,
        "mar_support": supp_err,
        "near_miss_hits": nm_hits,
        "wrong_cites": wrong,
    }
    if gold.must_abstain:
        r["abstained_correct"] = out.abstained and not C
        r["over_cited"] = bool(C)
    else:
        r["wrong_abstention"] = out.abstained
    return r


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _rate(items, pred):
    items = list(items)
    return (sum(1 for r in items if pred(r)) / len(items)) if items else None


def aggregate(results: list[dict]) -> dict:
    citing = [r for r in results if r["cites"]]
    unans = [r for r in results if r["unanswerable"]]
    ans = [r for r in results if not r["unanswerable"]]
    total_wrong = sum(r["wrong_cites"] for r in results)
    total_nm = sum(r["near_miss_hits"] for r in results)
    return {
        "n": len(results),
        "n_citing": len(citing),
        "n_unanswerable": len(unans),
        "cer": _mean([r["cer"] for r in results]),
        "cg": _mean([r["cg"] for r in results]),
        "attr_f1_exact": _mean([r["exact"]["f1"] for r in results]),
        "attr_f1_span": _mean([r["span"]["f1"] for r in results]),
        "mar": _rate(citing, lambda r: r["misattributed"]),
        "mar_exist": _rate(citing, lambda r: r["mar_exist"]),
        "mar_support": _rate(citing, lambda r: r["mar_support"]),
        "nmr": (total_nm / total_wrong) if total_wrong else None,
        "abstention_accuracy": _rate(unans, lambda r: r["abstained_correct"]),
        "over_citation_rate": _rate(unans, lambda r: r["over_cited"]),
        "wrong_abstention_rate": _rate(ans, lambda r: r.get("wrong_abstention", False)),
    }


def format_table(agg: dict) -> str:
    order = [
        ("n", "items"), ("n_citing", "items citing"), ("n_unanswerable", "unanswerable"),
        ("cer", "Citation Existence Rate"), ("cg", "Citation Groundedness"),
        ("attr_f1_exact", "Attribution F1 (exact)"), ("attr_f1_span", "Attribution F1 (span)"),
        ("mar", "Misattribution Rate"), ("mar_exist", "  MAR-exist"), ("mar_support", "  MAR-support"),
        ("nmr", "Near-miss Misattr. Rate"),
        ("abstention_accuracy", "Abstention Accuracy"), ("over_citation_rate", "Over-citation Rate"),
        ("wrong_abstention_rate", "Wrong-abstention Rate"),
    ]
    lines = []
    for key, label in order:
        v = agg.get(key)
        s = "—" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
        lines.append(f"{label:<28} {s}")
    return "\n".join(lines)
