---
license: cc-by-4.0
language:
- en
- hi
- sa
- ta
- pa
- pi
language_details: >-
  en=English, hi=Hindi, sa=Sanskrit, ta=Tamil, pa=Punjabi (Gurmukhi), pi=Pali
task_categories:
- question-answering
- text-retrieval
tags:
- citation-attribution
- retrieval-augmented-generation
- multilingual
- religion
- law
- benchmark
pretty_name: CANONCITE — Canonical-Citation Attribution Benchmark
size_categories:
- 100K<n<1M
configs:
- config_name: corpora
  data_files: corpora/*/corpus_index.jsonl
- config_name: items
  data_files: items/*/seed_candidates.jsonl
---

# CANONCITE (v0) — Canonical-Citation Attribution Benchmark

**CANONCITE** is a trilingual, multi-tradition benchmark for **canonical-citation
attribution**: does a retrieval-augmented or generative system cite the *right
canonical unit* (e.g. Bhagavad Gita `2.47`, `Genesis 1:1`, Dhammapada `1.1`)
when it answers a question grounded in a fixed, citable corpus?

This public release contains **public-domain text only**, plus original
annotations under **CC BY 4.0**. Copyright-restricted translations are
deliberately excluded (see [Licensing](#licensing--exclusions)).

> **Scope disclaimer.** CANONCITE measures *textual-attribution faithfulness*.
> It is **not** an authority on the doctrine or correct interpretation of any
> tradition. Gold answers are textual-locator judgments, not endorsements of any
> interpretive position. The texts of multiple living traditions (Hindu,
> Buddhist, Sikh, Tamil-ethical, Christian) are treated with equivalent care.

## Structure

- **188,557** citable units across **10 corpora** and **5 scripts**.
- **622** benchmark items (v0 seed set).

| Corpus | Tradition | Native lang / script | Units | EN coverage | Items |
|---|---|---|---:|---:|---:|
| bhagavad_gita | Hindu | Sanskrit / Devanagari | 701 | 99.9% | 82 |
| bible | Christian | English / Latin | 31,095 | 100% | 80 |
| constitution_india | Secular-legal | English / Latin | 1,219 | 100% | 70 |
| dhammapada | Buddhist | Pali / Latin | 423 | 100% | 60 |
| guru_granth_sahib | Sikh | Punjabi / Gurmukhi | 60,555 | 0% (EN excluded) | 60 |
| mahabharata | Hindu | Sanskrit / Devanagari | 73,816 | 0% (EN excluded) | 40 |
| ramayana | Hindu | Sanskrit / Devanagari | 18,761 | 0% (EN excluded) | 60 |
| thirukkural | Tamil-ethical | Tamil / Tamil | 1,330 | 100% | 70 |
| upanishads | Hindu | Sanskrit / Devanagari | 462 | 90% | 50 |
| yoga_sutras | Hindu | Sanskrit / Devanagari | 195 | 99.5% | 50 |

Two coupled layers per corpus:

```
canoncite-v0/
├── corpora/<corpus>/corpus_index.jsonl   # citable text units (public-domain)
├── corpora/<corpus>/VALIDATION.md        # provenance, alignment notes, sha256
├── items/<corpus>/seed_candidates.jsonl  # benchmark questions (v0 seed)
└── manifest.json                          # counts, per-file sha256, sources, licenses
```

**Corpus record** (fields vary by corpus): canonical `id`, `original` /
`sanskrit` and/or `text_en`, `transliteration`, `tokens`, plus provenance
(`translation_source`, `original_source`, `source_urls`, `retrieved`).

**Item record:** `id`, `corpus`, `question`, `question_type`
(`factual` / `retrieval` / `conceptual` / `interpretive` / `unanswerable`),
`ambiguity`, `gold_citations` (⊆ the corpus id space), `near_miss_distractors`,
`gold_answer`, `must_abstain` / `abstain_reason`, `answer_support`,
`translations` (Hindi + native), and `provenance`.

> **Trilingual layer.** Each item's English `question`/`gold_answer` is the base;
> `translations` adds Hindi (`hi`) and the corpus's native language
> (`sa`/`ta`/`pa`/`pi`). Translations are machine-produced (**IndicTrans2** +
> **Claude**) and partially human-verified. Gold *citations* are
> language-independent.

> **Note on items.** v0 ships pre-review `seed_candidates.jsonl` (LLM-seeded,
> human-verification in progress). A post-review `gold.jsonl` will replace them.

## Metrics

Deterministic, retrieval-attribution metrics (no NLI needed for the core
signals):

| Metric | Meaning |
|---|---|
| **CER** — Citation Existence Rate | fraction of cited ids that exist in the corpus id space `U` |
| **CG** — Citation Groundedness | fraction of cited ids that were in the retrieved set `R` |
| **Attribution P/R/F1 (exact)** | cited set vs gold set, exact-id match |
| **Attribution P/R/F1 (span)** | credits ids adjacent within a per-corpus tolerance window |
| **MAR** — Misattribution Rate | answers citing ≥1 non-existent or unsupported id |
| **NMR** — Near-miss Misattribution Rate | wrong cites that are real-but-adjacent distractors |
| **Abstention Accuracy / Over-citation** | behavior on `unanswerable` items |

Reference implementation: `canoncite/metrics.py`, `canoncite/eval.py`,
`canoncite/ids.py` (per-corpus id grammar and span/adjacency rules).

## How to load

With the 🤗 `datasets` library:

```python
from datasets import load_dataset

# corpus text layer (one config across all corpora)
corpora = load_dataset("<org>/canoncite", "corpora")

# benchmark items
items = load_dataset("<org>/canoncite", "items")
```

Or with plain Python (stdlib) on the raw bundle:

```python
import json
from pathlib import Path

def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

gita_units = read_jsonl("canoncite-v0/corpora/bhagavad_gita/corpus_index.jsonl")
gita_items = read_jsonl("canoncite-v0/items/bhagavad_gita/seed_candidates.jsonl")
U = {u["id"] for u in gita_units}          # the corpus id space
assert set(gita_items[0]["gold_citations"]) <= U
```

Integrity of `manifest.json` (per-file sha256) is reproducible with the bundled
`build_release.py` and each corpus's `VALIDATION.md`.

## Licensing & exclusions

- **Annotations / questions:** **CC BY 4.0**.
- **Corpus text:** **public domain**, per source. Editions: Besant 1905 (Gita),
  WEB (Bible), Müller SBE (Upanishads, Dhammapada), Woods/Vivekananda 1896
  (Yoga Sutras), Griffith / Ganguli via GRETIL (Ramayana, Mahabharata — Sanskrit
  released), Pope 1886 (Thirukkural), GRETIL Sanskrit, Government-of-India
  Constitution text, and public-domain Gurmukhi via GurbaniNow/BaniDB (Guru
  Granth Sahib). See `LICENSE`/`NOTICE` and each `VALIDATION.md`.
- **Deliberately excluded (copyright / alignment):** Sant Singh Khalsa English
  (Guru Granth Sahib), IIT-Kanpur English (Ramayana), BBT/Prabhupada English
  (Gita), and unaligned Ganguli English (Mahabharata). These corpora are
  released **original-script only**; the build asserts no such text leaks in.

## Citation

```bibtex
@misc{canoncite2026,
  title        = {CANONCITE: A Trilingual, Multi-Tradition Benchmark for
                  Canonical-Citation Attribution},
  author       = {Shastra / Scripture-RAG contributors},
  year         = {2026},
  note         = {v0. Annotations CC BY 4.0; corpus text public-domain per source.},
  howpublished = {\url{https://huggingface.co/datasets/<org>/canoncite}}
}
```
