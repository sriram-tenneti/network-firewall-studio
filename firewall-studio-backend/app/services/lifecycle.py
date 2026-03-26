"""Rule Lifecycle Management Service.

Manages the full lifecycle of firewall rules across all modules:
- State machine with valid transitions
- Structured audit trail with typed events
- Periodic certification & auto-expiry detection
- Soft-delete with recovery
- Bulk lifecycle operations
- Decommission workflow
"""

from datetime import datetime, timedelta
from typing import Any

from app.database import (
    _load, _save, _load_ref, _now, _id,
    get_org_config, SEED_ORG_CONFIG,
)


# ============================================================
# Lifecycle State Machine
# ============================================================

# Full lifecycle states for NGDC rules (Studio-created / migrated)
NGDC_RULE_STATES: dict[str, list[str]] = {
    "Draft": ["Submitted"],
    "Submitted": ["In Progress", "Rejected"],
    "In Progress": ["Approved", "Rejected"],
    "Approved": ["Deployed", "Rejected"],
    "Rejected": ["Submitted"],  # Allow re-submission
    "Deployed": ["Certified", "Decommissioning"],
    "Certified": ["Expired", "Decommissioning", "Deployed"],  # Deployed = re-certify needed
    "Expired": ["Certified", "Decommissioning"],  # Can re-certify or decommission
    "Decommissioning": ["Decommissioned"],
    "Decommissioned": [],  # Terminal
    "Deleted": [],  # Soft-delete terminal (can be recovered via restore)
}

# Legacy rule lifecycle (simpler — they start deployed)
LEGACY_RULE_STATES: dict[str, list[str]] = {
    "Deployed": ["Certified", "Decommissioning"],
    "Certified": ["Expired", "Decommissioning", "Deployed"],
    "Expired": ["Certified", "Decommissioning"],
    "Decommissioning": ["Decommissioned"],
    "Decommissioned": [],
    "Deleted": [],
}

# Event types for structured audit trail
EVENT_TYPES = [
    "created", "submitted", "approved", "rejected",
    "deployed", "certified", "expired", "decommission_requested",
    "decommissioned", "soft_deleted", "restored",
    "modified", "migrated", "comment", "bulk_action",
    "recertified", "ownership_changed",
]


def get_valid_transitions(current_status: str, is_legacy: bool = False) -> list[str]:
    """Return valid next states for a rule."""
    states = LEGACY_RULE_STATES if is_legacy else NGDC_RULE_STATES
    return states.get(current_status, [])


def is_valid_transition(current_status: str, new_status: str, is_legacy: bool = False) -> bool:
    """Check if a status transition is valid."""
    return new_status in get_valid_transitions(current_status, is_legacy)


# ============================================================
# Lifecycle Events (Structured Audit Trail)
# ============================================================

def _load_lifecycle_events() -> list[dict[str, Any]]:
    return _load("lifecycle_events") or []


def _save_lifecycle_events(events: list[dict[str, Any]]) -> None:
    _save("lifecycle_events", events)


