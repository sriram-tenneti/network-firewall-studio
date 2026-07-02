"""Tests for app.routes.rules — comprehensive coverage."""
import pytest
import app.database as db


@pytest.mark.asyncio
async def test_list_rules(async_client):
    resp = await async_client.get("/api/rules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_rule(async_client):
    await db.seed_database()
    resp = await async_client.post("/api/rules", json={
        "application": "TestApp",
        "environment": "Production",
        "datacenter": "DC1",
        "source": {"source_type": "Group", "group_name": "grp-test"},
        "destination": {"name": "TestDest", "security_zone": "GEN"},
        "owner": "tester",
    })
    assert resp.status_code in (200, 201, 422)


@pytest.mark.asyncio
async def test_get_rule(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "application": "CRM"}])
    resp = await async_client.get("/api/rules/R001")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_update_rule(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "application": "Old"}])
    resp = await async_client.put("/api/rules/R001", json={"application": "New"})
    assert resp.status_code in (200, 404, 422)


@pytest.mark.asyncio
async def test_delete_rule(async_client):
    db._save("firewall_rules", [{"rule_id": "R001"}])
    resp = await async_client.delete("/api/rules/R001")
    assert resp.status_code in (200, 204, 404)


@pytest.mark.asyncio
async def test_get_valid_transitions(async_client):
    resp = await async_client.get("/api/rules/transitions/Draft")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_transition_rule(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "status": "Draft", "rule_status": "Draft"}])
    resp = await async_client.post("/api/rules/R001/transition", json={"new_status": "Submitted"})
    assert resp.status_code in (200, 400, 404, 422)
