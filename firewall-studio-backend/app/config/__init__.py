"""Backend reference-data configuration (per-DC, NH, SZ, applications, policy matrix).

JSON files in this package hold seed/reference data that is loaded at startup and
served via /api/reference/* routes. Mirrored from legacy seed-json/ for backwards
compatibility; this package is now the canonical location.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR: Path = Path(__file__).resolve().parent


def load_config(name: str) -> Any:
    """Load a JSON config file from app/config/ by stem name (no extension).

    Falls back to legacy ../../seed-json/ if the file is missing from app/config/,
    so partially-migrated installs still work.
    """
    candidate = CONFIG_DIR / f"{name}.json"
    if not candidate.exists():
        legacy = CONFIG_DIR.parent.parent / "seed-json" / f"{name}.json"
        if legacy.exists():
            candidate = legacy
    with candidate.open("r", encoding="utf-8") as fh:
        return json.load(fh)


__all__ = ["CONFIG_DIR", "load_config"]
