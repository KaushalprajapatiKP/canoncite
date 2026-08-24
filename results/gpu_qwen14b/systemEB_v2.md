# CANONCITE — System E: exact-ID verify + repair

reader=`top1`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.760 | 0.197 |
| bhagavad_gita | hi | 82 | 0.657 | 0.237 |
| bhagavad_gita | sa | 82 | 0.628 | 0.302 |
| yoga_sutras | en | 50 | 0.797 | 0.143 |
| yoga_sutras | hi | 50 | 0.616 | 0.121 |
| yoga_sutras | sa | 50 | 0.589 | 0.067 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.778  ·  MAR 0.170
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.622  ·  MAR 0.182
- **Cross-lingual attribution gap:** 0.156 absolute (20% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (`reader=top1`): it measures only *does retrieval rank the exact correct unit id first?* An LLM reader goes on top.
- **Verifier activity:** 8 repairs, 103 abstentions across 6 cells.
