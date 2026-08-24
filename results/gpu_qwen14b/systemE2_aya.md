# CANONCITE — System E2: joint discriminative exact-ID selector (ours)

reader=`llm`, model=`aya-expanse:8b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.693 | 0.103 |
| yoga_sutras | hi | 50 | 0.603 | 0.143 |
| yoga_sutras | sa | 50 | 0.430 | 0.375 |
| bhagavad_gita | en | 82 | 0.675 | 0.206 |
| bhagavad_gita | hi | 82 | 0.608 | 0.286 |
| bhagavad_gita | sa | 82 | 0.476 | 0.455 |
| dhammapada | en | 60 | 0.686 | 0.087 |
| dhammapada | hi | 60 | 0.678 | 0.087 |
| dhammapada | pi | 60 | 0.033 | 1.000 |
| upanishads | en | 50 | 0.163 | 0.706 |
| upanishads | hi | 50 | 0.200 | 0.562 |
| upanishads | sa | 50 | 0.140 | 0.895 |
| thirukkural | en | 70 | 0.721 | 0.164 |
| thirukkural | hi | 70 | 0.550 | 0.275 |
| thirukkural | ta | 70 | 0.550 | 0.369 |
| constitution_india | en | 70 | 0.521 | 0.352 |
| constitution_india | hi | 70 | 0.381 | 0.547 |
| ramayana | en | 60 | 0.058 | 0.979 |
| ramayana | hi | 60 | 0.083 | 0.977 |
| ramayana | sa | 60 | 0.008 | 0.978 |
| bible | en | 80 | 0.627 | 0.241 |
| bible | hi | 80 | 0.577 | 0.339 |
| guru_granth_sahib | en | 60 | 0.117 | 0.961 |
| guru_granth_sahib | hi | 60 | 0.108 | 0.909 |
| guru_granth_sahib | pa | 60 | 0.075 | 0.976 |
| mahabharata | en | 40 | 0.150 | 0.939 |
| mahabharata | hi | 40 | 0.242 | 0.840 |
| mahabharata | sa | 40 | 0.212 | 0.857 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.441  ·  MAR 0.474
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.331  ·  MAR 0.604
- **Cross-lingual attribution gap:** 0.110 absolute (25% relative drop)

## How to read this

- **Verifier activity:** 820 repairs, 437 abstentions across 28 cells.
