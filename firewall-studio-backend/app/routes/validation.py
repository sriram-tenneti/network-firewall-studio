"""Firewall Validation routes — pass-through connectivity checks.

Supports:
- Single validation (source→destination+ports)
- Bulk validation (multiple checks)
- Per-rule-request validation (validates a specific request's rules)
- Multiple agentless probe methods (TCP, ICMP, HTTP, Traceroute, DNS, Firewall API)
- Policy-based validation (checks against deployed rules)
- Environment filtering (Production, Non-Production, Pre-Production)
"""
from __future__ import annotations

import asyncio
import json
import socket
import struct
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/validation", tags=["Firewall Validation"])

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_json(name: str) -> Any:
    path = _DATA_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save_json(name: str, data: Any) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = _DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---- Probe Methods (all agentless, no login needed) ----

async def _tcp_probe(host: str, port: int, timeout: float = 3.0) -> dict[str, Any]:
    """TCP SYN probe — attempts socket connection."""
    try:
        loop = asyncio.get_event_loop()
        fut = loop.run_in_executor(None, _tcp_connect, host, port, timeout)
        result = await asyncio.wait_for(fut, timeout=timeout + 1)
        return result
    except asyncio.TimeoutError:
        return {"method": "tcp_socket", "status": "TIMEOUT", "detail": f"Connection to {host}:{port} timed out"}
    except Exception as e:
        return {"method": "tcp_socket", "status": "ERROR", "detail": str(e)}


def _tcp_connect(host: str, port: int, timeout: float) -> dict[str, Any]:
    """Synchronous TCP connect for executor."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        if result == 0:
            return {"method": "tcp_socket", "status": "REACHABLE", "detail": f"TCP port {port} open on {host}"}
        else:
            return {"method": "tcp_socket", "status": "UNREACHABLE", "detail": f"TCP port {port} closed/filtered on {host} (errno={result})"}
    except socket.timeout:
        return {"method": "tcp_socket", "status": "TIMEOUT", "detail": f"Connection to {host}:{port} timed out"}
    except socket.gaierror:
        return {"method": "tcp_socket", "status": "DNS_FAILED", "detail": f"Cannot resolve hostname: {host}"}
    except Exception as e:
        return {"method": "tcp_socket", "status": "ERROR", "detail": str(e)}


async def _icmp_probe(host: str, timeout: float = 3.0) -> dict[str, Any]:
    """ICMP ping probe using system ping command."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(int(timeout)), host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
        if proc.returncode == 0:
            return {"method": "icmp_ping", "status": "REACHABLE", "detail": f"Host {host} responded to ICMP"}
        else:
            return {"method": "icmp_ping", "status": "UNREACHABLE", "detail": f"Host {host} did not respond to ICMP"}
    except asyncio.TimeoutError:
        return {"method": "icmp_ping", "status": "TIMEOUT", "detail": f"ICMP ping to {host} timed out"}
    except Exception as e:
        return {"method": "icmp_ping", "status": "ERROR", "detail": str(e)}


async def _http_probe(host: str, port: int, timeout: float = 3.0) -> dict[str, Any]:
    """HTTP(S) HEAD probe for web services."""
    import urllib.request
    import urllib.error
    import ssl

    scheme = "https" if port in (443, 8443) else "http"
    url = f"{scheme}://{host}:{port}/"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="HEAD")
        loop = asyncio.get_event_loop()
        resp = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=timeout, context=ctx)),
            timeout=timeout + 1
        )
        return {"method": "http_probe", "status": "REACHABLE", "detail": f"HTTP {resp.status} from {url}"}
    except urllib.error.URLError as e:
        return {"method": "http_probe", "status": "UNREACHABLE", "detail": f"HTTP probe failed: {e.reason}"}
    except asyncio.TimeoutError:
        return {"method": "http_probe", "status": "TIMEOUT", "detail": f"HTTP probe to {url} timed out"}
    except Exception as e:
        return {"method": "http_probe", "status": "ERROR", "detail": str(e)}


async def _dns_probe(host: str, timeout: float = 3.0) -> dict[str, Any]:
    """DNS resolution probe."""
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyname, host),
            timeout=timeout
        )
        return {"method": "dns_lookup", "status": "REACHABLE", "detail": f"Resolved {host} → {result}"}
    except socket.gaierror:
        return {"method": "dns_lookup", "status": "UNREACHABLE", "detail": f"Cannot resolve: {host}"}
    except asyncio.TimeoutError:
        return {"method": "dns_lookup", "status": "TIMEOUT", "detail": f"DNS lookup for {host} timed out"}
    except Exception as e:
        return {"method": "dns_lookup", "status": "ERROR", "detail": str(e)}


# ---- Entity Resolution ----

