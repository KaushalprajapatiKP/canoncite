#!/usr/bin/env bash
# Reader #3 panel: Llama-3.3-70B via Groq free tier, run FROM THE MAC (no GPU box).
# Retrieval (BGE-M3 + reranker) runs locally via .venv-ret; llm.py sleeps through 429s,
# so the chain stalls through Groq quota windows instead of failing.
# Pilot corpora (gita + yoga), sequential C -> E2 -> D, checkpointed + resumable:
# re-running this script skips every completed (corpus,lang) cell.
set -u
cd "$(dirname "$0")/../.."
PY=./.venv-ret/bin/python
R=results/gpu_qwen14b
M=llama-3.3-70b-versatile
export PYTHONPATH=.
# Explicit provider pin: exported env beats .llm.env (load_env uses setdefault),
# so this chain stays on Groq even when .llm.env points at another provider.
# Key lives in the gitignored per-provider env file, never in this tracked script.
set -a; source canoncite/seed/.llm.env.groq; set +a

$PY -m canoncite.systems.sweep --system C  --reader llm --k 5 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemC_groq70b.jsonl  --out $R/systemC_groq70b.md \
  && \
$PY -m canoncite.systems.sweep --system E2 --retrieval rerank --reader llm --k 8 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemE2_groq70b.jsonl --out $R/systemE2_groq70b.md \
  && \
$PY -m canoncite.systems.sweep --system D  --retrieval rerank --reader llm --k 8 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemD_groq70b.jsonl  --out $R/systemD_groq70b.md \
  && echo "GROQ70B_CHAIN_COMPLETE"
