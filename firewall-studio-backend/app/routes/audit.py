"""Audit Trail routes — logs every request action with timestamps and user info.

Data is stored in a JSON file (audit_trail.json) for now, with the schema
designed to be MongoDB-ready (each entry is a document with _id, timestamps,
and indexed fields like app_distributed_id).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

# JSON storage path — same pattern as existing database.py
_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_audit_trail() -> list[dict[str, Any]]:
    path = _DATA_DIR / "audit_trail.json"
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_audit_trail(data: list[dict[str, Any]]) -> None:
    _ensure_dir()
    path = _DATA_DIR / "audit_trail.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


async def record_audit_event(
    action: str,
    entity_type: str,
    entity_id: str,
    app_distributed_id: str = "",
    environment: str = "",
    user_email: str = "system",
    user_id: str = "",
    details: dict[str, Any] | None = None,
    before_snapshot: dict[str, Any] | None = None,
    after_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record an audit event. Called by other routes when actions happen."""
    entry = {
        "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "app_distributed_id": app_distributed_id,
        "environment": environment,
        "user_email": user_email,
        "user_id": user_id,
        "details": details or {},
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    trail = _load_audit_trail()
    trail.append(entry)
    _save_audit_trail(trail)
    return entry


# ---- API Endpoints ----

@router.get("")
async def list_audit_trail(
    app_distributed_id: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    action: str | None = Query(None),
    environment: str | None = Query(None),
    user_email: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List audit trail entries with optional filters. Returns newest first."""
    entries = _load_audit_trail()

    if app_distributed_id:
        entries = [e for e in entries if e.get("app_distributed_id") == app_distributed_id]
    if entity_type:
        entries = [e for e in entries if e.get("entity_type") == entity_type]
    if entity_id:
        entries = [e for e in entries if e.get("entity_id") == entity_id]
    if action:
        entries = [e for e in entries if e.get("action") == action]
    if environment:
        entries = [e for e in entries if e.get("environment") == environment]
    if user_email:
        entries = [e for e in entries
                   if user_email.lower() in (e.get("user_email") or "").lower()]

    # Sort newest first
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(entries)
    page = entries[offset:offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "entries": page}


@router.get("/{audit_id}")
async def get_audit_entry(audit_id: str) -> dict[str, Any]:
    """Get a single audit entry by ID."""
    for entry in _load_audit_trail():
        if entry.get("audit_id") == audit_id:
            return entry
    raise HTTPException(404, "Audit entry not found")


@router.get("/export/xlsx")
async def export_audit_xlsx(
    app_distributed_id: str | None = Query(None),
    environment: str | None = Query(None),
    entity_type: str | None = Query(None),
) -> StreamingResponse:
    """Export audit trail as Excel file."""
    from io import BytesIO
    from openpyxl import Workbook

    entries = _load_audit_trail()
    if app_distributed_id:
        entries = [e for e in entries if e.get("app_distributed_id") == app_distributed_id]
    if environment:
        entries = [e for e in entries if e.get("environment") == environment]
    if entity_type:
        entries = [e for e in entries if e.get("entity_type") == entity_type]

    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Trail"
    ws.append(["Audit ID", "Timestamp", "Action", "Entity Type", "Entity ID",
               "App Distributed ID", "Environment", "User Email", "Details"])
    for e in entries:
        ws.append([
            e.get("audit_id", ""),
            e.get("timestamp", ""),
            e.get("action", ""),
            e.get("entity_type", ""),
            e.get("entity_id", ""),
            e.get("app_distributed_id", ""),
            e.get("environment", ""),
            e.get("user_email", ""),
            json.dumps(e.get("details", {})),
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="audit_trail.xlsx"'},
    )
