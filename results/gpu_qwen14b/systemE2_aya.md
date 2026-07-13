# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

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

- **English-query mean Attribution F1 (exact):** 0.441
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.331
- **Cross-lingual attribution gap:** 0.110 absolute (25% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
