"""Readers: given a question + retrieved units, produce (answer, cited_ids, abstained).

Three backends, chosen by name so the pipeline runs at every compute budget:

  top1  — no LLM at all: cite the single top-retrieved unit. A pure-retrieval
          baseline. Answers *nothing*, just tests "does naive retrieval land the
          right verse id?". Runs instantly, zero deps — used to validate the whole
          scoring pipeline before any GPU/LLM is available.
  topk  — no LLM: cite all k retrieved ids (upper bound on recall; floor on precision).
  llm   — the real System-A reader: an LLM reads the k passages and cites the exact
          unit id(s) it relies on, or abstains. Uses canoncite.seed.llm (Ollama by
          default; any OpenAI-compatible endpoint via env).
"""
from __future__ import annotations
import re


def _extract_ids(obj: dict, U: set) -> list[str]:
    cites = obj.get("citations") or obj.get("cited_ids") or []
    if isinstance(cites, str):
        cites = [cites]
    out = []
    for c in cites:
        c = str(c).strip()
        # tolerate "[2.47]" / "2.47 —" style
        m = re.search(r"[\w.:]+", c)
        if m:
            c = m.group(0)
        if c in U:
            out.append(c)
    return out


def read_top1(question, retrieved, U, corpus):
    ids = [rid for rid, _ in retrieved[:1]]
    return {"answer": "", "cited_ids": ids, "abstained": False}


def read_topk(question, retrieved, U, corpus, k=5):
    ids = [rid for rid, _ in retrieved[:k]]
    return {"answer": "", "cited_ids": ids, "abstained": False}


_PROMPT = (
    "You answer questions about the canonical text '{corpus}'. Use ONLY the numbered "
    "passages below. Cite the exact passage ID(s) your answer relies on. If the answer "
    "is not contained in these passages, set answerable=false and cite nothing.\n\n"
    "Passages:\n{ctx}\n\nQuestion: {q}\n\n"
    'Return strict JSON: {{"answerable": true|false, "answer": "...", "citations": ["ID", ...]}}'
)


def _as_text(v) -> str:
    """Coerce a model's `answer` field to a string. Some models (e.g. Aya) return it
    as a list or dict instead of a string, which used to crash `.strip()` downstream."""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ".join(_as_text(x) for x in v)
    if isinstance(v, dict):
        return " ".join(_as_text(x) for x in v.values())
    return "" if v is None else str(v)


def read_llm(question, retrieved, U, corpus, id_to_text, temperature=0.2):
    from ..seed import llm  # lazy: only import when an LLM is actually used
    ctx = "\n".join(f"[{rid}] {id_to_text.get(rid, '')}" for rid, _ in retrieved)
    prompt = _PROMPT.format(corpus=corpus, ctx=ctx, q=question)
    obj = llm.chat_json(prompt, temperature=temperature) or {}
    answerable = obj.get("answerable", True)
    cited = _extract_ids(obj, U)
    answer = _as_text(obj.get("answer"))  # normalize once; downstream .strip() is now safe
    abstained = (answerable is False) or (not cited and not answer.strip())
    if abstained:
        cited = []
    return {"answer": answer, "cited_ids": cited, "abstained": abstained}
