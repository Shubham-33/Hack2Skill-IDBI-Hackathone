"""Shared pytest fixtures.

Tests run in DETERMINISTIC mode (LLM disabled) so they're fast, offline and
reproducible — this also exercises the fallback paths that must never break.
The live LLM integration is verified separately/manually.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "execution"))
os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

import pytest

# import app (this triggers config.load_dotenv, which may set NVIDIA_API_KEY)...
from web.app import app  # noqa: E402
# ...then force deterministic mode for the whole test session
os.environ.pop("NVIDIA_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _preserve_data():
    """Snapshot mutable data files and restore them after the session so tests
    (which create/save leads and feedback) don't pollute the repo."""
    from config import DATA_DIR
    targets = [DATA_DIR / "prospects.json", DATA_DIR / "feedback.json"]
    backups = {t: t.read_bytes() for t in targets if t.exists()}
    existed = set(backups)
    yield
    for t, data in backups.items():
        t.write_bytes(data)
    for t in targets:
        if t not in existed and t.exists():
            t.unlink()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def first_pid(client):
    """A valid prospect id from the live queue."""
    import re
    html = client.get("/").text
    m = re.search(r"openDetail\('([^']+)'", html)
    return m.group(1) if m else "L0001"
