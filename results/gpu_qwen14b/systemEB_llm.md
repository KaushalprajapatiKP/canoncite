# CANONCITE — System E: exact-ID verify + repair

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.754 | 0.209 |
| bhagavad_gita | hi | 82 | 0.659 | 0.267 |
| bhagavad_gita | sa | 82 | 0.635 | 0.290 |
| yoga_sutras | en | 50 | 0.794 | 0.119 |
| yoga_sutras | hi | 50 | 0.604 | 0.156 |
| yoga_sutras | sa | 50 | 0.579 | 0.100 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.774  ·  MAR 0.164
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.619  ·  MAR 0.203
- **Cross-lingual attribution gap:** 0.155 absolute (20% relative drop)

## How to read this

- **Verifier activity:** 9 repairs, 103 abstentions across 6 cells.
