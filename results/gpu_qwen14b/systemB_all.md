# CANONCITE — System B: hybrid BM25+dense RRF

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=hybrid

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.807 | 0.119 |
| yoga_sutras | hi | 50 | 0.612 | 0.152 |
| yoga_sutras | sa | 50 | 0.609 | 0.065 |
| bhagavad_gita | en | 82 | 0.746 | 0.212 |
| bhagavad_gita | hi | 82 | 0.648 | 0.283 |
| bhagavad_gita | sa | 82 | 0.621 | 0.317 |
| dhammapada | en | 60 | 0.804 | 0.275 |
| dhammapada | hi | 60 | 0.709 | 0.245 |
| dhammapada | pi | 60 | 0.167 | 0.714 |
| upanishads | en | 50 | 0.521 | 0.214 |
| upanishads | hi | 50 | 0.689 | 0.154 |
| upanishads | sa | 50 | 0.681 | 0.167 |
| thirukkural | en | 70 | 0.750 | 0.283 |
| thirukkural | hi | 70 | 0.680 | 0.179 |
| thirukkural | ta | 70 | 0.629 | 0.302 |
| constitution_india | en | 70 | 0.100 | — |
| constitution_india | hi | 70 | 0.100 | 1.000 |
| ramayana | en | 60 | 0.133 | 1.000 |
| ramayana | hi | 60 | 0.133 | 1.000 |
| ramayana | sa | 60 | 0.133 | 1.000 |
| bible | en | 80 | 0.125 | — |
| bible | hi | 80 | 0.125 | — |
| guru_granth_sahib | en | 60 | 0.167 | 0.778 |
| guru_granth_sahib | hi | 60 | 0.225 | 0.538 |
| guru_granth_sahib | pa | 60 | 0.192 | 0.714 |
| mahabharata | en | 40 | 0.243 | 0.833 |
| mahabharata | hi | 40 | 0.260 | 0.500 |
| mahabharata | sa | 40 | 0.275 | 0.250 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.440  ·  MAR 0.464
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.416  ·  MAR 0.446
- **Cross-lingual attribution gap:** 0.024 absolute (5% relative drop)
