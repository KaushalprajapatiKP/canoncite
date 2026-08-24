# CANONCITE — System C: hybrid + cross-encoder rerank

reader=`llm`, model=`aya-expanse:8b` · k=5, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.744 | 0.341 |
| yoga_sutras | hi | 50 | 0.595 | 0.368 |
| yoga_sutras | sa | 50 | 0.465 | 0.543 |
| bhagavad_gita | en | 82 | 0.715 | 0.343 |
| bhagavad_gita | hi | 82 | 0.703 | 0.319 |
| bhagavad_gita | sa | 82 | 0.495 | 0.532 |
| dhammapada | en | 60 | 0.766 | 0.415 |
| dhammapada | hi | 60 | 0.722 | 0.382 |
| dhammapada | pi | 60 | 0.000 | 1.000 |
| upanishads | en | 50 | 0.191 | 0.737 |
| upanishads | hi | 50 | 0.226 | 0.467 |
| upanishads | sa | 50 | 0.230 | 0.400 |
| thirukkural | en | 70 | 0.722 | 0.400 |
| thirukkural | hi | 70 | 0.629 | 0.361 |
| thirukkural | ta | 70 | 0.544 | 0.507 |
| constitution_india | en | 70 | 0.100 | 1.000 |
| constitution_india | hi | 70 | 0.107 | 0.000 |
| ramayana | en | 60 | 0.042 | 0.982 |
| ramayana | hi | 60 | 0.063 | 0.964 |
| ramayana | sa | 60 | 0.017 | 0.980 |
| bible | en | 80 | 0.125 | — |
| bible | hi | 80 | 0.125 | — |
| guru_granth_sahib | en | 60 | 0.050 | 0.964 |
| guru_granth_sahib | hi | 60 | 0.067 | 0.959 |
| guru_granth_sahib | pa | 60 | 0.022 | 0.981 |
| mahabharata | en | 40 | 0.175 | 0.929 |
| mahabharata | hi | 40 | 0.283 | 0.857 |
| mahabharata | sa | 40 | 0.154 | 0.906 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.363  ·  MAR 0.679
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.303  ·  MAR 0.619
- **Cross-lingual attribution gap:** 0.060 absolute (17% relative drop)
