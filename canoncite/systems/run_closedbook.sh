#!/usr/bin/env bash
# Closed-book base-competence control (paper Table 5.3).
# Reader = openai/gpt-oss-120b via Groq -- the SAME weights as the C/E2/D 120B column,
# so the control is matched to the reader whose RAG numbers it contextualises.
# No retrieval, so no BGE-M3/reranker load: this is purely API-bound.
# Checkpointed + resumable: re-running skips completed (corpus,lang) cells.
set -u
cd "$(dirname "$0")/../.."
PY="./.venv-ret/bin/python -u"
R=results/gpu_qwen14b
export PYTHONPATH=.
set -a; source canoncite/seed/.llm.env.groq120b; set +a

# n=20 items/cell: Groq free tier throttles hard, and 20 x 28 cells is enough
# to read both control signals (per-language competence, per-corpus memorisation).
$PY -m canoncite.systems.sweep --system CB --reader llm --limit 20 \
  --model openai/gpt-oss-120b \
  --checkpoint $R/systemCB_oss120b.jsonl --out $R/systemCB_oss120b.md \
  && echo "CLOSEDBOOK_CHAIN_COMPLETE"
