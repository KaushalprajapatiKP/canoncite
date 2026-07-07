"""Load a corpus_index.jsonl into (id, retrieval_text) pairs + the id-space U.

Handles the heterogeneous text fields across our 10 corpora: prefer English text
for lexical retrieval, then transliteration, then the native-script text, then any
translation supplement — so BM25 always has *something* to index even for corpora
whose released text is native-script only (e.g. Guru Granth Sahib).
"""
from __future__ import annotations
import json
import os

# Fields we try, in order, to build the text a lexical retriever indexes.
_TEXT_FIELDS = ("text_en", "text", "english", "transliteration", "sanskrit",
                "gurmukhi", "tamil", "pali", "verse_text", "content")


def _row_text(row: dict) -> str:
    parts = []
    for f in _TEXT_FIELDS:
        v = row.get(f)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    # de-dup while preserving order
    seen, out = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return "  ".join(out)


def corpus_path(root: str, corpus: str) -> str:
    return os.path.join(root, "canoncite", "data", "corpora", corpus, "corpus_index.jsonl")


def load_corpus(root: str, corpus: str) -> tuple[list[tuple[str, str]], dict, set]:
    """Returns (docs=[(id,text)], id_to_text, U=id-space set)."""
    path = corpus_path(root, corpus)
    docs, id_to_text = [], {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            uid = str(row["id"])
            txt = _row_text(row)
            docs.append((uid, txt))
            id_to_text[uid] = txt
    return docs, id_to_text, set(id_to_text)