def _resolve_entity(entity: str, entity_type: str | None = None) -> dict[str, Any]:
    """Resolve an entity (IP, CIDR, group name, VM, FQDN) to usable target info."""
    if not entity:
        return {"type": "unknown", "value": entity, "resolved_ips": []}

    # Auto-detect entity type if not provided
    if not entity_type:
        if "/" in entity and any(c.isdigit() for c in entity.split("/")[0]):
            entity_type = "cidr"
        elif entity.replace(".", "").isdigit():
            entity_type = "ip"
        elif entity.startswith("grp-") or entity.startswith("g-"):
            entity_type = "group"
        elif entity.startswith("vm-") or entity.startswith("svr-"):
            entity_type = "vm"
        elif "." in entity and not entity.replace(".", "").isdigit():
            entity_type = "fqdn"
        else:
            entity_type = "ip"

    resolved: dict[str, Any] = {"type": entity_type, "value": entity, "resolved_ips": []}

    if entity_type == "ip":
        resolved["resolved_ips"] = [entity]
    elif entity_type == "cidr":
        resolved["resolved_ips"] = [entity]  # Keep as CIDR for matching
    elif entity_type == "group":
        # Lookup group members from reference data
        groups = _load_json("groups") or []
        for g in groups:
            if g.get("name", "").upper() == entity.upper():
                resolved["resolved_ips"] = g.get("members", [])
                resolved["group_info"] = {
                    "name": g.get("name"),
                    "nh": g.get("nh_id") or g.get("nh", ""),
                    "sz": g.get("sz_code") or g.get("sz", ""),
                }
                break
    elif entity_type == "fqdn":
        # Try DNS resolution
        try:
            ip = socket.gethostbyname(entity)
            resolved["resolved_ips"] = [ip]
        except socket.gaierror:
            resolved["resolved_ips"] = []
            resolved["resolution_error"] = f"Cannot resolve {entity}"
    elif entity_type == "vm":
        # Look up in reference data (would be VM registry in production)
        resolved["resolved_ips"] = []
        resolved["note"] = "VM resolution requires VM registry integration"

    return resolved


# ---- Policy Check ----

def _check_policy(
    source_entity: str,
    destination_entity: str,
    ports: str,
    environment: str = "",
) -> dict[str, Any]:
    """Check if traffic would be permitted based on deployed rules."""
    rules = _load_json("rules") or []

    # Filter to deployed/certified rules only
    active_rules = [r for r in rules
                    if r.get("status") in ("Deployed", "Certified", "Approved")
                    or r.get("rule_status") in ("Deployed", "Certified", "Approved")]

    if environment:
        active_rules = [r for r in active_rules if r.get("environment") == environment]

    matching_rules = []
    for rule in active_rules:
        src = rule.get("source", "")
        dst = rule.get("destination", "")
        # Normalize source/destination for comparison
        src_str = src if isinstance(src, str) else (src.get("group_name", "") if isinstance(src, dict) else "")
        dst_str = dst if isinstance(dst, str) else (dst.get("name", "") if isinstance(dst, dict) else "")

        # Check if source or destination matches
        src_match = (
            source_entity.upper() in src_str.upper()
            or src_str.upper() in source_entity.upper()
        ) if src_str else False
        dst_match = (
            destination_entity.upper() in dst_str.upper()
            or dst_str.upper() in destination_entity.upper()
        ) if dst_str else False

        if src_match and dst_match:
            matching_rules.append({
                "rule_id": rule.get("rule_id", ""),
                "source": src_str,
                "destination": dst_str,
                "ports": rule.get("ports", ""),
                "action": rule.get("action", "permit"),
                "status": rule.get("status") or rule.get("rule_status", ""),
            })

    if matching_rules:
        # Check if any rule explicitly denies
        deny_rules = [r for r in matching_rules if r.get("action", "").lower() == "deny"]
        if deny_rules:
            return {"verdict": "DENY", "matching_rules": matching_rules, "detail": "Explicit deny rule found"}
        return {"verdict": "PERMIT", "matching_rules": matching_rules, "detail": f"{len(matching_rules)} matching rule(s) found"}
    return {"verdict": "NO_RULE", "matching_rules": [], "detail": "No matching rule found for this traffic path"}


# ---- Validation Logic ----