async def record_lifecycle_event(
    rule_id: str,
    event_type: str,
    from_status: str | None = None,
    to_status: str | None = None,
    actor: str = "system",
    module: str = "studio",
    details: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a structured lifecycle event."""
    events = _load_lifecycle_events()
    event = {
        "id": f"evt-{_id()}",
        "rule_id": rule_id,
        "event_type": event_type,
        "from_status": from_status,
        "to_status": to_status,
        "actor": actor,
        "module": module,
        "details": details,
        "metadata": metadata or {},
        "timestamp": _now(),
    }
    events.append(event)
    _save_lifecycle_events(events)
    return event


async def get_lifecycle_events(
    rule_id: str | None = None,
    event_type: str | None = None,
    module: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Query lifecycle events with optional filters."""
    events = _load_lifecycle_events()
    if rule_id:
        events = [e for e in events if e.get("rule_id") == rule_id]
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    if module:
        events = [e for e in events if e.get("module") == module]
    # Sort by timestamp descending (most recent first)
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return events[offset:offset + limit]


async def get_rule_timeline(rule_id: str) -> list[dict[str, Any]]:
    """Get complete timeline for a specific rule, oldest first."""
    events = _load_lifecycle_events()
    timeline = [e for e in events if e.get("rule_id") == rule_id]
    timeline.sort(key=lambda e: e.get("timestamp", ""))
    return timeline


# ============================================================
# Lifecycle Transitions
# ============================================================

async def transition_lifecycle(
    rule_id: str,
    new_status: str,
    actor: str = "system",
    module: str = "studio",
    comments: str = "",
    is_legacy: bool = False,
) -> dict[str, Any]:
    """Transition a rule through the lifecycle state machine.
    Returns the updated rule or an error dict."""
    store_name = "legacy_rules" if is_legacy else "firewall_rules"
    id_field = "id" if is_legacy else "rule_id"
    rules = _load(store_name) or []
    now = _now()

    for r in rules:
        if r.get(id_field) == rule_id:
            current = r.get("lifecycle_status") or r.get("rule_status") or ("Deployed" if is_legacy else "Submitted")

            if not is_valid_transition(current, new_status, is_legacy):
                valid = get_valid_transitions(current, is_legacy)
                return {"error": f"Invalid transition: {current} -> {new_status}. Valid: {valid}"}

            # Update the rule
            r["lifecycle_status"] = new_status
            r["rule_status"] = new_status  # Keep backward compat
            r["updated_at"] = now

            # Status-specific side effects
            if new_status == "Deployed":
                r["status"] = "Deployed"
                r["deployed_at"] = now
            elif new_status == "Certified":
                r["status"] = "Certified"
                r["certified_date"] = now
                r["certified_by"] = actor
                config = (await get_org_config()) or SEED_ORG_CONFIG
                expiry_days = config.get("auto_certify_days", 365)
                r["expiry_date"] = (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
            elif new_status == "Expired":
                r["status"] = "Expired"
            elif new_status == "Decommissioning":
                r["status"] = "Decommissioning"
                r["decommission_requested_at"] = now
                r["decommission_requested_by"] = actor
            elif new_status == "Decommissioned":
                r["status"] = "Decommissioned"
                r["decommissioned_at"] = now
            elif new_status == "Rejected":
                r["status"] = "Rejected"
            elif new_status == "Approved":
                r["status"] = "Approved"
            elif new_status == "In Progress":
                r["status"] = "Pending Review"
            elif new_status == "Submitted":
                r["status"] = "Pending Review"

            _save(store_name, rules)

            # Record lifecycle event
            event_map = {
                "Submitted": "submitted", "In Progress": "approved",
                "Approved": "approved", "Rejected": "rejected",
                "Deployed": "deployed", "Certified": "certified",
                "Expired": "expired", "Decommissioning": "decommission_requested",
                "Decommissioned": "decommissioned",
            }
            event_type = event_map.get(new_status, "modified")
            await record_lifecycle_event(
                rule_id=rule_id,
                event_type=event_type,
                from_status=current,
                to_status=new_status,
                actor=actor,
                module=module,
                details=comments or f"Status changed from {current} to {new_status}",
            )

            # Also log to legacy rule_history for backward compat
            history = _load("rule_history") or []
            history.append({
                "rule_id": rule_id,
                "action": f"Lifecycle: {current} -> {new_status}",
                "timestamp": now,
                "details": comments or f"Lifecycle transition from {current} to {new_status}",
                "user": actor,
            })
            _save("rule_history", history)

            return r
    return {"error": f"Rule {rule_id} not found"}


# ============================================================
# Soft Delete & Recovery
# ============================================================

async def soft_delete_rule(
    rule_id: str,
    actor: str = "system",
    is_legacy: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    """Soft-delete a rule (mark as Deleted, preserve data for recovery)."""
    store_name = "legacy_rules" if is_legacy else "firewall_rules"
    id_field = "id" if is_legacy else "rule_id"
    rules = _load(store_name) or []
    now = _now()

    for r in rules:
        if r.get(id_field) == rule_id:
            r["lifecycle_status"] = "Deleted"
            r["rule_status"] = "Deleted"
            r["status"] = "Deleted"
            r["deleted_at"] = now
            r["deleted_by"] = actor
            r["delete_reason"] = reason
            r["_pre_delete_status"] = r.get("lifecycle_status", r.get("rule_status", ""))
            r["updated_at"] = now
            _save(store_name, rules)

            await record_lifecycle_event(
                rule_id=rule_id,
                event_type="soft_deleted",
                from_status=r.get("_pre_delete_status"),
                to_status="Deleted",
                actor=actor,
                details=reason or "Rule soft-deleted",
            )
            return r
    return {"error": f"Rule {rule_id} not found"}


async def restore_rule(
    rule_id: str,
    actor: str = "system",
    is_legacy: bool = False,
) -> dict[str, Any]:
    """Restore a soft-deleted rule to its previous status."""
    store_name = "legacy_rules" if is_legacy else "firewall_rules"
    id_field = "id" if is_legacy else "rule_id"
    rules = _load(store_name) or []
    now = _now()

    for r in rules:
        if r.get(id_field) == rule_id:
            if r.get("lifecycle_status") != "Deleted":
                return {"error": "Rule is not in Deleted state"}
            prev = r.get("_pre_delete_status", "Deployed")
            r["lifecycle_status"] = prev
            r["rule_status"] = prev
            r["status"] = prev
            r["restored_at"] = now
            r["restored_by"] = actor
            r.pop("deleted_at", None)
            r.pop("deleted_by", None)
            r.pop("delete_reason", None)
            r.pop("_pre_delete_status", None)
            r["updated_at"] = now
            _save(store_name, rules)

            await record_lifecycle_event(
                rule_id=rule_id,
                event_type="restored",
                from_status="Deleted",
                to_status=prev,
                actor=actor,
                details=f"Rule restored to {prev} status",
            )
            return r
    return {"error": f"Rule {rule_id} not found"}


# ============================================================
# Certification & Expiry
# ============================================================

async def check_expiring_rules(days_ahead: int = 30) -> dict[str, Any]:
    """Find rules that are expiring within the given number of days."""
    now = datetime.utcnow()
    threshold = now + timedelta(days=days_ahead)
    expiring: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []

    for store_name in ["firewall_rules", "legacy_rules"]:
        rules = _load(store_name) or []
        id_field = "rule_id" if store_name == "firewall_rules" else "id"
        for r in rules:
            expiry_str = r.get("expiry_date")
            if not expiry_str:
                continue
            try:
                expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00").replace("+00:00", ""))
            except (ValueError, AttributeError):
                continue

            status = r.get("lifecycle_status") or r.get("rule_status", "")
            if status in ("Deleted", "Decommissioned", "Decommissioning"):
                continue

            if expiry <= now:
                expired.append({
                    "rule_id": r.get(id_field),
                    "application": r.get("application", r.get("app_name", "")),
                    "expiry_date": expiry_str,
                    "status": status,
                    "store": store_name,
                    "days_overdue": (now - expiry).days,
                })
            elif expiry <= threshold:
                expiring.append({
                    "rule_id": r.get(id_field),
                    "application": r.get("application", r.get("app_name", "")),
                    "expiry_date": expiry_str,
                    "status": status,
                    "store": store_name,
                    "days_until_expiry": (expiry - now).days,
                })

    return {
        "expiring_soon": expiring,
        "already_expired": expired,
        "expiring_count": len(expiring),
        "expired_count": len(expired),
        "check_date": _now(),
        "threshold_days": days_ahead,
    }


async def auto_expire_rules() -> dict[str, Any]:
    """Auto-transition Certified rules past their expiry date to Expired status."""
    now = datetime.utcnow()
    transitioned: list[str] = []

    for store_name, id_field, is_legacy in [
        ("firewall_rules", "rule_id", False),
        ("legacy_rules", "id", True),
    ]:
        rules = _load(store_name) or []
        changed = False
        for r in rules:
            expiry_str = r.get("expiry_date")
            if not expiry_str:
                continue
            status = r.get("lifecycle_status") or r.get("rule_status", "")
            if status != "Certified":
                continue
            try:
                expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00").replace("+00:00", ""))
            except (ValueError, AttributeError):
                continue
            if expiry <= now:
                rule_id = r.get(id_field)
                r["lifecycle_status"] = "Expired"
                r["rule_status"] = "Expired"
                r["status"] = "Expired"
                r["updated_at"] = _now()
                changed = True
                transitioned.append(rule_id)
                await record_lifecycle_event(
                    rule_id=rule_id,
                    event_type="expired",
                    from_status="Certified",
                    to_status="Expired",
                    actor="system",
                    module="lifecycle-auto",
                    details=f"Auto-expired: certification expired on {expiry_str}",
                )
        if changed:
            _save(store_name, rules)

    return {
        "transitioned": transitioned,
        "count": len(transitioned),
        "run_at": _now(),
    }


async def bulk_certify(rule_ids: list[str], actor: str = "system") -> dict[str, Any]:
    """Bulk certify multiple rules at once."""
    results: list[dict[str, Any]] = []
    for rule_id in rule_ids:
        # Try NGDC rules first, then legacy
        result = await transition_lifecycle(rule_id, "Certified", actor=actor, module="lifecycle-bulk")
        if "error" in result and "not found" in result["error"]:
            result = await transition_lifecycle(rule_id, "Certified", actor=actor, module="lifecycle-bulk", is_legacy=True)
        results.append({"rule_id": rule_id, "success": "error" not in result, "detail": result.get("error", "OK")})
    return {
        "results": results,
        "total": len(rule_ids),
        "succeeded": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
    }


async def bulk_decommission(rule_ids: list[str], actor: str = "system", reason: str = "") -> dict[str, Any]:
    """Bulk request decommission for multiple rules."""
    results: list[dict[str, Any]] = []
    for rule_id in rule_ids:
        result = await transition_lifecycle(rule_id, "Decommissioning", actor=actor, module="lifecycle-bulk", comments=reason)
        if "error" in result and "not found" in result["error"]:
            result = await transition_lifecycle(rule_id, "Decommissioning", actor=actor, module="lifecycle-bulk", comments=reason, is_legacy=True)
        results.append({"rule_id": rule_id, "success": "error" not in result, "detail": result.get("error", "OK")})
    return {
        "results": results,
        "total": len(rule_ids),
        "succeeded": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
    }


# ============================================================
# Lifecycle Dashboard Stats
# ============================================================

async def get_lifecycle_dashboard() -> dict[str, Any]:
    """Get comprehensive lifecycle dashboard data."""
    ngdc_rules = _load("firewall_rules") or []
    legacy_rules = _load("legacy_rules") or []
    events = _load_lifecycle_events()

    # Status distributions
    ngdc_status_dist: dict[str, int] = {}
    legacy_status_dist: dict[str, int] = {}
    app_status_map: dict[str, dict[str, int]] = {}

    for r in ngdc_rules:
        status = r.get("lifecycle_status") or r.get("rule_status") or r.get("status", "Draft")
        ngdc_status_dist[status] = ngdc_status_dist.get(status, 0) + 1
        app = r.get("application", "Unknown")
        if app not in app_status_map:
            app_status_map[app] = {}
        app_status_map[app][status] = app_status_map[app].get(status, 0) + 1

    for r in legacy_rules:
        status = r.get("lifecycle_status") or r.get("rule_status") or "Deployed"
        legacy_status_dist[status] = legacy_status_dist.get(status, 0) + 1
        app = r.get("app_name", "Unknown")
        if app not in app_status_map:
            app_status_map[app] = {}
        app_status_map[app][status] = app_status_map[app].get(status, 0) + 1

    # Certification stats
    cert_check = await check_expiring_rules(30)

    # Recent events (last 50)
    recent_events = sorted(events, key=lambda e: e.get("timestamp", ""), reverse=True)[:50]

    # Decommission queue
    decom_queue = []
    for r in ngdc_rules:
        if r.get("lifecycle_status") == "Decommissioning" or r.get("rule_status") == "Decommissioning":
            decom_queue.append({
                "rule_id": r.get("rule_id"),
                "application": r.get("application", ""),
                "requested_at": r.get("decommission_requested_at"),
                "requested_by": r.get("decommission_requested_by", "system"),
                "type": "ngdc",
            })
    for r in legacy_rules:
        if r.get("lifecycle_status") == "Decommissioning" or r.get("rule_status") == "Decommissioning":
            decom_queue.append({
                "rule_id": r.get("id"),
                "application": r.get("app_name", ""),
                "requested_at": r.get("decommission_requested_at"),
                "requested_by": r.get("decommission_requested_by", "system"),
                "type": "legacy",
            })

    return {
        "ngdc_rules": {
            "total": len(ngdc_rules),
            "status_distribution": ngdc_status_dist,
        },
        "legacy_rules": {
            "total": len(legacy_rules),
            "status_distribution": legacy_status_dist,
        },
        "certification": {
            "expiring_soon": cert_check["expiring_count"],
            "already_expired": cert_check["expired_count"],
            "expiring_rules": cert_check["expiring_soon"][:10],
            "expired_rules": cert_check["already_expired"][:10],
        },
        "decommission_queue": decom_queue,
        "recent_events": recent_events,
        "app_breakdown": app_status_map,
        "generated_at": _now(),
    }


# ============================================================
# Migration Lifecycle Integration
# ============================================================

async def record_migration_lifecycle_event(
    rule_id: str,
    migration_action: str,
    actor: str = "system",
    details: str = "",
) -> dict[str, Any]:
    """Record a migration-specific lifecycle event."""
    return await record_lifecycle_event(
        rule_id=rule_id,
        event_type="migrated",
        from_status=None,
        to_status=None,
        actor=actor,
        module="migration",
        details=details or f"Migration action: {migration_action}",
        metadata={"migration_action": migration_action},
    )
