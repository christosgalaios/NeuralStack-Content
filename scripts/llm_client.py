from __future__ import annotations

import json
import os
from typing import Iterable
from urllib import error, request


def _iter_ollama_stream(raw: str) -> Iterable[str]:
    """
    Ollama often returns newline-delimited JSON when streaming. This helper
    concatenates the "response" fields in order.
    """
    parts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = obj.get("response")
        if text:
            parts.append(text)
    if parts:
        yield "".join(parts)


def call_ollama(prompt: str) -> str:
    """
    Call a local Ollama model with the given prompt and return the full text
    response. This function:

    - Uses NEURALSTACK_OLLAMA_MODEL if set, otherwise a sensible default.
    - Talks only to http://localhost:11434 (no external network).
    - Raises on connection errors so callers can decide how to handle them.
    """
    model = os.getenv("NEURALSTACK_OLLAMA_MODEL", "qcwind/qwen3-8b-instruct-Q4-K-M")

    payload = json.dumps({"model": model, "prompt": prompt}).encode("utf-8")
    req = request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")
    except (error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Ollama call failed: {exc}") from exc

    # Try standard JSON first.
    try:
        data = json.loads(body)
        if isinstance(data, dict) and "response" in data:
            return str(data.get("response", "")).strip()
    except json.JSONDecodeError:
        pass

    # Then fall back to streaming-style parsing.
    for text in _iter_ollama_stream(body):
        stripped = text.strip()
        if stripped:
            return stripped

    raise RuntimeError("Ollama call returned no usable content.")


__all__ = ["call_ollama"]

