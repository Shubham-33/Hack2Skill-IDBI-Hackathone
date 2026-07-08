"""Shared config + path helpers for Layer 3 execution scripts.

Import this at the top of any execution script so paths and env vars
resolve the same way whether run locally or inside a Modal container.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional in cloud (env is injected there)
    load_dotenv = None

# Project root = parent of the execution/ directory
ROOT = Path(__file__).resolve().parent.parent
EXECUTION_DIR = ROOT / "execution"
DIRECTIVES_DIR = ROOT / "directives"
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
TMP_DIR = ROOT / ".tmp"

# --- NVIDIA NIM (OpenAI-compatible) ---
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
# Fast small model for low-latency interactive paths (chat, pitch, rationale).
# Larger models (meta/llama-3.3-70b-instruct) are far slower on the free tier.
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"
NVIDIA_TIMEOUT = 9.0  # seconds — past this we fall back to deterministic text

# Load .env from project root if present
if load_dotenv is not None:
    load_dotenv(ROOT / ".env")

# Ensure the intermediates dir exists
TMP_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def load_json(path):
    """Load a JSON file from the data dir (accepts a name or a full Path)."""
    import json
    p = path if isinstance(path, Path) else DATA_DIR / path
    return json.loads(Path(p).read_text())


def save_json(path, obj):
    """Write JSON to the data dir (accepts a name or a full Path)."""
    import json
    p = path if isinstance(path, Path) else DATA_DIR / path
    Path(p).write_text(json.dumps(obj, indent=2, default=str))
    return p


def env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Fetch an env var, optionally raising if it's required and missing."""
    val = os.environ.get(key, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


if __name__ == "__main__":
    print(f"ROOT:        {ROOT}")
    print(f"execution/:  {EXECUTION_DIR}")
    print(f"directives/: {DIRECTIVES_DIR}")
    print(f".tmp/:       {TMP_DIR}")
    print(f"ANTHROPIC_API_KEY set: {bool(env('ANTHROPIC_API_KEY'))}")
