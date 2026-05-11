"""High-coverage smoke tests against the live FastAPI app.

These exercise the most-trafficked GET endpoints to ensure the routers wire up
cleanly and seed data loads. We deliberately avoid asserting on full payload
shape (which is data-driven) and instead assert on HTTP semantics.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/api/reference/ngdc-datacenters",
        "/api/reference/legacy-datacenters",
        "/api/reference/neighbourhoods",
        "/api/reference/security-zones",
        "/api/reference/applications",
        "/api/reference/environments",
        "/api/reference/policy-matrix",
        "/api/reference/policy-matrix/ngdc-prod",
        "/api/reference/policy-matrix/nonprod",
        "/api/reference/policy-matrix/heritage-dc",
        "/api/reference/naming-standards",
        "/api/reference/ports",
        "/api/reference/org-config",
        "/api/reference/data-mode",
        "/api/reference/shared-services",
    ],
)
def test_reference_endpoints_respond(client: TestClient, path: str) -> None:
    resp = client.get(path)
    assert resp.status_code in (200, 204)
    if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/json"):
        body = resp.json()
        assert isinstance(body, list | dict)


def test_classify_ip_endpoint(client: TestClient) -> None:
    resp = client.post("/api/reference/classify-ip", json={"ip": "10.10.10.10"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "matched" in body


def test_classify_ips_batch_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/reference/classify-ips",
        json={"ips": ["10.10.10.10", "10.10.10.11", "not-an-ip"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list | dict)


def test_unknown_endpoint_returns_404(client: TestClient) -> None:
    resp = client.get("/api/this-does-not-exist")
    assert resp.status_code == 404


def test_openapi_schema_available(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    assert any(p.startswith("/api/reference/") for p in schema["paths"])
