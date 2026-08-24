# CANONCITE — System C: hybrid + cross-encoder rerank

reader=`llm`, model=`llama-3.3-70b-versatile` · k=5, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.787 | 0.254 |
| bhagavad_gita | hi | 82 | 0.767 | 0.235 |
| bhagavad_gita | sa | 82 | 0.689 | 0.338 |
| yoga_sutras | en | 50 | 0.807 | 0.209 |
| yoga_sutras | hi | 50 | 0.753 | 0.238 |
| yoga_sutras | sa | 50 | 0.653 | 0.289 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.797  ·  MAR 0.232
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.715  ·  MAR 0.275
- **Cross-lingual attribution gap:** 0.082 absolute (10% relative drop)
