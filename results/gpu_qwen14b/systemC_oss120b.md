# CANONCITE — System C: hybrid + cross-encoder rerank

reader=`llm`, model=`gpt-oss-120b` · k=5, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.774 | 0.271 |
| bhagavad_gita | hi | 82 | 0.756 | 0.286 |
| bhagavad_gita | sa | 82 | 0.729 | 0.310 |
| yoga_sutras | en | 50 | 0.822 | 0.205 |
| yoga_sutras | hi | 50 | 0.746 | 0.295 |
| yoga_sutras | sa | 50 | 0.634 | 0.359 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.798  ·  MAR 0.238
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.716  ·  MAR 0.313
- **Cross-lingual attribution gap:** 0.082 absolute (10% relative drop)
