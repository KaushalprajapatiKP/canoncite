#!/bin/bash
# Reordered scale chain: C (done) -> E2 -> B -> D. Fast, high-value systems first;
# slow SOTA baseline (D) last, so a box drop still leaves the A->B->C->E2 story intact.
# Each sweep checkpoints per (corpus,lang) cell and resume-skips completed cells.
cd ~/shastra || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
R="results/gpu_qwen14b"

run() {
  PYTHONPATH=. python3 -m canoncite.systems.sweep "$@" \
    --reader llm --model qwen2.5:14b
}

run --system C  --k 5                    --checkpoint $R/systemC_all.jsonl  --out $R/systemC_all.md
run --system E2 --retrieval rerank --k 8 --checkpoint $R/systemE2_all.jsonl --out $R/systemE2_all.md
run --system B  --k 5                    --checkpoint $R/systemB_all.jsonl  --out $R/systemB_all.md
run --system D  --retrieval rerank --k 8 --checkpoint $R/systemD_all.jsonl  --out $R/systemD_all.md

echo "CHAIN_COMPLETE" > /tmp/chain_verdict.txt
