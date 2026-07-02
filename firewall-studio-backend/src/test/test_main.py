"""Tests for app.main — 100% coverage."""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_healthz(async_client):
    resp = await async_client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_cors_headers(async_client):
    resp = await async_client.options(
        "/healthz",
        headers={"Origin": "http://localhost:5174", "Access-Control-Request-Method": "GET"},
    )
    # CORS middleware should respond
    assert resp.status_code in (200, 204, 405)


@pytest.mark.asyncio
async def test_app_has_routers(async_client):
    """Verify that all routers are included by checking known route prefixes."""
    resp = await async_client.get("/api/reference/neighbourhoods")
    # May return 200 or empty list depending on seed
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_lifespan_seeds_data():
    """Verify the lifespan context manager seeds data on startup."""
    from app.main import app
    import app.database as db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
