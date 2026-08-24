# CANONCITE — System E: exact-ID verify + repair

reader=`llm`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.774 | 0.250 |
| bhagavad_gita | hi | 82 | 0.670 | 0.226 |

## Summary

- **Cells:** 2
- **English-query mean Attribution F1 (exact):** 0.774  ·  MAR 0.250
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.670  ·  MAR 0.226
- **Cross-lingual attribution gap:** 0.104 absolute (13% relative drop)

## How to read this

- **Verifier activity:** 18 repairs, 34 abstentions across 2 cells.
