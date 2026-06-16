"""Rule Request Excel Export — simplified XLSX with the columns:
Source App, Source (Group), Source Details, Destination App,
Destination (Group), Destination Details, Ports.

This is the Phase 1 export: straightforward spreadsheet output
for each rule request's expanded physical rules.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.database import get_rule_request, get_rule_requests

router = APIRouter(prefix="/api/rules/requests", tags=["Request Export"])


def _resolve_group_members(group_name: str, dc: str = "") -> list[str]:
    """Resolve a group name to its member IPs/CIDRs from groups store.
    
    If dc is provided, looks for the DC-specific materialization of the group
    (same group name can have different members in different datacenters).
    Falls back to the first matching group if no DC-specific entry exists.
    """
    import json
    from pathlib import Path

    if not group_name:
        return []
    data_dir = Path(__file__).parent.parent.parent / "data"
    groups_path = data_dir / "groups.json"
    if not groups_path.exists():
        return []
    with open(groups_path, "r") as f:
        groups = json.load(f)

    def _extract_members(g: dict) -> list[str]:
        members = g.get("members") or g.get("member_ips") or []
        result = []
        for m in members:
            if isinstance(m, str):
                result.append(m)
            elif isinstance(m, dict):
                result.append(m.get("ip") or m.get("address") or m.get("value") or str(m))
            else:
                result.append(str(m))
        return result

    # First pass: find DC-specific match
    fallback_group = None
    for g in groups:
        name = g.get("name", "") or g.get("group_name", "")
        if name.upper() == group_name.upper():
            group_dc = g.get("dc") or g.get("datacenter") or g.get("dc_id") or ""
            if dc and group_dc and group_dc.upper() == dc.upper():
                return _extract_members(g)
            if fallback_group is None:
                fallback_group = g

    # Fallback: return first match (no DC filter)
    if fallback_group:
        return _extract_members(fallback_group)
    return []


def _details_block(members: list[str]) -> str:
    """Format group members for the Details cell:
      10.1.2.3
      10.1.2.4
      ...
    Returns empty string if no members found.
    """
    if not members:
        return "(no members found)"
    return "\n".join(members)


def _build_export_rows(request: dict[str, Any]) -> list[list[str]]:
    """Build rows for the simplified export spreadsheet.
    
    Each row represents one physical rule in a specific DC pair.
    Group members are resolved per-DC so each row shows the actual
    IPs for that datacenter.
    """
    rows: list[list[str]] = []
    expansion = request.get("expansion", [])

    src_app = request.get("source_ref") or request.get("application_ref", "")
    dst_app_default = request.get("destination_ref", "") or ""
    ports_default = request.get("ports", "")

    for rule in expansion:
        # Physical rule uses src_group_ref / dst_group_ref
        src_group = str(rule.get("src_group_ref", "") or rule.get("src_group", "") or "")
        dst_group = str(rule.get("dst_group_ref", "") or rule.get("dst_group", "") or "")
        ports = str(rule.get("ports", "") or ports_default)

        # DC information for this physical rule
        src_dc = str(rule.get("src_dc", "") or "")
        dst_dc = str(rule.get("dst_dc", "") or "")

        # Destination app — infer from the rule or the request
        dst_app = str(rule.get("dst_application", "") or rule.get("dst_app", "") or dst_app_default)

        # Resolve group members PER DC — different DCs have different IPs
        src_members = _resolve_group_members(src_group, dc=src_dc)
        dst_members = _resolve_group_members(dst_group, dc=dst_dc)

        rows.append([
            src_app,
            src_dc,
            src_group,
            _details_block(src_members),
            dst_app,
            dst_dc,
            dst_group,
            _details_block(dst_members),
            ports,
        ])

    # If no expansion rules, still output a row with request-level data
    if not rows:
        rows.append([
            src_app,
            "",
            "",
            "",
            dst_app_default,
            "",
            "",
            "",
            str(ports_default),
        ])

    return rows


@router.get("/{request_id}/export-xlsx")
async def export_request_xlsx(request_id: str) -> StreamingResponse:
    """Export a single rule request as the simplified Phase 1 Excel.

    Columns: Source App | Source (Group) | Source Expansion |
             Destination App | Destination (Group) | Destination Expansion | Ports
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    request = await get_rule_request(request_id)
    if not request:
        raise HTTPException(404, "Rule request not found")

    rows = _build_export_rows(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Rule Request"

    # Header styling
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Headers
    headers = [
        "Source App", "Source DC", "Source (Group)", "Source Details",
        "Destination App", "Destination DC", "Destination (Group)", "Destination Details",
        "Ports"
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # Data rows
    for row in rows:
        ws.append(row)

    # Set column widths (A-I)
    widths = [18, 18, 28, 40, 18, 18, 28, 40, 15]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # Wrap text for details columns (D=4 and H=8)
    for row_idx in range(2, ws.max_row + 1):
        for col in (4, 8):
            cell = ws.cell(row=row_idx, column=col)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Summary sheet
    ws2 = wb.create_sheet(title="Summary")
    ws2.append(["Field", "Value"])
    ws2.append(["Request ID", request.get("request_id", "")])
    ws2.append(["Source App", request.get("source_ref") or request.get("application_ref", "")])
    ws2.append(["Destination", request.get("destination_ref", "")])
    ws2.append(["Environment", request.get("environment", "")])
    ws2.append(["Ports", request.get("ports", "")])
    ws2.append(["Status", request.get("status", "")])
    ws2.append(["Created", request.get("created_at", "")])
    ws2.append(["Total Rules", str(len(rows))])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"{request_id}-rule-request.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export-all-xlsx")
async def export_all_requests_xlsx(
    environment: str | None = Query(None),
    status: str | None = Query(None),
) -> StreamingResponse:
    """Export all rule requests as a single Excel file with one sheet per request."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    requests = await get_rule_requests()
    if environment:
        requests = [r for r in requests if r.get("environment") == environment]
    if status:
        requests = [r for r in requests if r.get("status") == status]

    if not requests:
        raise HTTPException(404, "No rule requests found matching filters")

    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")

    headers = [
        "Source App", "Source DC", "Source (Group)", "Source Details",
        "Destination App", "Destination DC", "Destination (Group)", "Destination Details",
        "Ports"
    ]

    for req in requests[:50]:  # Limit to 50 sheets
        req_id = req.get("request_id", "Unknown")
        sheet_name = req_id[:31]  # Excel 31-char sheet name limit
        ws = wb.create_sheet(title=sheet_name)
        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        rows = _build_export_rows(req)
        for row in rows:
            ws.append(row)

        # Column widths (A-I)
        widths = [18, 18, 28, 40, 18, 18, 28, 40, 15]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[chr(64 + i)].width = w

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="all-rule-requests.xlsx"'},
    )
