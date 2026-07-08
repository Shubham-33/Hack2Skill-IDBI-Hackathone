"""NVIDIA NIM client (OpenAI-compatible) + structured-output helper.

- Points the OpenAI SDK at NVIDIA's free NIM endpoint (base_url swap).
- `complete_json` forces a parseable JSON object back (with one repair retry).
- Graceful DEGRADED mode: if NVIDIA_API_KEY is unset or a call fails, callers
  get `None` and fall back to deterministic templates — the app never dies on a
  missing key or a 40-RPM rate limit mid-demo.
- Compliance: `deidentify()` strips direct PII before anything is sent to the LLM.
  The LLM only ever phrases; it never sees a name/phone or computes a number.
"""
from __future__ import annotations

import json
import re
import time

from config import NVIDIA_BASE_URL, NVIDIA_MODEL, NVIDIA_TIMEOUT, env

MODEL = env("NVIDIA_MODEL", NVIDIA_MODEL)  # allow .env override

_client = None
_last_call_ts = 0.0
_MIN_INTERVAL = 0.5  # seconds between calls; bursts are fine (rate-limit → fast fallback)


def available() -> bool:
    return bool(env("NVIDIA_API_KEY"))


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        # hard timeout + no SDK retries so a slow free-tier call fails fast → deterministic fallback
        _client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=env("NVIDIA_API_KEY"),
                         timeout=NVIDIA_TIMEOUT, max_retries=0)
    return _client


def _throttle():
    global _last_call_ts
    dt = time.monotonic() - _last_call_ts
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    _last_call_ts = time.monotonic()


def deidentify(prospect: dict) -> dict:
    """Return a PII-stripped copy safe to send to a third-party LLM."""
    safe = dict(prospect)
    for k in ("name", "phone", "email", "pan", "aadhaar"):
        safe.pop(k, None)
    safe["ref"] = prospect.get("id", "LEAD")
    return safe


def complete_text(system: str, user: str, temperature: float = 0.4, max_tokens: int = 700):
    """Return model text, or None in degraded mode."""
    if not available():
        return None
    try:
        _throttle()
        resp = _get_client().chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:  # rate limit, network, auth — degrade gracefully
        print(f"[nvidia_llm] degraded ({type(e).__name__}): {e}")
        return None


def complete_json(system: str, user: str, temperature: float = 0.3, max_tokens: int = 900):
    """Return a parsed JSON object, or None in degraded mode."""
    system = system + "\n\nReturn ONLY a valid JSON object, no prose, no code fences."
    txt = complete_text(system, user, temperature, max_tokens)
    if txt is None:
        return None
    obj = _extract_json(txt)
    if obj is None:  # one repair attempt
        txt = complete_text(system, "Your previous reply was not valid JSON. "
                                    "Re-emit ONLY the JSON object.\n\n" + user, 0.0, max_tokens)
        obj = _extract_json(txt or "")
    return obj


def _extract_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


if __name__ == "__main__":
    print("NVIDIA_API_KEY present:", available())
    if available():
        r = complete_json(
            "You are a banking assistant.",
            'Return {"greeting": "<one short hello>", "model_ok": true}.',
        )
        print("Sample structured reply:", r)
    else:
        print("Running in DEGRADED mode — set NVIDIA_API_KEY in .env to enable the LLM.")
        print("Deterministic fallbacks will be used everywhere the LLM would phrase text.")
