"""Unified LLM interface for seed generation — endpoint-agnostic.

Supports two providers, selected by config:
  - `ollama`  : local/remote Ollama server (open weights, self-hosted).
  - `openai`  : any OpenAI-compatible endpoint (Together / Groq / OpenRouter /
                Fireworks / vLLM) serving an OPEN model — reproducible for a paper.

Config is read from env vars, optionally pre-loaded from a gitignored
`canoncite/seed/.llm.env` file so API keys never touch chat or git:

    CANONCITE_LLM_PROVIDER = ollama | openai
    CANONCITE_LLM_BASE_URL = https://api.together.xyz/v1   (openai provider)
    CANONCITE_LLM_API_KEY  = <key>                          (openai provider)
    CANONCITE_LLM_MODEL    = meta-llama/Llama-3.3-70B-Instruct-Turbo
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import ollama_client

_ENV_FILE = Path(__file__).with_name(".llm.env")


def load_env() -> None:
    """Load KEY=VALUE lines from the gitignored .llm.env into os.environ (once)."""
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def get_config() -> dict:
    load_env()
    return {
        "provider": os.getenv("CANONCITE_LLM_PROVIDER", "ollama"),
        "base_url": os.getenv("CANONCITE_LLM_BASE_URL"),
        "api_key": os.getenv("CANONCITE_LLM_API_KEY"),
        "model": os.getenv("CANONCITE_LLM_MODEL", "llama3.1:8b"),
    }


def _parse_json(text: str) -> dict | None:
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


def chat_json(prompt: str, system: str | None = None, temperature: float = 0.7) -> dict | None:
    """Return a parsed JSON object from the model, or None."""
    cfg = get_config()
    if cfg["provider"] == "openai":
        from openai import OpenAI
        client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        resp = client.chat.completions.create(
            model=cfg["model"], messages=messages, temperature=temperature)
        return _parse_json(resp.choices[0].message.content or "")
    # default: ollama
    return ollama_client.chat_json(prompt, model=cfg["model"], system=system, temperature=temperature)


def describe() -> str:
    cfg = get_config()
    where = cfg["base_url"] or ollama_client.DEFAULT_HOST
    return f"provider={cfg['provider']} model={cfg['model']} endpoint={where}"
