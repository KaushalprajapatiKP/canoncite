# CANONCITE — System C: hybrid + cross-encoder rerank

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.809 | 0.163 |
| yoga_sutras | hi | 50 | 0.689 | 0.231 |
| yoga_sutras | sa | 50 | 0.620 | 0.235 |
| bhagavad_gita | en | 82 | 0.755 | 0.231 |
| bhagavad_gita | hi | 82 | 0.757 | 0.235 |
| bhagavad_gita | sa | 82 | 0.712 | 0.309 |
| dhammapada | en | 60 | 0.815 | 0.353 |
| dhammapada | hi | 60 | 0.788 | 0.275 |
| dhammapada | pi | 60 | 0.133 | 1.000 |
| upanishads | en | 50 | 0.303 | 0.500 |
| upanishads | hi | 50 | 0.369 | 0.280 |
| upanishads | sa | 50 | 0.331 | 0.400 |
| thirukkural | en | 70 | 0.775 | 0.297 |
| thirukkural | hi | 70 | 0.739 | 0.306 |
| thirukkural | ta | 70 | 0.625 | 0.328 |
| constitution_india | en | 70 | 0.107 | 0.000 |
| constitution_india | hi | 70 | 0.100 | — |
| ramayana | en | 60 | 0.142 | 0.833 |
| ramayana | hi | 60 | 0.158 | 0.778 |
| ramayana | sa | 60 | 0.150 | 0.900 |
| bible | en | 80 | 0.125 | — |
| bible | hi | 80 | 0.125 | — |
| guru_granth_sahib | en | 60 | 0.150 | 0.875 |
| guru_granth_sahib | hi | 60 | 0.172 | 0.882 |
| guru_granth_sahib | pa | 60 | 0.167 | 0.800 |
| mahabharata | en | 40 | 0.260 | 0.667 |
| mahabharata | hi | 40 | 0.327 | 0.375 |
| mahabharata | sa | 40 | 0.312 | 0.375 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.424  ·  MAR 0.435
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.404  ·  MAR 0.482
- **Cross-lingual attribution gap:** 0.020 absolute (5% relative drop)
