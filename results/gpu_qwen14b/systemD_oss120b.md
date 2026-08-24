# CANONCITE — System D: Self-RAG/CRAG SOTA baseline

reader=`llm`, model=`gpt-oss-120b` · k=8, retrieval=rerank

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.742 | 0.171 |
| bhagavad_gita | hi | 82 | 0.722 | 0.188 |
| bhagavad_gita | sa | 82 | 0.699 | 0.239 |
| yoga_sutras | en | 50 | 0.777 | 0.047 |
| yoga_sutras | hi | 50 | 0.703 | 0.205 |
| yoga_sutras | sa | 50 | 0.673 | 0.175 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.759  ·  MAR 0.109
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.699  ·  MAR 0.202
- **Cross-lingual attribution gap:** 0.060 absolute (8% relative drop)

## How to read this

- **Verifier activity:** 1 repairs, 59 abstentions across 6 cells.
