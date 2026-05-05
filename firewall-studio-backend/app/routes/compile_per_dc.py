"""Per-DC compilation + deployed-snapshot routes.

A device (firewall) belongs to one DC, so the artifacts we ship to it
must be scoped to that DC: only rules whose src_dc OR dst_dc matches
the device's DC, and only the DC-local instance of every referenced
group (per-DC group identity is `(name, dc_id, environment)`).

A **deployed snapshot** is recorded per `(dc_id, environment)`. The
first compile after a snapshot exists emits delta-only operations;
the very first compile (no snapshot yet) emits everything as new.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Any

from app.database import (
    compile_per_dc,
    compile_per_dc_all,
    get_deployed_snapshot,
    list_deployed_snapshots,
    capture_deployed_snapshot,
)


router = APIRouter(prefix="/api/compile", tags=["Per-DC Compile"])


@router.post("/per-dc")
async def compile_per_dc_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a per-DC manifest for one DC + environment.

    Request body:
        {
          "dc_id": "ALPHA_NGDC",
          "environment": "Production",
          "vendor": "panos" | "fortinet" | "cisco" | "juniper" | "generic",
          "mode": "auto" | "initial" | "incremental"
        }

    `mode='auto'` (default) picks initial when no snapshot exists yet
    for `(dc_id, env)`, otherwise emits delta-only output.
    """
    dc_id = (payload.get("dc_id") or "").strip()
    if not dc_id:
        raise HTTPException(400, "dc_id is required")
    return await compile_per_dc(
        dc_id=dc_id,
        environment=payload.get("environment", "Production"),
        vendor=payload.get("vendor", "generic"),
        mode=payload.get("mode", "auto"),
    )


@router.post("/per-dc/all")
async def compile_per_dc_all_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    """Build per-DC manifests for every DC that has rules in the given
    environment. Returns ``{environment, vendor, mode, manifests}`` —
    one manifest per DC keyed by ``dc_id``.
    """
    return await compile_per_dc_all(
        environment=payload.get("environment", "Production"),
        vendor=payload.get("vendor", "generic"),
        mode=payload.get("mode", "auto"),
    )


@router.get("/snapshots")
async def list_snapshots_endpoint() -> list[dict[str, Any]]:
    """Flat list of all deployed snapshots — drives the Deployment
    Status banner ("which DCs have ever been deployed, and when")."""
    return await list_deployed_snapshots()


@router.get("/snapshots/{dc_id}")
async def get_snapshot_endpoint(
    dc_id: str, environment: str = Query("Production"),
) -> dict[str, Any]:
    """Most recent deployed snapshot for `(dc_id, environment)` or
    ``{exists: false}`` if nothing has ever been deployed there yet."""
    snap = await get_deployed_snapshot(dc_id, environment)
    if snap is None:
        return {
            "exists": False,
            "dc_id": dc_id,
            "environment": environment,
        }
    return {"exists": True, **snap}


@router.post("/snapshots/{dc_id}/capture")
async def capture_snapshot_endpoint(
    dc_id: str, payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Manually persist the current per-DC compile state as the deployed
    baseline. Used by the "Promote snapshot" admin action when an
    out-of-band deploy has happened and we want to mark it captured.
    """
    payload = payload or {}
    return await capture_deployed_snapshot(
        dc_id=dc_id,
        environment=payload.get("environment", "Production"),
        deployed_by=payload.get("deployed_by", "manual-capture"),
    )
