"""Routes for Shared Services, DC-scoped Application Presences, and the
multi-DC Rule Request / fan-out engine.

All endpoints are additive (do not break existing reference routes).
They live under /api/reference/shared-services and /api/rules/*.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.database import (
    classify_ip,
    classify_ips,
    create_rule_request,
    create_shared_service,
    delete_app_presence,
    delete_shared_service,
    delete_shared_service_presence,
    get_app_presences,
    get_occupants,
    get_rule_request,
    get_rule_requests,
    get_shared_service,
    get_shared_service_presences,
    get_shared_services,
    ingest_app_members,
    preview_rule_expansion,
    set_rule_request_status,
    update_shared_service,
    upsert_app_presence,
    upsert_shared_service_presence,
)

router = APIRouter(tags=["Shared Services & Multi-DC"])


# ---- Shared Services ----

@router.get("/api/reference/shared-services")
async def list_shared_services(
    environment: str | None = None,
    category: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    items = await get_shared_services()
    if environment:
        items = [s for s in items
                 if environment in (s.get("environments") or ["Production"])]
    if category:
        items = [s for s in items if s.get("category") == category]
    if q:
        ql = q.lower()
        items = [
            s for s in items
            if ql in str(s.get("service_id", "")).lower()
            or ql in str(s.get("name", "")).lower()
            or ql in str(s.get("description", "")).lower()
        ]
    return items


@router.post("/api/reference/shared-services")
async def create_shared_service_route(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("service_id"):
        raise HTTPException(400, "service_id is required")
    if not payload.get("name"):
        raise HTTPException(400, "name is required")
    return await create_shared_service(payload)


@router.get("/api/reference/shared-services/{service_id}")
async def get_shared_service_route(service_id: str) -> dict[str, Any]:
    s = await get_shared_service(service_id)
    if not s:
        raise HTTPException(404, f"Shared service {service_id} not found")
    return s


@router.put("/api/reference/shared-services/{service_id}")
async def update_shared_service_route(service_id: str,
                                       payload: dict[str, Any]) -> dict[str, Any]:
    s = await update_shared_service(service_id, payload)
    if not s:
        raise HTTPException(404, f"Shared service {service_id} not found")
    return s


@router.delete("/api/reference/shared-services/{service_id}")
async def delete_shared_service_route(service_id: str) -> dict[str, str]:
    ok = await delete_shared_service(service_id)
    if not ok:
        raise HTTPException(404, f"Shared service {service_id} not found")
    return {"status": "deleted", "service_id": service_id}


# ---- Shared Service Presences ----

@router.get("/api/reference/shared-services/{service_id}/presences")
async def list_shared_service_presences(service_id: str,
                                         environment: str | None = None,
                                         dc_id: str | None = None) -> list[dict[str, Any]]:
    items = await get_shared_service_presences(service_id)
    if environment:
        items = [p for p in items if p.get("environment") == environment]
    if dc_id:
        items = [p for p in items if p.get("dc_id") == dc_id]
    return items


@router.post("/api/reference/shared-services/{service_id}/presences")
async def upsert_shared_service_presence_route(service_id: str,
                                                 payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["service_id"] = service_id
    for required in ("dc_id", "environment", "nh_id", "sz_code"):
        if not payload.get(required):
            raise HTTPException(400, f"{required} is required on presence")
    return await upsert_shared_service_presence(payload)


@router.delete("/api/reference/shared-services/{service_id}/presences")
async def delete_shared_service_presence_route(service_id: str, dc_id: str,
                                                 environment: str, nh_id: str,
                                                 sz_code: str) -> dict[str, str]:
    ok = await delete_shared_service_presence(
        service_id, dc_id, environment, nh_id, sz_code)
    if not ok:
        raise HTTPException(404, "Presence not found")
    return {"status": "deleted"}


# ---- App Presences (DC-scoped) ----

@router.get("/api/reference/app-presences")
async def list_app_presences(app: str | None = None,
                              environment: str | None = None,
                              dc_id: str | None = None) -> list[dict[str, Any]]:
    items = await get_app_presences(app)
    if environment:
        items = [p for p in items if p.get("environment") == environment]
    if dc_id:
        items = [p for p in items if p.get("dc_id") == dc_id]
    return items


@router.post("/api/reference/app-presences")
async def upsert_app_presence_route(payload: dict[str, Any]) -> dict[str, Any]:
    for required in ("app_distributed_id", "dc_id", "environment",
                     "nh_id", "sz_code"):
        if not payload.get(required):
            raise HTTPException(400, f"{required} is required on app presence")
    return await upsert_app_presence(payload)


@router.delete("/api/reference/app-presences")
async def delete_app_presence_route(app_distributed_id: str, dc_id: str,
                                      environment: str, nh_id: str,
                                      sz_code: str) -> dict[str, str]:
    ok = await delete_app_presence(
        app_distributed_id, dc_id, environment, nh_id, sz_code)
    if not ok:
        raise HTTPException(404, "App presence not found")
    return {"status": "deleted"}


# ---- Bidirectional IP ↔ (DC, NH, SZ) classifier / occupants ----

@router.post("/api/reference/classify-ip")
async def classify_ip_route(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify a single IP/CIDR/range into (DC, NH, SZ).

    Body: {"ip": "10.1.2.3", "dc_hint": "DC1" (optional)}
    """
    ip = str(payload.get("ip", "")).strip()
    if not ip:
        raise HTTPException(400, "ip is required")
    return await classify_ip(ip, str(payload.get("dc_hint", "")))


