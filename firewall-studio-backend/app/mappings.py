"""Environment, neighbourhood, security zone, and component mappings.

This module contains all per-app per-environment mappings used for:
- Per-app per-environment DC/NH/SZ assignments (master table)
- Mapping application components (WEB, APP, DB, etc.) to appropriate security zones
- IP offset calculations for environment-specific addressing
- Convenience defaults for generating Non-Prod/Pre-Prod from Prod assignments

All mappings are editable via the Admin UI.
"""

from typing import Any


# =====================================================================
# PER-APP PER-ENVIRONMENT ASSIGNMENTS
# Each app has its own DC/NH/SZ for each environment independently.
# This is the master mapping table that the Admin UI edits.
# Cross-environment rules are exceptional - each row is environment-specific.
# 81 rows = 27 apps x 3 environments
# =====================================================================
APP_ENVIRONMENT_ASSIGNMENTS: list[dict[str, Any]] = [
    # --- CRM ---
    {"app_id": "CRM", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "criticality": 2, "pci_scope": True},
    {"app_id": "CRM", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UCDE", "criticality": 2, "pci_scope": True},
    {"app_id": "CRM", "environment": "Pre-Production",  "dc": "GAMMA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 2, "pci_scope": True},
    # --- ORD ---
    {"app_id": "ORD", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "GEN", "criticality": 1, "pci_scope": True},
    {"app_id": "ORD", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UGEN", "criticality": 1, "pci_scope": True},
    {"app_id": "ORD", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 1, "pci_scope": True},
    # --- PSA ---
    {"app_id": "PSA", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "GEN", "criticality": 3, "pci_scope": False},
    {"app_id": "PSA", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UGEN", "criticality": 3, "pci_scope": False},
    {"app_id": "PSA", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 3, "pci_scope": False},
    # --- DIG ---
    {"app_id": "DIG", "environment": "Production",     "dc": "BETA_NGDC",  "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "DIG", "environment": "Non-Production",  "dc": "BETA_NGDC",  "nh": "NH13", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "DIG", "environment": "Pre-Production",  "dc": "BETA_NGDC",  "nh": "NH17", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- PAY ---
    {"app_id": "PAY", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "PAY", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "PAY", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- ENT ---
    {"app_id": "ENT", "environment": "Production",     "dc": "BETA_NGDC",  "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "ENT", "environment": "Non-Production",  "dc": "BETA_NGDC",  "nh": "NH12", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "ENT", "environment": "Pre-Production",  "dc": "BETA_NGDC",  "nh": "NH16", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- SHR ---
    {"app_id": "SHR", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "GEN", "criticality": 3, "pci_scope": False},
    {"app_id": "SHR", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UGEN", "criticality": 3, "pci_scope": False},
    {"app_id": "SHR", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 3, "pci_scope": False},
    # --- WHL ---
    {"app_id": "WHL", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "WHL", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "WHL", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- CBK ---
    {"app_id": "CBK", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "CBK", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "CBK", "environment": "Pre-Production",  "dc": "GAMMA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- CLN ---
    {"app_id": "CLN", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "CLN", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "CLN", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- WLT ---
    {"app_id": "WLT", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "WLT", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "WLT", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- ACH ---
    {"app_id": "ACH", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "ACH", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "ACH", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- HRM ---
    {"app_id": "HRM", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "GEN", "criticality": 3, "pci_scope": False},
    {"app_id": "HRM", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UGEN", "criticality": 3, "pci_scope": False},
    {"app_id": "HRM", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 3, "pci_scope": False},
    # --- TRD ---
    {"app_id": "TRD", "environment": "Production",     "dc": "BETA_NGDC",  "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "TRD", "environment": "Non-Production",  "dc": "BETA_NGDC",  "nh": "NH13", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "TRD", "environment": "Pre-Production",  "dc": "BETA_NGDC",  "nh": "NH17", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- FRD ---
    {"app_id": "FRD", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "FRD", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "FRD", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- RGM ---
    {"app_id": "RGM", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH11", "sz": "RST", "criticality": 1, "pci_scope": True},
    {"app_id": "RGM", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UCCS", "criticality": 1, "pci_scope": True},
    {"app_id": "RGM", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_CCS", "criticality": 1, "pci_scope": True},
    # --- MBL ---
    {"app_id": "MBL", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "MBL", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "MBL", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- INS ---
    {"app_id": "INS", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "INS", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "INS", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- TAX ---
    {"app_id": "TAX", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "TAX", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "TAX", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- AML ---
    {"app_id": "AML", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "AML", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "AML", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- KYC ---
    {"app_id": "KYC", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "KYC", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "KYC", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- TRS ---
    {"app_id": "TRS", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "TRS", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "TRS", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- CCM ---
    {"app_id": "CCM", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True},
    {"app_id": "CCM", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UCDE", "criticality": 1, "pci_scope": True},
    {"app_id": "CCM", "environment": "Pre-Production",  "dc": "GAMMA_NGDC", "nh": "NH16", "sz": "PP_CDE", "criticality": 1, "pci_scope": True},
    # --- LON ---
    {"app_id": "LON", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "LON", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "LON", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- BRK ---
    {"app_id": "BRK", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False},
    {"app_id": "BRK", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH13", "sz": "UGEN", "criticality": 2, "pci_scope": False},
    {"app_id": "BRK", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_GEN", "criticality": 2, "pci_scope": False},
    # --- AGW ---
    {"app_id": "AGW", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "DMZ", "criticality": 1, "pci_scope": False},
    {"app_id": "AGW", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH15", "sz": "UGEN", "criticality": 1, "pci_scope": False},
    {"app_id": "AGW", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH17", "sz": "PP_DMZ", "criticality": 1, "pci_scope": False},
    # --- SOC ---
    {"app_id": "SOC", "environment": "Production",     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "GEN", "criticality": 1, "pci_scope": False},
    {"app_id": "SOC", "environment": "Non-Production",  "dc": "ALPHA_NGDC", "nh": "NH12", "sz": "UGEN", "criticality": 1, "pci_scope": False},
    {"app_id": "SOC", "environment": "Pre-Production",  "dc": "ALPHA_NGDC", "nh": "NH16", "sz": "PP_GEN", "criticality": 1, "pci_scope": False},
]


# =====================================================================
# CONVENIENCE DEFAULTS for auto-generating Non-Prod/Pre-Prod from Prod
# Used ONLY when creating new app entries from Prod data
# =====================================================================
SZ_TO_NONPROD: dict[str, str] = {
    "CDE": "UCDE", "GEN": "UGEN", "RST": "UCCS", "DMZ": "UGEN",
    "PAA": "UPAA", "CPA": "UCPA", "CCS": "UCCS", "Standard": "USTD",
}

SZ_TO_PREPROD: dict[str, str] = {
    "CDE": "PP_CDE", "GEN": "PP_GEN", "RST": "PP_RST", "DMZ": "PP_DMZ",
    "PAA": "PP_PAA", "CPA": "PP_CPA", "CCS": "PP_CCS", "Standard": "PP_GEN",
}

NH_TO_NONPROD: dict[str, str] = {
    "NH01": "NH12", "NH02": "NH12", "NH03": "NH13", "NH04": "NH13", "NH05": "NH12",
    "NH06": "NH13", "NH07": "NH15", "NH08": "NH12", "NH09": "NH15", "NH10": "NH13",
    "NH11": "NH12", "NH13": "NH15", "NH14": "NH15",
}

NH_TO_PREPROD: dict[str, str] = {
    "NH01": "NH16", "NH02": "NH16", "NH03": "NH17", "NH04": "NH17", "NH05": "NH16",
    "NH06": "NH17", "NH07": "NH16", "NH08": "NH16", "NH09": "NH16", "NH10": "NH17",
    "NH11": "NH16", "NH13": "NH17", "NH14": "NH17",
}


# =====================================================================
# COMPONENT-TO-SECURITY-ZONE MAPPING
# Maps app component types to appropriate SZs within each base SZ
# =====================================================================
COMPONENT_TO_SZ: dict[str, dict[str, str]] = {
    # === Production SZ mappings ===
    "CDE": {"WEB": "CDE", "APP": "CDE", "DB": "CDE", "BAT": "CDE", "MQ": "CDE", "API": "CDE", "LB": "DMZ", "MON": "MGT"},
    "GEN": {"WEB": "GEN", "APP": "GEN", "DB": "GEN", "BAT": "GEN", "MQ": "GEN", "API": "GEN", "LB": "DMZ", "MON": "MGT"},
    "RST": {"WEB": "RST", "APP": "RST", "DB": "RST", "BAT": "RST", "MQ": "RST", "API": "RST", "LB": "DMZ", "MON": "MGT"},
    "DMZ": {"WEB": "DMZ", "APP": "DMZ", "DB": "GEN", "BAT": "GEN", "MQ": "GEN", "API": "DMZ", "LB": "DMZ", "MON": "MGT"},
    "PAA": {"WEB": "PAA", "APP": "PAA", "DB": "PAA", "BAT": "PAA", "MQ": "PAA", "API": "PAA", "LB": "DMZ", "MON": "MGT"},
    # === Non-Production SZ mappings ===
    "UCDE": {"WEB": "UCDE", "APP": "UCDE", "DB": "UCDE", "BAT": "UCDE", "MQ": "UCDE", "API": "UCDE", "LB": "UGEN", "MON": "MGT"},
    "UGEN": {"WEB": "UGEN", "APP": "UGEN", "DB": "UGEN", "BAT": "UGEN", "MQ": "UGEN", "API": "UGEN", "LB": "UGEN", "MON": "MGT"},
    "USTD": {"WEB": "USTD", "APP": "USTD", "DB": "USTD", "BAT": "USTD", "MQ": "USTD", "API": "USTD", "LB": "UGEN", "MON": "MGT"},
    "UCCS": {"WEB": "UCCS", "APP": "UCCS", "DB": "UCCS", "BAT": "UCCS", "MQ": "UCCS", "API": "UCCS", "LB": "UGEN", "MON": "MGT"},
    "UPAA": {"WEB": "UPAA", "APP": "UPAA", "DB": "UPAA", "BAT": "UPAA", "MQ": "UPAA", "API": "UPAA", "LB": "UGEN", "MON": "MGT"},
    "UCPA": {"WEB": "UCPA", "APP": "UCPA", "DB": "UCPA", "BAT": "UCPA", "MQ": "UCPA", "API": "UCPA", "LB": "UGEN", "MON": "MGT"},
    # === Pre-Production SZ mappings ===
    "PP_CDE": {"WEB": "PP_CDE", "APP": "PP_CDE", "DB": "PP_CDE", "BAT": "PP_CDE", "MQ": "PP_CDE", "API": "PP_CDE", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_GEN": {"WEB": "PP_GEN", "APP": "PP_GEN", "DB": "PP_GEN", "BAT": "PP_GEN", "MQ": "PP_GEN", "API": "PP_GEN", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_CCS": {"WEB": "PP_CCS", "APP": "PP_CCS", "DB": "PP_CCS", "BAT": "PP_CCS", "MQ": "PP_CCS", "API": "PP_CCS", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_CPA": {"WEB": "PP_CPA", "APP": "PP_CPA", "DB": "PP_CPA", "BAT": "PP_CPA", "MQ": "PP_CPA", "API": "PP_CPA", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_PAA": {"WEB": "PP_PAA", "APP": "PP_PAA", "DB": "PP_PAA", "BAT": "PP_PAA", "MQ": "PP_PAA", "API": "PP_PAA", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_DMZ": {"WEB": "PP_DMZ", "APP": "PP_DMZ", "DB": "PP_GEN", "BAT": "PP_GEN", "MQ": "PP_GEN", "API": "PP_DMZ", "LB": "PP_DMZ", "MON": "MGT"},
    "PP_RST": {"WEB": "PP_RST", "APP": "PP_RST", "DB": "PP_RST", "BAT": "PP_RST", "MQ": "PP_RST", "API": "PP_RST", "LB": "PP_DMZ", "MON": "MGT"},
}


# =====================================================================
# IP OFFSET STRATEGY
# Non-Prod: +100 offset on 2nd octet; Pre-Prod: +80 offset
# =====================================================================
NONPROD_IP_OFFSET = 100
PREPROD_IP_OFFSET = 80


def offset_ip(ip_str: str, offset: int) -> str:
    """Offset the 2nd octet of an IP/CIDR by the given amount."""
    parts = ip_str.split("/")
    octets = parts[0].split(".")
    octets[1] = str(int(octets[1]) + offset)
    result = ".".join(octets)
    if len(parts) > 1:
        result += "/" + parts[1]
    return result


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def get_app_assignment(app_id: str, environment: str) -> dict[str, Any] | None:
    """Look up a specific app DC/NH/SZ assignment for a given environment."""
    for entry in APP_ENVIRONMENT_ASSIGNMENTS:
        if entry["app_id"] == app_id and entry["environment"] == environment:
            return dict(entry)
    return None


def get_all_app_ids() -> list[str]:
    """Return unique list of all app IDs from assignments."""
    seen: set[str] = set()
    result: list[str] = []
    for entry in APP_ENVIRONMENT_ASSIGNMENTS:
        aid = str(entry["app_id"])
        if aid not in seen:
            seen.add(aid)
            result.append(aid)
    return result


def build_standard_groups() -> list[dict[str, Any]]:
    """Generate NGDC standard group templates from APP_ENVIRONMENT_ASSIGNMENTS."""
    groups: list[dict[str, Any]] = []
    for entry in APP_ENVIRONMENT_ASSIGNMENTS:
        app_id = str(entry["app_id"])
        env = str(entry["environment"])
        nh = str(entry["nh"])
        sz = str(entry["sz"])
        for comp in ["WEB", "APP", "DB", "BAT", "MQ", "API"]:
            csz = COMPONENT_TO_SZ.get(sz, {}).get(comp, sz)
            groups.append({
                "app_id": app_id,
                "group_name": f"grp-{app_id}-{nh}-{csz}-{comp}",
                "nh": nh, "sz": csz, "component": comp,
                "environment": env,
                "description": f"NGDC standard {comp} group for {app_id} ({env})",
            })
    return groups


def expand_ip_mappings(prod_mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand production IP mappings to include Non-Prod and Pre-Prod variants
    using the per-app per-environment assignments table."""
    all_mappings = list(prod_mappings)
    for pm in prod_mappings:
        app_id = pm.get("app_id", "")
        np_assign = get_app_assignment(app_id, "Non-Production")
        pp_assign = get_app_assignment(app_id, "Pre-Production")
        if np_assign:
            all_mappings.append({
                **pm,
                "ngdc_ip": offset_ip(pm["ngdc_ip"], NONPROD_IP_OFFSET),
                "ngdc_nh": str(np_assign["nh"]),
                "ngdc_sz": str(np_assign["sz"]),
                "environment": "Non-Production",
            })
        if pp_assign:
            all_mappings.append({
                **pm,
                "ngdc_ip": offset_ip(pm["ngdc_ip"], PREPROD_IP_OFFSET),
                "ngdc_nh": str(pp_assign["nh"]),
                "ngdc_sz": str(pp_assign["sz"]),
                "environment": "Pre-Production",
            })
    return all_mappings
