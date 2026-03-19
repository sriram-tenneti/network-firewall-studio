"""Seed data for the Network Firewall Studio.

This module contains ALL seed / demo data used to initialize the JSON database
on first startup.  When real data arrives (e.g. from MongoDB or an Excel
import), this file can be safely deleted or emptied.

The module re-exports reference data from config.py, standards.py, and
mappings.py so that database.py has a single import source for seed data.

Architecture:
  config.py     -> Org config, naming standards, environments, predefined dests
  standards.py  -> Policy matrices (Heritage DC, NGDC Prod, Non-Prod, Pre-Prod)
  mappings.py   -> Per-app per-environment DC/NH/SZ assignments, component-to-SZ
  seed_data.py  -> This file: transient demo data (rules, groups, migrations, etc.)
  database.py   -> JSON persistence + CRUD operations (imports from above)
"""

from datetime import datetime, timedelta
from typing import Any

# ── Re-export from config.py ──────────────────────────────────────────
from app.config import (
    ORG_CONFIG as SEED_ORG_CONFIG,
    NAMING_STANDARDS as SEED_NAMING_STANDARDS,
    ENVIRONMENTS as SEED_ENVIRONMENTS,
    PREDEFINED_DESTINATIONS as SEED_PREDEFINED_DESTINATIONS,
)

# ── Re-export from standards.py ───────────────────────────────────────
from app.standards import (
    HERITAGE_DC_MATRIX as SEED_HERITAGE_DC_MATRIX,
    NGDC_PROD_MATRIX as SEED_NGDC_PROD_MATRIX,
    NONPROD_PREPROD_MATRIX as SEED_NONPROD_MATRIX,
    POLICY_MATRIX as SEED_POLICY_MATRIX,
)

# ── Re-export from mappings.py ────────────────────────────────────────
from app.mappings import (
    APP_ENVIRONMENT_ASSIGNMENTS as SEED_APP_ENVIRONMENT_ASSIGNMENTS,
    COMPONENT_TO_SZ as SEED_COMPONENT_TO_SZ,
)


def _now() -> str:
    return datetime.utcnow().isoformat()


# ============================================================
# Transient Seed Data  (can be wiped when real data arrives)
# ============================================================

# The following seed constants are defined in database.py directly
# because they reference helper functions (_offset_ip, _build_seed_rules)
# that live there.  This file serves as the architectural bridge:
#
#   SEED_NEIGHBOURHOODS        – defined in database.py (17 NHs)
#   SEED_SECURITY_ZONES        – defined in database.py (Prod/NP/PP/Infra)
#   SEED_NGDC_DATACENTERS      – defined in database.py (3 NGDC DCs)
#   SEED_LEGACY_DATACENTERS    – defined in database.py (6 legacy DCs)
#   SEED_APPLICATIONS          – defined in database.py (27 apps)
#   SEED_LEGACY_TO_NGDC_IP_MAPPINGS – defined in database.py
#   SEED_COMPONENT_TO_SZ       – re-exported from mappings.py above
#   SEED_NGDC_STANDARD_GROUPS  – generated in database.py
#   _build_seed_rules()        – defined in database.py
#   SEED_MIGRATIONS            – defined in database.py
#   SEED_MIGRATION_MAPPINGS    – defined in database.py
#   SEED_GROUPS                – defined in database.py
#   SEED_CHG_REQUESTS          – defined in database.py
#   SEED_LEGACY_RULES          – defined in database.py
#
# As the MongoDB migration proceeds, each of these will be moved here
# (or removed entirely when real data is available).

# Pre-Production matrix is the same as nonprod for now
SEED_PREPROD_MATRIX = SEED_NONPROD_MATRIX