@router.post("/api/reference/classify-ips")
async def classify_ips_route(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Batch classifier.

    Body: {"ips": ["10.1.2.3", "10.2.0.0/24"], "dc_hint": "..." (optional)}
    """
    ips = payload.get("ips") or []
    if not isinstance(ips, list):
        raise HTTPException(400, "ips must be a list")
    return await classify_ips([str(x) for x in ips], str(payload.get("dc_hint", "")))


@router.get("/api/reference/occupants")
async def occupants_route(dc: str = "", nh: str = "", sz: str = "",
                           environment: str = "") -> dict[str, Any]:
    """Reverse lookup: apps + shared services present in a (DC, NH, SZ) cell.

    Any of dc/nh/sz/environment may be empty (wildcard on that axis).
    """
    return await get_occupants(dc=dc, nh=nh, sz=sz, environment=environment)


@router.post("/api/reference/applications/{app_distributed_id}/ingest-members")
async def ingest_app_members_route(app_distributed_id: str,
                                     payload: dict[str, Any]) -> dict[str, Any]:
    """Classify IPs/CIDRs for an app and auto-materialize per-(DC, NH, SZ)
    presences + derived egress/ingress groups.

    Body: {
      "environment": "Production",
      "direction": "egress" | "ingress",
      "dc_hint": "DC1" (optional),
      "members": [{"kind": "ip"|"cidr"|"range"|"subnet", "value": "..."}, ...]
    }
    """
    env = str(payload.get("environment", "Production"))
    direction = str(payload.get("direction", "egress")).lower()
    members = payload.get("members") or []
    if not isinstance(members, list):
        raise HTTPException(400, "members must be a list")
    return await ingest_app_members(
        app_distributed_id=app_distributed_id,
        environment=env,
        members=[dict(m) for m in members],
        direction=direction,
        dc_hint=str(payload.get("dc_hint", "")),
        default_has_ingress=bool(payload.get("has_ingress", False)),
    )


# ---- Rule Requests (multi-DC fan-out) ----

@router.post("/api/rules/preview-expansion")
async def preview_expansion_route(payload: dict[str, Any]) -> dict[str, Any]:
    return await preview_rule_expansion(payload)


@router.get("/api/rules/requests")
async def list_rule_requests(environment: str | None = None,
                              status: str | None = None) -> list[dict[str, Any]]:
    items = await get_rule_requests()
    if environment:
        items = [r for r in items if r.get("environment") == environment]
    if status:
        items = [r for r in items if r.get("status") == status]
    return items


@router.post("/api/rules/requests")
async def create_rule_request_route(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("application_ref"):
        raise HTTPException(400, "application_ref is required")
    if not payload.get("destination_kind"):
        raise HTTPException(400, "destination_kind is required")
    return await create_rule_request(payload)


@router.get("/api/rules/requests/{request_id}")
async def get_rule_request_route(request_id: str) -> dict[str, Any]:
    r = await get_rule_request(request_id)
    if not r:
        raise HTTPException(404, "Rule request not found")
    return r


@router.put("/api/rules/requests/{request_id}/status")
async def set_rule_request_status_route(request_id: str,
                                          payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status")
    note = payload.get("note")
    if not status:
        raise HTTPException(400, "status is required")
    r = await set_rule_request_status(request_id, status, note)
    if not r:
        raise HTTPException(404, "Rule request not found")
    return r
