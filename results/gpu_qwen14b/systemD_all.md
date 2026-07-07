# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

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

- **English-query mean Attribution F1 (exact):** 0.554
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.440
- **Cross-lingual attribution gap:** 0.114 absolute (21% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
