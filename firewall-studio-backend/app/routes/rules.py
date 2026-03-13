from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import (
    get_all_rules, get_rule_by_id, create_rule, update_rule,
    delete_rule, certify_rule, submit_rule, get_rule_history,
)

router = APIRouter(prefix="/api/rules", tags=["Firewall Rules"])


@router.get("")
async def list_rules(
    application: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    return get_all_rules(application=application, status=status)


@router.get("/{rule_id}")
async def get_rule(rule_id: str):
    rule = get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("")
async def create_new_rule(data: dict):
    return create_rule(data)


@router.put("/{rule_id}")
async def update_existing_rule(rule_id: str, data: dict):
    result = update_rule(rule_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.delete("/{rule_id}")
async def delete_existing_rule(rule_id: str):
    if not delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


@router.post("/{rule_id}/certify")
async def certify_existing_rule(rule_id: str, user: str = Query("Jon")):
    result = certify_rule(rule_id, user)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.post("/{rule_id}/submit")
async def submit_existing_rule(rule_id: str):
    result = submit_rule(rule_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.get("/{rule_id}/history")
async def get_history(rule_id: str):
    return get_rule_history(rule_id)
