"""Unit tests for low-level helpers in app.database (no I/O required)."""

from __future__ import annotations

import re

from app.database import _auto_prefix, _id, _now, _shorten_ip_range


def test_id_is_unique_and_string() -> None:
    a = _id()
    b = _id()
    assert isinstance(a, str)
    assert a != b
    assert len(a) >= 8


def test_now_is_iso_like() -> None:
    val = _now()
    assert isinstance(val, str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", val), val


def test_auto_prefix_ip_default_type() -> None:
    assert _auto_prefix("10.10.10.10").startswith("svr-")


def test_auto_prefix_cidr_subnet_type() -> None:
    out = _auto_prefix("10.10.10.0/24", "subnet")
    assert out.startswith("net-")


def test_auto_prefix_range_type() -> None:
    out = _auto_prefix("10.10.10.1-10.10.10.20", "range")
    assert out.startswith("rng-")


def test_auto_prefix_group_type() -> None:
    out = _auto_prefix("CRM-NH02-PAA", "group")
    assert out.startswith("grp-")


def test_auto_prefix_normalizes_legacy_g_prefix() -> None:
    assert _auto_prefix("g-CRM") == "grp-CRM"


def test_auto_prefix_normalizes_legacy_sub_prefix() -> None:
    assert _auto_prefix("sub-10.10.10.0") == "net-10.10.10.0"


def test_auto_prefix_passthrough_for_named_token() -> None:
    assert _auto_prefix("grp-CRM-NH02-PAA") == "grp-CRM-NH02-PAA"
    assert _auto_prefix("svr-already") == "svr-already"
    assert _auto_prefix("net-10.10.10.0") == "net-10.10.10.0"
    assert _auto_prefix("rng-10.10.10.1-10") == "rng-10.10.10.1-10"


def test_shorten_ip_range_collapses_octets() -> None:
    out = _shorten_ip_range("10.10.10.1-10.10.10.5")
    assert "10.10.10.1" in out
    assert "5" in out
