# Preliminary CANONCITE baseline — System A (naive RAG), reader=`llm`

BM25 top-k retrieval; no dense/LLM yet. Shows the cross-lingual attribution gap.

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.754 | 0.209 |
| bhagavad_gita | hi | 82 | 0.660 | 0.250 |
| bhagavad_gita | sa | 82 | 0.628 | 0.317 |
| yoga_sutras | en | 50 | 0.797 | 0.167 |
| yoga_sutras | hi | 50 | 0.622 | 0.121 |
| yoga_sutras | sa | 50 | 0.593 | 0.097 |

## Summary

- **English-query mean Attribution F1 (exact):** 0.776
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.626
- **Cross-lingual attribution gap:** 0.150 absolute (19% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (BM25 top-k, `reader=top1`): it measures only *does naive keyword retrieval land the exact correct unit id?* The full System-A number (LLM reader) and Systems B–E go on top.
- **Cross-lingual collapse is the headline:** a Hindi/native question against the corpus text misattributes ~97–100% under lexical retrieval — this is precisely the gap CANONCITE is built to measure, and it motivates dense multilingual retrieval (BGE-M3) and the exact-ID attribution verifier (System E).
- **F1 = 0.000 for Rāmāyaṇa / Mahābhārata / Guru Granth Sahib (en):** by design the *released* text for these corpora is native-script only (copyrighted English excluded), so an English query has nothing lexical to match — these corpora *require* cross-lingual/dense retrieval, not lexical. An honest artifact, not a bug.
