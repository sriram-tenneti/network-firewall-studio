"""Lifecycle Management API Routes.

Provides endpoints for rule lifecycle transitions, audit trail,
certification management, soft-delete/recovery, and dashboard stats.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.lifecycle import (
    get_valid_transitions,
    transition_lifecycle,
    soft_delete_rule,
    restore_rule,
    check_expiring_rules,
    auto_expire_rules,
    bulk_certify,
    bulk_decommission,
    get_lifecycle_dashboard,
    get_lifecycle_events,
    get_rule_timeline,
    record_lifecycle_event,
    NGDC_RULE_STATES,
    LEGACY_RULE_STATES,
)

router = APIRouter(prefix="/api/lifecycle", tags=["Lifecycle Management"])


# ============================================================
# Dashboard
# ============================================================

@router.get("/dashboard")
async def dashboard():
    """Get comprehensive lifecycle dashboard data."""
    return await get_lifecycle_dashboard()


# ============================================================
# State Machine
# ============================================================

@router.get("/states")
async def list_states():
    """Get the full state machine definitions."""
    return {
        "ngdc": NGDC_RULE_STATES,
        "legacy": LEGACY_RULE_STATES,
    }


@router.get("/transitions/{rule_id}")
async def valid_transitions(rule_id: str, is_legacy: bool = Query(False)):
    """Get valid next states for a rule."""
    from app.database import get_rule, _load
    if is_legacy:
        rules = _load("legacy_rules") or []
        rule = next((r for r in rules if r.get("id") == rule_id), None)
        if not rule:
            raise HTTPException(status_code=404, detail="Legacy rule not found")
        current = rule.get("lifecycle_status") or rule.get("rule_status", "Deployed")
    else:
        rule = await get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        current = rule.get("lifecycle_status") or rule.get("rule_status", "Submitted")
    return {
        "rule_id": rule_id,
        "current_status": current,
        "valid_transitions": get_valid_transitions(current, is_legacy),
    }


@router.post("/transition")
async def transition(data: dict):
    """Transition a rule through the lifecycle state machine."""
    rule_id = data.get("rule_id")
    new_status = data.get("new_status")
    if not rule_id or not new_status:
        raise HTTPException(status_code=400, detail="rule_id and new_status required")
    actor = data.get("actor", "system")
    module = data.get("module", "studio")
    comments = data.get("comments", "")
    is_legacy = data.get("is_legacy", False)
    result = await transition_lifecycle(
        rule_id, new_status, actor=actor, module=module,
        comments=comments, is_legacy=is_legacy,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============================================================
# Soft Delete & Recovery
# ============================================================

@router.post("/soft-delete")
async def soft_delete(data: dict):
    """Soft-delete a rule (preserves data for recovery)."""
    rule_id = data.get("rule_id")
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id required")
    result = await soft_delete_rule(
        rule_id,
        actor=data.get("actor", "system"),
        is_legacy=data.get("is_legacy", False),
        reason=data.get("reason", ""),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/restore")
async def restore(data: dict):
    """Restore a soft-deleted rule."""
    rule_id = data.get("rule_id")
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id required")
    result = await restore_rule(
        rule_id,
        actor=data.get("actor", "system"),
        is_legacy=data.get("is_legacy", False),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============================================================
# Certification & Expiry
# ============================================================

@router.get("/certification/check")
async def certification_check(days_ahead: int = Query(30)):
    """Check for expiring and expired rules."""
    return await check_expiring_rules(days_ahead)


@router.post("/certification/auto-expire")
async def run_auto_expire():
    """Auto-transition expired Certified rules to Expired status."""
    return await auto_expire_rules()


@router.post("/certification/bulk-certify")
async def run_bulk_certify(data: dict):
    """Bulk certify multiple rules."""
    rule_ids = data.get("rule_ids", [])
    if not rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids required")
    return await bulk_certify(rule_ids, actor=data.get("actor", "system"))


# ============================================================
# Decommission
# ============================================================

@router.post("/decommission/bulk")
async def run_bulk_decommission(data: dict):
    """Bulk request decommission for multiple rules."""
    rule_ids = data.get("rule_ids", [])
    if not rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids required")
    return await bulk_decommission(
        rule_ids, actor=data.get("actor", "system"),
        reason=data.get("reason", ""),
    )


# ============================================================
# Audit Trail / Events
# ============================================================

@router.get("/events")
async def list_events(
    rule_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    """Query lifecycle events with optional filters."""
    return await get_lifecycle_events(
        rule_id=rule_id, event_type=event_type,
        module=module, limit=limit, offset=offset,
    )


@router.get("/timeline/{rule_id}")
async def rule_timeline(rule_id: str):
    """Get complete lifecycle timeline for a specific rule."""
    return await get_rule_timeline(rule_id)


@router.post("/events")
async def create_event(data: dict):
    """Manually record a lifecycle event (e.g., comment, ownership change)."""
    rule_id = data.get("rule_id")
    event_type = data.get("event_type")
    if not rule_id or not event_type:
        raise HTTPException(status_code=400, detail="rule_id and event_type required")
    return await record_lifecycle_event(
        rule_id=rule_id,
        event_type=event_type,
        from_status=data.get("from_status"),
        to_status=data.get("to_status"),
        actor=data.get("actor", "system"),
        module=data.get("module", "manual"),
        details=data.get("details", ""),
        metadata=data.get("metadata"),
    )
