# CANONCITE — System A: naive RAG (BM25)

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.728 | 0.056 |
| yoga_sutras | hi | 50 | 0.140 | 0.800 |
| yoga_sutras | sa | 50 | 0.140 | 0.857 |
| bhagavad_gita | en | 82 | 0.710 | 0.183 |
| bhagavad_gita | hi | 82 | 0.183 | 0.750 |
| bhagavad_gita | sa | 82 | 0.244 | 0.619 |
| dhammapada | en | 60 | 0.756 | 0.213 |
| dhammapada | hi | 60 | 0.212 | 0.600 |
| dhammapada | pi | 60 | 0.167 | 0.333 |
| upanishads | en | 50 | 0.567 | 0.138 |
| upanishads | hi | 50 | 0.196 | 0.200 |
| upanishads | sa | 50 | 0.196 | 0.200 |
| thirukkural | en | 70 | 0.720 | 0.218 |
| thirukkural | hi | 70 | 0.100 | 0.667 |
| thirukkural | ta | 70 | 0.100 | 0.900 |
| constitution_india | en | 70 | 0.100 | 1.000 |
| constitution_india | hi | 70 | 0.107 | 0.000 |
| ramayana | en | 60 | 0.133 | 1.000 |
| ramayana | hi | 60 | 0.133 | — |
| ramayana | sa | 60 | 0.133 | — |
| bible | en | 80 | 0.125 | — |
| bible | hi | 80 | 0.125 | — |
| guru_granth_sahib | en | 60 | 0.133 | 1.000 |
| guru_granth_sahib | hi | 60 | 0.203 | 0.333 |
| guru_granth_sahib | pa | 60 | 0.222 | 0.455 |
| mahabharata | en | 40 | 0.252 | 0.500 |
| mahabharata | hi | 40 | 0.263 | 0.000 |
| mahabharata | sa | 40 | 0.258 | 0.333 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.422  ·  MAR 0.479
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.173  ·  MAR 0.470
- **Cross-lingual attribution gap:** 0.249 absolute (59% relative drop)
