"""Benchmark item schema, JSONL IO, and validation (BENCHMARK_DESIGN.md §2).

An Item is one annotated benchmark question. `validate_item` enforces the
integrity invariants that make the deterministic metrics meaningful — above all,
that every gold and near-miss citation exists in the corpus ID space `U`, and that
unanswerable items carry an empty gold set.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

QUESTION_TYPES = {"factual", "retrieval", "conceptual", "interpretive", "unanswerable"}
AMBIGUITY = {"low", "medium", "high"}
SUPPORT = {"full", "partial", "none"}

_CORE = {
    "id", "corpus", "question", "question_type", "gold_citations", "answerable",
    "ambiguity", "near_miss_distractors", "gold_answer", "must_abstain",
    "abstain_reason", "answer_support", "provenance", "adjudicated", "license",
    "version", "translations",
}

# Trilingual layer: every item's English `question`/`gold_answer` is the base;
# `translations` adds Hindi (hi) + the corpus's native language. Query languages
# are en/hi; native is the third. (BENCHMARK_DESIGN multilingual scope.)
LANGS = {"hi", "sa", "ta", "pa", "pi"}  # hi=Hindi sa=Sanskrit ta=Tamil pa=Punjabi pi=Pali
CORPUS_NATIVE = {
    "bhagavad_gita": "sa", "upanishads": "sa", "yoga_sutras": "sa",
    "ramayana": "sa", "mahabharata": "sa",
    "thirukkural": "ta", "guru_granth_sahib": "pa", "dhammapada": "pi",
    "constitution_india": "hi", "bible": "hi",  # native == hi (no separate third lang)
}


@dataclass
class Item:
    id: str
    corpus: str
    question: str
    question_type: str
    gold_citations: list = field(default_factory=list)
    answerable: bool = True
    ambiguity: str = "low"
    near_miss_distractors: list = field(default_factory=list)
    gold_answer: str = ""
    must_abstain: bool = False
    abstain_reason: Optional[str] = None
    answer_support: list = field(default_factory=list)  # [{citation, support, rationale}]
    provenance: dict = field(default_factory=dict)
    adjudicated: bool = False
    license: str = "public-domain"
    version: str = "v0.1"
    translations: dict = field(default_factory=dict)  # {lang: {question, gold_answer}}
    extra: dict = field(default_factory=dict)  # gold_citation_spans, annotations, etc.

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        known = {k: d[k] for k in _CORE if k in d}
        extra = {k: v for k, v in d.items() if k not in _CORE}
        return cls(**known, extra=extra)

    def to_dict(self) -> dict:
        out = {
            "id": self.id, "corpus": self.corpus, "question": self.question,
            "question_type": self.question_type, "answerable": self.answerable,
            "ambiguity": self.ambiguity, "gold_citations": self.gold_citations,
            "near_miss_distractors": self.near_miss_distractors,
            "gold_answer": self.gold_answer, "must_abstain": self.must_abstain,
            "abstain_reason": self.abstain_reason, "answer_support": self.answer_support,
            "provenance": self.provenance, "adjudicated": self.adjudicated,
            "license": self.license, "version": self.version,
            "translations": self.translations,
        }
        out.update(self.extra)
        return out


def load_items(path: str | Path) -> list[Item]:
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(Item.from_dict(json.loads(line)))
    return items


def save_items(items: list[Item], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")


def validate_item(item: Item, U: set, id_parser: Optional[Callable[[str], object]] = None) -> list[tuple[str, str]]:
    """Return a list of (level, message) issues; level in {'error','warn'}. Empty = clean."""
    issues: list[tuple[str, str]] = []
    err = lambda m: issues.append(("error", m))
    warn = lambda m: issues.append(("warn", m))

    if item.question_type not in QUESTION_TYPES:
        err(f"invalid question_type {item.question_type!r}")
    if item.ambiguity not in AMBIGUITY:
        err(f"invalid ambiguity {item.ambiguity!r}")
    if not item.question.strip():
        err("empty question")

    gold = set(item.gold_citations)
    nm = set(item.near_miss_distractors)

    # existence in U (the core integrity check)
    for c in gold:
        if c not in U:
            err(f"gold citation {c!r} not in corpus ID space U")
        elif id_parser and id_parser(c) is None:
            err(f"gold citation {c!r} fails the corpus ID grammar")
    for c in nm:
        if c not in U:
            err(f"near-miss distractor {c!r} not in U")

    if gold & nm:
        err(f"near-miss distractors overlap gold: {sorted(gold & nm)}")

    # unanswerable / abstention consistency
    is_unans = item.question_type == "unanswerable"
    if is_unans != item.must_abstain:
        err(f"question_type 'unanswerable' must match must_abstain (got type={item.question_type}, must_abstain={item.must_abstain})")
    if item.must_abstain:
        if gold:
            err("unanswerable item must have empty gold_citations")
        if item.answerable:
            err("unanswerable item must have answerable=false")
        if not item.abstain_reason:
            warn("unanswerable item has no abstain_reason")
    else:
        if not gold:
            err("answerable item must have at least one gold citation")

    # answer_support sanity
    for s in item.answer_support:
        c = s.get("citation")
        if c is not None and c not in gold:
            warn(f"answer_support cites {c!r} which is not in gold_citations")
        if s.get("support") not in SUPPORT:
            err(f"answer_support has invalid support label {s.get('support')!r}")

    # distractor coverage guidance (§3): factual/retrieval should carry >=2 near-miss
    if item.question_type in {"factual", "retrieval"} and len(nm) < 2:
        warn(f"{item.question_type} item has <2 near-miss distractors ({len(nm)})")

    # trilingual layer (only checked when present; gold is language-independent)
    if item.translations:
        if not isinstance(item.translations, dict):
            err("translations must be a dict {lang: {question, gold_answer}}")
        else:
            for lang, payload in item.translations.items():
                if lang not in LANGS:
                    err(f"translation lang {lang!r} not in {sorted(LANGS)}")
                elif not isinstance(payload, dict) or not str(payload.get("question", "")).strip():
                    err(f"translation [{lang}] missing a non-empty question")

    return issues


def validate_items(items: list[Item], U: set, id_parser=None) -> dict:
    """Validate a set; returns {ok, n_items, errors, warnings, by_item}. Also checks
    item-id uniqueness."""
    by_item: dict = {}
    n_err = n_warn = 0
    ids = [it.id for it in items]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    for it in items:
        iss = validate_item(it, U, id_parser)
        if iss:
            by_item[it.id] = iss
        n_err += sum(1 for lvl, _ in iss if lvl == "error")
        n_warn += sum(1 for lvl, _ in iss if lvl == "warn")
    return {
        "ok": n_err == 0 and not dup_ids,
        "n_items": len(items),
        "errors": n_err,
        "warnings": n_warn,
        "duplicate_item_ids": dup_ids,
        "by_item": by_item,
    }
