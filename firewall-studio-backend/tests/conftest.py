"""Shared pytest fixtures for the firewall-studio backend test suite.

Sets `FIREWALL_STUDIO_DATA_DIR` to a fresh temp directory before each test so
JSON persistence in app.database is isolated and reproducible.
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def temp_data_dir(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Provide a fresh data directory and reset the module-level cache."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        monkeypatch.setenv("FIREWALL_STUDIO_DATA_DIR", str(path))
        os.environ["FIREWALL_STUDIO_DATA_DIR"] = str(path)
        yield path


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
