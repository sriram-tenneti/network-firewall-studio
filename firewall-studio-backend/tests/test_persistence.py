"""Tests for the persistence layer helpers (_load / _save round-trips)."""

from __future__ import annotations

from pathlib import Path

from app import database as db


def test_load_save_round_trip(temp_data_dir: Path, monkeypatch) -> None:
    monkeypatch.setattr(db, "_get_data_dir", lambda: temp_data_dir)
    db._ensure_dir()
    payload = [{"id": "a", "value": 1}, {"id": "b", "value": 2}]
    db._save("unit_test_collection", payload)
    out = db._load("unit_test_collection")
    assert out == payload


def test_load_missing_returns_empty_list(temp_data_dir: Path, monkeypatch) -> None:
    monkeypatch.setattr(db, "_get_data_dir", lambda: temp_data_dir)
    db._ensure_dir()
    out = db._load("non_existent_collection")
    assert out in ([], {}, None)


def test_set_data_mode_round_trip() -> None:
    original = db.get_data_mode()
    try:
        db.set_data_mode("seed")
        assert db.get_data_mode() == "seed"
        db.set_data_mode("live")
        assert db.get_data_mode() == "live"
    finally:
        db.set_data_mode(original)


def test_set_hide_seed_round_trip() -> None:
    original = db.get_hide_seed()
    try:
        db.set_hide_seed(True)
        assert db.get_hide_seed() is True
        db.set_hide_seed(False)
        assert db.get_hide_seed() is False
    finally:
        db.set_hide_seed(original)
