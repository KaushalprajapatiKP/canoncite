"""Stdlib review server. No framework dependency.

Endpoints:
  GET  /                                  -> index.html
  GET  /api/corpora                       -> [{corpus, n_items, n_done}]
  GET  /api/items?corpus=X&reviewer=Y     -> items enriched with source text + this
                                             reviewer's saved verdicts
  POST /api/verdict  {reviewer,corpus,item_id,status,edits,notes}
                                          -> upsert data/reviews/<corpus>/<reviewer>.jsonl

Verdicts are read straight back by canoncite.agreement (its `load_verdicts` falls
back to these per-reviewer files), so the whole verify -> agreement -> gold chain
runs locally with no hosted backend.

Pass a sample manifest (see canoncite/review/build_sample.py) to restrict review
to the stratified human-verification sample instead of all 622 items.
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
DEFAULT_SAMPLE = os.path.join(ITEMS_DIR, "_review_sample_v1.json")

_corpus_index_cache: dict[str, dict] = {}
# {corpus: {item_id}} when reviewing a sample; None means "every item".
SAMPLE: dict[str, set] | None = None


def load_sample(path: str) -> dict[str, set]:
    with open(path, encoding="utf-8") as fh:
        return {c: set(ids) for c, ids in json.load(fh)["by_corpus"].items()}


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


def list_corpora(reviewer: str = "anon"):
    """Corpora in scope, with this reviewer's progress so the UI can show N done/M."""
    out = []
    for c in sorted(os.listdir(ITEMS_DIR)):
        p = os.path.join(ITEMS_DIR, c, "seed_candidates.jsonl")
        if not os.path.isfile(p):
            continue
        if SAMPLE is not None:
            keep = SAMPLE.get(c)
            if not keep:
                continue  # corpus excluded from the sample
            n_items = len(keep)
            done = sum(1 for i in load_verdicts(c, reviewer) if i in keep)
        else:
            n_items = sum(1 for _ in open(p, encoding="utf-8"))
            done = len(load_verdicts(c, reviewer))
        out.append({"corpus": c, "n_items": n_items, "n_done": done})
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
    if SAMPLE is not None:
        keep = SAMPLE.get(corpus, set())
        items = [it for it in items if it["id"] in keep]
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
                self._send(200, list_corpora(q.get("reviewer", ["anon"])[0]))
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


def serve(port=8080, sample: str | None = None):
    """Serve the review UI. `sample` is a path to a build_sample.py manifest, or
    "all" / None to review every item."""
    global SAMPLE
    if sample and sample != "all":
        SAMPLE = load_sample(sample)
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"CANONCITE review app → http://localhost:{port}  (Ctrl-C to stop)")
    if SAMPLE is not None:
        n = sum(len(v) for v in SAMPLE.values())
        print(f"  scope: stratified sample, {n} items across {len(SAMPLE)} corpora")
    else:
        print("  scope: ALL items")
    print(f"  items: {ITEMS_DIR}\n  verdicts: {REVIEWS_DIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="CANONCITE review app")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sample", default=DEFAULT_SAMPLE,
                    help="sample manifest path, or 'all' to review every item")
    a = ap.parse_args(argv)
    serve(a.port, a.sample)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
