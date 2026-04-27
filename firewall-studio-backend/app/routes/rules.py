from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import (
    get_rules, get_rule, create_rule, update_rule,
    delete_rule, update_rule_status, get_rule_history,
    compile_rule,
    transition_rule_status, get_valid_rule_status_transitions,
    get_rule_lifecycle_summary,
)

router = APIRouter(prefix="/api/rules", tags=["Firewall Rules"])


@router.get("")
async def list_rules(
    application: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    rule_status: Optional[str] = Query(None),
    rule_migration_status: Optional[str] = Query(None),
):
    rules = await get_rules()
    if application:
        rules = [r for r in rules if r.get("application") == application]
    if status:
        rules = [r for r in rules if r.get("status") == status]
    if rule_status:
        rules = [r for r in rules if r.get("rule_status") == rule_status]
    if rule_migration_status:
        rules = [r for r in rules if r.get("rule_migration_status") == rule_migration_status]
    return rules


# Static routes MUST come before /{rule_id} to avoid path parameter capture
@router.get("/lifecycle/summary")
async def lifecycle_summary():
    """Get aggregate lifecycle status counts across all modules."""
    return await get_rule_lifecycle_summary()


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
    rule = await get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    # Certify is only available for Deployed rules
    if rule.get("rule_status", "Submitted") != "Deployed":
        raise HTTPException(status_code=400, detail="Certify is only available for Deployed rules")
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
    rule = await get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    # Compile is a preview/export operation and is safe to run for any
    # post-Draft status. SNS routinely needs to view the device-vendor
    # output during review (Approved) and during operations (Deployed /
    # Certified). Blocking compile for Approved rules left no path to
    # download per-vendor configs before deployment.
    allowed = {"Pending Review", "Approved", "Deployed", "Certified"}
    if rule.get("rule_status", "Submitted") not in allowed and rule.get("status") not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Compile is only available for Pending Review / Approved / Deployed / Certified rules",
        )
    result = await compile_rule(rule_id, vendor)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.post("/{rule_id}/lifecycle-transition")
async def lifecycle_transition(rule_id: str, data: dict):
    """Transition a Studio rule through the lifecycle: Submitted -> In Progress -> Approved -> Deployed"""
    new_status = data.get("new_status")
    if not new_status:
        raise HTTPException(status_code=400, detail="new_status is required")
    module = data.get("module", "studio")
    reviewer = data.get("reviewer", "system")
    result = await transition_rule_status(rule_id, new_status, module=module, reviewer=reviewer)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{rule_id}/valid-transitions")
async def valid_transitions(rule_id: str):
    """Get valid next lifecycle statuses for a rule."""
    rule = await get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    current = rule.get("rule_status", "Submitted")
    transitions = get_valid_rule_status_transitions(current, is_legacy=False)
    return {"rule_id": rule_id, "current_status": current, "valid_transitions": transitions}
