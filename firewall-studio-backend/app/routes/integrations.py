"""Integration routes: ServiceNow CHG, Work Request, GitOps, Audit, Versioning."""

from fastapi import APIRouter, Query
from typing import Optional
from app.database import (
    get_audit_logs, create_audit_log,
    get_rule_versions, create_rule_version, get_rule,
    submit_servicenow_chg, close_servicenow_chg,
    get_chg_requests, get_chg_for_rule,
    submit_work_request, get_work_requests,
    gitops_push_rule, get_gitops_log, get_all_rules_for_gitops,
)

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


# ---- Audit Log ----

@router.get("/audit-log")
async def list_audit_logs(rule_id: Optional[str] = Query(None), limit: int = Query(100)):
    return await get_audit_logs(rule_id=rule_id, limit=limit)


@router.post("/audit-log")
async def add_audit_log(data: dict):
    return await create_audit_log(data)


# ---- Rule Versioning ----

@router.get("/rule-versions/{rule_id}")
async def list_rule_versions(rule_id: str):
    return await get_rule_versions(rule_id)


@router.post("/rule-versions/{rule_id}")
async def snapshot_rule_version(rule_id: str, data: dict | None = None):
    rule = await get_rule(rule_id)
    if not rule:
        return {"error": "Rule not found"}
    return await create_rule_version(
        rule_id=rule_id,
        rule_snapshot=rule,
        change_summary=(data or {}).get("change_summary", ""),
    )


# ---- ServiceNow CHG ----

@router.get("/servicenow/chg")
async def list_chg_requests():
    return await get_chg_requests()


@router.post("/servicenow/chg")
async def create_servicenow_chg(data: dict):
    return await submit_servicenow_chg(data)


@router.post("/servicenow/chg/{chg_id}/close")
async def close_chg(chg_id: str):
    return await close_servicenow_chg(chg_id)


@router.get("/servicenow/chg/rule/{rule_id}")
async def get_chg_by_rule(rule_id: str):
    chg = await get_chg_for_rule(rule_id)
    if not chg:
        return {"error": "No CHG found for this rule"}
    return chg


# ---- Work Request Portal ----

@router.get("/work-requests")
async def list_work_requests():
    return await get_work_requests()


@router.post("/work-requests")
async def create_work_request(data: dict):
    return await submit_work_request(data)


# ---- GitOps ----

@router.get("/gitops/log")
async def list_gitops_log():
    return await get_gitops_log()


@router.get("/gitops/rules")
async def list_gitops_rules():
    return await get_all_rules_for_gitops()


@router.post("/gitops/push")
async def push_to_gitops(data: dict):
    return await gitops_push_rule(data)
