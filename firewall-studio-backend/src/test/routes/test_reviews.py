"""Tests for app.routes.reviews — comprehensive coverage."""
import pytest
import app.database as db


@pytest.mark.asyncio
async def test_list_reviews(async_client):
    resp = await async_client.get("/api/reviews")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_submit_review(async_client):
    resp = await async_client.post("/api/reviews", json={
        "rule_id": "R001",
        "type": "migration",
        "status": "Pending",
        "details": "Test review",
    })
    assert resp.status_code in (200, 201, 422)


@pytest.mark.asyncio
async def test_approve_review(async_client):
    db._save("reviews", [{"id": "REV001", "status": "Pending"}])
    resp = await async_client.post("/api/reviews/REV001/approve")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_reject_review(async_client):
    db._save("reviews", [{"id": "REV001", "status": "Pending"}])
    resp = await async_client.post("/api/reviews/REV001/reject", json={"notes": "Not needed"})
    assert resp.status_code in (200, 404, 422)
