---
license: cc-by-4.0
language:
  - en
  - hi
  - sa
  - ta
  - pa
  - pi
task_categories:
  - question-answering
  - text-retrieval
tags:
  - citation-attribution
  - abstention
  - retrieval-augmented-generation
  - multilingual
  - cross-lingual
  - benchmark
  - low-resource
size_categories:
  - 100K<n<1M
pretty_name: CANONCITE
configs:
  - config_name: items
    data_files:
      - split: train
        path: items/*/seed_candidates.jsonl
  - config_name: corpora
    data_files:
      - split: train
        path: corpora/*/corpus_index.jsonl
  - config_name: verified
    data_files:
      - split: train
        path: verified/*/verified.jsonl
  - config_name: reviews
    data_files:
      - split: train
        path: reviews/*/*.jsonl
---

# CANONCITE

A benchmark for **exact-ID citation attribution and abstention** over ten public-domain
canonical corpora, in four scripts across four religious traditions plus Tamil ethical
literature and Indian constitutional law.

Every question is posed three ways: in English, in Hindi, and in the corpus's own native
script.

## What this measures, and why it is not the usual thing

Most attribution benchmarks ask whether a generated claim is *supported by a retrieved
passage*. That question cannot tell a correct citation from its neighbour, because both
passages look supportive. Citing Gita 2.48 when the answer lives at 2.47 passes a support
check and is still wrong.

CANONCITE scores the **exact identifier**. Each corpus is frozen as a `corpus_index.jsonl`
keyed by its own canonical scheme (`2.47` for Gita chapter.verse, `Art. 370` for the
Constitution, `Romans 8:28` for the Bible), and a system is credited only when the ID it
names is the right one. Abstention is scored as a first-class outcome, so declining to cite
is measured rather than silently rewarded.

A finding worth knowing before you use this: when a model is asked these questions with no
retrieval at all, the rate of **invented, non-existent identifiers is 0.000**. Every ID it
produces is real. It has simply attached it to the wrong passage. The failure mode here is
misattribution, not fabrication, and the two need different defences.

## Corpora

| Corpus | Units | Script | Tradition | Items |
|---|---:|---|---|---:|
| Mahabharata | 73,816 | Devanagari | Hindu | 40 |
| Guru Granth Sahib | 60,555 | Gurmukhi | Sikh | 60 |
| Bible | 31,095 | Latin | Christian | 80 |
| Ramayana | 18,761 | Devanagari | Hindu | 60 |
| Thirukkural | 1,330 | Tamil | Tamil ethical | 70 |
| Constitution of India | 1,219 | Latin / Devanagari | Constitutional law | 70 |
| Bhagavad Gita | 701 | Devanagari | Hindu | 82 |
| Upanishads | 462 | Devanagari | Hindu | 50 |
| Dhammapada | 423 | Latin (Pali) | Buddhist | 60 |
| Yoga Sutras | 195 | Devanagari | Hindu | 50 |
| **Total** | **188,557** | **4 scripts** | | **622** |

## Layout

```
corpora/<corpus>/corpus_index.jsonl   frozen citable units, keyed by canonical ID
items/<corpus>/seed_candidates.jsonl  the 622 benchmark items
verified/<corpus>/verified.jsonl      the 120-item human-verified subsample
reviews/<corpus>/annotator_*.jsonl    raw review records, pseudonymised
manifest.json                         counts, per-file sha256, sources, licences
DATASHEET.md                          full datasheet
```

**On the filename `seed_candidates.jsonl`.** This is the benchmark, all 622 items, and the
exact files every reported experiment loaded. The name is kept for reproducibility against
the released harness. "Seed" describes how the items were drafted (LLM-seeded from the
frozen corpus index), not their status.

## Human verification

A 120-item stratified subsample was independently reviewed by two annotators.

**Every label was confirmed.** The only differences between the reviewed records and their
originals are 18 citation lists in a different order. Those are set-identical, and the
scorer compares as sets, so nothing in any result moves. Agreement on the citation set was
Krippendorff's alpha-MASI 0.991 (99.2% raw agreement).

One caveat we would rather state than have you discover: on the binary accept/reject
verdict, raw agreement is 98.3% while Cohen's kappa is 0.000. That is the standard
high-agreement, low-kappa artefact of a heavily skewed label, not a disagreement between
annotators. PABAK, which corrects for the skew, is 0.967.

Review records ship pseudonymised as `annotator_A` / `annotator_B`.

## Licensing, and what is deliberately absent

Two layers, two licences:

- **Corpus text**: public domain, per source. Editions are named per corpus in
  `manifest.json` (World English Bible; G. U. Pope's Thirukkural, 1886; GRETIL Sanskrit;
  SuttaCentral Pali; and so on).
- **Items and annotations**: CC BY 4.0.

Copyright-restricted English translations are **excluded** from this release, which is what
makes it redistributable:

- **Guru Granth Sahib**: Sant Singh Khalsa's English is under copyright. Released as
  Gurmukhi original only.
- **Ramayana**: the IIT-Kanpur English is under copyright, and Griffith's public-domain
  English could not be aligned to the shloka grid. Released as Sanskrit only.
- **Mahabharata**: Ganguli's public-domain English does not align to the critical-edition
  shloka grid, so it is excluded from the released text.

The consequence matters for interpreting results: English coverage is not uniform across
corpora, and scores on those three reflect original-script retrieval only. They are not
comparable to systems that use the copyrighted translations.

## Known limitations

- **Near-miss distractors are model-declared** at item construction. They capture adjacency
  as the drafting model conceived it, not as a philologist would.
- **Non-English questions are machine-translated** (IndicTrans2) and not natively authored,
  so an unknown share of any cross-lingual gap is translationese.
- **Cells are unbalanced.** Gurmukhi and Pali contribute one condition each, so per-script
  numbers on those rest on very little data.
- **One corpus is substantially memorised.** Closed-book English F1 on the Bhagavad Gita is
  0.497, against 0.310 for the next corpus. Results there are partly parametric.

## Citation

A paper describing this benchmark is in preparation. Until it appears, please cite the
dataset:

```bibtex
@misc{canoncite2026,
  title  = {CANONCITE: A Multilingual, Multi-Tradition Benchmark for
            Canonical-Citation Attribution and Abstention},
  year   = {2026},
  note   = {Dataset. Corpus text public domain; annotations CC BY 4.0.}
}
```

## Code

The harness, the system implementations and the scoring code are at
[github.com/pralia-labs/canoncite](https://github.com/pralia-labs/canoncite).
A mirror is kept at
[github.com/KaushalprajapatiKP/canoncite](https://github.com/KaushalprajapatiKP/canoncite).
