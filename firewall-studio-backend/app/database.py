"""JSON-file-backed database for the Network Firewall Studio.

All reference data (Neighbourhoods, Security Zones, Data Centers, Applications,
IP Ranges, Naming Standards, Policy Matrix) is fully customizable via CRUD APIs.

Data is stored in JSON files under the data/ directory and seeded on first startup.
"""

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
    SEED_LEGACY_RULES as _SD_LEGACY_RULES,
    SEED_IP_MAPPINGS as _SD_IP_MAPPINGS,
    SEED_FIREWALL_DEVICES as _SD_FW_DEVICES,
    SEED_FIREWALL_DEVICE_PATTERNS as _SD_FW_PATTERNS,
    SEED_DC_VENDOR_MAP as _SD_DC_VENDOR,
    SEED_APP_DC_MAPPINGS as _SD_APP_DC_MAPPINGS,
    SEED_REVIEWS as _SD_REVIEWS,
    build_seed_migrations as _sd_build_migrations,
    build_seed_chg_requests as _sd_build_chg_requests,
)

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
    return _data_mode


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


def _auto_prefix(value: str, entry_type: str = "ip") -> str:
    """Auto-prefix a value based on entry type for NGDC naming standards.
    - ip -> svr-
    - group -> grp- (normalizes legacy g- to grp-)
    - cidr/range/subnet -> rng-
    If already prefixed, returns as-is (except g- which is normalized to grp-).
    """
    v = value.strip()
    if not v:
        return v
    vl = v.lower()
    # Normalize legacy g- prefix to NGDC grp-
    if vl.startswith("g-") and not vl.startswith("grp-"):
        v = "grp-" + v[2:]
        return v
    # Already has a recognized prefix
    if vl.startswith(("svr-", "grp-", "rng-", "sub-")):
        return v
    # Add prefix based on type
    if entry_type in ("group",):
        return f"grp-{v}"
    if entry_type in ("cidr", "subnet", "range"):
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
SEED_LEGACY_RULES = _SD_LEGACY_RULES
SEED_IP_MAPPINGS = _SD_IP_MAPPINGS
SEED_MIGRATIONS = _sd_build_migrations()
SEED_MIGRATION_MAPPINGS: list[dict[str, Any]] = []
SEED_CHG_REQUESTS = _sd_build_chg_requests()
SEED_REVIEWS = _SD_REVIEWS


