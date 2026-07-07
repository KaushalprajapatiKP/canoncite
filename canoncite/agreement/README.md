# CANONCITE — reviewer agreement & adjudication

Turns the raw reviewer `verdicts` (produced by the web review app, `canoncite/review/`)
into (a) an **inter-annotator agreement** report and (b) an **adjudicated gold set**.
Implements Step 4 (agreement reporting) and Step 3 (adjudication) of
`BENCHMARK_DESIGN.md` §4.

Everything here is **pure stdlib** — the statistics (MASI distance, Krippendorff's
alpha, Cohen's / Fleiss' kappa) are implemented from scratch, so there is no
numpy / scipy / nltk dependency and the math is fully unit-tested.

## Verdict schema

One row per **reviewer × item** (Supabase table `verdicts`), reviewer identified by phone:

```json
{"reviewer": "<phone>", "corpus": "bhagavad_gita", "item_id": "gita-seed-0001",
 "status": "approve|reject|edit",
 "edits": {"gold_citations": ["2.48"], "question_type": "factual", "ambiguity": "high"},
 "notes": "...", "ts": 1710000000}
```

`edits` is present only when `status == "edit"`.

## Pipeline

```bash
# 1. Pull verdicts from Supabase -> canoncite/data/reviews/<corpus>/verdicts.jsonl
PYTHONPATH=. python canoncite/agreement/fetch.py [--corpus bhagavad_gita]

# 2. Report inter-annotator agreement (add --json for the full machine-readable report)
PYTHONPATH=. python canoncite/agreement/agreement.py [--corpus bhagavad_gita]

# 3. Adjudicate into gold -> canoncite/data/items/<corpus>/gold.jsonl
PYTHONPATH=. python canoncite/agreement/adjudicate.py [--corpus bhagavad_gita]

# tests (known-value unit tests for every metric + the adjudication logic)
PYTHONPATH=. python canoncite/agreement/tests/test_agreement.py
PYTHONPATH=. python -m pytest canoncite/agreement/tests -q
```

`fetch.py` reads the Supabase project URL + publishable key from `canoncite/.env`
(free-form keys — it recognises a `*.supabase.co` URL or reconstructs one from
`project_id` / the dashboard `project_link`, and recognises an `sb_...` / JWT
key, preferring a key whose name mentions api/key/publishable/anon). It calls
`GET {url}/rest/v1/verdicts?select=*` with `apikey` + `Authorization: Bearer`
headers and pages by `limit`/`offset`. `--print-config` shows the resolved URL
(key redacted) without fetching.

## The metrics

### Citation-set agreement — Krippendorff's α with MASI distance

Reviewers annotate an **overlapping set** of gold citations, so ordinary kappa is
wrong (it treats every distinct set as an unrelated category). We use
**Krippendorff's α** with the **MASI distance** (Passonneau 2006), which credits
partial set overlap.

The "value" each reviewer assigns to an item is the **effective gold set**:

| status  | effective gold set        |
|---------|---------------------------|
| approve | the item's original gold  |
| edit    | `edits.gold_citations`    |
| reject  | ∅ (asserts "no correct citation") |

**MASI** similarity = Jaccard × monotonicity, where monotonicity is
`1` (identical), `2/3` (subset), `1/3` (overlap, neither a subset), `0` (disjoint);
MASI *distance* = `1 − similarity`. **α** = `1 − Do/De`, where `Do` is the mean
within-item pairwise distance and `De` the mean distance over all value pairs in
the dataset. α = 1 is perfect agreement, 0 is chance, negative is systematic
disagreement.

### Categorical agreement — Cohen's / Fleiss' κ

On the `status` label and on the edited `question_type` / `ambiguity` labels.
**Cohen's κ** when every item has exactly two raters, else **Fleiss' κ**
(generalized to an uneven number of raters per item). κ = `(pₒ − pₑ)/(1 − pₑ)`:
observed agreement corrected for chance.

Agreement is reported **overall, per corpus, and per question_type** (interpretive
items are expected to score lower — that is informative, not disqualifying).
Items with `< 2` reviewers are skipped; a label with only one category yields
`n/a` (κ/α undefined), not a crash.

## Adjudication → gold

For each reviewed item `adjudicate.py` decides:

| resolution            | condition                                                      | effect |
|-----------------------|---------------------------------------------------------------|--------|
| `verified`            | ≥2 reviewers, none reject, agree on gold + question_type + ambiguity | agreed values applied; `verified=true`, `adjudicated=true` |
| `needs_adjudication`  | reject/approve split, all-reject, or conflicting edits         | `needs_adjudication=true`, disagreement recorded on the item |
| `insufficient_reviews`| exactly one reviewer                                          | kept, `verified=false` |
| `unreviewed`          | no verdicts                                                   | dropped (not written) |

Output `canoncite/data/items/<corpus>/gold.jsonl` — every written item is checked
with `canoncite.items.validate_item` against the corpus ID space `U` (from
`corpus_index.jsonl`); items flagged `needs_adjudication` stay in the file so an
adjudicator can find them. A summary (resolution counts, validation errors, and
the list of items needing adjudication) is printed.

## Quality-gate targets (`BENCHMARK_DESIGN.md` §4)

| metric                                   | acceptable | aim   |
|------------------------------------------|-----------:|------:|
| Krippendorff's α (citation sets, MASI)   | **≥ 0.67** | ≥ 0.80 |
| Cohen's / Fleiss' κ (categorical labels) | **≥ 0.60** | ≥ 0.80 |

`agreement.py` prints `PASS` / `FAIL` against these thresholds
(`ALPHA_TARGET = 0.67`, `KAPPA_TARGET = 0.60` in `__init__.py`).
