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
    # From reference: Each NH has multiple security zones with VRF-IDs and Transit VNIs
    {"nh_id": "NH01", "name": "Platform Services", "environment": "Production",
     "description": "Platform and infrastructure services", "ip_ranges": [
        {"cidr": "10.0.1.0/24", "description": "NH01 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "10.0.2.0/24", "description": "NH01 East Secondary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.50.0/24", "description": "NH01 West Primary", "dc": "BETA_NGDC"},
        {"cidr": "10.50.50.0/24", "description": "NH01 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH01 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH01 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH01 sz06", "description": "Critical Payment Applications"},
        {"zone": "PSE", "vrf_id": "NH01 sz07", "description": "Production Simulation Environment"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH02", "name": "Team Eta", "environment": "Production",
     "description": "Data processing and analytics platforms", "ip_ranges": [
        {"cidr": "10.1.1.0/24", "description": "NH02 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.1.2.0/24", "description": "NH02 East DB Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.1.0/24", "description": "NH02 West App", "dc": "BETA_NGDC"},
        {"cidr": "10.50.1.0/24", "description": "NH02 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH02 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH02 sz05", "transit_vni": 8051, "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH02 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH03", "name": "Team Delta", "environment": "Production",
     "description": "Web application and API hosting", "ip_ranges": [
        {"cidr": "10.2.1.0/24", "description": "NH03 East Web Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "10.2.2.0/24", "description": "NH03 East App Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.3.0/24", "description": "NH03 West Web", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH03 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH03 sz05", "description": "Card Holder Data"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH04", "name": "Customer Portal", "environment": "Production",
     "description": "Customer-facing portal services", "ip_ranges": [
        {"cidr": "10.3.1.0/24", "description": "NH04 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.5.0/24", "description": "NH04 West Primary", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH04 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH04 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH04 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH05", "name": "Team Theta", "environment": "Production",
     "description": "Enterprise system hosting", "ip_ranges": [
        {"cidr": "10.4.1.0/24", "description": "NH05 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.4.2.0/24", "description": "NH05 East DB Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.10.0/24", "description": "NH05 West App", "dc": "BETA_NGDC"},
        {"cidr": "10.54.1.0/24", "description": "NH05 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH05 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH05 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH05 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH06", "name": "Enterprise Extended", "environment": "Production",
     "description": "Enterprise extended services (overlay)", "ip_ranges": [
        {"cidr": "10.5.1.0/24", "description": "NH06 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.20.0/24", "description": "NH06 West App", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH06 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH06 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH06 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "Overlay01", "transit_vni": 4000, "description": "Standard/General (Overlay)"},
     ]},
    {"nh_id": "NH07", "name": "Transaction Processing", "environment": "Production",
     "description": "Transaction processing and settlement", "ip_ranges": [
        {"cidr": "10.6.1.0/24", "description": "NH07 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.6.2.0/24", "description": "NH07 East DB Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.22.0/24", "description": "NH07 West App", "dc": "BETA_NGDC"},
        {"cidr": "10.56.1.0/24", "description": "NH07 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH07 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH07 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH07 sz06", "description": "Critical Payment Applications"},
        {"zone": "Extra", "vrf_id": "NH07 sz08", "description": "Additional zone"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH08", "name": "Data Processing Extended", "environment": "Production",
     "description": "Extended data processing platforms", "ip_ranges": [
        {"cidr": "10.7.1.0/24", "description": "NH08 East App", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.30.0/24", "description": "NH08 West App", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH08 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH08 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH08 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH09", "name": "Team Mu", "environment": "Production",
     "description": "Support and service channel applications", "ip_ranges": [
        {"cidr": "10.8.1.0/24", "description": "NH09 East App", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.40.0/24", "description": "NH09 West App", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH09 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH09 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH09 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH10", "name": "Team Kappa", "environment": "Production",
     "description": "Lending and origination services", "ip_ranges": [
        {"cidr": "10.9.1.0/24", "description": "NH10 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.55.1.0/24", "description": "NH10 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH10 sz04", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH10 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH10 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "gen", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH11", "name": "Production Mainframe", "environment": "Production",
     "description": "Production mainframe systems", "ip_ranges": [
        {"cidr": "10.10.1.0/24", "description": "NH11 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "10.60.1.0/24", "description": "NH11 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": []},
    {"nh_id": "NH12", "name": "Non-Production Mainframe", "environment": "Non-Production",
     "description": "Non-production mainframe systems", "ip_ranges": [
        {"cidr": "10.11.1.0/24", "description": "NH12 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "10.61.1.0/24", "description": "NH12 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": []},
    {"nh_id": "NH13", "name": "Non-Production Shared", "environment": "Non-Production",
     "description": "Shared non-production environment", "ip_ranges": [
        {"cidr": "10.100.1.0/24", "description": "NH13 East App", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.100.0/24", "description": "NH13 West App", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH13 sz04", "transit_vni": 3061, "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH13 sz05", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH13 sz06", "description": "Critical Payment Applications"},
        {"zone": "Standard", "vrf_id": "Overlay01", "transit_vni": 4000, "description": "Standard/General (Overlay)"},
     ]},
    {"nh_id": "NH14", "name": "DMZ", "environment": "Production",
     "description": "Demilitarized zone for external-facing services", "ip_ranges": [
        {"cidr": "10.70.1.0/24", "description": "NH14 East Web Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.70.2.0/24", "description": "NH14 East API Gateway", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.70.0/24", "description": "NH14 West Web", "dc": "BETA_NGDC"},
        {"cidr": "10.70.10.0/24", "description": "NH14 Central Web", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": []},
    {"nh_id": "NH15", "name": "Non-Production DMZ", "environment": "Non-Production",
     "description": "Non-production DMZ for test external services", "ip_ranges": [
        {"cidr": "10.80.1.0/24", "description": "NH15 East Web", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.80.0/24", "description": "NH15 West Web", "dc": "BETA_NGDC"},
     ],
     "security_zones": []},
    {"nh_id": "NH16", "name": "Pre-Production Shared", "environment": "Pre-Production",
     "description": "Pre-production staging environment", "ip_ranges": [
        {"cidr": "10.90.1.0/24", "description": "NH16 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.65.1.0/24", "description": "NH16 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": []},
    {"nh_id": "NH17", "name": "Pre-Production DMZ", "environment": "Pre-Production",
     "description": "Pre-production DMZ for staging external services", "ip_ranges": [
        {"cidr": "10.91.1.0/24", "description": "NH17 East Web", "dc": "ALPHA_NGDC"},
        {"cidr": "10.66.1.0/24", "description": "NH17 Central Web", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": []},
]

SEED_SECURITY_ZONES = [
    # === Production Security Zones (per NH reference) ===
    {"code": "CCS", "name": "Critical Core Services", "description": "Critical core services zone - highest security tier",
     "risk_level": "Critical", "pci_scope": True, "zone_type": "Production",
     "vrf_suffix": "sz04", "ip_ranges": [
        {"cidr": "10.1.0.0/16", "description": "CCS East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.0.0/20", "description": "CCS West Block", "dc": "BETA_NGDC"},
        {"cidr": "10.50.0.0/16", "description": "CCS Central Block", "dc": "GAMMA_NGDC"},
     ]},
    {"code": "CDE", "name": "Card Holder Data", "description": "Cardholder Data Environment - PCI DSS compliant",
     "risk_level": "Critical", "pci_scope": True, "zone_type": "Production",
     "vrf_suffix": "sz05", "ip_ranges": [
        {"cidr": "10.2.0.0/16", "description": "CDE East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.16.0/20", "description": "CDE West Block", "dc": "BETA_NGDC"},
        {"cidr": "10.52.0.0/16", "description": "CDE Central Block", "dc": "GAMMA_NGDC"},
     ]},
    {"code": "CPA", "name": "Critical Payment Applications", "description": "Critical payment application processing zone",
     "risk_level": "Critical", "pci_scope": True, "zone_type": "Production",
     "vrf_suffix": "sz06", "ip_ranges": [
        {"cidr": "10.3.0.0/16", "description": "CPA East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.32.0/20", "description": "CPA West Block", "dc": "BETA_NGDC"},
        {"cidr": "10.53.0.0/16", "description": "CPA Central Block", "dc": "GAMMA_NGDC"},
     ]},
    {"code": "PSE", "name": "Production Simulation Environment", "description": "Production simulation for testing in prod-like conditions",
     "risk_level": "High", "pci_scope": False, "zone_type": "Production",
     "vrf_suffix": "sz07", "ip_ranges": [
        {"cidr": "10.4.0.0/16", "description": "PSE East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "Standard", "name": "Standard/General", "description": "Standard general-purpose zone (GEN VRF)",
     "risk_level": "Medium", "pci_scope": False, "zone_type": "Production",
     "vrf_suffix": "gen", "ip_ranges": [
        {"cidr": "10.0.0.0/16", "description": "Standard East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.48.0/20", "description": "Standard West Block", "dc": "BETA_NGDC"},
     ]},
    {"code": "GEN", "name": "General", "description": "General purpose security zone (alias for Standard)",
     "risk_level": "Medium", "pci_scope": False, "zone_type": "Production",
     "vrf_suffix": "gen", "ip_ranges": [
        {"cidr": "10.0.0.0/16", "description": "GEN East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.48.0/20", "description": "GEN West Block", "dc": "BETA_NGDC"},
     ]},
    {"code": "DMZ", "name": "DMZ", "description": "Demilitarized zone for external-facing services",
     "risk_level": "High", "pci_scope": False, "zone_type": "Production", "ip_ranges": [
        {"cidr": "10.70.0.0/16", "description": "DMZ East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.70.0/22", "description": "DMZ West Block", "dc": "BETA_NGDC"},
     ]},
    {"code": "RST", "name": "Restricted", "description": "Highly restricted zone for sensitive systems",
     "risk_level": "Critical", "pci_scope": True, "zone_type": "Production", "ip_ranges": [
        {"cidr": "10.10.0.0/16", "description": "RST East Block", "dc": "ALPHA_NGDC"},
        {"cidr": "10.60.0.0/16", "description": "RST Central Block", "dc": "GAMMA_NGDC"},
     ]},
    {"code": "PAA", "name": "Publicly Accessible Applications", "description": "Publicly accessible application zone",
     "risk_level": "High", "pci_scope": True, "zone_type": "Production", "ip_ranges": [
        {"cidr": "10.71.0.0/16", "description": "PAA East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "3PY", "name": "Third Party", "description": "Third-party connectivity zone",
     "risk_level": "High", "pci_scope": False, "zone_type": "Production", "ip_ranges": [
        {"cidr": "10.79.0.0/16", "description": "3PY East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "PCI_CAN", "name": "PCI CAN", "description": "PCI Cardholder Area Network",
     "risk_level": "Critical", "pci_scope": True, "zone_type": "Heritage", "ip_ranges": [
        {"cidr": "10.73.0.0/16", "description": "PCI CAN East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "CAN", "name": "CAN", "description": "Campus Area Network",
     "risk_level": "High", "pci_scope": False, "zone_type": "Heritage", "ip_ranges": [
        {"cidr": "10.74.0.0/16", "description": "CAN East Block", "dc": "ALPHA_NGDC"},
     ]},
    # === Non-Production Security Zones ===
    {"code": "UGEN", "name": "Non-Prod General", "description": "Non-production general zone (UGEN/USTD)",
     "risk_level": "Low", "pci_scope": False, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.100.0.0/16", "description": "UGEN East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "USTD", "name": "Non-Prod Standard", "description": "Non-production standard zone",
     "risk_level": "Low", "pci_scope": False, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.101.0.0/16", "description": "USTD East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "UCCS", "name": "Non-Prod Critical Core Services", "description": "Non-production CCS zone",
     "risk_level": "Medium", "pci_scope": False, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.102.0.0/16", "description": "UCCS East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "UPAA", "name": "Non-Prod PAA", "description": "Non-production publicly accessible apps zone",
     "risk_level": "Medium", "pci_scope": False, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.103.0.0/16", "description": "UPAA East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "UCPA", "name": "Non-Prod Critical Payment Apps", "description": "Non-production critical payment apps zone",
     "risk_level": "Medium", "pci_scope": True, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.104.0.0/16", "description": "UCPA East Block", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "UCDE", "name": "Non-Prod Card Holder Data", "description": "Non-production cardholder data zone",
     "risk_level": "Medium", "pci_scope": True, "zone_type": "Non-Production", "ip_ranges": [
        {"cidr": "10.105.0.0/16", "description": "UCDE East Block", "dc": "ALPHA_NGDC"},
     ]},
    # === Additional Zones ===
    {"code": "MGT", "name": "Management", "description": "Network management and monitoring zone",
     "risk_level": "High", "pci_scope": False, "zone_type": "Infrastructure", "ip_ranges": [
        {"cidr": "10.200.1.0/24", "description": "MGT East", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "EXT", "name": "External Partners", "description": "External partner connectivity zone",
     "risk_level": "High", "pci_scope": False, "zone_type": "External", "ip_ranges": [
        {"cidr": "10.79.1.0/24", "description": "EXT East", "dc": "ALPHA_NGDC"},
     ]},
]

SEED_NGDC_DATACENTERS = [
    {"name": "Alpha NGDC", "code": "ALPHA_NGDC", "location": "Region Alpha", "status": "Active",
     "description": "Primary Alpha NGDC facility", "contact": "noc-alpha@example.com",
     "capacity": "2000 racks", "ip_supernet": "10.0.0.0/8",
     "neighbourhoods": ["NH01","NH02","NH03","NH04","NH05","NH07","NH08","NH09","NH13","NH14","NH15","NH16","NH17"]},
    {"name": "Beta NGDC", "code": "BETA_NGDC", "location": "Region Beta", "status": "Active",
     "description": "Primary Beta NGDC facility", "contact": "noc-beta@example.com",
     "capacity": "1500 racks", "ip_supernet": "172.16.0.0/12",
     "neighbourhoods": ["NH03","NH05","NH06","NH08","NH09","NH14","NH15"]},
    {"name": "Gamma NGDC", "code": "GAMMA_NGDC", "location": "Region Gamma", "status": "Active",
     "description": "Gamma NGDC for DR and mainframe", "contact": "noc-gamma@example.com",
     "capacity": "1200 racks", "ip_supernet": "10.50.0.0/12",
     "neighbourhoods": ["NH02","NH10","NH11","NH12","NH16","NH17"]},
]

SEED_LEGACY_DATACENTERS = [
    {"name": "Legacy DC Alpha", "code": "DC_LEGACY_A", "location": "Legacy Region A", "status": "Decommissioning",
     "description": "Legacy DC - migration to Gamma NGDC", "ip_range": "10.25.0.0/16", "server_count": 450, "app_count": 35},
    {"name": "Legacy DC Beta", "code": "DC_LEGACY_B", "location": "Legacy Region B", "status": "Decommissioning",
     "description": "Legacy DC - migration to Alpha NGDC", "ip_range": "10.26.0.0/16", "server_count": 320, "app_count": 22},
    {"name": "Legacy DC Gamma", "code": "DC_LEGACY_C", "location": "Legacy Region C", "status": "Active",
     "description": "Legacy DC - partial migration in progress", "ip_range": "10.27.0.0/16", "server_count": 580, "app_count": 41},
    {"name": "Legacy DC Delta", "code": "DC_LEGACY_D", "location": "Legacy Region D", "status": "Active",
     "description": "Legacy DC - migration planned", "ip_range": "10.28.0.0/16", "server_count": 410, "app_count": 29},
    {"name": "Legacy DC Epsilon", "code": "DC_LEGACY_E", "location": "Legacy Region E", "status": "Decommissioning",
     "description": "Legacy DC - final migration wave", "ip_range": "10.29.0.0/16", "server_count": 270, "app_count": 18},
    {"name": "Legacy DC Zeta", "code": "DC_LEGACY_F", "location": "Legacy Region F", "status": "Active",
     "description": "Legacy DC - migration in planning", "ip_range": "10.30.0.0/16", "server_count": 390, "app_count": 27},
]

SEED_APPLICATIONS = [
    {"app_id": "CRM", "name": "App Alpha", "owner": "Owner A", "team": "Team Alpha",
     "nh": "NH02", "sz": "CDE", "criticality": 2, "pci_scope": True, "description": "Application alpha system"},
    {"app_id": "ORD", "name": "App Beta", "owner": "Jon", "team": "Team Beta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application beta platform"},
    {"app_id": "PSA", "name": "App Gamma", "owner": "Owner A", "team": "Team Gamma",
     "nh": "NH05", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application gamma automation"},
    {"app_id": "DIG", "name": "App Delta", "owner": "Jon", "team": "Team Delta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application delta platform"},
    {"app_id": "PAY", "name": "App Epsilon", "owner": "Owner A", "team": "Team Epsilon",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application epsilon engine"},
    {"app_id": "ENT", "name": "App Zeta", "owner": "Jon", "team": "Team Gamma",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application zeta system"},
    {"app_id": "SHR", "name": "App Eta", "owner": "Owner A", "team": "Team Eta",
     "nh": "NH08", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application eta platform"},
    {"app_id": "WHL", "name": "Team Theta", "owner": "Jon", "team": "Team Theta",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application theta system"},
    {"app_id": "CBK", "name": "Team Iota", "owner": "Owner A", "team": "Team Iota",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application iota ledger"},
    {"app_id": "CLN", "name": "Team Kappa", "owner": "Jon", "team": "Team Kappa",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application kappa origination"},
    {"app_id": "WLT", "name": "App Lambda", "owner": "Owner A", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application lambda advisory"},
    {"app_id": "ACH", "name": "Team Mu", "owner": "Jon", "team": "Team Mu",
     "nh": "NH09", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application mu services"},
    # --- 15 additional applications ---
    {"app_id": "HRM", "name": "App Nu", "owner": "Owner B", "team": "Team Nu",
     "nh": "NH01", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application nu management"},
    {"app_id": "TRD", "name": "App Xi", "owner": "Owner C", "team": "Team Xi",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application xi processing"},
    {"app_id": "FRD", "name": "App Omicron", "owner": "Owner D", "team": "Team Omicron",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application omicron detection"},
    {"app_id": "RGM", "name": "App Pi", "owner": "Owner E", "team": "Team Pi",
     "nh": "NH11", "sz": "RST", "criticality": 1, "pci_scope": True, "description": "Application pi reporting"},
    {"app_id": "MBL", "name": "App Rho", "owner": "Owner F", "team": "Team Delta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application rho mobile app"},
    {"app_id": "INS", "name": "App Sigma", "owner": "Owner G", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application sigma underwriting"},
    {"app_id": "TAX", "name": "App Tau", "owner": "Owner H", "team": "Team Tau",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application tau calculation"},
    {"app_id": "AML", "name": "App Upsilon", "owner": "Owner I", "team": "Team Omicron",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application upsilon screening"},
    {"app_id": "KYC", "name": "App Phi", "owner": "Owner J", "team": "Team Pi",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application phi verification"},
    {"app_id": "TRS", "name": "App Chi", "owner": "Owner K", "team": "Team Chi",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application chi management"},
    {"app_id": "CCM", "name": "App Psi", "owner": "Owner L", "team": "Team Psi",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application psi processing"},
    {"app_id": "LON", "name": "App Omega", "owner": "Owner M", "team": "Team Kappa",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application omega underwriting"},
    {"app_id": "BRK", "name": "App Alpha2", "owner": "Owner N", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application alpha2 platform"},
    {"app_id": "AGW", "name": "App Beta2", "owner": "Owner O", "team": "Team Beta2",
     "nh": "NH14", "sz": "DMZ", "criticality": 1, "pci_scope": False, "description": "Application beta2 gateway"},
    {"app_id": "SOC", "name": "App Gamma2", "owner": "Owner P", "team": "Team Gamma2",
     "nh": "NH01", "sz": "GEN", "criticality": 1, "pci_scope": False, "description": "Application gamma2 monitoring"},
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
    {"name": "grp-DIG-NH03-CDE-WEB", "security_zone": "CDE", "description": "Web App Servers",
     "friendly_name": "WEB APPS - PROD", "ip": "10.2.1.0/24", "port": "TCP 8443", "nh": "NH03"},
    {"name": "grp-ENT-NH05-GEN-APP", "security_zone": "GEN", "description": "Enterprise App Servers",
     "friendly_name": "ENTERPRISE APPS", "ip": "10.4.1.0/24", "port": "TCP 8443", "nh": "NH05"},
    {"name": "grp-SHR-NH13-GEN-SVC", "security_zone": "GEN", "description": "Shared Platform Services",
     "friendly_name": "SHARED PLATFORMS", "ip": "10.100.1.0/24", "port": "TCP 8080", "nh": "NH13"},
    {"name": "grp-EXT-NH14-DMZ-API", "security_zone": "DMZ", "description": "External API Gateway",
     "friendly_name": "EXTERNAL APIS", "ip": "10.70.2.0/24", "port": "TCP 443", "nh": "NH14"},
    {"name": "grp-CBK-NH02-CDE-DB", "security_zone": "CDE", "description": "Primary DB Cluster",
     "friendly_name": "PRIMARY DATABASE", "ip": "10.50.1.0/24", "port": "TCP 1521", "nh": "NH02"},
    {"name": "grp-PAY-NH07-CDE-DB", "security_zone": "CDE", "description": "Transaction Database",
     "friendly_name": "TRANSACTION DATABASE", "ip": "10.6.2.0/24", "port": "TCP 1521", "nh": "NH07"},
    {"name": "grp-DMZ-NH14-DMZ-WEB", "security_zone": "DMZ", "description": "DMZ Web Services",
     "friendly_name": "DMZ WEB SERVICES", "ip": "10.70.1.0/24", "port": "TCP 443", "nh": "NH14"},
    {"name": "grp-MGT-NH01-MGT-MON", "security_zone": "MGT", "description": "Management & Monitoring",
     "friendly_name": "MANAGEMENT PLANE", "ip": "10.200.1.0/24", "port": "TCP 8443", "nh": "NH01"},
    {"name": "grp-WHL-NH06-CDE-APP", "security_zone": "CDE", "description": "Enterprise App Servers Group",
     "friendly_name": "ENTERPRISE SYSTEMS", "ip": "10.5.1.0/24", "port": "TCP 8443", "nh": "NH06"},
    {"name": "grp-DAT-NH08-GEN-APP", "security_zone": "GEN", "description": "Data Processing App Servers",
     "friendly_name": "DATA PROCESSING", "ip": "10.7.1.0/24", "port": "TCP 8443", "nh": "NH08"},
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

# =====================================================================
# THREE-PART POLICY MATRIX (from NGDC reference)
# "Blocked" means a new Firewall Request is required to open the flow
# =====================================================================

# --- 1) Heritage Data Center Matrix ---
# Legacy zone-to-NGDC zone migration rules
SEED_HERITAGE_DC_MATRIX = [
    {"heritage_dc": "Any", "heritage_zone": "Default", "new_dc": "Any", "prod_nonprod": "Prod",
     "new_dc_zone": "Standard", "action": "Permitted",
     "reason": "Default heritage zone maps to Standard in prod NGDC"},
    {"heritage_dc": "Any", "heritage_zone": "Default", "new_dc": "Any", "prod_nonprod": "Non Prod",
     "new_dc_zone": "Standard", "action": "Permitted (Exception)",
     "reason": "Default heritage zone to Non-Prod Standard requires exception approval"},
    {"heritage_dc": "Any", "heritage_zone": "PAA", "new_dc": "Any", "prod_nonprod": "Prod",
     "new_dc_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "reason": "PAA to PAA is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "PAA", "new_dc": "Any", "prod_nonprod": "Non Prod",
     "new_dc_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "reason": "PAA to Non-Prod PAA is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "PCI CAN", "new_dc": "Any", "prod_nonprod": "Prod",
     "new_dc_zone": "CDE", "action": "Blocked - Firewall Request Required",
     "reason": "PCI CAN to CDE is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "PCI CAN", "new_dc": "Any", "prod_nonprod": "Non Prod",
     "new_dc_zone": "CDE", "action": "Blocked - Firewall Request Required",
     "reason": "PCI CAN to Non-Prod CDE is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "CAN", "new_dc": "Any", "prod_nonprod": "Prod",
     "new_dc_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "reason": "CAN to CPA is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "CAN", "new_dc": "Any", "prod_nonprod": "Non Prod",
     "new_dc_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "reason": "CAN to Non-Prod CPA is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "CAN", "new_dc": "Any", "prod_nonprod": "Prod",
     "new_dc_zone": "3PY", "action": "Blocked - Firewall Request Required",
     "reason": "CAN to 3PY is blocked by default; submit a firewall request to open"},
    {"heritage_dc": "Any", "heritage_zone": "CAN", "new_dc": "Any", "prod_nonprod": "Non Prod",
     "new_dc_zone": "3PY", "action": "Blocked - Firewall Request Required",
     "reason": "CAN to Non-Prod 3PY is blocked by default; submit a firewall request to open"},
]

# --- 2) NGDC Prod Rules Matrix ---
# DC / Neighbourhood / Security Zone based permit/block rules
SEED_NGDC_PROD_MATRIX = [
    {"src_dc": "Any", "src_nh": "Any", "src_sz": "GEN", "dst_dc": "Any", "dst_nh": "Any", "dst_sz": "GEN",
     "action": "Permitted", "reason": "GEN-to-GEN traffic is permitted across all DCs and NHs"},
    {"src_dc": "Same", "src_nh": "Same", "src_sz": "Same", "dst_dc": "Same", "dst_nh": "Same", "dst_sz": "Same",
     "action": "Permitted", "reason": "Same DC + Same NH + Same SZ = Permitted"},
    {"src_dc": "Different", "src_nh": "Same", "src_sz": "Same", "dst_dc": "Different", "dst_nh": "Same", "dst_sz": "Same",
     "action": "Permitted", "reason": "Different DC + Same NH + Same SZ = Permitted (cross-DC HA)"},
    {"src_dc": "Same", "src_nh": "Same", "src_sz": "Different", "dst_dc": "Same", "dst_nh": "Same", "dst_sz": "Different",
     "action": "Blocked - Firewall Request Required",
     "reason": "Same DC + Same NH + Different SZ = Blocked; submit a firewall request to open"},
    {"src_dc": "Same", "src_nh": "Different", "src_sz": "Same", "dst_dc": "Same", "dst_nh": "Different", "dst_sz": "Same",
     "action": "Permitted", "reason": "Same DC + Different NH + Same SZ = Permitted"},
    {"src_dc": "Different", "src_nh": "Different", "src_sz": "Same", "dst_dc": "Different", "dst_nh": "Different", "dst_sz": "Same",
     "action": "Blocked - Firewall Request Required",
     "reason": "Different DC + Different NH + Same SZ = Blocked; submit a firewall request to open"},
    {"src_dc": "Same", "src_nh": "Non-Prod to PROD", "src_sz": "Any", "dst_dc": "Same", "dst_nh": "Non-Prod to PROD", "dst_sz": "Any",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod to PROD traffic is blocked; submit a firewall request to open"},
]

# --- 3) Non-Prod Rules Matrix ---
# Source zone to destination zone rules for non-production
SEED_NONPROD_MATRIX = [
    {"dc": "Any", "source_zone": "UGEN/USTD", "dest_zone": "UGEN/USTD",
     "action": "Permitted", "reason": "Non-Prod UGEN/USTD to Pre-Prod UGEN/USTD = Permitted"},
    {"dc": "Any", "source_zone": "UGEN/USTD", "dest_zone": "PAA/CCS/CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN/USTD to Pre-Prod PAA/CCS/CPA = Blocked; submit a firewall request"},
    {"dc": "Any", "source_zone": "UCCS", "dest_zone": "PAA/CCS/CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCCS to Pre-Prod PAA/CCS/CPA = Blocked; submit a firewall request"},
    {"dc": "Any", "source_zone": "UPAA", "dest_zone": "PAA/CCS/CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UPAA to Pre-Prod PAA/CCS/CPA = Blocked; submit a firewall request"},
    {"dc": "Any", "source_zone": "UCPA", "dest_zone": "PAA/CCS/CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCPA to Pre-Prod PAA/CCS/CPA = Blocked; submit a firewall request"},
    {"dc": "Any", "source_zone": "UCDE", "dest_zone": "PAA/CCS/CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCDE to Pre-Prod PAA/CCS/CPA = Blocked; submit a firewall request"},
]

# Combined policy matrix for backward compatibility (flat list used by API)
SEED_POLICY_MATRIX = [
    # Heritage DC rules (flattened)
    {"source_zone": "Default", "dest_zone": "Standard", "action": "Permitted",
     "matrix_type": "Heritage DC", "reason": "Heritage Default to NGDC Standard = Permitted"},
    {"source_zone": "PAA", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Heritage DC", "reason": "Heritage PAA to NGDC PAA = Blocked; submit firewall request to open"},
    {"source_zone": "PCI_CAN", "dest_zone": "CDE", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Heritage DC", "reason": "Heritage PCI CAN to NGDC CDE = Blocked; submit firewall request to open"},
    {"source_zone": "CAN", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Heritage DC", "reason": "Heritage CAN to NGDC CPA = Blocked; submit firewall request to open"},
    {"source_zone": "CAN", "dest_zone": "3PY", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Heritage DC", "reason": "Heritage CAN to NGDC 3PY = Blocked; submit firewall request to open"},
    # NGDC Prod rules (flattened)
    {"source_zone": "GEN", "dest_zone": "GEN", "action": "Permitted",
     "matrix_type": "NGDC Prod", "reason": "GEN-to-GEN across all DCs/NHs = Permitted"},
    {"source_zone": "CCS", "dest_zone": "CCS", "action": "Permitted",
     "matrix_type": "NGDC Prod", "reason": "Same DC + Same NH + Same SZ = Permitted"},
    {"source_zone": "CDE", "dest_zone": "CDE", "action": "Permitted",
     "matrix_type": "NGDC Prod", "reason": "Same DC + Same NH + Same SZ = Permitted"},
    {"source_zone": "CPA", "dest_zone": "CPA", "action": "Permitted",
     "matrix_type": "NGDC Prod", "reason": "Same DC + Same NH + Same SZ = Permitted"},
    {"source_zone": "CCS", "dest_zone": "CDE", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    {"source_zone": "CCS", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    {"source_zone": "CDE", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    {"source_zone": "CDE", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    {"source_zone": "CPA", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    {"source_zone": "CPA", "dest_zone": "CDE", "action": "Blocked - Firewall Request Required",
     "matrix_type": "NGDC Prod", "reason": "Same NH + Different SZ = Blocked; submit firewall request to open"},
    # Non-Prod rules (flattened)
    {"source_zone": "UGEN", "dest_zone": "UGEN", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "USTD", "dest_zone": "USTD", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "UGEN", "dest_zone": "USTD", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "USTD", "dest_zone": "UGEN", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "UGEN", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UGEN to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UGEN", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UGEN to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UGEN", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UGEN to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCCS", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCCS to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCCS", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCCS to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCCS", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCCS to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UPAA", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UPAA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UPAA", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UPAA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UPAA", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UPAA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCPA", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCPA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCPA", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCPA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCPA", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCPA to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCDE", "dest_zone": "PAA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCDE to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCDE", "dest_zone": "CCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCDE to PAA/CCS/CPA = Blocked; submit firewall request to open"},
    {"source_zone": "UCDE", "dest_zone": "CPA", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UCDE to PAA/CCS/CPA = Blocked; submit firewall request to open"},
]

SEED_ORG_CONFIG = {
    "org_name": "Acme Corporation",
    "org_code": "ACME",
    "servicenow_instance": "https://acme.service-now.com",
    "servicenow_api_path": "/api/now/table/change_request",
    "gitops_repo": "https://github.com/acme-network/firewall-policies.git",
    "gitops_branch": "main",
    "approval_workflow": "two-tier",
    "auto_certify_days": 365,
    "max_rule_expiry_days": 730,
    "notification_email": "firewall-ops@example.com",
    "notification_slack_channel": "#firewall-changes",
    "default_environment": "Production",
    "default_datacenter": "ALPHA_NGDC",
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
         "App Alpha to Primary DB", "CRM", "Deployed", True, -30),
        ("R-3002", "grp-DIG-NH03-CDE-WEB", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Delta to Transaction Processing", "DIG", "Certified", True, -15),
        ("R-3003", "grp-ENT-NH05-GEN-APP", "GEN", "grp-SHR-NH13-GEN-SVC", "GEN", "TCP 8080",
         "App Zeta to Shared Services", "ENT", "Pending Review", True, -5),
        ("R-3004", "grp-WHL-NH06-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Theta to Primary DB", "WHL", "Draft", True, -1),
        ("R-3005", "grp-PAY-NH07-CDE-APP", "CDE", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "App Epsilon to External API", "PAY", "Certified", False, -20),
        ("R-3006", "grp-DAT-NH08-GEN-APP", "GEN", "grp-ENT-NH05-GEN-APP", "GEN", "TCP 8443",
         "App Eta to Enterprise", "SHR", "Deployed", True, -45),
        ("R-3007", "192.168.1.10", "GEN", "grp-SHR-NH13-GEN-SVC", "GEN", "TCP 8443",
         "Single IP to Shared Services", "SHR", "Pending Review", False, -2),
        # --- HRM (HR Management) rules ---
        ("R-3008", "grp-HRM-NH01-GEN-WEB", "GEN", "grp-HRM-NH01-GEN-APP", "GEN", "TCP 8443",
         "App Nu Web to App Tier", "HRM", "Deployed", True, -90),
        ("R-3009", "grp-HRM-NH01-GEN-APP", "GEN", "grp-HRM-NH01-GEN-DB", "GEN", "TCP 5432",
         "App Nu App to Database", "HRM", "Deployed", True, -90),
        ("R-3010", "grp-HRM-NH01-GEN-BAT", "GEN", "grp-HRM-NH01-GEN-DB", "GEN", "TCP 5432",
         "App Nu Batch to DB", "HRM", "Certified", True, -60),
        # --- TRD (Trading Platform) rules ---
        ("R-3011", "grp-TRD-NH06-CDE-WEB", "CDE", "grp-TRD-NH06-CDE-APP", "CDE", "TCP 8443",
         "App Xi Web to App Tier", "TRD", "Deployed", True, -120),
        ("R-3012", "grp-TRD-NH06-CDE-APP", "CDE", "grp-TRD-NH06-CDE-DB", "CDE", "TCP 1521",
         "App Xi App to DB", "TRD", "Deployed", True, -120),
        ("R-3013", "grp-TRD-NH06-CDE-APP", "CDE", "grp-TRD-NH06-CDE-MQ", "CDE", "TCP 1414",
         "App Xi App to MQ Broker", "TRD", "Certified", True, -80),
        ("R-3014", "grp-TRD-NH06-CDE-APP", "CDE", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "App Xi to Market Data Feed", "TRD", "Certified", False, -50),
        # --- FRD (Fraud Detection) rules ---
        ("R-3015", "grp-FRD-NH02-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Omicron to Primary DB", "FRD", "Deployed", True, -100),
        ("R-3016", "grp-FRD-NH02-CDE-APP", "CDE", "grp-CCM-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Omicron to Card DB", "FRD", "Deployed", True, -100),
        ("R-3017", "grp-FRD-NH02-CDE-APP", "CDE", "grp-AML-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Omicron to Upsilon Integration", "FRD", "Certified", True, -40),
        # --- RGM (Regulatory Compliance) rules ---
        ("R-3018", "grp-RGM-NH11-RST-APP", "RST", "grp-RGM-NH11-RST-DB", "RST", "TCP 1521",
         "App Pi to Compliance DB", "RGM", "Deployed", True, -150),
        ("R-3019", "grp-RGM-NH11-RST-BAT", "RST", "grp-RGM-NH11-RST-DB", "RST", "TCP 1521",
         "App Pi Batch to DB", "RGM", "Certified", True, -75),
        # --- MBL (Mobile Banking) rules ---
        ("R-3020", "grp-MBL-NH03-CDE-API", "CDE", "grp-MBL-NH03-CDE-APP", "CDE", "TCP 8443",
         "App Rho API to App", "MBL", "Deployed", True, -200),
        ("R-3021", "grp-MBL-NH03-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Rho to Primary Banking", "MBL", "Deployed", True, -200),
        ("R-3022", "grp-MBL-NH03-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Rho to Payments", "MBL", "Certified", True, -100),
        ("R-3023", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-MBL-NH03-CDE-API", "CDE", "TCP 8443",
         "API Gateway to App Rho Backend", "MBL", "Pending Review", False, -3),
        # --- INS (Insurance Platform) rules ---
        ("R-3024", "grp-INS-NH04-GEN-WEB", "GEN", "grp-INS-NH04-GEN-APP", "GEN", "TCP 8443",
         "App Sigma Portal to App Tier", "INS", "Deployed", True, -85),
        ("R-3025", "grp-INS-NH04-GEN-APP", "GEN", "grp-INS-NH04-GEN-DB", "GEN", "TCP 5432",
         "App Sigma App to Claims DB", "INS", "Deployed", True, -85),
        # --- TAX (Tax Processing) rules ---
        ("R-3026", "grp-TAX-NH10-GEN-APP", "GEN", "grp-TAX-NH10-GEN-DB", "GEN", "TCP 5432",
         "App Tau Engine to DB", "TAX", "Certified", True, -55),
        ("R-3027", "grp-TAX-NH10-GEN-BAT", "GEN", "grp-TAX-NH10-GEN-DB", "GEN", "TCP 5432",
         "App Tau Batch to DB", "TAX", "Deployed", True, -110),
        # --- AML (Anti Money Laundering) rules ---
        ("R-3028", "grp-AML-NH07-CDE-APP", "CDE", "grp-AML-NH07-CDE-DB", "CDE", "TCP 1521",
         "App Upsilon Engine to DB", "AML", "Deployed", True, -130),
        ("R-3029", "grp-AML-NH07-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Upsilon to Transaction Monitoring", "AML", "Certified", True, -60),
        ("R-3030", "grp-AML-NH07-CDE-BAT", "CDE", "grp-RGM-NH11-RST-APP", "RST", "TCP 8443",
         "App Upsilon Batch to Reporting", "AML", "Pending Review", False, -7),
        # --- KYC (Know Your Customer) rules ---
        ("R-3031", "grp-KYC-NH05-GEN-WEB", "GEN", "grp-KYC-NH05-GEN-APP", "GEN", "TCP 8443",
         "App Phi Portal to Verification", "KYC", "Deployed", True, -95),
        ("R-3032", "grp-KYC-NH05-GEN-APP", "GEN", "grp-KYC-NH05-GEN-DB", "GEN", "TCP 5432",
         "App Phi Engine to Customer DB", "KYC", "Deployed", True, -95),
        ("R-3033", "grp-KYC-NH05-GEN-APP", "GEN", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "App Phi to External Verification API", "KYC", "Certified", False, -30),
        # --- TRS (Treasury Services) rules ---
        ("R-3034", "grp-TRS-NH06-CDE-APP", "CDE", "grp-TRS-NH06-CDE-DB", "CDE", "TCP 1521",
         "App Chi to Cash DB", "TRS", "Deployed", True, -140),
        ("R-3035", "grp-TRS-NH06-CDE-APP", "CDE", "grp-CBK-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Chi to Primary Ledger", "TRS", "Deployed", True, -140),
        ("R-3036", "grp-TRS-NH06-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Chi to Wire Transfers", "TRS", "Certified", True, -45),
        # --- CCM (Credit Card Management) rules ---
        ("R-3037", "grp-CCM-NH02-CDE-WEB", "CDE", "grp-CCM-NH02-CDE-APP", "CDE", "TCP 8443",
         "App Psi Portal to App", "CCM", "Deployed", True, -180),
        ("R-3038", "grp-CCM-NH02-CDE-APP", "CDE", "grp-CCM-NH02-CDE-DB", "CDE", "TCP 1521",
         "App Psi to Transaction DB", "CCM", "Deployed", True, -180),
        ("R-3039", "grp-CCM-NH02-CDE-APP", "CDE", "grp-PAY-NH07-CDE-APP", "CDE", "TCP 8443",
         "App Psi to Payment Auth", "CCM", "Certified", True, -70),
        ("R-3040", "grp-CCM-NH02-CDE-APP", "CDE", "grp-FRD-NH02-CDE-APP", "CDE", "TCP 8443",
         "App Psi to Fraud Scoring", "CCM", "Deployed", True, -160),
        # --- LON (Loan Origination) rules ---
        ("R-3041", "grp-LON-NH10-GEN-WEB", "GEN", "grp-LON-NH10-GEN-APP", "GEN", "TCP 8443",
         "App Omega Portal to Engine", "LON", "Deployed", True, -110),
        ("R-3042", "grp-LON-NH10-GEN-APP", "GEN", "grp-LON-NH10-GEN-DB", "GEN", "TCP 5432",
         "App Omega to Loan DB", "LON", "Deployed", True, -110),
        ("R-3043", "grp-LON-NH10-GEN-APP", "GEN", "grp-KYC-NH05-GEN-APP", "GEN", "TCP 8443",
         "App Omega to Verification", "LON", "Certified", True, -35),
        # --- BRK (Brokerage Services) rules ---
        ("R-3044", "grp-BRK-NH04-GEN-WEB", "GEN", "grp-BRK-NH04-GEN-APP", "GEN", "TCP 8443",
         "App Alpha2 Portal to Engine", "BRK", "Deployed", True, -160),
        ("R-3045", "grp-BRK-NH04-GEN-APP", "GEN", "grp-BRK-NH04-GEN-DB", "GEN", "TCP 5432",
         "App Alpha2 to Portfolio DB", "BRK", "Deployed", True, -160),
        ("R-3046", "grp-BRK-NH04-GEN-APP", "GEN", "grp-EXT-NH14-DMZ-API", "DMZ", "TCP 443",
         "App Alpha2 to Market Data", "BRK", "Certified", False, -25),
        # --- AGW (API Gateway) rules ---
        ("R-3047", "grp-AGW-NH14-DMZ-LB", "DMZ", "grp-AGW-NH14-DMZ-API", "DMZ", "TCP 443",
         "External LB to API Gateway", "AGW", "Deployed", True, -200),
        ("R-3048", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-DIG-NH03-CDE-WEB", "CDE", "TCP 8443",
         "API GW to Web App Backend", "AGW", "Deployed", False, -200),
        ("R-3049", "grp-AGW-NH14-DMZ-API", "DMZ", "grp-AGW-NH14-DMZ-MON", "DMZ", "TCP 9090",
         "API GW to Monitoring", "AGW", "Certified", True, -50),
        # --- SOC (Security Operations Center) rules ---
        ("R-3050", "grp-SOC-NH01-GEN-APP", "GEN", "grp-SOC-NH01-GEN-DB", "GEN", "TCP 9200",
         "Log Collector to Search DB", "SOC", "Deployed", True, -250),
        ("R-3051", "grp-SOC-NH01-GEN-MON", "GEN", "grp-MGT-NH01-MGT-MON", "MGT", "TCP 8443",
         "Monitoring to Management Plane", "SOC", "Deployed", False, -250),
        ("R-3052", "grp-SOC-NH01-GEN-APP", "GEN", "grp-SOC-NH01-GEN-APP", "GEN", "TCP 514",
         "Log Aggregation within Monitoring", "SOC", "Certified", True, -120),
        # --- Legacy non-standard rules for migration ---
        ("R-3053", "10.25.10.0/24", "CDE", "10.25.20.0/24", "CDE", "TCP 1521",
         "Legacy DC Alpha DB Traffic", "CRM", "Deployed", False, -365),
        ("R-3054", "10.26.5.0/24", "GEN", "10.26.15.0/24", "GEN", "TCP 8443",
         "Legacy DC Beta App Traffic", "HRM", "Deployed", False, -300),
        ("R-3055", "10.27.1.0/24", "CDE", "10.27.2.0/24", "CDE", "TCP 443",
         "Legacy DC Gamma Web to App", "TRD", "Deployed", False, -280),
        ("R-3056", "10.28.10.0/24", "GEN", "10.28.20.0/24", "GEN", "TCP 5432",
         "Legacy DC Delta App to DB", "INS", "Deployed", False, -350),
        ("R-3057", "svr-10.29.1.50", "CDE", "10.29.2.0/24", "CDE", "TCP 1521",
         "Legacy DC Epsilon Single Server", "FRD", "Deployed", False, -400),
        ("R-3058", "10.30.5.0/24", "GEN", "10.30.10.0/24", "GEN", "TCP 8080",
         "Legacy DC Zeta App Traffic", "KYC", "Deployed", False, -320),
    ]
    for rid, src, sz_s, dst, sz_d, port, desc, app, st, g2g, days in defs:
        ct = (base + timedelta(days=days)).isoformat()
        rules.append({
            "rule_id": rid, "source": src, "source_zone": sz_s, "destination": dst,
            "destination_zone": sz_d, "port": port, "protocol": port.split(" ")[0],
            "action": "Allow", "description": desc, "application": app, "status": st,
            "is_group_to_group": g2g, "environment": "Production", "datacenter": "ALPHA_NGDC",
            "created_at": ct, "updated_at": ct,
            "certified_date": ct if st in ("Certified", "Deployed") else None,
            "expiry_date": (base + timedelta(days=365)).isoformat() if st in ("Certified", "Deployed") else None,
        })
    return rules


SEED_MIGRATIONS = [
    {"migration_id": "mig-001", "name": "Legacy DC Alpha to Gamma NGDC Wave 1",
     "application": "CRM", "source_legacy_dc": "DC_LEGACY_A", "target_ngdc": "GAMMA_NGDC",
     "legacy_dc": "DC_LEGACY_A", "target_dc": "GAMMA_NGDC",
     "status": "In Progress", "progress": 35,
     "total_rules": 45, "migrated_rules": 16, "failed_rules": 2,
     "created_at": (datetime.utcnow() + timedelta(days=-60)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-002", "name": "Legacy DC Beta to Alpha NGDC Wave 1",
     "application": "HRM", "source_legacy_dc": "DC_LEGACY_B", "target_ngdc": "ALPHA_NGDC",
     "legacy_dc": "DC_LEGACY_B", "target_dc": "ALPHA_NGDC",
     "status": "In Progress", "progress": 60,
     "total_rules": 32, "migrated_rules": 19, "failed_rules": 1,
     "created_at": (datetime.utcnow() + timedelta(days=-45)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-003", "name": "Legacy DC Gamma App Migration",
     "application": "TRD", "source_legacy_dc": "DC_LEGACY_C", "target_ngdc": "BETA_NGDC",
     "legacy_dc": "DC_LEGACY_C", "target_dc": "BETA_NGDC",
     "status": "Planning", "progress": 10,
     "total_rules": 58, "migrated_rules": 0, "failed_rules": 0,
     "created_at": (datetime.utcnow() + timedelta(days=-15)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-004", "name": "Legacy DC Delta App Migration",
     "application": "INS", "source_legacy_dc": "DC_LEGACY_D", "target_ngdc": "ALPHA_NGDC",
     "legacy_dc": "DC_LEGACY_D", "target_dc": "ALPHA_NGDC",
     "status": "In Progress", "progress": 45,
     "total_rules": 28, "migrated_rules": 12, "failed_rules": 3,
     "created_at": (datetime.utcnow() + timedelta(days=-30)).isoformat(),
     "updated_at": _now()},
    {"migration_id": "mig-005", "name": "Legacy DC Epsilon Systems Migration",
     "application": "FRD", "source_legacy_dc": "DC_LEGACY_E", "target_ngdc": "ALPHA_NGDC",
     "legacy_dc": "DC_LEGACY_E", "target_dc": "ALPHA_NGDC",
     "status": "Completed", "progress": 100,
     "total_rules": 22, "migrated_rules": 22, "failed_rules": 0,
     "created_at": (datetime.utcnow() + timedelta(days=-90)).isoformat(),
     "updated_at": (datetime.utcnow() + timedelta(days=-10)).isoformat()},
    {"migration_id": "mig-006", "name": "Legacy DC Zeta App Migration",
     "application": "KYC", "source_legacy_dc": "DC_LEGACY_F", "target_ngdc": "ALPHA_NGDC",
     "legacy_dc": "DC_LEGACY_F", "target_dc": "ALPHA_NGDC",
     "status": "In Progress", "progress": 25,
     "total_rules": 38, "migrated_rules": 9, "failed_rules": 1,
     "created_at": (datetime.utcnow() + timedelta(days=-20)).isoformat(),
     "updated_at": _now()},
]

SEED_MIGRATION_MAPPINGS = [
    # --- mig-001: CRM from DC Legacy A ---
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
    # --- mig-002: HRM from DC Legacy B ---
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
    # --- mig-003: TRD from DC Legacy C ---
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
    # --- mig-004: INS from DC Legacy D ---
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
    # --- mig-005: FRD from DC Legacy E (completed) ---
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
    # --- mig-006: KYC from DC Legacy F ---
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
     "description": "App Alpha Application Servers", "members": [
        {"type": "ip", "value": "10.1.1.10", "description": "Alpha App Server 1"},
        {"type": "ip", "value": "10.1.1.11", "description": "Alpha App Server 2"},
        {"type": "ip", "value": "10.1.1.12", "description": "Alpha App Server 3"},
     ]},
    {"name": "grp-CRM-NH02-CDE-DB", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "App Alpha Database Servers", "members": [
        {"type": "ip", "value": "10.1.2.10", "description": "Alpha DB Primary"},
        {"type": "ip", "value": "10.1.2.11", "description": "Alpha DB Standby"},
     ]},
    # CBK groups
    {"name": "grp-CBK-NH02-CDE-DB", "app_id": "CBK", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "Primary Database Cluster", "members": [
        {"type": "ip", "value": "10.1.2.20", "description": "Iota DB Primary"},
        {"type": "ip", "value": "10.1.2.21", "description": "Iota DB Standby"},
        {"type": "cidr", "value": "10.1.2.64/28", "description": "Iota DB Pool"},
     ]},
    # DIG groups
    {"name": "grp-DIG-NH03-CDE-WEB", "app_id": "DIG", "nh": "NH03", "sz": "CDE", "subtype": "WEB",
     "description": "App Delta Web Servers", "members": [
        {"type": "ip", "value": "10.2.1.10", "description": "Delta Web 1"},
        {"type": "ip", "value": "10.2.1.11", "description": "Delta Web 2"},
     ]},
    # PAY groups
    {"name": "grp-PAY-NH07-CDE-APP", "app_id": "PAY", "nh": "NH07", "sz": "CDE", "subtype": "APP",
     "description": "Transaction Processing Servers", "members": [
        {"type": "ip", "value": "10.6.1.10", "description": "Epsilon App 1"},
        {"type": "ip", "value": "10.6.1.11", "description": "Epsilon App 2"},
        {"type": "cidr", "value": "10.6.1.64/28", "description": "Epsilon App Pool"},
     ]},
    # ENT groups
    {"name": "grp-ENT-NH05-GEN-APP", "app_id": "ENT", "nh": "NH05", "sz": "GEN", "subtype": "APP",
     "description": "App Zeta Application Servers", "members": [
        {"type": "ip", "value": "10.4.1.10", "description": "Zeta App 1"},
        {"type": "ip", "value": "10.4.1.11", "description": "Zeta App 2"},
     ]},
    # SHR groups
    {"name": "grp-SHR-NH13-GEN-SVC", "app_id": "SHR", "nh": "NH13", "sz": "GEN", "subtype": "SVC",
     "description": "Shared Analytics Services", "members": [
        {"type": "cidr", "value": "10.100.1.0/28", "description": "Shared SVC Subnet"},
     ]},
    # HRM groups
    {"name": "grp-HRM-NH01-GEN-WEB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "WEB",
     "description": "App Nu Web Servers", "members": [
        {"type": "ip", "value": "10.0.1.10", "description": "Nu Web 1"},
        {"type": "ip", "value": "10.0.1.11", "description": "Nu Web 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-APP", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "App Nu Application Servers", "members": [
        {"type": "ip", "value": "10.0.1.20", "description": "Nu App 1"},
        {"type": "ip", "value": "10.0.1.21", "description": "Nu App 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-DB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "DB",
     "description": "App Nu Database", "members": [
        {"type": "ip", "value": "10.0.1.30", "description": "Nu DB Primary"},
        {"type": "ip", "value": "10.0.1.31", "description": "Nu DB Replica"},
     ]},
    {"name": "grp-HRM-NH01-GEN-BAT", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "BAT",
     "description": "App Nu Batch Servers", "members": [
        {"type": "ip", "value": "10.0.1.40", "description": "Nu Batch 1"},
     ]},
    # TRD groups
    {"name": "grp-TRD-NH06-CDE-WEB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "WEB",
     "description": "App Xi Web Tier", "members": [
        {"type": "ip", "value": "10.5.1.10", "description": "Xi Web 1"},
        {"type": "ip", "value": "10.5.1.11", "description": "Xi Web 2"},
     ]},
    {"name": "grp-TRD-NH06-CDE-APP", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "APP",
     "description": "App Xi Application Servers", "members": [
        {"type": "ip", "value": "10.5.1.20", "description": "Xi App 1"},
        {"type": "ip", "value": "10.5.1.21", "description": "Xi App 2"},
        {"type": "ip", "value": "10.5.1.22", "description": "Xi App 3"},
     ]},
    {"name": "grp-TRD-NH06-CDE-DB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "DB",
     "description": "App Xi Database", "members": [
        {"type": "ip", "value": "10.5.1.30", "description": "Xi DB Primary"},
        {"type": "ip", "value": "10.5.1.31", "description": "Xi DB Standby"},
     ]},
    {"name": "grp-TRD-NH06-CDE-MQ", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "MQ",
     "description": "App Xi MQ Broker", "members": [
        {"type": "ip", "value": "10.5.1.40", "description": "Xi MQ Broker 1"},
     ]},
    # FRD groups
    {"name": "grp-FRD-NH02-CDE-APP", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "App Omicron Detection Engine", "members": [
        {"type": "ip", "value": "10.1.1.50", "description": "Omicron Engine 1"},
        {"type": "ip", "value": "10.1.1.51", "description": "Omicron Engine 2"},
     ]},
    # AGW groups
    {"name": "grp-AGW-NH14-DMZ-API", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "API Gateway Servers", "members": [
        {"type": "ip", "value": "10.70.1.10", "description": "Beta2 API 1"},
        {"type": "ip", "value": "10.70.1.11", "description": "Beta2 API 2"},
     ]},
    {"name": "grp-AGW-NH14-DMZ-LB", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "LB",
     "description": "API Gateway Load Balancer", "members": [
        {"type": "ip", "value": "10.70.1.5", "description": "Beta2 LB VIP"},
     ]},
    # EXT group (DMZ external API)
    {"name": "grp-EXT-NH14-DMZ-API", "app_id": "EXT", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "External API Endpoints", "members": [
        {"type": "cidr", "value": "10.70.2.0/28", "description": "External API Subnet"},
     ]},
    # MBL groups
    {"name": "grp-MBL-NH03-CDE-API", "app_id": "MBL", "nh": "NH03", "sz": "CDE", "subtype": "API",
     "description": "App Rho API", "members": [
        {"type": "ip", "value": "10.2.1.50", "description": "Rho API 1"},
        {"type": "ip", "value": "10.2.1.51", "description": "Rho API 2"},
     ]},
    {"name": "grp-MBL-NH03-CDE-APP", "app_id": "MBL", "nh": "NH03", "sz": "CDE", "subtype": "APP",
     "description": "App Rho App Servers", "members": [
        {"type": "ip", "value": "10.2.2.10", "description": "Rho App 1"},
        {"type": "ip", "value": "10.2.2.11", "description": "Rho App 2"},
     ]},
    # SOC groups
    {"name": "grp-SOC-NH01-GEN-APP", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "Log Collectors", "members": [
        {"type": "ip", "value": "10.0.2.10", "description": "Gamma2 Collector 1"},
        {"type": "ip", "value": "10.0.2.11", "description": "Gamma2 Collector 2"},
     ]},
    {"name": "grp-SOC-NH01-GEN-DB", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "DB",
     "description": "Search DB Cluster", "members": [
        {"type": "ip", "value": "10.0.2.20", "description": "Gamma2 DB Node 1"},
        {"type": "ip", "value": "10.0.2.21", "description": "Gamma2 DB Node 2"},
        {"type": "ip", "value": "10.0.2.22", "description": "Gamma2 DB Node 3"},
     ]},
    {"name": "grp-SOC-NH01-GEN-MON", "app_id": "SOC", "nh": "NH01", "sz": "GEN", "subtype": "MON",
     "description": "Monitoring Agents", "members": [
        {"type": "cidr", "value": "10.0.2.64/28", "description": "Gamma2 Mon Subnet"},
     ]},
]

SEED_CHG_REQUESTS = [
    {"chg_id": "CHG10001", "rule_ids": ["R-3001"], "status": "Approved",
     "description": "Deploy App Alpha to Primary DB rule",
     "requested_by": "Owner A", "approved_by": "Security Team",
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
    _save("heritage_dc_matrix", deepcopy(SEED_HERITAGE_DC_MATRIX))
    _save("ngdc_prod_matrix", deepcopy(SEED_NGDC_PROD_MATRIX))
    _save("nonprod_matrix", deepcopy(SEED_NONPROD_MATRIX))
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


async def get_heritage_dc_matrix() -> list[dict[str, Any]]:
    return _load("heritage_dc_matrix") or []


async def get_ngdc_prod_matrix() -> list[dict[str, Any]]:
    return _load("ngdc_prod_matrix") or []


async def get_nonprod_matrix() -> list[dict[str, Any]]:
    return _load("nonprod_matrix") or []


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
    matched_matrix = ""
    for p in policy_matrix:
        if p.get("source_zone") == source_zone and p.get("dest_zone") == dest_zone:
            policy = p
            matched_matrix = p.get("matrix_type", "")
            break

    details: list[str] = []
    firewall_request_required = False
    if policy:
        result = policy.get("action", "Permitted")
        requires_exception = "Exception" in result
        firewall_request_required = "Firewall Request Required" in result
        if matched_matrix:
            details.append(f"Matrix: {matched_matrix}")
        details.append(f"Policy: {source_zone} -> {dest_zone} = {result}")
        if firewall_request_required:
            details.append("Action: Submit a new Firewall Request to open this traffic flow")
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
        "matrix_type": matched_matrix,
        "ngdc_zone_check": True,
        "birthright_compliant": not requires_exception and not firewall_request_required,
        "firewall_request_required": firewall_request_required,
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
