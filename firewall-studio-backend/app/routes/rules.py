from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import (
    get_rules, get_rule, create_rule, update_rule,
    delete_rule, update_rule_status, get_rule_history,
    compile_rule,
)

router = APIRouter(prefix="/api/rules", tags=["Firewall Rules"])


@router.get("")
async def list_rules(
    application: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    rules = await get_rules()
    if application:
        rules = [r for r in rules if r.get("application") == application]
    if status:
        rules = [r for r in rules if r.get("status") == status]
    return rules


@router.get("/{rule_id}")
async def get_rule_endpoint(rule_id: str):
    rule = await get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("")
async def create_new_rule(data: dict):
    return await create_rule(data)


@router.put("/{rule_id}")
async def update_existing_rule(rule_id: str, data: dict):
    result = await update_rule(rule_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.delete("/{rule_id}")
async def delete_existing_rule(rule_id: str):
    if not await delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


@router.post("/{rule_id}/certify")
async def certify_existing_rule(rule_id: str):
    result = await update_rule_status(rule_id, "Certified")
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.post("/{rule_id}/submit")
async def submit_existing_rule(rule_id: str):
    result = await update_rule_status(rule_id, "Pending Review")
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.get("/{rule_id}/history")
async def get_history(rule_id: str):
    return await get_rule_history(rule_id)


@router.post("/{rule_id}/compile")
async def compile_rule_endpoint(rule_id: str, vendor: str = Query("generic")):
    result = await compile_rule(rule_id, vendor)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result
