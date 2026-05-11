"""Tests for IP classification helpers in app.database."""

from __future__ import annotations

import pytest

from app.database import _classify_ip_sync, _ip_in_cidr


@pytest.mark.parametrize(
    "ip,cidr,contained",
    [
        ("10.10.10.10", "10.10.10.0/24", True),
        ("10.10.11.10", "10.10.10.0/24", False),
        ("192.168.1.1", "192.168.0.0/16", True),
        ("172.16.5.5", "10.0.0.0/8", False),
        ("not-an-ip", "10.0.0.0/8", False),
        ("10.10.10.10", "not-a-cidr", False),
    ],
)
def test_ip_in_cidr(ip: str, cidr: str, contained: bool) -> None:
    result = _ip_in_cidr(ip, cidr)
    if contained:
        assert result >= 0
    else:
        assert result < 0


def test_classify_ip_returns_dict_shape() -> None:
    result = _classify_ip_sync("10.10.10.10")
    assert isinstance(result, dict)
    for key in ("dc", "nh", "sz", "cidr", "matched"):
        assert key in result


def test_classify_invalid_ip_returns_dict() -> None:
    result = _classify_ip_sync("definitely-not-an-ip")
    assert isinstance(result, dict)
