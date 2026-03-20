"""Seed data definitions for the Network Firewall Studio.

All reference data constants are defined here and imported by database.py.
This keeps the seed data separate from the database logic.
"""

from datetime import datetime, timedelta
from typing import Any


# ============================================================
# Neighbourhoods
# ============================================================

SEED_NEIGHBOURHOODS = [
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


# ============================================================
# Security Zones
# ============================================================

SEED_SECURITY_ZONES = [
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
    {"code": "MGT", "name": "Management", "description": "Network management and monitoring zone",
     "risk_level": "High", "pci_scope": False, "zone_type": "Infrastructure", "ip_ranges": [
        {"cidr": "10.200.1.0/24", "description": "MGT East", "dc": "ALPHA_NGDC"},
     ]},
    {"code": "EXT", "name": "External Partners", "description": "External partner connectivity zone",
     "risk_level": "High", "pci_scope": False, "zone_type": "External", "ip_ranges": [
        {"cidr": "10.79.1.0/24", "description": "EXT East", "dc": "ALPHA_NGDC"},
     ]},
]


# ============================================================
# Datacenters
# ============================================================

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


# ============================================================
# Applications
# ============================================================

SEED_APPLICATIONS = [
    {"app_id": "CRM", "app_distributed_id": "SEA3", "name": "App Alpha", "owner": "Owner A", "team": "Team Alpha",
     "nh": "NH02", "sz": "CDE", "criticality": 2, "pci_scope": True, "description": "Application alpha system"},
    {"app_id": "ORD", "app_distributed_id": "LOGIN", "name": "App Beta", "owner": "Jon", "team": "Team Beta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application beta platform"},
    {"app_id": "PSA", "app_distributed_id": "PSA01", "name": "App Gamma", "owner": "Owner A", "team": "Team Gamma",
     "nh": "NH05", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application gamma automation"},
    {"app_id": "DIG", "app_distributed_id": "DIG01", "name": "App Delta", "owner": "Jon", "team": "Team Delta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application delta platform"},
    {"app_id": "PAY", "app_distributed_id": "PAY01", "name": "App Epsilon", "owner": "Owner A", "team": "Team Epsilon",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application epsilon engine"},
    {"app_id": "ENT", "app_distributed_id": "ENT01", "name": "App Zeta", "owner": "Jon", "team": "Team Gamma",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application zeta system"},
    {"app_id": "SHR", "app_distributed_id": "SHR01", "name": "App Eta", "owner": "Owner A", "team": "Team Eta",
     "nh": "NH08", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application eta platform"},
    {"app_id": "WHL", "app_distributed_id": "WHL01", "name": "Team Theta", "owner": "Jon", "team": "Team Theta",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application theta system"},
    {"app_id": "CBK", "app_distributed_id": "CBK01", "name": "Team Iota", "owner": "Owner A", "team": "Team Iota",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application iota ledger"},
    {"app_id": "CLN", "app_distributed_id": "CLN01", "name": "Team Kappa", "owner": "Jon", "team": "Team Kappa",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application kappa origination"},
    {"app_id": "WLT", "app_distributed_id": "WLT01", "name": "App Lambda", "owner": "Owner A", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application lambda advisory"},
    {"app_id": "ACH", "app_distributed_id": "ACH01", "name": "Team Mu", "owner": "Jon", "team": "Team Mu",
     "nh": "NH09", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application mu services"},
    {"app_id": "HRM", "app_distributed_id": "HRM01", "name": "App Nu", "owner": "Owner B", "team": "Team Nu",
     "nh": "NH01", "sz": "GEN", "criticality": 3, "pci_scope": False, "description": "Application nu management"},
    {"app_id": "TRD", "app_distributed_id": "TRD01", "name": "App Xi", "owner": "Owner C", "team": "Team Xi",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application xi processing"},
    {"app_id": "FRD", "app_distributed_id": "FRD01", "name": "App Omicron", "owner": "Owner D", "team": "Team Omicron",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application omicron detection"},
    {"app_id": "RGM", "app_distributed_id": "RGM01", "name": "App Pi", "owner": "Owner E", "team": "Team Pi",
     "nh": "NH11", "sz": "RST", "criticality": 1, "pci_scope": True, "description": "Application pi reporting"},
    {"app_id": "MBL", "app_distributed_id": "MBL01", "name": "App Rho", "owner": "Owner F", "team": "Team Delta",
     "nh": "NH03", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application rho mobile app"},
    {"app_id": "INS", "app_distributed_id": "INS01", "name": "App Sigma", "owner": "Owner G", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application sigma underwriting"},
    {"app_id": "TAX", "app_distributed_id": "TAX01", "name": "App Tau", "owner": "Owner H", "team": "Team Tau",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application tau calculation"},
    {"app_id": "AML", "app_distributed_id": "AML01", "name": "App Upsilon", "owner": "Owner I", "team": "Team Omicron",
     "nh": "NH07", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application upsilon screening"},
    {"app_id": "KYC", "app_distributed_id": "KYC01", "name": "App Phi", "owner": "Owner J", "team": "Team Pi",
     "nh": "NH05", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application phi verification"},
    {"app_id": "TRS", "app_distributed_id": "TRS01", "name": "App Chi", "owner": "Owner K", "team": "Team Chi",
     "nh": "NH06", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application chi management"},
    {"app_id": "CCM", "app_distributed_id": "CCM01", "name": "App Psi", "owner": "Owner L", "team": "Team Psi",
     "nh": "NH02", "sz": "CDE", "criticality": 1, "pci_scope": True, "description": "Application psi processing"},
    {"app_id": "LON", "app_distributed_id": "LON01", "name": "App Omega", "owner": "Owner M", "team": "Team Kappa",
     "nh": "NH10", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application omega underwriting"},
    {"app_id": "BRK", "app_distributed_id": "BRK01", "name": "App Alpha2", "owner": "Owner N", "team": "Team Lambda",
     "nh": "NH04", "sz": "GEN", "criticality": 2, "pci_scope": False, "description": "Application alpha2 platform"},
    {"app_id": "AGW", "app_distributed_id": "AGW01", "name": "App Beta2", "owner": "Owner O", "team": "Team Beta2",
     "nh": "NH14", "sz": "DMZ", "criticality": 1, "pci_scope": False, "description": "Application beta2 gateway"},
    {"app_id": "SOC", "app_distributed_id": "SOC01", "name": "App Gamma2", "owner": "Owner P", "team": "Team Gamma2",
     "nh": "NH01", "sz": "GEN", "criticality": 1, "pci_scope": False, "description": "Application gamma2 monitoring"},
]


# ============================================================
# Legacy rules (populated via Excel import only)
# ============================================================

SEED_LEGACY_RULES: list[dict[str, Any]] = []


# ============================================================
# Environments
# ============================================================

SEED_ENVIRONMENTS = [
    {"name": "Production", "code": "PROD", "description": "Live production environment"},
    {"name": "Non-Production", "code": "NON-PROD", "description": "Shared non-production for testing"},
    {"name": "Pre-Production", "code": "PRE-PROD", "description": "Staging environment"},
    {"name": "Development", "code": "DEV", "description": "Development and sandbox"},
    {"name": "Staging", "code": "STG", "description": "Final validation before production"},
    {"name": "DR", "code": "DR", "description": "Disaster recovery"},
]


# ============================================================
# Predefined Destinations
# ============================================================

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


# ============================================================
# Naming Standards
# ============================================================

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


# ============================================================
# Policy Matrices
# ============================================================

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

SEED_NONPROD_MATRIX = [
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "UGEN",
     "action": "Permitted", "reason": "Non-Prod UGEN to Non-Prod UGEN = Permitted"},
    {"dc": "Any", "source_zone": "USTD", "dest_zone": "USTD",
     "action": "Permitted", "reason": "Non-Prod USTD to Non-Prod USTD = Permitted"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "USTD",
     "action": "Permitted", "reason": "Non-Prod UGEN to Non-Prod USTD = Permitted"},
    {"dc": "Any", "source_zone": "USTD", "dest_zone": "UGEN",
     "action": "Permitted", "reason": "Non-Prod USTD to Non-Prod UGEN = Permitted"},
    {"dc": "Any", "source_zone": "UCCS", "dest_zone": "UCCS",
     "action": "Permitted", "reason": "Non-Prod UCCS to Non-Prod UCCS = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "UPAA", "dest_zone": "UPAA",
     "action": "Permitted", "reason": "Non-Prod UPAA to Non-Prod UPAA = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "UCPA", "dest_zone": "UCPA",
     "action": "Permitted", "reason": "Non-Prod UCPA to Non-Prod UCPA = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "UCDE", "dest_zone": "UCDE",
     "action": "Permitted", "reason": "Non-Prod UCDE to Non-Prod UCDE = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "UCCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Non-Prod UCCS = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "UPAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Non-Prod UPAA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "UCPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Non-Prod UCPA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "UCDE",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Non-Prod UCDE = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Pre-Prod CCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UGEN", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UGEN to Pre-Prod CPA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "USTD", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod USTD to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCCS", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCCS to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCCS", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCCS to Pre-Prod CCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCCS", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCCS to Pre-Prod CPA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UPAA", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UPAA to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UPAA", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UPAA to Pre-Prod CCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UPAA", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UPAA to Pre-Prod CPA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCPA", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCPA to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCPA", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCPA to Pre-Prod CCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCPA", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCPA to Pre-Prod CPA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCDE", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCDE to Pre-Prod PAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCDE", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCDE to Pre-Prod CCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "UCDE", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Non-Prod UCDE to Pre-Prod CPA = Blocked; cross-environment"},
]

SEED_PREPROD_MATRIX = [
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "GEN",
     "action": "Permitted", "reason": "Pre-Prod GEN to Pre-Prod GEN = Permitted"},
    {"dc": "Any", "source_zone": "STD", "dest_zone": "STD",
     "action": "Permitted", "reason": "Pre-Prod STD to Pre-Prod STD = Permitted"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "STD",
     "action": "Permitted", "reason": "Pre-Prod GEN to Pre-Prod STD = Permitted"},
    {"dc": "Any", "source_zone": "STD", "dest_zone": "GEN",
     "action": "Permitted", "reason": "Pre-Prod STD to Pre-Prod GEN = Permitted"},
    {"dc": "Any", "source_zone": "PAA", "dest_zone": "PAA",
     "action": "Permitted", "reason": "Pre-Prod PAA to Pre-Prod PAA = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "CCS", "dest_zone": "CCS",
     "action": "Permitted", "reason": "Pre-Prod CCS to Pre-Prod CCS = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "CPA", "dest_zone": "CPA",
     "action": "Permitted", "reason": "Pre-Prod CPA to Pre-Prod CPA = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "CDE", "dest_zone": "CDE",
     "action": "Permitted", "reason": "Pre-Prod CDE to Pre-Prod CDE = Permitted (same SZ)"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "PAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod GEN to Pre-Prod PAA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod GEN to Pre-Prod CCS = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod GEN to Pre-Prod CPA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "CDE",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod GEN to Pre-Prod CDE = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "PAA", "dest_zone": "CCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod PAA to Pre-Prod CCS = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "PAA", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod PAA to Pre-Prod CPA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "CCS", "dest_zone": "CPA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod CCS to Pre-Prod CPA = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "CCS", "dest_zone": "CDE",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod CCS to Pre-Prod CDE = Blocked; different security zones"},
    {"dc": "Any", "source_zone": "GEN", "dest_zone": "UGEN",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod GEN to Non-Prod UGEN = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "PAA", "dest_zone": "UPAA",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod PAA to Non-Prod UPAA = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "CCS", "dest_zone": "UCCS",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod CCS to Non-Prod UCCS = Blocked; cross-environment"},
    {"dc": "Any", "source_zone": "Any", "dest_zone": "Any",
     "action": "Blocked - Firewall Request Required",
     "reason": "Pre-Prod to Prod traffic is blocked; submit a firewall request to open",
     "cross_env": "Pre-Prod to Prod"},
]

SEED_POLICY_MATRIX = [
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
    {"source_zone": "UGEN", "dest_zone": "UGEN", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "USTD", "dest_zone": "USTD", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "UGEN", "dest_zone": "USTD", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "USTD", "dest_zone": "UGEN", "action": "Permitted",
     "matrix_type": "Non-Prod", "reason": "UGEN/USTD to UGEN/USTD = Permitted"},
    {"source_zone": "UGEN", "dest_zone": "UCCS", "action": "Blocked - Firewall Request Required",
     "matrix_type": "Non-Prod", "reason": "UGEN to UCCS = Blocked; different security zones"},
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


# ============================================================
# Org Config
# ============================================================

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


# ============================================================
# One-to-One IP Mapping: Legacy DC to NGDC
# Maps legacy IP ranges to their NGDC equivalents for migration
# ============================================================

SEED_IP_MAPPINGS = [
    # DC_LEGACY_A (10.25.x.x) -> GAMMA_NGDC
    {"legacy_dc": "DC_LEGACY_A", "ngdc_dc": "GAMMA_NGDC", "app_id": "CRM",
     "legacy_ip": "10.25.1.0/24", "ngdc_ip": "10.50.1.10/32", "ngdc_group": "grp-CRM-NH02-CDE-APP",
     "legacy_desc": "CRM App Servers (Legacy A)", "ngdc_desc": "CRM App Servers (Gamma NGDC)",
     "nh": "NH02", "sz": "CDE"},
    {"legacy_dc": "DC_LEGACY_A", "ngdc_dc": "GAMMA_NGDC", "app_id": "CRM",
     "legacy_ip": "10.25.2.0/24", "ngdc_ip": "10.50.1.20/32", "ngdc_group": "grp-CRM-NH02-CDE-DB",
     "legacy_desc": "CRM DB Servers (Legacy A)", "ngdc_desc": "CRM DB Servers (Gamma NGDC)",
     "nh": "NH02", "sz": "CDE"},
    # DC_LEGACY_B (10.26.x.x) -> ALPHA_NGDC
    {"legacy_dc": "DC_LEGACY_B", "ngdc_dc": "ALPHA_NGDC", "app_id": "HRM",
     "legacy_ip": "10.26.5.0/24", "ngdc_ip": "10.0.1.10/32", "ngdc_group": "grp-HRM-NH01-GEN-APP",
     "legacy_desc": "HRM App Servers (Legacy B)", "ngdc_desc": "HRM App Servers (Alpha NGDC)",
     "nh": "NH01", "sz": "GEN"},
    {"legacy_dc": "DC_LEGACY_B", "ngdc_dc": "ALPHA_NGDC", "app_id": "HRM",
     "legacy_ip": "10.26.15.0/24", "ngdc_ip": "10.0.1.30/32", "ngdc_group": "grp-HRM-NH01-GEN-DB",
     "legacy_desc": "HRM DB Servers (Legacy B)", "ngdc_desc": "HRM DB Servers (Alpha NGDC)",
     "nh": "NH01", "sz": "GEN"},
    # DC_LEGACY_C (10.27.x.x) -> BETA_NGDC
    {"legacy_dc": "DC_LEGACY_C", "ngdc_dc": "BETA_NGDC", "app_id": "TRD",
     "legacy_ip": "10.27.1.0/24", "ngdc_ip": "172.16.20.10/32", "ngdc_group": "grp-TRD-NH06-CDE-WEB",
     "legacy_desc": "TRD Web Servers (Legacy C)", "ngdc_desc": "TRD Web Servers (Beta NGDC)",
     "nh": "NH06", "sz": "CDE"},
    {"legacy_dc": "DC_LEGACY_C", "ngdc_dc": "BETA_NGDC", "app_id": "TRD",
     "legacy_ip": "10.27.2.0/24", "ngdc_ip": "172.16.20.20/32", "ngdc_group": "grp-TRD-NH06-CDE-APP",
     "legacy_desc": "TRD App Servers (Legacy C)", "ngdc_desc": "TRD App Servers (Beta NGDC)",
     "nh": "NH06", "sz": "CDE"},
    # DC_LEGACY_D (10.28.x.x) -> ALPHA_NGDC
    {"legacy_dc": "DC_LEGACY_D", "ngdc_dc": "ALPHA_NGDC", "app_id": "INS",
     "legacy_ip": "10.28.10.0/24", "ngdc_ip": "10.3.1.10/32", "ngdc_group": "grp-INS-NH04-GEN-APP",
     "legacy_desc": "INS App Servers (Legacy D)", "ngdc_desc": "INS App Servers (Alpha NGDC)",
     "nh": "NH04", "sz": "GEN"},
    {"legacy_dc": "DC_LEGACY_D", "ngdc_dc": "ALPHA_NGDC", "app_id": "INS",
     "legacy_ip": "10.28.20.0/24", "ngdc_ip": "10.3.1.20/32", "ngdc_group": "grp-INS-NH04-GEN-DB",
     "legacy_desc": "INS DB Servers (Legacy D)", "ngdc_desc": "INS DB Servers (Alpha NGDC)",
     "nh": "NH04", "sz": "GEN"},
    # DC_LEGACY_E (10.29.x.x) -> ALPHA_NGDC
    {"legacy_dc": "DC_LEGACY_E", "ngdc_dc": "ALPHA_NGDC", "app_id": "FRD",
     "legacy_ip": "10.29.1.50/32", "ngdc_ip": "10.1.1.50/32", "ngdc_group": "grp-FRD-NH02-CDE-APP",
     "legacy_desc": "FRD Detection Engine (Legacy E)", "ngdc_desc": "FRD Detection Engine (Alpha NGDC)",
     "nh": "NH02", "sz": "CDE"},
    {"legacy_dc": "DC_LEGACY_E", "ngdc_dc": "ALPHA_NGDC", "app_id": "FRD",
     "legacy_ip": "10.29.2.0/24", "ngdc_ip": "10.1.2.20/32", "ngdc_group": "grp-CBK-NH02-CDE-DB",
     "legacy_desc": "FRD DB Servers (Legacy E)", "ngdc_desc": "FRD/CBK DB Servers (Alpha NGDC)",
     "nh": "NH02", "sz": "CDE"},
    # DC_LEGACY_F (10.30.x.x) -> ALPHA_NGDC
    {"legacy_dc": "DC_LEGACY_F", "ngdc_dc": "ALPHA_NGDC", "app_id": "KYC",
     "legacy_ip": "10.30.5.0/24", "ngdc_ip": "10.4.1.10/32", "ngdc_group": "grp-KYC-NH05-GEN-APP",
     "legacy_desc": "KYC App Servers (Legacy F)", "ngdc_desc": "KYC App Servers (Alpha NGDC)",
     "nh": "NH05", "sz": "GEN"},
    {"legacy_dc": "DC_LEGACY_F", "ngdc_dc": "ALPHA_NGDC", "app_id": "KYC",
     "legacy_ip": "10.30.10.0/24", "ngdc_ip": "10.4.2.10/32", "ngdc_group": "grp-KYC-NH05-GEN-DB",
     "legacy_desc": "KYC DB Servers (Legacy F)", "ngdc_desc": "KYC DB Servers (Alpha NGDC)",
     "nh": "NH05", "sz": "GEN"},
]


# ============================================================
# Groups
# ============================================================

SEED_GROUPS = [
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
    {"name": "grp-CBK-NH02-CDE-DB", "app_id": "CBK", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "Primary Database Cluster", "members": [
        {"type": "ip", "value": "10.1.2.20", "description": "Iota DB Primary"},
        {"type": "ip", "value": "10.1.2.21", "description": "Iota DB Standby"},
        {"type": "cidr", "value": "10.1.2.64/28", "description": "Iota DB Pool"},
     ]},
    {"name": "grp-DIG-NH03-CDE-WEB", "app_id": "DIG", "nh": "NH03", "sz": "CDE", "subtype": "WEB",
     "description": "App Delta Web Servers", "members": [
        {"type": "ip", "value": "10.2.1.10", "description": "Delta Web 1"},
        {"type": "ip", "value": "10.2.1.11", "description": "Delta Web 2"},
     ]},
    {"name": "grp-PAY-NH07-CDE-APP", "app_id": "PAY", "nh": "NH07", "sz": "CDE", "subtype": "APP",
     "description": "Transaction Processing Servers", "members": [
        {"type": "ip", "value": "10.6.1.10", "description": "Epsilon App 1"},
        {"type": "ip", "value": "10.6.1.11", "description": "Epsilon App 2"},
        {"type": "cidr", "value": "10.6.1.64/28", "description": "Epsilon App Pool"},
     ]},
    {"name": "grp-ENT-NH05-GEN-APP", "app_id": "ENT", "nh": "NH05", "sz": "GEN", "subtype": "APP",
     "description": "App Zeta Application Servers", "members": [
        {"type": "ip", "value": "10.4.1.10", "description": "Zeta App 1"},
        {"type": "ip", "value": "10.4.1.11", "description": "Zeta App 2"},
     ]},
    {"name": "grp-SHR-NH13-GEN-SVC", "app_id": "SHR", "nh": "NH13", "sz": "GEN", "subtype": "SVC",
     "description": "Shared Analytics Services", "members": [
        {"type": "cidr", "value": "10.100.1.0/28", "description": "Shared SVC Subnet"},
     ]},
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
    {"name": "grp-FRD-NH02-CDE-APP", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "App Omicron Detection Engine", "members": [
        {"type": "ip", "value": "10.1.1.50", "description": "Omicron Engine 1"},
        {"type": "ip", "value": "10.1.1.51", "description": "Omicron Engine 2"},
     ]},
    {"name": "grp-AGW-NH14-DMZ-API", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "API Gateway Servers", "members": [
        {"type": "ip", "value": "10.70.1.10", "description": "Beta2 API 1"},
        {"type": "ip", "value": "10.70.1.11", "description": "Beta2 API 2"},
     ]},
    {"name": "grp-AGW-NH14-DMZ-LB", "app_id": "AGW", "nh": "NH14", "sz": "DMZ", "subtype": "LB",
     "description": "API Gateway Load Balancer", "members": [
        {"type": "ip", "value": "10.70.1.5", "description": "Beta2 LB VIP"},
     ]},
    {"name": "grp-EXT-NH14-DMZ-API", "app_id": "EXT", "nh": "NH14", "sz": "DMZ", "subtype": "API",
     "description": "External API Endpoints", "members": [
        {"type": "cidr", "value": "10.70.2.0/28", "description": "External API Subnet"},
     ]},
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


def build_seed_migrations() -> list[dict[str, Any]]:
    """Build seed migration records."""
    from datetime import datetime, timedelta
    now = datetime.utcnow().isoformat()
    return [
        {"migration_id": "mig-001", "name": "Legacy DC Alpha to Gamma NGDC Wave 1",
         "application": "CRM", "source_legacy_dc": "DC_LEGACY_A", "target_ngdc": "GAMMA_NGDC",
         "legacy_dc": "DC_LEGACY_A", "target_dc": "GAMMA_NGDC",
         "status": "In Progress", "progress": 35,
         "total_rules": 45, "migrated_rules": 16, "failed_rules": 2,
         "created_at": (datetime.utcnow() + timedelta(days=-60)).isoformat(),
         "updated_at": now},
        {"migration_id": "mig-002", "name": "Legacy DC Beta to Alpha NGDC Wave 1",
         "application": "HRM", "source_legacy_dc": "DC_LEGACY_B", "target_ngdc": "ALPHA_NGDC",
         "legacy_dc": "DC_LEGACY_B", "target_dc": "ALPHA_NGDC",
         "status": "In Progress", "progress": 60,
         "total_rules": 32, "migrated_rules": 19, "failed_rules": 1,
         "created_at": (datetime.utcnow() + timedelta(days=-45)).isoformat(),
         "updated_at": now},
        {"migration_id": "mig-003", "name": "Legacy DC Gamma App Migration",
         "application": "TRD", "source_legacy_dc": "DC_LEGACY_C", "target_ngdc": "BETA_NGDC",
         "legacy_dc": "DC_LEGACY_C", "target_dc": "BETA_NGDC",
         "status": "Planning", "progress": 10,
         "total_rules": 58, "migrated_rules": 0, "failed_rules": 0,
         "created_at": (datetime.utcnow() + timedelta(days=-15)).isoformat(),
         "updated_at": now},
        {"migration_id": "mig-004", "name": "Legacy DC Delta App Migration",
         "application": "INS", "source_legacy_dc": "DC_LEGACY_D", "target_ngdc": "ALPHA_NGDC",
         "legacy_dc": "DC_LEGACY_D", "target_dc": "ALPHA_NGDC",
         "status": "In Progress", "progress": 45,
         "total_rules": 28, "migrated_rules": 12, "failed_rules": 3,
         "created_at": (datetime.utcnow() + timedelta(days=-30)).isoformat(),
         "updated_at": now},
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
         "updated_at": now},
    ]


def build_seed_chg_requests() -> list[dict[str, Any]]:
    """Build seed change requests."""
    return [
        {"chg_id": "CHG10001", "rule_ids": ["R-3001"], "status": "Approved",
         "description": "Deploy App Alpha to Primary DB rule",
         "requested_by": "Owner A", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-31)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-30)).isoformat()},
    ]
