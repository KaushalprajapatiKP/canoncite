# CANONCITE — System E: exact-ID verify + repair

reader=`top1`, model=`qwen2.5:14b` · k=5, retrieval=bm25

| Corpus | Query lang | N | Attribution F1 (exact) | Misattribution Rate |
|---|---|---:|---:|---:|
| bhagavad_gita | en | 82 | 0.724 | 0.177 |
| bhagavad_gita | hi | 82 | 0.646 | 0.182 |
| bhagavad_gita | sa | 82 | 0.648 | 0.254 |
| yoga_sutras | en | 50 | 0.677 | 0.031 |
| yoga_sutras | hi | 50 | 0.530 | 0.115 |
| yoga_sutras | sa | 50 | 0.530 | 0.042 |

## Summary

- **Cells:** 6
- **English-query mean Attribution F1 (exact):** 0.701  ·  MAR 0.104
- **Cross-lingual (hi/native) mean Attribution F1 (exact):** 0.588  ·  MAR 0.148
- **Cross-lingual attribution gap:** 0.112 absolute (16% relative drop)

## How to read this

- This is a **lexical-only, no-LLM lower bound** (`reader=top1`): it measures only *does retrieval rank the exact correct unit id first?* An LLM reader goes on top.
- **Verifier activity:** 52 repairs, 138 abstentions across 6 cells.
