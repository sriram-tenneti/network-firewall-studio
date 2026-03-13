"""In-memory database with seed data for the Network Firewall Studio.

Updated with real NGDC organizational constructs:
- 17 Neighbourhoods (NH01-NH17)
- 17 Security Zones (CDE, GEN, DMZ, RST, MGT, PNA, EPAA, UCPA, etc.)
- 6 Legacy Data Centers (Garland, Lynhaven, Richardson, Sterling, Glen Bornie, Manassas)
- 3 NGDC Data Centers (East, West, Central)
- Strict naming standards: grp-, svr-, rng-
- Group-to-group rule enforcement
"""

import uuid
from datetime import datetime, timedelta
from copy import deepcopy


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


# ============================================================
# NGDC Neighbourhoods (NH01-NH17)
# ============================================================

NEIGHBOURHOODS_REGISTRY = [
    {"id": "NH01", "name": "Technology Enablement Services", "zone": "GEN", "environment": "Production"},
    {"id": "NH02", "name": "Core Banking", "zone": "CDE", "environment": "Production"},
    {"id": "NH03", "name": "Digital Channels", "zone": "CDE", "environment": "Production"},
    {"id": "NH04", "name": "Wealth Management", "zone": "GEN", "environment": "Production"},
    {"id": "NH05", "name": "Enterprise Services", "zone": "GEN", "environment": "Production"},
    {"id": "NH06", "name": "Wholesale Banking", "zone": "CDE", "environment": "Production"},
    {"id": "NH07", "name": "Global Payments and Liquidity", "zone": "CDE", "environment": "Production"},
    {"id": "NH08", "name": "Data and Analytics", "zone": "GEN", "environment": "Production"},
    {"id": "NH09", "name": "Assisted Channels", "zone": "GEN", "environment": "Production"},
    {"id": "NH10", "name": "Consumer Lending", "zone": "GEN", "environment": "Production"},
    {"id": "NH11", "name": "Production Mainframe", "zone": "RST", "environment": "Production"},
    {"id": "NH12", "name": "Non-Production Mainframe", "zone": "GEN", "environment": "Non-Production"},
    {"id": "NH13", "name": "Non-Production Shared", "zone": "GEN", "environment": "Non-Production"},
    {"id": "NH14", "name": "DMZ", "zone": "DMZ", "environment": "Production"},
    {"id": "NH15", "name": "Non-Production DMZ", "zone": "DMZ", "environment": "Non-Production"},
    {"id": "NH16", "name": "Pre-Production (Non-Prod Shared)", "zone": "GEN", "environment": "Pre-Production"},
    {"id": "NH17", "name": "Pre-Production DMZ", "zone": "DMZ", "environment": "Pre-Production"},
]


# ============================================================
# Security Zones
# ============================================================

SECURITY_ZONES = [
    {"name": "Cardholder Data Environment", "code": "CDE", "description": "PCI DSS compliant zone for cardholder data processing"},
    {"name": "General", "code": "GEN", "description": "General purpose security zone for standard applications"},
    {"name": "DMZ", "code": "DMZ", "description": "Demilitarized zone for external-facing services"},
    {"name": "Restricted", "code": "RST", "description": "Highly restricted internal zone for sensitive systems"},
    {"name": "Management", "code": "MGT", "description": "Network management and monitoring zone"},
    {"name": "PAA Zone", "code": "PNA", "description": "Publicly Accessible Application zone"},
    {"name": "Extended PAA", "code": "EPAA", "description": "Extended Publicly Accessible Application zone"},
    {"name": "Ultra-Critical Payment Apps", "code": "UCPA", "description": "Enterprise Critical Payment Application zone"},
    {"name": "Business Critical CI", "code": "BCCI", "description": "Business Critical CI zone for most critical apps"},
    {"name": "Global General", "code": "GGEN", "description": "Global general purpose zone"},
    {"name": "Enterprise PIN", "code": "EPIN", "description": "Enterprise PIN processing zone"},
    {"name": "Lightweight PAA", "code": "LPAA", "description": "Lightweight PAA zone"},
    {"name": "US Pre-Production", "code": "USPP", "description": "US Pre-Production environment zone"},
    {"name": "External Enterprise", "code": "EXEN", "description": "External enterprise partner connectivity zone"},
    {"name": "External Partners", "code": "EXT", "description": "Zone for external partner connectivity"},
    {"name": "Critical Payment Network", "code": "CPN", "description": "Critical Payment Network zone"},
    {"name": "Special Zone", "code": "SPN", "description": "Special-purpose security zone"},
]


# ============================================================
# NGDC Data Centers with real Neighbourhoods
# ============================================================

