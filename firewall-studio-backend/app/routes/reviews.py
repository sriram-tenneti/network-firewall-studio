from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_reviews, create_review, approve_review, reject_review

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.get("")
async def list_reviews(
    status: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
):
    reviews = await get_reviews(status)
    if module:
        reviews = [r for r in reviews if r.get("module", "studio") == module]
    return reviews


@router.post("")
async def submit_review(data: dict):
    rule_id = data.get("rule_id")
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id is required")
    comments = data.get("comments", "")
    module = data.get("module", "design-studio")
    return await create_review(rule_id, comments, module)


@router.post("/{review_id}/approve")
async def approve_review_endpoint(review_id: str, data: dict = None):
    notes = (data or {}).get("notes", "")
    result = await approve_review(review_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    return result


@router.post("/{review_id}/reject")
async def reject_review_endpoint(review_id: str, data: dict):
    notes = data.get("notes", "")
    if not notes:
        raise HTTPException(status_code=400, detail="Rejection notes are required")
    result = await reject_review(review_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    return result
