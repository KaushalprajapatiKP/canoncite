"""Dense multilingual retrieval (BGE-M3 + FAISS) — the dense half of System B.

BGE-M3 is a strong multilingual embedding model: it maps a Hindi/Sanskrit/Tamil query
and an English (or native-script) verse into the *same* semantic space, so a
cross-lingual query can retrieve the correct verse even with zero lexical overlap —
precisely the failure mode BM25 has in the cross-lingual conditions.

Embeddings are cached per corpus (npz next to the corpus) so we embed each corpus once;
subsequent runs just load the matrix and rebuild the (cheap) FAISS flat index. Requires
`sentence-transformers` + `faiss-cpu` (installed on the GPU box); the model runs on CUDA.
"""
from __future__ import annotations
import os

import numpy as np

_MODEL = None
_MODEL_NAME = "BAAI/bge-m3"


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        # device auto: CUDA on the box, CPU fallback elsewhere
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def _cache_path(root: str, corpus: str, tag: str = "bgem3") -> str:
    d = os.path.join(root, "canoncite", "data", "corpora", corpus)
    return os.path.join(d, f"dense_{tag}.npz")


# BGE-M3 is XLM-RoBERTa-based; long-prose passages (Upanishad sections concatenating
# en+Sanskrit+IAST reach ~8000 tokens) blow its attention tensor to ~4 GB at batch 64 and
# OOM the 22 GB L4 next to Ollama's 9 GB. Cap the text (lossless for real verses — their
# combined text is well under 4000 chars) and shrink the batch so the cache build fits.
_MAX_CHARS = 4000


def _embed(texts: list[str]) -> np.ndarray:
    m = _get_model()
    texts = [t[:_MAX_CHARS] for t in texts]
    emb = m.encode(texts, batch_size=16, normalize_embeddings=True,
                   show_progress_bar=False)
    return np.asarray(emb, dtype="float32")


class DenseRetriever:
    """Cosine-similarity dense retriever over one corpus (embeddings cached to disk)."""

    def __init__(self, root: str, corpus: str, docs: list[tuple[str, str]]):
        self.ids = [d[0] for d in docs]
        texts = [d[1] for d in docs]
        cache = _cache_path(root, corpus)
        emb = None
        if os.path.exists(cache):
            z = np.load(cache, allow_pickle=True)
            if list(z["ids"]) == self.ids:      # cache valid only if id-space matches
                emb = z["emb"]
        if emb is None:
            emb = _embed(texts)
            np.savez(cache, emb=emb, ids=np.array(self.ids, dtype=object))
        self.emb = emb

        import faiss
        self.index = faiss.IndexFlatIP(emb.shape[1])  # inner product on L2-normalized = cosine
        self.index.add(emb)

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        q = _embed([query])
        D, I = self.index.search(q, k)
        return [(self.ids[i], float(D[0][r])) for r, i in enumerate(I[0]) if i >= 0]
