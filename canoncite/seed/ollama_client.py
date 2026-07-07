"""Minimal Ollama client (stdlib only — no extra deps).

Talks to a local Ollama server (default http://localhost:11434). Open-source,
self-hostable, reproducible — preferred over a closed API for a benchmark.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

DEFAULT_HOST = "http://localhost:11434"


def chat(prompt: str, model: str = "llama3.1:8b", host: str = DEFAULT_HOST,
         system: str | None = None, temperature: float = 0.7, timeout: int = 300) -> str:
    """One-shot chat completion; returns the assistant text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }).encode("utf-8")
    req = urllib.request.Request(f"{host}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    return out.get("message", {}).get("content", "")


def chat_json(prompt: str, **kw) -> dict | None:
    """Chat and parse the first JSON object in the reply (lenient — small models
    wrap JSON in prose/markdown). Returns None if no parseable object.

    Network/timeout errors return None (never raise): a single slow generation must
    make that one item abstain, not crash the whole sweep. A read timeout after 300 s
    was previously fatal — it killed an entire System's run mid-grid and forfeited its
    remaining corpora."""
    try:
        text = chat(prompt, **kw)
    except (urllib.error.URLError, TimeoutError, OSError, ConnectionError):
        return None
    # strip ```json fences and grab the first {...} block
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def is_up(host: str = DEFAULT_HOST, timeout: int = 3) -> bool:
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False
