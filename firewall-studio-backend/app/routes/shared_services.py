"""Routes for Shared Services, DC-scoped Application Presences, and the
multi-DC Rule Request / fan-out engine.

All endpoints are additive (do not break existing reference routes).
They live under /api/reference/shared-services and /api/rules/*.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.database import (
    create_rule_request,
    create_shared_service,
    delete_app_presence,
    delete_shared_service,
    delete_shared_service_presence,
    get_app_presences,
    get_rule_request,
    get_rule_requests,
    get_shared_service,
    get_shared_service_presences,
    get_shared_services,
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
    if not status:
        raise HTTPException(400, "status is required")
    r = await set_rule_request_status(request_id, status)
    if not r:
        raise HTTPException(404, "Rule request not found")
    return r