NGDC_DATA_CENTERS = [
    {
        "name": "East NGDC",
        "code": "EAST_NGDC",
        "rule_count": 24,
        "neighbourhoods": [
            {"name": "Technology Enablement Services", "nh_id": "NH01", "zone": "GEN", "subnets": ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]},
            {"name": "Core Banking", "nh_id": "NH02", "zone": "CDE", "subnets": ["10.1.1.0/24", "10.1.2.0/24"]},
            {"name": "Digital Channels", "nh_id": "NH03", "zone": "CDE", "subnets": ["10.2.1.0/24", "10.2.2.0/24"]},
            {"name": "Wealth Management", "nh_id": "NH04", "zone": "GEN", "subnets": ["10.3.1.0/24"]},
            {"name": "Enterprise Services", "nh_id": "NH05", "zone": "GEN", "subnets": ["10.4.1.0/24", "10.4.2.0/24"]},
            {"name": "Global Payments and Liquidity", "nh_id": "NH07", "zone": "CDE", "subnets": ["10.6.1.0/24"]},
            {"name": "DMZ", "nh_id": "NH14", "zone": "DMZ", "subnets": ["10.70.1.0/24", "10.70.2.0/24"]},
            {"name": "Non-Production Shared", "nh_id": "NH13", "zone": "GEN", "subnets": ["10.100.1.0/24", "10.100.2.0/24"]},
        ],
        "ip_groups": [
            {
                "name": "grp-CRM-NH02-CDE-DB",
                "entries": [
                    {"name": "svr-CRM-NH02-CDE-CRMDB01", "ip": "10.1.1.10"},
                    {"name": "svr-CRM-NH02-CDE-CRMDB02", "ip": "10.1.1.11"},
                ],
            },
            {
                "name": "grp-CRM-NH02-CDE-APP",
                "entries": [
                    {"name": "svr-CRM-NH02-CDE-CRMAPP01", "ip": "10.1.2.10"},
                    {"name": "svr-CRM-NH02-CDE-CRMAPP02", "ip": "10.1.2.11"},
                ],
            },
            {
                "name": "grp-DIG-NH03-CDE-WEB",
                "entries": [
                    {"name": "svr-DIG-NH03-CDE-DIGWEB01", "ip": "10.2.1.10"},
                    {"name": "svr-DIG-NH03-CDE-DIGWEB02", "ip": "10.2.1.11"},
                ],
            },
            {
                "name": "grp-PAY-NH07-CDE-APP",
                "entries": [
                    {"name": "svr-PAY-NH07-CDE-PAYAPP01", "ip": "10.6.1.10"},
                    {"name": "svr-PAY-NH07-CDE-PAYAPP02", "ip": "10.6.1.11"},
                ],
            },
        ],
    },
    {
        "name": "West NGDC",
        "code": "WEST_NGDC",
        "rule_count": 18,
        "neighbourhoods": [
            {"name": "Digital Channels", "nh_id": "NH03", "zone": "CDE", "subnets": ["172.16.1.0/24", "172.16.2.0/24"]},
            {"name": "Enterprise Services", "nh_id": "NH05", "zone": "GEN", "subnets": ["172.16.10.0/24", "172.16.11.0/24"]},
            {"name": "Wholesale Banking", "nh_id": "NH06", "zone": "CDE", "subnets": ["172.16.20.0/24"]},
            {"name": "Data and Analytics", "nh_id": "NH08", "zone": "GEN", "subnets": ["172.16.30.0/24", "172.16.31.0/24"]},
            {"name": "Assisted Channels", "nh_id": "NH09", "zone": "GEN", "subnets": ["172.16.40.0/24"]},
            {"name": "DMZ", "nh_id": "NH14", "zone": "DMZ", "subnets": ["172.16.70.0/24"]},
            {"name": "Non-Production DMZ", "nh_id": "NH15", "zone": "DMZ", "subnets": ["172.16.80.0/24"]},
        ],
        "ip_groups": [
            {
                "name": "grp-DIG-NH03-CDE-APP",
                "entries": [
                    {"name": "svr-DIG-NH03-CDE-DIGAPP01", "ip": "172.16.1.10"},
                    {"name": "svr-DIG-NH03-CDE-DIGAPP02", "ip": "172.16.1.11"},
                ],
            },
            {
                "name": "grp-ENT-NH05-GEN-WEB",
                "entries": [
                    {"name": "svr-ENT-NH05-GEN-ENTWEB01", "ip": "172.16.10.10"},
                    {"name": "svr-ENT-NH05-GEN-ENTWEB02", "ip": "172.16.10.11"},
                ],
            },
        ],
    },
    {
        "name": "Central NGDC",
        "code": "CENTRAL_NGDC",
        "rule_count": 21,
        "neighbourhoods": [
            {"name": "Core Banking", "nh_id": "NH02", "zone": "CDE", "subnets": ["10.50.1.0/24", "10.50.2.0/24"]},
            {"name": "Consumer Lending", "nh_id": "NH10", "zone": "GEN", "subnets": ["10.55.1.0/24"]},
            {"name": "Production Mainframe", "nh_id": "NH11", "zone": "RST", "subnets": ["10.60.1.0/24"]},
            {"name": "Non-Production Mainframe", "nh_id": "NH12", "zone": "GEN", "subnets": ["10.61.1.0/24"]},
            {"name": "Pre-Production (Non-Prod Shared)", "nh_id": "NH16", "zone": "GEN", "subnets": ["10.65.1.0/24"]},
            {"name": "Pre-Production DMZ", "nh_id": "NH17", "zone": "DMZ", "subnets": ["10.66.1.0/24"]},
        ],
        "ip_groups": [
            {
                "name": "grp-CBK-NH02-CDE-DB",
                "entries": [
                    {"name": "svr-CBK-NH02-CDE-CBKDB01", "ip": "10.50.1.10"},
                    {"name": "svr-CBK-NH02-CDE-CBKDB02", "ip": "10.50.1.11"},
                ],
            },
            {
                "name": "grp-CBK-NH02-CDE-APP",
                "entries": [
                    {"name": "svr-CBK-NH02-CDE-CBKAPP01", "ip": "10.50.2.10"},
                ],
            },
        ],
    },
]


# ============================================================
# Legacy Data Centers
# ============================================================