def _build_seed_rules() -> list[dict[str, Any]]:
    """Build NGDC firewall rules from seed data groups.

    Comprehensive test data covering ALL six Logical Data Flow scenarios:

    LDF-001: GEN/STD zones across NHs → 0 boundaries (no firewall)
    LDF-002: Same NH, same SZ → 0 boundaries (no firewall)
    LDF-003: Segmented zone → different zone, different NHs → 1 boundary (egress)
    LDF-004: Same segmented zone, different NHs → 2 boundaries (egress+ingress)
    LDF-005: Same NH, different segmented zones → 1 boundary
    LDF-006: PAA flow (internet → PAA → internal) → 2 boundaries
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

        # CRM internal (NH02, CDE)
        ("grp-CRM-NH02-CDE-WEB", "CDE", "NH02", "grp-CRM-NH02-CDE-APP", "CDE", "NH02",
         "TCP 443", "CRM Web to App (same NH/SZ)", "CRM", "Deployed", True, -30, "Production", "LDF-002"),
        ("grp-CRM-NH02-CDE-APP", "CDE", "NH02", "grp-CRM-NH02-CDE-DB", "CDE", "NH02",
         "TCP 1521", "CRM App to DB (same NH/SZ)", "CRM", "Deployed", True, -30, "Production", "LDF-002"),
        ("grp-CRM-NH02-CDE-BAT", "CDE", "NH02", "grp-CRM-NH02-CDE-DB", "CDE", "NH02",
         "TCP 1521", "CRM Batch to DB (same NH/SZ)", "CRM", "Certified", True, -20, "Production", "LDF-002"),
        ("grp-CRM-NH02-CDE-API", "CDE", "NH02", "grp-CRM-NH02-CDE-APP", "CDE", "NH02",
         "TCP 8443", "CRM API to App (same NH/SZ)", "CRM", "Deployed", True, -25, "Production", "LDF-002"),

        # TRD internal (NH06, CDE)
        ("grp-TRD-NH06-CDE-WEB", "CDE", "NH06", "grp-TRD-NH06-CDE-APP", "CDE", "NH06",
         "TCP 8443", "TRD Web to App (same NH/SZ)", "TRD", "Deployed", True, -120, "Production", "LDF-002"),
        ("grp-TRD-NH06-CDE-APP", "CDE", "NH06", "grp-TRD-NH06-CDE-DB", "CDE", "NH06",
         "TCP 1521", "TRD App to DB (same NH/SZ)", "TRD", "Deployed", True, -120, "Production", "LDF-002"),
        ("grp-TRD-NH06-CDE-APP", "CDE", "NH06", "grp-TRD-NH06-CDE-MQ", "CDE", "NH06",
         "TCP 9092", "TRD App to MQ (same NH/SZ)", "TRD", "Certified", True, -80, "Production", "LDF-002"),
        ("grp-TRD-NH06-CDE-API", "CDE", "NH06", "grp-TRD-NH06-CDE-APP", "CDE", "NH06",
         "TCP 8443", "TRD API to App (same NH/SZ)", "TRD", "Deployed", True, -100, "Production", "LDF-002"),

        # PAY internal (NH07, CPA)
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-PAY-NH07-CPA-DB", "CPA", "NH07",
         "TCP 1521", "PAY App to DB (same NH/SZ)", "PAY", "Deployed", True, -150, "Production", "LDF-002"),
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-PAY-NH07-CPA-MQ", "CPA", "NH07",
         "TCP 5672", "PAY App to MQ (same NH/SZ)", "PAY", "Certified", True, -100, "Production", "LDF-002"),
        ("grp-PAY-NH07-CPA-API", "CPA", "NH07", "grp-PAY-NH07-CPA-APP", "CPA", "NH07",
         "TCP 8443", "PAY API to App (same NH/SZ)", "PAY", "Deployed", True, -140, "Production", "LDF-002"),

        # FRD internal (NH02, CDE)
        ("grp-FRD-NH02-CDE-APP", "CDE", "NH02", "grp-FRD-NH02-CDE-DB", "CDE", "NH02",
         "TCP 1521", "FRD Engine to DB (same NH/SZ)", "FRD", "Deployed", True, -100, "Production", "LDF-002"),
        ("grp-FRD-NH02-CDE-APP", "CDE", "NH02", "grp-FRD-NH02-CDE-MQ", "CDE", "NH02",
         "TCP 9092", "FRD App to Kafka (same NH/SZ)", "FRD", "Deployed", True, -90, "Production", "LDF-002"),
        ("grp-FRD-NH02-CDE-API", "CDE", "NH02", "grp-FRD-NH02-CDE-APP", "CDE", "NH02",
         "TCP 8443", "FRD API to Engine (same NH/SZ)", "FRD", "Certified", True, -50, "Production", "LDF-002"),

        # CBK internal (NH08, CCS)
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-CBK-NH08-CCS-DB", "CCS", "NH08",
         "TCP 1521", "CBK App to DB (same NH/SZ)", "CBK", "Deployed", True, -200, "Production", "LDF-002"),
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-CBK-NH08-CCS-MQ", "CCS", "NH08",
         "TCP 5672", "CBK App to MQ (same NH/SZ)", "CBK", "Deployed", True, -180, "Production", "LDF-002"),
        ("grp-CBK-NH08-CCS-API", "CCS", "NH08", "grp-CBK-NH08-CCS-APP", "CCS", "NH08",
         "TCP 8443", "CBK API to App (same NH/SZ)", "CBK", "Certified", True, -150, "Production", "LDF-002"),
        ("grp-CBK-NH08-CCS-BAT", "CCS", "NH08", "grp-CBK-NH08-CCS-DB", "CCS", "NH08",
         "TCP 1521", "CBK Batch to DB (same NH/SZ)", "CBK", "Deployed", True, -160, "Production", "LDF-002"),

        # LND internal (NH09, CCS)
        ("grp-LND-NH09-CCS-WEB", "CCS", "NH09", "grp-LND-NH09-CCS-APP", "CCS", "NH09",
         "TCP 8443", "LND Web to App (same NH/SZ)", "LND", "Deployed", True, -110, "Production", "LDF-002"),
        ("grp-LND-NH09-CCS-APP", "CCS", "NH09", "grp-LND-NH09-CCS-DB", "CCS", "NH09",
         "TCP 1521", "LND App to DB (same NH/SZ)", "LND", "Deployed", True, -110, "Production", "LDF-002"),
        ("grp-LND-NH09-CCS-BAT", "CCS", "NH09", "grp-LND-NH09-CCS-DB", "CCS", "NH09",
         "TCP 1521", "LND Batch to DB (same NH/SZ)", "LND", "Certified", True, -80, "Production", "LDF-002"),

        # WLT internal (NH10, CDE)
        ("grp-WLT-NH10-CDE-WEB", "CDE", "NH10", "grp-WLT-NH10-CDE-APP", "CDE", "NH10",
         "TCP 8443", "WLT Web to App (same NH/SZ)", "WLT", "Deployed", True, -130, "Production", "LDF-002"),
        ("grp-WLT-NH10-CDE-APP", "CDE", "NH10", "grp-WLT-NH10-CDE-DB", "CDE", "NH10",
         "TCP 1521", "WLT App to DB (same NH/SZ)", "WLT", "Deployed", True, -130, "Production", "LDF-002"),
        ("grp-WLT-NH10-CDE-API", "CDE", "NH10", "grp-WLT-NH10-CDE-APP", "CDE", "NH10",
         "TCP 8443", "WLT API to App (same NH/SZ)", "WLT", "Certified", True, -60, "Production", "LDF-002"),

        # MBK internal (NH07, CPA)
        ("grp-MBK-NH07-CPA-WEB", "CPA", "NH07", "grp-MBK-NH07-CPA-APP", "CPA", "NH07",
         "TCP 443", "MBK Web to App (same NH/SZ)", "MBK", "Deployed", True, -40, "Production", "LDF-002"),
        ("grp-MBK-NH07-CPA-APP", "CPA", "NH07", "grp-MBK-NH07-CPA-DB", "CPA", "NH07",
         "TCP 1521", "MBK App to DB (same NH/SZ)", "MBK", "Deployed", True, -40, "Production", "LDF-002"),

        # ================================================================
        # LDF-001: GEN/STD zones across NHs — 0 boundaries (no firewall)
        # ================================================================

        # HRM (NH01/GEN) -> INS (NH04/GEN)
        ("grp-HRM-NH01-GEN-WEB", "GEN", "NH01", "grp-HRM-NH01-GEN-APP", "GEN", "NH01",
         "TCP 8443", "HRM Web to App", "HRM", "Deployed", True, -90, "Production", "LDF-002"),
        ("grp-HRM-NH01-GEN-APP", "GEN", "NH01", "grp-HRM-NH01-GEN-DB", "GEN", "NH01",
         "TCP 5432", "HRM App to DB", "HRM", "Deployed", True, -90, "Production", "LDF-002"),
        ("grp-HRM-NH01-GEN-BAT", "GEN", "NH01", "grp-HRM-NH01-GEN-DB", "GEN", "NH01",
         "TCP 5432", "HRM Batch to DB", "HRM", "Certified", True, -60, "Production", "LDF-002"),
        ("grp-HRM-NH01-GEN-APP", "GEN", "NH01", "grp-INS-NH04-GEN-API", "GEN", "NH04",
         "TCP 8443", "HRM to INS API (GEN→GEN cross-NH, no FW)", "HRM", "Deployed", True, -85, "Production", "LDF-001"),
        ("grp-INS-NH04-GEN-APP", "GEN", "NH04", "grp-KYC-NH05-GEN-API", "GEN", "NH05",
         "TCP 8443", "INS to KYC API (GEN→GEN cross-NH, no FW)", "INS", "Certified", True, -75, "Production", "LDF-001"),
        ("grp-KYC-NH05-GEN-APP", "GEN", "NH05", "grp-HRM-NH01-GEN-APP", "GEN", "NH01",
         "TCP 8443", "KYC to HRM callback (GEN→GEN cross-NH, no FW)", "KYC", "Deployed", True, -65, "Production", "LDF-001"),

        # INS internal (NH04, GEN)
        ("grp-INS-NH04-GEN-WEB", "GEN", "NH04", "grp-INS-NH04-GEN-APP", "GEN", "NH04",
         "TCP 8443", "INS Web to App", "INS", "Deployed", True, -85, "Production", "LDF-002"),
        ("grp-INS-NH04-GEN-APP", "GEN", "NH04", "grp-INS-NH04-GEN-DB", "GEN", "NH04",
         "TCP 5432", "INS App to DB", "INS", "Deployed", True, -85, "Production", "LDF-002"),

        # KYC internal (NH05, GEN)
        ("grp-KYC-NH05-GEN-WEB", "GEN", "NH05", "grp-KYC-NH05-GEN-APP", "GEN", "NH05",
         "TCP 8443", "KYC Web to App", "KYC", "Deployed", True, -95, "Production", "LDF-002"),
        ("grp-KYC-NH05-GEN-APP", "GEN", "NH05", "grp-KYC-NH05-GEN-DB", "GEN", "NH05",
         "TCP 5432", "KYC App to DB", "KYC", "Deployed", True, -95, "Production", "LDF-002"),
        ("grp-KYC-NH05-GEN-API", "GEN", "NH05", "grp-KYC-NH05-GEN-APP", "GEN", "NH05",
         "TCP 8443", "KYC API to App", "KYC", "Certified", True, -70, "Production", "LDF-002"),

        # ================================================================
        # LDF-003: Segmented → different zone, different NHs — 1 boundary (egress)
        # Egress through source NH's SZ firewall only
        # ================================================================

        # PAY(NH07/CPA) → FRD(NH02/CDE): 1 boundary, egress via fw-PA-NH07-CPA
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-FRD-NH02-CDE-API", "CDE", "NH02",
         "TCP 8443", "PAY to Fraud Check (CPA→CDE, 1 FW egress)", "PAY", "Pending Review", False, -10, "Production", "LDF-003"),

        # CBK(NH08/CCS) → PAY(NH07/CPA): 1 boundary, egress via fw-PA-NH08-CCS
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-PAY-NH07-CPA-API", "CPA", "NH07",
         "TCP 8443", "CBK to Payment (CCS→CPA, 1 FW egress)", "CBK", "Pending Review", False, -5, "Production", "LDF-003"),

        # LND(NH09/CCS) → KYC(NH05/GEN): 1 boundary, egress via fw-PA-NH09-CCS
        ("grp-LND-NH09-CCS-APP", "CCS", "NH09", "grp-KYC-NH05-GEN-API", "GEN", "NH05",
         "TCP 8443", "LND to KYC Check (CCS→GEN, 1 FW egress)", "LND", "Certified", True, -35, "Production", "LDF-003"),

        # FRD(NH02/CDE) → HRM(NH01/GEN): 1 boundary, egress via fw-PA-NH02-CDE
        ("grp-FRD-NH02-CDE-APP", "CDE", "NH02", "grp-HRM-NH01-GEN-APP", "GEN", "NH01",
         "TCP 8443", "FRD to HRM lookup (CDE→GEN, 1 FW egress)", "FRD", "Certified", True, -45, "Production", "LDF-003"),

        # TRD(NH06/CDE) → INS(NH04/GEN): 1 boundary, egress via fw-PA-NH06-CDE
        ("grp-TRD-NH06-CDE-APP", "CDE", "NH06", "grp-INS-NH04-GEN-APP", "GEN", "NH04",
         "TCP 8443", "TRD to INS policy (CDE→GEN, 1 FW egress)", "TRD", "Pending Review", False, -8, "Production", "LDF-003"),

        # MBK(NH07/CPA) → CBK(NH08/CCS): 1 boundary, egress via fw-PA-NH07-CPA
        ("grp-MBK-NH07-CPA-APP", "CPA", "NH07", "grp-CBK-NH08-CCS-API", "CCS", "NH08",
         "TCP 8443", "MBK to Core Banking (CPA→CCS, 1 FW egress)", "MBK", "Certified", True, -30, "Production", "LDF-003"),

        # ================================================================
        # LDF-004: Same segmented zone, different NHs — 2 boundaries (egress+ingress)
        # Egress via source NH's SZ firewall + Ingress via dest NH's SZ firewall
        # ================================================================

        # CRM(NH02/CDE) → WLT(NH10/CDE): 2 boundaries (NH02-CDE egress, NH10-CDE ingress)
        ("grp-CRM-NH02-CDE-APP", "CDE", "NH02", "grp-WLT-NH10-CDE-API", "CDE", "NH10",
         "TCP 8443", "CRM to WLT portfolio (CDE→CDE cross-NH, 2 FW)", "CRM", "Certified", True, -25, "Production", "LDF-004"),

        # WLT(NH10/CDE) → TRD(NH06/CDE): 2 boundaries (NH10-CDE egress, NH06-CDE ingress)
        ("grp-WLT-NH10-CDE-APP", "CDE", "NH10", "grp-TRD-NH06-CDE-API", "CDE", "NH06",
         "TCP 8443", "WLT to Trading (CDE→CDE cross-NH, 2 FW)", "WLT", "Certified", True, -45, "Production", "LDF-004"),

        # FRD(NH02/CDE) → TRD(NH06/CDE): 2 boundaries (NH02-CDE egress, NH06-CDE ingress)
        ("grp-FRD-NH02-CDE-API", "CDE", "NH02", "grp-TRD-NH06-CDE-APP", "CDE", "NH06",
         "TCP 8443", "FRD alert to TRD (CDE→CDE cross-NH, 2 FW)", "FRD", "Pending Review", False, -7, "Production", "LDF-004"),

        # CRM(NH02/CDE) → FRD(NH02/CDE): same NH — should be LDF-002, 0 boundaries
        ("grp-CRM-NH02-CDE-APP", "CDE", "NH02", "grp-FRD-NH02-CDE-API", "CDE", "NH02",
         "TCP 8443", "CRM to Fraud (same NH02/CDE, 0 FW)", "CRM", "Certified", True, -40, "Production", "LDF-002"),

        # CBK(NH08/CCS) → LND(NH09/CCS): 2 boundaries (NH08-CCS egress, NH09-CCS ingress)
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-LND-NH09-CCS-APP", "CCS", "NH09",
         "TCP 8443", "CBK to LND transfer (CCS→CCS cross-NH, 2 FW)", "CBK", "Pending Review", False, -3, "Production", "LDF-004"),

        # PAY(NH07/CPA) → MBK(NH07/CPA): same NH — should be LDF-002, 0 boundaries
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-MBK-NH07-CPA-API", "CPA", "NH07",
         "TCP 8443", "PAY to Mobile Banking (same NH07/CPA, 0 FW)", "PAY", "Deployed", True, -20, "Production", "LDF-002"),

        # ================================================================
        # LDF-005: Same NH, different segmented zones — 1 boundary
        # ================================================================

        # CRM(NH02/CDE) → within NH02 but to CPA zone (hypothetical cross-zone)
        # Need a CPA group in NH02 — use PAA or create a scenario
        # PAY data feed to FRD within NH07: CPA → CDE cross-zone within NH07
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-MBK-NH07-CPA-DB", "CPA", "NH07",
         "TCP 1521", "PAY to MBK DB within NH07 (same NH/SZ, 0 FW)", "PAY", "Deployed", True, -15, "Production", "LDF-002"),

        # ================================================================
        # LDF-006: PAA flow — 2 boundaries (PAA perimeter + internal NH firewall)
        # ================================================================

        # EPT(NH01/PAA) → CRM(NH02/CDE): PAA perimeter + NH02 CDE firewall
        ("grp-EPT-NH01-PAA-WEB", "PAA", "NH01", "grp-CRM-NH02-CDE-API", "CDE", "NH02",
         "TCP 443", "EPT Portal to CRM API (PAA→CDE, 2 FW)", "EPT", "Pending Review", False, -4, "Production", "LDF-006"),

        # EPT(NH01/PAA) → CBK(NH08/CCS): PAA perimeter + NH08 CCS firewall
        ("grp-EPT-NH01-PAA-APP", "PAA", "NH01", "grp-CBK-NH08-CCS-API", "CCS", "NH08",
         "TCP 8443", "EPT to Core Banking (PAA→CCS, 2 FW)", "EPT", "Pending Review", False, -3, "Production", "LDF-006"),

        # EPT(NH01/PAA) → PAY(NH07/CPA): PAA perimeter + NH07 CPA firewall
        ("grp-EPT-NH01-PAA-API", "PAA", "NH01", "grp-PAY-NH07-CPA-API", "CPA", "NH07",
         "TCP 8443", "EPT to Payment (PAA→CPA, 2 FW)", "EPT", "Pending Review", False, -2, "Production", "LDF-006"),

        # EPT(NH01/PAA) internal (same NH/SZ)
        ("grp-EPT-NH01-PAA-WEB", "PAA", "NH01", "grp-EPT-NH01-PAA-APP", "PAA", "NH01",
         "TCP 443", "EPT Web to App (same NH/SZ)", "EPT", "Deployed", True, -10, "Production", "LDF-002"),
        ("grp-EPT-NH01-PAA-APP", "PAA", "NH01", "grp-EPT-NH01-PAA-API", "PAA", "NH01",
         "TCP 8443", "EPT App to API (same NH/SZ)", "EPT", "Deployed", True, -10, "Production", "LDF-002"),

        # ================================================================
        # Non-Production environment rules (replicating key scenarios)
        # ================================================================

        # CRM Non-Prod (NH02, CDE)
        ("grp-CRM-NH02-CDE-WEB", "CDE", "NH02", "grp-CRM-NH02-CDE-APP", "CDE", "NH02",
         "TCP 443", "CRM Web to App (Non-Prod)", "CRM", "Deployed", True, -60, "Non-Production", "LDF-002"),
        ("grp-CRM-NH02-CDE-APP", "CDE", "NH02", "grp-CRM-NH02-CDE-DB", "CDE", "NH02",
         "TCP 1521", "CRM App to DB (Non-Prod)", "CRM", "Deployed", True, -60, "Non-Production", "LDF-002"),

        # TRD Non-Prod (NH06, CDE)
        ("grp-TRD-NH06-CDE-WEB", "CDE", "NH06", "grp-TRD-NH06-CDE-APP", "CDE", "NH06",
         "TCP 8443", "TRD Web to App (Non-Prod)", "TRD", "Deployed", True, -90, "Non-Production", "LDF-002"),
        ("grp-TRD-NH06-CDE-APP", "CDE", "NH06", "grp-TRD-NH06-CDE-DB", "CDE", "NH06",
         "TCP 1521", "TRD App to DB (Non-Prod)", "TRD", "Certified", True, -90, "Non-Production", "LDF-002"),

        # PAY Pre-Prod (NH07, CPA) — cross-SZ test in pre-prod
        ("grp-PAY-NH07-CPA-APP", "CPA", "NH07", "grp-FRD-NH02-CDE-API", "CDE", "NH02",
         "TCP 8443", "PAY to FRD Check (Pre-Prod, CPA→CDE, 1 FW)", "PAY", "Certified", True, -50, "Pre-Production", "LDF-003"),

        # CBK Non-Prod (NH08, CCS)
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-CBK-NH08-CCS-DB", "CCS", "NH08",
         "TCP 1521", "CBK App to DB (Non-Prod)", "CBK", "Deployed", True, -120, "Non-Production", "LDF-002"),
        ("grp-CBK-NH08-CCS-APP", "CCS", "NH08", "grp-LND-NH09-CCS-APP", "CCS", "NH09",
         "TCP 8443", "CBK to LND (Non-Prod, CCS→CCS, 2 FW)", "CBK", "Pending Review", False, -14, "Non-Production", "LDF-004"),

        # HRM UAT (NH01, GEN) — GEN cross-NH
        ("grp-HRM-NH01-GEN-APP", "GEN", "NH01", "grp-KYC-NH05-GEN-API", "GEN", "NH05",
         "TCP 8443", "HRM to KYC (UAT, GEN→GEN, no FW)", "HRM", "Certified", True, -40, "UAT", "LDF-001"),

        # INS SIT (NH04, GEN)
        ("grp-INS-NH04-GEN-WEB", "GEN", "NH04", "grp-INS-NH04-GEN-APP", "GEN", "NH04",
         "TCP 8443", "INS Web to App (SIT)", "INS", "Deployed", True, -55, "SIT", "LDF-002"),

        # WLT DR (NH10, CDE) — cross-NH CDE in DR
        ("grp-WLT-NH10-CDE-APP", "CDE", "NH10", "grp-CRM-NH02-CDE-API", "CDE", "NH02",
         "TCP 8443", "WLT to CRM (DR, CDE→CDE, 2 FW)", "WLT", "Pending Review", False, -5, "DR", "LDF-004"),

        # EPT Non-Prod PAA flow
        ("grp-EPT-NH01-PAA-WEB", "PAA", "NH01", "grp-FRD-NH02-CDE-API", "CDE", "NH02",
         "TCP 443", "EPT to FRD (Non-Prod, PAA→CDE, 2 FW)", "EPT", "Certified", True, -20, "Non-Production", "LDF-006"),
    ]

    for src, sz_s, src_nh, dst, sz_d, dst_nh, port, desc, app, st, g2g, days, env, ldf in app_rules:
        seq += 1
        ct = (base + timedelta(days=days)).isoformat()
        rules.append({
            "rule_id": f"R-{seq}", "source": src, "source_zone": sz_s, "source_nh": src_nh,
            "destination": dst, "destination_zone": sz_d, "destination_nh": dst_nh,
            "port": port, "protocol": port.split(" ")[0],
            "action": "Allow", "description": desc, "application": app, "status": st,
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
    _save("legacy_rules", deepcopy(SEED_LEGACY_RULES))
    _save("ip_mappings", deepcopy(SEED_IP_MAPPINGS))
    _save("firewall_devices", deepcopy(_SD_FW_DEVICES))
    _save("app_dc_mappings", deepcopy(_SD_APP_DC_MAPPINGS))
    _save("reviews", deepcopy(SEED_REVIEWS))
    _save("rule_modifications", [])


# ============================================================
# Read Operations (Reference Data)
# ============================================================

async def get_neighbourhoods() -> list[dict[str, Any]]:
    return _load("neighbourhoods") or []


async def get_security_zones() -> list[dict[str, Any]]:
    return _load("security_zones") or []


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


async def update_legacy_rule(rule_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    rules = _load("legacy_rules") or []
    for r in rules:
        if r["id"] == rule_id:
            r.update(data)
            _save("legacy_rules", rules)
            return r
    return None


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
    skip = {"id", "is_standard", "migration_status", "imported_at", "environment"}
    parts: list[str] = []
    for k in sorted(rule.keys()):
        if k in skip:
            continue
        parts.append(f"{k}={rule[k]}")
    return "|".join(parts)


async def import_legacy_rules(new_rules: list[dict[str, Any]]) -> dict[str, int]:
    """Import legacy rules from Excel, dedup against existing rules using ALL columns.
    Optimised for large imports (50K+ rows). Delta-based — only new/changed rows are added.
    NGDC auto-promotion is deferred — use the dedicated auto-import endpoint instead."""
    existing = _load("legacy_rules") or []
    existing_keys: set[str] = set()
    for r in existing:
        existing_keys.add(_rule_fingerprint(r))

    max_num = 0
    for r in existing:
        try:
            num = int(r["id"].split("-")[1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            pass

    added = 0
    duplicates = 0
    for rule in new_rules:
        fp = _rule_fingerprint(rule)
        if fp in existing_keys:
            duplicates += 1
            continue
        max_num += 1
        rule["id"] = f"LR-{max_num:05d}"
        rule.setdefault("is_standard", False)
        rule.setdefault("migration_status", "Not Started")
        existing.append(rule)
        existing_keys.add(fp)
        added += 1

    _save("legacy_rules", existing)
    return {"added": added, "duplicates": duplicates, "total": len(existing)}


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
            r["migrated_at"] = _now()
            _save("legacy_rules", rules)
            await log_migration(rule_id, "migrate_to_ngdc", old_status, "Completed",
                                f"Rule {rule_id} migrated to NGDC standards")
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
        "is_group_to_group": rule_data.get("is_group_to_group", True),
        "environment": rule_data.get("environment", "Production"),
        "datacenter": rule_data.get("datacenter", "ALPHA_NGDC"),
        "created_at": now,
        "updated_at": now,
        "certified_date": None,
        "expiry_date": None,
    }
    rules.append(rule)
    _save("firewall_rules", rules)
    history = _load("rule_history") or []
    history.append({
        "rule_id": rule_id, "action": "Created", "timestamp": now,
        "details": f"Rule created: {rule['description']}", "user": "system",
    })
    _save("rule_history", history)
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
            return r
    return None


async def update_rule_status(rule_id: str, new_status: str) -> dict[str, Any] | None:
    rules = _load("firewall_rules") or []
    now = _now()
    for r in rules:
        if r.get("rule_id") == rule_id:
            r["status"] = new_status
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
    items.append(dict(data))
    _save("security_zones", items)
    return data


async def update_security_zone(code: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("security_zones") or []
    for item in items:
        if item.get("code") == code:
            item.update(updates)
            _save("security_zones", items)
            return item
    return None


async def delete_security_zone(code: str) -> bool:
    items = _load("security_zones") or []
    new_items = [i for i in items if i.get("code") != code]
    if len(new_items) == len(items):
        return False
    _save("security_zones", new_items)
    return True


async def create_application(data: dict[str, Any]) -> dict[str, Any]:
    items = _load("applications") or []
    items.append(dict(data))
    _save("applications", items)
    return data


async def update_application(app_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = _load("applications") or []
    for item in items:
        if item.get("app_id") == app_id:
            item.update(updates)
            _save("applications", items)
            return item
    return None


async def delete_application(app_id: str) -> bool:
    items = _load("applications") or []
    new_items = [i for i in items if i.get("app_id") != app_id]
    if len(new_items) == len(items):
        return False
    _save("applications", new_items)
    return True


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


async def create_group(data: dict[str, Any]) -> dict[str, Any]:
    groups = _load("groups") or []
    # Auto-prefix group name if missing
    if "name" in data:
        data["name"] = _auto_prefix(data["name"], "group")
    # Auto-prefix member values
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
            f"set rulebase security rules \"{rule_id}\" description \"{desc}\""
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
            f"  comments \"{desc}\""
        )
    elif vendor == "cisco_asa":
        compiled = (
            f"access-list ACL_{'IN' if action == 'Allow' else 'OUT'} extended "
            f"{'permit' if action == 'Allow' else 'deny'} "
            f"{proto.lower()} object-group {src} object-group {dst} eq {port}\n"
            f"! {desc}"
        )
    else:
        compiled = (
            f"# Firewall Rule: {rule_id}\n"
            f"# Description: {desc}\n"
            f"# Application: {rule.get('application', 'N/A')}\n"
            f"# Environment: {rule.get('environment', 'N/A')}\n"
            f"---\n"
            f"rule:\n"
            f"  id: {rule_id}\n"
            f"  action: {action.lower()}\n"
            f"  source:\n"
            f"    objects: [{src}]\n"
            f"    zone: {rule.get('source_zone', 'any')}\n"
            f"  destination:\n"
            f"    objects: [{dst}]\n"
            f"    zone: {rule.get('destination_zone', 'any')}\n"
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


async def create_review(rule_id: str, comments: str = "") -> dict[str, Any]:
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
        await update_rule_status(rule_id, "Pending Review")
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
            rule_id = r.get("rule_id")
            if rule_id:
                await update_rule_status(rule_id, "Approved")
                # Also update in separate studio_rules.json
                rule = await get_rule(rule_id)
                if rule:
                    await add_studio_rule(rule)
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
            rule_id = r.get("rule_id")
            if rule_id:
                await update_rule_status(rule_id, "Rejected")
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

    return modification


async def get_rule_modifications(rule_id: str | None = None) -> list[dict[str, Any]]:
    mods = _load("rule_modifications") or []
    if rule_id:
        mods = [m for m in mods if m.get("rule_id") == rule_id]
    return mods


async def approve_rule_modification(mod_id: str, notes: str = "") -> dict[str, Any] | None:
    """Approve a modification and apply changes to the rule."""
    mods = _load("rule_modifications") or []
    now = _now()
    for m in mods:
        if m.get("id") == mod_id:
            m["status"] = "Approved"
            m["reviewed_at"] = now
            m["reviewer"] = "sns_user"
            m["review_notes"] = notes
            _save("rule_modifications", mods)
            # Apply modification to rule
            rule_id = m.get("rule_id")
            if rule_id:
                modified = m.get("modified", {})
                await update_legacy_rule(rule_id, modified)
            return m
    return None


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

    src_objs = [s.strip() for s in src.split("\n") if s.strip()] or ["any"]
    dst_objs = [d.strip() for d in dst.split("\n") if d.strip()] or ["any"]
    svc_list = [s.strip() for s in svc.split("\n") if s.strip()] or ["any"]

    if vendor == "palo_alto":
        compiled = (
            f"# Palo Alto - {app_name} - {rule_id}\n"
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
    elif vendor == "cisco_asa":
        compiled = (
            f"! Cisco ASA - {app_name} - {rule_id}\n"
            + "\n".join(
                f"access-list ACL_{'IN' if action == 'Accept' else 'OUT'} extended "
                f"{'permit' if action == 'Accept' else 'deny'} "
                f"tcp object-group {s} object-group {d} eq {sv}"
                for s in src_objs for d in dst_objs for sv in svc_list
            )
        )
    else:
        compiled = (
            f"# Firewall Rule: {rule_id}\n"
            f"# Application: {app_name}\n"
            f"# Policy: {policy}\n"
            f"---\n"
            f"rule:\n"
            f"  id: {rule_id}\n"
            f"  action: {action.lower()}\n"
            f"  source:\n"
            f"    objects: [{', '.join(src_objs)}]\n"
            f"    zone: {src_zone}\n"
            f"  destination:\n"
            f"    objects: [{', '.join(dst_objs)}]\n"
            f"    zone: {dst_zone}\n"
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
    app_dist = rule.get("app_distributed_id", "")
    app_name = rule.get("app_name", "")
    rule_env = rule.get("environment", "Production")
    app_info = next((a for a in apps if str(a.get("app_id")) == app_id or a.get("app_distributed_id") == app_dist), None)

    # --- Step 1: Determine NH/SZ using the rule's actual source/dest zones ---
    # The rule itself tells us source_zone and destination_zone — use these to
    # find the correct NH for each direction from app-DC mappings.
    rule_src_zone = (rule.get("rule_source_zone") or "").strip()
    rule_dst_zone = (rule.get("rule_destination_zone") or "").strip()

    # Get ALL app-DC mappings for this app (component-level)
    all_app_comps = [m for m in app_dc_mappings
                     if str(m.get("app_id", "")).upper() == app_id.upper()]

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
        """Look up NGDC equivalent IP from the 1-to-1 ip_mappings table."""
        clean = legacy_ip_raw.strip()
        for pfx in ("svr-", "rng-", "grp-"):
            if clean.startswith(pfx):
                clean = clean[len(pfx):]
                break
        for m in _ip_mappings_early:
            legacy_val = str(m.get("legacy_ip", ""))
            if legacy_val == clean or legacy_val == legacy_ip_raw:
                ngdc_ip = str(m.get("ngdc_ip", ""))
                return f"svr-{ngdc_ip}" if ngdc_ip else None
        return None

    def _suggest_ngdc_name(legacy_name: str, entry_type: str, direction: str = "source") -> str:
        prefix = "grp" if legacy_name.startswith("grp") or legacy_name.startswith("gapigr") else \
                 "svr" if legacy_name.startswith("svr") else \
                 "rng" if legacy_name.startswith("rng") else "grp"
        short_app = app_id.upper()
        # For individual IPs (svr-*), try 1-to-1 IP mapping first
        if prefix == "svr":
            mapped = _lookup_ip_mapping(legacy_name)
            if mapped:
                return mapped
        # Use direction-specific NH/SZ from the rule's actual zones
        if direction == "destination":
            nh, sz = dst_nh, dst_sz
        else:
            nh, sz = src_nh, src_sz
        return f"{prefix}-{short_app}-{entry_type}-{nh}-{sz}"

    def _build_mapping(legacy_name: str, entry_type: str, idx: int, direction: str = "source") -> dict[str, Any]:
        obj_type = "group" if legacy_name.startswith("grp") or legacy_name.startswith("gapigr") else \
                   "server" if legacy_name.startswith("svr") else \
                   "range" if legacy_name.startswith("rng") else "other"
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
    app_components = [m for m in app_dc_mappings if str(m.get("app_id", "")).upper() == app_id.upper()]
    short_app = app_id.upper()

    # Load IP mappings table for 1-to-1 legacy -> NGDC IP lookups
    ip_mappings_table = _load("ip_mappings") or []

    def _detect_component(ip_str: str) -> str:
        """Detect component type from IP by matching against app_dc_mappings CIDRs,
        ip_mappings table (NGDC IP -> component), legacy group names, and port heuristics."""
        import ipaddress
        ip_clean = ip_str.strip().split("\n")[0].strip()

        # Strip svr-/rng-/grp- prefix for raw IP matching
        ip_raw = ip_clean
        for pfx in ("svr-", "rng-", "grp-"):
            if ip_raw.startswith(pfx):
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
        # Strip svr- / rng- / grp- prefixes for matching
        clean = legacy_ip_raw.strip()
        for pfx in ("svr-", "rng-", "grp-"):
            if clean.startswith(pfx):
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

        # Build NGDC IPs by looking up 1-to-1 IP mapping table
        ngdc_ips: list[str] = []
        for ip in ips:
            mapped = _lookup_ngdc_ip(ip)
            if mapped:
                ngdc_ips.append(mapped)
            else:
                # Fallback: use svr- prefix with the legacy IP (stripped of old prefix)
                clean_ip = ip.strip()
                for pfx in ("svr-", "rng-", "grp-"):
                    if clean_ip.startswith(pfx):
                        clean_ip = clean_ip[len(pfx):]
                        break
                ngdc_ips.append(f"svr-{clean_ip}")

        ngdc_group_name = f"grp-{short_app}-{comp}-{comp_nh}-{comp_sz}"
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
        "naming_standard": f"grp-{short_app}-{{COMPONENT}}-{{NH}}-{{SZ}}",
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
    mappings.append(mapping)
    _save("app_dc_mappings", mappings)
    return mapping


async def update_app_dc_mapping(mapping_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    mappings = _load("app_dc_mappings") or []
    for m in mappings:
        if m.get("id") == mapping_id:
            m.update(data)
            m["updated_at"] = _now()
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
        """Check if entry is a group (grp-, g-, gapigr- prefix) vs individual IP/subnet/range."""
        lower = name.lower()
        return lower.startswith("grp-") or lower.startswith("g-") or lower.startswith("gapigr-")

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
            lines.append(f"# {suffix} Rule — Device: {dev_name} ({dev_id})")
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
        elif vendor == "cisco_asa":
            objs = src_objs if direction == "egress" else dst_objs
            lines.append(f"! {suffix} Rule — Device: {dev_name} ({dev_id})")
            for obj in objs:
                if direction == "egress":
                    lines.append(f"access-list ACL_{suffix} extended permit "
                                 f"{proto.lower()} object-group {obj} any eq {svc}")
                else:
                    lines.append(f"access-list ACL_{suffix} extended permit "
                                 f"{proto.lower()} any object-group {obj} eq {svc}")
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
