"""Cross-encoder reranking (BGE-reranker-v2-m3) — the ranking stage of System C.

Diagnosis (recall_probe): hybrid retrieval *finds* the gold verse (recall@50 = 93-99%)
but ranks it DEEP cross-lingually (median rank 7-13), below the top-5 the reader sees.
Brute-force widening k to reach it plateaus and then hurts — the reader drowns in 20
noisy passages (E@20 gita-hi 0.670 < E@10 0.683).

A cross-encoder fixes the *ordering* instead of the window: it jointly encodes
(query, passage) and scores true relevance, pulling the gold verse from rank ~10 into
the top-5 while keeping the reader's context short and clean. BGE-reranker-v2-m3 is
XLM-RoBERTa based and multilingual, so it scores a Hindi/Sanskrit query against an
English or native-script verse directly — the cross-lingual condition we need.
"""
from __future__ import annotations

_MODEL = None
_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import CrossEncoder
        _MODEL = CrossEncoder(_MODEL_NAME)  # full context; device auto: CUDA on the box
    return _MODEL


# Near-full character cap per passage. A rare long-prose passage (Upanishad sections with
# en+Sanskrit+IAST concatenated) tokenizes to ~8000 tokens, whose attention tensor alone is
# ~4.3 GB — which OOMs the 22 GB L4 next to Ollama's 9 GB even at batch 1 (the spike is per
# single passage, not from batching). 4000 chars (~1000 tokens) is longer than every real
# verse's combined text, so this is lossless in practice and only clips pathological outliers,
# whose first 4000 chars still carry the full relevance signal for a short query.
_MAX_CHARS = 4000


def rerank(query: str, candidates: list[tuple[str, str]],
           top: int = 5) -> list[tuple[str, float]]:
    """candidates=[(id, text)] -> top reranked [(id, score)] by cross-encoder relevance."""
    if not candidates:
        return []
    model = _get_model()
    pairs = [[query[:_MAX_CHARS], text[:_MAX_CHARS]] for _, text in candidates]
    scores = model.predict(pairs, batch_size=8, show_progress_bar=False)
    ranked = sorted(
        ((cid, float(s)) for (cid, _), s in zip(candidates, scores)),
        key=lambda x: -x[1],
    )
    return ranked[:top]
