# CANONCITE — System E: exact-ID verify + repair

reader=`top1`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.691 | 0.143 |
| bhagavad_gita | hi | 82 | 0.189 | 0.500 |
| bhagavad_gita | sa | 82 | 0.244 | 0.556 |
| yoga_sutras | en | 50 | 0.660 | 0.033 |
| yoga_sutras | hi | 50 | 0.120 | 1.000 |
| yoga_sutras | sa | 50 | 0.140 | 0.750 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.676  ·  MAR 0.088
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.173  ·  MAR 0.701
- **Cross-lingual attribution gap:** 0.503 absolute (74% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (`reader=top1`): it measures only *does retrieval rank the exact correct unit id first?* An LLM reader goes on top.
- **Verifier activity:** 32 repairs, 277 abstentions across 6 cells.
