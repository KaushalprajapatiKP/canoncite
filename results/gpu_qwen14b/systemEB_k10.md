# CANONCITE — System E: exact-ID verify + repair

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.770 | 0.224 |
| bhagavad_gita | hi | 82 | 0.683 | 0.262 |
| bhagavad_gita | sa | 82 | 0.688 | 0.299 |
| yoga_sutras | en | 50 | 0.824 | 0.136 |
| yoga_sutras | hi | 50 | 0.636 | 0.200 |
| yoga_sutras | sa | 50 | 0.629 | 0.152 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.797  ·  MAR 0.180
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.659  ·  MAR 0.228
- **Cross-lingual attribution gap:** 0.138 absolute (17% relative drop)

## How to read this

- **Verifier activity:** 15 repairs, 85 abstentions across 6 cells.
