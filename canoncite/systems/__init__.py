"""Systems under test for CANONCITE (the RAG pipelines we evaluate).

Each system answers a benchmark question and emits (answer, cited_ids, retrieved_ids,
abstained), which the metric harness (canoncite.eval) scores. This package builds
them up:

  A  naive RAG    — retrieve (BM25 or dense) top-k -> LLM answers + cites   [naive_rag.py]
  B  hybrid       — BM25 + dense (RRF)                                       [planned]
  C  reranking    — retrieve 20 -> cross-encoder -> top-k                    [planned]
  D  SOTA         — Self-RAG / CRAG / VeriCite reproduction                  [planned]
  E  ours         — exact-ID attribution-verifier + repair                  [planned]

System A + BM25 run with NO GPU (BM25 is stdlib; the reader can be local Ollama),
so the full pipeline is testable now; dense retrieval (BGE-M3) plugs in for scale.
"""
