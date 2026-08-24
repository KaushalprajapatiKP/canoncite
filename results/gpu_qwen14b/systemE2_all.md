# CANONCITE — System E2: joint discriminative exact-ID selector (ours)

reader=`llm`, model=`qwen2.5:14b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.743 | 0.095 |
| yoga_sutras | hi | 50 | 0.670 | 0.132 |
| yoga_sutras | sa | 50 | 0.620 | 0.143 |
| bhagavad_gita | en | 82 | 0.742 | 0.123 |
| bhagavad_gita | hi | 82 | 0.728 | 0.194 |
| bhagavad_gita | sa | 82 | 0.724 | 0.138 |
| dhammapada | en | 60 | 0.719 | 0.047 |
| dhammapada | hi | 60 | 0.756 | 0.098 |
| dhammapada | pi | 60 | 0.142 | 0.800 |
| upanishads | en | 50 | 0.210 | 0.000 |
| upanishads | hi | 50 | 0.220 | 0.250 |
| upanishads | sa | 50 | 0.160 | 0.000 |
| thirukkural | en | 70 | 0.757 | 0.115 |
| thirukkural | hi | 70 | 0.721 | 0.180 |
| thirukkural | ta | 70 | 0.579 | 0.383 |
| constitution_india | en | 70 | 0.502 | 0.233 |
| constitution_india | hi | 70 | 0.555 | 0.265 |
| ramayana | en | 60 | 0.142 | 0.875 |
| ramayana | hi | 60 | 0.150 | 0.889 |
| ramayana | sa | 60 | 0.142 | 0.929 |
| bible | en | 80 | 0.500 | 0.057 |
| bible | hi | 80 | 0.463 | 0.256 |
| guru_granth_sahib | en | 60 | 0.150 | 0.900 |
| guru_granth_sahib | hi | 60 | 0.183 | 0.842 |
| guru_granth_sahib | pa | 60 | 0.167 | 0.833 |
| mahabharata | en | 40 | 0.250 | 0.667 |
| mahabharata | hi | 40 | 0.329 | 0.250 |
| mahabharata | sa | 40 | 0.312 | 0.375 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.472  ·  MAR 0.311
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.423  ·  MAR 0.387
- **Cross-lingual attribution gap:** 0.048 absolute (10% relative drop)

## How to read this

- **Verifier activity:** 485 repairs, 848 abstentions across 28 cells.
