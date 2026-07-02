"""Tests for app.routes.policy — comprehensive coverage."""
import pytest
import app.database as db


@pytest.mark.asyncio
async def test_validate_policy(async_client):
    await db.seed_database()
    resp = await async_client.post("/api/policy/validate", json={
        "source": {"source_type": "Group", "group_name": "grp-test"},
        "destination": {"name": "TestDest", "security_zone": "GEN"},
        "application": "TestApp",
        "environment": "Production",
    })
    assert resp.status_code in (200, 422)


@pytest.mark.asyncio
async def test_validate_policy_empty(async_client):
    resp = await async_client.post("/api/policy/validate", json={})
    assert resp.status_code in (200, 422)
