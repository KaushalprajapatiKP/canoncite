"""Stdlib review server. No framework dependency.

Endpoints:
  GET  /                                  -> index.html
  GET  /api/corpora                       -> [{corpus, n_items}]
  GET  /api/items?corpus=X&reviewer=Y     -> items enriched with source text + this
                                             reviewer's saved verdicts
  POST /api/verdict  {reviewer,corpus,item_id,status,edits,notes}
                                          -> upsert data/reviews/<corpus>/<reviewer>.jsonl
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ITEMS_DIR = os.path.join(ROOT, "canoncite", "data", "items")
CORPORA_DIR = os.path.join(ROOT, "canoncite", "data", "corpora")
REVIEWS_DIR = os.path.join(ROOT, "canoncite", "data", "reviews")
HTML = os.path.join(os.path.dirname(__file__), "index.html")

_corpus_index_cache: dict[str, dict] = {}


def _load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def corpus_index(corpus: str) -> dict[str, dict]:
    """id -> record (text_en/original/transliteration), cached."""
    if corpus not in _corpus_index_cache:
        path = os.path.join(CORPORA_DIR, corpus, "corpus_index.jsonl")
        _corpus_index_cache[corpus] = {r["id"]: r for r in _load_jsonl(path)}
    return _corpus_index_cache[corpus]


def source_text(corpus: str, cid: str) -> dict:
    r = corpus_index(corpus).get(cid, {})
    return {"id": cid,
            "text_en": r.get("text_en"),
            "original": r.get("original") or r.get("sanskrit"),
            "translit": r.get("transliteration"),
            "heading": r.get("heading")}


def list_corpora():
    out = []
    for c in sorted(os.listdir(ITEMS_DIR)):
        p = os.path.join(ITEMS_DIR, c, "seed_candidates.jsonl")
        if os.path.isfile(p):
            out.append({"corpus": c, "n_items": sum(1 for _ in open(p, encoding="utf-8"))})
    return out


def reviewer_file(corpus: str, reviewer: str) -> str:
    safe = "".join(ch for ch in reviewer if ch.isalnum() or ch in "-_") or "anon"
    d = os.path.join(REVIEWS_DIR, corpus)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{safe}.jsonl")


def load_verdicts(corpus: str, reviewer: str) -> dict:
    p = reviewer_file(corpus, reviewer)
    if not os.path.isfile(p):
        return {}
    return {v["item_id"]: v for v in _load_jsonl(p)}


def save_verdict(v: dict):
    corpus, reviewer = v["corpus"], v["reviewer"]
    verdicts = load_verdicts(corpus, reviewer)
    verdicts[v["item_id"]] = v
    with open(reviewer_file(corpus, reviewer), "w", encoding="utf-8") as f:
        for item_id in sorted(verdicts):
            f.write(json.dumps(verdicts[item_id], ensure_ascii=False, sort_keys=True) + "\n")


def items_for_review(corpus: str, reviewer: str) -> list[dict]:
    items = _load_jsonl(os.path.join(ITEMS_DIR, corpus, "seed_candidates.jsonl"))
    verdicts = load_verdicts(corpus, reviewer)
    for it in items:
        it["_gold_src"] = [source_text(corpus, c) for c in it.get("gold_citations", [])]
        it["_nearmiss_src"] = [source_text(corpus, c) for c in it.get("near_miss_distractors", [])]
        it["_verdict"] = verdicts.get(it["id"])
    return items


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass  # quiet

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/":
                self._send(200, open(HTML, "rb").read(), "text/html; charset=utf-8")
            elif u.path == "/api/corpora":
                self._send(200, list_corpora())
            elif u.path == "/api/items":
                corpus = q.get("corpus", [""])[0]
                reviewer = q.get("reviewer", ["anon"])[0]
                self._send(200, {"corpus": corpus, "reviewer": reviewer,
                                 "items": items_for_review(corpus, reviewer)})
            else:
                self._send(404, {"error": "not found"})
        except Exception as e:  # surface errors to the UI
            self._send(500, {"error": str(e)})

    def do_POST(self):
        if urlparse(self.path).path != "/api/verdict":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            v = json.loads(self.rfile.read(n) or b"{}")
            for k in ("reviewer", "corpus", "item_id", "status"):
                if not v.get(k):
                    return self._send(400, {"error": f"missing {k}"})
            import time
            v["ts"] = int(time.time())
            save_verdict(v)
            self._send(200, {"ok": True, "item_id": v["item_id"], "status": v["status"]})
        except Exception as e:
            self._send(500, {"error": str(e)})


def serve(port=8080):
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"CANONCITE review app → http://localhost:{port}  (Ctrl-C to stop)")
    print(f"  items: {ITEMS_DIR}\n  verdicts: {REVIEWS_DIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