async def _run_validation(
    source: str,
    destination: str,
    ports: str,
    source_type: str | None = None,
    destination_type: str | None = None,
    environment: str = "",
    live_check: bool = True,
    probe_methods: list[str] | None = None,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Run a single validation check."""

    validation_id = f"VAL-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Resolve entities
    src_resolved = _resolve_entity(source, source_type)
    dst_resolved = _resolve_entity(destination, destination_type)

    # Policy check
    policy_result = _check_policy(source, destination, ports, environment)

    # Live probe (if enabled)
    live_results: list[dict[str, Any]] = []
    if live_check and dst_resolved["resolved_ips"]:
        methods = probe_methods or ["tcp_socket", "icmp_ping"]
        port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()] if ports else []
        target_ip = dst_resolved["resolved_ips"][0]

        for method in methods:
            if method == "tcp_socket" and port_list:
                for port in port_list[:5]:  # Limit to 5 ports
                    result = await _tcp_probe(target_ip, port, timeout)
                    result["port"] = port
                    live_results.append(result)
            elif method == "icmp_ping":
                live_results.append(await _icmp_probe(target_ip, timeout))
            elif method == "http_probe" and port_list:
                for port in port_list[:3]:
                    live_results.append(await _http_probe(target_ip, port, timeout))
            elif method == "dns_lookup":
                live_results.append(await _dns_probe(destination, timeout))

    # Determine overall live verdict
    live_verdict = "NOT_TESTED"
    if live_results:
        reachable = any(r.get("status") == "REACHABLE" for r in live_results)
        unreachable = any(r.get("status") == "UNREACHABLE" for r in live_results)
        if reachable:
            live_verdict = "REACHABLE"
        elif unreachable:
            live_verdict = "UNREACHABLE"
        else:
            live_verdict = "TIMEOUT"

    # Drift detection
    drift_detected = False
    if policy_result["verdict"] == "PERMIT" and live_verdict == "UNREACHABLE":
        drift_detected = True
    elif policy_result["verdict"] in ("DENY", "NO_RULE") and live_verdict == "REACHABLE":
        drift_detected = True

    # Overall verdict
    if live_check and live_results:
        overall_verdict = live_verdict
    else:
        overall_verdict = policy_result["verdict"]

    return {
        "validation_id": validation_id,
        "timestamp": timestamp,
        "source": source,
        "source_type": src_resolved["type"],
        "source_resolved": src_resolved,
        "destination": destination,
        "destination_type": dst_resolved["type"],
        "destination_resolved": dst_resolved,
        "ports": ports,
        "environment": environment,
        "policy_verdict": policy_result["verdict"],
        "policy_detail": policy_result["detail"],
        "matching_rules": policy_result["matching_rules"],
        "live_verdict": live_verdict,
        "live_results": live_results,
        "drift_detected": drift_detected,
        "overall_verdict": overall_verdict,
    }


# ---- API Endpoints ----

@router.post("/single")
async def validate_single(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a single source→destination+ports check."""
    source = str(payload.get("source", "")).strip()
    destination = str(payload.get("destination", "")).strip()
    ports = str(payload.get("ports", "")).strip()

    if not source:
        raise HTTPException(400, "source is required")
    if not destination:
        raise HTTPException(400, "destination is required")

    result = await _run_validation(
        source=source,
        destination=destination,
        ports=ports,
        source_type=payload.get("source_type"),
        destination_type=payload.get("destination_type"),
        environment=payload.get("environment", ""),
        live_check=payload.get("live_check", True),
        probe_methods=payload.get("probe_methods"),
        timeout=float(payload.get("timeout", 3.0)),
    )

    # Record in audit trail
    from app.routes.audit import record_audit_event
    await record_audit_event(
        action="validation_single",
        entity_type="validation",
        entity_id=result["validation_id"],
        app_distributed_id=payload.get("app_distributed_id", ""),
        environment=payload.get("environment", ""),
        user_email=payload.get("user_email", "system"),
        details={"source": source, "destination": destination, "ports": ports, "verdict": result["overall_verdict"]},
    )

    return result


@router.post("/bulk")
async def validate_bulk(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate multiple checks in parallel."""
    checks = payload.get("checks", [])
    if not checks or not isinstance(checks, list):
        raise HTTPException(400, "checks must be a non-empty list")
    if len(checks) > 50:
        raise HTTPException(400, "Maximum 50 checks per bulk request")

    environment = payload.get("environment", "")
    live_check = payload.get("live_check", True)
    probe_methods = payload.get("probe_methods")
    timeout = float(payload.get("timeout", 3.0))

    tasks = []
    for check in checks:
        tasks.append(_run_validation(
            source=str(check.get("source", "")).strip(),
            destination=str(check.get("destination", "")).strip(),
            ports=str(check.get("ports", "")).strip(),
            source_type=check.get("source_type"),
            destination_type=check.get("destination_type"),
            environment=check.get("environment") or environment,
            live_check=live_check,
            probe_methods=probe_methods,
            timeout=timeout,
        ))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    processed = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            processed.append({"error": str(r), "source": checks[i].get("source"), "destination": checks[i].get("destination")})
        else:
            processed.append(r)

    # Summary
    total = len(processed)
    pass_count = sum(1 for r in processed if isinstance(r, dict) and r.get("overall_verdict") in ("REACHABLE", "PERMIT"))
    fail_count = sum(1 for r in processed if isinstance(r, dict) and r.get("overall_verdict") in ("UNREACHABLE", "DENY", "NO_RULE"))
    drift_count = sum(1 for r in processed if isinstance(r, dict) and r.get("drift_detected"))

    return {
        "total": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "drift_count": drift_count,
        "results": processed,
    }


@router.post("/request/{request_id}")
async def validate_request(request_id: str, payload: dict[str, Any] = {}) -> dict[str, Any]:
    """Validate all rules in a specific rule request."""
    from app.database import get_rule_request

    request = await get_rule_request(request_id)
    if not request:
        raise HTTPException(404, "Rule request not found")

    live_check = payload.get("live_check", True)
    probe_methods = payload.get("probe_methods")

    # Extract source/destination from the request's expansion
    expansion = request.get("expansion", [])
    if not expansion:
        return {
            "request_id": request_id,
            "total": 0,
            "results": [],
            "message": "No expanded rules to validate",
        }

    checks = []
    for rule in expansion:
        src_group = rule.get("src_group", "")
        dst_group = rule.get("dst_group", "")
        ports = rule.get("ports", "")
        checks.append({
            "source": src_group,
            "destination": dst_group,
            "ports": ports,
            "source_type": "group",
            "destination_type": "group",
            "environment": request.get("environment", ""),
        })

    if not checks:
        return {"request_id": request_id, "total": 0, "results": [], "message": "No rules extracted"}

    # Run validation for each expanded rule
    tasks = [_run_validation(**check, live_check=live_check, probe_methods=probe_methods) for check in checks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    processed = [r if not isinstance(r, Exception) else {"error": str(r)} for r in results]

    pass_count = sum(1 for r in processed if isinstance(r, dict) and r.get("overall_verdict") in ("REACHABLE", "PERMIT"))
    fail_count = sum(1 for r in processed if isinstance(r, dict) and r.get("overall_verdict") in ("UNREACHABLE", "DENY", "NO_RULE"))

    # Record audit
    from app.routes.audit import record_audit_event
    await record_audit_event(
        action="validation_request",
        entity_type="rule_request",
        entity_id=request_id,
        app_distributed_id=request.get("application_ref", ""),
        environment=request.get("environment", ""),
        details={"total": len(processed), "pass_count": pass_count, "fail_count": fail_count},
    )

    return {
        "request_id": request_id,
        "total": len(processed),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "results": processed,
    }


@router.post("/resolve")
async def resolve_entity(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve an entity to IPs/groups for debugging."""
    entity = str(payload.get("entity", "")).strip()
    entity_type = payload.get("entity_type")
    if not entity:
        raise HTTPException(400, "entity is required")
    return _resolve_entity(entity, entity_type)


@router.get("/methods")
async def list_methods() -> list[dict[str, str]]:
    """List available probe methods."""
    return [
        {"id": "tcp_socket", "name": "TCP Socket", "description": "SYN probe — most common for TCP ports"},
        {"id": "icmp_ping", "name": "ICMP Ping", "description": "Host reachability check"},
        {"id": "http_probe", "name": "HTTP(S) Probe", "description": "HEAD request for web services"},
        {"id": "dns_lookup", "name": "DNS Lookup", "description": "Hostname resolution check"},
        {"id": "traceroute", "name": "Traceroute", "description": "Hop-by-hop path trace (not yet implemented)"},
        {"id": "firewall_api", "name": "Firewall API", "description": "Query Palo Alto/Checkpoint/Fortinet (requires config)"},
    ]


@router.post("/export/xlsx")
async def export_validation_xlsx(payload: dict[str, Any]) -> StreamingResponse:
    """Export validation results as Excel file."""
    from openpyxl import Workbook

    results = payload.get("results", [])
    if not results:
        raise HTTPException(400, "results list is required")

    wb = Workbook()
    ws = wb.active
    ws.title = "Validation Results"
    ws.append(["Source", "Source Type", "Destination", "Dest Type", "Ports",
               "Environment", "Policy Verdict", "Live Verdict", "Drift", "Overall", "Detail"])
    for r in results:
        ws.append([
            r.get("source", ""),
            r.get("source_type", ""),
            r.get("destination", ""),
            r.get("destination_type", ""),
            r.get("ports", ""),
            r.get("environment", ""),
            r.get("policy_verdict", ""),
            r.get("live_verdict", ""),
            "YES" if r.get("drift_detected") else "NO",
            r.get("overall_verdict", ""),
            r.get("policy_detail", ""),
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="validation_results.xlsx"'},
    )
