# CANONCITE — System E: exact-ID verify + repair

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.754 | 0.227 |
| bhagavad_gita | hi | 82 | 0.753 | 0.235 |
| bhagavad_gita | sa | 82 | 0.695 | 0.328 |
| yoga_sutras | en | 50 | 0.799 | 0.186 |
| yoga_sutras | hi | 50 | 0.720 | 0.205 |
| yoga_sutras | sa | 50 | 0.624 | 0.294 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.776  ·  MAR 0.207
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.698  ·  MAR 0.266
- **Cross-lingual attribution gap:** 0.078 absolute (10% relative drop)

## How to read this

- **Verifier activity:** 16 repairs, 79 abstentions across 6 cells.
