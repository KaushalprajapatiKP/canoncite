#!/bin/bash
cd ~/shastra
export PYTHONPATH=.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
R=results/gpu_qwen14b
M=aya-expanse:8b
echo "AYA_CHAIN_START $(date)"
python3 -m canoncite.systems.sweep --system C  --reader llm --k 5 --model "$M" --checkpoint $R/systemC_aya.jsonl  --out $R/systemC_aya.md  && echo "C_DONE"
python3 -m canoncite.systems.sweep --system E2 --retrieval rerank --reader llm --k 8 --model "$M" --checkpoint $R/systemE2_aya.jsonl --out $R/systemE2_aya.md && echo "E2_DONE"
python3 -m canoncite.systems.sweep --system D  --retrieval rerank --reader llm --k 8 --model "$M" --checkpoint $R/systemD_aya.jsonl  --out $R/systemD_aya.md  && echo "D_DONE"
echo "AYA_CHAIN_COMPLETE $(date)"
