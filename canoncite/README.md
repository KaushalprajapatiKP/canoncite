# CANONCITE — benchmark code

Implementation of the cross-corpus canonical-citation attribution benchmark
specified in [`../BENCHMARK_DESIGN.md`](../BENCHMARK_DESIGN.md). Re-anchored on the
prior-art findings in [`../RELATED_WORK.md`](../RELATED_WORK.md).

## Status (v0)

- [x] **Metric harness** — `metrics.py`, `eval.py`, `ids.py` (deterministic; 20 unit tests).
- [x] **Item schema + validator** — `items.py`, `corpus_io.py` (integrity: gold ⊆ U).
- [x] **All 10 corpora built** — `data/corpora/*/corpus_index.jsonl`, **188,557 citable units**, public-domain text, each with a `VALIDATION.md` + sha256. See [`CORPORA.md`](./CORPORA.md).
- [ ] 60–100 double-annotated Gita items + agreement number — next.
- [ ] Naive-RAG baseline run scored by the harness.

Per-corpus span/adjacency rules are registered in `ids.py` for the numeric ID grammars (Gita, Dhammapada, Yoga Sutras, Ramayana, Mahabharata, Thirukkural, Bible, GGS); heterogeneous IDs (Constitution, Upanishads) use exact-ID matching.

**Corpus builders** (`corpus/build_*.py`) need `requirements.txt` (`requests`, `beautifulsoup4`, `indic-transliteration`); the harness itself needs nothing. Copyright-restricted English (GGS Sant Singh Khalsa, Ramayana IIT-K) is gitignored/private — released corpora are public-domain only.

## Layout

```
canoncite/
├── ids.py        # canonical-ID parsing + span/adjacency matching (per corpus)
├── metrics.py    # CER, CG, Attribution P/R/F1 (exact+span), MAR, NMR, abstention — pure fns
├── eval.py       # GoldItem / SystemOutput dataclasses, score_item(), aggregate(), format_table()
└── tests/
    └── test_metrics.py   # worked-example tests from BENCHMARK_DESIGN.md §5
```

## Metrics (see BENCHMARK_DESIGN.md §5)

| Metric | Determinism | Meaning |
|---|---|---|
| **CER** Citation Existence Rate | exact | cited ids that exist in the corpus ID space `U` |
| **CG** Citation Groundedness | exact | cited ids that were in the retrieved set `R` |
| **Attribution P/R/F1 (exact)** | exact | cited set vs gold set, exact-id match |
| **Attribution P/R/F1 (span)** | exact | credits adjacent ids within a corpus tolerance window |
| **MAR** Misattribution Rate | exist=exact, support=judge | answers citing ≥1 non-existent **or** unsupported id |
| **NMR** Near-miss Misattribution Rate | exact | wrong cites that are real-but-adjacent distractors |
| **Abstention Accuracy / Over-citation** | exact | behavior on `unanswerable` items |

`MAR-exist` and `NMR` are fully NLI-free (the clean signal); `MAR-support` uses a
content-support judge whose labels are calibrated against the benchmark's human
`answer_support` annotations (a C2 contribution).

## Run the tests

```bash
PYTHONPATH=. python canoncite/tests/test_metrics.py     # stdlib only, no deps
# or
PYTHONPATH=. python -m pytest canoncite/tests -q
```

## Usage sketch

```python
from canoncite.eval import GoldItem, SystemOutput, score_item, aggregate, format_table

gold = [GoldItem("g1", "bhagavad_gita", gold_citations={"2.47", "2.48"},
                 near_miss_distractors={"5.18"})]
outs = {"g1": SystemOutput("g1", cited_ids={"2.47", "5.18"},
                           retrieved_ids={"2.47", "2.48", "5.18"})}
U = {"2.47", "2.48", "5.18", ...}        # corpus_index ID space

results = [score_item(g, outs[g.id], U) for g in gold]
print(format_table(aggregate(results)))
```
