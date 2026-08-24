# CANONCITE — System E2: joint discriminative exact-ID selector (ours)

reader=`llm`, model=`gpt-oss-120b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.740 | 0.125 |
| bhagavad_gita | hi | 82 | 0.748 | 0.123 |
| bhagavad_gita | sa | 82 | 0.691 | 0.177 |
| yoga_sutras | en | 50 | 0.670 | 0.000 |
| yoga_sutras | hi | 50 | 0.653 | 0.118 |
| yoga_sutras | sa | 50 | 0.633 | 0.065 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.705  ·  MAR 0.062
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.681  ·  MAR 0.121
- **Cross-lingual attribution gap:** 0.023 absolute (3% relative drop)

## How to read this

- **Verifier activity:** 100 repairs, 108 abstentions across 6 cells.
