"""Load a frozen `corpus_index.jsonl` and expose its canonical ID space `U`.

`U` is the single source of truth for "does this citation exist" (BENCHMARK_DESIGN.md
§1). Every gold/near-miss citation in an item must be a member of its corpus's `U`.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_corpus_index(path: str | Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def id_space(records: list[dict]) -> set[str]:
    """The set of all citable ids `U`. Errors on duplicate ids (a build bug)."""
    ids = [r["id"] for r in records]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"corpus_index has duplicate ids: {sorted(dupes)[:10]}")
    return set(ids)


def load_id_space(path: str | Path) -> set[str]:
    return id_space(load_corpus_index(path))
