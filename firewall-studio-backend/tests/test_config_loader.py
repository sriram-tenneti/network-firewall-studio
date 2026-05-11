"""Tests for the app/config package — reference data loader."""

from __future__ import annotations

import json

import pytest

from app.config import CONFIG_DIR, load_config


def test_config_dir_exists() -> None:
    assert CONFIG_DIR.exists()
    assert CONFIG_DIR.is_dir()


@pytest.mark.parametrize(
    "name",
    [
        "datacenters",
        "neighbourhoods",
        "security_zones",
        "applications",
        "app_dc_mappings",
        "policy_matrix",
    ],
)
def test_load_each_config(name: str) -> None:
    payload = load_config(name)
    assert payload is not None
    assert isinstance(payload, list | dict)


def test_load_config_missing_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config("does-not-exist-xyz")


def test_load_config_returns_valid_json() -> None:
    for name in ("datacenters", "applications", "neighbourhoods"):
        payload = load_config(name)
        json.dumps(payload)
