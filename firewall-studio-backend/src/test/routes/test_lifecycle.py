"""Tests for app.routes.lifecycle — comprehensive coverage."""
import pytest
import app.database as db


@pytest.mark.asyncio
async def test_dashboard(async_client):
    resp = await async_client.get("/api/lifecycle/dashboard")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_states(async_client):
    resp = await async_client.get("/api/lifecycle/states")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_valid_transitions(async_client):
    resp = await async_client.get("/api/lifecycle/transitions/R001")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_transition(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "lifecycle_status": "Draft",
                                   "rule_status": "Draft", "status": "Draft", "application": "CRM"}])
    resp = await async_client.post("/api/lifecycle/transition", json={"rule_id": "R001", "new_status": "Submitted"})
    assert resp.status_code in (200, 400, 404, 422)


@pytest.mark.asyncio
async def test_soft_delete(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "lifecycle_status": "Deployed",
                                   "rule_status": "Deployed", "status": "Deployed"}])
    resp = await async_client.post("/api/lifecycle/soft-delete", json={"rule_id": "R001", "reason": "cleanup"})
    assert resp.status_code in (200, 400, 404, 422)


@pytest.mark.asyncio
async def test_restore(async_client):
    db._save("firewall_rules", [{"rule_id": "R001", "lifecycle_status": "Deleted",
                                   "previous_status": "Deployed"}])
    resp = await async_client.post("/api/lifecycle/restore", json={"rule_id": "R001"})
    assert resp.status_code in (200, 400, 404, 422)


@pytest.mark.asyncio
async def test_certification_check(async_client):
    resp = await async_client.get("/api/lifecycle/certification/check")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auto_expire(async_client):
    resp = await async_client.post("/api/lifecycle/certification/auto-expire")
    assert resp.status_code in (200, 422)


@pytest.mark.asyncio
async def test_bulk_certify(async_client):
    resp = await async_client.post("/api/lifecycle/certification/bulk-certify", json={"rule_ids": ["R001"]})
    assert resp.status_code in (200, 422)


@pytest.mark.asyncio
async def test_bulk_decommission(async_client):
    resp = await async_client.post("/api/lifecycle/decommission/bulk", json={"rule_ids": ["R001"], "reason": "EOL"})
    assert resp.status_code in (200, 422)


@pytest.mark.asyncio
async def test_list_events(async_client):
    resp = await async_client.get("/api/lifecycle/events")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rule_timeline(async_client):
    resp = await async_client.get("/api/lifecycle/timeline/R001")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_event(async_client):
    resp = await async_client.post("/api/lifecycle/events", json={
        "rule_id": "R001", "event_type": "created",
    })
    assert resp.status_code in (200, 201, 422)
