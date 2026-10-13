"""Tiny OpenAI-compatible chat client (standard library only)."""
from __future__ import annotations
import json, os, time, urllib.request, urllib.error


class LLMError(RuntimeError):
    pass


def api_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def chat(messages, model=None, temperature=0.2, retries=2, timeout=90):
    """Call /chat/completions. Retries transient failures with backoff."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise LLMError("OPENAI_API_KEY is not set")
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    body = {"model": model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": temperature, "messages": messages}
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            f"{base}/chat/completions", data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"Chat API failed after {retries + 1} tries: {last}")