LEGACY_DATA_CENTERS = [
    {"name": "DC Garland", "code": "DC_GARLAND"},
    {"name": "DC Lynhaven", "code": "DC_LYNHAVEN"},
    {"name": "DC Richardson", "code": "DC_RICHARDSON"},
    {"name": "DC Sterling", "code": "DC_STERLING"},
    {"name": "DC Glen Bornie", "code": "DC_GLEN_BORNIE"},
    {"name": "DC Manassas", "code": "DC_MANASSAS"},
]


# ============================================================
# Predefined Destinations (standards-compliant group names)
# ============================================================

PREDEFINED_DESTINATIONS = [
    {"name": "grp-DIG-NH03-CDE-WEB", "security_zone": "CDE", "description": "Digital Channels - Production Web Servers", "friendly_name": "DIGITAL CHANNELS - PROD"},
    {"name": "grp-ENT-NH05-GEN-APP", "security_zone": "GEN", "description": "Enterprise Services Application Servers", "friendly_name": "ENTERPRISE SERVICES"},
    {"name": "grp-SHR-NH13-GEN-SVC", "security_zone": "GEN", "description": "Shared Platform Services", "friendly_name": "SHARED PLATFORMS"},
    {"name": "grp-EXT-NH14-DMZ-API", "security_zone": "DMZ", "description": "External Partner API Gateway", "friendly_name": "EXTERNAL PARTNERS"},
    {"name": "grp-CBK-NH02-CDE-DB", "security_zone": "CDE", "description": "Core Banking Database Cluster", "friendly_name": "CORE DATABASE"},
    {"name": "grp-PAY-NH07-CDE-DB", "security_zone": "CDE", "description": "Global Payments Database", "friendly_name": "PAYMENTS DATABASE"},
    {"name": "grp-DMZ-NH14-DMZ-WEB", "security_zone": "DMZ", "description": "DMZ-hosted Web Services", "friendly_name": "DMZ WEB SERVICES"},
    {"name": "grp-MGT-NH01-MGT-MON", "security_zone": "MGT", "description": "Network Management & Monitoring", "friendly_name": "MANAGEMENT PLANE"},
    {"name": "grp-WHL-NH06-CDE-APP", "security_zone": "CDE", "description": "Wholesale Banking Application Servers", "friendly_name": "WHOLESALE BANKING"},
    {"name": "grp-DAT-NH08-GEN-APP", "security_zone": "GEN", "description": "Data & Analytics Application Servers", "friendly_name": "DATA & ANALYTICS"},
]

# Backward-compatible alias
NEIGHBOURHOODS = [{"name": n["name"], "zone": n["zone"]} for n in NEIGHBOURHOODS_REGISTRY]


# ============================================================
# Applications (structured with AppID, NH, SZ)
# ============================================================

APPLICATIONS = [
    {"id": "CRM", "name": "CRM Application", "app_id": "CRM", "owner": "Jane Smith", "nh": "NH02", "sz": "CDE"},
    {"id": "ORD", "name": "Ordering System", "app_id": "ORD", "owner": "Jon", "nh": "NH03", "sz": "CDE"},
    {"id": "PSA", "name": "PSA Services", "app_id": "PSA", "owner": "Jane Smith", "nh": "NH05", "sz": "GEN"},
    {"id": "DIG", "name": "Digital Banking", "app_id": "DIG", "owner": "Jon", "nh": "NH03", "sz": "CDE"},
    {"id": "PAY", "name": "Core Payments", "app_id": "PAY", "owner": "Jane Smith", "nh": "NH07", "sz": "CDE"},
    {"id": "ENT", "name": "Enterprise CRM", "app_id": "ENT", "owner": "Jon", "nh": "NH05", "sz": "GEN"},
    {"id": "SHR", "name": "Shared Analytics", "app_id": "SHR", "owner": "Jane Smith", "nh": "NH08", "sz": "GEN"},
    {"id": "WHL", "name": "Wholesale Banking", "app_id": "WHL", "owner": "Jon", "nh": "NH06", "sz": "CDE"},
    {"id": "CBK", "name": "Core Banking", "app_id": "CBK", "owner": "Jane Smith", "nh": "NH02", "sz": "CDE"},
    {"id": "CLN", "name": "Consumer Lending", "app_id": "CLN", "owner": "Jon", "nh": "NH10", "sz": "GEN"},
]

ENVIRONMENTS = ["Production", "Non-Production", "Pre-Production", "Development", "Staging", "DR"]


# ============================================================
# Naming Standards Config
# ============================================================

NAMING_STANDARDS = {
    "prefixes": {
        "grp": {"description": "Group (collection of servers)", "pattern": "grp-{AppID}-{NH}-{SZ}-{Subtype}"},
        "svr": {"description": "Individual server/IP", "pattern": "svr-{AppID}-{NH}-{SZ}-{ServerName}"},
        "rng": {"description": "Subnet/IP range", "pattern": "rng-{AppID}-{NH}-{SZ}-{Descriptor}"},
    },
    "subtypes": {
        "APP": "Application Servers",
        "WEB": "Web Servers",
        "DB": "Database Servers",
        "BAT": "Batch Servers",
        "MQ": "Message Queue",
        "API": "API Servers",
        "LB": "Load Balancers",
        "MON": "Monitoring",
        "MFR": "Mainframe",
        "SVC": "Services",
    },
    "enforcement_rules": [
        "All firewall rules MUST be group-to-group by default",
        "Non-group rules require security exception approval",
        "All names must follow naming convention with valid NH, SZ, and Subtype",
        "Legacy names must be migrated to standards-compliant names",
    ],
}


