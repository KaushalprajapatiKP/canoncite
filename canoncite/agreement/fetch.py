"""Pull `verdicts` rows from Supabase into data/reviews/<corpus>/verdicts.jsonl.

Stdlib-only (urllib). Credentials are read from canoncite/.env, whose keys are
free-form (a human-written file), so parsing is deliberately robust:

  * the Supabase project *URL* is taken from any value that looks like
    https://<ref>.supabase.co, or reconstructed from `project_id` / a dashboard
    `project_link` (https://supabase.com/dashboard/project/<ref>/...);
  * the API key is any value that looks like a Supabase key
    (sb_publishable_..., sb_..., or a JWT eyJ...), preferring a key whose *name*
    mentions "api"/"key"/"publishable"/"anon".

Usage:
    PYTHONPATH=. python canoncite/agreement/fetch.py [--corpus bhagavad_gita]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(ROOT, "canoncite", ".env")
REVIEWS_DIR = os.path.join(ROOT, "canoncite", "data", "reviews")

_URL_RE = re.compile(r"https://([a-z0-9]{16,})\.supabase\.co", re.I)
_DASH_RE = re.compile(r"supabase\.com/dashboard/project/([a-z0-9]{16,})", re.I)
_KEYVAL_RE = re.compile(r"\b(sb_[A-Za-z0-9_\-]+|eyJ[A-Za-z0-9_\-.]+)\b")


def parse_env(path: str = ENV_PATH) -> dict[str, str]:
    """Parse a loose `key = value` .env into a lowercased-key dict (quotes stripped)."""
    env: dict[str, str] = {}
    if not os.path.isfile(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip().lower()] = v.strip().strip('"').strip("'")
    return env


def resolve_credentials(env: Optional[dict[str, str]] = None) -> tuple[str, str]:
    """Return (rest_base_url, api_key). Raises ValueError if either is missing.

    rest_base_url is the project root, e.g. https://<ref>.supabase.co (no trailing
    /rest/v1).
    """
    env = parse_env() if env is None else env
    values = list(env.values())

    # --- URL ---------------------------------------------------------------
    ref = None
    for v in values:
        m = _URL_RE.search(v)
        if m:
            ref = m.group(1)
            break
    if ref is None:
        for v in values:
            m = _DASH_RE.search(v)
            if m:
                ref = m.group(1)
                break
    if ref is None:
        pid = env.get("project_id") or env.get("project_ref") or env.get("supabase_project_id")
        if pid and re.fullmatch(r"[a-z0-9]{16,}", pid, re.I):
            ref = pid
    if not ref:
        raise ValueError(f"Could not find a Supabase project URL/ref in {ENV_PATH}")
    url = f"https://{ref}.supabase.co"

    # --- API key -----------------------------------------------------------
    key = None
    # prefer a value whose *key name* mentions api/key/publishable/anon/service
    for name, v in env.items():
        if any(t in name for t in ("api", "key", "publishable", "anon", "service")):
            m = _KEYVAL_RE.search(v)
            if m:
                key = m.group(1)
                break
    if key is None:  # otherwise any value that looks like a supabase key
        for v in values:
            m = _KEYVAL_RE.search(v)
            if m:
                key = m.group(1)
                break
    if not key:
        raise ValueError(f"Could not find a Supabase API key in {ENV_PATH}")
    return url, key


def _get(url: str, headers: dict[str, str]) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read(), dict(resp.headers)


def fetch_verdicts(corpus: Optional[str] = None, page_size: int = 1000,
                   env: Optional[dict[str, str]] = None) -> list[dict]:
    """GET {url}/rest/v1/verdicts?select=* with apikey + Bearer, paging by
    limit/offset until a short page is returned. Optional server-side corpus
    filter (?corpus=eq.<corpus>)."""
    base, key = resolve_credentials(env)
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    rows: list[dict] = []
    offset = 0
    while True:
        params = {"select": "*", "order": "ts.asc", "limit": str(page_size), "offset": str(offset)}
        if corpus:
            params["corpus"] = f"eq.{corpus}"
        url = f"{base}/rest/v1/verdicts?" + urllib.parse.urlencode(params)
        try:
            body, _ = _get(url, headers)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"Supabase GET failed ({e.code}): {detail}") from e
        page = json.loads(body or b"[]")
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return rows


def write_by_corpus(rows: list[dict]) -> dict[str, int]:
    """Write rows to data/reviews/<corpus>/verdicts.jsonl grouped by corpus."""
    by_corpus: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_corpus[r.get("corpus", "unknown")].append(r)
    counts: dict[str, int] = {}
    for corpus, crows in by_corpus.items():
        d = os.path.join(REVIEWS_DIR, corpus)
        os.makedirs(d, exist_ok=True)
        crows.sort(key=lambda r: (r.get("item_id", ""), r.get("reviewer", ""), r.get("ts", 0)))
        with open(os.path.join(d, "verdicts.jsonl"), "w", encoding="utf-8") as f:
            for r in crows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        counts[corpus] = len(crows)
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch CANONCITE verdicts from Supabase.")
    ap.add_argument("--corpus", help="only pull verdicts for this corpus")
    ap.add_argument("--print-config", action="store_true",
                    help="print the resolved Supabase URL (key redacted) and exit")
    args = ap.parse_args(argv)

    if args.print_config:
        url, key = resolve_credentials()
        print(f"url = {url}\nkey = {key[:10]}... ({len(key)} chars)")
        return 0

    rows = fetch_verdicts(args.corpus)
    counts = write_by_corpus(rows)
    total = sum(counts.values())
    print(f"Fetched {total} verdict rows -> {REVIEWS_DIR}")
    for corpus, n in sorted(counts.items()):
        print(f"  {corpus}: {n}")
    if not rows:
        print("  (no rows returned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
