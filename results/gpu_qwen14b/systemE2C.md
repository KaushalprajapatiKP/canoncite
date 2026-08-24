# CANONCITE — System E2: joint discriminative exact-ID selector (ours)

reader=`llm`, model=`qwen2.5:14b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.754 | 0.119 |
| bhagavad_gita | hi | 82 | 0.744 | 0.149 |
| bhagavad_gita | sa | 82 | 0.724 | 0.138 |
| yoga_sutras | en | 50 | 0.723 | 0.100 |
| yoga_sutras | hi | 50 | 0.683 | 0.128 |
| yoga_sutras | sa | 50 | 0.620 | 0.216 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.739  ·  MAR 0.110
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.693  ·  MAR 0.158
- **Cross-lingual attribution gap:** 0.046 absolute (6% relative drop)

## How to read this

- **Verifier activity:** 83 repairs, 81 abstentions across 6 cells.
