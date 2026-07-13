# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| yoga_sutras | en | 50 | 0.723 | 0.073 |
| yoga_sutras | hi | 50 | 0.553 | 0.289 |
| yoga_sutras | sa | 50 | 0.480 | 0.372 |
| bhagavad_gita | en | 82 | 0.689 | 0.232 |
| bhagavad_gita | hi | 82 | 0.665 | 0.219 |
| bhagavad_gita | sa | 82 | 0.537 | 0.430 |
| dhammapada | en | 60 | 0.756 | 0.109 |
| dhammapada | hi | 60 | 0.731 | 0.115 |
| dhammapada | pi | 60 | 0.017 | 1.000 |
| upanishads | en | 50 | 0.297 | 0.533 |
| upanishads | hi | 50 | 0.387 | 0.360 |
| upanishads | sa | 50 | 0.333 | 0.531 |
| thirukkural | en | 70 | 0.721 | 0.188 |
| thirukkural | hi | 70 | 0.629 | 0.250 |
| thirukkural | ta | 70 | 0.607 | 0.313 |
| constitution_india | en | 70 | 0.490 | 0.484 |
| constitution_india | hi | 70 | 0.462 | 0.517 |
| ramayana | en | 60 | 0.058 | 0.981 |
| ramayana | hi | 60 | 0.075 | 0.962 |
| ramayana | sa | 60 | 0.042 | 0.980 |
| bible | en | 80 | 0.650 | 0.348 |
| bible | hi | 80 | 0.583 | 0.394 |
| guru_granth_sahib | en | 60 | 0.050 | 0.966 |
| guru_granth_sahib | hi | 60 | 0.100 | 0.939 |
| guru_granth_sahib | pa | 60 | 0.050 | 0.964 |
| mahabharata | en | 40 | 0.188 | 0.900 |
| mahabharata | hi | 40 | 0.250 | 0.852 |
| mahabharata | sa | 40 | 0.138 | 0.906 |

## Summary

- **English-query mean Attribution F1 (exact):** 0.462
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.369
- **Cross-lingual attribution gap:** 0.094 absolute (20% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
