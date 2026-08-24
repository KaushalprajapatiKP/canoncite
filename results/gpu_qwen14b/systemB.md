# CANONCITE — System B: hybrid BM25+dense RRF

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=hybrid

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.754 | 0.209 |
| bhagavad_gita | hi | 82 | 0.660 | 0.250 |
| bhagavad_gita | sa | 82 | 0.628 | 0.317 |
| yoga_sutras | en | 50 | 0.797 | 0.167 |
| yoga_sutras | hi | 50 | 0.622 | 0.121 |
| yoga_sutras | sa | 50 | 0.593 | 0.097 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.776  ·  MAR 0.188
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.626  ·  MAR 0.196
- **Cross-lingual attribution gap:** 0.150 absolute (19% relative drop)
