#!/usr/bin/env bash
# Reader panel: gpt-oss-120b (OpenAI open weights) via Cerebras ($5 credits, ~30 RPM).
# Full pilot chain C -> E2 -> D, run FROM THE MAC; retrieval local via .venv-ret.
# Checkpointed + resumable: re-running skips completed (corpus,lang) cells.
set -u
cd "$(dirname "$0")/../.."
PY=./.venv-ret/bin/python
R=results/gpu_qwen14b
M=gpt-oss-120b
export PYTHONPATH=.
# Provider pin (gitignored env file; exported env beats .llm.env's setdefault).
set -a; source canoncite/seed/.llm.env.cerebras; set +a

$PY -m canoncite.systems.sweep --system C  --reader llm --k 5 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemC_oss120b.jsonl  --out $R/systemC_oss120b.md \
  && \
$PY -m canoncite.systems.sweep --system E2 --retrieval rerank --reader llm --k 8 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemE2_oss120b.jsonl --out $R/systemE2_oss120b.md \
  && \
$PY -m canoncite.systems.sweep --system D  --retrieval rerank --reader llm --k 8 \
  --corpora bhagavad_gita yoga_sutras --model $M \
  --checkpoint $R/systemD_oss120b.jsonl  --out $R/systemD_oss120b.md \
  && echo "OSS120B_CHAIN_COMPLETE"
