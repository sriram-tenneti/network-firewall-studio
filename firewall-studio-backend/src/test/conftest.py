"""Shared fixtures for all backend tests."""
import os
import sys
import json
from pathlib import Path

import pytest

# Ensure the backend root is on sys.path so `app.*` imports work
_backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)


@pytest.fixture(autouse=True)
def isolate_data(tmp_path, monkeypatch):
    """Redirect all JSON persistence to a temp directory so tests never touch real data."""
    import app.database as db

    data_dir = tmp_path / "data"
    live_dir = tmp_path / "live-data"
    user_dir = tmp_path / "user-data"
    data_dir.mkdir()
    live_dir.mkdir()
    user_dir.mkdir()

    monkeypatch.setattr(db, "SEED_DATA_DIR", data_dir)
    monkeypatch.setattr(db, "LIVE_DATA_DIR", live_dir)
    monkeypatch.setattr(db, "SEPARATE_DATA_DIR", user_dir)
    monkeypatch.setattr(db, "DATA_DIR", data_dir)
    monkeypatch.setattr(db, "_data_mode", "seed")
    monkeypatch.setattr(db, "_hide_seed", False)

    yield tmp_path


@pytest.fixture
def seeded_db(isolate_data):
    """Run seed_database so tests get full reference data."""
    import asyncio
    import app.database as db

    loop = asyncio.new_event_loop()
    loop.run_until_complete(db.seed_database())
    loop.close()
    return isolate_data


@pytest.fixture
def async_client(isolate_data):
    """Provide an async HTTPX test client wired to the FastAPI app."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app as fastapi_app

    transport = ASGITransport(app=fastapi_app)
    return AsyncClient(transport=transport, base_url="http://testserver")