# ============================================================
# Firewall Rules - Standards-compliant seed data
# ============================================================

_firewall_rules: list[dict] = [
    {
        "id": _id(),
        "rule_id": "R-3012",
        "application": "ORD",
        "application_name": "Ordering System",
        "environment": "Production",
        "datacenter": "EAST_NGDC",
        "source": {
            "source_type": "Group",
            "ip_address": None,
            "cidr": None,
            "group_name": "grp-ORD-NH03-CDE-APP",
            "ports": "TCP 8443",
            "neighbourhood": "NH03",
            "neighbourhood_name": "Digital Channels",
            "security_zone": "CDE",
        },
        "destination": {
            "name": "grp-DIG-NH03-CDE-WEB",
            "friendly_name": "DIGITAL CHANNELS - PROD",
            "security_zone": "CDE",
            "dest_ip": "10.2.1.0/24",
            "ports": "TCP 8443",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Permitted",
        "status": "Deployed",
        "compliance": {"naming_valid": True, "group_to_group": True, "requires_exception": False},
        "expiry": "21-Dec-2025",
        "owner": "Jane Smith",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "certified_by": "Jon",
    },
    {
        "id": _id(),
        "rule_id": "R-3014",
        "application": "ORD",
        "application_name": "Ordering System",
        "environment": "Production",
        "datacenter": "EAST_NGDC",
        "source": {
            "source_type": "Group",
            "ip_address": None,
            "cidr": None,
            "group_name": "grp-ORD-NH03-CDE-APP",
            "ports": "TCP 8443",
            "neighbourhood": "NH05",
            "neighbourhood_name": "Enterprise Services",
            "security_zone": "GEN",
        },
        "destination": {
            "name": "grp-ENT-NH05-GEN-APP",
            "friendly_name": "ENTERPRISE SERVICES",
            "security_zone": "GEN",
            "dest_ip": "10.4.1.0/24",
            "ports": "TCP 8443",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Permitted",
        "status": "Draft",
        "compliance": {"naming_valid": True, "group_to_group": True, "requires_exception": False},
        "expiry": "19-Jul-2025",
        "owner": "Jane Smith",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": None,
        "certified_by": None,
    },
    {
        "id": _id(),
        "rule_id": "R-3018",
        "application": "CRM",
        "application_name": "CRM Application",
        "environment": "Production",
        "datacenter": "EAST_NGDC",
        "source": {
            "source_type": "Group",
            "ip_address": None,
            "cidr": None,
            "group_name": "grp-CRM-NH02-CDE-APP",
            "ports": "TCP 443",
            "neighbourhood": "NH03",
            "neighbourhood_name": "Digital Channels",
            "security_zone": "CDE",
        },
        "destination": {
            "name": "grp-DIG-NH03-CDE-WEB",
            "friendly_name": "DIGITAL CHANNELS - PROD",
            "security_zone": "CDE",
            "dest_ip": "10.2.1.0/24",
            "ports": "TCP 443",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Permitted",
        "status": "Deployed",
        "compliance": {"naming_valid": True, "group_to_group": True, "requires_exception": False},
        "expiry": "15-Mar-2026",
        "owner": "Jon",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
        "certified_by": "Jane Smith",
    },
    {
        "id": _id(),
        "rule_id": "R-3020",
        "application": "PSA",
        "application_name": "PSA Services",
        "environment": "Non-Production",
        "datacenter": "EAST_NGDC",
        "source": {
            "source_type": "Group",
            "ip_address": None,
            "cidr": None,
            "group_name": "grp-PSA-NH05-GEN-APP",
            "ports": "TCP 8080-8443",
            "neighbourhood": "NH13",
            "neighbourhood_name": "Non-Production Shared",
            "security_zone": "GEN",
        },
        "destination": {
            "name": "grp-SHR-NH13-GEN-SVC",
            "friendly_name": "SHARED PLATFORMS",
            "security_zone": "GEN",
            "dest_ip": "10.100.1.0/24",
            "ports": "TCP 8080",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Permitted",
        "status": "Certified",
        "compliance": {"naming_valid": True, "group_to_group": True, "requires_exception": False},
        "expiry": "30-Jun-2026",
        "owner": "Jane Smith",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": _now(),
        "certified_by": "Jon",
    },
    {
        "id": _id(),
        "rule_id": "R-3025",
        "application": "DIG",
        "application_name": "Digital Banking",
        "environment": "Production",
        "datacenter": "EAST_NGDC",
        "source": {
            "source_type": "Single IP",
            "ip_address": "10.0.0.1",
            "cidr": None,
            "group_name": None,
            "ports": "TCP 22",
            "neighbourhood": "NH14",
            "neighbourhood_name": "DMZ",
            "security_zone": "DMZ",
        },
        "destination": {
            "name": "grp-CBK-NH02-CDE-DB",
            "friendly_name": "CORE DATABASE",
            "security_zone": "CDE",
            "dest_ip": "10.50.1.10",
            "ports": "TCP 1521",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Blocked",
        "status": "Draft",
        "compliance": {"naming_valid": False, "group_to_group": False, "requires_exception": True},
        "expiry": None,
        "owner": "Jon",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": None,
        "certified_by": None,
    },
    {
        "id": _id(),
        "rule_id": "R-3030",
        "application": "PAY",
        "application_name": "Core Payments",
        "environment": "Production",
        "datacenter": "CENTRAL_NGDC",
        "source": {
            "source_type": "Group",
            "ip_address": None,
            "cidr": None,
            "group_name": "grp-PAY-NH07-CDE-APP",
            "ports": "TCP 8443",
            "neighbourhood": "NH07",
            "neighbourhood_name": "Global Payments and Liquidity",
            "security_zone": "CDE",
        },
        "destination": {
            "name": "grp-CBK-NH02-CDE-DB",
            "friendly_name": "CORE DATABASE",
            "security_zone": "CDE",
            "dest_ip": "10.50.1.0/24",
            "ports": "TCP 1521",
            "is_predefined": True,
            "dest_type": "Group",
        },
        "policy_result": "Permitted",
        "status": "Deployed",
        "compliance": {"naming_valid": True, "group_to_group": True, "requires_exception": False},
        "expiry": "01-Jan-2027",
        "owner": "Jane Smith",
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": _now(),
        "certified_by": "Jon",
    },
]


# ============================================================
# Migration Data - with legacy non-standard names
# ============================================================

_migrations: list[dict] = [
    {
        "id": "mig-001",
        "application": "CRM",
        "application_name": "CRM Application",
        "source_legacy_dc": "DC_GARLAND",
        "target_ngdc": "EAST_NGDC",
        "map_to_standard_groups": True,
        "map_to_subnet_cidr": False,
        "status": "In Progress",
        "created_at": _now(),
    },
]

_migration_mappings: list[dict] = [
    {
        "id": _id(),
        "migration_id": "mig-001",
        "legacy_source": "CRM_APP_GROUP",
        "legacy_source_detail": "TCP 8080-8443",
        "legacy_group": "CRM_APP_GROUP",
        "ngdc_target": "grp-CRM-NH02-CDE-APP",
        "ngdc_target_detail": "Core Banking / CDE zone",
        "mapping_status": "Auto-Mapped",
        "trust_zones_automapped": 2,
        "related_policies": ["PW14963", "PW17021", "PW15124"],
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "legacy_source": "Retail_DC_SUBNET",
        "legacy_source_detail": "10.100.0.0/16",
        "legacy_group": None,
        "ngdc_target": "rng-CRM-NH03-CDE-WEBNET",
        "ngdc_target_detail": "Digital Channels / CDE zone",
        "mapping_status": "Needs Review",
        "trust_zones_automapped": 0,
        "related_policies": [],
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "legacy_source": "CORE_DB_SERVICES",
        "legacy_source_detail": "Database cluster",
        "legacy_group": "CORE_DB",
        "ngdc_target": "grp-CRM-NH02-CDE-DB",
        "ngdc_target_detail": "Core Banking / CDE DB zone",
        "mapping_status": "Auto-Mapped",
        "trust_zones_automapped": 3,
        "related_policies": ["PW14863", "PW1524", "PW1721"],
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "legacy_source": "UDAT_EXTRA_SERVER",
        "legacy_source_detail": "Application server 10.25.3.50",
        "legacy_group": None,
        "ngdc_target": "svr-CRM-NH02-CDE-UDATXTRA01",
        "ngdc_target_detail": "Individual server - needs group assignment",
        "mapping_status": "New Group",
        "trust_zones_automapped": 0,
        "related_policies": [],
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "legacy_source": "OLD_BATCH_FARM",
        "legacy_source_detail": "Batch processing cluster",
        "legacy_group": "OLD_BATCH",
        "ngdc_target": "grp-CRM-NH02-CDE-BAT",
        "ngdc_target_detail": "Core Banking / CDE batch zone",
        "mapping_status": "Auto-Mapped",
        "trust_zones_automapped": 1,
        "related_policies": ["PW16543"],
        "naming_compliant": True,
    },
]

_migration_rule_lifecycle: list[dict] = [
    {
        "id": _id(),
        "migration_id": "mig-001",
        "rule_id": "R-L001",
        "source": "CRM_APP_GROUP (10.25.12.12)",
        "source_ip": "10.25.12.12",
        "mapping_status": "Policy Review",
        "ngdc_target": "grp-CRM-NH02-CDE-APP",
        "destination_detail": "TCP 8443",
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "rule_id": "R-L002",
        "source": "Retail_DC_SUBNET (10.100.0.0/16)",
        "source_ip": "10.100.0.0/16",
        "mapping_status": "Draft",
        "ngdc_target": "rng-CRM-NH03-CDE-WEBNET",
        "destination_detail": "TCP 443",
        "naming_compliant": True,
    },
    {
        "id": _id(),
        "migration_id": "mig-001",
        "rule_id": "R-L003",
        "source": "CORE_DB (10.50.1.10-11)",
        "source_ip": "10.50.1.10",
        "mapping_status": "Draft",
        "ngdc_target": "grp-CRM-NH02-CDE-DB",
        "destination_detail": "TCP 1521",
        "naming_compliant": True,
    },
]


# ============================================================
# Rule History
# ============================================================

_rule_history: list[dict] = [
    {
        "id": _id(),
        "rule_id": "R-3012",
        "action": "Created",
        "timestamp": (datetime.utcnow() - timedelta(days=90)).isoformat(),
        "user": "Jane Smith",
        "details": "Rule created for Ordering System - grp-ORD-NH03-CDE-APP -> grp-DIG-NH03-CDE-WEB",
    },
    {
        "id": _id(),
        "rule_id": "R-3012",
        "action": "Naming Validated",
        "timestamp": (datetime.utcnow() - timedelta(days=89)).isoformat(),
        "user": "System",
        "details": "Naming standards compliance check passed. Group-to-group verified.",
    },
    {
        "id": _id(),
        "rule_id": "R-3012",
        "action": "Deployed",
        "timestamp": (datetime.utcnow() - timedelta(days=85)).isoformat(),
        "user": "Jon",
        "details": "Rule deployed via CHG00012345",
    },
    {
        "id": _id(),
        "rule_id": "R-3012",
        "action": "Certified",
        "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "user": "Jon",
        "details": "Periodic certification completed",
    },
    {
        "id": _id(),
        "rule_id": "R-3014",
        "action": "Created",
        "timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat(),
        "user": "Jane Smith",
        "details": "Rule created for Ordering System - grp-ORD-NH03-CDE-APP -> grp-ENT-NH05-GEN-APP",
    },
    {
        "id": _id(),
        "rule_id": "R-3025",
        "action": "Created",
        "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "user": "Jon",
        "details": "Rule created - NON-COMPLIANT: Single IP source (not group-to-group)",
    },
    {
        "id": _id(),
        "rule_id": "R-3025",
        "action": "Compliance Warning",
        "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "user": "System",
        "details": "Rule does not follow group-to-group policy. Exception required.",
    },
]


# ============================================================
# CHG Requests
# ============================================================

_chg_requests: list[dict] = [
    {
        "id": _id(),
        "chg_number": "CHG00012345",
        "rule_ids": ["R-3012"],
        "migration_id": None,
        "status": "Closed",
        "created_at": (datetime.utcnow() - timedelta(days=85)).isoformat(),
        "description": "Deploy firewall rule R-3012 for Ordering System (grp-ORD-NH03-CDE-APP -> grp-DIG-NH03-CDE-WEB)",
    },
]


# ============================================================
# CRUD operations
# ============================================================

# --- Firewall Rules ---

def get_all_rules(application: str | None = None, status: str | None = None) -> list[dict]:
    rules = deepcopy(_firewall_rules)
    if application:
        rules = [r for r in rules if r["application"] == application or r.get("application_name") == application]
    if status:
        rules = [r for r in rules if r["status"] == status]
    return rules


def get_rule_by_id(rule_id: str) -> dict | None:
    for r in _firewall_rules:
        if r["rule_id"] == rule_id or r["id"] == rule_id:
            return deepcopy(r)
    return None


def create_rule(data: dict) -> dict:
    from app.services.naming_standards import validate_name, check_group_to_group

    rule_num = 3000 + len(_firewall_rules) + 1
    source = data.get("source", {})
    destination = data.get("destination", {})

    # Validate naming standards
    naming_valid = True
    naming_errors: list[str] = []

    src_group = source.get("group_name")
    if src_group and src_group.startswith(("grp-", "svr-", "rng-")):
        src_validation = validate_name(src_group)
        if not src_validation["valid"]:
            naming_valid = False
            naming_errors.append(f"Source: {src_validation.get('error', 'Invalid name')}")

    dst_name = destination.get("name", "")
    if dst_name and dst_name.startswith(("grp-", "svr-", "rng-")):
        dst_validation = validate_name(dst_name)
        if not dst_validation["valid"]:
            naming_valid = False
            naming_errors.append(f"Destination: {dst_validation.get('error', 'Invalid name')}")

    # Check group-to-group compliance
    src_type = source.get("source_type", "Single IP")
    dst_type = destination.get("dest_type", "predefined" if destination.get("is_predefined") else "custom")
    g2g = check_group_to_group(src_type, dst_type)

    rule = {
        "id": _id(),
        "rule_id": f"R-{rule_num}",
        "application": data.get("application", "ORD"),
        "application_name": data.get("application_name", ""),
        "environment": data.get("environment", "Production"),
        "datacenter": data.get("datacenter", "EAST_NGDC"),
        "source": source,
        "destination": destination,
        "policy_result": "Permitted",
        "status": "Draft",
        "compliance": {
            "naming_valid": naming_valid,
            "naming_errors": naming_errors,
            "group_to_group": g2g["compliant"],
            "requires_exception": g2g["requires_exception"],
        },
        "expiry": None,
        "owner": data.get("owner", "Jane Smith"),
        "created_at": _now(),
        "updated_at": _now(),
        "certified_at": None,
        "certified_by": None,
    }
    _firewall_rules.append(rule)

    _rule_history.append({
        "id": _id(),
        "rule_id": rule["rule_id"],
        "action": "Created",
        "timestamp": _now(),
        "user": rule["owner"],
        "details": f"Rule created for {rule.get('application_name') or rule['application']}",
    })

    if not naming_valid:
        _rule_history.append({
            "id": _id(),
            "rule_id": rule["rule_id"],
            "action": "Compliance Warning",
            "timestamp": _now(),
            "user": "System",
            "details": f"Naming standards violation: {'; '.join(naming_errors)}",
        })

    if not g2g["compliant"]:
        _rule_history.append({
            "id": _id(),
            "rule_id": rule["rule_id"],
            "action": "Compliance Warning",
            "timestamp": _now(),
            "user": "System",
            "details": g2g["message"],
        })

    return deepcopy(rule)


def update_rule(rule_id: str, data: dict) -> dict | None:
    for r in _firewall_rules:
        if r["rule_id"] == rule_id or r["id"] == rule_id:
            for k, v in data.items():
                if v is not None and k in r:
                    r[k] = v
            r["updated_at"] = _now()

            _rule_history.append({
                "id": _id(),
                "rule_id": r["rule_id"],
                "action": "Modified",
                "timestamp": _now(),
                "user": r["owner"],
                "details": f"Rule updated: {', '.join(data.keys())}",
            })

            return deepcopy(r)
    return None


def delete_rule(rule_id: str) -> bool:
    for r in _firewall_rules:
        if r["rule_id"] == rule_id or r["id"] == rule_id:
            r["status"] = "Deleted"
            _rule_history.append({
                "id": _id(),
                "rule_id": r["rule_id"],
                "action": "Deleted",
                "timestamp": _now(),
                "user": r["owner"],
                "details": "Rule marked as deleted",
            })
            return True
    return False


def certify_rule(rule_id: str, user: str = "Jon") -> dict | None:
    for r in _firewall_rules:
        if r["rule_id"] == rule_id or r["id"] == rule_id:
            r["status"] = "Certified"
            r["certified_at"] = _now()
            r["certified_by"] = user
            r["updated_at"] = _now()

            _rule_history.append({
                "id": _id(),
                "rule_id": r["rule_id"],
                "action": "Certified",
                "timestamp": _now(),
                "user": user,
                "details": "Rule certified",
            })

            return deepcopy(r)
    return None


def submit_rule(rule_id: str) -> dict | None:
    """Submit rule: creates a CHG request and marks rule as Pending Review."""
    for r in _firewall_rules:
        if r["rule_id"] == rule_id or r["id"] == rule_id:
            r["status"] = "Pending Review"
            r["updated_at"] = _now()

            chg_num = f"CHG{10000 + len(_chg_requests) + 1:08d}"
            chg = {
                "id": _id(),
                "chg_number": chg_num,
                "rule_ids": [r["rule_id"]],
                "migration_id": None,
                "status": "Open",
                "created_at": _now(),
                "description": f"Deploy firewall rule {r['rule_id']} for {r.get('application_name') or r['application']}",
            }
            _chg_requests.append(chg)

            _rule_history.append({
                "id": _id(),
                "rule_id": r["rule_id"],
                "action": "Submitted",
                "timestamp": _now(),
                "user": r["owner"],
                "details": f"ServiceNow CHG request {chg_num} created",
            })

            return {"rule": deepcopy(r), "chg": deepcopy(chg)}
    return None


# --- Rule History ---

def get_rule_history(rule_id: str) -> list[dict]:
    return [deepcopy(h) for h in _rule_history if h["rule_id"] == rule_id]


# --- Migrations ---

def get_all_migrations() -> list[dict]:
    return deepcopy(_migrations)


def get_migration_by_id(migration_id: str) -> dict | None:
    for m in _migrations:
        if m["id"] == migration_id:
            return deepcopy(m)
    return None


def create_migration(data: dict) -> dict:
    migration = {
        "id": f"mig-{len(_migrations) + 1:03d}",
        "application": data["application"],
        "application_name": data.get("application_name", ""),
        "source_legacy_dc": data["source_legacy_dc"],
        "target_ngdc": data["target_ngdc"],
        "map_to_standard_groups": data.get("map_to_standard_groups", True),
        "map_to_subnet_cidr": data.get("map_to_subnet_cidr", False),
        "status": "Draft",
        "created_at": _now(),
    }
    _migrations.append(migration)

    # Auto-generate mappings with standards-compliant names
    _auto_generate_mappings(migration["id"], data["application"])

    return deepcopy(migration)


def _auto_generate_mappings(migration_id: str, application: str) -> None:
    """Auto-map legacy rules to NGDC with standards-compliant naming."""
    app_id = application.upper()[:3]
    nh = "NH05"
    sz = "GEN"

    # Find app info
    for app in APPLICATIONS:
        if app["id"] == application or app["app_id"] == application:
            app_id = app["app_id"]
            nh = app["nh"]
            sz = app["sz"]
            break

    legacy_entries = [
        (f"LEGACY_{app_id}_SRV_GROUP", "TCP 8080", "Auto-Mapped", f"grp-{app_id}-{nh}-{sz}-APP", 2),
        (f"LEGACY_{app_id}_DB_SUBNET", "10.x.x.0/24", "Needs Review", f"rng-{app_id}-{nh}-{sz}-DBNET", 0),
        (f"LEGACY_{app_id}_WEB_FARM", "HTTP/HTTPS", "Auto-Mapped", f"grp-{app_id}-{nh}-{sz}-WEB", 3),
    ]
    for src, detail, status, target, zones in legacy_entries:
        _migration_mappings.append({
            "id": _id(),
            "migration_id": migration_id,
            "legacy_source": src,
            "legacy_source_detail": detail,
            "legacy_group": src,
            "ngdc_target": target,
            "ngdc_target_detail": "",
            "mapping_status": status,
            "trust_zones_automapped": zones,
            "related_policies": [],
            "naming_compliant": True,
        })


def get_migration_mappings(migration_id: str) -> list[dict]:
    return [deepcopy(m) for m in _migration_mappings if m["migration_id"] == migration_id]


def get_migration_rule_lifecycle(migration_id: str) -> list[dict]:
    return [deepcopy(r) for r in _migration_rule_lifecycle if r["migration_id"] == migration_id]


def validate_migration(migration_id: str) -> dict:
    mappings = get_migration_mappings(migration_id)
    auto_mapped = sum(1 for m in mappings if m["mapping_status"] == "Auto-Mapped")
    conflicts = sum(1 for m in mappings if m["mapping_status"] in ("Conflict", "Needs Review"))
    naming_compliant = sum(1 for m in mappings if m.get("naming_compliant", False))
    return {
        "migration_id": migration_id,
        "total_mappings": len(mappings),
        "auto_mapped": auto_mapped,
        "conflicts": conflicts,
        "naming_compliant": naming_compliant,
        "validation_passed": conflicts == 0,
        "message": "Validation passed - all mappings standards-compliant" if conflicts == 0 else f"{conflicts} conflict(s) need review",
    }


def submit_migration(migration_id: str) -> dict | None:
    for m in _migrations:
        if m["id"] == migration_id:
            m["status"] = "Submitted"

            chg_num = f"CHG{10000 + len(_chg_requests) + 1:08d}"
            chg = {
                "id": _id(),
                "chg_number": chg_num,
                "rule_ids": [],
                "migration_id": migration_id,
                "status": "Open",
                "created_at": _now(),
                "description": f"Migration {migration_id} for {m.get('application_name') or m['application']}",
            }
            _chg_requests.append(chg)
            return {"migration": deepcopy(m), "chg": deepcopy(chg)}
    return None


# --- Reference Data ---

def get_ngdc_datacenters() -> list[dict]:
    return deepcopy(NGDC_DATA_CENTERS)


def get_security_zones() -> list[dict]:
    return deepcopy(SECURITY_ZONES)


def get_predefined_destinations() -> list[dict]:
    return deepcopy(PREDEFINED_DESTINATIONS)


def get_neighbourhoods() -> list[dict]:
    return deepcopy(NEIGHBOURHOODS_REGISTRY)


def get_legacy_datacenters() -> list[dict]:
    return deepcopy(LEGACY_DATA_CENTERS)


def get_applications() -> list[dict]:
    return deepcopy(APPLICATIONS)


def get_environments() -> list[str]:
    return list(ENVIRONMENTS)


def get_chg_requests() -> list[dict]:
    return deepcopy(_chg_requests)


def get_naming_standards() -> dict:
    return deepcopy(NAMING_STANDARDS)


# --- Policy Validation ---

def validate_policy(source: dict, destination: dict, application: str = "", environment: str = "Production") -> dict:
    """Validate policy against NGDC matrix with naming standards check."""
    from app.services.naming_standards import validate_name, check_group_to_group

    src_zone = source.get("security_zone", "GEN")
    dst_zone = destination.get("security_zone", "GEN")

    # Check naming compliance
    naming_issues: list[str] = []
    src_group = source.get("group_name")
    if src_group and src_group.startswith(("grp-", "svr-", "rng-")):
        v = validate_name(src_group)
        if not v["valid"]:
            naming_issues.append(f"Source naming: {v.get('error', 'Invalid')}")

    dst_name = destination.get("name", "")
    if dst_name and dst_name.startswith(("grp-", "svr-", "rng-")):
        v = validate_name(dst_name)
        if not v["valid"]:
            naming_issues.append(f"Destination naming: {v.get('error', 'Invalid')}")

    # Check group-to-group
    src_type = source.get("source_type", "Single IP")
    dst_type = "Group" if destination.get("is_predefined") else "custom"
    g2g = check_group_to_group(src_type, dst_type)

    # Simulated policy matrix rules
    blocked_pairs = [
        ("DMZ", "RST"),
        ("EXT", "RST"),
        ("EXT", "CDE"),
        ("DMZ", "CDE"),
    ]

    for bsrc, bdst in blocked_pairs:
        if src_zone == bsrc and dst_zone == bdst:
            return {
                "result": "Blocked",
                "message": f"Traffic from {src_zone} to {dst_zone} is blocked by NGDC security policy",
                "details": [
                    f"Source zone: {src_zone}",
                    f"Destination zone: {dst_zone}",
                    "This zone pair is explicitly denied in the NGDC matrix",
                ] + naming_issues,
                "ngdc_zone_check": False,
                "birthright_compliant": False,
                "naming_compliant": len(naming_issues) == 0,
                "group_to_group_compliant": g2g["compliant"],
            }

    exception_pairs = [("GEN", "RST"), ("GEN", "CDE"), ("DMZ", "GEN")]
    for esrc, edst in exception_pairs:
        if src_zone == esrc and dst_zone == edst:
            return {
                "result": "Exception Required",
                "message": f"Traffic from {src_zone} to {dst_zone} requires a security exception",
                "details": [
                    f"Source zone: {src_zone}",
                    f"Destination zone: {dst_zone}",
                    "Exception approval needed from Security team",
                ] + naming_issues,
                "ngdc_zone_check": True,
                "birthright_compliant": False,
                "naming_compliant": len(naming_issues) == 0,
                "group_to_group_compliant": g2g["compliant"],
            }

    result_details = [
        f"Source zone: {src_zone}",
        f"Destination zone: {dst_zone}",
        "Zone pair permitted in NGDC matrix",
        "Birthright rules check passed",
    ]

    if not g2g["compliant"]:
        result_details.append(f"WARNING: {g2g['message']}")

    return {
        "result": "Permitted",
        "message": "Compliant with NGDC Security Policy",
        "details": result_details + naming_issues,
        "ngdc_zone_check": True,
        "birthright_compliant": True,
        "naming_compliant": len(naming_issues) == 0,
        "group_to_group_compliant": g2g["compliant"],
    }
