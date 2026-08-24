# CANONCITE — System C: hybrid + cross-encoder rerank

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.735 | 0.250 |
| bhagavad_gita | hi | 82 | 0.747 | 0.254 |
| bhagavad_gita | sa | 82 | 0.710 | 0.309 |
| yoga_sutras | en | 50 | 0.811 | 0.186 |
| yoga_sutras | hi | 50 | 0.690 | 0.231 |
| yoga_sutras | sa | 50 | 0.613 | 0.242 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.773  ·  MAR 0.218
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.690  ·  MAR 0.259
- **Cross-lingual attribution gap:** 0.083 absolute (11% relative drop)
