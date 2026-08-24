# CANONCITE — System D: Self-RAG/CRAG SOTA baseline

reader=`llm`, model=`qwen2.5:14b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.777 | 0.047 |
| yoga_sutras | hi | 50 | 0.643 | 0.162 |
| yoga_sutras | sa | 50 | 0.673 | 0.154 |
| bhagavad_gita | en | 82 | 0.744 | 0.136 |
| bhagavad_gita | hi | 82 | 0.738 | 0.176 |
| bhagavad_gita | sa | 82 | 0.693 | 0.224 |
| dhammapada | en | 60 | 0.803 | 0.038 |
| dhammapada | hi | 60 | 0.764 | 0.098 |
| dhammapada | pi | 60 | 0.125 | 0.875 |
| upanishads | en | 50 | 0.677 | 0.125 |
| upanishads | hi | 50 | 0.330 | 0.321 |
| upanishads | sa | 50 | 0.223 | 0.533 |
| thirukkural | en | 70 | 0.750 | 0.172 |
| thirukkural | hi | 70 | 0.707 | 0.186 |
| thirukkural | ta | 70 | 0.636 | 0.263 |
| constitution_india | en | 70 | 0.576 | 0.361 |
| constitution_india | hi | 70 | 0.531 | 0.370 |
| ramayana | en | 60 | 0.125 | 0.909 |
| ramayana | hi | 60 | 0.158 | 0.800 |
| ramayana | sa | 60 | 0.150 | 0.889 |
| bible | en | 80 | 0.656 | 0.303 |
| bible | hi | 80 | 0.587 | 0.316 |
| guru_granth_sahib | en | 60 | 0.167 | 0.846 |
| guru_granth_sahib | hi | 60 | 0.158 | 0.833 |
| guru_granth_sahib | pa | 60 | 0.167 | 0.833 |
| mahabharata | en | 40 | 0.263 | 0.500 |
| mahabharata | hi | 40 | 0.317 | 0.500 |
| mahabharata | sa | 40 | 0.312 | 0.444 |

## Summary

- **Cells:** 28
- **English-query mean Attribution F1 (exact):** 0.554  ·  MAR 0.344
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.440  ·  MAR 0.443
- **Cross-lingual attribution gap:** 0.114 absolute (21% relative drop)

## How to read this

- **Verifier activity:** 250 repairs, 686 abstentions across 28 cells.
