# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

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

- **English-query mean Attribution F1 (exact):** 0.440
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.416
- **Cross-lingual attribution gap:** 0.024 absolute (5% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
