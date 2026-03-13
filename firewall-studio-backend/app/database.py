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

DATA_DIR = Path(__file__).parent.parent / "data"


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.utcnow().isoformat()


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> Any:
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save(name: str, data: Any) -> None:
    _ensure_dir()
    path = DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


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
    # --- 15 additional applications ---
    {"app_id": "HRM", "name": "HR Management", "owner": "Alice Carter", "team": "Human Resources",
     "nh": "NH01", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "HR and payroll management system"},
    {"app_id": "TRD", "name": "Trading Platform", "owner": "Bob Martinez", "team": "Capital Markets",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Equities and fixed-income trading"},
    {"app_id": "FRD", "name": "Fraud Detection", "owner": "Carol Liu", "team": "Risk Management",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Real-time fraud detection and prevention"},
    {"app_id": "RGM", "name": "Regulatory Compliance", "owner": "Dan Okafor", "team": "Compliance",
     "nh": "NH11", "sz": "RST", "criticality": 1, "pci_scope": True, "description": "Regulatory reporting and compliance engine"},
    {"app_id": "MBL", "name": "Mobile Banking", "owner": "Eva Chen", "team": "Digital Channels",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "iOS and Android mobile banking app"},
    {"app_id": "INS", "name": "Insurance Platform", "owner": "Frank Nguyen", "team": "Wealth Management",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Insurance underwriting and claims"},
    {"app_id": "TAX", "name": "Tax Processing", "owner": "Grace Park", "team": "Finance Operations",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Tax calculation and filing system"},
    {"app_id": "AML", "name": "Anti Money Laundering", "owner": "Hector Ruiz", "team": "Risk Management",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "AML screening and suspicious activity reporting"},
    {"app_id": "KYC", "name": "Know Your Customer", "owner": "Irene Walsh", "team": "Compliance",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Customer identity verification and due diligence"},
    {"app_id": "TRS", "name": "Treasury Services", "owner": "Jack Thompson", "team": "Treasury",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Cash management and liquidity"},
    {"app_id": "CCM", "name": "Credit Card Management", "owner": "Karen Davis", "team": "Card Services",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Credit card issuance and transaction processing"},
    {"app_id": "LON", "name": "Loan Origination", "owner": "Leo Kim", "team": "Consumer Lending",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Loan application and underwriting"},
    {"app_id": "BRK", "name": "Brokerage Services", "owner": "Maria Santos", "team": "Wealth Management",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Stock and bond brokerage platform"},
    {"app_id": "AGW", "name": "API Gateway", "owner": "Naveen Patel", "team": "Platform Engineering",
     "nh": "NH14", "sz": "DMZ", "criticality": 1, "pci_scope": False, "description": "External-facing API gateway and rate limiting"},
    {"app_id": "SOC", "name": "Security Operations Center", "owner": "Olivia Brown", "team": "Cybersecurity",
     "nh": "NH01", "sz": "GEN", "criticality": 1, "pci_scope": False, "description": "SIEM, threat monitoring, incident response"},
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


def _build_seed_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    base = datetime.utcnow()
    defs = [
        # --- Original 7 rules ---
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
        ("R-3007", "192.168.1.10", "GEN", "grp-SHR-NH13-GEN-SVC", "GEN", "TCP 8443",
         "Single IP to Shared Services", "SHR", "Pending Review", False, -2),
        # --- HRM (HR Management) rules ---
        ("R-3008", "grp-HRM-NH01-GEN-WEB", "GEN", "grp-HRM-NH01-GEN-APP", "GEN", "TCP 8443",
         "HR Portal Web to App Tier", "HRM", "Deployed", True, -90),
        ("R-3009", "grp-HRM-NH01-GEN-APP", "GEN", "grp-HRM-NH01-GEN-DB", "GEN", "TCP 5432",
         "HR App to HR Database", "HRM", "Deployed", True, -90),
        ("R-3010", "grp-HRM-NH01-GEN-BAT", "GEN", "grp-HRM-NH01-GEN-DB", "GEN", "TCP 5432",
         "HR Payroll Batch to DB", "HRM", "Certified", True, -60),
        # --- TRD (Trading Platform) rules ---
        ("R-3011", "grp-TRD-NH06-CDE-WEB", "CDE", "grp-TRD-NH06-CDE-APP", "CDE", "TCP 8443",
         "Trading Web to App Tier", "TRD", "Deployed", True, -120),
        ("R-3012", "grp-TRD-NH06-CDE-APP", "CDE", "grp-TRD-NH06-CDE-DB", "CDE", "TCP 1521",
         "Trading App to Oracle DB", "TRD", "Deployed", True, -120),
        ("R-3013", "grp-TRD-NH06-CDE-APP", "CDE", "grp-TRD-NH06-CDE-MQ", "CDE", "TCP 1414",
         "Trading App to MQ Broker", "TRD", "Certified", True, -80),
        ("R-3014", "grp-TRD-NH06-CDE-APP", "CDE", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "Trading to Market Data Feed", "TRD", "Certified", False, -50),
        # --- FRD (Fraud Detection) rules ---
        ("R-3015", "grp-FRD-NH02-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "Fraud Engine to Core Banking DB", "FRD", "Deployed", True, -100),
        ("R-3016", "grp-FRD-NH02-CDE-APP", "CDE", "grp-CCM-NH02-CDE-DB", "CDE", "TCP 1521",
         "Fraud Engine to Credit Card DB", "FRD", "Deployed", True, -100),
        ("R-3017", "grp-FRD-NH02-CDE-APP", "CDE", "grp-AML-NH07-CDE-APP", "CDE", "TCP 8443",
         "Fraud to AML Integration", "FRD", "Certified", True, -40),
        # --- RGM (Regulatory Compliance) rules ---
        ("R-3018", "grp-RGM-NH11-RST-APP", "RST", "grp-RGM-NH11-RST-DB", "RST", "TCP 1521",
         "Regulatory App to Compliance DB", "RGM", "Deployed", True, -150),
        ("R-3019", "grp-RGM-NH11-RST-BAT", "RST", "grp-RGM-NH11-RST-DB", "RST", "TCP 1521",
         "Regulatory Batch Reporting to DB", "RGM", "Certified", True, -75),
        # --- MBL (Mobile Banking) rules ---
        ("R-3020", "grp-MBL-NH03-CDE-API", "CDE", "grp-MBL-NH03-CDE-APP", "CDE", "TCP 8443",
         "Mobile API Gateway to App", "MBL", "Deployed", True, -200),
        ("R-3021", "grp-MBL-NH03-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "Mobile App to Core Banking", "MBL", "Deployed", True, -200),
        ("R-3022", "grp-MBL-NH03-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "Mobile to Payments", "MBL", "Certified", True, -100),
        ("R-3023", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-MBL-NH03-CDE-API", "CDE", "TCP 8443",
         "API Gateway to Mobile Backend", "MBL", "Pending Review", False, -3),
        # --- INS (Insurance Platform) rules ---
        ("R-3024", "grp-INS-NH04-GEN-WEB", "GEN", "grp-INS-NH04-GEN-APP", "GEN", "TCP 8443",
         "Insurance Portal to App Tier", "INS", "Deployed", True, -85),
        ("R-3025", "grp-INS-NH04-GEN-APP", "GEN", "grp-INS-NH04-GEN-DB", "GEN", "TCP 5432",
         "Insurance App to Claims DB", "INS", "Deployed", True, -85),
        # --- TAX (Tax Processing) rules ---
        ("R-3026", "grp-TAX-NH10-GEN-APP", "GEN", "grp-TAX-NH10-GEN-DB", "GEN", "TCP 5432",
         "Tax Engine to Tax DB", "TAX", "Certified", True, -55),
        ("R-3027", "grp-TAX-NH10-GEN-BAT", "GEN", "grp-TAX-NH10-GEN-DB", "GEN", "TCP 5432",
         "Tax Batch Processing to DB", "TAX", "Deployed", True, -110),
        # --- AML (Anti Money Laundering) rules ---
        ("R-3028", "grp-AML-NH07-CDE-APP", "CDE", "grp-AML-NH07-CDE-DB", "CDE", "TCP 1521",
         "AML Engine to Screening DB", "AML", "Deployed", True, -130),
        ("R-3029", "grp-AML-NH07-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "AML to Payments for Transaction Monitoring", "AML", "Certified", True, -60),
        ("R-3030", "grp-AML-NH07-CDE-BAT", "CDE", "grp-RGM-NH11-RST-APP", "RST", "TCP 8443",
         "AML Batch to Regulatory Reporting", "AML", "Pending Review", False, -7),
        # --- KYC (Know Your Customer) rules ---
        ("R-3031", "grp-KYC-NH05-GEN-WEB", "GEN", "grp-KYC-NH05-GEN-APP", "GEN", "TCP 8443",
         "KYC Portal to Verification Engine", "KYC", "Deployed", True, -95),
        ("R-3032", "grp-KYC-NH05-GEN-APP", "GEN", "grp-KYC-NH05-GEN-DB", "GEN", "TCP 5432",
         "KYC Engine to Customer DB", "KYC", "Deployed", True, -95),
        ("R-3033", "grp-KYC-NH05-GEN-APP", "GEN", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "KYC to External ID Verification API", "KYC", "Certified", False, -30),
        # --- TRS (Treasury Services) rules ---
        ("R-3034", "grp-TRS-NH06-CDE-APP", "CDE", "grp-TRS-NH06-CDE-DB", "CDE", "TCP 1521",
         "Treasury App to Cash Mgmt DB", "TRS", "Deployed", True, -140),
        ("R-3035", "grp-TRS-NH06-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "Treasury to Core Banking Ledger", "TRS", "Deployed", True, -140),
        ("R-3036", "grp-TRS-NH06-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "Treasury to Payments for Wire Transfers", "TRS", "Certified", True, -45),
        # --- CCM (Credit Card Management) rules ---
        ("R-3037", "grp-CCM-NH02-CDE-WEB", "CDE", "grp-CCM-NH02-CDE-APP", "CDE", "TCP 8443",
         "Card Portal to Card Mgmt App", "CCM", "Deployed", True, -180),
        ("R-3038", "grp-CCM-NH02-CDE-APP", "CDE", "grp-CCM-NH02-CDE-DB", "CDE", "TCP 1521",
         "Card App to Card Transaction DB", "CCM", "Deployed", True, -180),
        ("R-3039", "grp-CCM-NH02-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "Card Mgmt to Payment Authorization", "CCM", "Certified", True, -70),
        ("R-3040", "grp-CCM-NH02-CDE-APP", "CDE", "grp-FRD-NH02-CDE-APP", "CDE", "TCP 8443",
         "Card Transactions to Fraud Scoring", "CCM", "Deployed", True, -160),
        # --- LON (Loan Origination) rules ---
        ("R-3041", "grp-LON-NH10-GEN-WEB", "GEN", "grp-LON-NH10-GEN-APP", "GEN", "TCP 8443",
         "Loan Portal to Origination Engine", "LON", "Deployed", True, -110),
        ("R-3042", "grp-LON-NH10-GEN-APP", "GEN", "grp-LON-NH10-GEN-DB", "GEN", "TCP 5432",
         "Loan Origination to Loan DB", "LON", "Deployed", True, -110),
        ("R-3043", "grp-LON-NH10-GEN-APP", "GEN", "grp-KYC-NH05-GEN-APP", "GEN", "TCP 8443",
         "Loan App to KYC Verification", "LON", "Certified", True, -35),
        # --- BRK (Brokerage Services) rules ---
        ("R-3044", "grp-BRK-NH04-GEN-WEB", "GEN", "grp-BRK-NH04-GEN-APP", "GEN", "TCP 8443",
         "Brokerage Portal to Trading Engine", "BRK", "Deployed", True, -160),
        ("R-3045", "grp-BRK-NH04-GEN-APP", "GEN", "grp-BRK-NH04-GEN-DB", "GEN", "TCP 5432",
         "Brokerage App to Portfolio DB", "BRK", "Deployed", True, -160),
        ("R-3046", "grp-BRK-NH04-GEN-APP", "GEN", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "Brokerage to Market Data Feed", "BRK", "Certified", False, -25),
        # --- AGW (API Gateway) rules ---
        ("R-3047", "grp-AGW-NH14-DMZ-LB", "DMZ", "grp-AGW-NH14-DMZ-API", "DMZ", "TCP 443",
         "External LB to API Gateway", "AGW", "Deployed", True, -200),
        ("R-3048", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-DIG-NH03-CDE-WEB", "CDE", "TCP 8443",
         "API GW to Digital Banking Backend", "AGW", "Deployed", False, -200),
        ("R-3049", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-AGW-NH14-DMZ-MON", "DMZ", "TCP 9090",
         "API GW to Monitoring", "AGW", "Certified", True, -50),
        # --- SOC (Security Operations Center) rules ---
        ("R-3050", "grp-SOC-NH01-GEN-APP", "GEN", "grp-SOC-NH01-GEN-DB", "GEN", "TCP 9200",
         "SIEM Collector to Elasticsearch", "SOC", "Deployed", True, -250),
        ("R-3051", "grp-SOC-NH01-GEN-MON", "GEN", "grp-MGT-NH01-MGT-MON", "MGT", "TCP 8443",
         "SOC Monitoring to Management Plane", "SOC", "Deployed", False, -250),
        ("R-3052", "grp-SOC-NH01-GEN-APP", "GEN", "grp-SOC-NH01-GEN-APP", "GEN", "TCP 514",
         "Syslog Aggregation within SOC", "SOC", "Certified", True, -120),
        # --- Legacy non-standard rules for migration ---
        ("R-3053", "10.25.10.0/24", "CDE", "10.25.20.0/24", "CDE", "TCP 1521",
         "Legacy Garland DB Traffic", "CRM", "Deployed", False, -365),
        ("R-3054", "10.26.5.0/24", "GEN", "10.26.15.0/24", "GEN", "TCP 8443",
         "Legacy Lynhaven App Traffic", "HRM", "Deployed", False, -300),
        ("R-3055", "10.27.1.0/24", "CDE", "10.27.2.0/24", "CDE", "TCP 443",
         "Legacy Richardson Web to App", "TRD", "Deployed", False, -280),
        ("R-3056", "10.28.10.0/24", "GEN", "10.28.20.0/24", "GEN", "TCP 5432",
         "Legacy Sterling App to DB", "INS", "Deployed", False, -350),
        ("R-3057", "svr-10.29.1.50", "CDE", "10.29.2.0/24", "CDE", "TCP 1521",
         "Legacy Glen Bornie Single Server", "FRD", "Deployed", False, -400),
        ("R-3058", "10.30.5.0/24", "GEN", "10.30.10.0/24", "GEN", "TCP 8080",
         "Legacy Manassas App Traffic", "KYC", "Deployed", False, -320),
    ]
    for rid, src, sz_s, dst, sz_d, port, desc, app, st, g2g, days in defs:
        ct = (base + timedelta(days=days)).isoformat()
        rules.append({
            "rule_id": rid, "source": src, "source_zone": sz_s, "destination": dst,
            "destination_zone": sz_d, "port": port, "protocol": port.split(" ")[0],
            "action": "Allow", "description": desc, "application": app, "status": st,
            "is_group_to_group": g2g, "environment": "Production", "datacenter": "EAST_NGDC",
            "created_at": ct, "updated_at": ct,
            "certified_date": ct if st in ("Certified", "Deployed") else None,
            "expiry_date": (base + timedelta(days=365)).isoformat() if st in ("Certified", "Deployed") else None,
        })
    return rules


SEED_MIGRATIONS = [
    {"migration_id": "mig-001", "name": "DC Garland to Central NGDC Wave 1",
     "application": "CRM", "source_legacy_dc": "DC_GARLAND", "target_ngdc": "CENTRAL_NGDC",
     "legacy_dc": "DC_GARLAND", "target_dc": "CENTRAL_NGDC",
     "status": "In Progress", "progress": 35,
     "total_rules": 45, "migrated_rules": 16, "failed_rules": 2,
     "created_at": (datetime.utcnow() + timedelta(days=-60)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-002", "name": "DC Lynhaven to East NGDC Wave 1",
     "application": "HRM", "source_legacy_dc": "DC_LYNHAVEN", "target_ngdc": "EAST_NGDC",
     "legacy_dc": "DC_LYNHAVEN", "target_dc": "EAST_NGDC",
     "status": "In Progress", "progress": 60,
     "total_rules": 32, "migrated_rules": 19, "failed_rules": 1,
     "created_at": (datetime.utcnow() + timedelta(days=-45)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-003", "name": "DC Richardson Trading Migration",
     "application": "TRD", "source_legacy_dc": "DC_RICHARDSON", "target_ngdc": "WEST_NGDC",
     "legacy_dc": "DC_RICHARDSON", "target_dc": "WEST_NGDC",
     "status": "Planning", "progress": 10,
     "total_rules": 58, "migrated_rules": 0, "failed_rules": 0,
     "created_at": (datetime.utcnow() + timedelta(days=-15)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-004", "name": "DC Sterling Insurance Migration",
     "application": "INS", "source_legacy_dc": "DC_STERLING", "target_ngdc": "EAST_NGDC",
     "legacy_dc": "DC_STERLING", "target_dc": "EAST_NGDC",
     "status": "In Progress", "progress": 45,
     "total_rules": 28, "migrated_rules": 12, "failed_rules": 3,
     "created_at": (datetime.utcnow() + timedelta(days=-30)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-005", "name": "DC Glen Bornie Fraud Systems",
     "application": "FRD", "source_legacy_dc": "DC_GLEN_BORNIE", "target_ngdc": "EAST_NGDC",
     "legacy_dc": "DC_GLEN_BORNIE", "target_dc": "EAST_NGDC",
     "status": "Completed", "progress": 100,
     "total_rules": 22, "migrated_rules": 22, "failed_rules": 0,
     "created_at": (datetime.utcnow() + timedelta(days=-90)).isoformat(),
     "updated_at": (datetime.utcnow() + timedelta(days=-10)).isoformat()},
    {"migration_id": "mig-006", "name": "DC Manassas KYC Migration",
     "application": "KYC", "source_legacy_dc": "DC_MANASSAS", "target_ngdc": "EAST_NGDC",
     "legacy_dc": "DC_MANASSAS", "target_dc": "EAST_NGDC",
     "status": "In Progress", "progress": 25,
     "total_rules": 38, "migrated_rules": 9, "failed_rules": 1,
     "created_at": (datetime.utcnow() + timedelta(days=-20)).isoformat(),
     "updated_at": _now()},
]

SEED_MIGRATION_MAPPINGS = [
    # --- mig-001: CRM from DC Garland ---
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
    # --- mig-002: HRM from DC Lynhaven ---
    {"mapping_id": "map-004", "migration_id": "mig-002",
     "legacy_rule": "permit tcp 10.26.5.0/24 10.26.15.0/24 eq 8443",
     "legacy_source": "10.26.5.0/24", "legacy_destination": "10.26.15.0/24",
     "legacy_port": "TCP 8443", "legacy_action": "permit",
     "ngdc_source": "grp-HRM-NH01-GEN-WEB", "ngdc_destination": "grp-HRM-NH01-GEN-APP",
     "ngdc_port": "TCP 8443", "ngdc_action": "Allow",
     "source_nh": "NH01", "source_sz": "GEN", "dest_nh": "NH01", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-005", "migration_id": "mig-002",
     "legacy_rule": "permit tcp 10.26.15.0/24 10.26.30.0/24 eq 5432",
     "legacy_source": "10.26.15.0/24", "legacy_destination": "10.26.30.0/24",
     "legacy_port": "TCP 5432", "legacy_action": "permit",
     "ngdc_source": "grp-HRM-NH01-GEN-APP", "ngdc_destination": "grp-HRM-NH01-GEN-DB",
     "ngdc_port": "TCP 5432", "ngdc_action": "Allow",
     "source_nh": "NH01", "source_sz": "GEN", "dest_nh": "NH01", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-006", "migration_id": "mig-002",
     "legacy_rule": "permit tcp 10.26.100.0/24 any eq 22",
     "legacy_source": "10.26.100.0/24", "legacy_destination": "any",
     "legacy_port": "TCP 22", "legacy_action": "permit",
     "ngdc_source": "", "ngdc_destination": "", "ngdc_port": "", "ngdc_action": "",
     "source_nh": "", "source_sz": "", "dest_nh": "", "dest_sz": "",
     "status": "Review Required", "compliance": "Non-Compliant"},
    # --- mig-003: TRD from DC Richardson ---
    {"mapping_id": "map-007", "migration_id": "mig-003",
     "legacy_rule": "permit tcp 10.27.1.0/24 10.27.2.0/24 eq 443",
     "legacy_source": "10.27.1.0/24", "legacy_destination": "10.27.2.0/24",
     "legacy_port": "TCP 443", "legacy_action": "permit",
     "ngdc_source": "grp-TRD-NH06-CDE-WEB", "ngdc_destination": "grp-TRD-NH06-CDE-APP",
     "ngdc_port": "TCP 8443", "ngdc_action": "Allow",
     "source_nh": "NH06", "source_sz": "CDE", "dest_nh": "NH06", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-008", "migration_id": "mig-003",
     "legacy_rule": "permit tcp 10.27.2.0/24 10.27.10.0/24 eq 1521",
     "legacy_source": "10.27.2.0/24", "legacy_destination": "10.27.10.0/24",
     "legacy_port": "TCP 1521", "legacy_action": "permit",
     "ngdc_source": "grp-TRD-NH06-CDE-APP", "ngdc_destination": "grp-TRD-NH06-CDE-DB",
     "ngdc_port": "TCP 1521", "ngdc_action": "Allow",
     "source_nh": "NH06", "source_sz": "CDE", "dest_nh": "NH06", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-009", "migration_id": "mig-003",
     "legacy_rule": "permit tcp 10.27.2.0/24 10.27.50.0/24 eq 1414",
     "legacy_source": "10.27.2.0/24", "legacy_destination": "10.27.50.0/24",
     "legacy_port": "TCP 1414", "legacy_action": "permit",
     "ngdc_source": "grp-TRD-NH06-CDE-APP", "ngdc_destination": "grp-TRD-NH06-CDE-MQ",
     "ngdc_port": "TCP 1414", "ngdc_action": "Allow",
     "source_nh": "NH06", "source_sz": "CDE", "dest_nh": "NH06", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-010", "migration_id": "mig-003",
     "legacy_rule": "permit ip 10.27.0.0/16 any",
     "legacy_source": "10.27.0.0/16", "legacy_destination": "any",
     "legacy_port": "ANY", "legacy_action": "permit",
     "ngdc_source": "", "ngdc_destination": "", "ngdc_port": "", "ngdc_action": "",
     "source_nh": "", "source_sz": "", "dest_nh": "", "dest_sz": "",
     "status": "Review Required", "compliance": "Non-Compliant"},
    # --- mig-004: INS from DC Sterling ---
    {"mapping_id": "map-011", "migration_id": "mig-004",
     "legacy_rule": "permit tcp 10.28.10.0/24 10.28.20.0/24 eq 8443",
     "legacy_source": "10.28.10.0/24", "legacy_destination": "10.28.20.0/24",
     "legacy_port": "TCP 8443", "legacy_action": "permit",
     "ngdc_source": "grp-INS-NH04-GEN-WEB", "ngdc_destination": "grp-INS-NH04-GEN-APP",
     "ngdc_port": "TCP 8443", "ngdc_action": "Allow",
     "source_nh": "NH04", "source_sz": "GEN", "dest_nh": "NH04", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-012", "migration_id": "mig-004",
     "legacy_rule": "permit tcp 10.28.20.0/24 10.28.50.0/24 eq 5432",
     "legacy_source": "10.28.20.0/24", "legacy_destination": "10.28.50.0/24",
     "legacy_port": "TCP 5432", "legacy_action": "permit",
     "ngdc_source": "grp-INS-NH04-GEN-APP", "ngdc_destination": "grp-INS-NH04-GEN-DB",
     "ngdc_port": "TCP 5432", "ngdc_action": "Allow",
     "source_nh": "NH04", "source_sz": "GEN", "dest_nh": "NH04", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-013", "migration_id": "mig-004",
     "legacy_rule": "permit tcp 10.28.10.50 10.28.99.0/24 eq 22",
     "legacy_source": "10.28.10.50", "legacy_destination": "10.28.99.0/24",
     "legacy_port": "TCP 22", "legacy_action": "permit",
     "ngdc_source": "", "ngdc_destination": "", "ngdc_port": "", "ngdc_action": "",
     "source_nh": "", "source_sz": "", "dest_nh": "", "dest_sz": "",
     "status": "Review Required", "compliance": "Non-Compliant"},
    # --- mig-005: FRD from DC Glen Bornie (completed) ---
    {"mapping_id": "map-014", "migration_id": "mig-005",
     "legacy_rule": "permit tcp 10.29.1.0/24 10.29.2.0/24 eq 1521",
     "legacy_source": "10.29.1.0/24", "legacy_destination": "10.29.2.0/24",
     "legacy_port": "TCP 1521", "legacy_action": "permit",
     "ngdc_source": "grp-FRD-NH02-CDE-APP", "ngdc_destination": "grp-CBK-NH02-CDE-DB",
     "ngdc_port": "TCP 1521", "ngdc_action": "Allow",
     "source_nh": "NH02", "source_sz": "CDE", "dest_nh": "NH02", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-015", "migration_id": "mig-005",
     "legacy_rule": "permit tcp 10.29.1.50 10.29.5.0/24 eq 1521",
     "legacy_source": "10.29.1.50", "legacy_destination": "10.29.5.0/24",
     "legacy_port": "TCP 1521", "legacy_action": "permit",
     "ngdc_source": "grp-FRD-NH02-CDE-APP", "ngdc_destination": "grp-CCM-NH02-CDE-DB",
     "ngdc_port": "TCP 1521", "ngdc_action": "Allow",
     "source_nh": "NH02", "source_sz": "CDE", "dest_nh": "NH02", "dest_sz": "CDE",
     "status": "Mapped", "compliance": "Compliant"},
    # --- mig-006: KYC from DC Manassas ---
    {"mapping_id": "map-016", "migration_id": "mig-006",
     "legacy_rule": "permit tcp 10.30.5.0/24 10.30.10.0/24 eq 8443",
     "legacy_source": "10.30.5.0/24", "legacy_destination": "10.30.10.0/24",
     "legacy_port": "TCP 8443", "legacy_action": "permit",
     "ngdc_source": "grp-KYC-NH05-GEN-WEB", "ngdc_destination": "grp-KYC-NH05-GEN-APP",
     "ngdc_port": "TCP 8443", "ngdc_action": "Allow",
     "source_nh": "NH05", "source_sz": "GEN", "dest_nh": "NH05", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-017", "migration_id": "mig-006",
     "legacy_rule": "permit tcp 10.30.10.0/24 10.30.20.0/24 eq 5432",
     "legacy_source": "10.30.10.0/24", "legacy_destination": "10.30.20.0/24",
     "legacy_port": "TCP 5432", "legacy_action": "permit",
     "ngdc_source": "grp-KYC-NH05-GEN-APP", "ngdc_destination": "grp-KYC-NH05-GEN-DB",
     "ngdc_port": "TCP 5432", "ngdc_action": "Allow",
     "source_nh": "NH05", "source_sz": "GEN", "dest_nh": "NH05", "dest_sz": "GEN",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-018", "migration_id": "mig-006",
     "legacy_rule": "permit tcp 10.30.10.0/24 any eq 443",
     "legacy_source": "10.30.10.0/24", "legacy_destination": "any",
     "legacy_port": "TCP 443", "legacy_action": "permit",
     "ngdc_source": "grp-KYC-NH05-GEN-APP", "ngdc_destination": "grp-EXT-NH14-DMZ-API",
     "ngdc_port": "TCP 443", "ngdc_action": "Allow",
     "source_nh": "NH05", "source_sz": "GEN", "dest_nh": "NH14", "dest_sz": "DMZ",
     "status": "Mapped", "compliance": "Compliant"},
    {"mapping_id": "map-019", "migration_id": "mig-006",
     "legacy_rule": "permit ip 10.30.0.0/16 10.30.0.0/16",
     "legacy_source": "10.30.0.0/16", "legacy_destination": "10.30.0.0/16",
     "legacy_port": "ANY", "legacy_action": "permit",
     "ngdc_source": "", "ngdc_destination": "", "ngdc_port": "", "ngdc_action": "",
     "source_nh": "", "source_sz": "", "dest_nh": "", "dest_sz": "",
     "status": "Review Required", "compliance": "Non-Compliant"},
]

# Groups: collections of IPs/ranges that follow naming standards
# Each group has a name (grp-/svr-/rng-), app_id, nh, sz, subtype, and a list of members (IPs or CIDRs)
SEED_GROUPS = [
    # CRM groups
    {"name": "grp-CRM-NH02-CDE-APP", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "CRM Application Servers", "members": [
        {"type": "ip", "value": "10.1.1.10", "description": "CRM App Server 1"},
        {"type": "ip", "value": "10.1.1.11", "description": "CRM App Server 2"},
        {"type": "ip", "value": "10.1.1.12", "description": "CRM App Server 3"},
     ]},
    {"name": "grp-CRM-NH02-CDE-DB", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "CRM Database Servers", "members": [
        {"type": "ip", "value": "10.1.2.10", "description": "CRM Oracle Primary"},
        {"type": "ip", "value": "10.1.2.11", "description": "CRM Oracle Standby"},
     ]},
    # CBK groups
    {"name": "grp-CBK-NH02-CDE-DB", "app_id": "CBK", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "Core Banking Database", "members": [
        {"type": "ip", "value": "10.1.2.20", "description": "CBK DB Primary"},
        {"type": "ip", "value": "10.1.2.21", "description": "CBK DB Standby"},
        {"type": "cidr", "value": "10.1.2.64/28", "description": "CBK DB Pool"},
     ]},
    # DIG groups
    {"name": "grp-DIG-NH03-CDE-WEB", "app_id": "DIG", "nh": "NH03", "sz": "CDE", "subtype": "WEB",
     "description": "Digital Banking Web Servers", "members": [
        {"type": "ip", "value": "10.2.1.10", "description": "DIG Web 1"},
        {"type": "ip", "value": "10.2.1.11", "description": "DIG Web 2"},
     ]},
    # PAY groups
    {"name": "grp-PAY-NH07-CDE-APP", "app_id": "PAY", "nh": "NH07", "sz": "CDE", "subtype": "APP",
     "description": "Payment Processing App Servers", "members": [
        {"type": "ip", "value": "10.6.1.10", "description": "PAY App 1"},
        {"type": "ip", "value": "10.6.1.11", "description": "PAY App 2"},
        {"type": "cidr", "value": "10.6.1.64/28", "description": "PAY App Pool"},
     ]},
    # ENT groups
    {"name": "grp-ENT-NH05-GEN-APP", "app_id": "ENT", "nh": "NH05", "sz": "GEN", "subtype": "APP",
     "description": "Enterprise CRM App Servers", "members": [
        {"type": "ip", "value": "10.4.1.10", "description": "ENT App 1"},
        {"type": "ip", "value": "10.4.1.11", "description": "ENT App 2"},
     ]},
    # SHR groups
    {"name": "grp-SHR-NH13-GEN-SVC", "app_id": "SHR", "nh": "NH13", "sz": "GEN", "subtype": "SVC",
     "description": "Shared Analytics Services", "members": [
        {"type": "cidr", "value": "10.100.1.0/28", "description": "Shared SVC Subnet"},
     ]},
    # HRM groups
    {"name": "grp-HRM-NH01-GEN-WEB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "WEB",
     "description": "HR Portal Web Servers", "members": [
        {"type": "ip", "value": "10.0.1.10", "description": "HR Web 1"},
        {"type": "ip", "value": "10.0.1.11", "description": "HR Web 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-APP", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "HR Application Servers", "members": [
        {"type": "ip", "value": "10.0.1.20", "description": "HR App 1"},
        {"type": "ip", "value": "10.0.1.21", "description": "HR App 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-DB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "DB",
     "description": "HR Database", "members": [
        {"type": "ip", "value": "10.0.1.30", "description": "HR Postgres Primary"},
        {"type": "ip", "value": "10.0.1.31", "description": "HR Postgres Replica"},
     ]},
    {"name": "grp-HRM-NH01-GEN-BAT", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "BAT",
     "description": "HR Payroll Batch Servers", "members": [
        {"type": "ip", "value": "10.0.1.40", "description": "HR Batch 1"},
     ]},
    # TRD groups
    {"name": "grp-TRD-NH06-CDE-WEB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "WEB",
     "description": "Trading Web Tier", "members": [
        {"type": "ip", "value": "10.5.1.10", "description": "TRD Web 1"},
        {"type": "ip", "value": "10.5.1.11", "description": "TRD Web 2"},
     ]},
    {"name": "grp-TRD-NH06-CDE-APP", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "APP",
     "description": "Trading Application Servers", "members": [
        {"type": "ip", "value": "10.5.1.20", "description": "TRD App 1"},
        {"type": "ip", "value": "10.5.1.21", "description": "TRD App 2"},
        {"type": "ip", "value": "10.5.1.22", "description": "TRD App 3"},
     ]},
    {"name": "grp-TRD-NH06-CDE-DB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "DB",
     "description": "Trading Oracle DB", "members": [
        {"type": "ip", "value": "10.5.1.30", "description": "TRD Oracle Primary"},
        {"type": "ip", "value": "10.5.1.31", "description": "TRD Oracle Standby"},
     ]},
    {"name": "grp-TRD-NH06-CDE-MQ", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "MQ",
     "description": "Trading MQ Broker", "members": [
        {"type": "ip", "value": "10.5.1.40", "description": "TRD MQ Broker 1"},
     ]},
    # FRD groups
    {"name": "grp-FRD-NH02-CDE-APP", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "Fraud Detection Engine", "members": [
        {"type": "ip", "value": "10.1.1.50", "description": "FRD Engine 1"},
        {"type": "ip", "value": "10.1.1.51", "description": "FRD Engine 2"},
     ]},
    # AGW groups
    {"name": "grp-AGW-NH14-DMZ-API", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "API Gateway Servers", "members": [
        {"type": "ip", "value": "10.70.1.10", "description": "AGW API 1"},
        {"type": "ip", "value": "10.70.1.11", "description": "AGW API 2"},
     ]},
    {"name": "grp-AGW-NH14-DMZ-LB", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "LB",
     "description": "API Gateway Load Balancer", "members": [
        {"type": "ip", "value": "10.70.1.5", "description": "AGW LB VIP"},
     ]},
    # EXT group (DMZ external API)
    {"name": "grp-EXT-NH14-DMZ-API", "app_id": "EXT", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "External Partner API Endpoints", "members": [
        {"type": "cidr", "value": "10.70.2.0/28", "description": "External API Subnet"},
     ]},
    # MBL groups
    {"name": "grp-MBL-NH03-CDE-API", "app_id": "MBL", "nh": "NH03", "sz": "CDE", "subtype": "API",
     "description": "Mobile Banking API", "members": [
        {"type": "ip", "value": "10.2.1.50", "description": "MBL API 1"},
        {"type": "ip", "value": "10.2.1.51", "description": "MBL API 2"},
     ]},
    {"name": "grp-MBL-NH03-CDE-APP", "app_id": "MBL", "nh": "NH03", "sz": "CDE", "subtype": "APP",
     "description": "Mobile Banking App Servers", "members": [
        {"type": "ip", "value": "10.2.2.10", "description": "MBL App 1"},
        {"type": "ip", "value": "10.2.2.11", "description": "MBL App 2"},
     ]},
    # SOC groups
    {"name": "grp-SOC-NH01-GEN-APP", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "SIEM and SOC Collectors", "members": [
        {"type": "ip", "value": "10.0.2.10", "description": "SOC SIEM 1"},
        {"type": "ip", "value": "10.0.2.11", "description": "SOC SIEM 2"},
     ]},
    {"name": "grp-SOC-NH01-GEN-DB", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "DB",
     "description": "SOC Elasticsearch Cluster", "members": [
        {"type": "ip", "value": "10.0.2.20", "description": "SOC ES Node 1"},
        {"type": "ip", "value": "10.0.2.21", "description": "SOC ES Node 2"},
        {"type": "ip", "value": "10.0.2.22", "description": "SOC ES Node 3"},
     ]},
    {"name": "grp-SOC-NH01-GEN-MON", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "MON",
     "description": "SOC Monitoring Agents", "members": [
        {"type": "cidr", "value": "10.0.2.64/28", "description": "SOC Mon Subnet"},
     ]},
]

SEED_CHG_REQUESTS = [
    {"chg_id": "CHG10001", "rule_ids": ["R-3001"], "status": "Approved",
     "description": "Deploy CRM to Core Banking DB rule",
     "requested_by": "Jane Smith", "approved_by": "Security Team",
     "created_at": (datetime.utcnow() + timedelta(days=-31)).isoformat(),
     "updated_at": (datetime.utcnow() + timedelta(days=-30)).isoformat()},
]


# ============================================================
# Seed / Init
# ============================================================

async def seed_database() -> None:
    """Seed JSON files with initial data if they don't exist."""
    _ensure_dir()
    if _load("neighbourhoods") is not None:
        return
    _save("neighbourhoods", deepcopy(SEED_NEIGHBOURHOODS))
    _save("security_zones", deepcopy(SEED_SECURITY_ZONES))
    _save("ngdc_datacenters", deepcopy(SEED_NGDC_DATACENTERS))
    _save("legacy_datacenters", deepcopy(SEED_LEGACY_DATACENTERS))
    _save("applications", deepcopy(SEED_APPLICATIONS))
    _save("environments", deepcopy(SEED_ENVIRONMENTS))
    _save("predefined_destinations", deepcopy(SEED_PREDEFINED_DESTINATIONS))
    _save("naming_standards", deepcopy(SEED_NAMING_STANDARDS))
    _save("policy_matrix", deepcopy(SEED_POLICY_MATRIX))
    _save("org_config", deepcopy(SEED_ORG_CONFIG))
    _save("firewall_rules", _build_seed_rules())
    _save("rule_history", [])
    _save("migrations", deepcopy(SEED_MIGRATIONS))
    _save("migration_mappings", deepcopy(SEED_MIGRATION_MAPPINGS))
    _save("chg_requests", deepcopy(SEED_CHG_REQUESTS))
    _save("groups", deepcopy(SEED_GROUPS))


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


async def get_org_config() -> dict[str, Any] | None:
    return _load("org_config")


# ============================================================
# Firewall Rules CRUD
# ============================================================

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
        "datacenter": rule_data.get("datacenter", "EAST_NGDC"),
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
    policy_matrix = _load("policy_matrix") or []
    source_zone = source.get("security_zone", "GEN") if isinstance(source, dict) else "GEN"
    dest_zone = destination.get("security_zone", "GEN") if isinstance(destination, dict) else "GEN"
    source_type = source.get("source_type", "Group") if isinstance(source, dict) else "Group"
    group_name = source.get("group_name", "") if isinstance(source, dict) else ""
    is_group_to_group = source_type == "Group" and bool(group_name)
    naming_compliant = bool(group_name and group_name.startswith("grp-")) if group_name else True

    policy = None
    for p in policy_matrix:
        if p.get("source_zone") == source_zone and p.get("dest_zone") == dest_zone:
            policy = p
            break

    details: list[str] = []
    if policy:
        result = policy.get("action", "Permitted")
        requires_exception = result == "Exception Required"
        details.append(f"Policy: {source_zone} -> {dest_zone} = {result}")
    else:
        result = "Permitted"
        requires_exception = False
        details.append(f"No explicit policy for {source_zone} -> {dest_zone}, defaulting to Permitted")

    if not is_group_to_group:
        details.append("Warning: Rule is not group-to-group")
    if not naming_compliant and group_name:
        details.append(f"Warning: Group name '{group_name}' does not follow naming standards")

    return {
        "result": result,
        "message": f"Traffic from {source_zone} to {dest_zone}: {result}",
        "details": details,
        "ngdc_zone_check": True,
        "birthright_compliant": not requires_exception,
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
