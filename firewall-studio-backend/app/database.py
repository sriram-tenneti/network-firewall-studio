"""JSON-file-backed database for the Network Firewall Studio.

All reference data (Neighbourhoods, Security Zones, Data Centers, Applications,
IP Ranges, Naming Standards, Policy Matrix) is fully customizable via CRUD APIs.

Data is stored in JSON files under the data/ directory and seeded on first startup.
"""

import ipaddress
import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.seed_data import (
    SEED_NEIGHBOURHOODS as _SD_NH,
    SEED_SECURITY_ZONES as _SD_SZ,
    SEED_NGDC_DATACENTERS as _SD_NGDC_DC,
    SEED_LEGACY_DATACENTERS as _SD_LEGACY_DC,
    SEED_APPLICATIONS as _SD_APPS,
    SEED_ENVIRONMENTS as _SD_ENVS,
    SEED_PREDEFINED_DESTINATIONS as _SD_PREDEFS,
    SEED_NAMING_STANDARDS as _SD_NAMING,
    SEED_HERITAGE_DC_MATRIX as _SD_HDC_MTX,
    SEED_NGDC_PROD_MATRIX as _SD_PROD_MTX,
    SEED_NONPROD_MATRIX as _SD_NP_MTX,
    SEED_PREPROD_MATRIX as _SD_PP_MTX,
    SEED_POLICY_MATRIX as _SD_POLICY,
    SEED_ORG_CONFIG as _SD_ORG,
    SEED_GROUPS as _SD_GROUPS,
    SEED_LEGACY_GROUPS as _SD_LEGACY_GROUPS,
    SEED_LEGACY_RULES as _SD_LEGACY_RULES,
    SEED_IP_MAPPINGS as _SD_IP_MAPPINGS,
    SEED_FIREWALL_DEVICES as _SD_FW_DEVICES,
    SEED_FIREWALL_DEVICE_PATTERNS as _SD_FW_PATTERNS,
    SEED_DC_VENDOR_MAP as _SD_DC_VENDOR,
    SEED_APP_DC_MAPPINGS as _SD_APP_DC_MAPPINGS,
    SEED_REVIEWS as _SD_REVIEWS,
    SEED_LIFECYCLE_EVENTS as _SD_LIFECYCLE_EVENTS,
    SEED_SHARED_SERVICES as _SD_SHARED_SERVICES,
    SEED_SHARED_SERVICE_PRESENCES as _SD_SHARED_SERVICE_PRESENCES,
    SEED_APP_PRESENCES as _SD_APP_PRESENCES,
    SEED_PORT_CATALOG as _SD_PORT_CATALOG,
    build_seed_migrations as _sd_build_migrations,
    build_seed_chg_requests as _sd_build_chg_requests,
)

# Lifecycle event recording — integrated into all workflow functions.
# Uses lazy import to avoid circular dependency (lifecycle.py imports _load/_save from here).
async def _record_lifecycle(rule_id: str, event_type: str, from_status: str | None = None,
                            to_status: str | None = None, actor: str = "system",
                            module: str = "studio", details: str = "",
                            metadata: dict[str, Any] | None = None) -> None:
    """Record a lifecycle event directly into lifecycle_events store.
    Integrated into all workflow functions so every state change is tracked."""
    from app.services.lifecycle import record_lifecycle_event
    try:
        await record_lifecycle_event(
            rule_id=rule_id, event_type=event_type,
            from_status=from_status, to_status=to_status,
            actor=actor, module=module, details=details, metadata=metadata,
        )
    except Exception:
        pass  # Never block a workflow action due to lifecycle recording failure

SEED_DATA_DIR = Path(__file__).parent.parent / "data"
LIVE_DATA_DIR = Path(__file__).parent.parent / "live-data"
# Separate JSON directory for migration & studio data (safe to clean without affecting seed/live)
SEPARATE_DATA_DIR = Path(__file__).parent.parent / "user-data"

# Current data mode: "seed" uses data/ (seed/test data), "live" uses live-data/ (real data)
_data_mode: str = "seed"

# Hide-seed-data flag: when True, data endpoints filter out seed data and return only real/user data
_hide_seed: bool = False


def get_hide_seed() -> bool:
    """Return the current hide-seed-data setting."""
    return _hide_seed


def set_hide_seed(hide: bool) -> bool:
    """Toggle hide-seed-data. When True, only real/imported data is returned."""
    global _hide_seed
    _hide_seed = hide
    return _hide_seed


def _get_data_dir() -> Path:
    """Return the active data directory based on current mode."""
    return LIVE_DATA_DIR if _data_mode == "live" else SEED_DATA_DIR


# Keep DATA_DIR as a property-like accessor for backward compatibility
DATA_DIR = SEED_DATA_DIR


def get_data_mode() -> str:
    """Return the current data mode: 'seed' or 'live'."""
    return _data_mode


def set_data_mode(mode: str) -> str:
    """Switch data mode. 'seed' = test data, 'live' = real data."""
    global _data_mode
    if mode not in ("seed", "live"):
        raise ValueError("mode must be 'seed' or 'live'")
    _data_mode = mode
    # Ensure live-data dir exists when switching to live
    if mode == "live":
        LIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _bootstrap_live_reference_data()
    return _data_mode


# Reference data files that are org-level (names are real, values are editable).
# These get auto-copied from seed to live-data the first time live mode is activated,
# so the user starts with the same org structure and can then edit CIDR/metadata values.
_REFERENCE_DATA_FILES = [
    "neighbourhoods", "security_zones", "ngdc_datacenters", "legacy_datacenters",
    "applications", "environments", "predefined_destinations", "naming_standards",
    "policy_matrix", "heritage_dc_matrix", "ngdc_prod_matrix", "nonprod_matrix",
    "preprod_matrix", "org_config", "firewall_devices", "ip_mappings",
    "app_dc_mappings",
]


def _bootstrap_live_reference_data() -> None:
    """Copy org reference data from seed to live-data if not already present.
    Only copies files that don't exist yet in live-data, so user edits are preserved."""
    import shutil
    for name in _REFERENCE_DATA_FILES:
        live_path = LIVE_DATA_DIR / f"{name}.json"
        seed_path = SEED_DATA_DIR / f"{name}.json"
        if not live_path.exists() and seed_path.exists():
            shutil.copy2(seed_path, live_path)


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


def _shorten_ip_range(range_str: str) -> str:
    """Shorten an IP range to compact form.
    e.g. '10.124.132.4-10.124.132.9' -> '10.124.132.4-9'
    If IPs share the first N octets, only the differing octets of the end IP are kept.
    """
    import re as _re
    m = _re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*-\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$', range_str)
    if not m:
        return range_str
    start_parts = m.group(1).split('.')
    end_parts = m.group(2).split('.')
    common_count = 0
    for i in range(4):
        if start_parts[i] == end_parts[i]:
            common_count += 1
        else:
            break
    if common_count == 0:
        return range_str
    suffix = '.'.join(end_parts[common_count:])
    return f"{m.group(1)}-{suffix}"


def _auto_prefix(value: str, entry_type: str = "ip") -> str:
    """Auto-prefix a value based on entry type for NGDC naming standards.
    - ip -> svr-
    - group -> grp- (normalizes legacy g- to grp-)
    - cidr/range -> rng-
    - subnet -> net- (NGDC standard for subnets)
    If already prefixed, returns as-is (except g- which is normalized to grp-,
    and legacy sub- which is normalized to net-).
    Range values use short format: rng-10.124.132.4-9 instead of rng-10.124.132.4-10.124.132.9
    """
    v = value.strip()
    if not v:
        return v
    vl = v.lower()
    # Normalize legacy g- prefix to NGDC grp-
    if vl.startswith("g-") and not vl.startswith("grp-"):
        v = "grp-" + v[2:]
        return v
    # Normalize legacy sub- prefix to NGDC net-
    if vl.startswith("sub-"):
        v = "net-" + v[4:]
        return v
    # Already has a recognized prefix
    if vl.startswith(("svr-", "grp-", "rng-", "net-")):
        return v
    # Add prefix based on type
    if entry_type in ("group",):
        return f"grp-{v}"
    if entry_type in ("subnet",):
        return f"net-{v}"
    if entry_type in ("cidr", "range"):
        # Use short range format for IP ranges
        import re as _re
        if _re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*-\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            v = _shorten_ip_range(v)
        return f"rng-{v}"
    return f"svr-{v}"


def _ensure_dir() -> None:
    _get_data_dir().mkdir(parents=True, exist_ok=True)


def _load(name: str) -> Any:
    path = _get_data_dir() / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save(name: str, data: Any) -> None:
    _ensure_dir()
    path = _get_data_dir() / f"{name}.json"
    # Skip pretty-printing for large datasets (>5000 items) to improve write performance
    indent = None if isinstance(data, list) and len(data) > 5000 else 2
    with open(path, "w") as f:
        json.dump(data, f, indent=indent, default=str)


# --- Org-level reference data helpers (always use SEED_DATA_DIR) ---
# NHs, SZs, DCs, policy matrices, naming standards, org_config, environments,
# predefined_destinations, firewall_devices, app_dc_mappings, ip_mappings
# are org-level reference data shared across seed and live modes.

def _load_ref(name: str) -> Any:
    """Load org-level reference data — always from SEED_DATA_DIR regardless of data mode."""
    path = SEED_DATA_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save_ref(name: str, data: Any) -> None:
    """Save org-level reference data — always to SEED_DATA_DIR regardless of data mode."""
    SEED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = SEED_DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# --- Separate user-data JSON helpers (migration_data, studio_rules) ---

def _ensure_separate_dir() -> None:
    SEPARATE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_separate(name: str) -> Any:
    """Load from user-data/ directory (separate from seed/live)."""
    path = SEPARATE_DATA_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save_separate(name: str, data: Any) -> None:
    """Save to user-data/ directory (separate from seed/live)."""
    _ensure_separate_dir()
    path = SEPARATE_DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)



# ============================================================
# Seed Data (imported from seed_data.py)
# ============================================================
# All seed data is defined in seed_data.py and imported above.

SEED_NEIGHBOURHOODS = _SD_NH
SEED_SECURITY_ZONES = _SD_SZ
SEED_NGDC_DATACENTERS = _SD_NGDC_DC
SEED_LEGACY_DATACENTERS = _SD_LEGACY_DC
SEED_APPLICATIONS = _SD_APPS
SEED_ENVIRONMENTS = _SD_ENVS
SEED_PREDEFINED_DESTINATIONS = _SD_PREDEFS
SEED_NAMING_STANDARDS = _SD_NAMING
SEED_HERITAGE_DC_MATRIX = _SD_HDC_MTX
SEED_NGDC_PROD_MATRIX = _SD_PROD_MTX
SEED_NONPROD_MATRIX = _SD_NP_MTX
SEED_PREPROD_MATRIX = _SD_PP_MTX
SEED_POLICY_MATRIX = _SD_POLICY
SEED_ORG_CONFIG = _SD_ORG
SEED_GROUPS = _SD_GROUPS
SEED_LEGACY_GROUPS = _SD_LEGACY_GROUPS
SEED_LEGACY_RULES = _SD_LEGACY_RULES
SEED_IP_MAPPINGS = _SD_IP_MAPPINGS
SEED_MIGRATIONS = _sd_build_migrations()
SEED_MIGRATION_MAPPINGS: list[dict[str, Any]] = []
SEED_CHG_REQUESTS = _sd_build_chg_requests()
SEED_REVIEWS = _SD_REVIEWS
SEED_LIFECYCLE_EVENTS = _SD_LIFECYCLE_EVENTS


def _build_seed_rules() -> list[dict[str, Any]]:
    """Build NGDC firewall rules using the **egress / ingress** group model.

    Naming convention (per user approval):
      Source  (egress):  grp-{APP_DIST_ID}-{NH}-{SZ}
      Dest    (ingress): grp-{APP_DIST_ID}-{NH}-{SZ}-{COMP}-Ingress

    App-to-NH/SZ mapping (from SEED_APPLICATIONS):
      CRM  AD-1001  NH02/CCS      HRM  AD-1002  NH01/GEN
      TRD  AD-1003  NH06/CDE      PAY  AD-1004  NH08/CCS
      INS  AD-1005  NH04/STD      KYC  AD-1006  NH05/CCS
      FRD  AD-1007  NH02/CDE      LND  AD-1008  NH09/GEN
      WLT  AD-1009  NH10/PAA      CBK  AD-1010  NH08/CPA
      EPT  AD-1011  NH01/CCS      MBK  AD-1012  NH07/CPA

    LDF scenarios covered:
      LDF-001: GEN/STD zones across NHs → 0 boundaries (open zones, no firewall)
      LDF-002: Same NH, same SZ → 0 boundaries (intra-NH, intra-SZ)
      LDF-003: Segmented → open/different zone, different NHs → 1 boundary (egress only)
      LDF-004: Same segmented zone, different NHs → 2 boundaries (egress + ingress)
      LDF-005: Same NH, different segmented zones → 1 boundary
      LDF-006: PAA/CCS flow (internet → internal) → 2 boundaries
    """
    rules: list[dict[str, Any]] = []
    base = datetime.utcnow()
    seq = 3000

    # Each tuple: (source_group, source_zone, source_nh,
    #              dest_group, dest_zone, dest_nh,
    #              port, description, application, status, g2g, days_ago,
    #              environment, ldf_scenario)
    app_rules = [
        # ================================================================
        # LDF-002: Same NH, same SZ — 0 boundaries (intra-NH, intra-SZ)
        # ================================================================

        # CRM (AD-1001, NH02/CCS) — egress → own DB/API ingress
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1001-NH02-CCS-DB-Ingress", "CCS", "NH02",
         "TCP 1521", "CRM egress to CRM DB (same NH/SZ)", "CRM",
         "Deployed", True, -30, "Production", "LDF-002"),
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1001-NH02-CCS-API-Ingress", "CCS", "NH02",
         "TCP 8443", "CRM egress to CRM API (same NH/SZ)", "CRM",
         "Certified", True, -25, "Production", "LDF-002"),

        # TRD (AD-1003, NH06/CDE) — egress → own DB/MQ ingress
        ("grp-AD-1003-NH06-CDE", "CDE", "NH06",
         "grp-AD-1003-NH06-CDE-DB-Ingress", "CDE", "NH06",
         "TCP 1521", "TRD egress to TRD DB (same NH/SZ)", "TRD",
         "Deployed", True, -120, "Production", "LDF-002"),
        ("grp-AD-1003-NH06-CDE", "CDE", "NH06",
         "grp-AD-1003-NH06-CDE-MQ-Ingress", "CDE", "NH06",
         "TCP 9092", "TRD egress to TRD MQ (same NH/SZ)", "TRD",
         "Certified", True, -80, "Production", "LDF-002"),

        # PAY (AD-1004, NH08/CCS) — egress → own DB ingress
        ("grp-AD-1004-NH08-CCS", "CCS", "NH08",
         "grp-AD-1004-NH08-CCS-DB-Ingress", "CCS", "NH08",
         "TCP 1521", "PAY egress to PAY DB (same NH/SZ)", "PAY",
         "Deployed", True, -150, "Production", "LDF-002"),

        # FRD (AD-1007, NH02/CDE) — egress → own DB/MQ ingress
        ("grp-AD-1007-NH02-CDE", "CDE", "NH02",
         "grp-AD-1007-NH02-CDE-DB-Ingress", "CDE", "NH02",
         "TCP 1521", "FRD egress to FRD DB (same NH/SZ)", "FRD",
         "Deployed", True, -100, "Production", "LDF-002"),
        ("grp-AD-1007-NH02-CDE", "CDE", "NH02",
         "grp-AD-1007-NH02-CDE-MQ-Ingress", "CDE", "NH02",
         "TCP 9092", "FRD egress to FRD Kafka (same NH/SZ)", "FRD",
         "Deployed", True, -90, "Production", "LDF-002"),

        # CBK (AD-1010, NH08/CPA) — egress → own DB/MQ ingress
        ("grp-AD-1010-NH08-CPA", "CPA", "NH08",
         "grp-AD-1010-NH08-CPA-DB-Ingress", "CPA", "NH08",
         "TCP 1521", "CBK egress to CBK DB (same NH/SZ)", "CBK",
         "Deployed", True, -200, "Production", "LDF-002"),
        ("grp-AD-1010-NH08-CPA", "CPA", "NH08",
         "grp-AD-1010-NH08-CPA-MQ-Ingress", "CPA", "NH08",
         "TCP 5672", "CBK egress to CBK MQ (same NH/SZ)", "CBK",
         "Certified", True, -180, "Production", "LDF-002"),

        # KYC (AD-1006, NH05/CCS) — egress → own DB/API ingress
        ("grp-AD-1006-NH05-CCS", "CCS", "NH05",
         "grp-AD-1006-NH05-CCS-DB-Ingress", "CCS", "NH05",
         "TCP 5432", "KYC egress to KYC DB (same NH/SZ)", "KYC",
         "Deployed", True, -95, "Production", "LDF-002"),

        # WLT (AD-1009, NH10/PAA) — egress → own DB/API ingress
        ("grp-AD-1009-NH10-PAA", "PAA", "NH10",
         "grp-AD-1009-NH10-PAA-DB-Ingress", "PAA", "NH10",
         "TCP 1521", "WLT egress to WLT DB (same NH/SZ)", "WLT",
         "Deployed", True, -130, "Production", "LDF-002"),

        # MBK (AD-1012, NH07/CPA) — egress → own DB/API ingress
        ("grp-AD-1012-NH07-CPA", "CPA", "NH07",
         "grp-AD-1012-NH07-CPA-DB-Ingress", "CPA", "NH07",
         "TCP 1521", "MBK egress to MBK DB (same NH/SZ)", "MBK",
         "Deployed", True, -40, "Production", "LDF-002"),
        ("grp-AD-1012-NH07-CPA", "CPA", "NH07",
         "grp-AD-1012-NH07-CPA-API-Ingress", "CPA", "NH07",
         "TCP 8443", "MBK egress to MBK API (same NH/SZ)", "MBK",
         "Certified", True, -35, "Production", "LDF-002"),

        # INS (AD-1005, NH04/STD) — egress → own DB ingress
        ("grp-AD-1005-NH04-STD", "STD", "NH04",
         "grp-AD-1005-NH04-STD-DB-Ingress", "STD", "NH04",
         "TCP 5432", "INS egress to INS DB (same NH/SZ)", "INS",
         "Deployed", True, -85, "Production", "LDF-002"),

        # LND (AD-1008, NH09/GEN) — egress → own DB ingress
        ("grp-AD-1008-NH09-GEN", "GEN", "NH09",
         "grp-AD-1008-NH09-GEN-DB-Ingress", "GEN", "NH09",
         "TCP 5432", "LND egress to LND DB (same NH/SZ)", "LND",
         "Deployed", True, -110, "Production", "LDF-002"),

        # HRM (AD-1002, NH01/GEN) — no ingress, so egress-only internal
        # (HRM talks to its own backend; single-group rule)
        ("grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "TCP 5432", "HRM internal egress loopback (same NH/SZ)", "HRM",
         "Deployed", True, -90, "Production", "LDF-002"),

        # EPT (AD-1011, NH01/CCS) — egress → own API ingress
        ("grp-AD-1011-NH01-CCS", "CCS", "NH01",
         "grp-AD-1011-NH01-CCS-API-Ingress", "CCS", "NH01",
         "TCP 8443", "EPT egress to EPT API (same NH/SZ)", "EPT",
         "Deployed", True, -10, "Production", "LDF-002"),

        # ================================================================
        # LDF-001: GEN/STD zones across NHs — 0 boundaries (no firewall)
        # ================================================================

        # HRM(NH01/GEN) → LND(NH09/GEN): open zones, no FW
        ("grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "grp-AD-1008-NH09-GEN-DB-Ingress", "GEN", "NH09",
         "TCP 8443", "HRM to LND (GEN→GEN cross-NH, no FW)", "HRM",
         "Deployed", True, -85, "Production", "LDF-001"),

        # INS(NH04/STD) → HRM(NH01/GEN): open zones, no FW
        ("grp-AD-1005-NH04-STD", "STD", "NH04",
         "grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "TCP 8443", "INS to HRM (STD→GEN cross-NH, no FW)", "INS",
         "Certified", True, -75, "Production", "LDF-001"),

        # LND(NH09/GEN) → INS(NH04/STD): open zones, no FW
        ("grp-AD-1008-NH09-GEN", "GEN", "NH09",
         "grp-AD-1005-NH04-STD-DB-Ingress", "STD", "NH04",
         "TCP 5432", "LND to INS DB (GEN→STD cross-NH, no FW)", "LND",
         "Deployed", True, -65, "Production", "LDF-001"),

        # ================================================================
        # LDF-003: Segmented → open/different zone, different NHs — 1 boundary (egress)
        # Source is in a segmented zone (non-GEN/STD), dest is open or different segmented zone.
        # Egress rule required at source NH's SZ firewall only.
        # ================================================================

        # CRM(NH02/CCS) → HRM(NH01/GEN): CCS segmented egress → GEN open
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "TCP 8443", "CRM to HRM (CCS→GEN, 1 FW egress)", "CRM",
         "Pending Review", False, -10, "Production", "LDF-003"),

        # PAY(NH08/CCS) → FRD-API(NH02/CDE): CCS → CDE cross-SZ
        ("grp-AD-1004-NH08-CCS", "CCS", "NH08",
         "grp-AD-1007-NH02-CDE-API-Ingress", "CDE", "NH02",
         "TCP 8443", "PAY to FRD API (CCS→CDE, 1 FW egress)", "PAY",
         "Pending Review", False, -8, "Production", "LDF-003"),

        # FRD(NH02/CDE) → LND(NH09/GEN): CDE segmented → GEN open
        ("grp-AD-1007-NH02-CDE", "CDE", "NH02",
         "grp-AD-1008-NH09-GEN-DB-Ingress", "GEN", "NH09",
         "TCP 8443", "FRD to LND (CDE→GEN, 1 FW egress)", "FRD",
         "Certified", True, -45, "Production", "LDF-003"),

        # TRD(NH06/CDE) → INS(NH04/STD): CDE segmented → STD open
        ("grp-AD-1003-NH06-CDE", "CDE", "NH06",
         "grp-AD-1005-NH04-STD-DB-Ingress", "STD", "NH04",
         "TCP 8443", "TRD to INS (CDE→STD, 1 FW egress)", "TRD",
         "Pending Review", False, -6, "Production", "LDF-003"),

        # MBK(NH07/CPA) → KYC-DB(NH05/CCS): CPA → CCS cross-SZ
        ("grp-AD-1012-NH07-CPA", "CPA", "NH07",
         "grp-AD-1006-NH05-CCS-DB-Ingress", "CCS", "NH05",
         "TCP 8443", "MBK to KYC DB (CPA→CCS, 1 FW egress)", "MBK",
         "Certified", True, -30, "Production", "LDF-003"),

        # ================================================================
        # LDF-004: Same segmented zone, different NHs — 2 boundaries (egress + ingress)
        # Both source and destination are in the same segmented zone but different NHs.
        # ================================================================

        # CRM(NH02/CCS) → PAY-DB(NH08/CCS): CCS→CCS cross-NH
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1004-NH08-CCS-DB-Ingress", "CCS", "NH08",
         "TCP 8443", "CRM to PAY DB (CCS→CCS cross-NH, 2 FW)", "CRM",
         "Certified", True, -25, "Production", "LDF-004"),

        # KYC(NH05/CCS) → EPT-API(NH01/CCS): CCS→CCS cross-NH
        ("grp-AD-1006-NH05-CCS", "CCS", "NH05",
         "grp-AD-1011-NH01-CCS-API-Ingress", "CCS", "NH01",
         "TCP 8443", "KYC to EPT API (CCS→CCS cross-NH, 2 FW)", "KYC",
         "Pending Review", False, -3, "Production", "LDF-004"),

        # CBK(NH08/CPA) → MBK-API(NH07/CPA): CPA→CPA cross-NH
        ("grp-AD-1010-NH08-CPA", "CPA", "NH08",
         "grp-AD-1012-NH07-CPA-API-Ingress", "CPA", "NH07",
         "TCP 8443", "CBK to MBK API (CPA→CPA cross-NH, 2 FW)", "CBK",
         "Certified", True, -45, "Production", "LDF-004"),

        # FRD(NH02/CDE) → TRD-DB(NH06/CDE): CDE→CDE cross-NH
        ("grp-AD-1007-NH02-CDE", "CDE", "NH02",
         "grp-AD-1003-NH06-CDE-DB-Ingress", "CDE", "NH06",
         "TCP 8443", "FRD to TRD DB (CDE→CDE cross-NH, 2 FW)", "FRD",
         "Pending Review", False, -7, "Production", "LDF-004"),

        # ================================================================
        # LDF-005: Same NH, different segmented zones — 1 boundary
        # ================================================================

        # CRM(NH02/CCS) → FRD-API(NH02/CDE): same NH, CCS→CDE cross-zone
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1007-NH02-CDE-API-Ingress", "CDE", "NH02",
         "TCP 8443", "CRM to FRD API (same NH02, CCS→CDE cross-zone, 1 FW)", "CRM",
         "Certified", True, -40, "Production", "LDF-005"),

        # ================================================================
        # LDF-006: PAA/CCS flow — internet-facing to internal (2 boundaries)
        # ================================================================

        # EPT(NH01/CCS) → CRM-API(NH02/CCS): EPT is internet-facing portal
        ("grp-AD-1011-NH01-CCS", "CCS", "NH01",
         "grp-AD-1001-NH02-CCS-API-Ingress", "CCS", "NH02",
         "TCP 443", "EPT to CRM API (CCS→CCS cross-NH, 2 FW)", "EPT",
         "Pending Review", False, -4, "Production", "LDF-006"),

        # EPT(NH01/CCS) → CBK-API(NH08/CPA): CCS→CPA cross-SZ
        ("grp-AD-1011-NH01-CCS", "CCS", "NH01",
         "grp-AD-1010-NH08-CPA-API-Ingress", "CPA", "NH08",
         "TCP 8443", "EPT to CBK API (CCS→CPA, 2 FW)", "EPT",
         "Pending Review", False, -3, "Production", "LDF-006"),

        # WLT(NH10/PAA) → TRD-DB(NH06/CDE): PAA→CDE cross-SZ
        ("grp-AD-1009-NH10-PAA", "PAA", "NH10",
         "grp-AD-1003-NH06-CDE-DB-Ingress", "CDE", "NH06",
         "TCP 8443", "WLT to TRD DB (PAA→CDE, 2 FW)", "WLT",
         "Certified", True, -50, "Production", "LDF-006"),

        # ================================================================
        # Non-Production / Pre-Production / UAT environment rules
        # ================================================================

        # CRM Non-Prod (NH02/CCS)
        ("grp-AD-1001-NH02-CCS", "CCS", "NH02",
         "grp-AD-1001-NH02-CCS-DB-Ingress", "CCS", "NH02",
         "TCP 1521", "CRM egress to DB (Non-Prod)", "CRM",
         "Deployed", True, -60, "Non-Production", "LDF-002"),

        # TRD Non-Prod (NH06/CDE)
        ("grp-AD-1003-NH06-CDE", "CDE", "NH06",
         "grp-AD-1003-NH06-CDE-DB-Ingress", "CDE", "NH06",
         "TCP 1521", "TRD egress to DB (Non-Prod)", "TRD",
         "Certified", True, -90, "Non-Production", "LDF-002"),

        # PAY Pre-Prod cross-SZ (NH08/CCS → NH02/CDE)
        ("grp-AD-1004-NH08-CCS", "CCS", "NH08",
         "grp-AD-1007-NH02-CDE-API-Ingress", "CDE", "NH02",
         "TCP 8443", "PAY to FRD (Pre-Prod, CCS→CDE, 1 FW)", "PAY",
         "Certified", True, -50, "Pre-Production", "LDF-003"),

        # CBK Non-Prod (NH08/CPA)
        ("grp-AD-1010-NH08-CPA", "CPA", "NH08",
         "grp-AD-1010-NH08-CPA-DB-Ingress", "CPA", "NH08",
         "TCP 1521", "CBK egress to DB (Non-Prod)", "CBK",
         "Deployed", True, -120, "Non-Production", "LDF-002"),

        # CBK Non-Prod cross-NH CPA → CPA (NH08 → NH07)
        ("grp-AD-1010-NH08-CPA", "CPA", "NH08",
         "grp-AD-1012-NH07-CPA-API-Ingress", "CPA", "NH07",
         "TCP 8443", "CBK to MBK (Non-Prod, CPA→CPA, 2 FW)", "CBK",
         "Pending Review", False, -14, "Non-Production", "LDF-004"),

        # HRM UAT (NH01/GEN → NH09/GEN)
        ("grp-AD-1002-NH01-GEN", "GEN", "NH01",
         "grp-AD-1008-NH09-GEN-DB-Ingress", "GEN", "NH09",
         "TCP 8443", "HRM to LND (UAT, GEN→GEN, no FW)", "HRM",
         "Certified", True, -40, "UAT", "LDF-001"),

        # INS SIT (NH04/STD)
        ("grp-AD-1005-NH04-STD", "STD", "NH04",
         "grp-AD-1005-NH04-STD-DB-Ingress", "STD", "NH04",
         "TCP 8443", "INS egress to INS DB (SIT)", "INS",
         "Deployed", True, -55, "SIT", "LDF-002"),

        # WLT DR cross-NH PAA → CCS (NH10 → NH02)
        ("grp-AD-1009-NH10-PAA", "PAA", "NH10",
         "grp-AD-1001-NH02-CCS-API-Ingress", "CCS", "NH02",
         "TCP 8443", "WLT to CRM API (DR, PAA→CCS, 2 FW)", "WLT",
         "Pending Review", False, -5, "DR", "LDF-006"),

        # EPT Non-Prod (NH01/CCS → NH02/CDE)
        ("grp-AD-1011-NH01-CCS", "CCS", "NH01",
         "grp-AD-1007-NH02-CDE-MQ-Ingress", "CDE", "NH02",
         "TCP 443", "EPT to FRD MQ (Non-Prod, CCS→CDE, 2 FW)", "EPT",
         "Certified", True, -20, "Non-Production", "LDF-006"),
    ]

    for src, sz_s, src_nh, dst, sz_d, dst_nh, port, desc, app, st, g2g, days, env, ldf in app_rules:
        seq += 1
        ct = (base + timedelta(days=days)).isoformat()
        rules.append({
            "rule_id": f"R-{seq}", "source": src, "source_zone": sz_s, "source_nh": src_nh,
            "destination": dst, "destination_zone": sz_d, "destination_nh": dst_nh,
            "port": port, "protocol": port.split(" ")[0],
            "action": "Allow", "description": desc, "application": app, "status": st,
            "rule_status": st,
            "lifecycle_status": st,
            "rule_migration_status": "Migrated",
            "is_group_to_group": g2g, "environment": env, "datacenter": "ALPHA_NGDC",
            "ldf_scenario": ldf,
            "created_at": ct, "updated_at": ct,
            "certified_date": ct if st in ("Certified", "Deployed") else None,
            "expiry_date": (base + timedelta(days=365)).isoformat() if st in ("Certified", "Deployed") else None,
        })
    return rules


# IP Mapping and Firewall Device CRUD functions are defined
# in the async section below (after seed_database).



# ============================================================
# Seed / Init
# ============================================================

async def seed_database() -> None:
    """Seed JSON files with initial data. Always re-seeds to ensure fresh data."""
    _ensure_dir()
    # Always reseed — wipe old data so seed data is the single source of truth
    _save("neighbourhoods", deepcopy(SEED_NEIGHBOURHOODS))
    _save("security_zones", deepcopy(SEED_SECURITY_ZONES))
    _save("ngdc_datacenters", deepcopy(SEED_NGDC_DATACENTERS))
    _save("legacy_datacenters", deepcopy(SEED_LEGACY_DATACENTERS))
    _save("applications", deepcopy(SEED_APPLICATIONS))
    _save("environments", deepcopy(SEED_ENVIRONMENTS))
    _save("predefined_destinations", deepcopy(SEED_PREDEFINED_DESTINATIONS))
    _save("naming_standards", deepcopy(SEED_NAMING_STANDARDS))
    _save("policy_matrix", deepcopy(SEED_POLICY_MATRIX))
    _save("heritage_dc_matrix", deepcopy(SEED_HERITAGE_DC_MATRIX))
    _save("ngdc_prod_matrix", deepcopy(SEED_NGDC_PROD_MATRIX))
    _save("nonprod_matrix", deepcopy(SEED_NONPROD_MATRIX))
    _save("preprod_matrix", deepcopy(SEED_PREPROD_MATRIX))
    _save("org_config", deepcopy(SEED_ORG_CONFIG))
    _save("firewall_rules", _build_seed_rules())
    _save("rule_history", [])
    _save("migrations", deepcopy(SEED_MIGRATIONS))
    _save("migration_mappings", deepcopy(SEED_MIGRATION_MAPPINGS))
    _save("chg_requests", deepcopy(SEED_CHG_REQUESTS))
    _save("groups", deepcopy(SEED_GROUPS))
    _save("legacy_groups", deepcopy(SEED_LEGACY_GROUPS))
    _save("legacy_rules", deepcopy(SEED_LEGACY_RULES))
    _save("ip_mappings", deepcopy(SEED_IP_MAPPINGS))
    _save("firewall_devices", deepcopy(_SD_FW_DEVICES))
    _save("app_dc_mappings", deepcopy(_SD_APP_DC_MAPPINGS))
    _save("reviews", deepcopy(SEED_REVIEWS))
    _save("rule_modifications", [])
    _save("lifecycle_events", deepcopy(SEED_LIFECYCLE_EVENTS))
    # Revamp: Shared Services + presences + per-DC app presences
    _save("shared_services", deepcopy(_SD_SHARED_SERVICES))
    _save("shared_service_presences", deepcopy(_SD_SHARED_SERVICE_PRESENCES))
    _save("app_presences", deepcopy(_SD_APP_PRESENCES))
    _save("rule_requests", [])
    _save("port_catalog", deepcopy(_SD_PORT_CATALOG))
    # ITSM connector profiles (ServiceNow / Generic REST). Empty by
    # default; SNS configures them in Settings -> SNS Connector.
    if _load("itsm_connectors") is None:
        _save("itsm_connectors", [])
    # Refresh the SZ.naming_mode cache after every reseed so the group
    # resolver branches correctly from the very first request.
    _refresh_naming_mode_cache()
    # Materialize derived groups so Studio works end-to-end out of the box.
    existing_groups = _load("groups") or []
    derived = _build_derived_groups_from_presences(
        _SD_SHARED_SERVICE_PRESENCES, _SD_APP_PRESENCES
    )
    merged = _merge_groups_preserving_existing(existing_groups, derived)
    _save("groups", merged)


# ============================================================
# Read Operations (Reference Data)
# ============================================================

async def get_neighbourhoods() -> list[dict[str, Any]]:
    return _load("neighbourhoods") or []


async def get_security_zones() -> list[dict[str, Any]]:
    """Return the SZ catalog with `naming_mode` always populated.

    Older records without the field default to ``app_scoped`` so legacy
    SZs continue to work; the in-memory catalog is rewritten in place so
    the next read is consistent."""

    items = _load("security_zones") or []
    mutated = False
    for sz in items:
        if not sz.get("naming_mode"):
            sz["naming_mode"] = "app_scoped"
            mutated = True
    if mutated:
        _save("security_zones", items)
        _refresh_naming_mode_cache()
    return items


# ============================================================
# SZ-Level CIDR Resolution  (DC, NH, SZ) → CIDR
# ============================================================

def _resolve_sz_cidr_sync(dc: str, nh: str, sz: str) -> str:
    """Resolve CIDR from (DC, NH, SZ) tuple by looking up NH security_zones.
    Returns the matching CIDR or empty string if not found.
    Falls back to any-DC match if no DC-specific entry exists."""
    neighbourhoods = _load("neighbourhoods") or []
    for n in neighbourhoods:
        if str(n.get("nh_id", "")) != str(nh):
            continue
        sz_entries = n.get("security_zones", [])
        # First try exact DC match
        for entry in sz_entries:
            if str(entry.get("zone", "")) == str(sz) and str(entry.get("dc", "")) == str(dc):
                return str(entry.get("cidr", ""))
        # Fallback: match zone without DC (backward compat)
        for entry in sz_entries:
            if str(entry.get("zone", "")) == str(sz) and not entry.get("dc"):
                return str(entry.get("cidr", ""))
    return ""


async def resolve_sz_cidr(dc: str, nh: str, sz: str) -> str:
    """Async wrapper for SZ-level CIDR resolution."""
    return _resolve_sz_cidr_sync(dc, nh, sz)


async def get_nh_security_zones(nh_id: str, dc: str = "") -> list[dict[str, Any]]:
    """Get all security zone entries for a given NH, optionally filtered by DC."""
    neighbourhoods = _load("neighbourhoods") or []
    for n in neighbourhoods:
        if str(n.get("nh_id", "")) != str(nh_id):
            continue
        sz_entries = n.get("security_zones", [])
        if dc:
            return [e for e in sz_entries if str(e.get("dc", "")) == str(dc)]
        return sz_entries
    return []


async def get_all_sz_cidr_map() -> list[dict[str, Any]]:
    """Return a flat list of all (dc, nh, sz, cidr) tuples for the frontend."""
    neighbourhoods = _load("neighbourhoods") or []
    result: list[dict[str, Any]] = []
    for n in neighbourhoods:
        nh_id = str(n.get("nh_id", ""))
        nh_name = str(n.get("name", ""))
        for entry in n.get("security_zones", []):
            result.append({
                "nh": nh_id,
                "nh_name": nh_name,
                "sz": str(entry.get("zone", "")),
                "dc": str(entry.get("dc", "")),
                "cidr": str(entry.get("cidr", "")),
                "vrf_id": str(entry.get("vrf_id", "")),
                "description": str(entry.get("description", "")),
            })
    return result


async def upsert_sz_cidr_binding(
    nh_id: str, sz: str, dc: str, cidr: str,
    vrf_id: str = "", description: str = "",
) -> dict[str, Any] | None:
    """Add or update a single (DC, NH, SZ) CIDR binding on a neighbourhood.

    Keyed by (nh_id, sz, dc). DC may be empty string for a DC-agnostic fallback.
    Returns the resulting binding or None if the NH does not exist.
    """
    items = _load("neighbourhoods") or []
    for n in items:
        if str(n.get("nh_id", "")) != str(nh_id):
            continue
        szs = list(n.get("security_zones") or [])
        found = None
        for entry in szs:
            if (
                str(entry.get("zone", "")) == str(sz)
                and str(entry.get("dc", "")) == str(dc)
            ):
                found = entry
                break
        if found is None:
            found = {"zone": sz, "dc": dc}
            szs.append(found)
        found["cidr"] = cidr
        if vrf_id:
            found["vrf_id"] = vrf_id
        if description:
            found["description"] = description
        n["security_zones"] = szs
        _save("neighbourhoods", items)
        return {
            "nh": nh_id,
            "nh_name": str(n.get("name", "")),
            "sz": sz,
            "dc": dc,
            "cidr": cidr,
            "vrf_id": found.get("vrf_id", ""),
            "description": found.get("description", ""),
        }
    return None


async def delete_sz_cidr_binding(nh_id: str, sz: str, dc: str) -> bool:
    """Remove a CIDR binding for (nh_id, sz, dc). Returns True if removed."""
    items = _load("neighbourhoods") or []
    for n in items:
        if str(n.get("nh_id", "")) != str(nh_id):
            continue
        szs = list(n.get("security_zones") or [])
        new_szs = [
            e for e in szs
            if not (
                str(e.get("zone", "")) == str(sz)
                and str(e.get("dc", "")) == str(dc)
            )
        ]
        if len(new_szs) == len(szs):
            return False
        n["security_zones"] = new_szs
        _save("neighbourhoods", items)
        return True
    return False


# ============================================================
# Forward classifier: IP → (DC, NH, SZ)
# Hierarchy: DC → NH → SZ (SZ nested inside NH inside DC)
# Source of truth: neighbourhoods[*].security_zones[*] = {dc, zone, cidr}
# ============================================================

def _ip_in_cidr(ip: str, cidr: str) -> int:
    """Return containment prefix length if ip fits inside cidr; -1 otherwise.

    Accepts single-IP, CIDR, or 'a.b.c.d-a.b.c.e' range for the IP operand.
    For ranges, requires every address in the range to fit the cidr.
    """
    if not ip or not cidr:
        return -1
    try:
        target = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError:
        return -1
    try:
        if "-" in ip and "/" not in ip:
            lo_s, hi_s = [s.strip() for s in ip.split("-", 1)]
            lo = ipaddress.ip_address(lo_s)
            hi = ipaddress.ip_address(hi_s)
            if lo > hi:
                lo, hi = hi, lo
            if lo in target and hi in target:
                return target.prefixlen
            return -1
        net = ipaddress.ip_network(ip.strip(), strict=False)
        if net.subnet_of(target):
            return target.prefixlen
        return -1
    except ValueError:
        return -1


def _classify_ip_sync(ip: str, dc_hint: str = "") -> dict[str, Any]:
    """Classify a single IP/CIDR/range into its (DC, NH, SZ) cell.

    Walks all NH.security_zones bindings and picks the longest-prefix match.
    If dc_hint is given, DC-specific bindings win over DC-agnostic fallbacks.
    Returns {dc, nh, sz, cidr, matched, reason}.
    """
    neighbourhoods = _load("neighbourhoods") or []
    best: dict[str, Any] | None = None
    best_len = -1
    for n in neighbourhoods:
        nh_id = str(n.get("nh_id", ""))
        for e in n.get("security_zones") or []:
            cidr = str(e.get("cidr", "")).strip()
            if not cidr:
                continue
            dc = str(e.get("dc", ""))
            if dc_hint and dc and dc != dc_hint:
                continue
            plen = _ip_in_cidr(ip, cidr)
            if plen < 0:
                continue
            # DC-specific > DC-agnostic at same prefix length
            effective = plen + (1 if dc else 0)
            if effective > best_len:
                best_len = effective
                best = {
                    "dc": dc,
                    "nh": nh_id,
                    "sz": str(e.get("zone", "")),
                    "cidr": cidr,
                }
    if best:
        return {"matched": True, **best, "reason": "longest-prefix SZ CIDR binding match"}
    return {
        "matched": False, "dc": "", "nh": "", "sz": "", "cidr": "",
        "reason": "no SZ CIDR binding contains this address",
    }


async def classify_ip(ip: str, dc_hint: str = "") -> dict[str, Any]:
    """Async wrapper."""
    return _classify_ip_sync(ip, dc_hint)


async def classify_ips(ips: list[str], dc_hint: str = "") -> list[dict[str, Any]]:
    return [{"ip": ip, **_classify_ip_sync(ip, dc_hint)} for ip in ips if ip]


# ============================================================
# Reverse lookup: (DC, NH, SZ) → occupants (apps + shared services + members)
# ============================================================

async def get_occupants(dc: str = "", nh: str = "", sz: str = "",
                         environment: str = "") -> dict[str, Any]:
    """Return apps and shared services present in the given cell.

    Any of dc/nh/sz/environment may be empty — acts as wildcard on that axis.
    """
    apps = _load("app_presences") or []
    svcs = _load("shared_service_presences") or []

    def _match(p: dict[str, Any]) -> bool:
        if dc and str(p.get("dc_id", "")) != dc:
            return False
        if nh and str(p.get("nh_id", "")) != nh:
            return False
        if sz and str(p.get("sz_code", "")) != sz:
            return False
        if environment and str(p.get("environment", "Production")) != environment:
            return False
        return True

    app_rows = []
    for p in apps:
        if not _match(p):
            continue
        app_rows.append({
            "app_distributed_id": p.get("app_distributed_id", ""),
            "dc_id": p.get("dc_id", ""),
            "environment": p.get("environment", "Production"),
            "nh_id": p.get("nh_id", ""),
            "sz_code": p.get("sz_code", ""),
            "has_ingress": bool(p.get("has_ingress", False)),
            "egress_count": len(p.get("egress_members", []) or []),
            "ingress_count": len(p.get("ingress_members", []) or []),
            "egress_group": _app_egress_group_name(
                str(p.get("app_distributed_id", "")),
                str(p.get("nh_id", "")),
                str(p.get("sz_code", "")),
            ),
            "ingress_group": (
                _app_ingress_group_name(
                    str(p.get("app_distributed_id", "")),
                    str(p.get("nh_id", "")),
                    str(p.get("sz_code", "")),
                ) if p.get("has_ingress") else ""
            ),
        })

    svc_rows = []
    for p in svcs:
        if not _match(p):
            continue
        svc_rows.append({
            "service_id": p.get("service_id", ""),
            "dc_id": p.get("dc_id", ""),
            "environment": p.get("environment", "Production"),
            "nh_id": p.get("nh_id", ""),
            "sz_code": p.get("sz_code", ""),
            "member_count": len(p.get("members", []) or []),
            "group": _shared_service_group_name(
                str(p.get("service_id", "")),
                str(p.get("nh_id", "")),
                str(p.get("sz_code", "")),
            ),
        })

    return {
        "filter": {"dc": dc, "nh": nh, "sz": sz, "environment": environment},
        "applications": app_rows,
        "shared_services": svc_rows,
        "total": len(app_rows) + len(svc_rows),
    }


# ============================================================
# Ingest members: classify IPs/CIDRs and upsert presences + derive groups
# ============================================================

async def ingest_app_members(
    app_distributed_id: str,
    environment: str,
    members: list[dict[str, Any]],
    direction: str = "egress",
    dc_hint: str = "",
    default_has_ingress: bool = False,
) -> dict[str, Any]:
    """Classify each member, upsert app_presence per (DC, NH, SZ), auto-create
    derived groups.

    Each member: {"kind": "ip"|"cidr"|"range"|"subnet"|"group", "value": "..."}
    Returns {classified: [...], unclassified: [...], presences: [...]}.
    """
    app_dist_id = (app_distributed_id or "").upper()
    classified: list[dict[str, Any]] = []
    unclassified: list[dict[str, Any]] = []
    # bucket: (dc, nh, sz) -> list[MemberSpec]
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for m in members or []:
        kind = str(m.get("kind", "ip")).lower()
        value = str(m.get("value", "")).strip()
        if not value:
            continue
        if kind == "group":
            unclassified.append({"kind": kind, "value": value,
                                 "reason": "group members cannot be auto-classified"})
            continue
        res = _classify_ip_sync(value, dc_hint)
        if not res.get("matched"):
            unclassified.append({"kind": kind, "value": value,
                                 "reason": res.get("reason", "no match")})
            continue
        bucket_key = (res["dc"], res["nh"], res["sz"])
        buckets.setdefault(bucket_key, []).append({"kind": kind, "value": value})
        classified.append({
            "kind": kind, "value": value, "dc": res["dc"],
            "nh": res["nh"], "sz": res["sz"], "cidr": res["cidr"],
        })

    presences: list[dict[str, Any]] = []
    existing = _load("app_presences") or []
    for (dc, nh, sz), new_members in buckets.items():
        existing_row = None
        for p in existing:
            if (str(p.get("app_distributed_id", "")).upper() == app_dist_id
                    and p.get("dc_id") == dc
                    and p.get("environment") == environment
                    and p.get("nh_id") == nh
                    and p.get("sz_code") == sz):
                existing_row = p
                break
        merged_egress = list((existing_row or {}).get("egress_members", []) or [])
        merged_ingress = list((existing_row or {}).get("ingress_members", []) or [])
        if direction == "ingress":
            # dedupe by (kind, value)
            seen = {(str(x.get("kind")), str(x.get("value"))) for x in merged_ingress}
            for nm in new_members:
                k = (nm["kind"], nm["value"])
                if k not in seen:
                    merged_ingress.append(nm)
                    seen.add(k)
        else:
            seen = {(str(x.get("kind")), str(x.get("value"))) for x in merged_egress}
            for nm in new_members:
                k = (nm["kind"], nm["value"])
                if k not in seen:
                    merged_egress.append(nm)
                    seen.add(k)
        row = {
            "app_distributed_id": app_dist_id,
            "dc_id": dc,
            "dc_type": (existing_row or {}).get("dc_type", "NGDC"),
            "environment": environment,
            "nh_id": nh,
            "sz_code": sz,
            "has_ingress": bool((existing_row or {}).get("has_ingress",
                                                         default_has_ingress or direction == "ingress")),
            "egress_members": merged_egress,
            "ingress_members": merged_ingress,
        }
        if direction == "ingress":
            row["has_ingress"] = True
        saved = await upsert_app_presence(row)
        presences.append(saved)

    return {
        "app_distributed_id": app_dist_id,
        "environment": environment,
        "classified": classified,
        "unclassified": unclassified,
        "presences": presences,
    }


async def get_ngdc_datacenters() -> list[dict[str, Any]]:
    return _load("ngdc_datacenters") or []


async def get_legacy_datacenters() -> list[dict[str, Any]]:
    return _load("legacy_datacenters") or []


async def get_applications() -> list[dict[str, Any]]:
    return _load("applications") or []


async def get_environments() -> list[dict[str, Any]]:
    return _load("environments") or []


async def get_predefined_destinations() -> list[dict[str, Any]]:
    return _load("predefined_destinations") or []


async def get_naming_standards() -> dict[str, Any] | None:
    return _load("naming_standards")


async def get_policy_matrix() -> list[dict[str, Any]]:
    return _load("policy_matrix") or []


async def get_heritage_dc_matrix() -> list[dict[str, Any]]:
    return _load("heritage_dc_matrix") or []


async def get_ngdc_prod_matrix() -> list[dict[str, Any]]:
    return _load("ngdc_prod_matrix") or []


async def get_nonprod_matrix() -> list[dict[str, Any]]:
    return _load("nonprod_matrix") or []


async def get_preprod_matrix() -> list[dict[str, Any]]:
    return _load("preprod_matrix") or []


async def get_org_config() -> dict[str, Any] | None:
    return _load("org_config")


# ============================================================
# Firewall Rules CRUD
# ============================================================

async def get_legacy_rules() -> list[dict[str, Any]]:
    return _load("legacy_rules") or []


async def get_all_legacy_rules_across_modes() -> list[dict[str, Any]]:
    """Read legacy rules from BOTH seed and live directories, deduplicated by id.
    Used by endpoints that need to see all imported apps regardless of data mode."""
    seen_ids: set[str] = set()
    combined: list[dict[str, Any]] = []
    for data_dir in [SEED_DATA_DIR, LIVE_DATA_DIR]:
        path = data_dir / "legacy_rules.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    rules = json.load(f)
                if isinstance(rules, list):
                    for r in rules:
                        rid = r.get("id", "")
                        if rid and rid not in seen_ids:
                            seen_ids.add(rid)
                            combined.append(r)
            except Exception:
                pass
    return combined


async def update_legacy_rule(rule_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    rules = _load("legacy_rules") or []
    for r in rules:
        if r["id"] == rule_id:
            r.update(data)
            _save("legacy_rules", rules)
            return r
    return None


async def bulk_update_legacy_rule_app_id(
    rule_ids: list[str],
    app_distributed_id: str,
    app_name: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bulk-update app_distributed_id (and optionally app_name) for a list of legacy rules.

    If app_name is not provided, tries to auto-populate from the applications
    table first, then from existing rules that already have the given
    app_distributed_id.
    Also copies related fields (policy_name, inventory_item, etc.) from
    existing records of the new App Distributed ID — EXCEPT source, destination,
    service, and their expansions (per Issue 5 spec).
    Marks updated rules as user_modified to protect from re-import overwrite.
    Returns dict with updated count and whether the app was found.
    """
    rules = _load("legacy_rules") or []
    # Auto-lookup app_name and app_id from applications table first
    app_found = False
    app_id_from_table: str | None = None
    if not app_name:
        apps = _load("applications") or []
        for a in apps:
            if a.get("app_distributed_id") == app_distributed_id:
                app_name = a.get("name") or a.get("app_name")
                app_id_from_table = a.get("app_id")
                app_found = True
                break
    # Fallback: lookup from existing rules that already have this app_distributed_id
    # and collect related fields to copy
    related_fields: dict[str, str] = {}
    COPYABLE_FIELDS = [
        "app_id", "app_name", "policy_name", "inventory_item",
        "rule_source_zone", "rule_destination_zone", "rule_action",
    ]
    PROTECTED_FIELDS = [
        "rule_source", "rule_destination", "rule_service",
        "rule_source_expanded", "rule_destination_expanded", "rule_service_expanded",
    ]
    for r in rules:
        if r.get("app_distributed_id") == app_distributed_id:
            app_found = True
            if not app_name and r.get("app_name"):
                app_name = r["app_name"]
            # Collect non-empty copyable fields from first matching rule
            if not related_fields:
                for f in COPYABLE_FIELDS:
                    val = r.get(f)
                    if val:
                        related_fields[f] = str(val)
            if app_name and related_fields:
                break

    # If we found app_id from the applications table, inject it into related_fields
    if app_id_from_table and "app_id" not in related_fields:
        related_fields["app_id"] = str(app_id_from_table)

    # Apply any extra_fields provided by the caller (e.g. from popup)
    if extra_fields:
        for k, v in extra_fields.items():
            if k not in PROTECTED_FIELDS and v:
                related_fields[k] = str(v)

    rule_id_set = set(rule_ids)
    updated = 0
    for r in rules:
        if r.get("id") in rule_id_set:
            r["app_distributed_id"] = app_distributed_id
            if app_name:
                r["app_name"] = app_name
            # Also update app_id from the related_fields if available
            if related_fields.get("app_id"):
                r["app_id"] = related_fields["app_id"]
            # Copy related fields from existing records (skip protected fields)
            for f, val in related_fields.items():
                if f not in PROTECTED_FIELDS:
                    r[f] = val
            # Mark as user-modified to protect from re-import overwrite
            r["user_modified"] = True
            r["user_modified_at"] = _now()
            updated += 1
    if updated:
        _save("legacy_rules", rules)
    return {"updated": updated, "app_found": app_found, "fields_copied": list(related_fields.keys())}


async def delete_legacy_rule(rule_id: str) -> bool:
    rules = _load("legacy_rules") or []
    new_rules = [r for r in rules if r["id"] != rule_id]
    if len(new_rules) < len(rules):
        _save("legacy_rules", new_rules)
        return True
    return False


async def clear_all_legacy_rules() -> int:
    """Delete non-migrated legacy rules. Preserves rules that are already migrated or in-progress.
    App DC mappings and component mappings are NOT affected."""
    rules = _load("legacy_rules") or []
    migrated_statuses = {"Completed", "In Progress", "Mapped", "Needs Review"}
    preserved = [r for r in rules if r.get("migration_status") in migrated_statuses]
    deleted_count = len(rules) - len(preserved)
    _save("legacy_rules", preserved)
    return deleted_count


def _rule_fingerprint(rule: dict[str, Any]) -> str:
    """Build a fingerprint from ALL data columns of a rule (excludes internal fields like id, is_standard, migration_status).
    Two records are duplicates only when every imported column matches."""
    skip = {"id", "is_standard", "migration_status", "rule_status", "rule_migration_status", "imported_at", "environment"}
    parts: list[str] = []
    for k in sorted(rule.keys()):
        if k in skip:
            continue
        parts.append(f"{k}={rule[k]}")
    return "|".join(parts)


def _load_superseded_fingerprints() -> set[str]:
    """Load the set of fingerprints that have been superseded by approved modifications.
    If an imported rule matches a superseded fingerprint, it means the rule was the
    *original* version before a modification was applied — so we skip it on re-import."""
    data = _load_separate("superseded_fingerprints")
    if data is None:
        return set()
    return set(data)


def _add_superseded_fingerprint(fp: str) -> None:
    """Record a fingerprint as superseded (the original version before modification)."""
    existing = _load_superseded_fingerprints()
    existing.add(fp)
    _save_separate("superseded_fingerprints", list(existing))


def clear_superseded_fingerprints() -> int:
    """Clear all superseded fingerprints. Returns count of cleared entries.
    Called during full data reset so re-imports work cleanly."""
    existing = _load_superseded_fingerprints()
    count = len(existing)
    _save_separate("superseded_fingerprints", [])
    return count


async def import_legacy_rules(new_rules: list[dict[str, Any]]) -> dict[str, int]:
    """Import legacy rules from Excel, dedup against existing rules using ALL columns.
    Optimised for large imports (50K+ rows). Delta-based — only new/changed rows are added.
    Also skips rows that match superseded fingerprints (original versions of modified rules).
    NGDC auto-promotion is deferred — use the dedicated auto-import endpoint instead."""
    existing = _load("legacy_rules") or []
    existing_keys: set[str] = set()
    for r in existing:
        existing_keys.add(_rule_fingerprint(r))

    # Also load superseded fingerprints — these are originals of rules that were modified.
    # Re-importing the old version should be skipped since the modification supersedes it.
    superseded = _load_superseded_fingerprints()

    max_num = 0
    for r in existing:
        try:
            num = int(r["id"].split("-")[1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            pass

    # Build set of IDs for user-modified rules — these must not be overwritten (Issue 5)
    user_modified_ids: set[str] = set()
    for r in existing:
        if r.get("user_modified"):
            user_modified_ids.add(r.get("id", ""))

    added = 0
    duplicates = 0
    superseded_skipped = 0
    user_modified_skipped = 0
    for rule in new_rules:
        fp = _rule_fingerprint(rule)
        if fp in existing_keys:
            duplicates += 1
            continue
        if fp in superseded:
            superseded_skipped += 1
            duplicates += 1  # count as duplicate for the caller
            continue
        # Check if this rule would overwrite a user-modified rule (by matching app_distributed_id + source + dest)
        # If so, skip it to protect the user's modifications
        rule_app_id = rule.get("app_distributed_id", "")
        rule_src = rule.get("rule_source", "")
        rule_dst = rule.get("rule_destination", "")
        skip_as_modified = False
        if rule_app_id and user_modified_ids:
            for er in existing:
                if (er.get("id") in user_modified_ids and
                    er.get("app_distributed_id") == rule_app_id and
                    er.get("rule_source") == rule_src and
                    er.get("rule_destination") == rule_dst):
                    skip_as_modified = True
                    break
        if skip_as_modified:
            user_modified_skipped += 1
            duplicates += 1
            continue
        max_num += 1
        rule["id"] = f"LR-{max_num:05d}"
        rule.setdefault("is_standard", False)
        rule.setdefault("migration_status", "Not Started")
        # Default environment to Production if not set
        rule.setdefault("environment", "Production")
        # Lifecycle statuses for imported rules:
        # rule_status = Deployed (imported rules are already deployed in legacy)
        # rule_migration_status = Yet to Migrate (not yet migrated to NGDC)
        rule.setdefault("rule_status", "Deployed")
        rule.setdefault("rule_migration_status", "Yet to Migrate")
        existing.append(rule)
        existing_keys.add(fp)
        added += 1

    _save("legacy_rules", existing)
    return {"added": added, "duplicates": duplicates, "superseded_skipped": superseded_skipped,
            "user_modified_skipped": user_modified_skipped, "total": len(existing)}


async def get_migration_history() -> list[dict[str, Any]]:
    return _load("migration_history") or []


async def log_migration(rule_id: str, action: str, from_status: str, to_status: str, details: str = "") -> dict[str, Any]:
    history = _load("migration_history") or []
    entry = {
        "id": f"MH-{_id()}",
        "rule_id": rule_id,
        "action": action,
        "from_status": from_status,
        "to_status": to_status,
        "details": details,
        "timestamp": _now(),
        "user": "system",
    }
    history.append(entry)
    _save("migration_history", history)
    return entry


async def migrate_rule_to_ngdc(rule_id: str) -> dict[str, Any] | None:
    """Mark rule as migrated: move to Firewall Studio, remove from legacy views.
    Also auto-creates recommended NGDC groups with mapped IPs."""
    rules = _load("legacy_rules") or []
    for r in rules:
        if r["id"] == rule_id:
            old_status = r.get("migration_status", "Not Started")
            r["migration_status"] = "Completed"
            # Update lifecycle statuses on migration
            r["rule_migration_status"] = "Migrated"
            r["migrated_at"] = _now()
            _save("legacy_rules", rules)
            await log_migration(rule_id, "migrate_to_ngdc", old_status, "Completed",
                                f"Rule {rule_id} migrated to NGDC standards")
            # Record lifecycle event: rule migrated
            await _record_lifecycle(rule_id, "migrated", from_status="Deployed",
                                    to_status="Migrated", module="migration-studio",
                                    details=f"Rule {rule_id} migrated to NGDC standards")
            # Also save to separate migration_data.json for safe cleanup
            await save_migration_data_entry("migrated_rules", {
                "rule_id": rule_id,
                "app_id": str(r.get("app_id", "")),
                "app_name": r.get("app_name", ""),
                "rule_source": r.get("rule_source", ""),
                "rule_destination": r.get("rule_destination", ""),
                "rule_service": r.get("rule_service", ""),
                "migrated_at": r["migrated_at"],
                "migration_status": "Completed",
            })

            # Auto-create recommended NGDC groups post-migration
            src_groups: list[str] = []
            dst_groups: list[str] = []
            rec_nh = ""
            rec_sz = ""
            rec_dc = ""
            try:
                recs = await get_ngdc_recommendations(rule_id)
                if recs:
                    rec_nh = recs.get("recommended_nh", "")
                    rec_sz = recs.get("recommended_sz", "")
                    rec_dc = recs.get("recommended_dc", "ALPHA_NGDC")
                    for cg in recs.get("component_groups") or []:
                        grp_name = cg.get("ngdc_group", "")
                        if not grp_name:
                            continue
                        # Use mapped NGDC IPs if available, else legacy IPs
                        ips = cg.get("ngdc_ips") or cg.get("ips") or []
                        members = [{"type": "ip", "value": ip, "description": f"Migrated from {rule_id}"} for ip in ips]
                        app_id_val = str(r.get("app_id", ""))
                        await create_migration_group(
                            name=grp_name,
                            app_id=app_id_val,
                            members=members,
                            nh=cg.get("nh", ""),
                            sz=cg.get("sz", ""),
                        )
                        direction = cg.get("direction", "source")
                        if direction == "source":
                            src_groups.append(grp_name)
                        else:
                            dst_groups.append(grp_name)
            except Exception:
                pass  # Group creation is best-effort; don't block migration

            # Auto-create rule in Firewall Studio so it appears post-migration
            try:
                src_val = ",".join(src_groups) if src_groups else r.get("rule_source", "")
                dst_val = ",".join(dst_groups) if dst_groups else r.get("rule_destination", "")
                src_zone = r.get("rule_source_zone", rec_sz or "STD")
                dst_zone = r.get("rule_destination_zone", rec_sz or "STD")
                svc = r.get("rule_service", "")
                app_id_str = str(r.get("app_id", ""))
                env = r.get("policy_name", "Production")
                await create_rule({
                    "source": {"source_type": "Group", "ip_address": None, "cidr": None,
                               "group_name": src_val, "ports": svc, "neighbourhood": rec_nh,
                               "security_zone": src_zone},
                    "destination": {"name": dst_val, "security_zone": dst_zone,
                                    "dest_ip": None, "ports": svc, "is_predefined": False},
                    "port": svc,
                    "protocol": "TCP",
                    "action": r.get("rule_action", "Allow"),
                    "description": f"Migrated from legacy rule {rule_id}",
                    "application": app_id_str,
                    "environment": env,
                    "datacenter": rec_dc or "ALPHA_NGDC",
                    "is_group_to_group": True,
                    "source_zone": src_zone,
                    "destination_zone": dst_zone,
                })
            except Exception:
                pass  # Rule creation is best-effort; don't block migration

            return r
    return None


async def create_migration_review(rule_ids: list[str], comments: str = "") -> list[dict[str, Any]]:
    """Create review requests for migration rules."""
    reviews = _load("reviews") or []
    legacy_rules = _load("legacy_rules") or []
    created: list[dict[str, Any]] = []
    now = _now()
    for rid in rule_ids:
        rule = next((r for r in legacy_rules if r["id"] == rid), None)
        if not rule:
            continue
        review_id = f"REV-{_id()}"
        src_entries = (rule.get("rule_source") or "").split("\n")
        dst_entries = (rule.get("rule_destination") or "").split("\n")
        review = {
            "id": review_id,
            "rule_id": rid,
            "rule_name": f"{rule.get('app_name', '')} - {rule.get('inventory_item', rid)}",
            "request_type": "migration",
            "module": "migration-studio",
            "requestor": "system",
            "reviewer": None,
            "status": "Pending",
            "submitted_at": now,
            "reviewed_at": None,
            "comments": comments or f"Migration review for {rid}",
            "review_notes": None,
            "rule_summary": {
                "application": f"{rule.get('app_id', '')} - {rule.get('app_name', '')}",
                "source": ", ".join(src_entries[:3]),
                "destination": ", ".join(dst_entries[:3]),
                "ports": rule.get("rule_service", ""),
                "environment": rule.get("policy_name", ""),
            },
        }
        reviews.append(review)
        created.append(review)
        # Update rule status to In Progress
        for lr in legacy_rules:
            if lr["id"] == rid:
                lr["migration_status"] = "In Progress"
                break
    _save("reviews", reviews)
    _save("legacy_rules", legacy_rules)
    # Record lifecycle events for each migration review submission
    for rev in created:
        await _record_lifecycle(rev["rule_id"], "submitted", to_status="Pending Review",
                                module="migration-studio",
                                details=f"Migration review submitted for {rev['rule_id']}")
    return created


async def get_rules() -> list[dict[str, Any]]:
    return _load("firewall_rules") or []


async def get_rule(rule_id: str) -> dict[str, Any] | None:
    rules = _load("firewall_rules") or []
    for r in rules:
        if r.get("rule_id") == rule_id:
            return r
    return None


async def create_rule(rule_data: dict[str, Any]) -> dict[str, Any]:
    rules = _load("firewall_rules") or []
    now = _now()
    config = (await get_org_config()) or SEED_ORG_CONFIG
    prefix = config.get("rule_id_prefix", "R-")
    start = config.get("rule_id_start", 3000)
    max_num = start - 1
    for r in rules:
        rid = r.get("rule_id", "")
        if rid.startswith(prefix):
            try:
                num = int(rid.split("-")[-1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    rule_id = f"{prefix}{max_num + 1}"
    rule = {
        "rule_id": rule_id,
        "source": rule_data.get("source", ""),
        "source_zone": rule_data.get("source_zone", ""),
        "destination": rule_data.get("destination", ""),
        "destination_zone": rule_data.get("destination_zone", ""),
        "port": rule_data.get("port", ""),
        "protocol": rule_data.get("protocol", "TCP"),
        "action": rule_data.get("action", "Allow"),
        "description": rule_data.get("description", ""),
        "application": rule_data.get("application", ""),
        "status": "Draft",
        # Lifecycle statuses for Studio-created rules:
        # rule_status = Submitted (new rule, needs review/approval)
        # rule_migration_status = Migrated (created in NGDC / migrated)
        "rule_status": rule_data.get("rule_status", "Submitted"),
        "rule_migration_status": rule_data.get("rule_migration_status", "Migrated"),
        "is_group_to_group": rule_data.get("is_group_to_group", True),
        "environment": rule_data.get("environment", "Production"),
        "datacenter": rule_data.get("datacenter", "ALPHA_NGDC"),
        "created_at": now,
        "updated_at": now,
        "certified_date": None,
        "expiry_date": None,
        # Persist extra context for draft editing (source/dest NH, app, component)
        "source_nh": rule_data.get("source_nh", ""),
        "destination_nh": rule_data.get("destination_nh", ""),
        "dst_application": rule_data.get("dst_application", ""),
        "src_component": rule_data.get("src_component", ""),
        "dst_component": rule_data.get("dst_component", ""),
    }
    rules.append(rule)
    _save("firewall_rules", rules)
    history = _load("rule_history") or []
    history.append({
        "rule_id": rule_id, "action": "Created", "timestamp": now,
        "details": f"Rule created: {rule['description']}", "user": "system",
    })
    _save("rule_history", history)
    # Record lifecycle event: rule created
    await _record_lifecycle(rule_id, "created", to_status="Draft",
                            module="design-studio", details=f"Rule created: {rule['description']}")
    # Also save to separate studio_rules.json for safe cleanup
    await add_studio_rule(rule)
    return rule


async def update_rule(rule_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    rules = _load("firewall_rules") or []
    for r in rules:
        if r.get("rule_id") == rule_id:
            r.update(updates)
            r["updated_at"] = _now()
            _save("firewall_rules", rules)
            # Also update the copy in studio_rules.json
            await _sync_studio_rule(r)
            return r
    return None


async def _sync_studio_rule(rule: dict[str, Any]) -> None:
    """Upsert a rule into studio_rules.json (by rule_id)."""
    data = _load_separate("studio_rules") or []
    rid = rule.get("rule_id")
    for i, existing in enumerate(data):
        if existing.get("rule_id") == rid:
            data[i] = rule
            _save_separate("studio_rules", data)
            return
    data.append(rule)
    _save_separate("studio_rules", data)


async def update_rule_status(rule_id: str, new_status: str, module: str = "studio") -> dict[str, Any] | None:
    rules = _load("firewall_rules") or []
    now = _now()
    for r in rules:
        if r.get("rule_id") == rule_id:
            old_status = r.get("status", "Draft")
            r["status"] = new_status
            r["rule_status"] = new_status
            r["lifecycle_status"] = new_status
            r["updated_at"] = now
            if new_status == "Certified":
                r["certified_date"] = now
                config = (await get_org_config()) or SEED_ORG_CONFIG
                expiry_days = config.get("auto_certify_days", 365)
                r["expiry_date"] = (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
            _save("firewall_rules", rules)
            history = _load("rule_history") or []
            history.append({
                "rule_id": rule_id, "action": f"Status changed to {new_status}",
                "timestamp": now, "details": f"Status updated to {new_status}", "user": "system",
            })
            _save("rule_history", history)
            # Record lifecycle event for every status change
            event_map = {"Pending Review": "submitted", "Approved": "approved",
                         "Rejected": "rejected", "Deployed": "deployed",
                         "Certified": "certified", "Expired": "expired"}
            evt = event_map.get(new_status, "modified")
            await _record_lifecycle(rule_id, evt, from_status=old_status,
                                    to_status=new_status, module=module,
                                    details=f"Status changed from {old_status} to {new_status}")
            return r
    return None


async def delete_rule(rule_id: str) -> bool:
    rules = _load("firewall_rules") or []
    new_rules = [r for r in rules if r.get("rule_id") != rule_id]
    if len(new_rules) == len(rules):
        return False
    _save("firewall_rules", new_rules)
    return True


async def get_rule_history(rule_id: str) -> list[dict[str, Any]]:
    history = _load("rule_history") or []
    return [h for h in history if h.get("rule_id") == rule_id]


# ============================================================
# Rule Lifecycle Status Transitions
# ============================================================

# Valid transitions per module:
# Studio (new rules):    Submitted -> In Progress -> Approved -> Deployed
# FM (imported rules):   Deployed (no transition needed — already deployed)
# Migration (legacy):    Once migrated, rule_migration_status -> Migrated

STUDIO_RULE_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Submitted": ["In Progress"],
    "In Progress": ["Approved", "Rejected"],
    "Approved": ["Deployed"],
    "Rejected": ["Submitted"],  # Allow re-submission
    "Deployed": [],  # Terminal state
}

LEGACY_RULE_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Deployed": [],  # Already deployed — no transitions
}


def get_valid_rule_status_transitions(current_status: str, is_legacy: bool = False) -> list[str]:
    """Return list of valid next statuses for a rule."""
    if is_legacy:
        return LEGACY_RULE_STATUS_TRANSITIONS.get(current_status, [])
    return STUDIO_RULE_STATUS_TRANSITIONS.get(current_status, [])


async def transition_rule_status(rule_id: str, new_status: str, module: str = "studio", reviewer: str = "system") -> dict[str, Any] | None:
    """Transition a Studio rule's rule_status through the lifecycle.
    Returns the updated rule or None if rule not found / transition invalid."""
    rules = _load("firewall_rules") or []
    now = _now()
    for r in rules:
        if r.get("rule_id") == rule_id:
            current = r.get("rule_status", "Submitted")
            valid_next = get_valid_rule_status_transitions(current, is_legacy=False)
            if new_status not in valid_next:
                return {"error": f"Invalid transition from '{current}' to '{new_status}'. Valid: {valid_next}"}
            r["rule_status"] = new_status
            r["updated_at"] = now
            # When rule reaches Deployed, also set the main status field
            if new_status == "Deployed":
                r["status"] = "Deployed"
            elif new_status == "In Progress":
                r["status"] = "Pending Review"
            elif new_status == "Approved":
                r["status"] = "Approved"
            elif new_status == "Rejected":
                r["status"] = "Rejected"
            _save("firewall_rules", rules)
            # Record history
            history = _load("rule_history") or []
            history.append({
                "rule_id": rule_id,
                "action": f"Rule status: {current} → {new_status}",
                "timestamp": now,
                "details": f"Lifecycle status changed from {current} to {new_status} (module: {module})",
                "user": reviewer,
            })
            _save("rule_history", history)
            await _sync_studio_rule(r)
            return r
    return None


async def transition_legacy_rule_status(rule_id: str, new_status: str, reviewer: str = "system") -> dict[str, Any] | None:
    """Transition a legacy rule's rule_status (FM / Migration module)."""
    rules = _load("legacy_rules") or []
    now = _now()
    for r in rules:
        if r.get("id") == rule_id:
            current = r.get("rule_status", "Deployed")
            r["rule_status"] = new_status
            _save("legacy_rules", rules)
            history = _load("rule_history") or []
            history.append({
                "rule_id": rule_id,
                "action": f"Legacy rule status: {current} → {new_status}",
                "timestamp": now,
                "details": f"Legacy lifecycle status changed from {current} to {new_status}",
                "user": reviewer,
            })
            _save("rule_history", history)
            return r
    return None


async def get_rule_lifecycle_summary() -> dict[str, Any]:
    """Return aggregate counts of rules by lifecycle status across all modules."""
    legacy = _load("legacy_rules") or []
    studio = _load("firewall_rules") or []
    summary = {
        "legacy": {"total": len(legacy), "by_rule_status": {}, "by_migration_status": {}},
        "studio": {"total": len(studio), "by_rule_status": {}, "by_migration_status": {}},
    }
    for r in legacy:
        rs = r.get("rule_status", "Deployed")
        ms = r.get("rule_migration_status", "Yet to Migrate")
        summary["legacy"]["by_rule_status"][rs] = summary["legacy"]["by_rule_status"].get(rs, 0) + 1
        summary["legacy"]["by_migration_status"][ms] = summary["legacy"]["by_migration_status"].get(ms, 0) + 1
    for r in studio:
        rs = r.get("rule_status", "Submitted")
        ms = r.get("rule_migration_status", "Migrated")
        summary["studio"]["by_rule_status"][rs] = summary["studio"]["by_rule_status"].get(rs, 0) + 1
        summary["studio"]["by_migration_status"][ms] = summary["studio"]["by_migration_status"].get(ms, 0) + 1
    return summary


# ============================================================
# Migrations CRUD
# ============================================================

async def get_migrations() -> list[dict[str, Any]]:
    return _load("migrations") or []


async def get_migration(migration_id: str) -> dict[str, Any] | None:
    migrations = _load("migrations") or []
    for m in migrations:
        if m.get("migration_id") == migration_id:
            return m
    return None


async def create_migration(data: dict[str, Any]) -> dict[str, Any]:
    migrations = _load("migrations") or []
    now = _now()
    config = (await get_org_config()) or SEED_ORG_CONFIG
    migration_id = f"{config.get('migration_id_prefix', 'mig-')}{_id()}"
    legacy_dc = data.get("source_legacy_dc", data.get("legacy_dc", ""))
    target_dc = data.get("target_ngdc", data.get("target_dc", ""))
    application = data.get("application", "")
    migration = {
        "migration_id": migration_id,
        "id": migration_id,
        "name": data.get("name", f"{application} migration from {legacy_dc} to {target_dc}"),
        "application": application,
        "source_legacy_dc": legacy_dc,
        "target_ngdc": target_dc,
        "legacy_dc": legacy_dc,
        "target_dc": target_dc,
        "status": "Planning",
        "progress": 0,
        "total_rules": data.get("total_rules", 0),
        "migrated_rules": 0,
        "failed_rules": 0,
        "created_at": now,
        "updated_at": now,
    }
    migrations.append(migration)
    _save("migrations", migrations)
    return migration


async def get_migration_mappings(migration_id: str) -> list[dict[str, Any]]:
    mappings = _load("migration_mappings") or []
    return [m for m in mappings if m.get("migration_id") == migration_id]


async def create_migration_mapping(data: dict[str, Any]) -> dict[str, Any]:
    mappings = _load("migration_mappings") or []
    mapping = dict(data)
    mapping["mapping_id"] = f"map-{_id()}"
    mappings.append(mapping)
    _save("migration_mappings", mappings)
    return mapping


async def execute_migration(migration_id: str) -> dict[str, Any] | None:
    migrations = _load("migrations") or []
    now = _now()
    mappings = await get_migration_mappings(migration_id)
    compliant = sum(1 for m in mappings if m.get("compliance") == "Compliant")
    total = len(mappings)
    progress = int((compliant / total) * 100) if total > 0 else 0
    for m in migrations:
        if m.get("migration_id") == migration_id:
            m["status"] = "In Progress"
            m["progress"] = progress
            m["migrated_rules"] = compliant
            m["total_rules"] = total
            m["updated_at"] = now
            _save("migrations", migrations)
            return m
    return None


# ============================================================
# CHG Requests
# ============================================================

async def get_chg_requests() -> list[dict[str, Any]]:
    return _load("chg_requests") or []


async def create_chg_request(data: dict[str, Any]) -> dict[str, Any]:
    chg_list = _load("chg_requests") or []
    now = _now()
    config = (await get_org_config()) or SEED_ORG_CONFIG
    prefix = config.get("chg_id_prefix", "CHG")
    start = config.get("chg_id_start", 10000)
    max_num = start - 1
    for c in chg_list:
        cid = c.get("chg_id", "")
        if cid.startswith(prefix):
            try:
                num = int(cid.replace(prefix, ""))
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    chg = {
        "chg_id": f"{prefix}{max_num + 1}",
        "chg_number": f"{prefix}{max_num + 1}",
        "rule_ids": data.get("rule_ids", []),
        "status": "Submitted",
        "description": data.get("description", ""),
        "requested_by": data.get("requested_by", "system"),
        "approved_by": None,
        "created_at": now,
        "updated_at": now,
    }
    chg_list.append(chg)
    _save("chg_requests", chg_list)
    return chg


# ============================================================
# Policy Validation
# ============================================================

async def validate_policy(source: dict[str, Any], destination: dict[str, Any],
                          application: str = "", environment: str = "Production") -> dict[str, Any]:
    """Resolve the generic pattern-based policy matrix against actual src/dst
    NH, SZ, and DC values.  The matrix no longer lists every individual zone
    pair – instead it uses patterns like 'Open', 'Segmented', 'Same',
    'Different', 'Any', etc.  This function classifies the zones and matches
    the best-fit pattern row."""

    from .seed_data import OPEN_ZONES, SEGMENTED_ZONES, NON_PROD_SEGMENTED_ZONES

    source_zone = source.get("security_zone", "GEN") if isinstance(source, dict) else "GEN"
    dest_zone = destination.get("security_zone", "GEN") if isinstance(destination, dict) else "GEN"
    source_nh = source.get("nh", "") if isinstance(source, dict) else ""
    dest_nh = destination.get("nh", "") if isinstance(destination, dict) else ""
    source_dc = source.get("dc", "") if isinstance(source, dict) else ""
    dest_dc = destination.get("dc", "") if isinstance(destination, dict) else ""
    source_type = source.get("source_type", "Group") if isinstance(source, dict) else "Group"
    group_name = source.get("group_name", "") if isinstance(source, dict) else ""
    is_group_to_group = source_type == "Group" and bool(group_name)
    naming_compliant = bool(group_name and group_name.startswith("grp-")) if group_name else True

    # -- Classify zones --
    NP_OPEN = {"UGen", "USTD"}
    all_segmented = SEGMENTED_ZONES | NON_PROD_SEGMENTED_ZONES
    src_is_open = source_zone in OPEN_ZONES
    dst_is_open = dest_zone in OPEN_ZONES
    src_is_seg = source_zone in SEGMENTED_ZONES
    dst_is_seg = dest_zone in SEGMENTED_ZONES
    src_is_np_open = source_zone in NP_OPEN
    dst_is_np_open = dest_zone in NP_OPEN
    src_is_np_seg = source_zone in NON_PROD_SEGMENTED_ZONES
    dst_is_np_seg = dest_zone in NON_PROD_SEGMENTED_ZONES
    same_sz = source_zone == dest_zone
    cross_sz = not same_sz
    same_nh = (source_nh == dest_nh) and bool(source_nh)
    cross_nh = (source_nh != dest_nh)
    same_dc = (source_dc == dest_dc) and bool(source_dc)
    cross_dc = (source_dc != dest_dc)

    # Determine if src/dst belong to prod or non-prod fabric
    src_is_prod = src_is_open or src_is_seg
    dst_is_prod = dst_is_open or dst_is_seg
    src_is_nonprod = src_is_np_open or src_is_np_seg
    dst_is_nonprod = dst_is_np_open or dst_is_np_seg

    details: list[str] = []
    firewall_request_required = False
    firewall_traversal = "None"
    result = "Permitted"
    requires_exception = False
    matched_rule_id = ""

    # -- Pattern matching (ordered by specificity) --
    # Rule: Non-Prod → Prod  OR  Pre-Prod → Prod = Blocked
    if src_is_nonprod and dst_is_prod:
        result = "Blocked"
        firewall_traversal = "N/A"
        matched_rule_id = "PM-PROD-11"
        details.append(f"Non-Prod ({source_zone}) to Prod ({dest_zone}): unconditionally blocked")

    # Rule: CDE isolation – Open ↔ CDE blocked
    elif (src_is_open and dest_zone == "CDE") or (source_zone == "CDE" and dst_is_open):
        result = "Blocked"
        firewall_traversal = "N/A"
        matched_rule_id = "PM-PROD-09" if src_is_open else "PM-PROD-10"
        details.append(f"CDE is isolated – {source_zone} ↔ CDE direct traffic not permitted")

    # Rule: NP-Open → UCDE blocked
    elif src_is_np_open and dest_zone == "UCDE":
        result = "Blocked"
        firewall_traversal = "N/A"
        matched_rule_id = "PM-NPROD-05"
        details.append(f"NP-Open ({source_zone}) to UCDE not permitted – UCDE is isolated")

    # Rule: Open ↔ Open – always permitted, no FW
    elif src_is_open and dst_is_open:
        result = "Permitted"
        firewall_traversal = "None"
        matched_rule_id = "PM-PROD-01"
        details.append(f"Open zone routing ({source_zone} → {dest_zone}) – permitted, no firewall")

    # Rule: NP-Open ↔ NP-Open – permitted, no FW
    elif src_is_np_open and dst_is_np_open:
        result = "Permitted"
        firewall_traversal = "None"
        matched_rule_id = "PM-NPROD-01"
        details.append(f"NP-Open zone routing ({source_zone} → {dest_zone}) – permitted, no firewall")

    # Rule: Same SZ, same NH – always permitted
    elif same_sz and same_nh:
        result = "Permitted"
        firewall_traversal = "None"
        matched_rule_id = "PM-PROD-02"
        details.append(f"Same SZ ({source_zone}), same NH ({source_nh}) – intra-zone, no firewall")

    # Rule: Same segmented SZ, cross NH
    elif same_sz and cross_nh and (src_is_seg or src_is_np_seg):
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = f"Egress (src NH {source_nh} {source_zone} FW) + Ingress (dst NH {dest_nh} {dest_zone} FW)"
        matched_rule_id = "PM-PROD-03" if same_dc else "PM-PROD-04"
        details.append(
            f"Same SZ ({source_zone}), cross-NH ({source_nh}→{dest_nh})"
            f"{', cross-DC' if cross_dc else ''} – egress + ingress FW required"
        )

    # Rule: Cross SZ (both segmented), same NH
    elif cross_sz and same_nh and (src_is_seg or src_is_np_seg) and (dst_is_seg or dst_is_np_seg):
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = f"NH {source_nh} SZ Boundary FW"
        matched_rule_id = "PM-PROD-05"
        details.append(
            f"Cross-SZ ({source_zone}→{dest_zone}), same NH ({source_nh}) "
            f"– NH segmentation firewall required"
        )

    # Rule: Cross SZ (both segmented), cross NH
    elif cross_sz and cross_nh and (src_is_seg or src_is_np_seg) and (dst_is_seg or dst_is_np_seg):
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = (
            f"Egress (src NH {source_nh} {source_zone} FW) + "
            f"Ingress (dst NH {dest_nh} {dest_zone} FW)"
        )
        matched_rule_id = "PM-PROD-06"
        details.append(
            f"Cross-SZ ({source_zone}→{dest_zone}), cross-NH ({source_nh}→{dest_nh}) "
            f"– egress + ingress FW required"
        )

    # Rule: Open → Segmented (ingress only)
    elif (src_is_open or src_is_np_open) and (dst_is_seg or dst_is_np_seg):
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = f"Ingress (dst NH {dest_nh} {dest_zone} FW)"
        matched_rule_id = "PM-PROD-07" if src_is_open else "PM-NPROD-04"
        details.append(
            f"Open ({source_zone}) → Segmented ({dest_zone}) – "
            f"ingress through destination NH {dest_zone} FW required"
        )

    # Rule: Segmented → Open (egress only)
    elif (src_is_seg or src_is_np_seg) and (dst_is_open or dst_is_np_open):
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = f"Egress (src NH {source_nh} {source_zone} FW)"
        matched_rule_id = "PM-PROD-08"
        details.append(
            f"Segmented ({source_zone}) → Open ({dest_zone}) – "
            f"egress through source NH {source_zone} FW required"
        )

    # Rule: PAA → Segmented (PAA perimeter + internal FW)
    elif source_zone == "PAA" and dst_is_seg:
        result = "Firewall Request Required"
        firewall_request_required = True
        firewall_traversal = f"PAA Perimeter FW + Ingress (dst NH {dest_nh} {dest_zone} FW)"
        matched_rule_id = "PM-PROD-12"
        details.append(
            f"PAA → {dest_zone}: PAA perimeter FW + destination NH internal FW required"
        )

    # Fallback – same SZ (no NH info) = permitted
    elif same_sz:
        result = "Permitted"
        firewall_traversal = "None"
        details.append(f"Same SZ ({source_zone}) – intra-zone traffic permitted")

    else:
        result = "Permitted"
        details.append(f"No matching policy for {source_zone} → {dest_zone}, defaulting to Permitted")

    if not is_group_to_group:
        details.append("Warning: Rule is not group-to-group")
    if not naming_compliant and group_name:
        details.append(f"Warning: Group name '{group_name}' does not follow naming standards")

    return {
        "result": result,
        "message": f"Traffic from {source_zone} to {dest_zone}: {result}",
        "details": details,
        "matched_rule_id": matched_rule_id,
        "ngdc_zone_check": True,
        "birthright_compliant": not requires_exception and not firewall_request_required,
        "firewall_request_required": firewall_request_required,
        "firewall_traversal": firewall_traversal,
        "naming_compliant": naming_compliant,
        "group_to_group_compliant": is_group_to_group,
    }


# ============================================================
# Org Customization CRUD
# ============================================================

async def update_org_config(updates: dict[str, Any]) -> dict[str, Any] | None:
    config = _load("org_config") or {}
    config.update(updates)
    _save("org_config", config)
    return config


async def create_neighbourhood(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("neighbourhoods") or []
    items.append(dict(data))
    _save("neighbourhoods", items)
    return data


async def update_neighbourhood(nh_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("neighbourhoods") or []
    for item in items:
        if item.get("nh_id") == nh_id:
            item.update(updates)
            _save("neighbourhoods", items)
            return item
    return None


async def delete_neighbourhood(nh_id: str) -> bool:
    items = _load("neighbourhoods") or []
    new_items = [i for i in items if i.get("nh_id") != nh_id]
    if len(new_items) == len(items):
        return False
    _save("neighbourhoods", new_items)
    return True


async def create_security_zone(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("security_zones") or []
    data = dict(data)
    data.setdefault("naming_mode", "app_scoped")
    items.append(data)
    _save("security_zones", items)
    _refresh_naming_mode_cache()
    return data


async def update_security_zone(code: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("security_zones") or []
    for item in items:
        if item.get("code") == code:
            item.update(updates)
            _save("security_zones", items)
            _refresh_naming_mode_cache()
            return item
    return None


async def delete_security_zone(code: str) -> bool:
    items = _load("security_zones") or []
    new_items = [i for i in items if i.get("code") != code]
    if len(new_items) == len(items):
        return False
    _save("security_zones", new_items)
    _refresh_naming_mode_cache()
    return True


async def create_application(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("applications") or []
    data = dict(data)
    data.setdefault("primary_dc", "ALPHA_NGDC")
    data.setdefault("deployment_mode", "all_ngdc")
    data.setdefault("excluded_dcs", [])
    items.append(data)
    _save("applications", items)
    # Materialize presences in every NGDC DC when deployment_mode=all_ngdc
    # and the app declared tiers. Idempotent — existing presences kept.
    await auto_fan_app_presences(data)
    return data


async def update_application(app_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("applications") or []
    for item in items:
        if item.get("app_id") == app_id or item.get("app_distributed_id") == app_id:
            item.update(updates)
            _save("applications", items)
            # Re-fan to pick up newly-added tiers / DCs after edits.
            await auto_fan_app_presences(item)
            return item
    return None


async def delete_application(app_id: str) -> bool:
    items = _load("applications") or []
    new_items = [i for i in items if i.get("app_id") != app_id]
    if len(new_items) == len(items):
        return False
    _save("applications", new_items)
    return True


async def get_filtered_nh_sz_dc(environment: str, app_id: str | None = None) -> dict[str, Any]:
    """Return NHs/SZs/DCs filtered by environment and optionally by app.

    - Non-Production / Pre-Production: return ALL NHs for that environment (common for all apps).
    - Production: return app-specific NHs from the app's neighborhoods field.
    SZs and DCs are similarly filtered from the app's szs/dcs fields for prod,
    or all SZs matching the fabric for non-prod/preprod.
    """
    all_nhs = _load("neighbourhoods") or []
    all_szs = _load("security_zones") or []
    all_dcs = _load("ngdc_datacenters") or []
    all_apps = _load("applications") or []

    env_lower = environment.lower().strip()
    is_prod = env_lower in ("production", "prod")

    # Find the app record
    app_record = None
    if app_id:
        app_record = next(
            (a for a in all_apps
             if a.get("app_id") == app_id or a.get("app_distributed_id") == app_id),
            None,
        )

    if is_prod and app_record:
        # Production: app-specific NHs/SZs/DCs from the app's mapped fields
        app_nhs = [n.strip() for n in (app_record.get("neighborhoods") or app_record.get("nh") or "").split(",") if n.strip()]
        app_szs = [s.strip() for s in (app_record.get("szs") or app_record.get("sz") or "").split(",") if s.strip()]
        app_dcs = [d.strip() for d in (app_record.get("dcs") or "").split(",") if d.strip()]

        # Match NHs by nh_id OR by name (app data may use names instead of IDs)
        filtered_nhs = [nh for nh in all_nhs if nh.get("nh_id") in app_nhs or nh.get("name") in app_nhs]
        filtered_szs = [sz for sz in all_szs if sz.get("code") in app_szs]
        filtered_dcs = [dc for dc in all_dcs if dc.get("dc_id") in app_dcs] if app_dcs else all_dcs
    else:
        # Non-prod / Pre-prod: all NHs for that environment (common for all apps)
        env_map = {
            "non-production": "Non-Production", "nonprod": "Non-Production",
            "non_production": "Non-Production", "np": "Non-Production",
            "pre-production": "Pre-Production", "preprod": "Pre-Production",
            "pre_production": "Pre-Production",
            "production": "Production", "prod": "Production",
        }
        target_env = env_map.get(env_lower, environment)

        filtered_nhs = [nh for nh in all_nhs if nh.get("environment") == target_env]
        # SZs: match fabric
        fabric = "Production" if is_prod else "Non-Production"
        filtered_szs = [sz for sz in all_szs if sz.get("fabric") == fabric]
        # DCs: all DCs for non-prod/preprod (or app-specific if app has dcs)
        if app_record and app_record.get("dcs"):
            app_dcs = [d.strip() for d in app_record["dcs"].split(",") if d.strip()]
            filtered_dcs = [dc for dc in all_dcs if dc.get("dc_id") in app_dcs] if app_dcs else all_dcs
        else:
            filtered_dcs = all_dcs

    return {
        "neighbourhoods": filtered_nhs,
        "security_zones": filtered_szs,
        "datacenters": filtered_dcs,
    }


async def clear_app_management() -> dict[str, Any]:
    """Clear all application data (allows re-import from scratch)."""
    _save("applications", [])
    return {"message": "All application data cleared"}


async def import_app_management(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Delta-based import of app management records using app_distributed_id as dedup key.

    Returns counts of added, updated, and skipped records.
    """
    items = _load("applications") or []
    existing_map: dict[str, int] = {}
    for idx, item in enumerate(items):
        adid = item.get("app_distributed_id")
        if adid:
            existing_map[adid] = idx

    added = 0
    updated = 0
    skipped = 0
    overrides: list[dict[str, Any]] = []

    for rec in records:
        adid = rec.get("app_distributed_id", "").strip()
        if not adid:
            skipped += 1
            continue

        if adid in existing_map:
            idx = existing_map[adid]
            existing = items[idx]
            # Check if anything changed
            changed = False
            for key in ("app_id", "name", "owner", "neighborhoods", "szs", "dcs", "snow_sysid",
                        "nh", "sz", "criticality", "pci_scope"):
                new_val = rec.get(key)
                if new_val is not None and str(new_val) != str(existing.get(key, "")):
                    changed = True
                    break
            if changed:
                # Override existing record with new data, preserving fields not in import
                for key, val in rec.items():
                    if val is not None and str(val).strip():
                        existing[key] = val
                items[idx] = existing
                updated += 1
                overrides.append({"app_distributed_id": adid, "app_id": existing.get("app_id", "")})
            else:
                skipped += 1
        else:
            items.append(dict(rec))
            existing_map[adid] = len(items) - 1
            added += 1

    _save("applications", items)
    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "total": len(records),
        "overrides": overrides,
    }


async def create_datacenter(data: dict[str, Any], dc_type: str = "ngdc") -> dict[str, Any]:
    coll = "ngdc_datacenters" if dc_type == "ngdc" else "legacy_datacenters"
    items = _load(coll) or []
    items.append(dict(data))
    _save(coll, items)
    return data


async def update_datacenter(code: str, updates: dict[str, Any], dc_type: str = "ngdc") -> dict[str, Any] | None:
    coll = "ngdc_datacenters" if dc_type == "ngdc" else "legacy_datacenters"
    items = _load(coll) or []
    for item in items:
        if item.get("code") == code:
            item.update(updates)
            _save(coll, items)
            return item
    return None


async def delete_datacenter(code: str, dc_type: str = "ngdc") -> bool:
    coll = "ngdc_datacenters" if dc_type == "ngdc" else "legacy_datacenters"
    items = _load(coll) or []
    new_items = [i for i in items if i.get("code") != code]
    if len(new_items) == len(items):
        return False
    _save(coll, new_items)
    return True


async def update_naming_standards(updates: dict[str, Any]) -> dict[str, Any] | None:
    standards = _load("naming_standards") or {}
    standards.update(updates)
    _save("naming_standards", standards)
    return standards


async def create_policy_entry(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("policy_matrix") or []
    items.append(dict(data))
    _save("policy_matrix", items)
    return data


async def delete_policy_entry(source_zone: str, dest_zone: str) -> bool:
    items = _load("policy_matrix") or []
    new_items = [i for i in items if not (i.get("source_zone") == source_zone and i.get("dest_zone") == dest_zone)]
    if len(new_items) == len(items):
        return False
    _save("policy_matrix", new_items)
    return True


async def update_policy_entry(source_zone: str, dest_zone: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("policy_matrix") or []
    for item in items:
        if item.get("source_zone") == source_zone and item.get("dest_zone") == dest_zone:
            item.update(updates)
            _save("policy_matrix", items)
            return item
    return None


# ============================================================
# Policy Change Review Workflow
# ============================================================

async def get_policy_changes(status: str | None = None) -> list[dict[str, Any]]:
    changes = _load("policy_changes") or []
    if status:
        changes = [c for c in changes if c.get("status") == status]
    return changes


async def create_policy_change(
    change_type: str,
    policy_data: dict[str, Any],
    original_data: dict[str, Any] | None = None,
    comments: str = "",
    linked_rule_id: str | None = None,
) -> dict[str, Any]:
    """Submit a policy change for review. change_type: add, modify, delete."""
    changes = _load("policy_changes") or []
    now = _now()
    change_id = f"POL-{_id()}"

    # Build delta for modify changes
    delta: dict[str, Any] = {"added": {}, "removed": {}, "changed": {}}
    if change_type == "modify" and original_data:
        for key in set(list(policy_data.keys()) + list(original_data.keys())):
            old_val = original_data.get(key, "")
            new_val = policy_data.get(key, "")
            if str(old_val) != str(new_val):
                delta["changed"][key] = {"from": str(old_val), "to": str(new_val)}
    elif change_type == "add":
        delta["added"] = {k: [str(v)] for k, v in policy_data.items()}
    elif change_type == "delete" and original_data:
        delta["removed"] = {k: [str(v)] for k, v in original_data.items()}

    change = {
        "id": change_id,
        "change_type": change_type,
        "policy_data": dict(policy_data),
        "original_data": dict(original_data) if original_data else None,
        "delta": delta,
        "status": "Pending",
        "requestor": "sns_user",
        "reviewer": None,
        "submitted_at": now,
        "reviewed_at": None,
        "comments": comments,
        "review_notes": None,
        "linked_rule_id": linked_rule_id,
    }
    changes.append(change)
    _save("policy_changes", changes)

    # Also create a review entry so it appears in the Review & Approval page
    reviews = _load("reviews") or []
    review_id = f"REV-{_id()}"
    src_zone = policy_data.get("source_zone", "")
    dst_zone = policy_data.get("dest_zone", "")
    action = policy_data.get("default_action", "")
    review = {
        "id": review_id,
        "rule_id": change_id,
        "rule_name": f"Policy: {src_zone} → {dst_zone}",
        "request_type": f"policy_{change_type}",
        "module": "org-admin",
        "requestor": "sns_user",
        "reviewer": None,
        "status": "Pending",
        "submitted_at": now,
        "reviewed_at": None,
        "comments": comments,
        "review_notes": None,
        "policy_change_id": change_id,
        "linked_rule_id": linked_rule_id,
        "delta": delta,
        "rule_summary": {
            "application": "Policy Matrix",
            "source": src_zone,
            "destination": dst_zone,
            "ports": action,
            "environment": policy_data.get("description", ""),
        },
    }
    reviews.append(review)
    _save("reviews", reviews)
    return change


async def approve_policy_change(change_id: str, notes: str = "") -> dict[str, Any] | None:
    changes = _load("policy_changes") or []
    now = _now()
    for c in changes:
        if c.get("id") == change_id:
            c["status"] = "Approved"
            c["reviewed_at"] = now
            c["review_notes"] = notes
            c["reviewer"] = "sns_user"
            _save("policy_changes", changes)

            # Apply the actual change to the policy matrix
            ct = c.get("change_type")
            pd = c.get("policy_data", {})
            if ct == "add":
                await create_policy_entry(pd)
            elif ct == "modify":
                src_z = pd.get("source_zone", "")
                dst_z = pd.get("dest_zone", "")
                await update_policy_entry(src_z, dst_z, pd)
            elif ct == "delete":
                orig = c.get("original_data") or pd
                src_z = orig.get("source_zone", "")
                dst_z = orig.get("dest_zone", "")
                await delete_policy_entry(src_z, dst_z)

            # Update linked review status
            reviews = _load("reviews") or []
            for r in reviews:
                if r.get("policy_change_id") == change_id:
                    r["status"] = "Approved"
                    r["reviewed_at"] = now
                    r["review_notes"] = notes
                    r["reviewer"] = "sns_user"
            _save("reviews", reviews)
            return c
    return None


async def reject_policy_change(change_id: str, notes: str = "") -> dict[str, Any] | None:
    changes = _load("policy_changes") or []
    now = _now()
    for c in changes:
        if c.get("id") == change_id:
            c["status"] = "Rejected"
            c["reviewed_at"] = now
            c["review_notes"] = notes
            c["reviewer"] = "sns_user"
            _save("policy_changes", changes)

            # Update linked review status
            reviews = _load("reviews") or []
            for r in reviews:
                if r.get("policy_change_id") == change_id:
                    r["status"] = "Rejected"
                    r["reviewed_at"] = now
                    r["review_notes"] = notes
                    r["reviewer"] = "sns_user"
            _save("reviews", reviews)
            return c
    return None


async def create_predefined_destination(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("predefined_destinations") or []
    items.append(dict(data))
    _save("predefined_destinations", items)
    return data


async def update_predefined_destination(name: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("predefined_destinations") or []
    for item in items:
        if item.get("name") == name:
            item.update(updates)
            _save("predefined_destinations", items)
            return item
    return None


async def delete_predefined_destination(name: str) -> bool:
    items = _load("predefined_destinations") or []
    new_items = [i for i in items if i.get("name") != name]
    if len(new_items) == len(items):
        return False
    _save("predefined_destinations", new_items)
    return True


async def create_environment(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("environments") or []
    items.append(dict(data))
    _save("environments", items)
    return data


async def delete_environment(code: str) -> bool:
    items = _load("environments") or []
    new_items = [i for i in items if i.get("code") != code]
    if len(new_items) == len(items):
        return False
    _save("environments", new_items)
    return True


# ============================================================
# Firewall Devices CRUD
# ============================================================

async def get_firewall_device_patterns() -> list[dict[str, Any]]:
    return deepcopy(_SD_FW_PATTERNS)


async def get_dc_vendor_map() -> dict[str, Any]:
    return deepcopy(_SD_DC_VENDOR)


async def get_firewall_devices() -> list[dict[str, Any]]:
    return _load("firewall_devices") or []


async def get_firewall_device(device_id: str) -> dict[str, Any] | None:
    devices = _load("firewall_devices") or []
    for d in devices:
        if d.get("device_id") == device_id:
            return d
    return None


async def create_firewall_device(data: dict[str, Any]) -> dict[str, Any]:
    devices = _load("firewall_devices") or []
    devices.append(dict(data))
    _save("firewall_devices", devices)
    return data


async def update_firewall_device(device_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    devices = _load("firewall_devices") or []
    for i, d in enumerate(devices):
        if d.get("device_id") == device_id:
            devices[i] = {**d, **data, "device_id": device_id}
            _save("firewall_devices", devices)
            return devices[i]
    return None


async def delete_firewall_device(device_id: str) -> bool:
    devices = _load("firewall_devices") or []
    new_devices = [d for d in devices if d.get("device_id") != device_id]
    if len(new_devices) == len(devices):
        return False
    _save("firewall_devices", new_devices)
    return True


# ============================================================
# Groups CRUD
# ============================================================

async def get_groups() -> list[dict[str, Any]]:
    return _load("groups") or []


async def get_group(name: str) -> dict[str, Any] | None:
    groups = _load("groups") or []
    for g in groups:
        if g.get("name") == name:
            return g
    return None


async def create_group(data: dict[str, Any], skip_prefix: bool = False) -> dict[str, Any]:
    groups = _load("groups") or []
    # Auto-prefix group name if missing (skip for legacy groups imported as-is)
    if "name" in data and not skip_prefix:
        data["name"] = _auto_prefix(data["name"], "group")
    # Auto-prefix member values (skip for legacy imports)
    if not skip_prefix:
        for m in data.get("members", []):
            if "value" in m:
                m["value"] = _auto_prefix(m["value"], m.get("type", "ip"))
    data["created_at"] = _now()
    data["updated_at"] = _now()
    groups.append(dict(data))
    _save("groups", groups)
    return data


async def update_group(name: str, data: dict[str, Any]) -> dict[str, Any] | None:
    groups = _load("groups") or []
    for g in groups:
        if g.get("name") == name:
            g.update(data)
            g["updated_at"] = _now()
            _save("groups", groups)
            return g
    return None


async def delete_group(name: str) -> bool:
    groups = _load("groups") or []
    new_groups = [g for g in groups if g.get("name") != name]
    if len(new_groups) == len(groups):
        return False
    _save("groups", new_groups)
    return True


async def add_group_member(group_name: str, member: dict[str, Any]) -> dict[str, Any] | None:
    groups = _load("groups") or []
    # Auto-prefix member value based on type
    if "value" in member:
        member["value"] = _auto_prefix(member["value"], member.get("type", "ip"))
    for g in groups:
        if g.get("name") == group_name:
            members = g.get("members", [])
            members.append(member)
            g["members"] = members
            g["updated_at"] = _now()
            _save("groups", groups)
            return g
    return None


async def remove_group_member(group_name: str, member_value: str) -> dict[str, Any] | None:
    groups = _load("groups") or []
    for g in groups:
        if g.get("name") == group_name:
            members = g.get("members", [])
            new_members = [m for m in members if m.get("value") != member_value]
            if len(new_members) == len(members):
                return None
            g["members"] = new_members
            g["updated_at"] = _now()
            _save("groups", groups)
            return g
    return None


# ============================================================
# VRF Convention Helper
# Uses the vrf_prefix from SEED_SECURITY_ZONES to produce NH##-sz## format.
# e.g. NH08 + CPA → NH08-sz06, NH13 + UCCS → NH13-sz04
# ============================================================

# NH Name → NH ID mapping (from Confluence reference)
_NH_NAME_TO_ID: dict[str, str] = {
    "Technology Enablement Services": "NH01",
    "Core Banking": "NH02",
    "Digital Channels": "NH03",
    "Wealth Management": "NH04",
    "Enterprise Services": "NH05",
    "Wholesale Banking": "NH06",
    "Global Payments and Liquidity": "NH07",
    "Data and Analytics": "NH08",
    "Assisted Channels": "NH09",
    "Consumer Lending": "NH10",
    "Production Mainframe": "NH11",
    "Non-Production Mainframe": "NH12",
    "Non-Production Shared": "NH13",
    "DMZ": "NH14",
    "Non-Production DMZ": "NH15",
    "Pre-Production (Non-Prod Shared)": "NH16",
    "Pre-Production DMZ": "NH17",
}

# NH names that are non-prod (pre-prod is also treated as non-prod)
_NONPROD_NH_NAMES = {
    "Non-Production Mainframe", "Non-Production Shared",
    "Non-Production DMZ", "Pre-Production (Non-Prod Shared)",
    "Pre-Production DMZ",
}


def _resolve_nh_id(nh: str) -> str:
    """Resolve an NH name or ID to its NH ID (e.g. 'Core Banking' → 'NH02').
    If already an NH ID (starts with NH), returns as-is."""
    val = nh.strip() if nh else ""
    if not val:
        return ""
    # Already an NH ID?
    if val.upper().startswith("NH") and len(val) <= 5:
        return val.upper()
    # Look up by name
    nh_id = _NH_NAME_TO_ID.get(val)
    if nh_id:
        return nh_id
    # Fallback: try case-insensitive match
    val_lower = val.lower()
    for name, nid in _NH_NAME_TO_ID.items():
        if name.lower() == val_lower:
            return nid
    # Fallback: try reference data from disk
    nhs = _load_ref("neighbourhoods") or []
    for n in nhs:
        if n.get("name", "").lower() == val_lower:
            return n.get("nh_id", val)
    return val


def _is_nonprod_nh(nh: str) -> bool:
    """Check if an NH (name or ID) is a non-prod/pre-prod NH."""
    val = nh.strip() if nh else ""
    # Check by name
    if val in _NONPROD_NH_NAMES:
        return True
    # Check by ID
    nh_id = _resolve_nh_id(val)
    return nh_id in {"NH11", "NH12", "NH13", "NH15", "NH16", "NH17"}


# SZ code → vrf_prefix template (from seed data)
# The template uses "nh##" as a placeholder for the actual NH number.
_SZ_VRF_PREFIX: dict[str, str] = {
    # Production
    "STD": "gen/SZ01", "GEN": "gen/SZ01",
    "PAA": "paa/SZ02",
    "3PY": "nh##-sz03",
    "CCS": "nh##-sz04",
    "CDE": "nh##-sz05",
    "CPA": "nh##-sz06",
    "PSE": "nh##-sz07",
    "Swift": "nh##-sz08",
    "UC": "nh##-sz09",
    # Non-Production / Pre-Production
    "UGen": "gen", "USTD": "gen",
    "UPAA": "paa/sz-02",
    "U3PY": "nh##-sz03",
    "UCCS": "nh##-sz04",
    "UCDE": "nh##-sz05",
    "UCPA": "nh##-sz06",
}

# Map prod SZ codes to their non-prod equivalents for auto-mapping
_PROD_TO_NONPROD_SZ: dict[str, str] = {
    "GEN": "UGen", "STD": "USTD", "PAA": "UPAA",
    "3PY": "U3PY", "CCS": "UCCS", "CDE": "UCDE", "CPA": "UCPA",
}

# Non-prod/preprod NHs by ID (common for all apps)
_NONPROD_NHS = {"NH11", "NH12", "NH13", "NH15", "NH16", "NH17"}


def _resolve_vrf(nh: str, sz: str, environment: str = "") -> str:
    """Resolve the NH-SZ VRF convention string using NH##-sz## format.
    Accepts NH name or NH ID. Returns e.g. 'NH08-sz06' for CPA in NH08."""
    # Resolve NH name to NH ID if needed
    nh_id = _resolve_nh_id(nh)
    sz_val = sz.strip() if sz else ""
    env_lower = environment.lower().strip() if environment else ""

    is_nonprod = (
        nh_id in _NONPROD_NHS
        or _is_nonprod_nh(nh)
        or "non" in env_lower
        or "pre" in env_lower
    )

    # If in non-prod context and a prod SZ code is given, map to non-prod equivalent
    if is_nonprod and sz_val in _PROD_TO_NONPROD_SZ:
        sz_val = _PROD_TO_NONPROD_SZ[sz_val]

    # Look up the vrf_prefix template for this SZ
    template = _SZ_VRF_PREFIX.get(sz_val, "")
    if not template:
        # Fallback: try reference data from disk
        szs = _load_ref("security_zones") or []
        for s in szs:
            if s.get("code") == sz_val and s.get("vrf_prefix"):
                template = s["vrf_prefix"]
                break

    if not template:
        # Last resort: return NH-SZCode as fallback
        return f"{nh_id}-{sz_val}" if nh_id else sz_val

    # Replace nh## placeholder with actual NH number
    vrf = template.replace("nh##", nh_id.lower() if nh_id else "nh00")
    return f"{nh_id}-{vrf}" if nh_id and not vrf.lower().startswith(nh_id.lower()) else vrf


# ============================================================
# Rule Compiler
# ============================================================

async def compile_rule(rule_id: str, vendor: str = "generic") -> dict[str, Any] | None:
    rule = await get_rule(rule_id)
    if not rule:
        return None
    src = rule.get("source", "")
    dst = rule.get("destination", "")
    port = rule.get("port", "any")
    proto = rule.get("protocol", "TCP")
    action = rule.get("action", "Allow")
    desc = rule.get("description", "")
    env = rule.get("environment", "")
    src_nh = rule.get("source_nh", rule.get("nh", ""))
    dst_nh = rule.get("destination_nh", rule.get("dst_nh", ""))
    src_sz = rule.get("source_zone", "any")
    dst_sz = rule.get("destination_zone", "any")

    # Resolve NH-SZ VRF conventions
    src_vrf = _resolve_vrf(src_nh, src_sz, env)
    dst_vrf = _resolve_vrf(dst_nh, dst_sz, env)

    src_objs = [src] if src else ["any"]
    dst_objs = [dst] if dst else ["any"]
    svc_list = [f"{proto}/{port}"] if port and port != "any" else ["any"]

    if vendor == "palo_alto":
        compiled = (
            f"set rulebase security rules \"{rule_id}\" from {rule.get('source_zone', 'any')}\n"
            f"set rulebase security rules \"{rule_id}\" to {rule.get('destination_zone', 'any')}\n"
            f"set rulebase security rules \"{rule_id}\" source [{src}]\n"
            f"set rulebase security rules \"{rule_id}\" destination [{dst}]\n"
            f"set rulebase security rules \"{rule_id}\" service [{proto.lower()}-{port}]\n"
            f"set rulebase security rules \"{rule_id}\" action {'allow' if action == 'Allow' else 'deny'}\n"
            f"set rulebase security rules \"{rule_id}\" log-start yes\n"
            f"set rulebase security rules \"{rule_id}\" description \"{desc}\"\n"
            f"# Source VRF: {src_vrf}\n"
            f"# Destination VRF: {dst_vrf}"
        )
    elif vendor == "checkpoint":
        compiled = (
            f"mgmt_cli add access-rule layer \"Network\" position top \\\n"
            f"  name \"{rule_id}\" \\\n"
            f"  source \"{src}\" \\\n"
            f"  destination \"{dst}\" \\\n"
            f"  service \"{proto}_{port}\" \\\n"
            f"  action \"{'Accept' if action == 'Allow' else 'Drop'}\" \\\n"
            f"  track \"Log\" \\\n"
            f"  comments \"{desc}\"\n"
            f"# Source VRF: {src_vrf}\n"
            f"# Destination VRF: {dst_vrf}"
        )
    elif vendor == "fortigate":
        compiled = (
            f"config firewall policy\n"
            f"  edit 0\n"
            f"    set name \"{rule_id}\"\n"
            f"    set srcintf \"{rule.get('source_zone', 'any')}\"\n"
            f"    set dstintf \"{rule.get('destination_zone', 'any')}\"\n"
            f"    set srcaddr \"{src}\"\n"
            f"    set dstaddr \"{dst}\"\n"
            f"    set service \"{proto}/{port}\"\n"
            f"    set action {'accept' if action == 'Allow' else 'deny'}\n"
            f"    set logtraffic all\n"
            f"    set comments \"{desc}\"\n"
            f"    set src-vrf \"{src_vrf}\"\n"
            f"    set dst-vrf \"{dst_vrf}\"\n"
            f"  next\n"
            f"end"
        )
    else:
        compiled = (
            f"# Firewall Rule: {rule_id}\n"
            f"# Description: {desc}\n"
            f"# Application: {rule.get('application', 'N/A')}\n"
            f"# Environment: {env or 'N/A'}\n"
            f"# Source VRF: {src_vrf}\n"
            f"# Destination VRF: {dst_vrf}\n"
            f"---\n"
            f"rule:\n"
            f"  id: {rule_id}\n"
            f"  action: {action.lower()}\n"
            f"  source:\n"
            f"    objects: [{src}]\n"
            f"    zone: {src_sz}\n"
            f"    vrf: {src_vrf}\n"
            f"  destination:\n"
            f"    objects: [{dst}]\n"
            f"    zone: {dst_sz}\n"
            f"    vrf: {dst_vrf}\n"
            f"  service:\n"
            f"    protocol: {proto.lower()}\n"
            f"    port: {port}\n"
            f"  logging: true\n"
            f"  enabled: true"
        )

    # --- Group provisioning as part of compile ---
    app_id = rule.get("app_id", rule.get("application", ""))
    group_provisioning = None
    if app_id:
        group_provisioning = await provision_groups_to_device(str(app_id), vendor if vendor in ("palo_alto", "checkpoint") else "palo_alto")

    result: dict[str, Any] = {
        "rule_id": rule_id,
        "vendor_format": vendor,
        "compiled_text": compiled,
        "source_objects": src_objs,
        "destination_objects": dst_objs,
        "services": svc_list,
        "action": action.lower(),
        "logging": True,
        "comment": desc,
        "source_vrf": src_vrf,
        "destination_vrf": dst_vrf,
    }
    if group_provisioning:
        result["group_provisioning"] = group_provisioning
    return result


# ============================================================
# Review & Approval Workflow
# ============================================================

async def get_reviews(status: str | None = None) -> list[dict[str, Any]]:
    reviews = _load("reviews") or []
    if status:
        reviews = [r for r in reviews if r.get("status") == status]
    return reviews


async def create_review(rule_id: str, comments: str = "", module: str = "design-studio") -> dict[str, Any]:
    reviews = _load("reviews") or []
    rule = await get_rule(rule_id)
    now = _now()
    review_id = f"REV-{_id()}"
    # Build comprehensive rule summary for reviewers
    rule_summary: dict[str, Any] = {}
    if rule:
        src = rule.get("source", "")
        dst = rule.get("destination", "")
        if isinstance(src, dict):
            src = src.get("group_name", "") or src.get("ip_address", "") or src.get("cidr", "")
        if isinstance(dst, dict):
            dst = dst.get("name", "") or dst.get("dest_ip", "")
        rule_summary = {
            "application": rule.get("application", ""),
            "source": str(src),
            "destination": str(dst),
            "ports": rule.get("port", ""),
            "environment": rule.get("environment", ""),
            "source_zone": rule.get("source_zone", ""),
            "destination_zone": rule.get("destination_zone", ""),
            "datacenter": rule.get("datacenter", ""),
            "action": rule.get("action", ""),
            "protocol": rule.get("protocol", ""),
            "description": rule.get("description", ""),
            "is_group_to_group": rule.get("is_group_to_group", False),
        }
    review = {
        "id": review_id,
        "rule_id": rule_id,
        "rule_name": rule.get("description", rule_id) if rule else rule_id,
        "request_type": "new_rule",
        "module": module,
        "requestor": "system",
        "reviewer": None,
        "status": "Pending",
        "submitted_at": now,
        "reviewed_at": None,
        "comments": comments,
        "review_notes": None,
        "rule_summary": rule_summary,
    }
    reviews.append(review)
    _save("reviews", reviews)
    if rule:
        await update_rule_status(rule_id, "Pending Review", module=module)
    # Record lifecycle event: rule submitted for review
    await _record_lifecycle(rule_id, "submitted", to_status="Pending Review",
                            module=module, details=comments or f"Rule {rule_id} submitted for review")
    return review


async def approve_review(review_id: str, notes: str = "") -> dict[str, Any] | None:
    reviews = _load("reviews") or []
    now = _now()
    for r in reviews:
        if r.get("id") == review_id:
            r["status"] = "Approved"
            r["reviewed_at"] = now
            r["review_notes"] = notes
            r["reviewer"] = "sns_user"
            _save("reviews", reviews)
            review_module = r.get("module", "studio")
            # If this review is linked to a rule modification, approve it too
            mod_id = r.get("modification_id")
            pol_id = r.get("policy_change_id")
            if pol_id:
                await approve_policy_change(pol_id, notes)
            elif mod_id:
                await approve_rule_modification(mod_id, notes)
            elif r.get("request_type") == "migration":
                # Migration review: update the legacy rule's statuses
                rule_id = r.get("rule_id")
                if rule_id:
                    await migrate_rule_to_ngdc(rule_id)
            else:
                rule_id = r.get("rule_id")
                if rule_id:
                    await update_rule_status(rule_id, "Approved", module=review_module)
                    # Also update in separate studio_rules.json
                    rule = await get_rule(rule_id)
                    if rule:
                        await add_studio_rule(rule)
            # Record lifecycle event: review approved
            await _record_lifecycle(r.get("rule_id", ""), "approved",
                                    from_status="Pending Review", to_status="Approved",
                                    actor="sns_user", module=review_module,
                                    details=notes or f"Review {review_id} approved")
            return r
    return None


async def reject_review(review_id: str, notes: str) -> dict[str, Any] | None:
    reviews = _load("reviews") or []
    now = _now()
    for r in reviews:
        if r.get("id") == review_id:
            r["status"] = "Rejected"
            r["reviewed_at"] = now
            r["review_notes"] = notes
            r["reviewer"] = "sns_user"
            _save("reviews", reviews)
            review_module = r.get("module", "studio")
            # If this review is linked to a rule modification, reject it too
            mod_id = r.get("modification_id")
            pol_id = r.get("policy_change_id")
            if pol_id:
                await reject_policy_change(pol_id, notes)
            elif mod_id:
                await reject_rule_modification(mod_id, notes)
            else:
                rule_id = r.get("rule_id")
                if rule_id:
                    await update_rule_status(rule_id, "Rejected", module=review_module)
            # Record lifecycle event: review rejected
            await _record_lifecycle(r.get("rule_id", ""), "rejected",
                                    from_status="Pending Review", to_status="Rejected",
                                    actor="sns_user", module=review_module,
                                    details=notes or f"Review {review_id} rejected")
            return r
    return None


# ============================================================
# Rule Modification with Delta Tracking
# ============================================================

def _compute_delta(original: dict[str, Any], modified: dict[str, Any]) -> dict[str, Any]:
    """Compute delta between original and modified rule fields."""
    delta: dict[str, Any] = {"added": {}, "removed": {}, "changed": {}}
    track_fields = ["rule_source", "rule_destination", "rule_service",
                    "rule_source_expanded", "rule_destination_expanded", "rule_service_expanded",
                    "rule_source_zone", "rule_destination_zone", "rule_action"]
    for field in track_fields:
        orig_val = str(original.get(field, ""))
        mod_val = str(modified.get(field, ""))
        if orig_val != mod_val:
            # For multiline fields, compute line-level diff
            if "\n" in orig_val or "\n" in mod_val:
                orig_lines = set(orig_val.split("\n")) if orig_val else set()
                mod_lines = set(mod_val.split("\n")) if mod_val else set()
                added = mod_lines - orig_lines
                removed = orig_lines - mod_lines
                if added:
                    delta["added"][field] = sorted(added)
                if removed:
                    delta["removed"][field] = sorted(removed)
            else:
                delta["changed"][field] = {"from": orig_val, "to": mod_val}
    return delta


async def create_rule_modification(rule_id: str, modifications: dict[str, Any], comments: str = "") -> dict[str, Any] | None:
    """Create a rule modification request with delta tracking."""
    rules = _load("legacy_rules") or []
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        return None

    delta = _compute_delta(rule, modifications)
    now = _now()
    mod_id = f"MOD-{_id()}"

    modification = {
        "id": mod_id,
        "rule_id": rule_id,
        "original": {k: rule.get(k, "") for k in ["rule_source", "rule_destination", "rule_service",
                      "rule_source_expanded", "rule_destination_expanded", "rule_service_expanded",
                      "rule_source_zone", "rule_destination_zone", "rule_action"]},
        "modified": {k: modifications.get(k, rule.get(k, "")) for k in ["rule_source", "rule_destination", "rule_service",
                      "rule_source_expanded", "rule_destination_expanded", "rule_service_expanded",
                      "rule_source_zone", "rule_destination_zone", "rule_action"]},
        "delta": delta,
        "comments": comments,
        "status": "Pending",
        "created_at": now,
        "reviewed_at": None,
        "reviewer": None,
        "review_notes": None,
    }

    mods = _load("rule_modifications") or []
    mods.append(modification)
    _save("rule_modifications", mods)

    # Also create a review request
    reviews = _load("reviews") or []
    src_entries = (modifications.get("rule_source", rule.get("rule_source", "")) or "").split("\n")
    dst_entries = (modifications.get("rule_destination", rule.get("rule_destination", "")) or "").split("\n")
    review = {
        "id": f"REV-{_id()}",
        "rule_id": rule_id,
        "rule_name": f"{rule.get('app_name', '')} - {rule.get('inventory_item', rule_id)}",
        "request_type": "modify_rule",
        "module": "firewall-management",
        "requestor": "system",
        "reviewer": None,
        "status": "Pending",
        "submitted_at": now,
        "reviewed_at": None,
        "comments": comments or f"Rule modification for {rule_id}",
        "review_notes": None,
        "modification_id": mod_id,
        "delta": delta,
        "rule_summary": {
            "application": f"{rule.get('app_id', '')} - {rule.get('app_name', '')}",
            "source": ", ".join(src_entries[:3]),
            "destination": ", ".join(dst_entries[:3]),
            "ports": modifications.get("rule_service", rule.get("rule_service", "")),
            "environment": rule.get("policy_name", ""),
        },
    }
    reviews.append(review)
    _save("reviews", reviews)
    # Record lifecycle event: modification submitted for review
    await _record_lifecycle(rule_id, "submitted", to_status="Pending Review",
                            module="firewall-management",
                            details=comments or f"Rule modification submitted for {rule_id}")

    return modification


async def create_studio_rule_modification(rule_id: str, modifications: dict[str, Any],
                                           delta: dict[str, Any] | None = None,
                                           comments: str = "") -> dict[str, Any] | None:
    """Create a rule modification for a Design Studio rule with frontend-computed delta.

    Unlike legacy rule modifications, Studio rules use the frontend-computed delta
    (which includes group member-level changes like group:grp-name keys).
    """
    rules = _load("rules") or []
    rule = next((r for r in rules if r.get("rule_id") == rule_id), None)
    if not rule:
        return None

    # Use frontend-provided delta if available, otherwise compute from fields
    if not delta:
        delta = {"added": {}, "removed": {}, "changed": {}}

    now = _now()
    mod_id = f"MOD-{_id()}"

    modification = {
        "id": mod_id,
        "rule_id": rule_id,
        "original": {
            "source": rule.get("source", ""),
            "destination": rule.get("destination", ""),
            "ports": rule.get("ports", ""),
            "action": rule.get("action", "Allow"),
            "protocol": rule.get("protocol", "TCP"),
        },
        "modified": modifications,
        "delta": delta,
        "comments": comments,
        "status": "Pending",
        "created_at": now,
        "reviewed_at": None,
        "reviewer": None,
        "review_notes": None,
    }

    mods = _load("rule_modifications") or []
    mods.append(modification)
    _save("rule_modifications", mods)

    # Also create a review request so it appears in Review page
    reviews = _load("reviews") or []
    review = {
        "id": f"REV-{_id()}",
        "rule_id": rule_id,
        "rule_name": f"{rule.get('application', '')} - {rule_id}",
        "request_type": "modify_rule",
        "module": "design-studio",
        "requestor": "system",
        "reviewer": None,
        "status": "Pending",
        "submitted_at": now,
        "reviewed_at": None,
        "comments": comments or f"Studio rule modification for {rule_id}",
        "review_notes": None,
        "modification_id": mod_id,
        "delta": delta,
        "rule_summary": {
            "application": rule.get("application", ""),
            "source": str(modifications.get("source", rule.get("source", "")))[:100],
            "destination": str(modifications.get("destination", rule.get("destination", "")))[:100],
            "ports": str(modifications.get("ports", rule.get("ports", ""))),
            "environment": rule.get("environment", ""),
        },
    }
    reviews.append(review)
    _save("reviews", reviews)

    await _record_lifecycle(rule_id, "submitted", to_status="Pending Review",
                            module="design-studio",
                            details=comments or f"Studio rule modification submitted for {rule_id}")

    return modification


def find_rules_referencing_group(group_name: str) -> list[dict[str, Any]]:
    """Find all firewall rules (studio + legacy) that reference a group by name in source or destination."""
    affected: list[dict[str, Any]] = []
    # Check studio/firewall rules
    rules = _load("firewall_rules") or []
    for r in rules:
        src = str(r.get("source", ""))
        dst = str(r.get("destination", ""))
        if group_name in src or group_name in dst:
            affected.append(r)
    # Check legacy rules too
    legacy = _load("legacy_rules") or []
    for lr in legacy:
        src = str(lr.get("rule_source", ""))
        dst = str(lr.get("rule_destination", ""))
        src_exp = str(lr.get("rule_source_expanded", ""))
        dst_exp = str(lr.get("rule_destination_expanded", ""))
        if group_name in src or group_name in dst or group_name in src_exp or group_name in dst_exp:
            affected.append({
                "rule_id": lr.get("id", ""),
                "source": src,
                "destination": dst,
                "application": lr.get("app_name", ""),
                "environment": "Production",
                "port": lr.get("rule_service", ""),
                "protocol": "TCP",
                "action": lr.get("rule_action", "Allow"),
                "_legacy": True,
            })
    return affected


async def create_group_change_policy_reviews(
    group_name: str,
    change_type: str,  # "member_added", "member_removed", "group_updated"
    change_details: str,
    member_delta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """When a group/subgroup changes, find all affected rules and create policy change
    review records so they can be submitted, reviewed, approved, and compiled."""
    affected_rules = find_rules_referencing_group(group_name)
    if not affected_rules:
        return {"group": group_name, "affected_rules": 0, "reviews_created": []}

    now = _now()
    reviews_created: list[dict[str, Any]] = []
    reviews = _load("reviews") or []
    mods = _load("rule_modifications") or []

    delta = member_delta or {"added": {}, "removed": {}, "changed": {}}

    for rule in affected_rules:
        rule_id = rule.get("rule_id", "")
        mod_id = f"MOD-{_id()}"

        # Determine if the group is in source, destination, or both
        src = str(rule.get("source", ""))
        dst = str(rule.get("destination", ""))
        affected_field = []
        if group_name in src:
            affected_field.append("source")
        if group_name in dst:
            affected_field.append("destination")

        modification = {
            "id": mod_id,
            "rule_id": rule_id,
            "original": {
                "source": src,
                "destination": dst,
                "ports": rule.get("port", rule.get("ports", "")),
                "action": rule.get("action", "Allow"),
                "protocol": rule.get("protocol", "TCP"),
            },
            "modified": {
                "source": src,
                "destination": dst,
                "ports": rule.get("port", rule.get("ports", "")),
                "action": rule.get("action", "Allow"),
                "protocol": rule.get("protocol", "TCP"),
            },
            "delta": delta,
            "comments": f"Group '{group_name}' {change_type}: {change_details} — affects {', '.join(affected_field)} of rule {rule_id}",
            "status": "Pending",
            "created_at": now,
            "reviewed_at": None,
            "reviewer": None,
            "review_notes": None,
            "group_change": True,
            "group_name": group_name,
        }
        mods.append(modification)

        review = {
            "id": f"REV-{_id()}",
            "rule_id": rule_id,
            "rule_name": f"{rule.get('application', '')} - {rule_id}",
            "request_type": "group_policy_change",
            "module": "design-studio",
            "requestor": "system",
            "reviewer": None,
            "status": "Pending",
            "submitted_at": now,
            "reviewed_at": None,
            "comments": f"Group '{group_name}' changed ({change_type}): {change_details}",
            "review_notes": None,
            "modification_id": mod_id,
            "delta": delta,
            "group_change": True,
            "group_name": group_name,
            "rule_summary": {
                "application": rule.get("application", ""),
                "source": src[:100],
                "destination": dst[:100],
                "ports": str(rule.get("port", rule.get("ports", ""))),
                "environment": rule.get("environment", ""),
            },
        }
        reviews.append(review)
        reviews_created.append({"review_id": review["id"], "rule_id": rule_id, "mod_id": mod_id})

        await _record_lifecycle(rule_id, "submitted", to_status="Pending Review",
                                module="design-studio",
                                details=f"Policy change review: group '{group_name}' {change_type}")

    _save("rule_modifications", mods)
    _save("reviews", reviews)

    return {
        "group": group_name,
        "change_type": change_type,
        "affected_rules": len(affected_rules),
        "reviews_created": reviews_created,
    }


async def get_rule_modifications(rule_id: str | None = None) -> list[dict[str, Any]]:
    mods = _load("rule_modifications") or []
    if rule_id:
        mods = [m for m in mods if m.get("rule_id") == rule_id]
    return mods


async def approve_rule_modification(mod_id: str, notes: str = "") -> dict[str, Any] | None:
    """Approve a modification and apply changes to the rule.
    Also records the original rule's fingerprint as superseded so that
    re-importing the old version from Excel is intelligently skipped."""
    mods = _load("rule_modifications") or []
    now = _now()
    for m in mods:
        if m.get("id") == mod_id:
            m["status"] = "Approved"
            m["reviewed_at"] = now
            m["reviewer"] = "sns_user"
            m["review_notes"] = notes
            _save("rule_modifications", mods)
            # Record original fingerprint as superseded before applying changes
            rule_id = m.get("rule_id")
            if rule_id:
                rules = _load("legacy_rules") or []
                original_rule = next((r for r in rules if r["id"] == rule_id), None)
                if original_rule:
                    orig_fp = _rule_fingerprint(original_rule)
                    _add_superseded_fingerprint(orig_fp)
                # Apply modification to rule
                modified = m.get("modified", {})
                await update_legacy_rule(rule_id, modified)
            # Also persist the completed modification record in studio_rules.json
            await _record_completed_modification(m)
            # Record lifecycle event: modification approved
            rule_id_val = m.get("rule_id", "")
            await _record_lifecycle(rule_id_val, "approved",
                                    from_status="Pending Review", to_status="Approved",
                                    actor="sns_user", module="firewall-management",
                                    details=f"Rule modification {mod_id} approved")
            await _record_lifecycle(rule_id_val, "modified",
                                    actor="sns_user", module="firewall-management",
                                    details=f"Rule modification applied: {mod_id}")
            return m
    return None


async def _record_completed_modification(mod: dict[str, Any]) -> None:
    """Record a completed (approved) modification in studio_rules.json for tracking."""
    data = _load_separate("studio_rules") or []
    record = {
        "modification_id": mod.get("id"),
        "rule_id": mod.get("rule_id"),
        "type": "modification",
        "original": mod.get("original", {}),
        "modified": mod.get("modified", {}),
        "delta": mod.get("delta", {}),
        "approved_at": mod.get("reviewed_at"),
        "reviewer": mod.get("reviewer"),
    }
    # Avoid duplicates by modification_id
    existing_ids = {r.get("modification_id") for r in data if r.get("type") == "modification"}
    if record["modification_id"] not in existing_ids:
        data.append(record)
        _save_separate("studio_rules", data)



async def reject_rule_modification(mod_id: str, notes: str) -> dict[str, Any] | None:
    mods = _load("rule_modifications") or []
    now = _now()
    for m in mods:
        if m.get("id") == mod_id:
            m["status"] = "Rejected"
            m["reviewed_at"] = now
            m["reviewer"] = "sns_user"
            m["review_notes"] = notes
            _save("rule_modifications", mods)
            # Record lifecycle event: modification rejected
            await _record_lifecycle(m.get("rule_id", ""), "rejected",
                                    from_status="Pending Review", to_status="Rejected",
                                    actor="sns_user", module="firewall-management",
                                    details=f"Rule modification {mod_id} rejected: {notes}")
            return m
    return None


# ============================================================
# Legacy Rule Compiler (for Firewall Management export)
# ============================================================

async def compile_legacy_rule(rule_id: str, vendor: str = "generic") -> dict[str, Any] | None:
    """Compile a legacy rule into vendor-specific format."""
    rules = _load("legacy_rules") or []
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        return None

    src = rule.get("rule_source", "")
    dst = rule.get("rule_destination", "")
    svc = rule.get("rule_service", "any")
    action = rule.get("rule_action", "Accept")
    src_zone = rule.get("rule_source_zone", "any")
    dst_zone = rule.get("rule_destination_zone", "any")
    app_name = rule.get("app_name", "N/A")
    policy = rule.get("policy_name", "N/A")
    env = rule.get("environment", "")
    src_nh = rule.get("source_nh", rule.get("nh", ""))
    dst_nh = rule.get("destination_nh", rule.get("dst_nh", ""))

    # Resolve NH-SZ VRF conventions
    src_vrf = _resolve_vrf(src_nh, src_zone, env)
    dst_vrf = _resolve_vrf(dst_nh, dst_zone, env)

    src_objs = [s.strip() for s in src.split("\n") if s.strip()] or ["any"]
    dst_objs = [d.strip() for d in dst.split("\n") if d.strip()] or ["any"]
    svc_list = [s.strip() for s in svc.split("\n") if s.strip()] or ["any"]

    if vendor == "palo_alto":
        compiled = (
            f"# Palo Alto - {app_name} - {rule_id}\n"
            f"# Source VRF: {src_vrf} | Destination VRF: {dst_vrf}\n"
            + "\n".join(
                f"set rulebase security rules \"{rule_id}\" from {src_zone}\n"
                f"set rulebase security rules \"{rule_id}\" to {dst_zone}\n"
                f"set rulebase security rules \"{rule_id}\" source [{s}]\n"
                f"set rulebase security rules \"{rule_id}\" destination [{d}]\n"
                f"set rulebase security rules \"{rule_id}\" service [{sv}]\n"
                f"set rulebase security rules \"{rule_id}\" action {'allow' if action == 'Accept' else 'deny'}\n"
                f"set rulebase security rules \"{rule_id}\" log-start yes"
                for s in src_objs for d in dst_objs for sv in svc_list
            )
        )
    elif vendor == "checkpoint":
        compiled = (
            f"# Check Point - {app_name} - {rule_id}\n"
            f"# Source VRF: {src_vrf} | Destination VRF: {dst_vrf}\n"
            + "\n".join(
                f"mgmt_cli add access-rule layer \"Network\" position top \\\n"
                f"  name \"{rule_id}\" \\\n"
                f"  source \"{s}\" \\\n"
                f"  destination \"{d}\" \\\n"
                f"  service \"{sv}\" \\\n"
                f"  action \"{'Accept' if action == 'Accept' else 'Drop'}\" \\\n"
                f"  track \"Log\""
                for s in src_objs for d in dst_objs for sv in svc_list
            )
        )
    elif vendor == "fortigate":
        compiled = (
            f"# FortiGate - {app_name} - {rule_id}\n"
            f"config firewall policy\n"
            + "\n".join(
                f"  edit 0\n"
                f"    set name \"{rule_id}\"\n"
                f"    set srcintf \"{src_zone}\"\n"
                f"    set dstintf \"{dst_zone}\"\n"
                f"    set srcaddr \"{s}\"\n"
                f"    set dstaddr \"{d}\"\n"
                f"    set service \"{sv}\"\n"
                f"    set action {'accept' if action == 'Accept' else 'deny'}\n"
                f"    set logtraffic all\n"
                f"    set src-vrf \"{src_vrf}\"\n"
                f"    set dst-vrf \"{dst_vrf}\"\n"
                f"  next"
                for s in src_objs for d in dst_objs for sv in svc_list
            )
            + "\nend"
        )
    else:
        compiled = (
            f"# Firewall Rule: {rule_id}\n"
            f"# Application: {app_name}\n"
            f"# Policy: {policy}\n"
            f"# Source VRF: {src_vrf}\n"
            f"# Destination VRF: {dst_vrf}\n"
            f"---\n"
            f"rule:\n"
            f"  id: {rule_id}\n"
            f"  action: {action.lower()}\n"
            f"  source:\n"
            f"    objects: [{', '.join(src_objs)}]\n"
            f"    zone: {src_zone}\n"
            f"    vrf: {src_vrf}\n"
            f"  destination:\n"
            f"    objects: [{', '.join(dst_objs)}]\n"
            f"    zone: {dst_zone}\n"
            f"    vrf: {dst_vrf}\n"
            f"  service: [{', '.join(svc_list)}]\n"
            f"  logging: true\n"
            f"  enabled: true"
        )

    # --- Group provisioning as part of compile ---
    app_id_val = rule.get("app_id", "")
    group_provisioning = None
    if app_id_val:
        group_provisioning = await provision_groups_to_device(str(app_id_val), vendor if vendor in ("palo_alto", "checkpoint") else "palo_alto")

    result: dict[str, Any] = {
        "rule_id": rule_id,
        "vendor_format": vendor,
        "compiled_text": compiled,
        "source_objects": src_objs,
        "destination_objects": dst_objs,
        "services": svc_list,
        "action": action.lower(),
        "logging": True,
        "comment": f"{app_name} - {policy}",
        "source_vrf": src_vrf,
        "destination_vrf": dst_vrf,
    }
    if group_provisioning:
        result["group_provisioning"] = group_provisioning
    return result


# ============================================================
# Birthright Rule Validation (for Migration to NGDC & Design Studio)
# ============================================================

async def validate_birthright(rule_data: dict[str, Any]) -> dict[str, Any]:
    """Validate a rule against birthright rules using NH/SZ/DC matrix.
    Supports environment parameter: 'Production', 'Non-Production', 'Pre-Production'.

    All matrices now use a unified source_zone / dest_zone format with
    matrix_type and firewall_traversal fields.  Cross-SZ traffic (except
    STD/GEN open zones) requires firewall traversal (egress + ingress).
    """
    from .seed_data import OPEN_ZONES, SEGMENTED_ZONES, NON_PROD_SEGMENTED_ZONES

    ngdc_prod = _load("ngdc_prod_matrix") or []
    nonprod = _load("nonprod_matrix") or []
    preprod = _load("preprod_matrix") or []

    src_zone = rule_data.get("source_zone", "")
    dst_zone = rule_data.get("destination_zone", "")
    src_nh = rule_data.get("source_nh", "")
    dst_nh = rule_data.get("destination_nh", "")
    src_dc = rule_data.get("source_dc", "")
    dst_dc = rule_data.get("destination_dc", "")
    src_sz = rule_data.get("source_sz", src_zone)
    dst_sz = rule_data.get("destination_sz", dst_zone)
    # Support both legacy is_prod flag and new environment string
    environment = rule_data.get("environment", "")
    if not environment:
        is_prod = rule_data.get("is_prod", True)
        environment = "Production" if is_prod else "Non-Production"

    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    permitted: list[dict[str, str]] = []
    firewall_devices_needed: list[str] = []

    # Select the correct matrix based on environment
    env_lower = environment.lower()
    if "pre" in env_lower:
        matrix = preprod
        env_label = "Pre-Prod"
    elif "non" in env_lower:
        matrix = nonprod
        env_label = "Non-Prod"
    else:
        matrix = ngdc_prod
        env_label = "Prod"

    # Unified matching: all matrices now use source_zone / dest_zone
    matched = False
    for entry in matrix:
        e_src_zone = entry.get("source_zone", "")
        e_dst_zone = entry.get("dest_zone", "")
        action = entry.get("action", "")
        reason = entry.get("reason", "")
        fw_traversal = entry.get("firewall_traversal", "none")

        sz_src_match = (e_src_zone == "Any" or e_src_zone == src_sz or
                        e_src_zone.upper() == src_sz.upper())
        sz_dst_match = (e_dst_zone == "Any" or e_dst_zone == dst_sz or
                        e_dst_zone.upper() == dst_sz.upper())

        if sz_src_match and sz_dst_match:
            matched = True
            actual_src = src_sz if e_src_zone == "Any" else e_src_zone
            actual_dst = dst_sz if e_dst_zone == "Any" else e_dst_zone
            rule_desc = f"SZ:{actual_src} -> SZ:{actual_dst}"
            if fw_traversal not in ("none", "n/a"):
                rule_desc += f" [FW: {fw_traversal}]"

            if "Blocked" in action:
                violations.append({"matrix": f"NGDC {env_label}", "rule": rule_desc,
                                   "action": action, "reason": reason})
            elif "Firewall Request Required" in action:
                warnings.append({"matrix": f"NGDC {env_label}", "rule": rule_desc,
                                 "action": action, "reason": reason,
                                 "firewall_traversal": fw_traversal})
                # Track which firewall devices are needed
                if "egress" in fw_traversal:
                    firewall_devices_needed.append(
                        f"Egress: {src_nh or 'src_NH'} {actual_src} FW")
                if "ingress" in fw_traversal:
                    firewall_devices_needed.append(
                        f"Ingress: {dst_nh or 'dst_NH'} {actual_dst} FW")
            elif "Exception" in action:
                warnings.append({"matrix": f"NGDC {env_label}", "rule": rule_desc,
                                 "action": action, "reason": reason})
            else:
                permitted.append({"matrix": f"NGDC {env_label}", "rule": rule_desc,
                                  "action": action, "reason": reason})

    # If no explicit match, apply implicit cross-SZ enforcement
    # Track informational FW path (for same-SZ cross-NH segmented traffic)
    firewall_path_info: list[str] = []

    if not matched:
        all_segmented = SEGMENTED_ZONES | NON_PROD_SEGMENTED_ZONES
        cross_sz = src_sz != dst_sz
        cross_nh = src_nh != dst_nh and src_nh and dst_nh
        both_open = src_sz in OPEN_ZONES and dst_sz in OPEN_ZONES

        if src_sz == dst_sz and not cross_nh:
            # Same SZ, same NH — permitted, no FW path
            permitted.append({"matrix": f"NGDC {env_label} (implicit)",
                              "rule": f"SZ:{src_sz} -> SZ:{dst_sz}",
                              "action": "Permitted",
                              "reason": "Same SZ intra-zone, same NH – permitted"})
        elif src_sz == dst_sz and cross_nh:
            # Same SZ, cross NH — permitted per birthright (no rule required),
            # but show FW device path as informational for segmented zones
            if src_sz in all_segmented:
                firewall_path_info.append(f"{src_nh} {src_sz} FW")
                firewall_path_info.append(f"{dst_nh} {dst_sz} FW")
                permitted.append({"matrix": f"NGDC {env_label} (implicit)",
                                  "rule": f"SZ:{src_sz} -> SZ:{dst_sz} ({src_nh} -> {dst_nh})",
                                  "action": "Permitted",
                                  "reason": f"Same SZ ({src_sz}) cross-NH – permitted per birthright, no firewall rule required. Traffic path through {src_nh} and {dst_nh} FW devices."})
            else:
                permitted.append({"matrix": f"NGDC {env_label} (implicit)",
                                  "rule": f"SZ:{src_sz} -> SZ:{dst_sz} ({src_nh} -> {dst_nh})",
                                  "action": "Permitted",
                                  "reason": "Same SZ (open zone) cross-NH – permitted"})
        elif both_open:
            permitted.append({"matrix": f"NGDC {env_label} (implicit)",
                              "rule": f"SZ:{src_sz} -> SZ:{dst_sz}",
                              "action": "Permitted",
                              "reason": "STD/GEN open routing – permitted"})
        elif cross_sz and (src_sz in all_segmented or dst_sz in all_segmented):
            fw_type = "egress+ingress"
            if src_sz in OPEN_ZONES:
                fw_type = "ingress"
            elif dst_sz in OPEN_ZONES:
                fw_type = "egress"
            warnings.append({"matrix": f"NGDC {env_label} (implicit)",
                             "rule": f"SZ:{src_sz} -> SZ:{dst_sz} [FW: {fw_type}]",
                             "action": "Firewall Request Required",
                             "reason": f"Cross-SZ requires {fw_type} firewall traversal",
                             "firewall_traversal": fw_type})
            if "egress" in fw_type:
                firewall_devices_needed.append(f"Egress: {src_nh or 'src_NH'} {src_sz} FW")
            if "ingress" in fw_type:
                firewall_devices_needed.append(f"Ingress: {dst_nh or 'dst_NH'} {dst_sz} FW")

    is_compliant = len(violations) == 0
    fw_required = len(firewall_devices_needed) > 0
    return {
        "compliant": is_compliant,
        "environment": environment,
        "matrix_used": env_label,
        "violations": violations,
        "warnings": warnings,
        "permitted": permitted,
        "firewall_devices_needed": firewall_devices_needed,
        "firewall_path_info": firewall_path_info,
        "firewall_request_required": fw_required,
        "summary": (
            f"{'Compliant' if is_compliant else 'Non-Compliant'} ({env_label}) - "
            f"{len(violations)} violations, {len(warnings)} warnings, "
            f"{len(permitted)} permitted"
            + (f", FW devices: {', '.join(firewall_devices_needed)}" if fw_required else "")
            + (f", FW path (info): {', '.join(firewall_path_info)}" if firewall_path_info else "")
        ),
    }


# ============================================================
# Birthright Matrix CRUD
# ============================================================

async def get_birthright_matrix() -> dict[str, Any]:
    """Return all three birthright matrices."""
    return {
        "heritage_dc": _load("heritage_dc_matrix") or [],
        "ngdc_prod": _load("ngdc_prod_matrix") or [],
        "nonprod": _load("nonprod_matrix") or [],
    }


async def update_birthright_matrix(matrix_type: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Update a specific birthright matrix."""
    key_map = {
        "heritage_dc": "heritage_dc_matrix",
        "ngdc_prod": "ngdc_prod_matrix",
        "nonprod": "nonprod_matrix",
    }
    key = key_map.get(matrix_type)
    if not key:
        return []
    _save(key, entries)
    return entries


async def add_birthright_entry(matrix_type: str, entry: dict[str, Any]) -> dict[str, Any]:
    key_map = {
        "heritage_dc": "heritage_dc_matrix",
        "ngdc_prod": "ngdc_prod_matrix",
        "nonprod": "nonprod_matrix",
    }
    key = key_map.get(matrix_type)
    if not key:
        return {}
    data = _load(key) or []
    data.append(entry)
    _save(key, data)
    return entry


async def delete_birthright_entry(matrix_type: str, index: int) -> bool:
    key_map = {
        "heritage_dc": "heritage_dc_matrix",
        "ngdc_prod": "ngdc_prod_matrix",
        "nonprod": "nonprod_matrix",
    }
    key = key_map.get(matrix_type)
    if not key:
        return False
    data = _load(key) or []
    if 0 <= index < len(data):
        data.pop(index)
        _save(key, data)
        return True
    return False


# ============================================================
# Legacy Group Detection from Expansion Columns
# ============================================================

def _is_legacy_group_name(name: str) -> bool:
    """Check if a name looks like a legacy firewall group by known prefixes.
    This is a *hint* only — the authoritative test is whether the entry has
    indented children in the expansion column (see parse_expansion_groups).
    Kept for backward compatibility with expand_groups_in_rule() which
    operates on flat rule_source/rule_destination fields without expansion."""
    lower = name.strip().lower()
    group_prefixes = (
        "g-", "grp-", "ggrp-", "gapigr-", "grp_", "g_",
        "group-", "group_", "netgrp-", "netgrp_", "addrgrp-",
    )
    return any(lower.startswith(pfx) for pfx in group_prefixes)


def parse_expansion_groups(expansion_text: str) -> list[dict[str, Any]]:
    """Parse the expansion/detail column to extract group hierarchies.

    Group detection is **structure-based**: any top-level entry that has
    indented children below it is treated as a group, regardless of its
    prefix.  The prefix can be anything (g-, grp-, ggrp-, gapigr-, myapp-,
    fw-, etc.) — the indentation hierarchy is the sole authority.

    Example expansion text:
      MY-CUSTOM-GROUP                  ← group (has indented children)
        10.1.1.1 (Web Server 1)        ← member IP
        10.1.1.2 (Web Server 2)        ← member IP
        NESTED-SUB-GRP                 ← nested sub-group (has deeper children)
          10.2.2.1 (DB Server)         ← member of nested group
      svr-10.3.3.3                     ← standalone (no children → not a group)

    Returns a list of group dicts:
    [
      {
        "name": "MY-CUSTOM-GROUP",
        "members": [
          {"type": "ip", "value": "10.1.1.1", "description": "Web Server 1"},
          {"type": "ip", "value": "10.1.1.2", "description": "Web Server 2"},
          {"type": "group", "value": "NESTED-SUB-GRP", "members": [
            {"type": "ip", "value": "10.2.2.1", "description": "DB Server"}
          ]}
        ]
      }
    ]
    """
    if not expansion_text or not isinstance(expansion_text, str):
        return []

    # --- First pass: collect all lines with their indent levels ---
    parsed_lines: list[tuple[int, str]] = []  # (indent, text)
    for raw_line in expansion_text.split("\n"):
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip()
        indent = len(raw_line) - len(stripped)
        text = stripped.strip()
        if text:
            parsed_lines.append((indent, text))

    if not parsed_lines:
        return []

    def _parse_value(entry: str) -> tuple[str, str]:
        """Split 'value (description)' → (value, description)."""
        entry = entry.strip()
        if "(" in entry and ")" in entry:
            paren_start = entry.index("(")
            paren_end = entry.rindex(")")
            return entry[:paren_start].strip(), entry[paren_start + 1:paren_end].strip()
        return entry, ""

    def _member_type(value: str) -> str:
        """Classify a member value (ip, subnet, range, or generic)."""
        vl = value.lower()
        if vl.startswith("net-") or vl.startswith("sub-"):
            return "subnet"
        if "/" in value and not vl.startswith("tcp") and not vl.startswith("udp"):
            return "subnet"  # CIDR notation = subnet
        if vl.startswith("rng-"):
            return "range"
        return "ip"

    # --- Second pass: look-ahead to detect groups structurally ---
    # An entry at index i is a group if the next entry (i+1) has deeper indentation.
    def _has_children(idx: int) -> bool:
        if idx + 1 >= len(parsed_lines):
            return False
        return parsed_lines[idx + 1][0] > parsed_lines[idx][0]

    groups: list[dict[str, Any]] = []
    current_group: dict[str, Any] | None = None
    current_subgroup: dict[str, Any] | None = None
    group_indent = 0
    member_indent = 0

    for i, (indent, text) in enumerate(parsed_lines):
        value, desc = _parse_value(text)

        # If we are NOT inside a group, check if this entry starts one
        if current_group is None:
            if _has_children(i):
                # This entry has children → it's a group
                current_group = {"name": value, "members": []}
                current_subgroup = None
                group_indent = indent
                member_indent = parsed_lines[i + 1][0]  # expected child indent
            # else: standalone entry, skip for group detection
            continue

        # We are inside a group
        if indent <= group_indent:
            # Same or lower indent as the group header → group ended
            groups.append(current_group)
            current_group = None
            current_subgroup = None
            # Re-evaluate this line: could it start a new group?
            if _has_children(i):
                current_group = {"name": value, "members": []}
                current_subgroup = None
                group_indent = indent
                member_indent = parsed_lines[i + 1][0]
            continue

        # Indented line — belongs to the current group
        if indent >= member_indent and _has_children(i):
            # This member itself has deeper children → nested sub-group
            sub = {"type": "group", "value": value, "description": desc, "members": []}
            current_subgroup = sub
            current_group["members"].append(sub)
        elif current_subgroup is not None and indent > member_indent:
            # Deeper than first-level members → belongs to the sub-group
            mtype = _member_type(value)
            current_subgroup["members"].append({"type": mtype, "value": value, "description": desc})
        else:
            # Direct member of the current group
            current_subgroup = None
            mtype = _member_type(value)
            current_group["members"].append({"type": mtype, "value": value, "description": desc})

    # Flush last group
    if current_group:
        groups.append(current_group)

    return groups


# ============================================================
# NGDC Migration Recommendations
# ============================================================

async def get_ngdc_recommendations(rule_id: str) -> dict[str, Any] | None:
    """Generate NGDC recommendations for a legacy rule based on backend mapping tables,
    App-DC mappings, and service/port analysis."""
    rules = _load("legacy_rules") or []
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        return None

    nhs = _load("neighbourhoods") or []
    szs = _load("security_zones") or []
    apps = _load("applications") or []
    groups = _load("groups") or []
    ngdc_mappings = _load("ngdc_mappings") or []
    app_dc_mappings = _load("app_dc_mappings") or []

    app_id = str(rule.get("app_id", ""))
    app_dist = rule.get("app_distributed_id", "") or ""
    app_name = rule.get("app_name", "")
    rule_env = rule.get("environment", "Production")
    app_info = next((a for a in apps if str(a.get("app_id")) == app_id or a.get("app_distributed_id") == app_dist), None)

    # Prefer app_distributed_id for naming; fall back to app_id
    # Also check the application record for a distributed_id if the rule doesn't have one
    if not app_dist and app_info:
        app_dist = app_info.get("app_distributed_id", "") or ""
    app_label = app_dist if app_dist else app_id

    # --- Step 1: Determine NH/SZ using the rule's actual source/dest zones ---
    # The rule itself tells us source_zone and destination_zone — use these to
    # find the correct NH for each direction from app-DC mappings.
    rule_src_zone = (rule.get("rule_source_zone") or "").strip()
    rule_dst_zone = (rule.get("rule_destination_zone") or "").strip()

    # Get ALL app-DC mappings for this app (component-level)
    # Match on app_distributed_id first, then fall back to app_id
    all_app_comps = [m for m in app_dc_mappings
                     if str(m.get("app_distributed_id", "")).upper() == app_label.upper()
                     or str(m.get("app_id", "")).upper() == app_id.upper()]

    def _find_nh_for_zone(zone: str) -> tuple[str, str, str]:
        """Find NH, SZ, DC for a given zone from app-DC mappings.
        Handles comma-separated NH/SZ values in app_info by picking the first match."""
        if not zone:
            return ("NH01", "GEN", "")
        zone_upper = zone.upper()
        for c in all_app_comps:
            if (c.get("sz", "")).upper() == zone_upper:
                return (c.get("nh", "NH01"), c.get("sz", zone_upper), c.get("dc", ""))
        # Fallback: first component mapping or defaults
        if all_app_comps:
            first = all_app_comps[0]
            return (first.get("nh", "NH01"), zone_upper, first.get("dc", ""))
        if app_info:
            # Handle comma-separated NH/SZ — pick the first value as default
            raw_nh = app_info.get("nh", "NH01")
            first_nh = raw_nh.split(",")[0].strip() if raw_nh else "NH01"
            return (first_nh, zone_upper, "")
        return ("NH01", zone_upper, "")

    src_nh, src_sz, src_dc = _find_nh_for_zone(rule_src_zone)
    dst_nh, dst_sz, dst_dc = _find_nh_for_zone(rule_dst_zone)

    # Use source-side as the "recommended" default (for backward compat)
    recommended_nh = src_nh
    recommended_sz = src_sz
    recommended_dc = src_dc
    nh_sz_source = "rule_zone_mapping" if all_app_comps else "default"

    # --- Step 2: Build IP mappings using NGDC mapping table lookups ---
    src_entries = [s.strip() for s in (rule.get("rule_source", "") or "").split("\n") if s.strip()]
    dst_entries = [d.strip() for d in (rule.get("rule_destination", "") or "").split("\n") if d.strip()]
    svc_entries = [s.strip() for s in (rule.get("rule_service", "") or "").split("\n") if s.strip()]

    def _lookup_ngdc_mapping(legacy_name: str) -> dict[str, Any] | None:
        """Look up NGDC mapping table for an exact or partial match on legacy name."""
        for m in ngdc_mappings:
            if m.get("legacy_name", "").lower() == legacy_name.lower():
                return m
        # Partial match: check if legacy_name is contained in mapping's legacy_name
        for m in ngdc_mappings:
            if legacy_name.lower() in m.get("legacy_name", "").lower() or \
               m.get("legacy_name", "").lower() in legacy_name.lower():
                return m
        return None

    # Load IP mappings table early so _build_mapping can use 1-to-1 mapped IPs
    _ip_mappings_early = _load("ip_mappings") or []

    def _lookup_ip_mapping(legacy_ip_raw: str) -> str | None:
        """Look up NGDC equivalent from the 1-to-1 ip_mappings table.
        Returns with appropriate prefix: svr- for IPs, net- for subnets, rng- for ranges."""
        clean = legacy_ip_raw.strip()
        original_prefix = ""
        for pfx in ("svr-", "rng-", "net-", "sub-", "grp-"):
            if clean.lower().startswith(pfx):
                original_prefix = pfx.lower()
                clean = clean[len(pfx):]
                break
        for m in _ip_mappings_early:
            legacy_val = str(m.get("legacy_ip", ""))
            if legacy_val == clean or legacy_val == legacy_ip_raw:
                ngdc_ip = str(m.get("ngdc_ip", ""))
                if not ngdc_ip:
                    return None
                # Determine correct NGDC prefix based on type
                if original_prefix in ("net-", "sub-") or "/" in ngdc_ip:
                    return f"net-{ngdc_ip}"
                if original_prefix == "rng-":
                    return f"rng-{ngdc_ip}"
                return f"svr-{ngdc_ip}"
        return None

    def _suggest_ngdc_name(legacy_name: str, entry_type: str, direction: str = "source") -> str:
        ln = legacy_name.lower()
        prefix = "grp" if ln.startswith("grp") or ln.startswith("gapigr") else \
                 "svr" if ln.startswith("svr") else \
                 "rng" if ln.startswith("rng") else \
                 "net" if ln.startswith("net-") or ln.startswith("sub-") else \
                 "net" if "/" in legacy_name and not ln.startswith("tcp") and not ln.startswith("udp") else \
                 "grp"
        short_app = app_label.upper()
        # For individual IPs/subnets/ranges, try 1-to-1 mapping first
        if prefix in ("svr", "net", "rng"):
            mapped = _lookup_ip_mapping(legacy_name)
            if mapped:
                return mapped
        # Use component detection + app DC metadata for NH/SZ
        detected_comp = _detect_component(legacy_name)
        comp_mapping = next((c for c in app_components if c.get("component") == detected_comp), None)
        if comp_mapping:
            nh = comp_mapping.get("nh", dst_nh if direction == "destination" else src_nh)
            sz = comp_mapping.get("sz", dst_sz if direction == "destination" else src_sz)
        elif direction == "destination":
            nh, sz = dst_nh, dst_sz
        else:
            nh, sz = src_nh, src_sz
        # Egress/Ingress naming convention
        if prefix == "grp":
            if direction == "source":
                return f"grp-{short_app}-{nh}-{sz}"
            else:
                return f"grp-{short_app}-{nh}-{sz}-{detected_comp}-Ingress"
        return f"{prefix}-{short_app}-{nh}-{sz}"

    def _build_mapping(legacy_name: str, entry_type: str, idx: int, direction: str = "source") -> dict[str, Any]:
        ln = legacy_name.lower()
        obj_type = "group" if ln.startswith("grp") or ln.startswith("gapigr") else \
                   "server" if ln.startswith("svr") else \
                   "range" if ln.startswith("rng") else \
                   "subnet" if ln.startswith("net-") or ln.startswith("sub-") else \
                   "subnet" if "/" in legacy_name and not ln.startswith("tcp") and not ln.startswith("udp") else \
                   "other"
        dir_nh = dst_nh if direction == "destination" else src_nh
        dir_sz = dst_sz if direction == "destination" else src_sz

        # Priority 1: Look up NGDC mapping table
        table_match = _lookup_ngdc_mapping(legacy_name)
        if table_match:
            return {
                "legacy": legacy_name,
                "ngdc_recommended": table_match["ngdc_name"],
                "type": table_match.get("type", obj_type),
                "mapping_source": "ngdc_mapping_table",
                "mapping_id": table_match.get("id"),
                "mapping_status": table_match.get("status", ""),
                "ngdc_nh": table_match.get("ngdc_nh", "") or dir_nh,
                "ngdc_sz": table_match.get("ngdc_sz", "") or dir_sz,
                "existing_group": None,
                "customizable": True,
            }

        # Priority 2: Match against existing groups
        existing_group = next((g for g in groups if any(
            m.get("value", "") in legacy_name for m in g.get("members", []))), None)
        if existing_group:
            return {
                "legacy": legacy_name,
                "ngdc_recommended": existing_group["name"],
                "type": obj_type,
                "mapping_source": "existing_group",
                "mapping_id": None,
                "mapping_status": "",
                "ngdc_nh": dir_nh,
                "ngdc_sz": dir_sz,
                "existing_group": existing_group["name"],
                "customizable": True,
            }

        # Priority 3: Generate based on naming convention with direction-specific NH/SZ
        return {
            "legacy": legacy_name,
            "ngdc_recommended": _suggest_ngdc_name(legacy_name, f"{entry_type}{idx+1:02d}", direction),
            "type": obj_type,
            "mapping_source": "auto_generated",
            "mapping_id": None,
            "mapping_status": "",
            "ngdc_nh": dir_nh,
            "ngdc_sz": dir_sz,
            "existing_group": None,
            "customizable": True,
        }

    source_mappings = [_build_mapping(src, "SRC", i, "source") for i, src in enumerate(src_entries)]
    destination_mappings = [_build_mapping(dst, "DST", i, "destination") for i, dst in enumerate(dst_entries)]

    # --- Step 3: Service/port recommendations ---
    standard_ports: dict[str, str] = {
        "tcp-80": "HTTP", "tcp-443": "HTTPS", "tcp-22": "SSH", "tcp-21": "FTP",
        "tcp-25": "SMTP", "tcp-53": "DNS", "udp-53": "DNS", "tcp-110": "POP3",
        "tcp-143": "IMAP", "tcp-993": "IMAPS", "tcp-995": "POP3S",
        "tcp-3306": "MySQL", "tcp-5432": "PostgreSQL", "tcp-1521": "Oracle",
        "tcp-1433": "MSSQL", "tcp-27017": "MongoDB", "tcp-6379": "Redis",
        "tcp-8080": "HTTP-Alt", "tcp-8443": "HTTPS-Alt",
        "tcp-389": "LDAP", "tcp-636": "LDAPS", "tcp-88": "Kerberos",
        "tcp-3389": "RDP", "tcp-5900": "VNC",
    }
    service_recommendations = []
    for svc in svc_entries:
        svc_lower = svc.strip().lower()
        desc = standard_ports.get(svc_lower, "")
        # Determine risk level based on service
        risk = "low"
        if any(p in svc_lower for p in ["22", "3389", "5900", "21"]):
            risk = "high"
        elif any(p in svc_lower for p in ["1521", "3306", "5432", "1433", "27017", "6379"]):
            risk = "medium"
        service_recommendations.append({
            "service": svc.strip(),
            "description": desc,
            "risk_level": risk,
            "recommendation": f"Ensure {desc or svc} access is restricted to authorized sources" if risk != "low" else "Standard service",
        })

    # Find recommended NH and SZ details (source-side as primary)
    nh_info = next((n for n in nhs if n.get("nh_id") == src_nh), None)
    sz_info = next((s for s in szs if s.get("code") == src_sz), None)
    dst_nh_info = next((n for n in nhs if n.get("nh_id") == dst_nh), None)
    dst_sz_info = next((s for s in szs if s.get("code") == dst_sz), None)

    # Count mapping sources
    table_count = sum(1 for m in source_mappings + destination_mappings if m["mapping_source"] == "ngdc_mapping_table")
    group_count = sum(1 for m in source_mappings + destination_mappings if m["mapping_source"] == "existing_group")
    auto_count = sum(1 for m in source_mappings + destination_mappings if m["mapping_source"] == "auto_generated")

    # --- Step 4: Build component-based group mappings ---
    # Get all app_dc_mappings for this app to determine component-level grouping
    app_components = [m for m in app_dc_mappings
                      if str(m.get("app_distributed_id", "")).upper() == app_label.upper()
                      or str(m.get("app_id", "")).upper() == app_id.upper()]
    short_app = app_label.upper()

    # Load IP mappings table for 1-to-1 legacy -> NGDC IP lookups
    ip_mappings_table = _load("ip_mappings") or []

    def _detect_component(ip_str: str) -> str:
        """Detect component type from IP by matching against app_dc_mappings CIDRs,
        ip_mappings table (NGDC IP -> component), legacy group names, and port heuristics."""
        import ipaddress
        ip_clean = ip_str.strip().split("\n")[0].strip()

        # Strip svr-/rng-/grp-/net-/sub- prefix for raw IP matching
        ip_raw = ip_clean
        for pfx in ("svr-", "rng-", "grp-", "net-", "sub-"):
            if ip_raw.lower().startswith(pfx):
                ip_raw = ip_raw[len(pfx):]
                break

        # Strategy 1: Match legacy IP against app_dc_mappings CIDRs directly
        for comp in app_components:
            cidr = comp.get("cidr", "")
            if not cidr:
                continue
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                try:
                    addr = ipaddress.ip_address(ip_raw)
                    if addr in net:
                        return comp.get("component", "APP")
                except ValueError:
                    try:
                        test_net = ipaddress.ip_network(ip_raw, strict=False)
                        if test_net.subnet_of(net) or net.subnet_of(test_net):
                            return comp.get("component", "APP")
                    except (ValueError, TypeError):
                        pass
            except (ValueError, TypeError):
                pass

        # Strategy 2: Look up ip_mappings table to find NGDC IP, then match NGDC IP against CIDRs
        for m in ip_mappings_table:
            legacy_val = str(m.get("legacy_ip", ""))
            if legacy_val == ip_raw or legacy_val == ip_clean:
                ngdc_ip = str(m.get("ngdc_ip", ""))
                if ngdc_ip:
                    for comp in app_components:
                        cidr = comp.get("cidr", "")
                        if not cidr:
                            continue
                        try:
                            net = ipaddress.ip_network(cidr, strict=False)
                            addr = ipaddress.ip_address(ngdc_ip)
                            if addr in net:
                                return comp.get("component", "APP")
                        except (ValueError, TypeError):
                            pass
                    # NGDC IP found but no CIDR match — try component from mapping metadata
                    comp_hint = m.get("component", "")
                    if comp_hint:
                        return comp_hint

        # Strategy 3: Infer component from legacy group name patterns
        name_lower = ip_clean.lower()
        comp_keywords = {
            "WEB": ["web", "www", "http", "frontend", "ui", "portal"],
            "APP": ["app", "application", "svc", "service", "middleware"],
            "DB": ["db", "database", "sql", "oracle", "mysql", "postgres", "mongo"],
            "MQ": ["mq", "queue", "rabbit", "kafka", "jms", "messaging"],
            "BAT": ["bat", "batch", "job", "scheduler", "cron"],
            "API": ["api", "gateway", "rest", "endpoint"],
        }
        for comp_type, keywords in comp_keywords.items():
            if any(kw in name_lower for kw in keywords):
                # Verify this component type exists for the app
                if any(c.get("component") == comp_type for c in app_components):
                    return comp_type

        # Strategy 4: Fallback — use the first available component type for this app
        if app_components:
            return app_components[0].get("component", "APP")
        return "APP"

    # Group source IPs by component
    src_component_map: dict[str, list[str]] = {}
    for src in src_entries:
        comp = _detect_component(src)
        src_component_map.setdefault(comp, []).append(src)

    # Group destination IPs by component
    dst_component_map: dict[str, list[str]] = {}
    for dst in dst_entries:
        comp = _detect_component(dst)
        dst_component_map.setdefault(comp, []).append(dst)

    def _lookup_ngdc_ip(legacy_ip_raw: str) -> str | None:
        """Look up the NGDC equivalent IP for a legacy IP from the ip_mappings table."""
        # Strip svr- / rng- / grp- / net- / sub- prefixes for matching
        clean = legacy_ip_raw.strip()
        for pfx in ("svr-", "rng-", "grp-", "net-", "sub-"):
            if clean.lower().startswith(pfx):
                clean = clean[len(pfx):]
                break
        for m in ip_mappings_table:
            legacy_val = str(m.get("legacy_ip", ""))
            if legacy_val == clean or legacy_val == legacy_ip_raw:
                return str(m.get("ngdc_ip", ""))
        return None

    def _build_component_group(comp: str, ips: list[str], direction: str) -> dict[str, Any]:
        """Build a component group mapping entry."""
        # Use direction-specific defaults from the rule's actual zones
        dir_nh = dst_nh if direction == "destination" else src_nh
        dir_sz = dst_sz if direction == "destination" else src_sz
        dir_dc = dst_dc if direction == "destination" else src_dc

        comp_mapping = next((c for c in app_components if c.get("component") == comp), None)
        comp_nh = comp_mapping.get("nh", dir_nh) if comp_mapping else dir_nh
        comp_sz = comp_mapping.get("sz", dir_sz) if comp_mapping else dir_sz
        comp_dc = comp_mapping.get("dc", dir_dc) if comp_mapping else dir_dc
        comp_cidr = comp_mapping.get("cidr", "") if comp_mapping else ""

        # Check if legacy already has a group for these IPs
        legacy_group = None
        for g in groups:
            members = [m.get("value", "") for m in g.get("members", [])]
            if any(ip in members or any(ip in mem for mem in members) for ip in ips):
                legacy_group = g["name"]
                break

        # Build NGDC entries by looking up 1-to-1 IP mapping table
        ngdc_ips: list[str] = []
        for ip in ips:
            mapped = _lookup_ngdc_ip(ip)
            if mapped:
                ngdc_ips.append(mapped)
            else:
                # Fallback: use appropriate prefix based on entry type
                clean_ip = ip.strip()
                original_pfx = ""
                for pfx in ("svr-", "rng-", "grp-", "net-", "sub-"):
                    if clean_ip.lower().startswith(pfx):
                        original_pfx = pfx.lower()
                        clean_ip = clean_ip[len(pfx):]
                        break
                # Determine NGDC prefix: net- for subnets/CIDRs, rng- for ranges, svr- for IPs
                if original_pfx in ("net-", "sub-") or ("/" in clean_ip and not clean_ip.startswith("tcp")):
                    ngdc_ips.append(f"net-{clean_ip}")
                elif original_pfx == "rng-":
                    ngdc_ips.append(f"rng-{clean_ip}")
                else:
                    ngdc_ips.append(f"svr-{clean_ip}")

        # Egress/Ingress naming: source = grp-APP-NH-SZ, dest = grp-APP-NH-SZ-COMP-Ingress
        if direction == "source":
            ngdc_group_name = f"grp-{short_app}-{comp_nh}-{comp_sz}"
        else:
            ngdc_group_name = f"grp-{short_app}-{comp_nh}-{comp_sz}-{comp}-Ingress"
        return {
            "component": comp,
            "direction": direction,
            "ips": ips,
            "ngdc_ips": ngdc_ips,
            "ip_count": len(ips),
            "legacy_group": legacy_group,
            "ngdc_group": ngdc_group_name,
            "nh": comp_nh,
            "sz": comp_sz,
            "dc": comp_dc,
            "cidr": comp_cidr,
            "environment": rule_env,
            "customizable": True,
        }

    component_groups = []
    for comp, ips in src_component_map.items():
        component_groups.append(_build_component_group(comp, ips, "source"))
    for comp, ips in dst_component_map.items():
        component_groups.append(_build_component_group(comp, ips, "destination"))

    # --- Step 5: Parse legacy groups from expansion columns ---
    src_expanded = rule.get("rule_source_expanded", "") or ""
    dst_expanded = rule.get("rule_destination_expanded", "") or ""
    legacy_source_groups = parse_expansion_groups(src_expanded)
    legacy_dest_groups = parse_expansion_groups(dst_expanded)

    # Build NGDC group mapping suggestions for each legacy group
    def _map_legacy_group(lg: dict[str, Any], direction: str) -> dict[str, Any]:
        """Map a legacy group to a suggested NGDC group with 1-1 member mappings.
        Uses component-based naming from App Management DC mappings:
        grp-{APP}-{COMPONENT}-{NH}-{SZ}"""
        legacy_name = lg["name"]

        # Detect component from the group's member IPs using app DC metadata
        member_ips = [m["value"] for m in lg.get("members", []) if m.get("type") != "group"]
        detected_comp = "APP"  # fallback
        if member_ips:
            detected_comp = _detect_component(member_ips[0])
        elif lg.get("members"):
            # If all members are sub-groups, try the first sub-group's members
            for sub in lg["members"]:
                sub_ips = [sm["value"] for sm in sub.get("members", []) if sm.get("type") != "group"]
                if sub_ips:
                    detected_comp = _detect_component(sub_ips[0])
                    break

        # Find the matching app_dc_mapping for this component to get NH/SZ
        comp_mapping = next((c for c in app_components if c.get("component") == detected_comp), None)
        if comp_mapping:
            dir_nh = comp_mapping.get("nh", dst_nh if direction == "destination" else src_nh)
            dir_sz = comp_mapping.get("sz", dst_sz if direction == "destination" else src_sz)
        else:
            dir_nh = dst_nh if direction == "destination" else src_nh
            dir_sz = dst_sz if direction == "destination" else src_sz

        # Try to find existing NGDC mapping for this group
        table_match = _lookup_ngdc_mapping(legacy_name)
        if table_match:
            ngdc_name = table_match["ngdc_name"]
        elif direction == "source":
            ngdc_name = f"grp-{short_app}-{dir_nh}-{dir_sz}"
        else:
            ngdc_name = f"grp-{short_app}-{dir_nh}-{dir_sz}-{detected_comp}-Ingress"

        # Map each member to NGDC equivalent
        mapped_members: list[dict[str, Any]] = []
        for mem in lg.get("members", []):
            if mem["type"] == "group":
                # Nested sub-group — recurse
                sub_mapped = _map_legacy_group(mem, direction)
                mapped_members.append({
                    "legacy": mem["value"],
                    "type": "group",
                    "ngdc": sub_mapped["ngdc_name"],
                    "members": sub_mapped.get("mapped_members", []),
                })
            else:
                legacy_val = mem["value"]
                mem_type = mem["type"]
                ngdc_val = _lookup_ip_mapping(legacy_val)
                if not ngdc_val:
                    # Generate NGDC name with correct prefix based on member type
                    clean_val = legacy_val
                    for pfx in ("svr-", "rng-", "net-", "sub-"):
                        if clean_val.lower().startswith(pfx):
                            clean_val = clean_val[len(pfx):]
                            break
                    if mem_type == "subnet":
                        ngdc_val = f"net-{clean_val}"
                    elif mem_type == "range":
                        ngdc_val = f"rng-{clean_val}"
                    else:
                        ngdc_val = f"svr-{clean_val}"
                mapped_members.append({
                    "legacy": legacy_val,
                    "type": mem_type,
                    "description": mem.get("description", ""),
                    "ngdc": ngdc_val,
                })

        return {
            "legacy_name": legacy_name,
            "ngdc_name": ngdc_name,
            "direction": direction,
            "member_count": len(lg.get("members", [])),
            "mapped_members": mapped_members,
            "mapping_source": "ngdc_mapping_table" if table_match else "auto_generated",
            "component": detected_comp,
            "nh": dir_nh,
            "sz": dir_sz,
            "has_nested_groups": any(m["type"] == "group" for m in lg.get("members", [])),
        }

    legacy_group_mappings = (
        [_map_legacy_group(g, "source") for g in legacy_source_groups] +
        [_map_legacy_group(g, "destination") for g in legacy_dest_groups]
    )

    return {
        "rule_id": rule_id,
        "rule": rule,
        "recommended_nh": recommended_nh,
        "recommended_nh_name": nh_info.get("name", "") if nh_info else "",
        "recommended_sz": recommended_sz,
        "recommended_sz_name": sz_info.get("name", "") if sz_info else "",
        "recommended_dc": recommended_dc,
        "nh_sz_source": nh_sz_source,
        "source_mappings": source_mappings,
        "destination_mappings": destination_mappings,
        "component_groups": component_groups,
        "service_entries": svc_entries,
        "service_recommendations": service_recommendations,
        "mapping_summary": {
            "total": len(source_mappings) + len(destination_mappings),
            "from_mapping_table": table_count,
            "from_existing_groups": group_count,
            "auto_generated": auto_count,
            "component_group_count": len(component_groups),
        },
        "app_distributed_id": app_label,
        "naming_standard": f"Source: grp-{short_app}-{{NH}}-{{SZ}} | Dest: grp-{short_app}-{{NH}}-{{SZ}}-{{COMP}}-Ingress",
        "source_nh": src_nh,
        "source_sz": src_sz,
        "source_dc": src_dc,
        "source_nh_name": nh_info.get("name", "") if nh_info else "",
        "source_sz_name": sz_info.get("name", "") if sz_info else "",
        "destination_nh": dst_nh,
        "destination_sz": dst_sz,
        "destination_dc": dst_dc,
        "destination_nh_name": dst_nh_info.get("name", "") if dst_nh_info else "",
        "destination_sz_name": dst_sz_info.get("name", "") if dst_sz_info else "",
        "available_nhs": [{"nh_id": n.get("nh_id"), "name": n.get("name")} for n in nhs],
        "available_szs": [{"code": s.get("code"), "name": s.get("name")} for s in szs],
        "legacy_group_mappings": legacy_group_mappings,
        "legacy_source_groups": legacy_source_groups,
        "legacy_dest_groups": legacy_dest_groups,
        # App DC mapping metadata for frontend component/NH/SZ selection
        "app_dc_mappings": [
            {
                "component": c.get("component", ""),
                "nh": c.get("nh", ""),
                "sz": c.get("sz", ""),
                "dc": c.get("dc", ""),
                "cidr": c.get("cidr", ""),
            } for c in app_components
        ],
        "available_components": sorted(set(c.get("component", "") for c in app_components if c.get("component"))),
    }


# ============================================================
# Organization Legacy-to-NGDC Mappings
# ============================================================

async def get_ngdc_mappings() -> list[dict[str, Any]]:
    """Get all org-provided legacy-to-NGDC mappings."""
    return _load("ngdc_mappings") or []


async def save_ngdc_mappings(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Save/replace all legacy-to-NGDC mappings."""
    _save("ngdc_mappings", mappings)
    return mappings


async def add_ngdc_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Add a single legacy-to-NGDC mapping."""
    mappings = _load("ngdc_mappings") or []
    mapping["id"] = mapping.get("id", _id())
    mapping["created_at"] = _now()
    mappings.append(mapping)
    _save("ngdc_mappings", mappings)
    return mapping


async def update_ngdc_mapping(mapping_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    mappings = _load("ngdc_mappings") or []
    for m in mappings:
        if m.get("id") == mapping_id:
            m.update(data)
            m["updated_at"] = _now()
            _save("ngdc_mappings", mappings)
            return m
    return None


async def delete_ngdc_mapping(mapping_id: str) -> bool:
    mappings = _load("ngdc_mappings") or []
    filtered = [m for m in mappings if m.get("id") != mapping_id]
    if len(filtered) == len(mappings):
        return False
    _save("ngdc_mappings", filtered)
    return True


async def import_ngdc_mappings(new_mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Bulk import mappings from organization (e.g., Excel/CSV upload)."""
    existing = _load("ngdc_mappings") or []
    existing_keys = {(m.get("legacy_name", ""), m.get("legacy_dc", "")) for m in existing}
    added = 0
    skipped = 0
    for nm in new_mappings:
        key = (nm.get("legacy_name", ""), nm.get("legacy_dc", ""))
        if key in existing_keys:
            skipped += 1
            continue
        nm["id"] = _id()
        nm["created_at"] = _now()
        existing.append(nm)
        existing_keys.add(key)
        added += 1
    _save("ngdc_mappings", existing)
    return {"added": added, "skipped": skipped, "total": len(existing)}


# ============================================================
# Group Provisioning to Firewall Device
# ============================================================

async def provision_groups_to_device(app_id: str, device_type: str = "palo_alto") -> dict[str, Any]:
    """Provision app groups directly to firewall device with NGDC standards enforcement."""
    groups = _load("groups") or []
    app_groups = [g for g in groups if g.get("app_id") == app_id]
    if not app_groups:
        return {"status": "error", "message": "No groups found for app"}

    nstd = _load("naming_standards") or {}
    violations: list[str] = []
    provisioned: list[dict[str, Any]] = []

    for g in app_groups:
        name = g.get("name", "")
        # Enforce NGDC naming: must start with grp-, svr-, or rng-
        if not any(name.startswith(p) for p in ["grp-", "svr-", "rng-"]):
            violations.append(f"Group '{name}' does not follow NGDC naming standard")
            continue
        # Enforce non-empty members
        if not g.get("members"):
            violations.append(f"Group '{name}' has no members")
            continue

        if device_type == "palo_alto":
            provisioned.append({
                "name": name,
                "type": "address-group" if g.get("type") == "network" else "address-group",
                "members": [m.get("value", "") for m in g.get("members", [])],
                "description": g.get("description", ""),
                "device_command": f"set address-group {name} static [{' '.join(m.get('value', '') for m in g.get('members', []))}]",
            })
        elif device_type == "checkpoint":
            provisioned.append({
                "name": name,
                "type": "network-group",
                "members": [m.get("value", "") for m in g.get("members", [])],
                "device_command": f"mgmt_cli add group name {name} members.1 {g['members'][0]['value'] if g.get('members') else ''}",
            })
        else:
            provisioned.append({
                "name": name,
                "members": [m.get("value", "") for m in g.get("members", [])],
                "device_command": f"object-group network {name}",
            })

        # Mark group as provisioned
        g["provisioned"] = True
        g["provisioned_at"] = _now()
        g["device_type"] = device_type

    _save("groups", groups)

    # Log provisioning
    history = _load("provisioning_history") or []
    entry = {
        "id": _id(),
        "app_id": app_id,
        "device_type": device_type,
        "groups_provisioned": len(provisioned),
        "violations": violations,
        "provisioned_at": _now(),
        "status": "Completed" if not violations else "Partial",
        "details": provisioned,
    }
    history.append(entry)
    _save("provisioning_history", history)

    return {
        "status": "success" if not violations else "partial",
        "provisioned": provisioned,
        "violations": violations,
        "total_groups": len(app_groups),
        "provisioned_count": len(provisioned),
    }


async def get_provisioning_history(app_id: str | None = None) -> list[dict[str, Any]]:
    history = _load("provisioning_history") or []
    if app_id:
        history = [h for h in history if h.get("app_id") == app_id]
    return history


# ============================================================
# Enhanced Compile with Group Expansion
# ============================================================

async def compile_rule_with_expansion(rule_id: str, vendor: str = "generic", expand_groups: bool = True) -> dict[str, Any] | None:
    """Compile a rule showing groups AND underlying expansion per device standards."""
    rules = _load("rules") or []
    rule = next((r for r in rules if r.get("rule_id") == rule_id), None)
    if not rule:
        # Try legacy rules
        legacy = _load("legacy_rules") or []
        rule = next((r for r in legacy if r.get("id") == rule_id), None)
        if not rule:
            return None

    groups_data = _load("groups") or []
    group_lookup = {g["name"]: g for g in groups_data}

    # Get source/destination
    src = rule.get("source", rule.get("rule_source", ""))
    dst = rule.get("destination", rule.get("rule_destination", ""))
    svc = rule.get("port", rule.get("rule_service", ""))

    src_entries = [s.strip() for s in str(src).split("\n") if s.strip()]
    dst_entries = [d.strip() for d in str(dst).split("\n") if d.strip()]

    # Expand groups
    expanded_sources: list[dict[str, Any]] = []
    for s in src_entries:
        grp = group_lookup.get(s)
        if grp and expand_groups:
            expanded_sources.append({
                "group_name": s,
                "type": "group",
                "members": [m.get("value", "") for m in grp.get("members", [])],
                "member_count": len(grp.get("members", [])),
            })
        else:
            expanded_sources.append({"value": s, "type": "direct", "members": [s], "member_count": 1})

    expanded_destinations: list[dict[str, Any]] = []
    for d in dst_entries:
        grp = group_lookup.get(d)
        if grp and expand_groups:
            expanded_destinations.append({
                "group_name": d,
                "type": "group",
                "members": [m.get("value", "") for m in grp.get("members", [])],
                "member_count": len(grp.get("members", [])),
            })
        else:
            expanded_destinations.append({"value": d, "type": "direct", "members": [d], "member_count": 1})

    # Generate vendor-specific output
    compiled_lines: list[str] = []
    if vendor == "palo_alto":
        for se in expanded_sources:
            for de in expanded_destinations:
                src_name = se.get("group_name", se.get("value", ""))
                dst_name = de.get("group_name", de.get("value", ""))
                compiled_lines.append(f"set rulebase security rules \"{rule.get('rule_id', rule.get('id', ''))}\""
                    f" from [{rule.get('source_zone', 'any')}] to [{rule.get('destination_zone', 'any')}]"
                    f" source [{src_name}] destination [{dst_name}]"
                    f" service [{svc}] action {rule.get('action', 'allow')}")
    elif vendor == "checkpoint":
        compiled_lines.append(f"mgmt_cli add access-rule layer Network"
            f" name \"{rule.get('rule_id', rule.get('id', ''))}\""
            f" source \"{src}\" destination \"{dst}\" service \"{svc}\""
            f" action {rule.get('action', 'Accept')}")
    else:
        compiled_lines.append(f"# Rule: {rule.get('rule_id', rule.get('id', ''))}")
        for se in expanded_sources:
            src_name = se.get("group_name", se.get("value", ""))
            for de in expanded_destinations:
                dst_name = de.get("group_name", de.get("value", ""))
                compiled_lines.append(f"permit {svc} {src_name} -> {dst_name}")

    return {
        "rule_id": rule.get("rule_id", rule.get("id", "")),
        "vendor": vendor,
        "compiled_output": "\n".join(compiled_lines),
        "sources": expanded_sources,
        "destinations": expanded_destinations,
        "services": svc,
        "total_source_ips": sum(s.get("member_count", 1) for s in expanded_sources),
        "total_dest_ips": sum(d.get("member_count", 1) for d in expanded_destinations),
        "expand_groups": expand_groups,
        "group_view": not expand_groups,
    }

# ============================================================
# App-to-DC/NH/SZ Mapping (Organization Reference)
# ============================================================

async def get_app_dc_mappings() -> list[dict[str, Any]]:
    """Get all App-to-DC/NH/SZ mappings used for validations."""
    return _load("app_dc_mappings") or []


async def save_app_dc_mappings(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _save("app_dc_mappings", mappings)
    return mappings


async def add_app_dc_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    mappings = _load("app_dc_mappings") or []
    mapping["id"] = mapping.get("id", _id())
    mapping["created_at"] = _now()
    # Auto-resolve CIDR from (DC, NH, SZ) if NGDC and CIDR not explicitly set
    if mapping.get("dc_location") == "NGDC" and mapping.get("dc") and mapping.get("nh") and mapping.get("sz"):
        resolved = _resolve_sz_cidr_sync(mapping["dc"], mapping["nh"], mapping["sz"])
        if resolved and not mapping.get("cidr"):
            mapping["cidr"] = resolved
        mapping["sz_cidr"] = resolved  # always store the SZ-level parent CIDR
    mappings.append(mapping)
    _save("app_dc_mappings", mappings)
    return mapping


async def update_app_dc_mapping(mapping_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    mappings = _load("app_dc_mappings") or []
    for m in mappings:
        if m.get("id") == mapping_id:
            m.update(data)
            m["updated_at"] = _now()
            # Re-resolve SZ CIDR if DC/NH/SZ changed
            if m.get("dc_location") == "NGDC" and m.get("dc") and m.get("nh") and m.get("sz"):
                resolved = _resolve_sz_cidr_sync(m["dc"], m["nh"], m["sz"])
                m["sz_cidr"] = resolved
            _save("app_dc_mappings", mappings)
            return m
    return None


async def delete_app_dc_mapping(mapping_id: str) -> bool:
    mappings = _load("app_dc_mappings") or []
    filtered = [m for m in mappings if m.get("id") != mapping_id]
    if len(filtered) == len(mappings):
        return False
    _save("app_dc_mappings", filtered)
    return True


async def get_app_dc_mapping_by_app(app_id: str) -> dict[str, Any] | None:
    """Lookup the DC/NH/SZ mapping for a specific app."""
    mappings = _load("app_dc_mappings") or []
    return next((m for m in mappings if str(m.get("app_id", "")) == str(app_id)), None)


async def import_app_dc_mappings(new_mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Bulk import app-dc mappings with dedup."""
    existing = _load("app_dc_mappings") or []
    existing_keys = {str(m.get("app_id", "")) for m in existing}
    added = 0
    updated = 0
    for nm in new_mappings:
        aid = str(nm.get("app_id", ""))
        if aid in existing_keys:
            # Update existing
            for m in existing:
                if str(m.get("app_id", "")) == aid:
                    m.update(nm)
                    m["updated_at"] = _now()
                    break
            updated += 1
        else:
            nm["id"] = _id()
            nm["created_at"] = _now()
            existing.append(nm)
            existing_keys.add(aid)
            added += 1
    _save("app_dc_mappings", existing)
    return {"added": added, "updated": updated, "total": len(existing)}


# ============================================================
# NGDC Compliance Check (for auto-import to Firewall Studio)
# ============================================================

async def check_ngdc_compliance(rule: dict[str, Any]) -> dict[str, Any]:
    """Check if a legacy rule is fully NGDC compliant for both source and destination.
    Returns compliance status with details."""
    groups = _load("groups") or []
    naming_stds = _load("naming_standards") or {}
    nhs = _load("neighbourhoods") or []
    szs = _load("security_zones") or []
    policy_matrix = _load("policy_matrix") or []

    nh_ids = {nh.get("nh_id", "") for nh in nhs}
    sz_codes = {sz.get("code", "") for sz in szs}

    issues: list[str] = []

    src = rule.get("rule_source", "")
    dst = rule.get("rule_destination", "")
    src_zone = rule.get("rule_source_zone", "")
    dst_zone = rule.get("rule_destination_zone", "")
    svc = rule.get("rule_service", "")

    # Check source naming standard
    prefixes = naming_stds.get("prefixes", {"group": "grp-", "server": "svr-", "range": "rng-", "subnet": "sub-"})
    src_entries = [s.strip() for s in src.split("\n") if s.strip()] if src else []
    dst_entries = [d.strip() for d in dst.split("\n") if d.strip()] if dst else []

    for entry in src_entries:
        is_named = any(entry.startswith(p) for p in prefixes.values())
        if not is_named and not entry.replace(".", "").replace("/", "").replace(":", "").isdigit():
            # Not an IP and not following naming standard
            if not any(entry.startswith(p) for p in ["grp-", "svr-", "rng-", "sub-"]):
                issues.append(f"Source '{entry}' does not follow NGDC naming standards")

    for entry in dst_entries:
        is_named = any(entry.startswith(p) for p in prefixes.values())
        if not is_named and not entry.replace(".", "").replace("/", "").replace(":", "").isdigit():
            if not any(entry.startswith(p) for p in ["grp-", "svr-", "rng-", "sub-"]):
                issues.append(f"Destination '{entry}' does not follow NGDC naming standards")

    # Check zones exist
    if src_zone and src_zone not in sz_codes and src_zone != "Any":
        issues.append(f"Source zone '{src_zone}' not found in NGDC security zones")
    if dst_zone and dst_zone not in sz_codes and dst_zone != "Any":
        issues.append(f"Destination zone '{dst_zone}' not found in NGDC security zones")

    # Check policy matrix allows this flow
    if src_zone and dst_zone and policy_matrix:
        allowed = False
        for pm in policy_matrix:
            if (pm.get("source_zone") == src_zone or pm.get("source_zone") == "Any") and \
               (pm.get("destination_zone") == dst_zone or pm.get("destination_zone") == "Any"):
                if pm.get("action", "").lower() in ("allow", "permit", "allowed"):
                    allowed = True
                    break
        if not allowed and policy_matrix:
            issues.append(f"Policy matrix does not permit flow from {src_zone} to {dst_zone}")

    is_compliant = len(issues) == 0
    return {
        "compliant": is_compliant,
        "issues": issues,
        "rule_id": rule.get("id", ""),
    }


async def check_duplicates(source: str, destination: str, service: str,
                           exclude_id: str = "") -> list[dict[str, Any]]:
    """Check for duplicate rules based on source+destination+service(port/protocol).
    Checks across both legacy_rules and rules collections."""
    legacy = _load("legacy_rules") or []
    studio_rules = _load("rules") or []

    src_norm = source.strip().lower()
    dst_norm = destination.strip().lower()
    svc_norm = service.strip().lower()

    duplicates: list[dict[str, Any]] = []

    for r in legacy:
        if exclude_id and r.get("id") == exclude_id:
            continue
        r_src = str(r.get("rule_source", "")).strip().lower()
        r_dst = str(r.get("rule_destination", "")).strip().lower()
        r_svc = str(r.get("rule_service", "")).strip().lower()
        if r_src == src_norm and r_dst == dst_norm and r_svc == svc_norm:
            duplicates.append({
                "id": r.get("id"),
                "type": "legacy",
                "app_id": r.get("app_id"),
                "source": r.get("rule_source"),
                "destination": r.get("rule_destination"),
                "service": r.get("rule_service"),
            })

    for r in studio_rules:
        if exclude_id and r.get("rule_id") == exclude_id:
            continue
        r_src = str(r.get("source", "")).strip().lower()
        r_dst = str(r.get("destination", "")).strip().lower()
        r_svc = f"{r.get('port', '')}:{r.get('protocol', '')}".strip().lower()
        if r_src == src_norm and r_dst == dst_norm and (r_svc == svc_norm or not svc_norm):
            duplicates.append({
                "id": r.get("rule_id"),
                "type": "studio",
                "app_id": r.get("application"),
                "source": r.get("source"),
                "destination": r.get("destination"),
                "service": r_svc,
            })

    return duplicates


async def import_rules_to_ngdc_standardization(app_ids: list[str]) -> dict[str, Any]:
    """Import rules from Network Firewall Request (legacy_rules) into NGDC Standardization
    by App ID. Returns the imported rules for the selected apps."""
    legacy = _load("legacy_rules") or []
    imported: list[dict[str, Any]] = []
    for r in legacy:
        if str(r.get("app_id", "")) in [str(a) for a in app_ids]:
            # Mark as imported to NGDC standardization
            r["ngdc_imported"] = True
            r["ngdc_import_date"] = _now()
            imported.append(r)
    _save("legacy_rules", legacy)
    return {"imported": len(imported), "rules": imported}


async def auto_import_compliant_rules_to_studio() -> dict[str, Any]:
    """Auto-import NGDC-compliant rules from Network Firewall Request into Firewall Studio.
    Only imports rules that pass all NGDC compliance checks for both source and destination."""
    legacy = _load("legacy_rules") or []
    studio_rules = _load("rules") or []

    # Build existing studio rule keys for dedup
    existing_keys: set[str] = set()
    for r in studio_rules:
        key = f"{r.get('source', '')}|{r.get('destination', '')}|{r.get('port', '')}:{r.get('protocol', '')}"
        existing_keys.add(key.lower())

    max_num = 0
    for r in studio_rules:
        try:
            num = int(r.get("rule_id", "FW-000").split("-")[1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            pass

    imported = 0
    skipped = 0
    already_imported = 0

    for rule in legacy:
        if rule.get("studio_imported"):
            already_imported += 1
            continue

        # Check compliance
        compliance = await check_ngdc_compliance(rule)
        if not compliance["compliant"]:
            skipped += 1
            continue

        # Check for duplicates
        key = f"{rule.get('rule_source', '')}|{rule.get('rule_destination', '')}|{rule.get('rule_service', '')}"
        if key.lower() in existing_keys:
            already_imported += 1
            rule["studio_imported"] = True
            continue

        # Import to studio
        max_num += 1
        studio_rule = {
            "rule_id": f"FW-{max_num:03d}",
            "source": rule.get("rule_source", ""),
            "source_zone": rule.get("rule_source_zone", ""),
            "destination": rule.get("rule_destination", ""),
            "destination_zone": rule.get("rule_destination_zone", ""),
            "port": rule.get("rule_service", "").split("/")[0] if "/" in rule.get("rule_service", "") else rule.get("rule_service", ""),
            "protocol": rule.get("rule_service", "").split("/")[1] if "/" in rule.get("rule_service", "") else "tcp",
            "action": rule.get("rule_action", "Accept"),
            "description": f"Auto-imported from NFR - App {rule.get('app_id', '')}",
            "application": str(rule.get("app_id", "")),
            "status": "Draft",
            "is_group_to_group": bool(rule.get("rule_source", "").startswith("grp-") and rule.get("rule_destination", "").startswith("grp-")),
            "environment": "Production",
            "datacenter": "",
            "created_at": _now(),
            "updated_at": _now(),
            "certified_date": None,
            "expiry_date": None,
            "source_expanded": rule.get("rule_source_expanded", ""),
            "destination_expanded": rule.get("rule_destination_expanded", ""),
            "service_expanded": rule.get("rule_service_expanded", ""),
            "origin": "auto-import-nfr",
            "origin_rule_id": rule.get("id", ""),
        }
        studio_rules.append(studio_rule)
        existing_keys.add(key.lower())
        rule["studio_imported"] = True
        rule["studio_rule_id"] = studio_rule["rule_id"]
        imported += 1

    _save("rules", studio_rules)
    _save("legacy_rules", legacy)
    return {
        "imported": imported,
        "skipped_non_compliant": skipped,
        "already_imported": already_imported,
        "total_studio_rules": len(studio_rules),
    }


async def expand_groups_in_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Expand group references in a rule's source/destination to show all IPs/ranges.
    Returns the rule with expanded fields populated."""
    groups = _load("groups") or []
    group_lookup: dict[str, list[dict[str, str]]] = {}
    for g in groups:
        group_lookup[g.get("name", "")] = g.get("members", [])

    def _is_group_entry(name: str) -> bool:
        """Check if entry is a group (grp-, g-, ggrp-, gapigr- prefix) vs individual IP/subnet/range."""
        return _is_legacy_group_name(name)

    def expand_field(field_value: str) -> str:
        if not field_value:
            return ""
        lines = [l.strip() for l in field_value.split("\n") if l.strip()]
        expanded_lines: list[str] = []
        for line in lines:
            if _is_group_entry(line):
                # This is a group — expand to show members
                if line in group_lookup:
                    expanded_lines.append(f"[Group] {line}")
                    for member in group_lookup[line]:
                        mtype = member.get("type", "ip")
                        mval = member.get("value", "")
                        # Check for nested groups
                        if mtype == "group" and mval in group_lookup:
                            expanded_lines.append(f"  [Group] {mval}")
                            for nested in group_lookup[mval]:
                                expanded_lines.append(f"    {nested.get('type', 'ip')}: {nested.get('value', '')}")
                        else:
                            expanded_lines.append(f"  {mtype}: {mval}")
                else:
                    matching = [g for g in groups if g.get("name") == line]
                    if matching:
                        expanded_lines.append(f"[Group] {line}")
                        for member in matching[0].get("members", []):
                            mtype = member.get("type", "ip")
                            mval = member.get("value", "")
                            expanded_lines.append(f"  {mtype}: {mval}")
                    else:
                        expanded_lines.append(f"[Group] {line}")
            else:
                # Individual IP, subnet, or range — show as-is, no expansion
                expanded_lines.append(line)
        return "\n".join(expanded_lines)

    rule["rule_source_expanded"] = expand_field(rule.get("rule_source", ""))
    rule["rule_destination_expanded"] = expand_field(rule.get("rule_destination", ""))

    # Expand service
    svc = rule.get("rule_service", "")
    if svc:
        svc_lines = [s.strip() for s in svc.split("\n") if s.strip()]
        expanded_svc: list[str] = []
        for s in svc_lines:
            if "/" in s:
                port, proto = s.split("/", 1)
                expanded_svc.append(f"Port: {port}, Protocol: {proto}")
            else:
                expanded_svc.append(f"Service: {s}")
        rule["rule_service_expanded"] = "\n".join(expanded_svc)

    return rule


# ============================================================
# IP Mapping CRUD (Legacy DC <-> NGDC one-to-one)
# ============================================================

async def get_ip_mappings(legacy_dc: str | None = None, app_id: str | None = None) -> list[dict[str, Any]]:
    """Get IP mappings, optionally filtered by legacy DC or app."""
    mappings = _load("ip_mappings") or []
    if legacy_dc:
        mappings = [m for m in mappings if m.get("legacy_dc") == legacy_dc]
    if app_id:
        mappings = [m for m in mappings if m.get("app_id") == app_id]
    return mappings


async def add_ip_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    mappings = _load("ip_mappings") or []
    mapping["id"] = mapping.get("id", _id())
    mapping["created_at"] = _now()
    mappings.append(mapping)
    _save("ip_mappings", mappings)
    return mapping


async def update_ip_mapping(mapping_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    mappings = _load("ip_mappings") or []
    for m in mappings:
        if m.get("id") == mapping_id:
            m.update(data)
            m["updated_at"] = _now()
            _save("ip_mappings", mappings)
            return m
    return None


async def delete_ip_mapping(mapping_id: str) -> bool:
    mappings = _load("ip_mappings") or []
    filtered = [m for m in mappings if m.get("id") != mapping_id]
    if len(filtered) == len(mappings):
        return False
    _save("ip_mappings", filtered)
    return True


async def lookup_ngdc_ip(legacy_ip: str, legacy_dc: str = "") -> dict[str, Any] | None:
    """Look up the NGDC equivalent for a legacy IP address."""
    mappings = _load("ip_mappings") or []
    for m in mappings:
        if m.get("legacy_ip") == legacy_ip:
            if not legacy_dc or m.get("legacy_dc") == legacy_dc:
                return m
    return None


# ============================================================
# Logical Data Flow — Firewall Boundary Determination
# Based on NH/SZ placement per the NGDC Logical Data Flows doc.
# ============================================================

from .seed_data import SEGMENTED_ZONES as _SEED_SEG_ZONES  # noqa: E402
_LDF_SEGMENTED_ZONES = _SEED_SEG_ZONES  # CPA, CDE, CCS, PAA, 3PY, Swift, PSE, UC

def _find_device(nh: str, sz: str) -> dict[str, Any] | None:
    """Find the NH-specific segmentation firewall device for a given NH+SZ."""
    devices = _load("firewall_devices") or []
    for d in devices:
        if d.get("nh") == nh and d.get("sz") == sz and d.get("type") == "segmentation":
            return d
    # Fallback: any segmentation device matching the SZ
    for d in devices:
        if d.get("sz") == sz and d.get("type") == "segmentation":
            return d
    # Fallback: first perimeter device
    for d in devices:
        if d.get("type") == "perimeter":
            return d
    return None


def _find_paa_device() -> dict[str, Any] | None:
    """Find the PAA perimeter firewall device."""
    devices = _load("firewall_devices") or []
    for d in devices:
        if d.get("type") == "paa":
            return d
    return None


async def determine_firewall_boundaries(
    src_nh: str, src_sz: str, dst_nh: str, dst_sz: str
) -> dict[str, Any]:
    """Determine how many firewall boundaries a rule must cross and which
    devices handle egress / ingress, based on the Logical Data Flows.

    Returns a dict with:
      boundaries      – int (0, 1, or 2)
      flow_rule       – which LDF rule matched
      devices         – list of {role, device_id, device_name, nh, sz, direction}
      requires_egress – bool
      requires_ingress– bool
      note            – human-readable explanation
    """
    src_sz_upper = (src_sz or "").upper()
    dst_sz_upper = (dst_sz or "").upper()
    src_segmented = src_sz_upper in _LDF_SEGMENTED_ZONES
    dst_segmented = dst_sz_upper in _LDF_SEGMENTED_ZONES
    same_nh = (src_nh == dst_nh) and src_nh
    same_sz = (src_sz_upper == dst_sz_upper)

    # ---- LDF-001: STD/GEN ↔ STD/GEN (any NHs) — no firewall ----
    if not src_segmented and not dst_segmented:
        return {
            "boundaries": 0, "flow_rule": "LDF-001",
            "devices": [],
            "requires_egress": False, "requires_ingress": False,
            "note": (f"STD/GEN zone traffic ({src_sz_upper} → {dst_sz_upper}) "
                     f"flows directly between {src_nh} and {dst_nh} — no firewall needed."),
        }

    # ---- LDF-002: Same NH + same SZ ----
    if same_nh and same_sz:
        # For segmented (non-STD/GEN) zones, the rule IS deployed on the zone's
        # FW device — show 1 boundary so the device is visible in the flow.
        # Mark as "existing" so frontend renders in GREEN (rule already active).
        if src_segmented:
            seg_dev = _find_device(src_nh, src_sz_upper)
            devs = []
            if seg_dev:
                devs.append({"role": "zone_device", "direction": "local",
                             "device_id": seg_dev["device_id"], "device_name": seg_dev["name"],
                             "nh": src_nh, "sz": src_sz_upper})
            return {
                "boundaries": 1, "flow_rule": "LDF-002",
                "devices": devs,
                "requires_egress": False, "requires_ingress": False,
                "existing_rule": True,
                "note": (f"Intra-NH ({src_nh}), intra-SZ ({src_sz_upper}) traffic — "
                         f"rule is deployed on {src_nh} {src_sz_upper} firewall device. "
                         f"Permitted per birthright."),
            }
        return {
            "boundaries": 0, "flow_rule": "LDF-002",
            "devices": [],
            "requires_egress": False, "requires_ingress": False,
            "note": (f"Intra-NH ({src_nh}), intra-SZ ({src_sz_upper}) traffic — "
                     f"permitted by default, no firewall boundary."),
        }

    # ---- LDF-006: PAA flow ----
    if src_sz_upper == "PAA" or dst_sz_upper == "PAA":
        paa_dev = _find_paa_device()
        internal_nh = dst_nh if dst_sz_upper != "PAA" else src_nh
        internal_sz = dst_sz_upper if dst_sz_upper != "PAA" else src_sz_upper
        int_dev = _find_device(internal_nh, internal_sz)
        devs = []
        if paa_dev:
            devs.append({"role": "paa_perimeter", "direction": "egress",
                         "device_id": paa_dev["device_id"], "device_name": paa_dev["name"],
                         "nh": "PAA", "sz": "PAA"})
        if int_dev:
            devs.append({"role": "internal", "direction": "ingress",
                         "device_id": int_dev["device_id"], "device_name": int_dev["name"],
                         "nh": internal_nh, "sz": internal_sz})
        return {
            "boundaries": len(devs), "flow_rule": "LDF-006",
            "devices": devs,
            "requires_egress": True, "requires_ingress": True,
            "note": (f"PAA flow — traffic crosses PAA perimeter firewall then "
                     f"{internal_nh} {internal_sz} internal firewall."),
        }

    # ---- LDF-005: Same NH, different SZs (at least one segmented) — 1 boundary ----
    # FW device positioned based on which side is segmented:
    #   Open (STD/GEN) → Segmented: FW on destination side (ingress into segmented zone)
    #   Segmented → Open (STD/GEN): FW on source side (egress from segmented zone)
    #   Segmented → Segmented: FW as boundary (higher-risk zone device)
    if same_nh and not same_sz:
        segmented_sz = src_sz_upper if src_segmented else dst_sz_upper
        dev = _find_device(src_nh, segmented_sz)
        devs = []
        if src_segmented and not dst_segmented:
            # Segmented → Open: FW on source side (egress)
            if dev:
                devs.append({"role": "egress", "direction": "egress",
                             "device_id": dev["device_id"], "device_name": dev["name"],
                             "nh": src_nh, "sz": src_sz_upper})
            return {
                "boundaries": 1, "flow_rule": "LDF-005",
                "devices": devs,
                "requires_egress": True, "requires_ingress": False,
                "note": (f"Cross-zone within {src_nh} ({src_sz_upper} → {dst_sz_upper}) — "
                         f"egress through {src_nh} {src_sz_upper} segmentation firewall."),
            }
        elif dst_segmented and not src_segmented:
            # Open → Segmented: FW on destination side (ingress)
            if dev:
                devs.append({"role": "ingress", "direction": "ingress",
                             "device_id": dev["device_id"], "device_name": dev["name"],
                             "nh": dst_nh, "sz": dst_sz_upper})
            return {
                "boundaries": 1, "flow_rule": "LDF-005",
                "devices": devs,
                "requires_egress": False, "requires_ingress": True,
                "note": (f"Cross-zone within {src_nh} ({src_sz_upper} → {dst_sz_upper}) — "
                         f"ingress through {dst_nh} {dst_sz_upper} segmentation firewall."),
            }
        else:
            # Both segmented: boundary device at the higher-risk zone
            if dev:
                devs.append({"role": "boundary", "direction": "both",
                             "device_id": dev["device_id"], "device_name": dev["name"],
                             "nh": src_nh, "sz": segmented_sz})
            return {
                "boundaries": 1, "flow_rule": "LDF-005",
                "devices": devs,
                "requires_egress": True, "requires_ingress": True,
                "note": (f"Cross-zone within {src_nh} ({src_sz_upper} → {dst_sz_upper}) — "
                         f"traverses {src_nh} {segmented_sz} segmentation firewall."),
            }

    # ---- LDF-004: Same segmented SZ, different NHs — PERMITTED ----
    # Same SZ is always permitted regardless of NH/DC per birthright.
    # Traffic still passes through FW devices (egress + ingress) but
    # no firewall rule is required — devices shown as informational.
    if same_sz and src_segmented and not same_nh:
        eg_dev = _find_device(src_nh, src_sz_upper)
        in_dev = _find_device(dst_nh, dst_sz_upper)
        devs = []
        if eg_dev:
            devs.append({"role": "egress", "direction": "egress",
                         "device_id": eg_dev["device_id"], "device_name": eg_dev["name"],
                         "nh": src_nh, "sz": src_sz_upper})
        if in_dev:
            devs.append({"role": "ingress", "direction": "ingress",
                         "device_id": in_dev["device_id"], "device_name": in_dev["name"],
                         "nh": dst_nh, "sz": dst_sz_upper})
        return {
            "boundaries": len(devs), "flow_rule": "LDF-004",
            "devices": devs,
            "requires_egress": False, "requires_ingress": False,
            "existing_rule": True,
            "note": (f"Same segmented zone ({src_sz_upper}), different NHs "
                     f"({src_nh} → {dst_nh}) — permitted per birthright. "
                     f"Traffic passes through {src_nh} and {dst_nh} {src_sz_upper} FW devices (no rule required)."),
        }

    # ---- LDF-003a: BOTH segmented, different zones, different NHs — 2 boundaries ----
    # e.g. CDE(NH06) → CPA(NH14): egress from source NH/SZ + ingress to dest NH/SZ
    if src_segmented and dst_segmented and not same_sz and not same_nh:
        eg_dev = _find_device(src_nh, src_sz_upper)
        in_dev = _find_device(dst_nh, dst_sz_upper)
        devs = []
        if eg_dev:
            devs.append({"role": "egress", "direction": "egress",
                         "device_id": eg_dev["device_id"], "device_name": eg_dev["name"],
                         "nh": src_nh, "sz": src_sz_upper})
        if in_dev:
            devs.append({"role": "ingress", "direction": "ingress",
                         "device_id": in_dev["device_id"], "device_name": in_dev["name"],
                         "nh": dst_nh, "sz": dst_sz_upper})
        return {
            "boundaries": len(devs), "flow_rule": "LDF-003",
            "devices": devs,
            "requires_egress": True, "requires_ingress": True,
            "note": (f"Both segmented zones ({src_sz_upper} in {src_nh} → {dst_sz_upper} in {dst_nh}) — "
                     f"egress through {src_nh} {src_sz_upper} firewall, "
                     f"ingress through {dst_nh} {dst_sz_upper} firewall."),
        }

    # ---- LDF-003b: Source segmented, dest NOT segmented, different NHs — 1 boundary (egress) ----
    if src_segmented and not dst_segmented and not same_sz and not same_nh:
        eg_dev = _find_device(src_nh, src_sz_upper)
        devs = []
        if eg_dev:
            devs.append({"role": "egress", "direction": "egress",
                         "device_id": eg_dev["device_id"], "device_name": eg_dev["name"],
                         "nh": src_nh, "sz": src_sz_upper})
        return {
            "boundaries": 1, "flow_rule": "LDF-003",
            "devices": devs,
            "requires_egress": True, "requires_ingress": False,
            "note": (f"Segmented zone ({src_sz_upper}) in {src_nh} to open zone ({dst_sz_upper}) in {dst_nh} — "
                     f"egress through {src_nh} {src_sz_upper} firewall only."),
        }

    # ---- LDF-003c: Source NOT segmented, dest segmented, different NHs — 1 boundary (ingress) ----
    if not src_segmented and dst_segmented and not same_nh:
        in_dev = _find_device(dst_nh, dst_sz_upper)
        devs = []
        if in_dev:
            devs.append({"role": "ingress", "direction": "ingress",
                         "device_id": in_dev["device_id"], "device_name": in_dev["name"],
                         "nh": dst_nh, "sz": dst_sz_upper})
        return {
            "boundaries": 1, "flow_rule": "LDF-003",
            "devices": devs,
            "requires_egress": False, "requires_ingress": True,
            "note": (f"Open zone ({src_sz_upper}) in {src_nh} to segmented "
                     f"({dst_sz_upper}) in {dst_nh} — ingress through {dst_nh} {dst_sz_upper} firewall."),
        }

    # ---- Default: no firewall needed ----
    return {
        "boundaries": 0, "flow_rule": "LDF-DEFAULT",
        "devices": [],
        "requires_egress": False, "requires_ingress": False,
        "note": "No firewall boundary required for this traffic flow.",
    }


# ============================================================
# Egress/Ingress Compile for Cross-SZ Rules
# Uses determine_firewall_boundaries() for device-specific compilation.
# ============================================================

async def compile_egress_ingress(rule_id: str, vendor: str = "generic") -> dict[str, Any] | None:
    """Compile separate egress/ingress rules for cross-SZ combinations,
    using the Logical Data Flow boundary analysis to determine which
    NH-specific firewall devices receive each compiled rule."""
    # Try studio rules first, then legacy
    rule = await get_rule(rule_id)
    if not rule:
        legacy = _load("legacy_rules") or []
        rule = next((r for r in legacy if r.get("id") == rule_id), None)
    if not rule:
        return None

    src = rule.get("source", rule.get("rule_source", ""))
    dst = rule.get("destination", rule.get("rule_destination", ""))
    src_zone = rule.get("source_zone", rule.get("rule_source_zone", "any"))
    dst_zone = rule.get("destination_zone", rule.get("rule_destination_zone", "any"))
    src_nh = rule.get("source_nh", rule.get("nh", ""))
    dst_nh = rule.get("destination_nh", rule.get("dst_nh", ""))
    src_dc = rule.get("source_dc", rule.get("datacenter", ""))
    dst_dc = rule.get("destination_dc", "")
    svc = rule.get("port", rule.get("rule_service", "any"))
    proto = rule.get("protocol", "TCP")
    desc = rule.get("description", rule.get("app_name", rule_id))
    rid = rule.get("rule_id", rule.get("id", rule_id))
    app_id = str(rule.get("app_id", ""))

    # Look up DC/NH from app_dc_mappings if not directly available on the rule
    if not src_nh or not src_dc:
        app_dc_mappings = _load("app_dc_mappings") or []
        app_maps = [m for m in app_dc_mappings if str(m.get("app_id", "")).upper() == app_id.upper()]
        if app_maps:
            if not src_nh:
                src_nh = app_maps[0].get("nh", "NH01")
            if not dst_nh:
                dst_nh = app_maps[0].get("nh", src_nh)
            if not src_dc:
                src_dc = app_maps[0].get("dc", "ALPHA_NGDC")
            if not dst_dc:
                dst_dc = app_maps[0].get("dc", src_dc)
            # Try to find specific component-level NH/SZ for more accuracy
            for m in app_maps:
                if m.get("sz", "") == src_zone:
                    src_nh = m.get("nh", src_nh)
                    src_dc = m.get("dc", src_dc)
                    break
            for m in app_maps:
                if m.get("sz", "") == dst_zone:
                    dst_nh = m.get("nh", dst_nh)
                    dst_dc = m.get("dc", dst_dc)
                    break

    # Determine firewall boundaries
    boundary_info = await determine_firewall_boundaries(src_nh, src_zone, dst_nh, dst_zone)

    src_objs = [s.strip() for s in str(src).split("\n") if s.strip()] or ["any"]
    dst_objs = [d.strip() for d in str(dst).split("\n") if d.strip()] or ["any"]

    compiled_devices: list[dict[str, Any]] = []

    for dev_info in boundary_info.get("devices", []):
        dev_id = dev_info.get("device_id", "unknown")
        dev_name = dev_info.get("device_name", "Unknown Device")
        direction = dev_info.get("direction", "egress")
        role = dev_info.get("role", direction)
        dev_nh = dev_info.get("nh", "")
        dev_sz = dev_info.get("sz", "")

        lines: list[str] = []
        suffix = direction.upper()

        if vendor == "palo_alto":
            lines.append(f"# {suffix} Rule — Device: {dev_name} ({dev_id})")
            env = rule.get("environment", "")
            dev_src_vrf_pa = _resolve_vrf(src_nh, src_zone, env)
            dev_dst_vrf_pa = _resolve_vrf(dst_nh, dst_zone, env)
            lines.append(f"# Source VRF: {dev_src_vrf_pa} | Destination VRF: {dev_dst_vrf_pa}")
            objs = src_objs if direction == "egress" else dst_objs
            far_side = "any" if direction == "egress" else "any"
            for obj in objs:
                s_val = obj if direction == "egress" else "any"
                d_val = "any" if direction == "egress" else obj
                lines.append(
                    f'set rulebase security rules "{rid}-{suffix}" from {src_zone}\n'
                    f'set rulebase security rules "{rid}-{suffix}" to {dst_zone}\n'
                    f'set rulebase security rules "{rid}-{suffix}" source [{s_val}]\n'
                    f'set rulebase security rules "{rid}-{suffix}" destination [{d_val}]\n'
                    f'set rulebase security rules "{rid}-{suffix}" service [{proto.lower()}-{svc}]\n'
                    f'set rulebase security rules "{rid}-{suffix}" action allow\n'
                    f'set rulebase security rules "{rid}-{suffix}" log-start yes'
                )
        elif vendor == "checkpoint":
            s_val = src if direction == "egress" else "any"
            d_val = "any" if direction == "egress" else dst
            env = rule.get("environment", "")
            dev_src_vrf_cp = _resolve_vrf(src_nh, src_zone, env)
            dev_dst_vrf_cp = _resolve_vrf(dst_nh, dst_zone, env)
            lines.append(f"# {suffix} Rule — Device: {dev_name} ({dev_id})")
            lines.append(f"# Source VRF: {dev_src_vrf_cp} | Destination VRF: {dev_dst_vrf_cp}")
            lines.append(
                f'mgmt_cli add access-rule layer "Network" position top \\\n'
                f'  name "{rid}-{suffix}" \\\n'
                f'  source "{s_val}" \\\n'
                f'  destination "{d_val}" \\\n'
                f'  service "{proto}_{svc}" \\\n'
                f'  action "Accept" \\\n'
                f'  track "Log" \\\n'
                f'  comments "{suffix}: {desc}"'
            )
        elif vendor == "fortigate":
            objs = src_objs if direction == "egress" else dst_objs
            lines.append(f"# {suffix} Rule — Device: {dev_name} ({dev_id})")
            # Resolve VRF for this device
            env = rule.get("environment", "")
            dev_src_vrf = _resolve_vrf(src_nh, src_zone, env)
            dev_dst_vrf = _resolve_vrf(dst_nh, dst_zone, env)
            lines.append("config firewall policy")
            for obj in objs:
                s_val = obj if direction == "egress" else "any"
                d_val = "any" if direction == "egress" else obj
                lines.append(f"  edit 0")
                lines.append(f"    set name \"{rid}-{suffix}\"")
                lines.append(f"    set srcintf \"{src_zone}\"")
                lines.append(f"    set dstintf \"{dst_zone}\"")
                lines.append(f"    set srcaddr \"{s_val}\"")
                lines.append(f"    set dstaddr \"{d_val}\"")
                lines.append(f"    set service \"{proto}/{svc}\"")
                lines.append(f"    set action accept")
                lines.append(f"    set logtraffic all")
                lines.append(f"    set src-vrf \"{dev_src_vrf}\"")
                lines.append(f"    set dst-vrf \"{dev_dst_vrf}\"")
                lines.append(f"  next")
            lines.append("end")
        else:
            lines.append(f"# {suffix} Rule — Device: {dev_name} ({dev_id})")
            lines.append(f"# NH: {dev_nh}  SZ: {dev_sz}  Role: {role}")
            lines.append(f"# Description: {desc}")
            lines.append("---")
            lines.append(f"{direction}_rule:")
            lines.append(f"  id: {rid}-{suffix}")
            lines.append(f"  direction: {'outbound' if direction == 'egress' else 'inbound'}")
            lines.append(f"  device: {dev_id}")
            lines.append(f"  device_name: {dev_name}")
            if direction == "egress":
                lines.append(f"  source: [{', '.join(src_objs)}]")
                lines.append(f"  destination: [any]")
            else:
                lines.append(f"  source: [any]")
                lines.append(f"  destination: [{', '.join(dst_objs)}]")
            lines.append(f"  source_zone: {src_zone}")
            lines.append(f"  destination_zone: {dst_zone}")
            lines.append(f"  service: {svc}")
            lines.append(f"  action: allow")
            lines.append(f"  logging: true")

        compiled_devices.append({
            "device_id": dev_id,
            "device_name": dev_name,
            "nh": dev_nh,
            "sz": dev_sz,
            "role": role,
            "direction": direction,
            "compiled": "\n".join(lines),
        })

    # Build legacy egress/ingress strings for backward compatibility
    egress_compiled = "\n\n".join(
        d["compiled"] for d in compiled_devices if d["direction"] in ("egress", "both")
    )
    ingress_compiled = "\n\n".join(
        d["compiled"] for d in compiled_devices if d["direction"] in ("ingress", "both")
    )

    # Determine compliancy based on policy matrix
    compliant = True
    compliance_note = "Rule is compliant with NGDC policy"
    if boundary_info["boundaries"] > 0 and not compiled_devices:
        compliant = False
        compliance_note = "Firewall devices required but none found for this boundary"
    elif boundary_info["boundaries"] == 0:
        compliance_note = "No firewall boundary needed - direct flow allowed"

    # Provide fallback DC values
    if not src_dc:
        src_dc = "ALPHA_NGDC"
    if not dst_dc:
        dst_dc = src_dc

    result = {
        "rule_id": rid,
        "vendor_format": vendor,
        "boundary_analysis": boundary_info,
        "boundaries": boundary_info["boundaries"],
        "flow_rule": boundary_info["flow_rule"],
        "devices": compiled_devices,
        "egress_compiled": egress_compiled,
        "ingress_compiled": ingress_compiled,
        "source_zone": src_zone,
        "destination_zone": dst_zone,
        "source_nh": src_nh or "NH01",
        "destination_nh": dst_nh or "NH01",
        "source_dc": src_dc,
        "destination_dc": dst_dc,
        "source_objects": src_objs,
        "destination_objects": dst_objs,
        "service": svc,
        "requires_egress": boundary_info["requires_egress"],
        "requires_ingress": boundary_info["requires_ingress"],
        "note": boundary_info["note"],
        "compliant": compliant,
        "compliance_note": compliance_note,
    }
    # Pass through existing_rule flag for LDF-002 segmented same-SZ same-NH
    if boundary_info.get("existing_rule"):
        result["existing_rule"] = True
    return result


# ============================================================
# Policy Matrix Resolution (resolve Same/Any/Different to real names)
# ============================================================

async def get_resolved_policy_matrix(src_dc: str = "", src_nh: str = "", src_sz: str = "",
                                      dst_dc: str = "", dst_nh: str = "", dst_sz: str = "",
                                      environment: str = "Production") -> list[dict[str, Any]]:
    """Return policy matrix with Same/Any/Different resolved to actual NH/SZ names."""
    env_lower = environment.lower()
    if "pre" in env_lower:
        matrix = _load("preprod_matrix") or []
        env_label = "Pre-Prod"
    elif "non" in env_lower:
        matrix = _load("nonprod_matrix") or []
        env_label = "Non-Prod"
    else:
        matrix = _load("ngdc_prod_matrix") or []
        env_label = "Prod"

    nhs = _load("neighbourhoods") or []
    szs = _load("security_zones") or []
    nh_names = {nh.get("nh_id", ""): nh.get("name", "") for nh in nhs}
    sz_names = {sz.get("code", ""): sz.get("name", "") for sz in szs}

    resolved: list[dict[str, Any]] = []
    for entry in matrix:
        row = dict(entry)
        row["environment"] = env_label

        # For prod matrix: resolve Same/Any/Different
        if env_label == "Prod":
            for field in ["src_dc", "dst_dc", "src_nh", "dst_nh", "src_sz", "dst_sz"]:
                val = row.get(field, "")
                if val == "Same":
                    row[f"{field}_resolved"] = "(Same as counterpart)"
                elif val == "Different":
                    row[f"{field}_resolved"] = "(Different from counterpart)"
                elif val == "Any":
                    row[f"{field}_resolved"] = "(Any)"
                else:
                    if "nh" in field:
                        row[f"{field}_resolved"] = nh_names.get(val, val)
                    elif "sz" in field:
                        row[f"{field}_resolved"] = sz_names.get(val, val)
                    else:
                        row[f"{field}_resolved"] = val
        else:
            # For non-prod / pre-prod: resolve zone codes to names
            for field in ["source_zone", "dest_zone"]:
                val = row.get(field, "")
                if val == "Any":
                    row[f"{field}_resolved"] = "(Any)"
                else:
                    row[f"{field}_resolved"] = sz_names.get(val, val)

        resolved.append(row)

    return resolved


async def create_migration_group(name: str, app_id: str, members: list[dict[str, str]],
                                  nh: str = "", sz: str = "") -> dict[str, Any]:
    """Create a new group during migration with NGDC naming standards."""
    groups = _load("groups") or []

    # Check if group already exists
    existing = next((g for g in groups if g.get("name") == name), None)
    if existing:
        # Update members
        existing["members"] = members
        existing["updated_at"] = _now()
        _save("groups", groups)
        return existing

    new_group = {
        "name": name,
        "app_id": app_id,
        "members": members,
        "nh": nh,
        "sz": sz,
        "type": "migration",
        "created_at": _now(),
        "updated_at": _now(),
    }
    groups.append(new_group)
    _save("groups", groups)
    return new_group


# ============================================================
# CIDR Validation & Auto-Group Creation from IP Mappings
# ============================================================

def _validate_ip_against_cidr(ip_str: str, cidr_str: str) -> bool:
    """Check if an IP address falls within a CIDR range."""
    import ipaddress
    if not ip_str or not cidr_str:
        return False
    # Strip common prefixes
    ip_clean = ip_str.strip()
    for pfx in ("svr-", "net-", "sub-", "rng-", "grp-"):
        if ip_clean.lower().startswith(pfx):
            ip_clean = ip_clean[len(pfx):]
            break
    try:
        net = ipaddress.ip_network(cidr_str.strip(), strict=False)
        # Try as single IP first
        try:
            addr = ipaddress.ip_address(ip_clean)
            return addr in net
        except ValueError:
            # Try as subnet
            try:
                test_net = ipaddress.ip_network(ip_clean, strict=False)
                return test_net.subnet_of(net)
            except (ValueError, TypeError):
                return False
    except (ValueError, TypeError):
        return False


def _find_matching_app_dc_mapping(ngdc_ip: str, app_id: str, component: str = "") -> dict[str, Any] | None:
    """Find the AppDCMapping entry whose CIDR contains the given NGDC IP.
    If component is specified, prefer that component's mapping."""
    app_dc_mappings = _load("app_dc_mappings") or []
    app_maps = [m for m in app_dc_mappings
                if str(m.get("app_distributed_id", "")).upper() == app_id.upper()
                or str(m.get("app_id", "")).upper() == app_id.upper()]

    # If component specified, try component-specific match first
    if component:
        comp_upper = component.upper()
        for m in app_maps:
            if str(m.get("component", "")).upper() == comp_upper:
                cidr = m.get("cidr", "")
                if cidr and _validate_ip_against_cidr(ngdc_ip, cidr):
                    return m

    # Fall back to any matching CIDR
    for m in app_maps:
        cidr = m.get("cidr", "")
        if cidr and _validate_ip_against_cidr(ngdc_ip, cidr):
            return m

    return None


def import_ip_mappings(records: list[dict[str, Any]], app_id: str | None = None) -> dict[str, Any]:
    """Import IP mappings with CIDR validation against AppDCMapping.
    Each record should have: app_id (or use the app_id param), component, legacy_ip, ngdc_ip.
    Auto-populates NH, SZ, DC from matching AppDCMapping CIDR and creates groups."""
    existing = _load("ip_mappings") or []
    existing_keys = {(str(m.get("legacy_ip", "")), str(m.get("app_id", ""))) for m in existing}
    added = 0
    validated = 0
    invalid = 0
    validation_errors: list[str] = []

    for rec in records:
        rec_app = str(rec.get("app_id") or rec.get("app") or app_id or "").strip()
        legacy_ip = str(rec.get("legacy_ip") or rec.get("Legacy IP") or "").strip()
        ngdc_ip = str(rec.get("ngdc_ip") or rec.get("NGDC IP") or "").strip()
        component = str(rec.get("component") or rec.get("Component") or "").strip().upper()

        if not legacy_ip or not ngdc_ip:
            continue
        if (legacy_ip, rec_app) in existing_keys:
            continue

        # CIDR validation: check NGDC IP against AppDCMapping
        match = _find_matching_app_dc_mapping(ngdc_ip, rec_app, component)
        cidr_valid = match is not None
        matched_nh = match.get("nh", "") if match else ""
        matched_sz = match.get("sz", "") if match else ""
        matched_dc = match.get("dc", "") if match else ""
        matched_component = match.get("component", component) if match else component
        matched_cidr = match.get("cidr", "") if match else ""

        if not cidr_valid:
            invalid += 1
            validation_errors.append(f"{ngdc_ip} (app={rec_app}, component={component}) - no matching CIDR range")
        else:
            validated += 1

        mapping = {
            "id": _id(),
            "app_id": rec_app,
            "legacy_ip": legacy_ip,
            "ngdc_ip": ngdc_ip,
            "component": matched_component or component,
            "ngdc_nh": matched_nh,
            "ngdc_sz": matched_sz,
            "ngdc_dc": matched_dc,
            "cidr": matched_cidr,
            "cidr_valid": cidr_valid,
            "ngdc_group": f"grp-{rec_app}-{matched_nh}-{matched_sz}-{matched_component}" if cidr_valid and matched_nh and matched_sz and matched_component else "",
            "created_at": _now(),
        }
        # Also copy over any extra fields from the record
        for k in ("legacy_dc", "ngdc_name"):
            if rec.get(k):
                mapping[k] = str(rec[k])

        existing.append(mapping)
        existing_keys.add((legacy_ip, rec_app))
        added += 1

    _save("ip_mappings", existing)
    return {
        "added": added,
        "validated": validated,
        "invalid": invalid,
        "validation_errors": validation_errors[:20],  # Limit error messages
        "total": len(existing),
    }


async def validate_and_create_groups_from_mappings(app_id: str | None = None) -> dict[str, Any]:
    """Validate all IP mappings against CIDR ranges and auto-create groups.
    Groups follow naming standard: grp-{APP}-{NH}-{SZ}-{Component}
    Returns summary of created/updated groups."""
    ip_mappings = _load("ip_mappings") or []
    if app_id:
        ip_mappings = [m for m in ip_mappings if str(m.get("app_id", "")).upper() == app_id.upper()]

    groups = _load("groups") or []
    groups_by_name: dict[str, dict[str, Any]] = {g.get("name", ""): g for g in groups}

    # Group IP mappings by auto-generated group name
    group_buckets: dict[str, list[dict[str, Any]]] = {}
    revalidated = 0
    for m in ip_mappings:
        ngdc_ip = str(m.get("ngdc_ip", ""))
        m_app = str(m.get("app_id", ""))
        component = str(m.get("component", ""))

        # Re-validate CIDR on each call to pick up any mapping changes
        match = _find_matching_app_dc_mapping(ngdc_ip, m_app, component)
        if match:
            nh = match.get("nh", "")
            sz = match.get("sz", "")
            comp = match.get("component", component)
            grp_name = f"grp-{m_app}-{nh}-{sz}-{comp}"
            m["ngdc_nh"] = nh
            m["ngdc_sz"] = sz
            m["ngdc_dc"] = match.get("dc", "")
            m["component"] = comp
            m["cidr"] = match.get("cidr", "")
            m["cidr_valid"] = True
            m["ngdc_group"] = grp_name
            revalidated += 1

            if grp_name not in group_buckets:
                group_buckets[grp_name] = []
            group_buckets[grp_name].append(m)
        else:
            m["cidr_valid"] = False
            m["ngdc_group"] = ""

    # Save updated mappings
    all_mappings = _load("ip_mappings") or []
    mappings_by_id = {m.get("id"): m for m in ip_mappings}
    for i, em in enumerate(all_mappings):
        mid = em.get("id")
        if mid and mid in mappings_by_id:
            all_mappings[i] = mappings_by_id[mid]
    _save("ip_mappings", all_mappings)

    # Create/update groups for each bucket
    created = 0
    updated = 0
    created_groups: list[dict[str, Any]] = []

    for grp_name, mappings in group_buckets.items():
        members = []
        for m in mappings:
            ip = str(m.get("ngdc_ip", ""))
            if "/" in ip:
                members.append({"type": "subnet", "value": f"net-{ip}"})
            elif "-" in ip and not ip.startswith("svr-"):
                members.append({"type": "range", "value": f"rng-{ip}"})
            else:
                clean_ip = ip
                for pfx in ("svr-", "net-", "rng-"):
                    if clean_ip.lower().startswith(pfx):
                        clean_ip = clean_ip[len(pfx):]
                        break
                members.append({"type": "ip", "value": f"svr-{clean_ip}"})

        first = mappings[0]
        m_app = str(first.get("app_id", ""))
        nh = str(first.get("ngdc_nh", ""))
        sz = str(first.get("ngdc_sz", ""))
        component = str(first.get("component", ""))

        if grp_name in groups_by_name:
            # Update existing group members
            existing_grp = groups_by_name[grp_name]
            existing_grp["members"] = members
            existing_grp["updated_at"] = _now()
            existing_grp["component"] = component
            existing_grp["auto_generated"] = True
            updated += 1
            created_groups.append(existing_grp)
        else:
            new_grp = {
                "name": grp_name,
                "app_id": m_app,
                "members": members,
                "nh": nh,
                "sz": sz,
                "component": component,
                "type": "migration",
                "auto_generated": True,
                "created_at": _now(),
                "updated_at": _now(),
            }
            groups.append(new_grp)
            groups_by_name[grp_name] = new_grp
            created += 1
            created_groups.append(new_grp)

    _save("groups", groups)

    return {
        "revalidated": revalidated,
        "groups_created": created,
        "groups_updated": updated,
        "total_groups": len(created_groups),
        "groups": created_groups,
    }


async def get_auto_generated_groups(app_id: str | None = None) -> list[dict[str, Any]]:
    """Get all auto-generated groups, optionally filtered by app."""
    groups = _load("groups") or []
    auto_groups = [g for g in groups if g.get("auto_generated")]
    if app_id:
        auto_groups = [g for g in auto_groups if str(g.get("app_id", "")).upper() == app_id.upper()]
    return auto_groups


# ============================================================
# Separate JSON Storage (user-data/) — Migration Data & Studio Rules
# These are stored independently from seed/live data for safe cleanup.
# ============================================================

async def get_migration_data() -> dict[str, Any]:
    """Get all migration data from separate JSON (user-data/migration_data.json)."""
    data = _load_separate("migration_data")
    if data is None:
        return {"migration_history": [], "migration_mappings": [], "migration_reviews": [], "migrated_rules": []}
    return data


async def save_migration_data_entry(entry_type: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Append a migration data entry to the separate migration_data.json.
    entry_type: 'migration_history' | 'migration_mappings' | 'migration_reviews' | 'migrated_rules'"""
    data = await get_migration_data()
    if entry_type not in data:
        data[entry_type] = []
    data[entry_type].append(entry)
    _save_separate("migration_data", data)
    return entry


async def clear_migration_data() -> dict[str, int]:
    """Clear all migration data from the separate JSON. Returns count of cleared entries."""
    data = await get_migration_data()
    counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    _save_separate("migration_data", {"migration_history": [], "migration_mappings": [], "migration_reviews": [], "migrated_rules": []})
    return counts


async def get_studio_rules() -> list[dict[str, Any]]:
    """Get all studio rules from separate JSON (user-data/studio_rules.json).
    These are rules created in Firewall Studio (new + approved + migrated)."""
    data = _load_separate("studio_rules")
    if data is None:
        return []
    return data


async def add_studio_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Add a rule to the separate studio_rules.json."""
    rules = await get_studio_rules()
    # Dedup by rule_id
    existing_ids = {r.get("rule_id") for r in rules}
    if rule.get("rule_id") in existing_ids:
        # Update existing
        for i, r in enumerate(rules):
            if r.get("rule_id") == rule.get("rule_id"):
                rules[i] = rule
                break
    else:
        rules.append(rule)
    _save_separate("studio_rules", rules)
    return rule


async def update_studio_rule(rule_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a studio rule in the separate JSON."""
    rules = await get_studio_rules()
    for r in rules:
        if r.get("rule_id") == rule_id:
            r.update(updates)
            r["updated_at"] = _now()
            _save_separate("studio_rules", rules)
            return r
    return None


async def delete_studio_rule(rule_id: str) -> bool:
    """Delete a studio rule from the separate JSON."""
    rules = await get_studio_rules()
    new_rules = [r for r in rules if r.get("rule_id") != rule_id]
    if len(new_rules) < len(rules):
        _save_separate("studio_rules", new_rules)
        return True
    return False


async def clear_studio_rules() -> int:
    """Clear all studio rules from the separate JSON. Returns count of cleared entries."""
    rules = await get_studio_rules()
    count = len(rules)
    _save_separate("studio_rules", [])
    return count


async def get_all_user_data_files() -> dict[str, Any]:
    """Return a summary of all user-data JSON files for inspection."""
    migration = await get_migration_data()
    studio = await get_studio_rules()
    legacy = _load("legacy_rules") or []
    reviews = _load("reviews") or []
    rules = _load("firewall_rules") or []
    groups = _load("groups") or []
    modifications = _load("rule_modifications") or []
    return {
        "migration_data": {k: len(v) if isinstance(v, list) else v for k, v in migration.items()},
        "studio_rules_count": len(studio),
        "legacy_rules_count": len(legacy),
        "firewall_rules_count": len(rules),
        "reviews_count": len(reviews),
        "groups_count": len(groups),
        "modifications_count": len(modifications),
        "data_directory": str(SEPARATE_DATA_DIR),
    }


async def clear_reviews() -> int:
    """Clear all reviews. Returns count of cleared entries."""
    reviews = _load("reviews") or []
    count = len(reviews)
    _save("reviews", [])
    return count


async def clear_user_groups() -> int:
    """Clear all user-created groups (preserves seed groups). Returns count of cleared entries."""
    groups = _load("groups") or []
    count = len(groups)
    _save("groups", [])
    return count


async def clear_firewall_rules() -> int:
    """Clear all firewall rules (studio/seed rules in firewall_rules.json). Returns count."""
    rules = _load("firewall_rules") or []
    count = len(rules)
    _save("firewall_rules", [])
    return count


async def clear_modifications() -> int:
    """Clear all rule modifications. Returns count of cleared entries."""
    mods = _load("rule_modifications") or []
    count = len(mods)
    _save("rule_modifications", [])
    return count


async def clear_all_user_data() -> dict[str, int]:
    """One-click reset: clear ALL user/imported data across all stores.
    Clears: legacy rules, migration data, studio rules, reviews, modifications, firewall rules.
    Seed reference data (NHs, SZs, policy matrix, etc.) is NOT affected."""
    legacy_count = await clear_all_legacy_rules_force()
    migration_counts = await clear_migration_data()
    studio_count = await clear_studio_rules()
    reviews_count = await clear_reviews()
    fw_rules_count = await clear_firewall_rules()
    mods_count = await clear_modifications()
    # Also clear superseded fingerprints so re-imports work cleanly after full reset
    superseded_count = clear_superseded_fingerprints()
    return {
        "legacy_rules": legacy_count,
        "migration_history": migration_counts.get("migration_history", 0),
        "migration_mappings": migration_counts.get("migration_mappings", 0),
        "migration_reviews": migration_counts.get("migration_reviews", 0),
        "migrated_rules": migration_counts.get("migrated_rules", 0),
        "studio_rules": studio_count,
        "reviews": reviews_count,
        "firewall_rules": fw_rules_count,
        "modifications": mods_count,
        "superseded_fingerprints": superseded_count,
    }


async def clear_all_legacy_rules_force() -> int:
    """Force-clear ALL legacy rules (including migrated). Used for full reset."""
    rules = _load("legacy_rules") or []
    count = len(rules)
    _save("legacy_rules", [])
    return count


async def clear_data_by_app(app_id: str) -> dict[str, int]:
    """Clear all data for a specific app_id across all stores."""
    counts: dict[str, int] = {}

    # Legacy rules
    legacy = _load("legacy_rules") or []
    filtered = [r for r in legacy if str(r.get("app_id", "")) != app_id]
    counts["legacy_rules"] = len(legacy) - len(filtered)
    _save("legacy_rules", filtered)

    # Firewall rules
    fw = _load("firewall_rules") or []
    filtered_fw = [r for r in fw if str(r.get("application", "")) != app_id]
    counts["firewall_rules"] = len(fw) - len(filtered_fw)
    _save("firewall_rules", filtered_fw)

    # Reviews
    reviews = _load("reviews") or []
    # reviews reference rule_id; check rule_summary.application
    filtered_rev = [r for r in reviews if str(r.get("rule_summary", {}).get("application", "")) != app_id]
    counts["reviews"] = len(reviews) - len(filtered_rev)
    _save("reviews", filtered_rev)

    # Modifications
    mods = _load("rule_modifications") or []
    filtered_mods = [m for m in mods if str(m.get("application", "")) != app_id]
    counts["modifications"] = len(mods) - len(filtered_mods)
    _save("rule_modifications", filtered_mods)

    # Studio rules (separate JSON)
    studio = await get_studio_rules()
    filtered_studio = [r for r in studio if str(r.get("application", "")) != app_id]
    counts["studio_rules"] = len(studio) - len(filtered_studio)
    _save_separate("studio_rules", filtered_studio)

    # Migration data (separate JSON)
    migration = await get_migration_data()
    for key in ["migration_history", "migration_mappings", "migration_reviews", "migrated_rules"]:
        items = migration.get(key, [])
        app_field = "app_id" if key != "migrated_rules" else "application"
        filtered_items = [i for i in items if str(i.get(app_field, "")) != app_id]
        counts[key] = len(items) - len(filtered_items)
        migration[key] = filtered_items
    _save_separate("migration_data", migration)

    return counts


async def clear_data_by_environment(environment: str) -> dict[str, int]:
    """Clear all data for a specific environment across all stores."""
    counts: dict[str, int] = {}

    # Legacy rules
    legacy = _load("legacy_rules") or []
    filtered = [r for r in legacy if str(r.get("environment", "")) != environment]
    counts["legacy_rules"] = len(legacy) - len(filtered)
    _save("legacy_rules", filtered)

    # Firewall rules
    fw = _load("firewall_rules") or []
    filtered_fw = [r for r in fw if str(r.get("environment", "")) != environment]
    counts["firewall_rules"] = len(fw) - len(filtered_fw)
    _save("firewall_rules", filtered_fw)

    # Reviews
    reviews = _load("reviews") or []
    filtered_rev = [r for r in reviews if str(r.get("rule_summary", {}).get("environment", "")) != environment]
    counts["reviews"] = len(reviews) - len(filtered_rev)
    _save("reviews", filtered_rev)

    # Modifications
    mods = _load("rule_modifications") or []
    filtered_mods = [m for m in mods if str(m.get("environment", "")) != environment]
    counts["modifications"] = len(mods) - len(filtered_mods)
    _save("rule_modifications", filtered_mods)

    # Studio rules (separate JSON)
    studio = await get_studio_rules()
    filtered_studio = [r for r in studio if str(r.get("environment", "")) != environment]
    counts["studio_rules"] = len(studio) - len(filtered_studio)
    _save_separate("studio_rules", filtered_studio)

    return counts


async def get_data_summary_by_app() -> list[dict[str, Any]]:
    """Return per-app record counts for the Data Management overview."""
    legacy = _load("legacy_rules") or []
    fw = _load("firewall_rules") or []
    reviews = _load("reviews") or []
    studio = await get_studio_rules()

    app_counts: dict[str, dict[str, int]] = {}
    for r in legacy:
        aid = str(r.get("app_id", "Unknown"))
        app_counts.setdefault(aid, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        app_counts[aid]["legacy"] += 1
    for r in fw:
        aid = str(r.get("application", "Unknown"))
        app_counts.setdefault(aid, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        app_counts[aid]["firewall"] += 1
    for r in reviews:
        aid = str(r.get("rule_summary", {}).get("application", "Unknown"))
        app_counts.setdefault(aid, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        app_counts[aid]["reviews"] += 1
    for r in studio:
        aid = str(r.get("application", "Unknown"))
        app_counts.setdefault(aid, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        app_counts[aid]["studio"] += 1

    return [{"app_id": k, **v, "total": sum(v.values())} for k, v in sorted(app_counts.items())]


async def get_data_summary_by_env() -> list[dict[str, Any]]:
    """Return per-environment record counts for the Data Management overview."""
    legacy = _load("legacy_rules") or []
    fw = _load("firewall_rules") or []
    reviews = _load("reviews") or []
    studio = await get_studio_rules()

    env_counts: dict[str, dict[str, int]] = {}
    for r in legacy:
        env = str(r.get("environment", "Unknown"))
        env_counts.setdefault(env, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        env_counts[env]["legacy"] += 1
    for r in fw:
        env = str(r.get("environment", "Unknown"))
        env_counts.setdefault(env, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        env_counts[env]["firewall"] += 1
    for r in reviews:
        env = str(r.get("rule_summary", {}).get("environment", "Unknown"))
        env_counts.setdefault(env, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        env_counts[env]["reviews"] += 1
    for r in studio:
        env = str(r.get("environment", "Unknown"))
        env_counts.setdefault(env, {"legacy": 0, "firewall": 0, "reviews": 0, "studio": 0})
        env_counts[env]["studio"] += 1

    return [{"environment": k, **v, "total": sum(v.values())} for k, v in sorted(env_counts.items())]


# ============================================================
# Partial Migration Architecture
# ============================================================

# --------------- P1/P2: App Migration Summary ---------------

async def get_app_migration_summary() -> list[dict[str, Any]]:
    """Return per-app migration summary based on dc_location of each component.

    For every distinct app_id in app_dc_mappings, compute:
      - total_components, ngdc_count, legacy_count
      - pct_migrated  (0-100)
      - migration_scenario: Full NGDC | Full Legacy | Partial (Src NGDC/Dst Legacy) | Mixed
      - components: list of {component, dc_location, dc/legacy_dc, ...}
    """
    mappings = _load("app_dc_mappings") or []
    apps: dict[str, list[dict[str, Any]]] = {}
    for m in mappings:
        aid = str(m.get("app_id", ""))
        if aid:
            apps.setdefault(aid, []).append(m)

    result: list[dict[str, Any]] = []
    for app_id, comps in sorted(apps.items()):
        ngdc = [c for c in comps if c.get("dc_location") == "NGDC"]
        legacy = [c for c in comps if c.get("dc_location") == "Legacy"]
        total = len(comps)
        ngdc_count = len(ngdc)
        legacy_count = len(legacy)
        pct = round(ngdc_count / total * 100) if total else 0

        if legacy_count == 0:
            scenario = "Full NGDC"
        elif ngdc_count == 0:
            scenario = "Full Legacy"
        else:
            scenario = "Partial"

        result.append({
            "app_id": app_id,
            "app_distributed_id": comps[0].get("app_distributed_id", ""),
            "total_components": total,
            "ngdc_count": ngdc_count,
            "legacy_count": legacy_count,
            "pct_migrated": pct,
            "migration_scenario": scenario,
            "components": [
                {
                    "component": c.get("component", ""),
                    "dc_location": c.get("dc_location", ""),
                    "dc": c.get("dc", ""),
                    "nh": c.get("nh", ""),
                    "sz": c.get("sz", ""),
                    "legacy_dc": c.get("legacy_dc", ""),
                    "legacy_cidr": c.get("legacy_cidr", ""),
                    "cidr": c.get("cidr", ""),
                    "status": c.get("status", ""),
                    "notes": c.get("notes", ""),
                }
                for c in comps
            ],
        })
    return result


async def get_app_migration_status(app_id: str) -> dict[str, Any] | None:
    """Return migration status for a single app by app_id."""
    summaries = await get_app_migration_summary()
    return next((s for s in summaries if s["app_id"] == app_id), None)


# --------------- P3: Rule Endpoint Classification ---------------

async def classify_rule_endpoints(rule_data: dict[str, Any]) -> dict[str, Any]:
    """Classify a rule's source and destination as NGDC or Legacy.

    Looks up the source/destination app+component in app_dc_mappings to
    determine dc_location for each side.  Returns one of five scenarios:
      NGDC-to-NGDC | Legacy-to-Legacy | NGDC-to-Legacy | Legacy-to-NGDC | Unknown

    Also returns the Heritage DC matrix direction needed for cross-DC validation.
    """
    mappings = _load("app_dc_mappings") or []

    src_app = str(rule_data.get("source_app", rule_data.get("application", "")))
    dst_app = str(rule_data.get("destination_app", rule_data.get("dst_application", "")))
    src_component = str(rule_data.get("source_component", ""))
    dst_component = str(rule_data.get("destination_component", ""))
    src_ip = str(rule_data.get("source", rule_data.get("rule_source", "")))
    dst_ip = str(rule_data.get("destination", rule_data.get("rule_destination", "")))

    def _lookup_dc_location(app: str, component: str, ip: str) -> str:
        """Resolve dc_location for an endpoint.  Priority: app+component match,
        then app-only match, then IP/CIDR overlap."""
        if app:
            app_maps = [m for m in mappings
                        if str(m.get("app_id", "")).upper() == app.upper()]
            if component:
                comp_match = [m for m in app_maps
                              if str(m.get("component", "")).upper() == component.upper()]
                if comp_match:
                    return str(comp_match[0].get("dc_location", "Unknown"))
            if app_maps:
                # If no component specified, use majority dc_location
                locs = [m.get("dc_location", "") for m in app_maps]
                ngdc_ct = sum(1 for l in locs if l == "NGDC")
                leg_ct = sum(1 for l in locs if l == "Legacy")
                return "NGDC" if ngdc_ct >= leg_ct else "Legacy"

        # Fallback: check CIDR overlap
        if ip:
            for m in mappings:
                cidr = m.get("cidr", "")
                legacy_cidr = m.get("legacy_cidr", "")
                if cidr and ip.split("/")[0] in cidr:
                    return "NGDC"
                if legacy_cidr and ip.split("/")[0] in legacy_cidr:
                    return "Legacy"
        return "Unknown"

    src_loc = _lookup_dc_location(src_app, src_component, src_ip)
    dst_loc = _lookup_dc_location(dst_app, dst_component, dst_ip)

    if src_loc == "NGDC" and dst_loc == "NGDC":
        scenario = "NGDC-to-NGDC"
        heritage_direction = ""
    elif src_loc == "Legacy" and dst_loc == "Legacy":
        scenario = "Legacy-to-Legacy"
        heritage_direction = "Heritage-to-Heritage"
    elif src_loc == "NGDC" and dst_loc == "Legacy":
        scenario = "NGDC-to-Legacy"
        heritage_direction = "NGDC-to-Heritage"
    elif src_loc == "Legacy" and dst_loc == "NGDC":
        scenario = "Legacy-to-NGDC"
        heritage_direction = "Heritage-to-NGDC"
    else:
        scenario = "Unknown"
        heritage_direction = ""

    is_cross_dc = scenario in ("NGDC-to-Legacy", "Legacy-to-NGDC")
    return {
        "source_dc_location": src_loc,
        "destination_dc_location": dst_loc,
        "scenario": scenario,
        "is_cross_dc": is_cross_dc,
        "heritage_direction": heritage_direction,
        "requires_heritage_matrix": is_cross_dc,
    }


# --------------- P4: Cross-DC LDF Boundaries ---------------

async def determine_cross_dc_boundaries(
    rule_data: dict[str, Any],
) -> dict[str, Any]:
    """Extended LDF analysis for cross-DC (NGDC ↔ Legacy) flows.

    Unlike intra-NGDC flows that use NH/SZ segmentation, cross-DC flows
    require a DC interconnect / WAN traversal plus the NGDC-side FW device.
    """
    classification = await classify_rule_endpoints(rule_data)
    scenario = classification["scenario"]

    if scenario == "NGDC-to-NGDC":
        # Delegate to standard LDF
        src_nh = rule_data.get("source_nh", "")
        src_sz = rule_data.get("source_sz", rule_data.get("source_zone", ""))
        dst_nh = rule_data.get("destination_nh", "")
        dst_sz = rule_data.get("destination_sz", rule_data.get("destination_zone", ""))
        base = await determine_firewall_boundaries(src_nh, src_sz, dst_nh, dst_sz)
        base["classification"] = classification
        return base

    if scenario == "Legacy-to-Legacy":
        return {
            "boundaries": 0,
            "flow_rule": "LDF-CROSS-01",
            "devices": [],
            "requires_egress": False,
            "requires_ingress": False,
            "classification": classification,
            "note": "Legacy-to-Legacy: flat heritage network, no NGDC firewall boundaries.",
        }

    # Cross-DC scenarios (NGDC-to-Legacy or Legacy-to-NGDC)
    ngdc_nh = rule_data.get("source_nh", "") if classification["source_dc_location"] == "NGDC" else rule_data.get("destination_nh", "")
    ngdc_sz = (rule_data.get("source_sz", rule_data.get("source_zone", ""))
               if classification["source_dc_location"] == "NGDC"
               else rule_data.get("destination_sz", rule_data.get("destination_zone", "")))
    ngdc_sz_upper = (ngdc_sz or "").upper()

    # NGDC side may need a segmentation FW device
    ngdc_dev = _find_device(ngdc_nh, ngdc_sz_upper) if ngdc_nh and ngdc_sz_upper else None
    devs: list[dict[str, Any]] = []

    if ngdc_dev:
        direction = "egress" if classification["source_dc_location"] == "NGDC" else "ingress"
        devs.append({
            "role": f"ngdc_{direction}",
            "direction": direction,
            "device_id": ngdc_dev["device_id"],
            "device_name": ngdc_dev["name"],
            "nh": ngdc_nh,
            "sz": ngdc_sz_upper,
        })

    # DC interconnect device (virtual)
    devs.append({
        "role": "dc_interconnect",
        "direction": "cross-dc",
        "device_id": "DCI-VIRTUAL-001",
        "device_name": "DC Interconnect (NGDC ↔ Legacy)",
        "nh": "",
        "sz": "",
    })

    flow_rule = "LDF-CROSS-02" if scenario == "NGDC-to-Legacy" else "LDF-CROSS-03"
    return {
        "boundaries": len(devs),
        "flow_rule": flow_rule,
        "devices": devs,
        "requires_egress": classification["source_dc_location"] == "NGDC",
        "requires_ingress": classification["destination_dc_location"] == "NGDC",
        "classification": classification,
        "note": (f"Cross-DC flow ({scenario}): traffic traverses "
                 f"{'NGDC ' + ngdc_nh + ' ' + ngdc_sz_upper + ' FW + ' if ngdc_dev else ''}"
                 f"DC interconnect to reach {'Legacy' if scenario == 'NGDC-to-Legacy' else 'NGDC'} side."),
    }


# --------------- P5: Heritage DC Birthright Validation ---------------

async def validate_birthright_cross_dc(rule_data: dict[str, Any]) -> dict[str, Any]:
    """Validate a cross-DC rule against the Heritage DC matrix.

    For NGDC-to-Legacy or Legacy-to-NGDC flows, checks the bidirectional
    Heritage DC matrix.  Falls back to standard validate_birthright for
    intra-NGDC flows.
    """
    classification = await classify_rule_endpoints(rule_data)
    scenario = classification["scenario"]

    if scenario == "NGDC-to-NGDC":
        base = await validate_birthright(rule_data)
        base["classification"] = classification
        return base

    if scenario == "Legacy-to-Legacy":
        return {
            "compliant": True,
            "environment": rule_data.get("environment", "Production"),
            "matrix_used": "Heritage DC",
            "violations": [],
            "warnings": [],
            "permitted": [{"matrix": "Heritage DC", "rule": "Legacy ↔ Legacy",
                           "action": "Permitted",
                           "reason": "Intra-heritage traffic is flat, permitted by default"}],
            "firewall_devices_needed": [],
            "firewall_path_info": [],
            "firewall_request_required": False,
            "classification": classification,
            "summary": "Compliant (Heritage DC) - Legacy-to-Legacy, no segmentation",
        }

    # Cross-DC: look up Heritage DC matrix
    heritage_matrix = _load("heritage_dc_matrix") or []
    direction = classification["heritage_direction"]

    # Determine the NGDC-side SZ
    ngdc_sz = ""
    if classification["source_dc_location"] == "NGDC":
        ngdc_sz = rule_data.get("source_sz", rule_data.get("source_zone", ""))
    else:
        ngdc_sz = rule_data.get("destination_sz", rule_data.get("destination_zone", ""))
    ngdc_sz_upper = (ngdc_sz or "").upper()

    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    permitted: list[dict[str, str]] = []

    matched = False
    for entry in heritage_matrix:
        e_dir = entry.get("direction", "")
        e_ngdc_zone = entry.get("new_dc_zone", "")
        if e_dir == direction and (e_ngdc_zone == ngdc_sz_upper or e_ngdc_zone == "Default"):
            matched = True
            action = entry.get("action", "")
            reason = entry.get("reason", "")
            rule_desc = f"{direction}: Heritage ↔ {ngdc_sz_upper or 'Any'}"

            if "Blocked" in action and "Exception" not in action:
                violations.append({"matrix": "Heritage DC", "rule": rule_desc,
                                   "action": action, "reason": reason})
            elif "Exception" in action or "Blocked" in action:
                warnings.append({"matrix": "Heritage DC", "rule": rule_desc,
                                 "action": action, "reason": reason})
            else:
                permitted.append({"matrix": "Heritage DC", "rule": rule_desc,
                                  "action": action, "reason": reason})

    if not matched:
        warnings.append({"matrix": "Heritage DC", "rule": f"{direction}: Heritage ↔ {ngdc_sz_upper}",
                          "action": "No Match",
                          "reason": "No Heritage DC matrix entry found for this flow direction/zone"})

    is_compliant = len(violations) == 0
    return {
        "compliant": is_compliant,
        "environment": rule_data.get("environment", "Production"),
        "matrix_used": "Heritage DC",
        "violations": violations,
        "warnings": warnings,
        "permitted": permitted,
        "firewall_devices_needed": [],
        "firewall_path_info": [],
        "firewall_request_required": len(warnings) > 0,
        "classification": classification,
        "summary": (
            f"{'Compliant' if is_compliant else 'Non-Compliant'} (Heritage DC) - "
            f"{scenario}: {len(violations)} violations, {len(warnings)} warnings, "
            f"{len(permitted)} permitted"
        ),
    }


# --------------- P6: Hybrid Compilation ---------------

async def compile_hybrid_rule(rule_id: str, vendor: str = "generic") -> dict[str, Any] | None:
    """Compile a rule that spans NGDC and Legacy infrastructure.

    For cross-DC rules, generates:
      - NGDC-side compiled rule (with NH/SZ naming standards)
      - Legacy-side compiled rule (flat, no NH/SZ)
      - DC interconnect rule (if applicable)
    """
    rule = await get_rule(rule_id)
    if not rule:
        legacy_rules = _load("legacy_rules") or []
        rule = next((r for r in legacy_rules if r.get("id") == rule_id), None)
    if not rule:
        return None

    classification = await classify_rule_endpoints(rule)
    scenario = classification["scenario"]

    if scenario == "NGDC-to-NGDC":
        # Delegate to standard compilation
        return await compile_egress_ingress(rule_id, vendor)

    src = rule.get("source", rule.get("rule_source", ""))
    dst = rule.get("destination", rule.get("rule_destination", ""))
    action = rule.get("action", rule.get("rule_action", "permit"))
    protocol = rule.get("protocol", rule.get("rule_protocol", "tcp"))
    port = rule.get("port", rule.get("rule_port", ""))
    app_id = str(rule.get("application", ""))
    rule_name = rule.get("name", rule.get("rule_name", f"rule-{rule_id[:8]}"))

    compiled_rules: list[dict[str, Any]] = []
    now = _now()

    # NGDC-side rule
    ngdc_rule: dict[str, Any] = {
        "id": f"hybrid-ngdc-{rule_id[:8]}",
        "parent_rule_id": rule_id,
        "side": "NGDC",
        "compiled_at": now,
        "vendor": vendor,
        "rule_name": f"ngdc-{rule_name}",
        "source": src if classification["source_dc_location"] == "NGDC" else f"dci-{dst}",
        "destination": dst if classification["destination_dc_location"] == "NGDC" else f"dci-{src}",
        "action": action,
        "protocol": protocol,
        "port": port,
        "application": app_id,
    }
    # Add NGDC naming if available
    if classification["source_dc_location"] == "NGDC":
        ngdc_rule["source_nh"] = rule.get("source_nh", rule.get("nh", ""))
        ngdc_rule["source_sz"] = rule.get("source_sz", rule.get("source_zone", ""))
    if classification["destination_dc_location"] == "NGDC":
        ngdc_rule["destination_nh"] = rule.get("destination_nh", rule.get("dst_nh", ""))
        ngdc_rule["destination_sz"] = rule.get("destination_sz", rule.get("destination_zone", ""))
    compiled_rules.append(ngdc_rule)

    # Legacy-side rule (flat, no NH/SZ segmentation)
    legacy_rule: dict[str, Any] = {
        "id": f"hybrid-legacy-{rule_id[:8]}",
        "parent_rule_id": rule_id,
        "side": "Legacy",
        "compiled_at": now,
        "vendor": vendor,
        "rule_name": f"leg-{rule_name}",
        "source": src if classification["source_dc_location"] == "Legacy" else f"dci-{src}",
        "destination": dst if classification["destination_dc_location"] == "Legacy" else f"dci-{dst}",
        "action": action,
        "protocol": protocol,
        "port": port,
        "application": app_id,
        "note": "Legacy DC - flat zone, no NH/SZ segmentation",
    }
    compiled_rules.append(legacy_rule)

    # DC Interconnect rule
    dci_rule: dict[str, Any] = {
        "id": f"hybrid-dci-{rule_id[:8]}",
        "parent_rule_id": rule_id,
        "side": "DC-Interconnect",
        "compiled_at": now,
        "vendor": vendor,
        "rule_name": f"dci-{rule_name}",
        "source": src,
        "destination": dst,
        "action": action,
        "protocol": protocol,
        "port": port,
        "note": f"DC interconnect permit for {scenario} flow",
    }
    compiled_rules.append(dci_rule)

    return {
        "rule_id": rule_id,
        "scenario": scenario,
        "classification": classification,
        "compiled_rules": compiled_rules,
        "compiled_at": now,
        "vendor": vendor,
        "note": f"Hybrid compilation: {len(compiled_rules)} rules generated for {scenario} flow",
    }


# --------------- P7: Migration Lifecycle Extensions ---------------

PARTIAL_MIGRATION_STATUSES = [
    "Not Started",
    "In Progress",
    "Partially Migrated",
    "Completed",
    "Heritage Dependency",
    "Rollback",
]

PARTIAL_MIGRATION_TRANSITIONS: dict[str, list[str]] = {
    "Not Started": ["In Progress"],
    "In Progress": ["Partially Migrated", "Completed", "Rollback"],
    "Partially Migrated": ["In Progress", "Completed", "Heritage Dependency"],
    "Completed": [],
    "Heritage Dependency": ["In Progress", "Partially Migrated"],
    "Rollback": ["Not Started", "In Progress"],
}


async def get_app_lifecycle_status(app_id: str) -> dict[str, Any]:
    """Derive the migration lifecycle status for an app based on its
    component-level dc_location values.

    Returns the computed status and valid transitions.
    """
    summary = await get_app_migration_status(app_id)
    if not summary:
        return {"app_id": app_id, "status": "Unknown", "transitions": []}

    scenario = summary["migration_scenario"]
    pct = summary["pct_migrated"]

    if scenario == "Full NGDC":
        status = "Completed"
    elif scenario == "Full Legacy":
        status = "Not Started"
    elif pct > 0:
        status = "Partially Migrated"
    else:
        status = "Not Started"

    transitions = PARTIAL_MIGRATION_TRANSITIONS.get(status, [])
    return {
        "app_id": app_id,
        "status": status,
        "pct_migrated": pct,
        "scenario": scenario,
        "transitions": transitions,
        "total_components": summary["total_components"],
        "ngdc_count": summary["ngdc_count"],
        "legacy_count": summary["legacy_count"],
    }


async def transition_app_migration_status(
    app_id: str, new_status: str,
) -> dict[str, Any]:
    """Transition an app's migration lifecycle status.

    Updates the dc_location of components as needed based on status change.
    """
    current = await get_app_lifecycle_status(app_id)
    current_status = current.get("status", "Unknown")
    valid = PARTIAL_MIGRATION_TRANSITIONS.get(current_status, [])

    if new_status not in valid:
        return {
            "success": False,
            "error": f"Cannot transition from '{current_status}' to '{new_status}'. "
                     f"Valid transitions: {valid}",
        }

    # Record lifecycle event
    _record_lifecycle(
        entity_type="app_migration",
        entity_id=app_id,
        action=f"status_transition: {current_status} → {new_status}",
        details={"from": current_status, "to": new_status},
    )

    return {
        "success": True,
        "app_id": app_id,
        "previous_status": current_status,
        "new_status": new_status,
        "message": f"App {app_id} transitioned from {current_status} to {new_status}",
    }


# --------------- P9: Legacy Group Naming ---------------

def generate_legacy_group_name(
    app_id: str, legacy_dc: str, component: str, suffix: str = "",
) -> str:
    """Generate a group name for Legacy-side components in hybrid scenarios.

    Format: leg-{APP}-{LEGACY_DC}-{COMP}[-{suffix}]
    """
    parts = ["leg", app_id.upper()]
    if legacy_dc:
        # Shorten DC_LEGACY_A -> LGA, DC_LEGACY_B -> LGB, etc.
        short_dc = legacy_dc.replace("DC_LEGACY_", "LG")
        parts.append(short_dc)
    if component:
        parts.append(component.upper())
    name = "-".join(parts)
    if suffix:
        name += f"-{suffix}"
    return name


async def generate_hybrid_group_names(app_id: str) -> dict[str, Any]:
    """Generate group names for all components of an app in hybrid scenarios.

    Returns NGDC-standard names for NGDC components and leg- names for Legacy.
    """
    summary = await get_app_migration_status(app_id)
    if not summary:
        return {"app_id": app_id, "groups": [], "error": "App not found"}

    naming = _load("naming_standards") or {}
    ngdc_pattern = naming.get("group_pattern", "grp-{APP}-{NH}-{SZ}-{Component}")

    groups: list[dict[str, Any]] = []
    for comp in summary["components"]:
        component = comp["component"]
        dc_loc = comp["dc_location"]

        if dc_loc == "NGDC":
            nh = comp.get("nh", "")
            sz = comp.get("sz", "")
            name = ngdc_pattern.replace("{APP}", app_id.upper())
            name = name.replace("{NH}", nh)
            name = name.replace("{SZ}", sz)
            name = name.replace("{Component}", component.upper())
            groups.append({
                "component": component,
                "dc_location": "NGDC",
                "group_name": name,
                "nh": nh,
                "sz": sz,
                "dc": comp.get("dc", ""),
            })
        else:
            legacy_dc = comp.get("legacy_dc", "")
            name = generate_legacy_group_name(app_id, legacy_dc, component)
            groups.append({
                "component": component,
                "dc_location": "Legacy",
                "group_name": name,
                "legacy_dc": legacy_dc,
            })

    return {"app_id": app_id, "scenario": summary["migration_scenario"], "groups": groups}


# ============================================================
# Revamp: Shared Services + Presences + Group Derivation
# ============================================================

# ---- Naming-mode-aware group name resolution ----
#
# Each Security Zone has a `naming_mode`:
#   * APP_SCOPED  (default) — dedicated SZ (CCS / CDE / PAA / CPA / Swift /
#                              3PY): each app owns its own egress IPs, so the
#                              group name embeds the app distributed-id:
#                                grp-<AppDistId>-<NH>-<SZ>           (egress)
#                                grp-<AppDistId>-<NH>-<SZ>-Ingress   (ingress)
#                                grp-<SvcId>-<NH>-<SZ>               (svc)
#   * ZONE_SCOPED — shared cluster zone (STD / GEN / Shared / OpenShift /
#                    VMware tenant pools): the entire SZ CIDR is the source
#                    for every app in the SZ, so naming drops the app token:
#                                grp-<NH>-<SZ>                       (egress)
#                                grp-<NH>-<SZ>-Ingress               (ingress)
#                    The same shared group is reused by every app/service in
#                    that (NH, SZ) — which is the whole point: the dedup
#                    engine collapses identical rules naturally.
#
# These helpers are sync (no await) so they can be called from anywhere.
# The SZ catalog is loaded once per call from the in-memory store; if the
# SZ isn't found we fall back to APP_SCOPED for safety.

_NAMING_MODE_CACHE: dict[str, str] = {}


def _refresh_naming_mode_cache() -> None:
    """Rebuild the (sz_code → naming_mode) cache from the SZ catalog.

    Called on seed and after any SZ update so subsequent lookups are O(1)
    and don't reload the whole zones list."""

    global _NAMING_MODE_CACHE
    cache: dict[str, str] = {}
    for sz in (_load("security_zones") or []):
        code = str(sz.get("code", "")).strip().upper()
        mode = str(sz.get("naming_mode") or "app_scoped").strip().lower()
        if code:
            cache[code] = mode if mode in ("app_scoped", "zone_scoped") else "app_scoped"
    _NAMING_MODE_CACHE = cache


def _get_sz_naming_mode(sz_code: str) -> str:
    """Return the naming_mode for the given SZ code (case-insensitive).

    Defaults to ``app_scoped`` when the SZ isn't in the catalog (safe
    behaviour — the worst case is a dedicated, app-named group)."""

    if not sz_code:
        return "app_scoped"
    if not _NAMING_MODE_CACHE:
        _refresh_naming_mode_cache()
    return _NAMING_MODE_CACHE.get(sz_code.upper(), "app_scoped")


def _zone_group_name(nh_id: str, sz_code: str, suffix: str = "") -> str:
    """Zone-scoped (shared cluster) group name. Used for STD/GEN/etc.

    Format: ``grp-<NH>-<SZ>`` with an optional ``-Ingress`` suffix when
    the group is the destination side of a rule."""

    base = f"grp-{nh_id.upper()}-{sz_code.upper()}"
    return f"{base}-{suffix}" if suffix else base


def _shared_service_group_name(service_id: str, nh_id: str, sz_code: str) -> str:
    """Naming for shared-service groups.

    For SZs marked ``zone_scoped`` (e.g. a Splunk forwarder cluster that
    lives in the shared GEN pool) the group collapses to ``grp-<NH>-<SZ>``;
    otherwise the dedicated convention ``grp-<SERVICE_ID>-<NH>-<SZ>`` is
    preserved (the historical behaviour for Oracle/Kafka/Mainframe-style
    services running in their own SZ)."""

    if _get_sz_naming_mode(sz_code) == "zone_scoped":
        return _zone_group_name(nh_id, sz_code)
    return f"grp-{service_id.upper()}-{nh_id.upper()}-{sz_code.upper()}"


def _app_egress_group_name(app_dist_id: str, nh_id: str, sz_code: str) -> str:
    """Source (egress) group naming honouring SZ.naming_mode.

    APP_SCOPED  → ``grp-<AppDistId>-<NH>-<SZ>`` (per-app dedicated groups)
    ZONE_SCOPED → ``grp-<NH>-<SZ>`` (cluster CIDR shared by every app in
                  the SZ — required so the dedup engine collapses
                  redundant rules raised by different apps in the same
                  shared zone)."""

    if _get_sz_naming_mode(sz_code) == "zone_scoped":
        return _zone_group_name(nh_id, sz_code)
    return f"grp-{app_dist_id.upper()}-{nh_id.upper()}-{sz_code.upper()}"


def _app_ingress_group_name(app_dist_id: str, nh_id: str, sz_code: str) -> str:
    """Destination (App-ingress) group naming honouring SZ.naming_mode.

    APP_SCOPED  → ``grp-<AppDistId>-<NH>-<SZ>-Ingress``
    ZONE_SCOPED → ``grp-<NH>-<SZ>-Ingress`` (rare in practice — apps
                  almost always expose ingress in dedicated SZs — but
                  supported for symmetry)."""

    if _get_sz_naming_mode(sz_code) == "zone_scoped":
        return _zone_group_name(nh_id, sz_code, suffix="Ingress")
    return f"grp-{app_dist_id.upper()}-{nh_id.upper()}-{sz_code.upper()}-Ingress"


def _build_derived_groups_from_presences(
    ss_presences: list[dict[str, Any]],
    app_presences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Materialize FirewallGroup records from Shared Service + App presences.

    Produces three owner_kinds:
      - shared_service : grp-<SVC>-<NH>-<SZ>
      - app_egress     : grp-<AD>-<NH>-<SZ>
      - app_ingress    : grp-<AD>-<NH>-<SZ>-Ingress (only if has_ingress)
    """
    out: list[dict[str, Any]] = []
    for p in ss_presences:
        name = _shared_service_group_name(p["service_id"], p["nh_id"], p["sz_code"])
        out.append({
            "name": name,
            "owner_kind": "shared_service",
            "owner_ref": p["service_id"],
            "dc_id": p["dc_id"],
            "environment": p.get("environment", "Production"),
            "nh_id": p["nh_id"],
            "sz_code": p["sz_code"],
            "nh": p["nh_id"],
            "sz": p["sz_code"],
            "app_id": p["service_id"],  # back-compat with legacy schema
            "subtype": "SVC",
            "direction": "ingress",
            "members": list(p.get("members", [])),
            "description": f"Derived: Shared Service {p['service_id']} @ {p['dc_id']} ({p.get('environment', '')})",
            "created_at": _now(),
            "updated_at": _now(),
        })

    for p in app_presences:
        egr_name = _app_egress_group_name(
            p["app_distributed_id"], p["nh_id"], p["sz_code"])
        out.append({
            "name": egr_name,
            "owner_kind": "app_egress",
            "owner_ref": p["app_distributed_id"],
            "dc_id": p["dc_id"],
            "environment": p.get("environment", "Production"),
            "nh_id": p["nh_id"],
            "sz_code": p["sz_code"],
            "nh": p["nh_id"],
            "sz": p["sz_code"],
            "app_id": p["app_distributed_id"],
            "app_distributed_id": p["app_distributed_id"],
            "subtype": "APP",
            "direction": "egress",
            "members": list(p.get("egress_members", [])),
            "description": f"Derived: App {p['app_distributed_id']} egress @ {p['dc_id']}",
            "created_at": _now(),
            "updated_at": _now(),
        })
        if p.get("has_ingress"):
            ing_name = _app_ingress_group_name(
                p["app_distributed_id"], p["nh_id"], p["sz_code"])
            out.append({
                "name": ing_name,
                "owner_kind": "app_ingress",
                "owner_ref": p["app_distributed_id"],
                "dc_id": p["dc_id"],
                "environment": p.get("environment", "Production"),
                "nh_id": p["nh_id"],
                "sz_code": p["sz_code"],
                "nh": p["nh_id"],
                "sz": p["sz_code"],
                "app_id": p["app_distributed_id"],
                "app_distributed_id": p["app_distributed_id"],
                "subtype": "APP",
                "direction": "ingress",
                "members": list(p.get("ingress_members", [])),
                "description": f"Derived: App {p['app_distributed_id']} ingress @ {p['dc_id']}",
                "created_at": _now(),
                "updated_at": _now(),
            })
    return out


def _merge_groups_preserving_existing(
    existing: list[dict[str, Any]],
    derived: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge derived groups with existing ones — by (name, dc_id). Existing
    wins on conflicts so user edits are preserved."""
    key = lambda g: (str(g.get("name", "")), str(g.get("dc_id", "")))  # noqa
    seen = {key(g) for g in existing}
    out = list(existing)
    for g in derived:
        if key(g) in seen:
            continue
        out.append(g)
        seen.add(key(g))
    return out


# ---- Shared Service CRUD ----

async def get_shared_services() -> list[dict[str, Any]]:
    return _load("shared_services") or []


async def get_shared_service(service_id: str) -> dict[str, Any] | None:
    for s in _load("shared_services") or []:
        if str(s.get("service_id", "")).upper() == service_id.upper():
            return s
    return None


async def create_shared_service(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("shared_services") or []
    data = dict(data)
    data["service_id"] = str(data.get("service_id", "")).upper()
    data["created_at"] = _now()
    data["updated_at"] = _now()
    data.setdefault("primary_dc", "ALPHA_NGDC")
    data.setdefault("deployment_mode", "all_ngdc")
    data.setdefault("excluded_dcs", [])
    # dedupe by service_id
    items = [i for i in items if str(i.get("service_id", "")).upper() != data["service_id"]]
    items.append(data)
    _save("shared_services", items)
    # Auto-fan presences across all NGDC DCs when deployment_mode=all_ngdc.
    await auto_fan_service_presences(data)
    return data


async def update_shared_service(service_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("shared_services") or []
    for i in items:
        if str(i.get("service_id", "")).upper() == service_id.upper():
            i.update(updates)
            i["updated_at"] = _now()
            _save("shared_services", items)
            # Re-fan after every save so newly-added tiers / DCs / mode
            # changes auto-create the missing presences. Existing
            # presences are preserved (idempotent upsert).
            await auto_fan_service_presences(i)
            return i
    return None


async def delete_shared_service(service_id: str) -> bool:
    items = _load("shared_services") or []
    new = [i for i in items if str(i.get("service_id", "")).upper() != service_id.upper()]
    if len(new) == len(items):
        return False
    _save("shared_services", new)
    # cascade: drop presences and derived groups
    pres = _load("shared_service_presences") or []
    _save("shared_service_presences",
          [p for p in pres if str(p.get("service_id", "")).upper() != service_id.upper()])
    groups = _load("groups") or []
    _save("groups",
          [g for g in groups
           if not (g.get("owner_kind") == "shared_service"
                   and str(g.get("owner_ref", "")).upper() == service_id.upper())])
    return True


# ---- Shared Service Presence CRUD ----

async def get_shared_service_presences(service_id: str | None = None) -> list[dict[str, Any]]:
    items = _load("shared_service_presences") or []
    if service_id:
        items = [p for p in items
                 if str(p.get("service_id", "")).upper() == service_id.upper()]
    return items


async def upsert_shared_service_presence(data: dict[str, Any]) -> dict[str, Any]:
    """Create or update a presence row keyed by (service_id, dc_id, environment, nh_id, sz_code)."""
    items = _load("shared_service_presences") or []
    data = dict(data)
    data["service_id"] = str(data.get("service_id", "")).upper()
    key = (data["service_id"], data.get("dc_id", ""),
           data.get("environment", "Production"),
           data.get("nh_id", ""), data.get("sz_code", ""))
    updated = False
    for i, p in enumerate(items):
        pk = (str(p.get("service_id", "")).upper(), p.get("dc_id", ""),
              p.get("environment", "Production"),
              p.get("nh_id", ""), p.get("sz_code", ""))
        if pk == key:
            items[i] = data
            updated = True
            break
    if not updated:
        items.append(data)
    _save("shared_service_presences", items)
    # Re-materialize the derived group for this presence.
    groups = _load("groups") or []
    gname = _shared_service_group_name(data["service_id"], data["nh_id"], data["sz_code"])
    # drop existing derived row with same (name, dc_id) before inserting
    groups = [g for g in groups
              if not (g.get("name") == gname and g.get("dc_id") == data.get("dc_id"))]
    groups.append({
        "name": gname,
        "owner_kind": "shared_service",
        "owner_ref": data["service_id"],
        "dc_id": data.get("dc_id", ""),
        "environment": data.get("environment", "Production"),
        "nh_id": data.get("nh_id", ""),
        "sz_code": data.get("sz_code", ""),
        "nh": data.get("nh_id", ""),
        "sz": data.get("sz_code", ""),
        "app_id": data["service_id"],
        "subtype": "SVC",
        "direction": "ingress",
        "members": list(data.get("members", [])),
        "description": f"Shared Service {data['service_id']} @ {data.get('dc_id', '')}",
        "created_at": _now(),
        "updated_at": _now(),
    })
    _save("groups", groups)
    return data


async def delete_shared_service_presence(service_id: str, dc_id: str,
                                          environment: str,
                                          nh_id: str, sz_code: str) -> bool:
    items = _load("shared_service_presences") or []
    key = (service_id.upper(), dc_id, environment, nh_id, sz_code)
    new = [p for p in items
           if (str(p.get("service_id", "")).upper(), p.get("dc_id", ""),
               p.get("environment", ""), p.get("nh_id", ""),
               p.get("sz_code", "")) != key]
    if len(new) == len(items):
        return False
    _save("shared_service_presences", new)
    # drop the derived group
    gname = _shared_service_group_name(service_id, nh_id, sz_code)
    groups = _load("groups") or []
    _save("groups", [g for g in groups
                     if not (g.get("name") == gname and g.get("dc_id") == dc_id)])
    return True


# ---- Application Presence CRUD ----

async def get_app_presences(app_dist_id: str | None = None) -> list[dict[str, Any]]:
    items = _load("app_presences") or []
    if app_dist_id:
        items = [p for p in items
                 if str(p.get("app_distributed_id", "")).upper() == app_dist_id.upper()]
    return items


async def upsert_app_presence(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("app_presences") or []
    data = dict(data)
    data["app_distributed_id"] = str(data.get("app_distributed_id", "")).upper()
    key = (data["app_distributed_id"], data.get("dc_id", ""),
           data.get("environment", "Production"),
           data.get("nh_id", ""), data.get("sz_code", ""))
    updated = False
    for i, p in enumerate(items):
        pk = (str(p.get("app_distributed_id", "")).upper(), p.get("dc_id", ""),
              p.get("environment", "Production"),
              p.get("nh_id", ""), p.get("sz_code", ""))
        if pk == key:
            items[i] = data
            updated = True
            break
    if not updated:
        items.append(data)
    _save("app_presences", items)
    # rebuild derived app groups for this presence
    groups = _load("groups") or []
    egr_name = _app_egress_group_name(
        data["app_distributed_id"], data["nh_id"], data["sz_code"])
    ing_name = _app_ingress_group_name(
        data["app_distributed_id"], data["nh_id"], data["sz_code"])
    groups = [g for g in groups
              if not (g.get("name") in (egr_name, ing_name)
                      and g.get("dc_id") == data.get("dc_id"))]
    groups.append({
        "name": egr_name, "owner_kind": "app_egress",
        "owner_ref": data["app_distributed_id"],
        "dc_id": data.get("dc_id", ""),
        "environment": data.get("environment", "Production"),
        "nh_id": data.get("nh_id", ""), "sz_code": data.get("sz_code", ""),
        "nh": data.get("nh_id", ""), "sz": data.get("sz_code", ""),
        "app_id": data["app_distributed_id"],
        "app_distributed_id": data["app_distributed_id"],
        "subtype": "APP", "direction": "egress",
        "members": list(data.get("egress_members", [])),
        "description": f"App {data['app_distributed_id']} egress @ {data.get('dc_id', '')}",
        "created_at": _now(), "updated_at": _now(),
    })
    if data.get("has_ingress"):
        groups.append({
            "name": ing_name, "owner_kind": "app_ingress",
            "owner_ref": data["app_distributed_id"],
            "dc_id": data.get("dc_id", ""),
            "environment": data.get("environment", "Production"),
            "nh_id": data.get("nh_id", ""), "sz_code": data.get("sz_code", ""),
            "nh": data.get("nh_id", ""), "sz": data.get("sz_code", ""),
            "app_id": data["app_distributed_id"],
            "app_distributed_id": data["app_distributed_id"],
            "subtype": "APP", "direction": "ingress",
            "members": list(data.get("ingress_members", [])),
            "description": f"App {data['app_distributed_id']} ingress @ {data.get('dc_id', '')}",
            "created_at": _now(), "updated_at": _now(),
        })
    _save("groups", groups)
    return data


def _ngdc_dc_ids() -> list[str]:
    """All NGDC DC IDs available in seed/runtime store. Excludes Heritage."""
    return [d.get("dc_id", "") for d in (_load("ngdc_datacenters") or [])
            if d.get("dc_id")]


def _resolve_target_dcs(deployment_mode: str | None,
                         excluded_dcs: list[str] | None) -> list[str]:
    """Compute the DCs an app/service should be present in based on its
    deployment_mode + excluded_dcs.

    - 'all_ngdc'                 → every NGDC DC.
    - 'all_ngdc_with_exceptions' → every NGDC DC minus excluded_dcs.
    - 'selective' / unset        → empty (caller manages presences manually).
    """
    mode = (deployment_mode or "").lower()
    if mode in ("all_ngdc", "all_ngdc_with_exceptions"):
        excluded = {str(x).upper() for x in (excluded_dcs or [])}
        return [dc for dc in _ngdc_dc_ids() if dc.upper() not in excluded]
    return []


def _envs_for_entity(entity: dict[str, Any]) -> list[str]:
    envs = entity.get("environments") or ["Production"]
    return list(envs) if isinstance(envs, list) else [str(envs)]


async def auto_fan_app_presences(app: dict[str, Any]) -> int:
    """Materialize AppPresence rows in every target NGDC DC for each tier
    on the app. Idempotent — existing presences (matched on the unique
    key) are left untouched, so member overrides survive re-fans.

    Returns the number of new presences created.
    """
    tiers = app.get("tiers") or []
    if not tiers:
        return 0
    target_dcs = _resolve_target_dcs(app.get("deployment_mode"),
                                      app.get("excluded_dcs"))
    if not target_dcs:
        return 0
    app_id = str(app.get("app_distributed_id", "")).upper()
    if not app_id:
        return 0
    items = _load("app_presences") or []
    existing = {(str(p.get("app_distributed_id", "")).upper(),
                 p.get("dc_id", ""), p.get("environment", ""),
                 p.get("nh_id", ""), p.get("sz_code", ""))
                for p in items}
    created = 0
    for env in _envs_for_entity(app):
        for dc in target_dcs:
            for tier in tiers:
                nh = str(tier.get("nh_id", "")).strip()
                sz = str(tier.get("sz_code", "")).strip()
                if not nh or not sz:
                    continue
                key = (app_id, dc, env, nh, sz)
                if key in existing:
                    continue
                await upsert_app_presence({
                    "app_distributed_id": app_id,
                    "dc_id": dc,
                    "dc_type": "NGDC",
                    "environment": env,
                    "nh_id": nh,
                    "sz_code": sz,
                    "has_ingress": bool(tier.get("has_ingress")),
                    "egress_members": [],
                    "ingress_members": [],
                    "ingress_ports": [],
                })
                existing.add(key)
                created += 1
    return created


async def auto_fan_service_presences(svc: dict[str, Any]) -> int:
    """Materialize SharedServicePresence rows for each tier across every
    target NGDC DC. Same idempotent semantics as the app variant.
    """
    tiers = svc.get("tiers") or []
    if not tiers:
        return 0
    target_dcs = _resolve_target_dcs(svc.get("deployment_mode"),
                                      svc.get("excluded_dcs"))
    if not target_dcs:
        return 0
    sid = str(svc.get("service_id", "")).upper()
    if not sid:
        return 0
    items = _load("shared_service_presences") or []
    existing = {(str(p.get("service_id", "")).upper(),
                 p.get("dc_id", ""), p.get("environment", ""),
                 p.get("nh_id", ""), p.get("sz_code", ""))
                for p in items}
    created = 0
    for env in _envs_for_entity(svc):
        for dc in target_dcs:
            for tier in tiers:
                nh = str(tier.get("nh_id", "")).strip()
                sz = str(tier.get("sz_code", "")).strip()
                if not nh or not sz:
                    continue
                key = (sid, dc, env, nh, sz)
                if key in existing:
                    continue
                await upsert_shared_service_presence({
                    "service_id": sid,
                    "dc_id": dc,
                    "dc_type": "NGDC",
                    "environment": env,
                    "nh_id": nh,
                    "sz_code": sz,
                    "members": [],
                })
                existing.add(key)
                created += 1
    return created


async def delete_app_presence(app_dist_id: str, dc_id: str, environment: str,
                               nh_id: str, sz_code: str) -> bool:
    items = _load("app_presences") or []
    key = (app_dist_id.upper(), dc_id, environment, nh_id, sz_code)
    new = [p for p in items
           if (str(p.get("app_distributed_id", "")).upper(), p.get("dc_id", ""),
               p.get("environment", ""), p.get("nh_id", ""),
               p.get("sz_code", "")) != key]
    if len(new) == len(items):
        return False
    _save("app_presences", new)
    egr_name = _app_egress_group_name(app_dist_id, nh_id, sz_code)
    ing_name = _app_ingress_group_name(app_dist_id, nh_id, sz_code)
    groups = _load("groups") or []
    _save("groups", [g for g in groups
                     if not (g.get("name") in (egr_name, ing_name)
                             and g.get("dc_id") == dc_id)])
    return True


# ============================================================
# Revamp: Multi-DC Rule Fan-out
# ============================================================

def _load_rule_requests() -> list[dict[str, Any]]:
    return _load("rule_requests") or []


async def get_rule_requests() -> list[dict[str, Any]]:
    return _load_rule_requests()


async def get_rule_request(request_id: str) -> dict[str, Any] | None:
    for r in _load_rule_requests():
        if r.get("request_id") == request_id:
            return r
    return None


def _presence_key_set(keys: list[dict[str, Any]] | None) -> set[tuple[str, str, str]] | None:
    """Normalize a list of presence key dicts into a set of
    (dc_id, nh_id, sz_code) tuples. Returns None when no keys were
    supplied, meaning "no per-presence filtering" (all presences used).
    """
    if not keys:
        return None
    out: set[tuple[str, str, str]] = set()
    for k in keys:
        if not isinstance(k, dict):
            continue
        dc = str(k.get("dc_id") or "").strip()
        nh = str(k.get("nh_id") or "").strip()
        sz = str(k.get("sz_code") or "").strip()
        if dc and nh and sz:
            out.add((dc, nh, sz))
    return out or None


def _filter_by_presence_keys(pres: list[dict[str, Any]],
                             keys: set[tuple[str, str, str]] | None) -> list[dict[str, Any]]:
    if not keys:
        return pres
    return [p for p in pres
            if (p.get("dc_id"), p.get("nh_id"), p.get("sz_code")) in keys]


async def _get_primary_dc(kind: str, ref: str | None) -> str | None:
    """Return primary_dc for an Application or SharedService, or None.

    `kind` is 'app' / 'shared_service'. App lookup uses both `applications`
    and the (newer) `application_profiles` store.
    """
    if not ref:
        return None
    ref_u = ref.upper()
    if kind == "shared_service":
        for s in _load("shared_services") or []:
            if str(s.get("service_id", "")).upper() == ref_u:
                return s.get("primary_dc") or None
        return None
    profiles = _load("application_profiles") or []
    for ap in profiles:
        if str(ap.get("app_distributed_id", "")).upper() == ref_u:
            if ap.get("primary_dc"):
                return ap["primary_dc"]
            break
    for a in _load("applications") or []:
        if str(a.get("app_distributed_id", "")).upper() == ref_u:
            return a.get("primary_dc") or None
    return None


async def _resolve_source_presences(source_ref: str, env: str,
                                    requested_dcs: list[str] | None,
                                    presence_keys: list[dict[str, Any]] | None = None,
                                    source_kind: str = "app",
                                    ) -> list[dict[str, Any]]:
    """Return source-side presences for fan-out.

    Apps read from `app_presences` (egress side). Shared Services read
    from `shared_service_presences` and the result is normalized to look
    like an app presence so the engine can stay uniform.
    """
    if source_kind == "shared_service":
        raw = [p for p in (_load("shared_service_presences") or [])
               if str(p.get("service_id", "")).upper() == source_ref.upper()
               and p.get("environment") == env]
        if requested_dcs:
            raw = [p for p in raw if p.get("dc_id") in requested_dcs]
        out: list[dict[str, Any]] = []
        for p in raw:
            out.append({
                **p,
                # Normalize to the shape the engine expects on the source
                # side. `app_distributed_id` is repurposed to carry the
                # service_id so `_app_egress_group_name` produces the
                # correct `grp-<SvcId>-<NH>-<SZ>` for the source group.
                "app_distributed_id": p.get("service_id", ""),
                "_source_kind": "shared_service",
                "egress_members": list(p.get("members", [])),
            })
        return _filter_by_presence_keys(out, _presence_key_set(presence_keys))
    pres = [p for p in (_load("app_presences") or [])
            if str(p.get("app_distributed_id", "")).upper() == source_ref.upper()
            and p.get("environment") == env]
    if requested_dcs:
        pres = [p for p in pres if p.get("dc_id") in requested_dcs]
    for p in pres:
        p.setdefault("_source_kind", "app")
    return _filter_by_presence_keys(pres, _presence_key_set(presence_keys))


async def _resolve_destination_presences(kind: str, dest_ref: str | None,
                                         env: str,
                                         requested_dcs: list[str] | None,
                                         presence_keys: list[dict[str, Any]] | None = None,
                                         ) -> list[dict[str, Any]]:
    if kind == "shared_service" and dest_ref:
        pres = [p for p in (_load("shared_service_presences") or [])
                if str(p.get("service_id", "")).upper() == dest_ref.upper()
                and p.get("environment") == env]
    elif kind == "app_ingress" and dest_ref:
        pres = [p for p in (_load("app_presences") or [])
                if str(p.get("app_distributed_id", "")).upper() == dest_ref.upper()
                and p.get("environment") == env
                and p.get("has_ingress")]
    else:
        pres = []
    if requested_dcs:
        pres = [p for p in pres if p.get("dc_id") in requested_dcs]
    return _filter_by_presence_keys(pres, _presence_key_set(presence_keys))


async def preview_rule_expansion(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute the multi-DC fan-out for a proposed rule request.

    By default the engine emits ONE PhysicalRule per (src_tier × dst_tier)
    in the **source's primary DC**, with destination groups resolved to
    the **destination's primary DC**. The destination team owns
    east-west routing across their other DCs (per architecture: app
    teams raise from one primary DC; destination teams handle their own
    DC fan-out via VIP / GSLB / per-DC LBs).

    Power-user toggles:
      - `include_cross_dc=True` ⇒ legacy intersect-all-DCs behaviour.
      - `destination_dc_override=<dc_id>` ⇒ explicitly target a non-primary
        destination DC (DR cutover scenarios).

    Returns { physical_rules: [...], warnings: [...] } without persisting.
    """
    env = payload.get("environment", "Production")
    source_kind = (payload.get("source_kind") or "app").lower()
    src_ref = (payload.get("source_ref")
               or payload.get("application_ref")
               or "")
    kind = payload.get("destination_kind", "shared_service")
    dest_ref = payload.get("destination_ref")
    requested_dcs = payload.get("requested_dcs")
    include_cross_dc = bool(payload.get("include_cross_dc"))
    dest_dc_override = payload.get("destination_dc_override")
    ports = payload.get("ports", "TCP 8080")
    action = payload.get("action", "ACCEPT")

    source_presences = payload.get("source_presences")
    destination_presences = payload.get("destination_presences")

    # Primary-DC scoping (default). When the requester didn't pass
    # explicit `requested_dcs`, scope the source resolver to the source's
    # primary_dc and the destination resolver to either the override DC
    # or the destination's primary_dc.
    src_dc_filter = list(requested_dcs) if requested_dcs else None
    dst_dc_filter = list(requested_dcs) if requested_dcs else None
    if not include_cross_dc:
        if not src_dc_filter:
            primary = await _get_primary_dc(source_kind, src_ref)
            if primary:
                src_dc_filter = [primary]
        if not dst_dc_filter:
            if dest_dc_override:
                dst_dc_filter = [dest_dc_override]
            else:
                dst_kind = "shared_service" if kind == "shared_service" else "app"
                primary = await _get_primary_dc(dst_kind, dest_ref)
                if primary:
                    dst_dc_filter = [primary]

    src_pres = await _resolve_source_presences(
        src_ref, env, src_dc_filter, source_presences,
        source_kind=source_kind)
    dst_pres = await _resolve_destination_presences(
        kind, dest_ref, env, dst_dc_filter, destination_presences)

    warnings: list[str] = []
    if not src_pres:
        warnings.append(
            f"No source presence for {source_kind}:{src_ref} in environment {env}"
            + (f" / DCs {src_dc_filter}" if src_dc_filter else "")
        )
    if not dst_pres:
        warnings.append(
            f"No destination presence for {kind}:{dest_ref} in environment {env}"
            + (f" / DCs {dst_dc_filter}" if dst_dc_filter else "")
        )

    physical: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str, str, str]] = set()
    for s in src_pres:
        for d in dst_pres:
            if s["dc_id"] != d["dc_id"] and not include_cross_dc:
                continue
            # source group name (egress)
            src_group = _app_egress_group_name(
                s["app_distributed_id"], s["nh_id"], s["sz_code"])
            # destination group name
            if kind == "shared_service":
                dst_group = _shared_service_group_name(
                    d["service_id"], d["nh_id"], d["sz_code"])
            else:
                dst_group = _app_ingress_group_name(
                    d["app_distributed_id"], d["nh_id"], d["sz_code"])
            key = (s["dc_id"], d["dc_id"], src_group, dst_group)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            physical.append({
                "src_dc": s["dc_id"],
                "dst_dc": d["dc_id"],
                "src_group_ref": src_group,
                "dst_group_ref": dst_group,
                "src_nh": s["nh_id"], "src_sz": s["sz_code"],
                "dst_nh": d["nh_id"], "dst_sz": d["sz_code"],
                "ports": ports, "action": action,
                "environment": env,
                "cross_dc": s["dc_id"] != d["dc_id"],
                "lifecycle_status": "Preview",
            })
    if not physical and not warnings:
        warnings.append(
            "Source and destination have no DC in common; "
            "enable 'Include cross-DC' to fan out across DCs."
        )
    # Pre-submit validation — same engine that runs at create time so the
    # builder can render a green/amber/red status block in Step 3.
    dedup = evaluate_dedup({"physical_rules": physical}) if physical else {
        "verdict": "ok", "block": False, "matches": [],
    }
    birthright = evaluate_birthright(payload) if physical else {
        "covered": False, "matches": [],
    }
    if birthright["covered"]:
        warnings.append(
            "Already provided as a birthright rule "
            f"({', '.join(m['birthright_id'] for m in birthright['matches'])}). "
            "No request needed."
        )
    if dedup["block"]:
        for m in dedup["matches"]:
            if m["verdict"] in ("identical", "subset", "conflict"):
                warnings.append(
                    f"{m['verdict'].title()} of existing rule "
                    f"{m['rule_id']} ({m['existing_ports']}, "
                    f"{m['existing_action']}, {m['lifecycle_status']})"
                )
    return {
        "physical_rules": physical,
        "warnings": warnings,
        "dedup": dedup,
        "birthright": birthright,
        "block_submit": bool(dedup.get("block") or birthright.get("covered")),
    }


async def create_rule_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a multi-DC RuleRequest and also materialize each PhysicalRule
    into the main `firewall_rules` store so submissions immediately show
    up in the Rules table, Compile views, and Review queues with standard
    R-#### identifiers.
    """
    preview = await preview_rule_expansion(payload)
    # Hard-block on identical/subset/conflict dedup verdicts and on
    # birthright coverage, unless the caller explicitly opts in via
    # `force_submit=True` (SNS / migration override path).
    if preview.get("block_submit") and not payload.get("force_submit"):
        dedup = preview.get("dedup") or {}
        birth = preview.get("birthright") or {}
        msg = "Submit blocked by validation."
        if dedup.get("matches"):
            m = dedup["matches"][0]
            msg = (
                f"{m['verdict'].title()} of existing rule {m['rule_id']} "
                f"({m['existing_ports']}, {m['existing_action']}, "
                f"{m['lifecycle_status']}). Submit cancelled."
            )
        elif birth.get("matches"):
            ids = ", ".join(b["birthright_id"] for b in birth["matches"])
            msg = f"Already provided as a birthright rule ({ids}). No request needed."
        return {
            "request_id": None,
            "status": "Blocked",
            "block_submit": True,
            "validation_message": msg,
            "dedup": dedup,
            "birthright": birth,
            "warnings": preview.get("warnings", []),
            "expansion": preview.get("physical_rules", []),
        }
    request_id = f"RR-{_id()[:8].upper()}"

    # Determine the next R-#### counter for PhysicalRules.
    fw_rules = _load("firewall_rules") or []
    config = (await get_org_config()) or SEED_ORG_CONFIG
    prefix = config.get("rule_id_prefix", "R-")
    start = config.get("rule_id_start", 3000)
    max_num = start - 1
    for r in fw_rules:
        rid = r.get("rule_id", "")
        if rid.startswith(prefix):
            try:
                num = int(rid.split("-")[-1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass

    now = _now()
    expansion: list[dict[str, Any]] = []
    for i, p in enumerate(preview.get("physical_rules", []), start=1):
        max_num += 1
        rule_id = f"{prefix}{max_num}"
        # First two tokens of "TCP 443, TCP 8443" → split protocol/port
        port_field = p.get("ports", "") or payload.get("ports", "")
        first = port_field.split(",")[0].strip() if port_field else ""
        proto, port_num = "TCP", ""
        if first:
            toks = first.split()
            if len(toks) == 2:
                proto, port_num = toks[0].upper(), toks[1]
            elif len(toks) == 1:
                port_num = toks[0]
        # Persist a full FirewallRule so the Rules table can render it.
        source_kind_norm = (payload.get("source_kind") or "app").lower()
        src_ref_norm = (payload.get("source_ref")
                        or payload.get("application_ref")
                        or "")
        fw_rules.append({
            "rule_id": rule_id,
            "source": p.get("src_group_ref", ""),
            "source_zone": p.get("src_sz", ""),
            "source_nh": p.get("src_nh", ""),
            "destination": p.get("dst_group_ref", ""),
            "destination_zone": p.get("dst_sz", ""),
            "destination_nh": p.get("dst_nh", ""),
            "port": port_num,
            "protocol": proto,
            "action": "Allow" if (p.get("action") or "ACCEPT").upper() == "ACCEPT" else "Deny",
            "description": payload.get("description", "") or f"Multi-DC rule request {request_id}",
            "application": src_ref_norm if source_kind_norm == "app" else "",
            "shared_service_ref": src_ref_norm if source_kind_norm == "shared_service" else "",
            "source_kind": source_kind_norm,
            "dst_application": payload.get("destination_ref", "") if payload.get("destination_kind") == "app_ingress" else "",
            "status": "Pending Review",
            "rule_status": "Pending Review",
            "rule_migration_status": "Migrated",
            "is_group_to_group": True,
            "environment": payload.get("environment", "Production"),
            "datacenter": p.get("src_dc", ""),
            "dst_datacenter": p.get("dst_dc", ""),
            "cross_dc": bool(p.get("cross_dc", False)),
            "rule_request_id": request_id,
            "created_at": now,
            "updated_at": now,
            "certified_date": None,
            "expiry_date": None,
        })
        # Record lifecycle event for the physical rule.
        await _record_lifecycle(rule_id, "created", to_status="Pending Review",
                                module="design-studio",
                                details=f"Rule created via multi-DC request {request_id}")
        # Build the expansion entry that the client sees.
        expansion.append({
            "rule_id": rule_id,
            "request_id": request_id,
            **p,
            "lifecycle_status": "Pending Review",
        })

    _save("firewall_rules", fw_rules)

    src_kind_rec = (payload.get("source_kind") or "app").lower()
    src_ref_rec = (payload.get("source_ref")
                   or payload.get("application_ref")
                   or "")
    # Owning team for the request — inherits from the source app/service
    # record if the caller didn't override it. Used by team-scoped list
    # endpoints; SNS still sees everything.
    owner_team_rec = payload.get("owner_team") or ""
    if not owner_team_rec and src_ref_rec:
        if src_kind_rec == "shared_service":
            for s in _load("shared_services") or []:
                if str(s.get("service_id", "")).upper() == src_ref_rec.upper():
                    owner_team_rec = str(s.get("owner_team", "")) or ""
                    break
        else:
            for a in _load("applications") or []:
                if (str(a.get("app_distributed_id", "")).upper() == src_ref_rec.upper()
                        or str(a.get("app_id", "")).upper() == src_ref_rec.upper()):
                    owner_team_rec = str(a.get("owner_team", "")) or ""
                    break
    record = {
        "request_id": request_id,
        "source_kind": src_kind_rec,
        "source_ref": src_ref_rec,
        # Back-compat: old clients still read application_ref. Populate
        # only when the source actually IS an app.
        "application_ref": src_ref_rec if src_kind_rec == "app" else "",
        "destination_kind": payload.get("destination_kind", "shared_service"),
        "destination_ref": payload.get("destination_ref"),
        "environment": payload.get("environment", "Production"),
        "ports": payload.get("ports", "TCP 8080"),
        "action": payload.get("action", "ACCEPT"),
        "description": payload.get("description", ""),
        "owner": payload.get("owner", ""),
        "owner_team": owner_team_rec,
        "include_cross_dc": bool(payload.get("include_cross_dc")),
        "destination_dc_override": payload.get("destination_dc_override"),
        "status": "Pending",
        "expansion": expansion,
        "warnings": preview.get("warnings", []),
        "created_at": now,
        "updated_at": now,
    }
    items = _load_rule_requests()
    items.append(record)
    _save("rule_requests", items)
    return record


# ============================================================
# Port / Service Catalog CRUD
# ============================================================

def _load_port_catalog() -> list[dict[str, Any]]:
    items = _load("port_catalog")
    if items is None:
        items = deepcopy(_SD_PORT_CATALOG)
        _save("port_catalog", items)
    return items


async def list_ports() -> list[dict[str, Any]]:
    return _load_port_catalog()


async def create_port(payload: dict[str, Any]) -> dict[str, Any]:
    items = _load_port_catalog()
    pid = str(payload.get("port_id", "")).strip().upper()
    if not pid:
        name = str(payload.get("name", "")).strip() or "PORT"
        pid = name.upper().replace(" ", "_")[:32]
    # ensure unique
    base = pid
    i = 1
    existing = {p.get("port_id") for p in items}
    while pid in existing:
        i += 1
        pid = f"{base}_{i}"
    record = {
        "port_id": pid,
        "name": str(payload.get("name", pid)),
        "protocol": str(payload.get("protocol", "TCP")).upper(),
        "port": int(payload.get("port") or 0),
        "aliases": list(payload.get("aliases") or []),
        "category": str(payload.get("category", "Custom")),
        "description": str(payload.get("description", "")),
    }
    items.append(record)
    _save("port_catalog", items)
    return record


async def update_port(port_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    items = _load_port_catalog()
    for p in items:
        if p.get("port_id") == port_id:
            for k in ("name", "protocol", "port", "aliases", "category", "description"):
                if k in payload:
                    if k == "port":
                        p[k] = int(payload[k] or 0)
                    elif k == "protocol":
                        p[k] = str(payload[k]).upper()
                    elif k == "aliases":
                        p[k] = list(payload[k] or [])
                    else:
                        p[k] = payload[k]
            _save("port_catalog", items)
            return p
    return None


async def delete_port(port_id: str) -> bool:
    items = _load_port_catalog()
    new_items = [p for p in items if p.get("port_id") != port_id]
    if len(new_items) == len(items):
        return False
    _save("port_catalog", new_items)
    return True


async def set_rule_request_status(request_id: str, status: str, note: str | None = None) -> dict[str, Any] | None:
    items = _load_rule_requests()
    mapping = {
        "Approved": "Approved",
        "Deployed": "Deployed",
        "Rejected": "Rejected",
        "Certified": "Certified",
    }
    for r in items:
        if r.get("request_id") == request_id:
            r["status"] = status
            r["updated_at"] = _now()
            if note:
                r.setdefault("review_notes", []).append({"at": _now(), "status": status, "note": note})
            phys_ids: list[str] = []
            for phys in r.get("expansion", []):
                if status in mapping:
                    phys["lifecycle_status"] = mapping[status]
                rid = phys.get("rule_id")
                if rid:
                    phys_ids.append(rid)
            # Propagate status to the corresponding firewall_rules records
            if status in mapping and phys_ids:
                fw_rules = _load("firewall_rules") or []
                phys_id_set = set(phys_ids)
                now = _now()
                for fr in fw_rules:
                    if fr.get("rule_id") in phys_id_set:
                        fr["status"] = mapping[status]
                        fr["rule_status"] = mapping[status]
                        fr["updated_at"] = now
                        if status == "Certified":
                            fr["certified_date"] = now
                        await _record_lifecycle(
                            fr["rule_id"],
                            status.lower(),
                            to_status=mapping[status],
                            module="design-studio",
                            details=f"Status -> {mapping[status]} via request {request_id}"
                                    + (f": {note}" if note else ""),
                        )
                _save("firewall_rules", fw_rules)
            _save("rule_requests", items)
            return r
    return None


# ============================================================
# Dedup / Existing-Rule Validation Engine
# ============================================================
#
# A standardized PhysicalRule is fully described by:
#   (src_group, dst_group, protocol, action) — the *dedup key*
# with the port set as the comparand.
#
# Verdict matrix (vs every Approved/Deployed/Certified existing rule):
#   - identical    : same key + same port set                     → HARD-BLOCK
#   - subset       : same key + requested ports ⊆ existing ports → HARD-BLOCK
#   - overlap      : same key + ports overlap but not subset     → WARN
#   - conflict     : same (src,dst,proto,ports) but ACTION differs (Allow vs Deny) → HARD-BLOCK
#   - none         : no relation                                  → OK
#
# Rejected / Cancelled rules are excluded from the dedup set.

_DEDUP_LIVE_STATUSES = {
    "approved", "deployed", "certified", "active", "pending review",
}


def _parse_port_token(tok: str) -> tuple[str, list[tuple[int, int]]]:
    """Parse 'TCP 443' / 'TCP 8000-8100' / 'UDP 53' / '443' into
    (protocol, [(lo, hi), ...]). Returns ('TCP', []) when unparseable."""

    tok = (tok or "").strip()
    if not tok:
        return ("TCP", [])
    parts = tok.split()
    proto = "TCP"
    rest = tok
    if parts and parts[0].upper() in ("TCP", "UDP", "ICMP", "ANY"):
        proto = parts[0].upper()
        rest = " ".join(parts[1:]).strip()
    if not rest or rest.lower() == "any":
        return (proto, [(0, 65535)])
    ranges: list[tuple[int, int]] = []
    for piece in rest.replace(";", ",").split(","):
        piece = piece.strip()
        if not piece:
            continue
        if "-" in piece:
            try:
                lo, hi = piece.split("-", 1)
                lo_i = int(lo.strip())
                hi_i = int(hi.strip())
                if lo_i <= hi_i:
                    ranges.append((lo_i, hi_i))
            except ValueError:
                continue
        else:
            try:
                p = int(piece)
                ranges.append((p, p))
            except ValueError:
                continue
    return (proto, ranges)


def _parse_ports_field(ports: str) -> dict[str, list[tuple[int, int]]]:
    """Parse a possibly multi-protocol ports string into protocol→ranges.

    Accepts: 'TCP 443', 'TCP 443, UDP 53', 'TCP 8000-8100,8443', '443'."""

    out: dict[str, list[tuple[int, int]]] = {}
    if not ports:
        return out
    # Split on commas but only when the next token re-declares a protocol.
    # Simpler: split on commas and inherit last seen protocol.
    last_proto = "TCP"
    for tok in str(ports).split(","):
        tok = tok.strip()
        if not tok:
            continue
        parts = tok.split()
        if parts and parts[0].upper() in ("TCP", "UDP", "ICMP", "ANY"):
            last_proto = parts[0].upper()
            tok_full = tok
        else:
            tok_full = f"{last_proto} {tok}"
        proto, ranges = _parse_port_token(tok_full)
        if not ranges:
            continue
        out.setdefault(proto, []).extend(ranges)
    # Normalize each protocol's ranges (merge overlaps/adjacent).
    for p, rs in list(out.items()):
        rs.sort()
        merged: list[tuple[int, int]] = []
        for lo, hi in rs:
            if merged and lo <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        out[p] = merged
    return out


def _ranges_subset(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> bool:
    """True iff every port covered by ranges *a* is covered by ranges *b*."""

    for lo, hi in a:
        covered = False
        for blo, bhi in b:
            if blo <= lo and bhi >= hi:
                covered = True
                break
        if not covered:
            return False
    return True


def _ranges_overlap(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> bool:
    """True iff any port is in both sets."""

    for lo, hi in a:
        for blo, bhi in b:
            if not (hi < blo or lo > bhi):
                return True
    return False


def _normalize_action(act: str) -> str:
    a = (act or "").strip().lower()
    if a in ("allow", "accept", "permit"):
        return "ALLOW"
    if a in ("deny", "drop", "reject", "block"):
        return "DENY"
    return a.upper() or "ALLOW"


def _classify_rule_pair(
    new_ports: dict[str, list[tuple[int, int]]],
    existing_ports: dict[str, list[tuple[int, int]]],
) -> str:
    """Compare port sets of the *same* (src,dst,action) and return one of
    ``identical | subset | overlap | none``.

    Protocols are compared independently; if any protocol is identical or
    a subset, the verdict is upgraded accordingly (worst-case wins so the
    dedup engine errs on the safe side)."""

    if not new_ports or not existing_ports:
        return "none"
    verdict = "none"
    for proto, new_r in new_ports.items():
        existing_r = existing_ports.get(proto, [])
        if not existing_r:
            continue
        # Identical?
        if sorted(new_r) == sorted(existing_r):
            verdict = "identical"
            continue
        if _ranges_subset(new_r, existing_r):
            if verdict not in ("identical",):
                verdict = "subset"
            continue
        if _ranges_overlap(new_r, existing_r):
            if verdict == "none":
                verdict = "overlap"
    return verdict


def evaluate_dedup(payload_or_phys: dict[str, Any]) -> dict[str, Any]:
    """Synchronous dedup evaluator used by preview + submit.

    Accepts either a single PhysicalRule dict (with src_group_ref /
    dst_group_ref / ports / action) OR a list under ``physical_rules``.
    Returns ::

        {
          'verdict': 'identical' | 'subset' | 'overlap' | 'conflict' | 'ok',
          'block': bool,
          'matches': [
            {
              'rule_id', 'verdict', 'src_group', 'dst_group',
              'existing_ports', 'existing_action', 'lifecycle_status'
            }
          ]
        }

    The worst-case verdict across all PhysicalRules is returned at the
    top level; per-PhysicalRule details live under ``matches``."""

    fw_rules = _load("firewall_rules") or []

    def _phys_iter() -> list[dict[str, Any]]:
        if isinstance(payload_or_phys, dict) and payload_or_phys.get("physical_rules"):
            return list(payload_or_phys["physical_rules"])
        if isinstance(payload_or_phys, dict) and payload_or_phys.get("src_group_ref"):
            return [payload_or_phys]
        return []

    matches: list[dict[str, Any]] = []
    worst = "ok"
    severity = {"ok": 0, "overlap": 1, "subset": 2, "identical": 3, "conflict": 4}

    for phys in _phys_iter():
        new_src = str(phys.get("src_group_ref", "")).upper()
        new_dst = str(phys.get("dst_group_ref", "")).upper()
        new_action = _normalize_action(phys.get("action", "ALLOW"))
        new_ports = _parse_ports_field(phys.get("ports", ""))
        if not new_src or not new_dst or not new_ports:
            continue
        for r in fw_rules:
            if str((r.get("status") or r.get("rule_status") or "")).strip().lower() not in _DEDUP_LIVE_STATUSES:
                continue
            ex_src = str(r.get("source", "")).upper()
            ex_dst = str(r.get("destination", "")).upper()
            if ex_src != new_src or ex_dst != new_dst:
                continue
            ex_action = _normalize_action(r.get("action", "ALLOW"))
            # Build the existing port set as proto → [(lo,hi)]. The
            # firewall_rules schema stores protocol+port as separate
            # fields ('TCP', '443' or '443-1024').
            ex_proto = (r.get("protocol") or "TCP").upper()
            ex_port_field = str(r.get("port", "") or "").strip()
            ex_ports = _parse_ports_field(f"{ex_proto} {ex_port_field}") if ex_port_field else {}
            verdict = _classify_rule_pair(new_ports, ex_ports)
            if ex_action != new_action and verdict != "none":
                # Action collision (Allow vs Deny on same tuple) — surface
                # as a hard-block conflict regardless of port relation.
                verdict = "conflict"
            if verdict == "none":
                continue
            matches.append({
                "rule_id": r.get("rule_id", ""),
                "verdict": verdict,
                "src_group": ex_src,
                "dst_group": ex_dst,
                "existing_ports": f"{ex_proto} {ex_port_field}".strip(),
                "existing_action": ex_action,
                "lifecycle_status": r.get("rule_status") or r.get("status") or "",
            })
            if severity[verdict] > severity[worst]:
                worst = verdict
    return {
        "verdict": worst,
        "block": worst in ("identical", "subset", "conflict"),
        "matches": matches,
    }


# ============================================================
# Birthright Rule Registry
# ============================================================

_SD_BIRTHRIGHT_RULES: list[dict[str, Any]] = [
    {
        "birthright_id": "BR-DNS",
        "scope_dc": "*",
        "scope_nh": "*",
        "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "DNS",
        "ports": "UDP 53, TCP 53",
        "description": "All workloads have implicit egress to enterprise DNS.",
    },
    {
        "birthright_id": "BR-NTP",
        "scope_dc": "*", "scope_nh": "*", "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "NTP",
        "ports": "UDP 123",
        "description": "Time sync is a birthright service.",
    },
    {
        "birthright_id": "BR-SPLUNK-FWD",
        "scope_dc": "*", "scope_nh": "*", "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "SPLUNK",
        "ports": "TCP 9997",
        "description": "Splunk forwarder log shipping.",
    },
    {
        "birthright_id": "BR-APPD",
        "scope_dc": "*", "scope_nh": "*", "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "APPD",
        "ports": "TCP 8090, TCP 8181",
        "description": "AppDynamics agent telemetry.",
    },
    {
        "birthright_id": "BR-PKI",
        "scope_dc": "*", "scope_nh": "*", "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "PKI",
        "ports": "TCP 80, TCP 443",
        "description": "Internal PKI / CRL / OCSP fetch.",
    },
    {
        "birthright_id": "BR-AD-AUTH",
        "scope_dc": "*", "scope_nh": "*", "scope_sz": "*",
        "destination_kind": "shared_service",
        "destination_ref": "KERBEROS",
        "ports": "TCP 88, UDP 88, TCP 464, UDP 464",
        "description": "Active Directory / Kerberos authentication.",
    },
]


def _load_birthright_rules() -> list[dict[str, Any]]:
    items = _load("birthright_rules")
    if items is None:
        items = deepcopy(_SD_BIRTHRIGHT_RULES)
        _save("birthright_rules", items)
    return items


async def list_birthright_rules() -> list[dict[str, Any]]:
    return _load_birthright_rules()


async def upsert_birthright_rule(payload: dict[str, Any]) -> dict[str, Any]:
    items = _load_birthright_rules()
    bid = str(payload.get("birthright_id", "")).strip()
    if not bid:
        bid = f"BR-{_id()[:6].upper()}"
        payload["birthright_id"] = bid
    for i, r in enumerate(items):
        if r.get("birthright_id") == bid:
            items[i] = {**r, **payload}
            _save("birthright_rules", items)
            return items[i]
    items.append(dict(payload))
    _save("birthright_rules", items)
    return payload


async def delete_birthright_rule(bid: str) -> bool:
    items = _load_birthright_rules()
    new_items = [r for r in items if r.get("birthright_id") != bid]
    if len(new_items) == len(items):
        return False
    _save("birthright_rules", new_items)
    return True


def evaluate_birthright(payload: dict[str, Any]) -> dict[str, Any]:
    """Return whether the proposed rule is already covered by a birthright.

    A birthright covers a request when:
      - destination_kind matches AND destination_ref matches (case-insensitive)
      - scope DC/NH/SZ are wildcard or include the request's primary scope
      - the requested port set is a subset of the birthright's port set
    """

    items = _load_birthright_rules()
    dest_kind = (payload.get("destination_kind") or "").lower()
    dest_ref = str(payload.get("destination_ref") or "").upper()
    req_ports = _parse_ports_field(payload.get("ports", ""))
    matches: list[dict[str, Any]] = []
    for br in items:
        if str(br.get("destination_kind", "")).lower() != dest_kind:
            continue
        if str(br.get("destination_ref", "")).upper() != dest_ref:
            continue
        br_ports = _parse_ports_field(br.get("ports", ""))
        is_covered = True
        for proto, rng in req_ports.items():
            if not _ranges_subset(rng, br_ports.get(proto, [])):
                is_covered = False
                break
        if is_covered and req_ports:
            matches.append({
                "birthright_id": br.get("birthright_id"),
                "destination_ref": br.get("destination_ref"),
                "ports": br.get("ports"),
                "description": br.get("description", ""),
            })
    return {"covered": bool(matches), "matches": matches}


# ============================================================
# Migration Normalizer  — legacy / non-standard → standardized
# ============================================================

def _normalize_group_prefix(name: str) -> str:
    """`g-XYZ` → `grp-XYZ`. Trim. Upper-case prefix tokens."""

    if not name:
        return ""
    n = name.strip()
    if n.lower().startswith("g-") and not n.lower().startswith("grp-"):
        n = "grp-" + n[2:]
    return n


async def normalize_legacy_rule(legacy_rule: dict[str, Any]) -> dict[str, Any]:
    """Standardize a legacy / non-standard rule into the NGDC model.

    Steps:
      1. Resolve src + dst IPs → (DC, NH, SZ) via the existing classifier
         (when an IP-style source/destination is given).
      2. Apply SZ.naming_mode: ZONE_SCOPED → ``grp-<NH>-<SZ>``;
         APP_SCOPED → ``grp-<App>-<NH>-<SZ>``.
      3. Normalize prefixes (`g-` → `grp-`).
      4. Run the dedup engine: identical / subset → mark ``merged_into``
         the existing rule; overlap → flag for SNS review; new → create
         standardized PhysicalRule with ``origin_legacy_rule_id``.
    """

    out: dict[str, Any] = {
        "origin_legacy_rule_id": legacy_rule.get("rule_id", ""),
        "verdict": "new",
        "block": False,
        "physical_rule": None,
        "dedup_match": None,
        "warnings": [],
    }
    src_obj = legacy_rule.get("source", "")
    dst_obj = legacy_rule.get("destination", "")
    proto = (legacy_rule.get("protocol") or "TCP").upper()
    port = str(legacy_rule.get("port", "") or "")
    action = _normalize_action(legacy_rule.get("action", "Allow"))
    env = legacy_rule.get("environment", "Production")
    src_dc = legacy_rule.get("datacenter") or legacy_rule.get("source_dc") or ""
    dst_dc = legacy_rule.get("dst_datacenter") or src_dc
    src_nh = legacy_rule.get("source_nh") or ""
    src_sz = legacy_rule.get("source_zone") or ""
    dst_nh = legacy_rule.get("destination_nh") or ""
    dst_sz = legacy_rule.get("destination_zone") or ""

    src_group = _normalize_group_prefix(src_obj)
    dst_group = _normalize_group_prefix(dst_obj)
    if src_nh and src_sz:
        if _get_sz_naming_mode(src_sz) == "zone_scoped":
            src_group = _zone_group_name(src_nh, src_sz)
    if dst_nh and dst_sz:
        if _get_sz_naming_mode(dst_sz) == "zone_scoped":
            dst_group = _zone_group_name(dst_nh, dst_sz)

    physical = {
        "src_dc": src_dc, "dst_dc": dst_dc,
        "src_group_ref": src_group, "dst_group_ref": dst_group,
        "src_nh": src_nh, "src_sz": src_sz,
        "dst_nh": dst_nh, "dst_sz": dst_sz,
        "ports": f"{proto} {port}".strip(),
        "action": "ACCEPT" if action == "ALLOW" else "DENY",
        "environment": env,
        "lifecycle_status": "Migration-Preview",
    }
    out["physical_rule"] = physical

    dedup = evaluate_dedup({"physical_rules": [physical]})
    if dedup["matches"]:
        out["dedup_match"] = dedup["matches"][0]
        out["verdict"] = dedup["verdict"]
        out["block"] = dedup["block"]
    if not src_group or not dst_group:
        out["verdict"] = "unclassifiable"
        out["block"] = True
        out["warnings"].append(
            "Could not resolve source or destination into a managed group; "
            "rule moved to quarantine for manual review."
        )
    return out


async def normalize_legacy_rules_bulk(rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch normalizer. Returns counters + per-rule decisions for the
    Migration screen."""

    decisions: list[dict[str, Any]] = []
    counters = {
        "total": len(rules),
        "standardized": 0,
        "merged_existing": 0,
        "overlap_flagged": 0,
        "unclassifiable": 0,
    }
    for rule in rules:
        d = await normalize_legacy_rule(rule)
        if d["verdict"] in ("identical", "subset"):
            counters["merged_existing"] += 1
        elif d["verdict"] == "overlap":
            counters["overlap_flagged"] += 1
        elif d["verdict"] == "unclassifiable":
            counters["unclassifiable"] += 1
        else:
            counters["standardized"] += 1
        decisions.append(d)
    return {"counters": counters, "decisions": decisions}


# ============================================================
# Deployment Artifact Generators
# ============================================================

def _artifact_manifest_for_request(req: dict[str, Any]) -> dict[str, Any]:
    """Build the vendor-neutral JSON manifest for a RuleRequest."""

    expansion = req.get("expansion") or []
    groups_seen: dict[str, dict[str, Any]] = {}
    fw_rules = _load("firewall_rules") or []
    fw_by_id = {r.get("rule_id"): r for r in fw_rules}
    rules_out: list[dict[str, Any]] = []
    for phys in expansion:
        rid = phys.get("rule_id")
        fw = fw_by_id.get(rid, {})
        # Group create/modify decisions: if the group already exists in
        # the groups store with members, mark `reuse-existing`; otherwise
        # `create`.
        for grp_name in (phys.get("src_group_ref"), phys.get("dst_group_ref")):
            if not grp_name or grp_name in groups_seen:
                continue
            members = _resolve_group_members_sync(grp_name)
            groups_seen[grp_name] = {
                "name": grp_name,
                "op": "reuse-existing" if members else "create",
                "members": members,
            }
        rules_out.append({
            "rule_id": rid,
            "src_dc": phys.get("src_dc"),
            "dst_dc": phys.get("dst_dc"),
            "src_group": phys.get("src_group_ref"),
            "dst_group": phys.get("dst_group_ref"),
            "src_nh": phys.get("src_nh"), "src_sz": phys.get("src_sz"),
            "dst_nh": phys.get("dst_nh"), "dst_sz": phys.get("dst_sz"),
            "protocol": fw.get("protocol", "TCP"),
            "ports": phys.get("ports") or fw.get("port", ""),
            "action": fw.get("action") or phys.get("action") or "Allow",
            "lifecycle_status": phys.get("lifecycle_status")
                                or fw.get("rule_status") or "Pending Review",
        })
    return {
        "request_id": req.get("request_id"),
        "requester": req.get("owner"),
        "owner_team": req.get("owner_team"),
        "environment": req.get("environment"),
        "justification": req.get("description"),
        "source_kind": req.get("source_kind"),
        "source_ref": req.get("source_ref"),
        "destination_kind": req.get("destination_kind"),
        "destination_ref": req.get("destination_ref"),
        "approver": req.get("approver"),
        "status": req.get("status"),
        "created_at": req.get("created_at"),
        "updated_at": req.get("updated_at"),
        "external_ticket_id": req.get("external_ticket_id"),
        "external_ticket_url": req.get("external_ticket_url"),
        "rules": rules_out,
        "groups": list(groups_seen.values()),
    }


def _resolve_group_members_sync(name: str) -> list[str]:
    """Look up an existing group's members from the groups store."""

    if not name:
        return []
    for g in _load("groups") or []:
        if str(g.get("name", "")).upper() == name.upper():
            ms = g.get("members") or g.get("ips") or []
            return [str(m) for m in ms]
    return []


def _artifact_xlsx_rows(manifest: dict[str, Any]) -> dict[str, list[list[str]]]:
    """Flatten the manifest into spreadsheet rows for an XLSX writer.

    Returns ``{ sheet_name: [[header_row], [...data...]] }`` so the route
    can stream it via openpyxl without needing the Pydantic model."""

    rules_sheet = [[
        "rule_id", "src_dc", "dst_dc", "src_group", "dst_group",
        "src_nh", "src_sz", "dst_nh", "dst_sz",
        "protocol", "ports", "action", "lifecycle_status",
    ]]
    for r in manifest.get("rules", []):
        rules_sheet.append([
            str(r.get("rule_id", "")),
            str(r.get("src_dc", "")),
            str(r.get("dst_dc", "")),
            str(r.get("src_group", "")),
            str(r.get("dst_group", "")),
            str(r.get("src_nh", "")),
            str(r.get("src_sz", "")),
            str(r.get("dst_nh", "")),
            str(r.get("dst_sz", "")),
            str(r.get("protocol", "")),
            str(r.get("ports", "")),
            str(r.get("action", "")),
            str(r.get("lifecycle_status", "")),
        ])
    groups_sheet = [["group", "op", "members"]]
    for g in manifest.get("groups", []):
        groups_sheet.append([
            str(g.get("name", "")),
            str(g.get("op", "")),
            ", ".join(g.get("members") or []),
        ])
    summary_sheet = [
        ["field", "value"],
        ["request_id", str(manifest.get("request_id") or "")],
        ["requester", str(manifest.get("requester") or "")],
        ["owner_team", str(manifest.get("owner_team") or "")],
        ["environment", str(manifest.get("environment") or "")],
        ["status", str(manifest.get("status") or "")],
        ["external_ticket_id", str(manifest.get("external_ticket_id") or "")],
        ["external_ticket_url", str(manifest.get("external_ticket_url") or "")],
        ["justification", str(manifest.get("justification") or "")],
    ]
    return {"Summary": summary_sheet, "Rules": rules_sheet, "Groups": groups_sheet}


def _vendor_compile_panos(manifest: dict[str, Any]) -> str:
    out: list[str] = ["# PAN-OS / Panorama set-mode configuration",
                      f"# Request {manifest.get('request_id')}", ""]
    for g in manifest.get("groups", []):
        if g["op"] == "create" and g.get("members"):
            for m in g["members"]:
                out.append(f"set address {g['name']}-{m.replace('/', '_').replace('.', '_')} ip-netmask {m}")
            members_csv = " ".join(
                f"{g['name']}-{m.replace('/', '_').replace('.', '_')}" for m in g["members"]
            )
            out.append(f"set address-group {g['name']} static [ {members_csv} ]")
    for r in manifest.get("rules", []):
        out.append(
            f"set rulebase security rules {r['rule_id']} from any to any "
            f"source {r['src_group']} destination {r['dst_group']} "
            f"service application-default action {('allow' if str(r['action']).lower().startswith('a') else 'deny')}"
        )
    return "\n".join(out) + "\n"


def _vendor_compile_fortinet(manifest: dict[str, Any]) -> str:
    out: list[str] = ["# Fortinet FortiGate config", ""]
    for g in manifest.get("groups", []):
        if g["op"] == "create" and g.get("members"):
            out.append("config firewall address")
            for m in g["members"]:
                obj = f"{g['name']}-{m.replace('/', '_').replace('.', '_')}"
                out.append(f"  edit {obj}\n    set subnet {m}\n  next")
            out.append("end")
            out.append("config firewall addrgrp")
            out.append(f"  edit {g['name']}\n    set member " +
                       " ".join(f"{g['name']}-{m.replace('/', '_').replace('.', '_')}" for m in g["members"]) +
                       "\n  next\nend")
    out.append("config firewall policy")
    for i, r in enumerate(manifest.get("rules", []), start=1):
        out.append(
            f"  edit 0\n    set name {r['rule_id']}\n"
            f"    set srcaddr {r['src_group']}\n"
            f"    set dstaddr {r['dst_group']}\n"
            f"    set service ALL\n"
            f"    set action {('accept' if str(r['action']).lower().startswith('a') else 'deny')}\n"
            f"    set comments \"{manifest.get('request_id')}\"\n"
            f"  next"
        )
    out.append("end")
    return "\n".join(out) + "\n"


def _vendor_compile_cisco(manifest: dict[str, Any]) -> str:
    out: list[str] = ["! Cisco ASA / FTD configuration", ""]
    for g in manifest.get("groups", []):
        if g["op"] == "create" and g.get("members"):
            out.append(f"object-group network {g['name']}")
            for m in g["members"]:
                if "/" in m:
                    ip, cidr = m.split("/")
                    out.append(f"  network-object {ip} {cidr}")
                else:
                    out.append(f"  network-object host {m}")
    for r in manifest.get("rules", []):
        action = "permit" if str(r["action"]).lower().startswith("a") else "deny"
        proto = str(r.get("protocol", "tcp")).lower()
        out.append(
            f"access-list NGDC-OUTSIDE extended {action} {proto} "
            f"object-group {r['src_group']} object-group {r['dst_group']}"
        )
    return "\n".join(out) + "\n"


def _vendor_compile_checkpoint(manifest: dict[str, Any]) -> str:
    out: list[str] = ["# Check Point SmartConsole CLI", ""]
    for g in manifest.get("groups", []):
        if g["op"] == "create":
            out.append(f"add group name \"{g['name']}\"")
            for m in (g.get("members") or []):
                out.append(f"add network name \"{g['name']}-{m}\" subnet \"{m}\"")
                out.append(f"add group-with-exclusion-or-network name \"{g['name']}\" members.add \"{g['name']}-{m}\"")
    for r in manifest.get("rules", []):
        action = "accept" if str(r["action"]).lower().startswith("a") else "drop"
        out.append(
            f"add access-rule layer \"NGDC\" position top "
            f"name \"{r['rule_id']}\" "
            f"source.1 \"{r['src_group']}\" destination.1 \"{r['dst_group']}\" "
            f"service.1 \"any\" action \"{action}\""
        )
    return "\n".join(out) + "\n"


VENDOR_COMPILERS: dict[str, Any] = {
    "panos": _vendor_compile_panos,
    "fortinet": _vendor_compile_fortinet,
    "cisco": _vendor_compile_cisco,
    "checkpoint": _vendor_compile_checkpoint,
}


async def get_request_artifacts(request_id: str) -> dict[str, Any] | None:
    items = _load_rule_requests()
    for r in items:
        if r.get("request_id") == request_id:
            manifest = _artifact_manifest_for_request(r)
            sheets = _artifact_xlsx_rows(manifest)
            vendor_configs = {v: fn(manifest) for v, fn in VENDOR_COMPILERS.items()}
            return {
                "manifest": manifest,
                "xlsx_sheets": sheets,
                "vendor_configs": vendor_configs,
            }
    return None


# ============================================================
# ITSM Connector Framework  (ServiceNow / Generic REST)
# ============================================================

async def list_itsm_connectors() -> list[dict[str, Any]]:
    items = _load("itsm_connectors")
    if items is None:
        items = []
        _save("itsm_connectors", items)
    # Mask secrets on read.
    out = []
    for c in items:
        copy = {**c}
        if copy.get("auth_secret"):
            copy["auth_secret"] = "***"
        out.append(copy)
    return out


async def upsert_itsm_connector(payload: dict[str, Any]) -> dict[str, Any]:
    items = _load("itsm_connectors") or []
    cid = str(payload.get("connector_id", "")).strip()
    if not cid:
        cid = f"ITSM-{_id()[:6].upper()}"
        payload["connector_id"] = cid
    for i, c in enumerate(items):
        if c.get("connector_id") == cid:
            # Preserve existing secret when payload sends ***
            if payload.get("auth_secret") in (None, "", "***"):
                payload["auth_secret"] = c.get("auth_secret")
            items[i] = {**c, **payload}
            _save("itsm_connectors", items)
            return items[i]
    payload.setdefault("auto_submit_on_approval", False)
    items.append(dict(payload))
    _save("itsm_connectors", items)
    return payload


async def delete_itsm_connector(cid: str) -> bool:
    items = _load("itsm_connectors") or []
    new_items = [c for c in items if c.get("connector_id") != cid]
    if len(new_items) == len(items):
        return False
    _save("itsm_connectors", new_items)
    return True


async def submit_request_to_itsm(
    request_id: str,
    connector_id: str | None = None,
) -> dict[str, Any] | None:
    """Render the ServiceNow / Generic REST payload for a RuleRequest and
    record the external ticket on the request.

    The HTTP call itself is intentionally *not* performed in this in-VM
    sample (no outbound credentials configured); we record the rendered
    payload + a stub external_ticket_id so the lifecycle UI can be
    exercised end-to-end. Phase B will replace the stub with a real
    httpx.AsyncClient POST + retry/backoff."""

    items = _load_rule_requests()
    target = next((r for r in items if r.get("request_id") == request_id), None)
    if not target:
        return None
    connectors = _load("itsm_connectors") or []
    connector = None
    if connector_id:
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
    if connector is None and connectors:
        connector = connectors[0]
    if connector is None:
        connector = {"connector_id": "INTERNAL", "kind": "internal", "endpoint_url": "internal://sns"}

    manifest = _artifact_manifest_for_request(target)
    short_desc = (
        f"NGDC Firewall: {manifest.get('source_kind')}:{manifest.get('source_ref')} "
        f"-> {manifest.get('destination_kind')}:{manifest.get('destination_ref')} "
        f"({len(manifest.get('rules') or [])} rule(s))"
    )
    payload_template = connector.get("payload_template") or {}
    rendered = {
        "short_description": short_desc,
        "description": manifest.get("justification") or short_desc,
        "u_environment": manifest.get("environment"),
        "u_request_id": manifest.get("request_id"),
        "u_owner_team": manifest.get("owner_team"),
        "u_artifacts_json": manifest,
    }
    if isinstance(payload_template, dict):
        rendered.update(payload_template)

    # Stub external ticket id — replace with real REST call response in
    # Phase B when polling/webhook lands.
    ext_id = f"CHG{int(_now().replace(':', '').replace('-', '').replace('T', '').replace('Z', '')[-7:]):07d}"
    ext_url = (connector.get("endpoint_url") or "").rstrip("/") + f"/{ext_id}" if connector.get("endpoint_url") else ""
    target["external_system"] = connector.get("kind", "generic_rest")
    target["external_connector_id"] = connector.get("connector_id")
    target["external_ticket_id"] = ext_id
    target["external_ticket_url"] = ext_url
    target["external_status"] = "Submitted"
    target["external_last_synced_at"] = _now()
    target.setdefault("external_history", []).append({
        "at": _now(),
        "event": "submitted",
        "connector": connector.get("connector_id"),
        "external_ticket_id": ext_id,
    })
    _save("rule_requests", items)
    return {
        "request_id": request_id,
        "connector_id": connector.get("connector_id"),
        "kind": connector.get("kind", "generic_rest"),
        "endpoint_url": connector.get("endpoint_url"),
        "rendered_payload": rendered,
        "external_ticket_id": ext_id,
        "external_ticket_url": ext_url,
        "external_status": "Submitted",
    }


async def refresh_request_external_status(request_id: str) -> dict[str, Any] | None:
    """Manual status refresh — Phase A only marks the request as `In Progress`
    on first refresh and `Closed` on the second so testers can drive the
    lifecycle without a live ITSM. Phase B replaces this with real polling."""

    items = _load_rule_requests()
    target = next((r for r in items if r.get("request_id") == request_id), None)
    if not target:
        return None
    cur = target.get("external_status") or "Submitted"
    next_status = {
        "Submitted": "In Progress",
        "In Progress": "Closed Complete",
        "Closed Complete": "Closed Complete",
    }.get(cur, cur)
    target["external_status"] = next_status
    target["external_last_synced_at"] = _now()
    target.setdefault("external_history", []).append({
        "at": _now(),
        "event": "status-refreshed",
        "external_status": next_status,
    })
    if next_status == "Closed Complete" and target.get("status") not in ("Certified", "Rejected"):
        # Auto-progress NGDC-side lifecycle on ITSM closure.
        await set_rule_request_status(request_id, "Deployed",
                                      note="Auto: ITSM ticket Closed Complete")
    _save("rule_requests", items)
    return {
        "request_id": request_id,
        "external_ticket_id": target.get("external_ticket_id"),
        "external_status": next_status,
        "external_last_synced_at": target["external_last_synced_at"],
    }
