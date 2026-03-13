"""MongoDB-backed database for the Network Firewall Studio.

All reference data (Neighbourhoods, Security Zones, Data Centers, Applications,
IP Ranges, Naming Standards, Policy Matrix) is fully customizable via CRUD APIs.

Data is seeded on first startup and persisted in MongoDB.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.mongodb import get_db, COLLECTIONS


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


def _strip_mongo_id(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc and "_id" in doc:
        doc.pop("_id")
    return doc


def _strip_many(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for d in docs:
        d.pop("_id", None)
    return docs


# ============================================================
# Seed Data Definitions
# ============================================================

SEED_NEIGHBOURHOODS = [
    {"nh_id": "NH01", "name": "Technology Enablement Services", "zone": "GEN", "environment": "Production",
     "description": "Infrastructure and platform services", "ip_ranges": [
        {"cidr": "10.0.1.0/24", "description": "TES Primary", "dc": "EAST_NGDC"},
        {"cidr": "10.0.2.0/24", "description": "TES Secondary", "dc": "EAST_NGDC"},
        {"cidr": "172.16.50.0/24", "description": "TES West Primary", "dc": "WEST_NGDC"},
        {"cidr": "10.50.50.0/24", "description": "TES Central Primary", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH02", "name": "Core Banking", "zone": "CDE", "environment": "Production",
     "description": "Core banking applications and databases", "ip_ranges": [
        {"cidr": "10.1.1.0/24", "description": "Core Banking App Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.1.2.0/24", "description": "Core Banking DB Tier", "dc": "EAST_NGDC"},
        {"cidr": "172.16.1.0/24", "description": "Core Banking West App", "dc": "WEST_NGDC"},
        {"cidr": "10.50.1.0/24", "description": "Core Banking Central App", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH03", "name": "Digital Channels", "zone": "CDE", "environment": "Production",
     "description": "Digital banking channels - web, mobile, API", "ip_ranges": [
        {"cidr": "10.2.1.0/24", "description": "Digital Web Servers", "dc": "EAST_NGDC"},
        {"cidr": "10.2.2.0/24", "description": "Digital App Servers", "dc": "EAST_NGDC"},
        {"cidr": "172.16.3.0/24", "description": "Digital West Web", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH04", "name": "Wealth Management", "zone": "GEN", "environment": "Production",
     "description": "Wealth management and advisory platforms", "ip_ranges": [
        {"cidr": "10.3.1.0/24", "description": "Wealth Mgmt App Tier", "dc": "EAST_NGDC"},
        {"cidr": "172.16.5.0/24", "description": "Wealth West Primary", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH05", "name": "Enterprise Services", "zone": "GEN", "environment": "Production",
     "description": "Shared enterprise platforms and services", "ip_ranges": [
        {"cidr": "10.4.1.0/24", "description": "Enterprise App Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.4.2.0/24", "description": "Enterprise DB Tier", "dc": "EAST_NGDC"},
        {"cidr": "172.16.10.0/24", "description": "Enterprise West App", "dc": "WEST_NGDC"},
        {"cidr": "10.54.1.0/24", "description": "Enterprise Central App", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH06", "name": "Wholesale Banking", "zone": "CDE", "environment": "Production",
     "description": "Wholesale and commercial banking", "ip_ranges": [
        {"cidr": "10.5.1.0/24", "description": "Wholesale App Tier", "dc": "EAST_NGDC"},
        {"cidr": "172.16.20.0/24", "description": "Wholesale West App", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH07", "name": "Global Payments and Liquidity", "zone": "CDE", "environment": "Production",
     "description": "Payment processing and liquidity management", "ip_ranges": [
        {"cidr": "10.6.1.0/24", "description": "Payments App Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.6.2.0/24", "description": "Payments DB Tier", "dc": "EAST_NGDC"},
        {"cidr": "172.16.22.0/24", "description": "Payments West App", "dc": "WEST_NGDC"},
        {"cidr": "10.56.1.0/24", "description": "Payments Central App", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH08", "name": "Data and Analytics", "zone": "GEN", "environment": "Production",
     "description": "Data warehousing, analytics, and BI platforms", "ip_ranges": [
        {"cidr": "10.7.1.0/24", "description": "Data Analytics App", "dc": "EAST_NGDC"},
        {"cidr": "172.16.30.0/24", "description": "Data West App", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH09", "name": "Assisted Channels", "zone": "GEN", "environment": "Production",
     "description": "Branch, call center, and assisted channel apps", "ip_ranges": [
        {"cidr": "10.8.1.0/24", "description": "Assisted Channels App", "dc": "EAST_NGDC"},
        {"cidr": "172.16.40.0/24", "description": "Assisted West App", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH10", "name": "Consumer Lending", "zone": "GEN", "environment": "Production",
     "description": "Consumer lending and loan origination", "ip_ranges": [
        {"cidr": "10.9.1.0/24", "description": "Lending App Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.55.1.0/24", "description": "Lending Central App", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH11", "name": "Production Mainframe", "zone": "RST", "environment": "Production",
     "description": "Production mainframe systems (z/OS, CICS, DB2)", "ip_ranges": [
        {"cidr": "10.10.1.0/24", "description": "Mainframe LPAR Primary", "dc": "EAST_NGDC"},
        {"cidr": "10.60.1.0/24", "description": "Mainframe Central Primary", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH12", "name": "Non-Production Mainframe", "zone": "GEN", "environment": "Non-Production",
     "description": "Non-production mainframe systems (test, dev)", "ip_ranges": [
        {"cidr": "10.11.1.0/24", "description": "Non-Prod MF Primary", "dc": "EAST_NGDC"},
        {"cidr": "10.61.1.0/24", "description": "Non-Prod MF Central", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH13", "name": "Non-Production Shared", "zone": "GEN", "environment": "Non-Production",
     "description": "Shared non-production environment for testing", "ip_ranges": [
        {"cidr": "10.100.1.0/24", "description": "Non-Prod Shared App", "dc": "EAST_NGDC"},
        {"cidr": "172.16.100.0/24", "description": "Non-Prod West Shared", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH14", "name": "DMZ", "zone": "DMZ", "environment": "Production",
     "description": "Demilitarized zone for external-facing services", "ip_ranges": [
        {"cidr": "10.70.1.0/24", "description": "DMZ Web Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.70.2.0/24", "description": "DMZ API Gateway", "dc": "EAST_NGDC"},
        {"cidr": "172.16.70.0/24", "description": "DMZ West Web", "dc": "WEST_NGDC"},
        {"cidr": "10.70.10.0/24", "description": "DMZ Central Web", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH15", "name": "Non-Production DMZ", "zone": "DMZ", "environment": "Non-Production",
     "description": "Non-production DMZ for test external services", "ip_ranges": [
        {"cidr": "10.80.1.0/24", "description": "Non-Prod DMZ Web", "dc": "EAST_NGDC"},
        {"cidr": "172.16.80.0/24", "description": "Non-Prod DMZ West", "dc": "WEST_NGDC"},
     ]},
    {"nh_id": "NH16", "name": "Pre-Production (Non-Prod Shared)", "zone": "GEN", "environment": "Pre-Production",
     "description": "Pre-production staging environment", "ip_ranges": [
        {"cidr": "10.90.1.0/24", "description": "Pre-Prod App Tier", "dc": "EAST_NGDC"},
        {"cidr": "10.65.1.0/24", "description": "Pre-Prod Central App", "dc": "CENTRAL_NGDC"},
     ]},
    {"nh_id": "NH17", "name": "Pre-Production DMZ", "zone": "DMZ", "environment": "Pre-Production",
     "description": "Pre-production DMZ for staging external services", "ip_ranges": [
        {"cidr": "10.91.1.0/24", "description": "Pre-Prod DMZ Web", "dc": "EAST_NGDC"},
        {"cidr": "10.66.1.0/24", "description": "Pre-Prod DMZ Central", "dc": "CENTRAL_NGDC"},
     ]},
]

SEED_SECURITY_ZONES = [
    {"code": "CDE", "name": "Cardholder Data Environment", "description": "PCI DSS compliant zone",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.1.0.0/16", "description": "CDE East Block", "dc": "EAST_NGDC"},
        {"cidr": "172.16.0.0/20", "description": "CDE West Block", "dc": "WEST_NGDC"},
        {"cidr": "10.50.0.0/16", "description": "CDE Central Block", "dc": "CENTRAL_NGDC"},
     ]},
    {"code": "GEN", "name": "General", "description": "General purpose security zone",
     "risk_level": "Medium", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.0.0.0/16", "description": "GEN East Block", "dc": "EAST_NGDC"},
        {"cidr": "172.16.32.0/20", "description": "GEN West Block", "dc": "WEST_NGDC"},
     ]},
    {"code": "DMZ", "name": "DMZ", "description": "Demilitarized zone for external-facing services",
     "risk_level": "High", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.70.0.0/16", "description": "DMZ East Block", "dc": "EAST_NGDC"},
        {"cidr": "172.16.70.0/22", "description": "DMZ West Block", "dc": "WEST_NGDC"},
     ]},
    {"code": "RST", "name": "Restricted", "description": "Highly restricted zone for sensitive systems",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.10.0.0/16", "description": "RST East Block", "dc": "EAST_NGDC"},
        {"cidr": "10.60.0.0/16", "description": "RST Central Block", "dc": "CENTRAL_NGDC"},
     ]},
    {"code": "MGT", "name": "Management", "description": "Network management and monitoring zone",
     "risk_level": "High", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.200.1.0/24", "description": "MGT East", "dc": "EAST_NGDC"},
     ]},
    {"code": "PNA", "name": "PAA Zone", "description": "Publicly Accessible Application zone",
     "risk_level": "High", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.71.1.0/24", "description": "PNA East", "dc": "EAST_NGDC"},
     ]},
    {"code": "EPAA", "name": "Extended PAA", "description": "Extended PAA zone",
     "risk_level": "High", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.72.1.0/24", "description": "EPAA East", "dc": "EAST_NGDC"},
     ]},
    {"code": "UCPA", "name": "Ultra-Critical Payment Apps", "description": "Critical Payment Application zone",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.73.1.0/24", "description": "UCPA East", "dc": "EAST_NGDC"},
     ]},
    {"code": "BCCI", "name": "Business Critical CI", "description": "Business Critical CI zone",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.74.1.0/24", "description": "BCCI East", "dc": "EAST_NGDC"},
     ]},
    {"code": "GGEN", "name": "Global General", "description": "Global general purpose zone",
     "risk_level": "Medium", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.75.1.0/24", "description": "GGEN East", "dc": "EAST_NGDC"},
     ]},
    {"code": "EPIN", "name": "Enterprise PIN", "description": "Enterprise PIN processing zone",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.76.1.0/24", "description": "EPIN East", "dc": "EAST_NGDC"},
     ]},
    {"code": "LPAA", "name": "Lightweight PAA", "description": "Lightweight PAA zone",
     "risk_level": "High", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.77.1.0/24", "description": "LPAA East", "dc": "EAST_NGDC"},
     ]},
    {"code": "USPP", "name": "US Pre-Production", "description": "US Pre-Production zone",
     "risk_level": "Low", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.90.0.0/16", "description": "USPP East", "dc": "EAST_NGDC"},
     ]},
    {"code": "EXEN", "name": "External Enterprise", "description": "External enterprise partner zone",
     "risk_level": "High", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.78.1.0/24", "description": "EXEN East", "dc": "EAST_NGDC"},
     ]},
    {"code": "EXT", "name": "External Partners", "description": "External partner connectivity zone",
     "risk_level": "High", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.79.1.0/24", "description": "EXT East", "dc": "EAST_NGDC"},
     ]},
    {"code": "CPN", "name": "Critical Payment Network", "description": "Critical Payment Network zone",
     "risk_level": "Critical", "pci_scope": True, "ip_ranges": [
        {"cidr": "10.73.2.0/24", "description": "CPN East", "dc": "EAST_NGDC"},
     ]},
    {"code": "SPN", "name": "Special Zone", "description": "Special-purpose security zone",
     "risk_level": "High", "pci_scope": False, "ip_ranges": [
        {"cidr": "10.79.10.0/24", "description": "SPN East", "dc": "EAST_NGDC"},
     ]},
]

SEED_NGDC_DATACENTERS = [
    {"name": "East NGDC", "code": "EAST_NGDC", "location": "Ashburn, VA", "status": "Active",
     "description": "Primary East Coast NGDC facility", "contact": "noc-east@company.com",
     "capacity": "2000 racks", "ip_supernet": "10.0.0.0/8",
     "neighbourhoods": ["NH01","NH02","NH03","NH04","NH05","NH07","NH08","NH09","NH13","NH14","NH15","NH16","NH17"]},
    {"name": "West NGDC", "code": "WEST_NGDC", "location": "Santa Clara, CA", "status": "Active",
     "description": "Primary West Coast NGDC facility", "contact": "noc-west@company.com",
     "capacity": "1500 racks", "ip_supernet": "172.16.0.0/12",
     "neighbourhoods": ["NH03","NH05","NH06","NH08","NH09","NH14","NH15"]},
    {"name": "Central NGDC", "code": "CENTRAL_NGDC", "location": "Dallas, TX", "status": "Active",
     "description": "Central NGDC for DR and mainframe", "contact": "noc-central@company.com",
     "capacity": "1200 racks", "ip_supernet": "10.50.0.0/12",
     "neighbourhoods": ["NH02","NH10","NH11","NH12","NH16","NH17"]},
]

SEED_LEGACY_DATACENTERS = [
    {"name": "DC Garland", "code": "DC_GARLAND", "location": "Garland, TX", "status": "Decommissioning",
     "description": "Legacy DC - migration to Central NGDC", "ip_range": "10.25.0.0/16", "server_count": 450, "app_count": 35},
    {"name": "DC Lynhaven", "code": "DC_LYNHAVEN", "location": "Virginia Beach, VA", "status": "Decommissioning",
     "description": "Legacy DC - migration to East NGDC", "ip_range": "10.26.0.0/16", "server_count": 320, "app_count": 22},
    {"name": "DC Richardson", "code": "DC_RICHARDSON", "location": "Richardson, TX", "status": "Active",
     "description": "Legacy DC - partial migration in progress", "ip_range": "10.27.0.0/16", "server_count": 580, "app_count": 41},
    {"name": "DC Sterling", "code": "DC_STERLING", "location": "Sterling, VA", "status": "Active",
     "description": "Legacy DC - migration planned", "ip_range": "10.28.0.0/16", "server_count": 410, "app_count": 29},
    {"name": "DC Glen Bornie", "code": "DC_GLEN_BORNIE", "location": "Glen Burnie, MD", "status": "Decommissioning",
     "description": "Legacy DC - final migration wave", "ip_range": "10.29.0.0/16", "server_count": 270, "app_count": 18},
    {"name": "DC Manassas", "code": "DC_MANASSAS", "location": "Manassas, VA", "status": "Active",
     "description": "Legacy DC - migration in planning", "ip_range": "10.30.0.0/16", "server_count": 390, "app_count": 27},
]

SEED_APPLICATIONS = [
    {"app_id": "CRM", "name": "CRM Application", "owner": "Jane Smith", "team": "Customer Platforms",
     "nh": "NH02", "sz": "CDE", "criticality": 2, "pci_scope": True, "description": "CRM system"},
    {"app_id": "ORD", "name": "Ordering System", "owner": "Jon", "team": "Retail Digital",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Online ordering platform"},
    {"app_id": "PSA", "name": "PSA Services", "owner": "Jane Smith", "team": "Enterprise Services",
     "nh": "NH05", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Professional Services Automation"},
    {"app_id": "DIG", "name": "Digital Banking", "owner": "Jon", "team": "Digital Channels",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Digital banking platforms"},
    {"app_id": "PAY", "name": "Core Payments", "owner": "Jane Smith", "team": "Global Payments",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Core payment engine"},
    {"app_id": "ENT", "name": "Enterprise CRM", "owner": "Jon", "team": "Enterprise Services",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Internal enterprise CRM"},
    {"app_id": "SHR", "name": "Shared Analytics", "owner": "Jane Smith", "team": "Data and Analytics",
     "nh": "NH08", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Analytics platform"},
    {"app_id": "WHL", "name": "Wholesale Banking", "owner": "Jon", "team": "Wholesale Banking",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Wholesale banking"},
    {"app_id": "CBK", "name": "Core Banking", "owner": "Jane Smith", "team": "Core Banking",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Core banking ledger"},
    {"app_id": "CLN", "name": "Consumer Lending", "owner": "Jon", "team": "Consumer Lending",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Lending origination"},
    {"app_id": "WLT", "name": "Wealth Platform", "owner": "Jane Smith", "team": "Wealth Management",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Wealth advisory"},
    {"app_id": "ACH", "name": "Assisted Channels", "owner": "Jon", "team": "Assisted Channels",
     "nh": "NH09", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Branch and call center apps"},
]

SEED_ENVIRONMENTS = [
    {"name": "Production", "code": "PROD", "description": "Live production environment"},
    {"name": "Non-Production", "code": "NON-PROD", "description": "Shared non-production for testing"},
    {"name": "Pre-Production", "code": "PRE-PROD", "description": "Staging environment"},
    {"name": "Development", "code": "DEV", "description": "Development and sandbox"},
    {"name": "Staging", "code": "STG", "description": "Final validation before production"},
    {"name": "DR", "code": "DR", "description": "Disaster recovery"},
]

SEED_PREDEFINED_DESTINATIONS = [
    {"name": "grp-DIG-NH03-CDE-WEB", "security_zone": "CDE", "description": "Digital Channels Web Servers",
     "friendly_name": "DIGITAL CHANNELS - PROD", "ip": "10.2.1.0/24", "port": "TCP 8443", "nh": "NH03"},
    {"name": "grp-ENT-NH05-GEN-APP", "security_zone": "GEN", "description": "Enterprise Services App Servers",
     "friendly_name": "ENTERPRISE SERVICES", "ip": "10.4.1.0/24", "port": "TCP 8443", "nh": "NH05"},
    {"name": "grp-SHR-NH13-GEN-SVC", "security_zone": "GEN", "description": "Shared Platform Services",
     "friendly_name": "SHARED PLATFORMS", "ip": "10.100.1.0/24", "port": "TCP 8080", "nh": "NH13"},
    {"name": "grp-EXT-NH14-DMZ-API", "security_zone": "DMZ", "description": "External Partner API Gateway",
     "friendly_name": "EXTERNAL PARTNERS", "ip": "10.70.2.0/24", "port": "TCP 443", "nh": "NH14"},
    {"name": "grp-CBK-NH02-CDE-DB", "security_zone": "CDE", "description": "Core Banking DB Cluster",
     "friendly_name": "CORE DATABASE", "ip": "10.50.1.0/24", "port": "TCP 1521", "nh": "NH02"},
    {"name": "grp-PAY-NH07-CDE-DB", "security_zone": "CDE", "description": "Global Payments Database",
     "friendly_name": "PAYMENTS DATABASE", "ip": "10.6.2.0/24", "port": "TCP 1521", "nh": "NH07"},
    {"name": "grp-DMZ-NH14-DMZ-WEB", "security_zone": "DMZ", "description": "DMZ Web Services",
     "friendly_name": "DMZ WEB SERVICES", "ip": "10.70.1.0/24", "port": "TCP 443", "nh": "NH14"},
    {"name": "grp-MGT-NH01-MGT-MON", "security_zone": "MGT", "description": "Management & Monitoring",
     "friendly_name": "MANAGEMENT PLANE", "ip": "10.200.1.0/24", "port": "TCP 8443", "nh": "NH01"},
    {"name": "grp-WHL-NH06-CDE-APP", "security_zone": "CDE", "description": "Wholesale Banking App Servers",
     "friendly_name": "WHOLESALE BANKING", "ip": "10.5.1.0/24", "port": "TCP 8443", "nh": "NH06"},
    {"name": "grp-DAT-NH08-GEN-APP", "security_zone": "GEN", "description": "Data & Analytics App Servers",
     "friendly_name": "DATA & ANALYTICS", "ip": "10.7.1.0/24", "port": "TCP 8443", "nh": "NH08"},
]

SEED_NAMING_STANDARDS = {
    "org_name": "Network Firewall Studio",
    "prefixes": {
        "grp": {"description": "Group (collection of servers)", "pattern": "grp-{AppID}-{NH}-{SZ}-{Subtype}"},
        "svr": {"description": "Individual server/IP", "pattern": "svr-{AppID}-{NH}-{SZ}-{ServerName}"},
        "rng": {"description": "Subnet/IP range", "pattern": "rng-{AppID}-{NH}-{SZ}-{Descriptor}"},
    },
    "subtypes": {
        "APP": "Application Servers", "WEB": "Web Servers", "DB": "Database Servers",
        "BAT": "Batch Servers", "MQ": "Message Queue", "API": "API Servers",
        "LB": "Load Balancers", "MON": "Monitoring", "MFR": "Mainframe", "SVC": "Services",
    },
    "enforcement_rules": [
        "All firewall rules MUST be group-to-group by default",
        "Non-group rules require security exception approval",
        "All names must follow naming convention with valid NH, SZ, and Subtype",
        "Legacy names must be migrated to standards-compliant names",
    ],
}

SEED_POLICY_MATRIX = [
    {"source_zone": "DMZ", "dest_zone": "RST", "action": "Blocked", "reason": "DMZ to Restricted is denied"},
    {"source_zone": "EXT", "dest_zone": "RST", "action": "Blocked", "reason": "External to Restricted is denied"},
    {"source_zone": "EXT", "dest_zone": "CDE", "action": "Blocked", "reason": "External to CDE is denied"},
    {"source_zone": "DMZ", "dest_zone": "CDE", "action": "Blocked", "reason": "DMZ to CDE is denied"},
    {"source_zone": "GEN", "dest_zone": "RST", "action": "Exception Required", "reason": "GEN to Restricted requires exception"},
    {"source_zone": "GEN", "dest_zone": "CDE", "action": "Exception Required", "reason": "GEN to CDE requires exception"},
    {"source_zone": "DMZ", "dest_zone": "GEN", "action": "Exception Required", "reason": "DMZ to GEN requires exception"},
    {"source_zone": "CDE", "dest_zone": "CDE", "action": "Permitted", "reason": "Same zone traffic permitted"},
    {"source_zone": "GEN", "dest_zone": "GEN", "action": "Permitted", "reason": "Same zone traffic permitted"},
    {"source_zone": "DMZ", "dest_zone": "DMZ", "action": "Permitted", "reason": "Same zone traffic permitted"},
    {"source_zone": "CDE", "dest_zone": "GEN", "action": "Permitted", "reason": "CDE to GEN is permitted"},
    {"source_zone": "RST", "dest_zone": "CDE", "action": "Permitted", "reason": "Restricted to CDE is permitted"},
]

SEED_ORG_CONFIG = {
    "org_name": "Enterprise Financial Services",
    "org_code": "EFS",
    "servicenow_instance": "https://efs.service-now.com",
    "servicenow_api_path": "/api/now/table/change_request",
    "gitops_repo": "https://github.com/efs-network/firewall-policies.git",
    "gitops_branch": "main",
    "approval_workflow": "two-tier",
    "auto_certify_days": 365,
    "max_rule_expiry_days": 730,
    "notification_email": "firewall-ops@company.com",
    "notification_slack_channel": "#firewall-changes",
    "default_environment": "Production",
    "default_datacenter": "EAST_NGDC",
    "rule_id_prefix": "R-",
    "rule_id_start": 3000,
    "migration_id_prefix": "mig-",
    "chg_id_prefix": "CHG",
    "chg_id_start": 10000,
}

# Sample firewall rules
SEED_FIREWALL_RULES: list[dict[str, Any]] = []
_base_time = datetime.utcnow()
_rule_defs = [
    ("R-3001", "grp-CRM-NH02-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
     "CRM to Core Banking DB", "CRM", "Deployed", True, -30),
    ("R-3002", "grp-DIG-NH03-CDE-WEB", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
     "Digital Channels to Payments", "DIG", "Certified", True, -15),
    ("R-3003", "grp-ENT-NH05-GEN-APP", "GEN", "grp-SHR-NH13-GEN-SVC", "GEN", "TCP 8080",
     "Enterprise to Shared Services", "ENT", "Pending Review", True, -5),
    ("R-3004", "grp-WHL-NH06-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
     "Wholesale to Core Banking DB", "WHL", "Draft", True, -1),
    ("R-3005", "grp-PAY-NH07-CDE-APP", "CDE", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
     "Payments to External API", "PAY", "Certified", False, -20),
    ("R-3006", "grp-DAT-NH08-GEN-APP", "GEN", "grp-ENT-NH05-GEN-APP", "GEN", "TCP 8443",
     "Analytics to Enterprise", "SHR", "Deployed", True, -45),
]
for _rid, _src, _sz_s, _dst, _sz_d, _port, _desc, _app, _st, _g2g, _days in _rule_defs:
    _ct = (_base_time + timedelta(days=_days)).isoformat()
    SEED_FIREWALL_RULES.append({
        "rule_id": _rid, "source": _src, "source_zone": _sz_s, "destination": _dst,
        "destination_zone": _sz_d, "port": _port, "protocol": _port.split(" ")[0],
        "action": "Allow", "description": _desc, "application": _app, "status": _st,
        "is_group_to_group": _g2g, "environment": "Production", "datacenter": "EAST_NGDC",
        "created_at": _ct, "updated_at": _ct,
        "certified_date": _ct if _st in ("Certified", "Deployed") else None,
        "expiry_date": (_base_time + timedelta(days=365)).isoformat() if _st in ("Certified", "Deployed") else None,
    })

SEED_MIGRATIONS = [
    {"migration_id": "mig-001", "name": "DC Garland to Central NGDC Wave 1",
     "legacy_dc": "DC_GARLAND", "target_dc": "CENTRAL_NGDC",
     "status": "In Progress", "progress": 35,
     "total_rules": 45, "migrated_rules": 16, "failed_rules": 2,
     "created_at": (_base_time + timedelta(days=-60)).isoformat(), "updated_at": _now()},
]

SEED_MIGRATION_MAPPINGS = [
    {"mapping_id": "map-001", "migration_id": "mig-001",
     "legacy_rule": "permit tcp 10.25.1.0/24 10.25.2.0/24 eq 1521",
     "legacy_source": "10.25.1.0/24", "legacy_destination": "10.25.2.0/24",
     "legacy_port": "TCP 1521", "legacy_action": "permit",
     "ngdc_source": "grp-CBK-NH02-CDE-APP", "ngdc_destination": "grp-CBK-NH02-CDE-DB",
     "ngdc_port": "TCP 1521", "ngdc_action": "Allow",
     "source_nh": "NH02", "source_sz": "CDE", "dest_nh": "NH02", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-002", "migration_id": "mig-001",
     "legacy_rule": "permit tcp 10.25.3.0/24 10.25.4.0/24 eq 8443",
     "legacy_source": "10.25.3.0/24", "legacy_destination": "10.25.4.0/24",
     "legacy_port": "TCP 8443", "legacy_action": "permit",
     "ngdc_source": "grp-PAY-NH07-CDE-APP", "ngdc_destination": "grp-PAY-NH07-CDE-DB",
     "ngdc_port": "TCP 8443", "ngdc_action": "Allow",
     "source_nh": "NH07", "source_sz": "CDE", "dest_nh": "NH07", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-003", "migration_id": "mig-001",
     "legacy_rule": "permit ip any any",
     "legacy_source": "any", "legacy_destination": "any",
     "legacy_port": "ANY", "legacy_action": "permit",
     "ngdc_source": "", "ngdc_destination": "", "ngdc_port": "", "ngdc_action": "",
     "source_nh": "", "source_sz": "", "dest_nh": "", "dest_sz": "",
     "status": "Review Required", "compliance": "Non-Compliant"},
]

SEED_CHG_REQUESTS = [
    {"chg_id": "CHG10001", "rule_ids": ["R-3001"], "status": "Approved",
     "description": "Deploy CRM to Core Banking DB rule",
     "requested_by": "Jane Smith", "approved_by": "Security Team",
     "created_at": (_base_time + timedelta(days=-31)).isoformat(),
     "updated_at": (_base_time + timedelta(days=-30)).isoformat()},
]


# ============================================================
# Seed Function
# ============================================================

async def seed_database() -> None:
    """Seed MongoDB with initial data if collections are empty."""
    db = get_db()
    count = await db[COLLECTIONS["neighbourhoods"]].count_documents({})
    if count > 0:
        return

    await db[COLLECTIONS["neighbourhoods"]].insert_many([dict(n) for n in SEED_NEIGHBOURHOODS])
    await db[COLLECTIONS["security_zones"]].insert_many([dict(s) for s in SEED_SECURITY_ZONES])
    await db[COLLECTIONS["ngdc_datacenters"]].insert_many([dict(d) for d in SEED_NGDC_DATACENTERS])
    await db[COLLECTIONS["legacy_datacenters"]].insert_many([dict(d) for d in SEED_LEGACY_DATACENTERS])
    await db[COLLECTIONS["applications"]].insert_many([dict(a) for a in SEED_APPLICATIONS])
    await db[COLLECTIONS["environments"]].insert_many([dict(e) for e in SEED_ENVIRONMENTS])
    await db[COLLECTIONS["predefined_destinations"]].insert_many([dict(p) for p in SEED_PREDEFINED_DESTINATIONS])
    await db[COLLECTIONS["naming_standards"]].insert_one(dict(SEED_NAMING_STANDARDS))
    await db[COLLECTIONS["policy_matrix"]].insert_many([dict(p) for p in SEED_POLICY_MATRIX])
    await db[COLLECTIONS["org_config"]].insert_one(dict(SEED_ORG_CONFIG))
    if SEED_FIREWALL_RULES:
        await db[COLLECTIONS["firewall_rules"]].insert_many([dict(r) for r in SEED_FIREWALL_RULES])
    if SEED_MIGRATIONS:
        await db[COLLECTIONS["migrations"]].insert_many([dict(m) for m in SEED_MIGRATIONS])
    if SEED_MIGRATION_MAPPINGS:
        await db[COLLECTIONS["migration_mappings"]].insert_many([dict(m) for m in SEED_MIGRATION_MAPPINGS])
    if SEED_CHG_REQUESTS:
        await db[COLLECTIONS["chg_requests"]].insert_many([dict(c) for c in SEED_CHG_REQUESTS])


# ============================================================
# Read Operations (Reference Data)
# ============================================================

async def get_neighbourhoods() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["neighbourhoods"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_security_zones() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["security_zones"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_ngdc_datacenters() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["ngdc_datacenters"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_legacy_datacenters() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["legacy_datacenters"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_applications() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["applications"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_environments() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["environments"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_predefined_destinations() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["predefined_destinations"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_naming_standards() -> dict[str, Any] | None:
    db = get_db()
    doc = await db[COLLECTIONS["naming_standards"]].find_one()
    return _strip_mongo_id(doc)


async def get_policy_matrix() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["policy_matrix"]].find().to_list(length=200)
    return _strip_many(docs)


async def get_org_config() -> dict[str, Any] | None:
    db = get_db()
    doc = await db[COLLECTIONS["org_config"]].find_one()
    return _strip_mongo_id(doc)


# ============================================================
# Firewall Rules CRUD
# ============================================================

async def get_rules() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["firewall_rules"]].find().to_list(length=1000)
    return _strip_many(docs)


async def get_rule(rule_id: str) -> dict[str, Any] | None:
    db = get_db()
    doc = await db[COLLECTIONS["firewall_rules"]].find_one({"rule_id": rule_id})
    return _strip_mongo_id(doc)


async def create_rule(rule_data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    now = _now()
    config = await get_org_config() or SEED_ORG_CONFIG
    last = await db[COLLECTIONS["firewall_rules"]].find_one(sort=[("rule_id", -1)])
    if last and last.get("rule_id", "").startswith(config.get("rule_id_prefix", "R-")):
        try:
            num = int(last["rule_id"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = config.get("rule_id_start", 3000)
    else:
        num = config.get("rule_id_start", 3000)
    rule_id = f"{config.get('rule_id_prefix', 'R-')}{num}"
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
        "datacenter": rule_data.get("datacenter", "EAST_NGDC"),
        "created_at": now,
        "updated_at": now,
        "certified_date": None,
        "expiry_date": None,
    }
    await db[COLLECTIONS["firewall_rules"]].insert_one(dict(rule))
    await db[COLLECTIONS["rule_history"]].insert_one({
        "rule_id": rule_id, "action": "Created", "timestamp": now,
        "details": f"Rule created: {rule['description']}", "user": "system",
    })
    return rule


async def update_rule(rule_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    updates["updated_at"] = _now()
    await db[COLLECTIONS["firewall_rules"]].update_one({"rule_id": rule_id}, {"$set": updates})
    doc = await db[COLLECTIONS["firewall_rules"]].find_one({"rule_id": rule_id})
    return _strip_mongo_id(doc)


async def update_rule_status(rule_id: str, new_status: str) -> dict[str, Any] | None:
    db = get_db()
    now = _now()
    update_fields: dict[str, Any] = {"status": new_status, "updated_at": now}
    if new_status == "Certified":
        update_fields["certified_date"] = now
        config = await get_org_config() or SEED_ORG_CONFIG
        expiry_days = config.get("auto_certify_days", 365)
        update_fields["expiry_date"] = (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
    await db[COLLECTIONS["firewall_rules"]].update_one({"rule_id": rule_id}, {"$set": update_fields})
    await db[COLLECTIONS["rule_history"]].insert_one({
        "rule_id": rule_id, "action": f"Status changed to {new_status}",
        "timestamp": now, "details": f"Status updated to {new_status}", "user": "system",
    })
    return await get_rule(rule_id)


async def delete_rule(rule_id: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["firewall_rules"]].delete_one({"rule_id": rule_id})
    return result.deleted_count > 0


async def get_rule_history(rule_id: str) -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["rule_history"]].find({"rule_id": rule_id}).to_list(length=500)
    return _strip_many(docs)


# ============================================================
# Migrations CRUD
# ============================================================

async def get_migrations() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["migrations"]].find().to_list(length=100)
    return _strip_many(docs)


async def get_migration(migration_id: str) -> dict[str, Any] | None:
    db = get_db()
    doc = await db[COLLECTIONS["migrations"]].find_one({"migration_id": migration_id})
    return _strip_mongo_id(doc)


async def create_migration(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    now = _now()
    config = await get_org_config() or SEED_ORG_CONFIG
    migration_id = f"{config.get('migration_id_prefix', 'mig-')}{_id()}"
    migration = {
        "migration_id": migration_id,
        "name": data.get("name", ""),
        "legacy_dc": data.get("legacy_dc", ""),
        "target_dc": data.get("target_dc", ""),
        "status": "Planning",
        "progress": 0,
        "total_rules": data.get("total_rules", 0),
        "migrated_rules": 0,
        "failed_rules": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db[COLLECTIONS["migrations"]].insert_one(dict(migration))
    return migration


async def get_migration_mappings(migration_id: str) -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["migration_mappings"]].find({"migration_id": migration_id}).to_list(length=1000)
    return _strip_many(docs)


async def create_migration_mapping(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    mapping = dict(data)
    mapping["mapping_id"] = f"map-{_id()}"
    await db[COLLECTIONS["migration_mappings"]].insert_one(dict(mapping))
    return mapping


async def execute_migration(migration_id: str) -> dict[str, Any] | None:
    db = get_db()
    now = _now()
    mappings = await get_migration_mappings(migration_id)
    compliant = sum(1 for m in mappings if m.get("compliance") == "Compliant")
    total = len(mappings)
    progress = int((compliant / total) * 100) if total > 0 else 0
    await db[COLLECTIONS["migrations"]].update_one(
        {"migration_id": migration_id},
        {"$set": {"status": "In Progress", "progress": progress, "migrated_rules": compliant,
                  "total_rules": total, "updated_at": now}})
    return await get_migration(migration_id)


# ============================================================
# CHG Requests
# ============================================================

async def get_chg_requests() -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COLLECTIONS["chg_requests"]].find().to_list(length=500)
    return _strip_many(docs)


async def create_chg_request(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    now = _now()
    config = await get_org_config() or SEED_ORG_CONFIG
    last = await db[COLLECTIONS["chg_requests"]].find_one(sort=[("chg_id", -1)])
    if last and last.get("chg_id", "").startswith(config.get("chg_id_prefix", "CHG")):
        try:
            num = int(last["chg_id"].replace(config.get("chg_id_prefix", "CHG"), "")) + 1
        except (ValueError, IndexError):
            num = config.get("chg_id_start", 10000)
    else:
        num = config.get("chg_id_start", 10000)
    chg = {
        "chg_id": f"{config.get('chg_id_prefix', 'CHG')}{num}",
        "rule_ids": data.get("rule_ids", []),
        "status": "Submitted",
        "description": data.get("description", ""),
        "requested_by": data.get("requested_by", "system"),
        "approved_by": None,
        "created_at": now,
        "updated_at": now,
    }
    await db[COLLECTIONS["chg_requests"]].insert_one(dict(chg))
    return chg


# ============================================================
# Policy Validation
# ============================================================

async def validate_policy(source_zone: str, dest_zone: str) -> dict[str, Any]:
    db = get_db()
    policy = await db[COLLECTIONS["policy_matrix"]].find_one(
        {"source_zone": source_zone, "dest_zone": dest_zone})
    if policy:
        return {"allowed": policy["action"] == "Permitted",
                "action": policy["action"], "reason": policy["reason"]}
    return {"allowed": True, "action": "Permitted", "reason": "No explicit policy restriction found"}


# ============================================================
# Org Customization CRUD
# ============================================================

async def update_org_config(updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["org_config"]].update_one({}, {"$set": updates}, upsert=True)
    return await get_org_config()


async def create_neighbourhood(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["neighbourhoods"]].insert_one(dict(data))
    return data


async def update_neighbourhood(nh_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["neighbourhoods"]].update_one({"nh_id": nh_id}, {"$set": updates})
    doc = await db[COLLECTIONS["neighbourhoods"]].find_one({"nh_id": nh_id})
    return _strip_mongo_id(doc)


async def delete_neighbourhood(nh_id: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["neighbourhoods"]].delete_one({"nh_id": nh_id})
    return result.deleted_count > 0


async def create_security_zone(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["security_zones"]].insert_one(dict(data))
    return data


async def update_security_zone(code: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["security_zones"]].update_one({"code": code}, {"$set": updates})
    doc = await db[COLLECTIONS["security_zones"]].find_one({"code": code})
    return _strip_mongo_id(doc)


async def delete_security_zone(code: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["security_zones"]].delete_one({"code": code})
    return result.deleted_count > 0


async def create_application(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["applications"]].insert_one(dict(data))
    return data


async def update_application(app_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["applications"]].update_one({"app_id": app_id}, {"$set": updates})
    doc = await db[COLLECTIONS["applications"]].find_one({"app_id": app_id})
    return _strip_mongo_id(doc)


async def delete_application(app_id: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["applications"]].delete_one({"app_id": app_id})
    return result.deleted_count > 0


async def create_datacenter(data: dict[str, Any], dc_type: str = "ngdc") -> dict[str, Any]:
    db = get_db()
    coll = COLLECTIONS["ngdc_datacenters"] if dc_type == "ngdc" else COLLECTIONS["legacy_datacenters"]
    await db[coll].insert_one(dict(data))
    return data


async def update_datacenter(code: str, updates: dict[str, Any], dc_type: str = "ngdc") -> dict[str, Any] | None:
    db = get_db()
    coll = COLLECTIONS["ngdc_datacenters"] if dc_type == "ngdc" else COLLECTIONS["legacy_datacenters"]
    await db[coll].update_one({"code": code}, {"$set": updates})
    doc = await db[coll].find_one({"code": code})
    return _strip_mongo_id(doc)


async def delete_datacenter(code: str, dc_type: str = "ngdc") -> bool:
    db = get_db()
    coll = COLLECTIONS["ngdc_datacenters"] if dc_type == "ngdc" else COLLECTIONS["legacy_datacenters"]
    result = await db[coll].delete_one({"code": code})
    return result.deleted_count > 0


async def update_naming_standards(updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["naming_standards"]].update_one({}, {"$set": updates}, upsert=True)
    return await get_naming_standards()


async def create_policy_entry(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["policy_matrix"]].insert_one(dict(data))
    return data


async def delete_policy_entry(source_zone: str, dest_zone: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["policy_matrix"]].delete_one(
        {"source_zone": source_zone, "dest_zone": dest_zone})
    return result.deleted_count > 0


async def create_predefined_destination(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["predefined_destinations"]].insert_one(dict(data))
    return data


async def update_predefined_destination(name: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    db = get_db()
    await db[COLLECTIONS["predefined_destinations"]].update_one({"name": name}, {"$set": updates})
    doc = await db[COLLECTIONS["predefined_destinations"]].find_one({"name": name})
    return _strip_mongo_id(doc)


async def delete_predefined_destination(name: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["predefined_destinations"]].delete_one({"name": name})
    return result.deleted_count > 0


async def create_environment(data: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    await db[COLLECTIONS["environments"]].insert_one(dict(data))
    return data


async def delete_environment(code: str) -> bool:
    db = get_db()
    result = await db[COLLECTIONS["environments"]].delete_one({"code": code})
    return result.deleted_count > 0
