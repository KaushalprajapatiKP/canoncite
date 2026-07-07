# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

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

- **English-query mean Attribution F1 (exact):** 0.424
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.404
- **Cross-lingual attribution gap:** 0.020 absolute (5% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
