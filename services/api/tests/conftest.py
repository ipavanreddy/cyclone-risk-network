"""Tests always run in demo mode with an isolated SQLite store, whatever is in the repo .env."""
import os
import tempfile

os.environ["FORCE_DEMO_MODE"] = "true"
os.environ["STORE_PATH"] = os.path.join(tempfile.mkdtemp(prefix="tatraksha-test-"), "store.sqlite3")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
