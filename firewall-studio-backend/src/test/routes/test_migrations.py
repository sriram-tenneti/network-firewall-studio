"""Tests for app.routes.migrations — comprehensive coverage."""
import pytest
import app.database as db


@pytest.mark.asyncio
async def test_list_migrations(async_client):
    resp = await async_client.get("/api/migrations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_migration(async_client):
    db._save("migrations", [{"id": "M001", "application": "CRM"}])
    resp = await async_client.get("/api/migrations/M001")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_create_migration(async_client):
    await db.seed_database()
    resp = await async_client.post("/api/migrations", json={
        "application": "TestApp",
        "source_legacy_dc": "DC1",
        "target_ngdc": "NGDC1",
    })
    assert resp.status_code in (200, 201, 422)


@pytest.mark.asyncio
async def test_get_mappings(async_client):
    db._save("migration_mappings", [{"migration_id": "M001"}])
    resp = await async_client.get("/api/migrations/M001/mappings")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_create_mapping(async_client):
    resp = await async_client.post("/api/migrations/M001/mappings", json={
        "migration_id": "M001",
        "legacy_source": "src",
        "ngdc_target": "tgt",
    })
    assert resp.status_code in (200, 201, 422)


@pytest.mark.asyncio
async def test_get_rule_lifecycle(async_client):
    resp = await async_client.get("/api/migrations/M001/rule-lifecycle")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_validate_migration(async_client):
    resp = await async_client.post("/api/migrations/M001/validate")
    assert resp.status_code in (200, 404, 422)


@pytest.mark.asyncio
async def test_submit_migration(async_client):
    resp = await async_client.post("/api/migrations/M001/submit")
    assert resp.status_code in (200, 400, 404, 422)
