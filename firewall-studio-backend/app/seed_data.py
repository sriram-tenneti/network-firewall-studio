"""Seed data definitions for the Network Firewall Studio.

All reference data constants are defined here and imported by database.py.
Comprehensive test data for multiple apps, environments, firewall devices.
IP naming: svr-xx.xx.xx.xx for IPs, rng-xx.xx.xx.xx-xy for ranges.
Each app has multiple components (WEB, APP, DB, MQ, BAT, API) across zones within its NH.
"""

from datetime import datetime, timedelta
from typing import Any


# ============================================================
# Neighbourhoods (with CIDR ranges per SZ within each NH per DC)
# CIDR is at the SZ level: same SZ can have different CIDRs in different NHs/DCs
# ============================================================

SEED_NEIGHBOURHOODS = [
    {"nh_id": "NH01", "name": "Technology Enablement Services", "environment": "Production",
     "cidr": "10.0.0.0/16",
     "description": "Technology enablement and platform services", "ip_ranges": [
        {"cidr": "10.0.1.0/24", "description": "NH01 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "10.0.2.0/24", "description": "NH01 East Secondary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.50.0/24", "description": "NH01 West Primary", "dc": "BETA_NGDC"},
        {"cidr": "10.50.50.0/24", "description": "NH01 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH01-sz04", "cidr": "10.0.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH01-sz05", "cidr": "10.0.1.128/25", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH01-sz06", "cidr": "10.0.2.0/25", "dc": "ALPHA_NGDC", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH01-gen", "cidr": "10.0.2.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
        {"zone": "CCS", "vrf_id": "NH01-sz04-west", "cidr": "172.16.50.0/25", "dc": "BETA_NGDC", "description": "Critical Core Services (West)"},
        {"zone": "GEN", "vrf_id": "NH01-gen-west", "cidr": "172.16.50.128/25", "dc": "BETA_NGDC", "transit_vni": 4000, "description": "Standard/General (West)"},
        {"zone": "CCS", "vrf_id": "NH01-sz04-central", "cidr": "10.50.50.0/25", "dc": "GAMMA_NGDC", "description": "Critical Core Services (Central)"},
        {"zone": "GEN", "vrf_id": "NH01-gen-central", "cidr": "10.50.50.128/25", "dc": "GAMMA_NGDC", "transit_vni": 4000, "description": "Standard/General (Central)"},
     ]},
    {"nh_id": "NH02", "name": "Core Banking", "environment": "Production",
     "cidr": "10.1.0.0/16",
     "description": "Core banking services and data processing", "ip_ranges": [
        {"cidr": "10.1.1.0/24", "description": "NH02 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.1.2.0/24", "description": "NH02 East DB Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.1.0/24", "description": "NH02 West App", "dc": "BETA_NGDC"},
        {"cidr": "10.50.1.0/24", "description": "NH02 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH02-sz04", "cidr": "10.1.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH02-sz05", "cidr": "10.1.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 8051, "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH02-sz06", "cidr": "10.1.2.0/25", "dc": "ALPHA_NGDC", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH02-gen", "cidr": "10.1.2.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
        {"zone": "CCS", "vrf_id": "NH02-sz04-west", "cidr": "172.16.1.0/25", "dc": "BETA_NGDC", "description": "Critical Core Services (West)"},
        {"zone": "CDE", "vrf_id": "NH02-sz05-west", "cidr": "172.16.1.128/25", "dc": "BETA_NGDC", "description": "Card Holder Data (West)"},
        {"zone": "CCS", "vrf_id": "NH02-sz04-central", "cidr": "10.50.1.0/25", "dc": "GAMMA_NGDC", "description": "Critical Core Services (Central)"},
        {"zone": "GEN", "vrf_id": "NH02-gen-central", "cidr": "10.50.1.128/25", "dc": "GAMMA_NGDC", "transit_vni": 4000, "description": "Standard/General (Central)"},
     ]},
    {"nh_id": "NH03", "name": "Digital Channels", "environment": "Production",
     "cidr": "10.2.0.0/16",
     "description": "Digital channels, web and API hosting", "ip_ranges": [
        {"cidr": "10.2.1.0/24", "description": "NH03 East Web Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "10.2.2.0/24", "description": "NH03 East App Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.3.0/24", "description": "NH03 West Web", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH03-sz04", "cidr": "10.2.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH03-sz05", "cidr": "10.2.1.128/25", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
        {"zone": "GEN", "vrf_id": "NH03-gen", "cidr": "10.2.2.0/24", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
        {"zone": "CCS", "vrf_id": "NH03-sz04-west", "cidr": "172.16.3.0/25", "dc": "BETA_NGDC", "description": "Critical Core Services (West)"},
        {"zone": "GEN", "vrf_id": "NH03-gen-west", "cidr": "172.16.3.128/25", "dc": "BETA_NGDC", "transit_vni": 4000, "description": "Standard/General (West)"},
     ]},
    {"nh_id": "NH04", "name": "Wealth Management", "environment": "Production",
     "cidr": "10.3.0.0/16",
     "description": "Wealth management and insurance", "ip_ranges": [
        {"cidr": "10.3.1.0/24", "description": "NH04 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.4.0/24", "description": "NH04 West Primary", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH04-sz04", "cidr": "10.3.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH04-gen", "cidr": "10.3.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
        {"zone": "CCS", "vrf_id": "NH04-sz04-west", "cidr": "172.16.4.0/25", "dc": "BETA_NGDC", "description": "Critical Core Services (West)"},
        {"zone": "GEN", "vrf_id": "NH04-gen-west", "cidr": "172.16.4.128/25", "dc": "BETA_NGDC", "transit_vni": 4000, "description": "Standard/General (West)"},
     ]},
    {"nh_id": "NH05", "name": "Enterprise Services", "environment": "Production",
     "cidr": "10.4.0.0/16",
     "description": "Enterprise services, compliance, and KYC", "ip_ranges": [
        {"cidr": "10.4.1.0/24", "description": "NH05 East App", "dc": "ALPHA_NGDC"},
        {"cidr": "10.4.2.0/24", "description": "NH05 East DB", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH05-sz04", "cidr": "10.4.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH05-gen", "cidr": "10.4.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH06", "name": "Wholesale Banking", "environment": "Production",
     "cidr": "10.5.0.0/16",
     "description": "Wholesale banking and trading platforms", "ip_ranges": [
        {"cidr": "10.5.1.0/24", "description": "NH06 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.6.0/24", "description": "NH06 West Primary", "dc": "BETA_NGDC"},
        {"cidr": "172.16.20.0/24", "description": "NH06 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH06-sz04", "cidr": "10.5.1.0/26", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH06-sz05", "cidr": "10.5.1.64/26", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH06-sz06", "cidr": "10.5.1.128/26", "dc": "ALPHA_NGDC", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH06-gen", "cidr": "10.5.1.192/26", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
        {"zone": "CCS", "vrf_id": "NH06-sz04-west", "cidr": "172.16.6.0/26", "dc": "BETA_NGDC", "description": "Critical Core Services (West)"},
        {"zone": "CDE", "vrf_id": "NH06-sz05-west", "cidr": "172.16.6.64/26", "dc": "BETA_NGDC", "description": "Card Holder Data (West)"},
        {"zone": "CPA", "vrf_id": "NH06-sz06-west", "cidr": "172.16.6.128/26", "dc": "BETA_NGDC", "description": "Critical Payment Applications (West)"},
        {"zone": "GEN", "vrf_id": "NH06-gen-west", "cidr": "172.16.6.192/26", "dc": "BETA_NGDC", "transit_vni": 4000, "description": "Standard/General (West)"},
        {"zone": "CCS", "vrf_id": "NH06-sz04-central", "cidr": "172.16.20.0/26", "dc": "GAMMA_NGDC", "description": "Critical Core Services (Central)"},
        {"zone": "CDE", "vrf_id": "NH06-sz05-central", "cidr": "172.16.20.64/26", "dc": "GAMMA_NGDC", "description": "Card Holder Data (Central)"},
        {"zone": "GEN", "vrf_id": "NH06-gen-central", "cidr": "172.16.20.128/26", "dc": "GAMMA_NGDC", "transit_vni": 4000, "description": "Standard/General (Central)"},
     ]},
    {"nh_id": "NH07", "name": "Global Payments and Liquidity", "environment": "Production",
     "cidr": "10.6.0.0/16",
     "description": "Global payments, liquidity, and settlement", "ip_ranges": [
        {"cidr": "10.6.1.0/24", "description": "NH07 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CDE", "vrf_id": "NH07-sz05", "cidr": "10.6.1.0/25", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH07-sz06", "cidr": "10.6.1.128/25", "dc": "ALPHA_NGDC", "description": "Critical Payment Applications"},
     ]},
    {"nh_id": "NH08", "name": "Data and Analytics", "environment": "Production",
     "cidr": "10.7.0.0/16",
     "description": "Data analytics and core banking engine", "ip_ranges": [
        {"cidr": "10.7.1.0/24", "description": "NH08 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH08-sz04", "cidr": "10.7.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH08-sz05", "cidr": "10.7.1.128/25", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
     ]},
    {"nh_id": "NH09", "name": "Assisted Channels", "environment": "Production",
     "cidr": "10.8.0.0/16",
     "description": "Assisted channels and digital lending", "ip_ranges": [
        {"cidr": "10.8.1.0/24", "description": "NH09 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH09-sz04", "cidr": "10.8.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH09-gen", "cidr": "10.8.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH10", "name": "Consumer Lending", "environment": "Production",
     "cidr": "10.9.0.0/16",
     "description": "Consumer lending and portfolio management", "ip_ranges": [
        {"cidr": "10.9.1.0/24", "description": "NH10 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CDE", "vrf_id": "NH10-sz05", "cidr": "10.9.1.0/25", "dc": "ALPHA_NGDC", "description": "Card Holder Data"},
        {"zone": "GEN", "vrf_id": "NH10-gen", "cidr": "10.9.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    # --- Production Mainframe ---
    {"nh_id": "NH11", "name": "Production Mainframe", "environment": "Production",
     "cidr": "10.10.0.0/16",
     "description": "Production mainframe systems", "ip_ranges": [
        {"cidr": "10.10.1.0/24", "description": "NH11 East Mainframe", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH11-sz04", "cidr": "10.10.1.0/25", "dc": "ALPHA_NGDC", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH11-gen", "cidr": "10.10.1.128/25", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    # --- Non-Production Mainframe ---
    {"nh_id": "NH12", "name": "Non-Production Mainframe", "environment": "Non-Production",
     "cidr": "10.11.0.0/16",
     "description": "Non-production mainframe systems", "ip_ranges": [
        {"cidr": "10.11.1.0/24", "description": "NH12 East NP Mainframe", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "UCCS", "vrf_id": "NH12-sz04", "cidr": "10.11.1.0/25", "dc": "ALPHA_NGDC", "description": "Non-Prod Critical Core Services"},
        {"zone": "USTD", "vrf_id": "NH12-gen", "cidr": "10.11.1.128/25", "dc": "ALPHA_NGDC", "description": "Non-Prod Standard"},
     ]},
    # --- Non-Production Shared ---
    {"nh_id": "NH13", "name": "Non-Production Shared", "environment": "Non-Production",
     "cidr": "10.12.0.0/16",
     "description": "Shared non-production workloads (DEV/SIT/UAT/CTE)", "ip_ranges": [
        {"cidr": "10.12.1.0/24", "description": "NH13 East NP Shared", "dc": "ALPHA_NGDC"},
        {"cidr": "10.12.2.0/24", "description": "NH13 East NP DB", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "USTD", "vrf_id": "NH13-gen", "cidr": "10.12.1.0/25", "dc": "ALPHA_NGDC", "description": "Non-Prod Standard"},
        {"zone": "UCCS", "vrf_id": "NH13-sz04", "cidr": "10.12.1.128/25", "dc": "ALPHA_NGDC", "description": "Non-Prod Critical Core Services"},
        {"zone": "UCDE", "vrf_id": "NH13-sz05", "cidr": "10.12.2.0/25", "dc": "ALPHA_NGDC", "description": "Non-Prod CDE"},
        {"zone": "UCPA", "vrf_id": "NH13-sz06", "cidr": "10.12.2.128/25", "dc": "ALPHA_NGDC", "description": "Non-Prod CPA"},
     ]},
    # --- DMZ ---
    {"nh_id": "NH14", "name": "DMZ", "environment": "Production",
     "cidr": "10.70.0.0/16",
     "description": "External-facing DMZ / Publicly Accessible Applications", "ip_ranges": [
        {"cidr": "10.70.1.0/24", "description": "NH14 East DMZ", "dc": "ALPHA_NGDC"},
        {"cidr": "10.70.2.0/24", "description": "NH14 East External", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "PAA", "vrf_id": "NH14-sz02", "cidr": "10.70.1.0/24", "dc": "ALPHA_NGDC", "description": "Publicly Accessible Applications"},
        {"zone": "GEN", "vrf_id": "NH14-gen", "cidr": "10.70.2.0/24", "dc": "ALPHA_NGDC", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    # --- Non-Production DMZ ---
    {"nh_id": "NH15", "name": "Non-Production DMZ", "environment": "Non-Production",
     "cidr": "10.80.0.0/16",
     "description": "Non-production DMZ and management", "ip_ranges": [
        {"cidr": "10.80.1.0/24", "description": "NH15 East NP DMZ", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "UPAA", "vrf_id": "NH15-sz02", "cidr": "10.80.1.0/25", "dc": "ALPHA_NGDC", "description": "Non-Prod PAA"},
        {"zone": "USTD", "vrf_id": "NH15-gen", "cidr": "10.80.1.128/25", "dc": "ALPHA_NGDC", "description": "Non-Prod Standard"},
     ]},
    # --- Pre-Production (Non-Prod Shared) ---
    {"nh_id": "NH16", "name": "Pre-Production (Non-Prod Shared)", "environment": "Pre-Production",
     "cidr": "10.13.0.0/16",
     "description": "Pre-production / staging shared workloads", "ip_ranges": [
        {"cidr": "10.13.1.0/24", "description": "NH16 East Pre-Prod", "dc": "ALPHA_NGDC"},
        {"cidr": "10.13.2.0/24", "description": "NH16 East Pre-Prod DB", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "USTD", "vrf_id": "NH16-gen", "cidr": "10.13.1.0/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod Standard"},
        {"zone": "UCCS", "vrf_id": "NH16-sz04", "cidr": "10.13.1.128/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod CCS"},
        {"zone": "UCDE", "vrf_id": "NH16-sz05", "cidr": "10.13.2.0/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod CDE"},
        {"zone": "UCPA", "vrf_id": "NH16-sz06", "cidr": "10.13.2.128/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod CPA"},
     ]},
    # --- Pre-Production DMZ ---
    {"nh_id": "NH17", "name": "Pre-Production DMZ", "environment": "Pre-Production",
     "cidr": "10.14.0.0/16",
     "description": "Pre-production DMZ", "ip_ranges": [
        {"cidr": "10.14.1.0/24", "description": "NH17 East Pre-Prod DMZ", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "UPAA", "vrf_id": "NH17-sz02", "cidr": "10.14.1.0/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod PAA"},
        {"zone": "USTD", "vrf_id": "NH17-gen", "cidr": "10.14.1.128/25", "dc": "ALPHA_NGDC", "description": "Pre-Prod Standard"},
     ]},
]


# ============================================================
# Security Zones (with CIDR ranges)
# ============================================================

SEED_SECURITY_ZONES = [
    # ---- Production Fabric ----
    {"code": "STD", "name": "Standard Zone", "risk_level": "Low", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "gen/SZ01",
     "cidr": "10.128.0.0/16", "description": "General application zone – standard workloads, non-sensitive"},
    {"code": "GEN", "name": "General Zone", "risk_level": "Low", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "gen/SZ01",
     "cidr": "10.129.0.0/16", "description": "General-purpose compute (alias for STD), routing/transit"},
    {"code": "PAA", "name": "Publicly Accessible Applications", "risk_level": "High", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "paa/SZ02",
     "cidr": "10.130.0.0/16", "description": "Front-end / internet-accessible applications in DMZ"},
    {"code": "3PY", "name": "Third Party", "risk_level": "High", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "nh##-sz03",
     "cidr": "10.131.0.0/16", "description": "Third-party owned or managed workloads"},
    {"code": "CCS", "name": "Critical Core Services", "risk_level": "Critical", "pci_scope": True,
     "fabric": "Production", "vrf_prefix": "nh##-sz04",
     "cidr": "10.132.0.0/16", "description": "Management/control-plane and critical core banking services"},
    {"code": "CDE", "name": "Card Holder Data Environment", "risk_level": "Critical", "pci_scope": True,
     "fabric": "Production", "vrf_prefix": "nh##-sz05",
     "cidr": "10.133.0.0/16", "description": "PCI DSS scope – cardholder/PAN data processing and storage"},
    {"code": "CPA", "name": "Critical Payment Applications", "risk_level": "Critical", "pci_scope": True,
     "fabric": "Production", "vrf_prefix": "nh##-sz06",
     "cidr": "10.134.0.0/16", "description": "Enterprise payment applications and settlement"},
    {"code": "PSE", "name": "Production Simulation", "risk_level": "High", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "nh##-sz07",
     "cidr": "10.135.0.0/16", "description": "Technology enablement simulation – uses CCS firewall"},
    {"code": "Swift", "name": "Swift Zone", "risk_level": "Critical", "pci_scope": True,
     "fabric": "Production", "vrf_prefix": "nh##-sz08",
     "cidr": "10.136.0.0/16", "description": "Dedicated Swift messaging applications – uses CPA firewall"},
    {"code": "UC", "name": "Unified Communications", "risk_level": "Medium", "pci_scope": False,
     "fabric": "Production", "vrf_prefix": "nh##-sz09",
     "cidr": "10.137.0.0/16", "description": "Unified communications zone"},

    # ---- Non-Production Fabric ----
    {"code": "UGen", "name": "Non-Prod General", "risk_level": "Low", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "gen",
     "cidr": "10.200.0.0/16", "description": "General zone for non-prod routing"},
    {"code": "USTD", "name": "Non-Prod Standard", "risk_level": "Low", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "gen",
     "cidr": "10.201.0.0/16", "description": "Non-prod/UAT/CTE/SIT/DEV standard workloads"},
    {"code": "UPAA", "name": "Non-Prod PAA", "risk_level": "Medium", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "paa/sz-02",
     "cidr": "10.202.0.0/16", "description": "Non-prod front-end / internet-accessible applications"},
    {"code": "UCPA", "name": "Non-Prod CPA", "risk_level": "High", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "nh##-sz06",
     "cidr": "10.203.0.0/16", "description": "Non-prod critical payment applications"},
    {"code": "UCDE", "name": "Non-Prod CDE", "risk_level": "High", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "nh##-sz05",
     "cidr": "10.204.0.0/16", "description": "Non-prod cardholder data environment"},
    {"code": "UCCS", "name": "Non-Prod CCS", "risk_level": "High", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "nh##-sz04",
     "cidr": "10.205.0.0/16", "description": "Non-prod critical core services"},
    {"code": "U3PY", "name": "Non-Prod Third Party", "risk_level": "Medium", "pci_scope": False,
     "fabric": "Non-Production", "vrf_prefix": "nh##-sz03",
     "cidr": "10.206.0.0/16", "description": "Non-prod third-party workloads"},

    # ---- Pre-Production Fabric ----
    {"code": "UGen", "name": "Pre-Prod General", "risk_level": "Low", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "gen",
     "cidr": "10.210.0.0/16", "description": "General zone for pre-prod routing"},
    {"code": "USTD", "name": "Pre-Prod Standard", "risk_level": "Low", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "gen",
     "cidr": "10.211.0.0/16", "description": "Pre-prod/staging standard workloads"},
    {"code": "UPAA", "name": "Pre-Prod PAA", "risk_level": "Medium", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "paa/sz-02",
     "cidr": "10.212.0.0/16", "description": "Pre-prod front-end / internet-accessible applications"},
    {"code": "UCPA", "name": "Pre-Prod CPA", "risk_level": "High", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "nh##-sz06",
     "cidr": "10.213.0.0/16", "description": "Pre-prod critical payment applications"},
    {"code": "UCDE", "name": "Pre-Prod CDE", "risk_level": "High", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "nh##-sz05",
     "cidr": "10.214.0.0/16", "description": "Pre-prod cardholder data environment"},
    {"code": "UCCS", "name": "Pre-Prod CCS", "risk_level": "High", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "nh##-sz04",
     "cidr": "10.215.0.0/16", "description": "Pre-prod critical core services"},
    {"code": "U3PY", "name": "Pre-Prod Third Party", "risk_level": "Medium", "pci_scope": False,
     "fabric": "Pre-Production", "vrf_prefix": "nh##-sz03",
     "cidr": "10.216.0.0/16", "description": "Pre-prod third-party workloads"},
]


# ============================================================
# Data Centers
# ============================================================

SEED_NGDC_DATACENTERS = [
    {"dc_id": "ALPHA_NGDC", "name": "Alpha NGDC (East)", "region": "US-East", "status": "Active",
     "cidr": "10.0.0.0/8", "description": "Primary NGDC data center - US East coast"},
    {"dc_id": "BETA_NGDC", "name": "Beta NGDC (West)", "region": "US-West", "status": "Active",
     "cidr": "172.16.0.0/12", "description": "Secondary NGDC data center - US West coast"},
    {"dc_id": "GAMMA_NGDC", "name": "Gamma NGDC (Central)", "region": "US-Central", "status": "Active",
     "cidr": "10.50.0.0/16", "description": "Central NGDC data center - US Central"},
]

SEED_LEGACY_DATACENTERS = [
    {"dc_id": "DC_LEGACY_A", "name": "Legacy DC Alpha", "region": "US-East", "status": "Migrating",
     "ip_prefix": "10.25.x.x", "cidr": "10.25.0.0/16", "target_ngdc": "GAMMA_NGDC"},
    {"dc_id": "DC_LEGACY_B", "name": "Legacy DC Beta", "region": "US-East", "status": "Migrating",
     "ip_prefix": "10.26.x.x", "cidr": "10.26.0.0/16", "target_ngdc": "ALPHA_NGDC"},
    {"dc_id": "DC_LEGACY_C", "name": "Legacy DC Gamma", "region": "US-West", "status": "Migrating",
     "ip_prefix": "10.27.x.x", "cidr": "10.27.0.0/16", "target_ngdc": "BETA_NGDC"},
    {"dc_id": "DC_LEGACY_D", "name": "Legacy DC Delta", "region": "US-Central", "status": "Migrating",
     "ip_prefix": "10.28.x.x", "cidr": "10.28.0.0/16", "target_ngdc": "ALPHA_NGDC"},
    {"dc_id": "DC_LEGACY_E", "name": "Legacy DC Epsilon", "region": "US-East", "status": "Decommissioned",
     "ip_prefix": "10.29.x.x", "cidr": "10.29.0.0/16", "target_ngdc": "ALPHA_NGDC"},
    {"dc_id": "DC_LEGACY_F", "name": "Legacy DC Zeta", "region": "US-Central", "status": "Migrating",
     "ip_prefix": "10.30.x.x", "cidr": "10.30.0.0/16", "target_ngdc": "ALPHA_NGDC"},
]


# ============================================================
# Applications (10 apps, multi-component)
# ============================================================

SEED_APPLICATIONS = [
    {"app_id": "CRM", "name": "Customer Relationship Manager", "app_distributed_id": "AD-1001",
     "owner": "Team Eta", "nh": "Core Banking,DMZ", "sz": "CCS,CDE,PAA", "criticality": "High", "pci_scope": True,
     "neighborhoods": "Core Banking,DMZ", "szs": "CCS,CDE,PAA", "dcs": "ALPHA_NGDC,BETA_NGDC", "snow_sysid": "SYSID-CRM-001",
     "components": ["WEB", "APP", "DB", "BAT", "API"],
     "description": "CRM platform for customer data management"},
    {"app_id": "HRM", "name": "Human Resource Manager", "app_distributed_id": "AD-1002",
     "owner": "Team Platform", "nh": "Technology Enablement Services", "sz": "GEN", "criticality": "Medium", "pci_scope": False,
     "neighborhoods": "Technology Enablement Services", "szs": "GEN", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-HRM-002",
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "HR management and employee portal"},
    {"app_id": "TRD", "name": "Trading Platform", "app_distributed_id": "AD-1003",
     "owner": "Team Xi", "nh": "Wholesale Banking,DMZ", "sz": "CCS,CDE,PAA", "criticality": "Critical", "pci_scope": True,
     "neighborhoods": "Wholesale Banking,DMZ", "szs": "CCS,CDE,PAA", "dcs": "ALPHA_NGDC,BETA_NGDC,GAMMA_NGDC", "snow_sysid": "SYSID-TRD-003",
     "components": ["WEB", "APP", "DB", "MQ", "API", "BAT"],
     "description": "Real-time trading and market data"},
    {"app_id": "PAY", "name": "Payment Gateway", "app_distributed_id": "AD-1004",
     "owner": "Team Epsilon", "nh": "Global Payments and Liquidity", "sz": "CDE,CPA", "criticality": "Critical", "pci_scope": True,
     "neighborhoods": "Global Payments and Liquidity", "szs": "CDE,CPA", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-PAY-004",
     "components": ["APP", "DB", "MQ", "API"],
     "description": "Payment processing and settlement"},
    {"app_id": "INS", "name": "Insurance Portal", "app_distributed_id": "AD-1005",
     "owner": "Team Kappa", "nh": "Wealth Management", "sz": "CCS,GEN", "criticality": "High", "pci_scope": False,
     "neighborhoods": "Wealth Management", "szs": "CCS,GEN", "dcs": "ALPHA_NGDC,BETA_NGDC", "snow_sysid": "SYSID-INS-005",
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "Insurance policy management"},
    {"app_id": "KYC", "name": "KYC Compliance", "app_distributed_id": "AD-1006",
     "owner": "Team Lambda", "nh": "Enterprise Services", "sz": "CCS,GEN", "criticality": "High", "pci_scope": False,
     "neighborhoods": "Enterprise Services", "szs": "CCS,GEN", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-KYC-006",
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Know Your Customer compliance platform"},
    {"app_id": "FRD", "name": "Fraud Detection", "app_distributed_id": "AD-1007",
     "owner": "Team Eta", "nh": "Core Banking", "sz": "CCS,CDE", "criticality": "Critical", "pci_scope": True,
     "neighborhoods": "Core Banking", "szs": "CCS,CDE", "dcs": "ALPHA_NGDC,BETA_NGDC", "snow_sysid": "SYSID-FRD-007",
     "components": ["APP", "DB", "MQ", "API"],
     "description": "Real-time fraud detection engine"},
    {"app_id": "LND", "name": "Lending Platform", "app_distributed_id": "AD-1008",
     "owner": "Team Iota", "nh": "Assisted Channels", "sz": "CCS,GEN", "criticality": "High", "pci_scope": False,
     "neighborhoods": "Assisted Channels", "szs": "CCS,GEN", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-LND-008",
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "Digital lending and loan origination"},
    {"app_id": "WLT", "name": "Wealth Management", "app_distributed_id": "AD-1009",
     "owner": "Team Mu", "nh": "Consumer Lending,DMZ", "sz": "CDE,GEN,PAA", "criticality": "High", "pci_scope": True,
     "neighborhoods": "Consumer Lending,DMZ", "szs": "CDE,GEN,PAA", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-WLT-009",
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Portfolio and wealth management"},
    {"app_id": "CBK", "name": "Core Banking", "app_distributed_id": "AD-1010",
     "owner": "Team Theta", "nh": "Data and Analytics", "sz": "CCS,CDE", "criticality": "Critical", "pci_scope": True,
     "neighborhoods": "Data and Analytics", "szs": "CCS,CDE", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-CBK-010",
     "components": ["APP", "DB", "MQ", "API", "BAT"],
     "description": "Core banking transaction engine"},
    {"app_id": "EPT", "name": "Enterprise Portal", "app_distributed_id": "AD-1011",
     "owner": "Team Platform", "nh": "Technology Enablement Services,DMZ", "sz": "CCS,PAA", "criticality": "High", "pci_scope": False,
     "neighborhoods": "Technology Enablement Services,DMZ", "szs": "CCS,PAA", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-EPT-011",
     "components": ["WEB", "APP", "API"],
     "description": "Internet-facing enterprise portal (PAA zone)"},
    {"app_id": "MBK", "name": "Mobile Banking", "app_distributed_id": "AD-1012",
     "owner": "Team Epsilon", "nh": "Global Payments and Liquidity,DMZ", "sz": "CPA,PAA", "criticality": "Critical", "pci_scope": True,
     "neighborhoods": "Global Payments and Liquidity,DMZ", "szs": "CPA,PAA", "dcs": "ALPHA_NGDC", "snow_sysid": "SYSID-MBK-012",
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Mobile banking application"},
]


# ============================================================
# App-to-DC/NH/SZ Component Mappings
# Each app can span multiple DCs, same NH, and multiple SZs
# depending on component type (WEB, APP, DB, MQ, BAT, API).
# ============================================================

SEED_APP_DC_MAPPINGS = [
    # ================================================================
    # App-DC Mappings — aligned with _build_ip_mappings() zones
    # NH/SZ must match SEED_GROUPS naming: grp-{APP}-{NH}-{SZ}-{COMP}
    # dc_location: "NGDC" | "Legacy"  — tracks where each component lives
    # ================================================================

    # --- CRM (AD-1001): Partially migrated — WEB/APP/BAT/API in NGDC, DB/MQ still in Legacy ---
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.1.10/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM internet-facing web tier"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CCS",
     "cidr": "10.1.1.0/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM application servers"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CCS",
     "cidr": "10.1.1.30/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM batch processing"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "API", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CCS",
     "cidr": "10.1.1.40/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM API gateway"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "DB", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_A", "legacy_cidr": "10.25.1.128/28",
     "status": "Active", "notes": "CRM database – still in Legacy DC Alpha"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "MQ", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_A", "legacy_cidr": "10.25.1.50/31",
     "status": "Active", "notes": "CRM message queue – still in Legacy DC Alpha"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "APP", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH02", "sz": "CCS",
     "cidr": "172.16.1.20/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM Beta DR app tier"},
    {"app_id": "CRM", "app_distributed_id": "AD-1001", "component": "DB", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH02", "sz": "CDE",
     "cidr": "172.16.1.128/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CRM Beta DR database"},

    # --- HRM (AD-1002): Fully in Legacy — not yet migrated ---
    {"app_id": "HRM", "app_distributed_id": "AD-1002", "component": "WEB", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_B", "legacy_cidr": "10.26.2.130/31",
     "status": "Active", "notes": "HRM web servers – Legacy DC Beta"},
    {"app_id": "HRM", "app_distributed_id": "AD-1002", "component": "APP", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_B", "legacy_cidr": "10.26.2.140/30",
     "status": "Active", "notes": "HRM application servers – Legacy DC Beta"},
    {"app_id": "HRM", "app_distributed_id": "AD-1002", "component": "BAT", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_B", "legacy_cidr": "10.26.2.160/32",
     "status": "Active", "notes": "HRM batch – Legacy DC Beta"},
    {"app_id": "HRM", "app_distributed_id": "AD-1002", "component": "DB", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_B", "legacy_cidr": "10.26.2.150/31",
     "status": "Active", "notes": "HRM database – Legacy DC Beta"},
    {"app_id": "HRM", "app_distributed_id": "AD-1002", "component": "MQ", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_B", "legacy_cidr": "10.26.2.162/31",
     "status": "Active", "notes": "HRM message queue – Legacy DC Beta"},

    # --- TRD (AD-1003): Fully in NGDC ---
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE",
     "cidr": "172.16.20.10/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD web servers"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE",
     "cidr": "172.16.20.20/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD application servers"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE",
     "cidr": "172.16.20.50/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD batch processing"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CPA",
     "cidr": "10.6.1.30/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD database cluster"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CPA",
     "cidr": "10.6.1.40/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD message queue brokers"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "APP", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH06", "sz": "CDE",
     "cidr": "172.16.6.64/27", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD Beta DR app tier"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "DB", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH07", "sz": "CPA",
     "cidr": "172.16.6.80/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD Beta DR database"},
    {"app_id": "TRD", "app_distributed_id": "AD-1003", "component": "APP", "dc_location": "NGDC",
     "dc": "GAMMA_NGDC", "nh": "NH06", "sz": "CDE",
     "cidr": "172.16.20.64/27", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "TRD Gamma DR app tier"},

    # --- PAY (AD-1004): Partially migrated — WEB/APP in NGDC, DB/MQ in Legacy ---
    {"app_id": "PAY", "app_distributed_id": "AD-1004", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CCS",
     "cidr": "10.50.8.10/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "PAY web servers"},
    {"app_id": "PAY", "app_distributed_id": "AD-1004", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CCS",
     "cidr": "10.50.8.20/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "PAY application servers"},
    {"app_id": "PAY", "app_distributed_id": "AD-1004", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CCS",
     "cidr": "10.50.8.50/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "PAY batch processing"},
    {"app_id": "PAY", "app_distributed_id": "AD-1004", "component": "DB", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_D", "legacy_cidr": "10.28.7.30/31",
     "status": "Active", "notes": "PAY database – still in Legacy DC Delta"},
    {"app_id": "PAY", "app_distributed_id": "AD-1004", "component": "MQ", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_D", "legacy_cidr": "10.28.7.40/31",
     "status": "Active", "notes": "PAY message queue – still in Legacy DC Delta"},

    # --- INS (AD-1005): Fully in NGDC ---
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "STD",
     "cidr": "10.3.1.130/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS web portal"},
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "STD",
     "cidr": "10.3.1.140/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS application servers"},
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "STD",
     "cidr": "10.3.1.160/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS batch processing"},
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.4.30/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS database"},
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.4.40/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS message queue"},
    {"app_id": "INS", "app_distributed_id": "AD-1005", "component": "APP", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH04", "sz": "STD",
     "cidr": "172.16.4.144/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "INS Beta DR"},

    # --- KYC (AD-1006): Fully in NGDC ---
    {"app_id": "KYC", "app_distributed_id": "AD-1006", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CCS",
     "cidr": "10.4.1.130/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "KYC web portal"},
    {"app_id": "KYC", "app_distributed_id": "AD-1006", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CCS",
     "cidr": "10.4.1.140/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "KYC application servers"},
    {"app_id": "KYC", "app_distributed_id": "AD-1006", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CCS",
     "cidr": "10.4.1.160/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "KYC batch processing"},
    {"app_id": "KYC", "app_distributed_id": "AD-1006", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CDE",
     "cidr": "10.4.2.10/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "KYC database"},
    {"app_id": "KYC", "app_distributed_id": "AD-1006", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CDE",
     "cidr": "10.4.2.20/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "KYC message queue"},

    # --- FRD (AD-1007): Partially migrated — APP/BAT in NGDC, DB/MQ in Legacy ---
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE",
     "cidr": "10.1.1.110/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "FRD web servers"},
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE",
     "cidr": "10.1.1.50/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "FRD fraud engine"},
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE",
     "cidr": "10.1.1.60/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "FRD batch processing"},
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "DB", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_A", "legacy_cidr": "10.25.2.20/31",
     "status": "Active", "notes": "FRD database – still in Legacy DC Alpha"},
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "MQ", "dc_location": "Legacy",
     "dc": "", "nh": "", "sz": "",
     "cidr": "", "legacy_dc": "DC_LEGACY_A", "legacy_cidr": "10.25.1.55/31",
     "status": "Active", "notes": "FRD Kafka MQ – still in Legacy DC Alpha"},
    {"app_id": "FRD", "app_distributed_id": "AD-1007", "component": "APP", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH02", "sz": "CDE",
     "cidr": "172.16.1.160/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "FRD Beta DR"},

    # --- LND (AD-1008): Fully in NGDC ---
    {"app_id": "LND", "app_distributed_id": "AD-1008", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "GEN",
     "cidr": "10.8.1.130/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "LND web portal"},
    {"app_id": "LND", "app_distributed_id": "AD-1008", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "GEN",
     "cidr": "10.8.1.140/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "LND application servers"},
    {"app_id": "LND", "app_distributed_id": "AD-1008", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "GEN",
     "cidr": "10.8.1.160/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "LND batch processing"},
    {"app_id": "LND", "app_distributed_id": "AD-1008", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "CPA",
     "cidr": "10.8.2.30/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "LND database"},
    {"app_id": "LND", "app_distributed_id": "AD-1008", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "CPA",
     "cidr": "10.8.2.40/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "LND message queue"},

    # --- WLT (AD-1009): Fully in NGDC ---
    {"app_id": "WLT", "app_distributed_id": "AD-1009", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.1.100/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "WLT internet-facing portal"},
    {"app_id": "WLT", "app_distributed_id": "AD-1009", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "PAA",
     "cidr": "10.9.1.20/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "WLT application servers"},
    {"app_id": "WLT", "app_distributed_id": "AD-1009", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "PAA",
     "cidr": "10.9.1.50/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "WLT batch processing"},
    {"app_id": "WLT", "app_distributed_id": "AD-1009", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "3PY",
     "cidr": "10.9.1.30/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "WLT database"},
    {"app_id": "WLT", "app_distributed_id": "AD-1009", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "3PY",
     "cidr": "10.9.1.40/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "WLT message queue"},

    # --- CBK (AD-1010): Fully in NGDC ---
    {"app_id": "CBK", "app_distributed_id": "AD-1010", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CPA",
     "cidr": "10.7.1.10/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CBK web servers"},
    {"app_id": "CBK", "app_distributed_id": "AD-1010", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CPA",
     "cidr": "10.7.1.20/29", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CBK core banking engine"},
    {"app_id": "CBK", "app_distributed_id": "AD-1010", "component": "BAT", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CPA",
     "cidr": "10.7.1.50/32", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CBK batch processing"},
    {"app_id": "CBK", "app_distributed_id": "AD-1010", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CDE",
     "cidr": "10.7.2.30/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CBK database – PCI CDE"},
    {"app_id": "CBK", "app_distributed_id": "AD-1010", "component": "MQ", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CDE",
     "cidr": "10.7.2.40/31", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "CBK message queue"},

    # --- EPT (AD-1011): Fully in NGDC ---
    {"app_id": "EPT", "app_distributed_id": "AD-1011", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.1.20/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "EPT internet-facing portal"},
    {"app_id": "EPT", "app_distributed_id": "AD-1011", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CCS",
     "cidr": "10.0.1.0/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "EPT application servers"},
    {"app_id": "EPT", "app_distributed_id": "AD-1011", "component": "API", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CCS",
     "cidr": "10.0.1.16/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "EPT API gateway"},
    {"app_id": "EPT", "app_distributed_id": "AD-1011", "component": "APP", "dc_location": "NGDC",
     "dc": "BETA_NGDC", "nh": "NH01", "sz": "CCS",
     "cidr": "172.16.50.0/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "EPT Beta DR"},

    # --- MBK (AD-1012): Fully in NGDC ---
    {"app_id": "MBK", "app_distributed_id": "AD-1012", "component": "WEB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH14", "sz": "PAA",
     "cidr": "10.70.1.30/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "MBK mobile banking web"},
    {"app_id": "MBK", "app_distributed_id": "AD-1012", "component": "APP", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CPA",
     "cidr": "10.6.1.168/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "MBK application servers"},
    {"app_id": "MBK", "app_distributed_id": "AD-1012", "component": "DB", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CDE",
     "cidr": "10.6.1.16/28", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "MBK database – PCI CDE"},
    {"app_id": "MBK", "app_distributed_id": "AD-1012", "component": "API", "dc_location": "NGDC",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CPA",
     "cidr": "10.6.1.184/30", "legacy_dc": "", "legacy_cidr": "",
     "status": "Active", "notes": "MBK API layer"},
]


# ============================================================
# Environments
# ============================================================

SEED_ENVIRONMENTS = [
    {"name": "Production", "code": "PROD", "description": "Live production environment"},
    {"name": "Non-Production", "code": "NPROD", "description": "Development and testing"},
    {"name": "Pre-Production", "code": "PPROD", "description": "Staging / pre-prod validation"},
    {"name": "UAT", "code": "UAT", "description": "User acceptance testing"},
    {"name": "SIT", "code": "SIT", "description": "System integration testing"},
    {"name": "DR", "code": "DR", "description": "Disaster recovery"},
]


# ============================================================
# Predefined Destinations (using svr- naming)
# ============================================================

SEED_PREDEFINED_DESTINATIONS = [
    {"name": "grp-INTERNET-EXT", "type": "external", "description": "Internet / External",
     "ips": ["0.0.0.0/0"]},
    {"name": "grp-DNS-INFRA", "type": "infrastructure", "description": "Internal DNS Servers",
     "ips": ["svr-10.0.1.53", "svr-10.0.2.53"]},
    {"name": "grp-NTP-INFRA", "type": "infrastructure", "description": "NTP Time Servers",
     "ips": ["svr-10.0.1.123", "svr-10.0.2.123"]},
    {"name": "grp-SYSLOG-INFRA", "type": "infrastructure", "description": "Syslog / Log Aggregators",
     "ips": ["svr-10.0.2.10", "svr-10.0.2.11"]},
    {"name": "grp-SMTP-INFRA", "type": "infrastructure", "description": "Email / SMTP Relay",
     "ips": ["svr-10.80.1.25"]},
    {"name": "grp-LDAP-INFRA", "type": "infrastructure", "description": "Active Directory / LDAP",
     "ips": ["svr-10.80.1.88", "svr-10.80.1.89"]},
    {"name": "grp-PROXY-INFRA", "type": "infrastructure", "description": "Web Proxy Servers",
     "ips": ["svr-10.70.1.80", "svr-10.70.1.81"]},
    {"name": "grp-BACKUP-INFRA", "type": "infrastructure", "description": "Backup Infrastructure",
     "ips": ["svr-10.90.1.10", "svr-10.90.1.11"]},
    {"name": "grp-MONITOR-INFRA", "type": "infrastructure", "description": "Monitoring Agents",
     "ips": ["svr-10.80.1.100", "svr-10.80.1.101"]},
    {"name": "grp-JUMP-MGT", "type": "management", "description": "Jump / Bastion Hosts",
     "ips": ["svr-10.80.1.50", "svr-10.80.1.51"]},
]


# ============================================================
# Naming Standards
# ============================================================

SEED_NAMING_STANDARDS = [
    {"pattern": "grp-{APP}-{NH}-{SZ}-{TIER}", "type": "group",
     "example": "grp-CRM-NH02-CDE-APP", "description": "Group naming: grp-AppID-NH-SZ-Tier"},
    {"pattern": "svr-{IP}", "type": "server",
     "example": "svr-10.1.1.10", "description": "Individual server/IP: svr-x.x.x.x"},
    {"pattern": "rng-{START_IP}-{END_OCTET}", "type": "range",
     "example": "rng-10.1.1.10-20", "description": "IP range: rng-x.x.x.x-y (last octet range)"},
    {"pattern": "sub-{CIDR}", "type": "subnet",
     "example": "sub-10.1.1.0/24", "description": "Subnet: sub-x.x.x.x/mask"},
    {"pattern": "pol-{APP}-{ENV}-{SEQ}", "type": "policy",
     "example": "pol-CRM-PROD-001", "description": "Policy naming: pol-AppID-Env-Sequence"},
    {"pattern": "fw-{VENDOR}-{DC}-{SEQ}", "type": "firewall_device",
     "example": "fw-PA-ALPHA-001", "description": "Firewall device: fw-Vendor-DC-Sequence"},
]


# ============================================================
# Firewall Device Naming Patterns (Generic)
# ============================================================
# Instead of enumerating every individual firewall device, we define
# naming patterns and categories.  The backend resolves the actual
# device name at runtime using:  fw-{VENDOR}-{DC}-{NH}-{SZ}
#
# Device categories:
#   perimeter  – DC-level north-south firewalls (HA pair per DC)
#   dmz        – DMZ-specific firewall per DC
#   paa        – PAA perimeter firewall per DC
#   segmentation – Per-NH, per-SZ east-west firewall (only for SEGMENTED zones)
#
# Open zones (STD, GEN, UGen, USTD) do NOT have per-NH firewalls.
# Segmented zones each get a dedicated per-NH firewall instance.

SEED_FIREWALL_DEVICE_PATTERNS = [
    # ---- Perimeter (one HA pair per DC) ----
    {"pattern_id": "FWP-PERIM", "type": "perimeter",
     "naming": "fw-{VENDOR}-{DC}-{SEQ}",
     "example": "fw-PA-ALPHA-001 / fw-PA-ALPHA-002 (HA pair)",
     "scope": "Per DC", "dc": "Any", "nh": "N/A", "sz": "N/A",
     "description": "DC-level perimeter firewall – north-south traffic, HA pair",
     "capabilities": ["L7 inspection", "URL filtering", "Threat prevention", "IPS", "VPN"]},

    # ---- DMZ (one per DC) ----
    {"pattern_id": "FWP-DMZ", "type": "dmz",
     "naming": "fw-{VENDOR}-{DC}-DMZ",
     "example": "fw-PA-ALPHA-DMZ, fw-CP-BETA-DMZ, fw-FG-GAMMA-DMZ",
     "scope": "Per DC", "dc": "Any", "nh": "N/A", "sz": "N/A",
     "description": "DMZ firewall – external-facing traffic isolation",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF integration"]},

    # ---- PAA Perimeter (one per DC) ----
    {"pattern_id": "FWP-PAA", "type": "paa",
     "naming": "fw-{VENDOR}-{DC}-PAA-{SEQ}",
     "example": "fw-PA-PAA-001 (Alpha), fw-CP-BETA-PAA-001 (Beta)",
     "scope": "Per DC", "dc": "Any", "nh": "N/A", "sz": "PAA",
     "description": "PAA perimeter firewall – internet-accessible app zone enforcement",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF", "PAA enforcement"]},

    # ---- NH Segmentation (per NH, per segmented SZ, per DC) ----
    {"pattern_id": "FWP-SEG", "type": "segmentation",
     "naming": "fw-{VENDOR}-{DC}-{NH}-{SZ}",
     "example": "fw-PA-NH01-CPA, fw-PA-NH02-CDE, fw-CP-BETA-NH06-CCS",
     "scope": "Per NH per SZ per DC", "dc": "Any", "nh": "Any (with segmented SZ)", "sz": "Segmented only",
     "description": "NH-level segmentation firewall – micro-segmentation, east-west enforcement. "
                    "One instance per NH per segmented zone (CPA, CDE, CCS, PAA, 3PY, Swift, PSE, UC). "
                    "Open zones (STD, GEN) do NOT get per-NH firewalls.",
     "capabilities": ["Micro-segmentation", "East-West enforcement", "SZ-specific policy"]},

    # ---- NP Segmentation (per NH, per NP segmented SZ) ----
    {"pattern_id": "FWP-NP-SEG", "type": "np_segmentation",
     "naming": "fw-{VENDOR}-{DC}-{NH}-{SZ}",
     "example": "fw-PA-NH13-UCCS, fw-PA-NH13-UCDE",
     "scope": "Per NH per NP-SZ per DC", "dc": "Any", "nh": "NP NHs (NH12-NH17)", "sz": "NP-Segmented only",
     "description": "Non-Prod NH-level segmentation firewall for UCPA, UCDE, UCCS, UPAA, U3PY zones. "
                    "Open NP zones (UGen, USTD) do NOT get per-NH firewalls.",
     "capabilities": ["Micro-segmentation", "NP SZ enforcement"]},
]

# DC-level vendor assignments (used by backend to resolve actual device names)
SEED_DC_VENDOR_MAP = {
    "ALPHA_NGDC": {"perimeter": "palo_alto", "dmz": "palo_alto", "paa": "palo_alto", "segmentation": "palo_alto"},
    "BETA_NGDC":  {"perimeter": "checkpoint", "dmz": "checkpoint", "paa": "checkpoint", "segmentation": "checkpoint"},
    "GAMMA_NGDC": {"perimeter": "fortigate", "dmz": "fortigate", "paa": "fortigate", "segmentation": "palo_alto"},
}

# Keep SEED_FIREWALL_DEVICES for backward compatibility (existing CRUD endpoints).
# This list now contains only representative examples; the backend auto-generates
# the full device inventory from NH/SZ/DC data + patterns above.
SEED_FIREWALL_DEVICES = [
    # Representative perimeter devices
    {"device_id": "fw-PA-ALPHA-001", "name": "Palo Alto Alpha Primary", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.0.254.1", "ha_pair": "fw-PA-ALPHA-002",
     "capabilities": ["L7 inspection", "URL filtering", "Threat prevention"]},
    {"device_id": "fw-CP-BETA-001", "name": "Check Point Beta Primary", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "172.16.254.1", "ha_pair": "fw-CP-BETA-002",
     "capabilities": ["Stateful inspection", "IPS", "VPN"]},
    {"device_id": "fw-FG-GAMMA-001", "name": "FortiGate Gamma Primary", "vendor": "fortigate",
     "dc": "GAMMA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.50.254.1", "ha_pair": "fw-FG-GAMMA-002",
     "capabilities": ["NGFW", "SD-WAN", "IPS", "VPN", "SSL inspection"]},

    # Representative DMZ devices
    {"device_id": "fw-PA-ALPHA-DMZ", "name": "Palo Alto Alpha DMZ", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "dmz", "status": "Active", "mgmt_ip": "10.70.254.1",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF integration"]},

    # Representative PAA devices
    {"device_id": "fw-PA-PAA-001", "name": "PAA Perimeter FW (Alpha)", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "paa", "status": "Active", "mgmt_ip": "10.0.252.1",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF", "PAA enforcement"]},

    # Representative segmentation devices (auto-generated from NH/SZ/DC at runtime)
    {"device_id": "fw-PA-NH01-CPA", "name": "NH01 CPA Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.0.253.11",
     "capabilities": ["Micro-segmentation", "East-West", "CPA enforcement"]},
    {"device_id": "fw-PA-NH02-CDE", "name": "NH02 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.1.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-CP-BETA-NH06-CCS", "name": "Beta NH06 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH06", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.6.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},
]


# ============================================================
# Logical Data Flow Rules
# Determines how many firewall boundaries a rule must cross
# based on source/destination NH and SZ placement.
# ============================================================

SEGMENTED_ZONES = {"CPA", "CDE", "CCS", "PAA", "3PY", "Swift", "PSE", "UC"}
NON_PROD_SEGMENTED_ZONES = {"UCPA", "UCDE", "UCCS", "UPAA", "U3PY"}
# STD/GEN/UGen/USTD zones do NOT have per-NH firewalls
OPEN_ZONES = {"STD", "GEN", "UGen", "USTD"}

LOGICAL_FLOW_RULES = [
    {
        "id": "LDF-001",
        "description": "STD/GEN zone workloads between NHs (same or different data halls) - no firewall needed",
        "condition": "src_sz in (STD, GEN) AND dst_sz in (STD, GEN)",
        "boundaries": 0,
        "note": "Standard zone workloads communicate directly between neighborhoods",
    },
    {
        "id": "LDF-002",
        "description": "Same NH, same SZ (any zone) - no firewall needed",
        "condition": "src_nh == dst_nh AND src_sz == dst_sz",
        "boundaries": 0,
        "note": "Intra-NH, intra-SZ traffic is permitted by default",
    },
    {
        "id": "LDF-003",
        "description": "Segmented zone to different zone, different NHs - 1 firewall (egress from source NH SZ)",
        "condition": "src_sz in SEGMENTED AND dst_sz != src_sz AND src_nh != dst_nh",
        "boundaries": 1,
        "devices": ["egress: src_nh src_sz firewall"],
        "note": "App in segmented zone egresses through its NH's SZ firewall to reach a different zone in another NH",
    },
    {
        "id": "LDF-004",
        "description": "Same segmented zone, different NHs - 2 firewalls (egress src NH + ingress dst NH)",
        "condition": "src_sz in SEGMENTED AND dst_sz == src_sz AND src_nh != dst_nh",
        "boundaries": 2,
        "devices": ["egress: src_nh src_sz firewall", "ingress: dst_nh dst_sz firewall"],
        "note": "Both NHs have their own SZ firewall; traffic must exit one and enter the other",
    },
    {
        "id": "LDF-005",
        "description": "Same NH, different segmented zones - 1 firewall (NH SZ boundary)",
        "condition": "src_nh == dst_nh AND src_sz != dst_sz AND (src_sz in SEGMENTED OR dst_sz in SEGMENTED)",
        "boundaries": 1,
        "devices": ["boundary: src_nh firewall (higher-security SZ)"],
        "note": "Cross-zone within same NH requires traversing the segmentation firewall",
    },
    {
        "id": "LDF-006",
        "description": "PAA flow (internet → PAA → internal NH) - multiple boundaries",
        "condition": "src_sz == PAA OR dst_sz == PAA",
        "boundaries": 2,
        "devices": ["paa_perimeter: PAA firewall", "internal: dst_nh dst_sz firewall"],
        "note": "PAA traffic crosses the PAA perimeter and then the destination NH's internal firewall",
    },
]


# ============================================================
# Policy Matrices
# ============================================================

SEED_HERITAGE_DC_MATRIX = [
    # --- Heritage (Legacy) → NGDC direction ---
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "CCS",
     "action": "Blocked - Exception Required", "reason": "Heritage DC to CCS requires exception approval"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "CDE",
     "action": "Blocked - Exception Required", "reason": "Heritage DC to CDE requires PCI exception"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "CPA",
     "action": "Blocked", "reason": "Heritage DC to CPA not permitted"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "GEN",
     "action": "Permitted", "reason": "Heritage DC to General zone is allowed during migration"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "STD",
     "action": "Permitted", "reason": "Heritage DC to Standard zone is allowed during migration"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "PAA",
     "action": "Blocked - Exception Required", "reason": "Heritage DC to PAA requires DMZ exception"},
    {"direction": "Heritage-to-NGDC", "heritage_zone": "Default", "new_dc_zone": "DMZ",
     "action": "Blocked", "reason": "Heritage DC to DMZ not permitted directly"},

    # --- NGDC → Heritage (Legacy) direction ---
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "CCS",
     "action": "Permitted - Migration Window", "reason": "NGDC CCS to Heritage DC allowed during migration window"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "CDE",
     "action": "Blocked - Exception Required", "reason": "NGDC CDE to Heritage DC requires PCI exception"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "CPA",
     "action": "Blocked - Exception Required", "reason": "NGDC CPA to Heritage DC requires compliance exception"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "GEN",
     "action": "Permitted", "reason": "NGDC General zone to Heritage DC is permitted"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "STD",
     "action": "Permitted", "reason": "NGDC Standard zone to Heritage DC is permitted"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "PAA",
     "action": "Permitted - Migration Window", "reason": "NGDC PAA to Heritage DC allowed during migration window"},
    {"direction": "NGDC-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "DMZ",
     "action": "Blocked", "reason": "NGDC DMZ to Heritage DC not permitted directly"},

    # --- Heritage ↔ Heritage (Legacy-to-Legacy) ---
    {"direction": "Heritage-to-Heritage", "heritage_zone": "Default", "new_dc_zone": "Default",
     "action": "Permitted", "reason": "Intra-heritage traffic is flat – no segmentation, permitted by default"},
]

# ---- NGDC Production Matrix (Generic Pattern-Based) ----
# Rules use generic patterns (source_zone/dest_zone as "Any", "Open", "Segmented",
# "Same", etc.) instead of listing every SZ combination.
# The backend resolve_policy() function interprets these patterns against actual
# source/destination NH, SZ, and DC values at runtime.
#
# Zone categories used in patterns:
#   OPEN  = {STD, GEN}  – no per-NH firewall needed
#   SEGMENTED = {CPA, CDE, CCS, PAA, 3PY, Swift, PSE, UC} – require firewall
#   NON_PROD_OPEN = {UGen, USTD}
#   NON_PROD_SEGMENTED = {UCPA, UCDE, UCCS, UPAA, U3PY}
#
SEED_NGDC_PROD_MATRIX = [
    # ---- Row 1: Open Zone ↔ Open Zone (Any DC, Any NH) ----
    {"id": "PM-PROD-01", "matrix_type": "NGDC-Prod",
     "source_zone": "Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Open zone (STD/GEN) traffic is permitted across any NH/DC without firewall"},

    # ---- Row 2: Same SZ, Same NH, Any DC ----
    {"id": "PM-PROD-02", "matrix_type": "NGDC-Prod",
     "source_zone": "Same", "source_nh": "Same", "source_dc": "Any",
     "dest_zone": "Same", "dest_nh": "Same", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Intra-zone, intra-NH traffic is permitted – no firewall boundary"},

    # ---- Row 3: Same SZ (Segmented), Cross NH, Same DC ----
    # Same SZ is always PERMITTED regardless of NH/DC. Traffic still passes
    # through FW devices (egress + ingress) but no firewall rule is required.
    {"id": "PM-PROD-03", "matrix_type": "NGDC-Prod",
     "source_zone": "Segmented (Same)", "source_nh": "Different", "source_dc": "Same",
     "dest_zone": "Segmented (Same)", "dest_nh": "Different", "dest_dc": "Same",
     "action": "Permitted", "firewall_traversal": "Egress (src NH) + Ingress (dst NH) [informational]",
     "reason": "Same segmented zone across different NHs – permitted per birthright. Traffic passes through egress (src NH FW) and ingress (dst NH FW) but no firewall rule is required."},

    # ---- Row 4: Same SZ (Segmented), Cross NH, Cross DC ----
    {"id": "PM-PROD-04", "matrix_type": "NGDC-Prod",
     "source_zone": "Segmented (Same)", "source_nh": "Different", "source_dc": "Different",
     "dest_zone": "Segmented (Same)", "dest_nh": "Different", "dest_dc": "Different",
     "action": "Permitted", "firewall_traversal": "Egress (src NH) + Ingress (dst NH) [informational]",
     "reason": "Same segmented zone, cross NH and cross DC – permitted per birthright. Traffic passes through egress and ingress FW devices but no rule is required."},

    # ---- Row 5: Cross SZ (both Segmented), Same NH, Any DC ----
    {"id": "PM-PROD-05", "matrix_type": "NGDC-Prod",
     "source_zone": "Segmented", "source_nh": "Same", "source_dc": "Any",
     "dest_zone": "Segmented (Different)", "dest_nh": "Same", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "NH SZ Boundary FW",
     "reason": "Cross-zone within same NH requires traversing the NH segmentation firewall"},

    # ---- Row 6: Cross SZ (both Segmented), Cross NH, Any DC ----
    {"id": "PM-PROD-06", "matrix_type": "NGDC-Prod",
     "source_zone": "Segmented", "source_nh": "Different", "source_dc": "Any",
     "dest_zone": "Segmented (Different)", "dest_nh": "Different", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "Egress (src NH src SZ FW) + Ingress (dst NH dst SZ FW)",
     "reason": "Cross-SZ cross-NH requires egress through source SZ FW and ingress through destination SZ FW"},

    # ---- Row 7: Open Zone → Segmented Zone (Any NH/DC) ----
    {"id": "PM-PROD-07", "matrix_type": "NGDC-Prod",
     "source_zone": "Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Segmented", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "Ingress (dst NH dst SZ FW)",
     "reason": "Open zone to segmented zone requires ingress through destination NH SZ firewall"},

    # ---- Row 8: Segmented Zone → Open Zone (Any NH/DC) ----
    {"id": "PM-PROD-08", "matrix_type": "NGDC-Prod",
     "source_zone": "Segmented", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "Egress (src NH src SZ FW)",
     "reason": "Segmented zone to open zone requires egress through source NH SZ firewall"},

    # ---- Row 9: Open/STD ↔ CDE (Blocked – CDE is isolated) ----
    {"id": "PM-PROD-09", "matrix_type": "NGDC-Prod",
     "source_zone": "Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "CDE", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Direct access from Open zone to CDE is not permitted – CDE is isolated"},

    # ---- Row 10: CDE → Open (Blocked) ----
    {"id": "PM-PROD-10", "matrix_type": "NGDC-Prod",
     "source_zone": "CDE", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "CDE to Open zone not permitted – CDE is isolated"},

    # ---- Row 11: Non-Prod → Prod (Blocked) ----
    {"id": "PM-PROD-11", "matrix_type": "NGDC-Prod",
     "source_zone": "Non-Prod (Any)", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Prod (Any)", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Non-Production to Production traffic is unconditionally blocked"},

    # ---- Row 12: PAA → Internal Segmented (PAA perimeter + internal FW) ----
    {"id": "PM-PROD-12", "matrix_type": "NGDC-Prod",
     "source_zone": "PAA", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Segmented", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "PAA Perimeter FW + Ingress (dst NH dst SZ FW)",
     "reason": "PAA traffic must traverse PAA perimeter firewall and destination NH internal firewall"},
]

# ---- Non-Production Matrix (Generic Pattern-Based) ----
SEED_NONPROD_MATRIX = [
    # ---- Row 1: NP Open ↔ NP Open (Any NH/DC) ----
    {"id": "PM-NPROD-01", "matrix_type": "Non-Prod",
     "source_zone": "NP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "NP-Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Non-Prod open zone (UGen/USTD) traffic is permitted without firewall"},

    # ---- Row 2: Same NP-SZ, Same NH ----
    {"id": "PM-NPROD-02", "matrix_type": "Non-Prod",
     "source_zone": "NP-Segmented (Same)", "source_nh": "Same", "source_dc": "Any",
     "dest_zone": "NP-Segmented (Same)", "dest_nh": "Same", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Same NP segmented zone within same NH – permitted"},

    # ---- Row 3: Cross NP-SZ (both Segmented), Any NH ----
    {"id": "PM-NPROD-03", "matrix_type": "Non-Prod",
     "source_zone": "NP-Segmented", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "NP-Segmented (Different)", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "Egress + Ingress (NP SZ FWs)",
     "reason": "Cross-SZ within Non-Prod requires egress + ingress through NP segmentation FWs"},

    # ---- Row 4: NP-Open → NP-Segmented ----
    {"id": "PM-NPROD-04", "matrix_type": "Non-Prod",
     "source_zone": "NP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "NP-Segmented", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Firewall Request Required", "firewall_traversal": "Ingress (dst NP SZ FW)",
     "reason": "NP Open zone to NP Segmented requires ingress through destination FW"},

    # ---- Row 5: NP-Open → UCDE (Blocked) ----
    {"id": "PM-NPROD-05", "matrix_type": "Non-Prod",
     "source_zone": "NP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "UCDE", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "NP Open to UCDE not permitted – UCDE is isolated in Non-Prod"},

    # ---- Row 6: Non-Prod → Prod (Blocked) ----
    {"id": "PM-NPROD-06", "matrix_type": "Non-Prod",
     "source_zone": "Non-Prod (Any)", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Prod (Any)", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Non-Prod to Prod traffic is unconditionally blocked"},
]

# ---- Pre-Production Matrix (Generic Pattern-Based) ----
SEED_PREPROD_MATRIX = [
    # ---- Row 1: PP Open ↔ PP Open ----
    {"id": "PM-PPROD-01", "matrix_type": "Pre-Prod",
     "source_zone": "PP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "PP-Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Pre-Prod open zone traffic is permitted"},

    # ---- Row 2: NP-Open → PP-Open (Cross-Env Permitted) ----
    {"id": "PM-PPROD-02", "matrix_type": "Pre-Prod",
     "source_zone": "NP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "PP-Open", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Permitted", "firewall_traversal": "None",
     "reason": "Non-Prod open to Pre-Prod open – permitted"},

    # ---- Row 3: NP-Open → PP-Segmented (Blocked) ----
    {"id": "PM-PPROD-03", "matrix_type": "Pre-Prod",
     "source_zone": "NP-Open", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "PP-Segmented", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Non-Prod open to Pre-Prod segmented – blocked"},

    # ---- Row 4: NP-Segmented → PP-Segmented (Blocked) ----
    {"id": "PM-PPROD-04", "matrix_type": "Pre-Prod",
     "source_zone": "NP-Segmented", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "PP-Segmented", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Non-Prod segmented to Pre-Prod segmented – blocked"},

    # ---- Row 5: Pre-Prod → Prod (Blocked) ----
    {"id": "PM-PPROD-05", "matrix_type": "Pre-Prod",
     "source_zone": "Pre-Prod (Any)", "source_nh": "Any", "source_dc": "Any",
     "dest_zone": "Prod (Any)", "dest_nh": "Any", "dest_dc": "Any",
     "action": "Blocked", "firewall_traversal": "N/A",
     "reason": "Pre-Prod to Prod traffic is unconditionally blocked"},
]

SEED_POLICY_MATRIX = SEED_NGDC_PROD_MATRIX + SEED_NONPROD_MATRIX + SEED_PREPROD_MATRIX


# ============================================================
# Organization Config
# ============================================================

SEED_ORG_CONFIG = {
    "org_name": "Enterprise Financial Corp",
    "org_id": "EFC-001",
    "default_environment": "Production",
    "pci_enabled": True,
    "auto_birthright_validation": True,
    "require_compile_before_submit": False,
    "naming_convention": "NGDC Standard",
    "ip_format": "svr-x.x.x.x",
    "range_format": "rng-x.x.x.x-y",
    "group_format": "grp-APP-NH-SZ-TIER",
    "approval_required": True,
    "max_rules_per_policy": 500,
}


# ============================================================
# Groups: Multi-component per app (WEB, APP, DB, MQ, BAT, API)
# Using svr- naming for IPs, rng- for ranges
# ============================================================

SEED_GROUPS = [
    # ================================================================
    # NGDC Groups — aligned with _build_ip_mappings() NGDC IPs exactly
    # Naming: grp-{APP}-{NH}-{SZ}-{COMPONENT}
    # ================================================================

    # --- CRM: Source NH02/STD, Destination NH02/GEN ---
    {"name": "grp-CRM-NH02-STD-WEB", "app_id": "CRM", "nh": "NH02", "sz": "STD", "subtype": "WEB",
     "description": "CRM Web Servers", "members": [
        {"type": "ip", "value": "svr-10.50.1.10", "description": "CRM Web 1"},
        {"type": "ip", "value": "svr-10.50.1.11", "description": "CRM Web 2"},
     ]},
    {"name": "grp-CRM-NH02-STD-APP", "app_id": "CRM", "nh": "NH02", "sz": "STD", "subtype": "APP",
     "description": "CRM Application Servers", "members": [
        {"type": "ip", "value": "svr-10.50.1.20", "description": "CRM App 1"},
        {"type": "ip", "value": "svr-10.50.1.21", "description": "CRM App 2"},
        {"type": "ip", "value": "svr-10.50.1.22", "description": "CRM App 3"},
     ]},
    {"name": "grp-CRM-NH02-STD-BAT", "app_id": "CRM", "nh": "NH02", "sz": "STD", "subtype": "BAT",
     "description": "CRM Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.50.1.40", "description": "CRM Batch 1"},
     ]},
    {"name": "grp-CRM-NH02-GEN-DB", "app_id": "CRM", "nh": "NH02", "sz": "GEN", "subtype": "DB",
     "description": "CRM Database Cluster", "members": [
        {"type": "ip", "value": "svr-10.50.1.30", "description": "CRM DB Primary"},
        {"type": "ip", "value": "svr-10.50.1.31", "description": "CRM DB Standby"},
     ]},
    {"name": "grp-CRM-NH02-GEN-MQ", "app_id": "CRM", "nh": "NH02", "sz": "GEN", "subtype": "MQ",
     "description": "CRM Message Queue", "members": [
        {"type": "ip", "value": "svr-10.50.1.42", "description": "CRM MQ 1"},
        {"type": "ip", "value": "svr-10.50.1.43", "description": "CRM MQ 2"},
     ]},

    # --- HRM: Source NH01/GEN, Destination NH01/STD ---
    {"name": "grp-HRM-NH01-GEN-WEB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "WEB",
     "description": "HRM Web Servers", "members": [
        {"type": "ip", "value": "svr-10.0.2.130", "description": "HRM Web 1"},
        {"type": "ip", "value": "svr-10.0.2.131", "description": "HRM Web 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-APP", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "HRM Application Servers", "members": [
        {"type": "ip", "value": "svr-10.0.2.140", "description": "HRM App 1"},
        {"type": "ip", "value": "svr-10.0.2.141", "description": "HRM App 2"},
        {"type": "ip", "value": "svr-10.0.2.142", "description": "HRM App 3"},
     ]},
    {"name": "grp-HRM-NH01-GEN-BAT", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "BAT",
     "description": "HRM Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.0.2.160", "description": "HRM Batch 1"},
     ]},
    {"name": "grp-HRM-NH01-STD-DB", "app_id": "HRM", "nh": "NH01", "sz": "STD", "subtype": "DB",
     "description": "HRM Database", "members": [
        {"type": "ip", "value": "svr-10.0.2.150", "description": "HRM DB Primary"},
        {"type": "ip", "value": "svr-10.0.2.151", "description": "HRM DB Replica"},
     ]},
    {"name": "grp-HRM-NH01-STD-MQ", "app_id": "HRM", "nh": "NH01", "sz": "STD", "subtype": "MQ",
     "description": "HRM Message Queue", "members": [
        {"type": "ip", "value": "svr-10.0.2.162", "description": "HRM MQ 1"},
        {"type": "ip", "value": "svr-10.0.2.163", "description": "HRM MQ 2"},
     ]},

    # --- TRD: Source NH06/CDE, Destination NH07/CPA ---
    {"name": "grp-TRD-NH06-CDE-WEB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "WEB",
     "description": "TRD Web Frontend", "members": [
        {"type": "ip", "value": "svr-172.16.20.10", "description": "TRD Web 1"},
        {"type": "ip", "value": "svr-172.16.20.11", "description": "TRD Web 2"},
     ]},
    {"name": "grp-TRD-NH06-CDE-APP", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "APP",
     "description": "TRD Application Servers", "members": [
        {"type": "ip", "value": "svr-172.16.20.20", "description": "TRD App 1"},
        {"type": "ip", "value": "svr-172.16.20.21", "description": "TRD App 2"},
        {"type": "ip", "value": "svr-172.16.20.22", "description": "TRD App 3"},
     ]},
    {"name": "grp-TRD-NH06-CDE-BAT", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "BAT",
     "description": "TRD Batch Processing", "members": [
        {"type": "ip", "value": "svr-172.16.20.50", "description": "TRD Batch 1"},
     ]},
    {"name": "grp-TRD-NH07-CPA-DB", "app_id": "TRD", "nh": "NH07", "sz": "CPA", "subtype": "DB",
     "description": "TRD Database Cluster", "members": [
        {"type": "ip", "value": "svr-10.6.1.30", "description": "TRD DB Primary"},
        {"type": "ip", "value": "svr-10.6.1.31", "description": "TRD DB Standby"},
     ]},
    {"name": "grp-TRD-NH07-CPA-MQ", "app_id": "TRD", "nh": "NH07", "sz": "CPA", "subtype": "MQ",
     "description": "TRD Message Queue", "members": [
        {"type": "ip", "value": "svr-10.6.1.40", "description": "TRD MQ Broker 1"},
        {"type": "ip", "value": "svr-10.6.1.41", "description": "TRD MQ Broker 2"},
     ]},

    # --- PAY: Source NH08/CCS, Destination NH07/CDE ---
    {"name": "grp-PAY-NH08-CCS-WEB", "app_id": "PAY", "nh": "NH08", "sz": "CCS", "subtype": "WEB",
     "description": "PAY Web Portal", "members": [
        {"type": "ip", "value": "svr-10.50.8.10", "description": "PAY Web 1"},
        {"type": "ip", "value": "svr-10.50.8.11", "description": "PAY Web 2"},
     ]},
    {"name": "grp-PAY-NH08-CCS-APP", "app_id": "PAY", "nh": "NH08", "sz": "CCS", "subtype": "APP",
     "description": "PAY Transaction Processors", "members": [
        {"type": "ip", "value": "svr-10.50.8.20", "description": "PAY App 1"},
        {"type": "ip", "value": "svr-10.50.8.21", "description": "PAY App 2"},
        {"type": "ip", "value": "svr-10.50.8.22", "description": "PAY App 3"},
     ]},
    {"name": "grp-PAY-NH08-CCS-BAT", "app_id": "PAY", "nh": "NH08", "sz": "CCS", "subtype": "BAT",
     "description": "PAY Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.50.8.50", "description": "PAY Batch 1"},
     ]},
    {"name": "grp-PAY-NH07-CDE-DB", "app_id": "PAY", "nh": "NH07", "sz": "CDE", "subtype": "DB",
     "description": "PAY Database (PCI CDE)", "members": [
        {"type": "ip", "value": "svr-10.50.7.30", "description": "PAY DB Primary"},
        {"type": "ip", "value": "svr-10.50.7.31", "description": "PAY DB Standby"},
     ]},
    {"name": "grp-PAY-NH07-CDE-MQ", "app_id": "PAY", "nh": "NH07", "sz": "CDE", "subtype": "MQ",
     "description": "PAY Message Queue", "members": [
        {"type": "ip", "value": "svr-10.50.7.40", "description": "PAY MQ 1"},
        {"type": "ip", "value": "svr-10.50.7.41", "description": "PAY MQ 2"},
     ]},

    # --- INS: Source NH04/STD, Destination NH14/PAA ---
    {"name": "grp-INS-NH04-STD-WEB", "app_id": "INS", "nh": "NH04", "sz": "STD", "subtype": "WEB",
     "description": "INS Web Portal", "members": [
        {"type": "ip", "value": "svr-10.3.1.130", "description": "INS Web 1"},
        {"type": "ip", "value": "svr-10.3.1.131", "description": "INS Web 2"},
     ]},
    {"name": "grp-INS-NH04-STD-APP", "app_id": "INS", "nh": "NH04", "sz": "STD", "subtype": "APP",
     "description": "INS Application Servers", "members": [
        {"type": "ip", "value": "svr-10.3.1.140", "description": "INS App 1"},
        {"type": "ip", "value": "svr-10.3.1.141", "description": "INS App 2"},
        {"type": "ip", "value": "svr-10.3.1.142", "description": "INS App 3"},
     ]},
    {"name": "grp-INS-NH04-STD-BAT", "app_id": "INS", "nh": "NH04", "sz": "STD", "subtype": "BAT",
     "description": "INS Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.3.1.160", "description": "INS Batch 1"},
     ]},
    {"name": "grp-INS-NH14-PAA-DB", "app_id": "INS", "nh": "NH14", "sz": "PAA", "subtype": "DB",
     "description": "INS Database", "members": [
        {"type": "ip", "value": "svr-10.70.4.30", "description": "INS DB Primary"},
        {"type": "ip", "value": "svr-10.70.4.31", "description": "INS DB Standby"},
     ]},
    {"name": "grp-INS-NH14-PAA-MQ", "app_id": "INS", "nh": "NH14", "sz": "PAA", "subtype": "MQ",
     "description": "INS Message Queue", "members": [
        {"type": "ip", "value": "svr-10.70.4.40", "description": "INS MQ 1"},
        {"type": "ip", "value": "svr-10.70.4.41", "description": "INS MQ 2"},
     ]},

    # --- KYC: Source NH05/CCS, Destination NH05/CDE ---
    {"name": "grp-KYC-NH05-CCS-WEB", "app_id": "KYC", "nh": "NH05", "sz": "CCS", "subtype": "WEB",
     "description": "KYC Web Interface", "members": [
        {"type": "ip", "value": "svr-10.4.1.130", "description": "KYC Web 1"},
        {"type": "ip", "value": "svr-10.4.1.131", "description": "KYC Web 2"},
     ]},
    {"name": "grp-KYC-NH05-CCS-APP", "app_id": "KYC", "nh": "NH05", "sz": "CCS", "subtype": "APP",
     "description": "KYC Application", "members": [
        {"type": "ip", "value": "svr-10.4.1.140", "description": "KYC App 1"},
        {"type": "ip", "value": "svr-10.4.1.141", "description": "KYC App 2"},
        {"type": "ip", "value": "svr-10.4.1.142", "description": "KYC App 3"},
     ]},
    {"name": "grp-KYC-NH05-CCS-BAT", "app_id": "KYC", "nh": "NH05", "sz": "CCS", "subtype": "BAT",
     "description": "KYC Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.4.1.160", "description": "KYC Batch 1"},
     ]},
    {"name": "grp-KYC-NH05-CDE-DB", "app_id": "KYC", "nh": "NH05", "sz": "CDE", "subtype": "DB",
     "description": "KYC Database", "members": [
        {"type": "ip", "value": "svr-10.4.2.10", "description": "KYC DB Primary"},
        {"type": "ip", "value": "svr-10.4.2.11", "description": "KYC DB Replica"},
     ]},
    {"name": "grp-KYC-NH05-CDE-MQ", "app_id": "KYC", "nh": "NH05", "sz": "CDE", "subtype": "MQ",
     "description": "KYC Message Queue", "members": [
        {"type": "ip", "value": "svr-10.4.2.20", "description": "KYC MQ 1"},
        {"type": "ip", "value": "svr-10.4.2.21", "description": "KYC MQ 2"},
     ]},

    # --- FRD: Source NH02/CDE, Destination NH02/Swift ---
    {"name": "grp-FRD-NH02-CDE-WEB", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "WEB",
     "description": "FRD Web Interface", "members": [
        {"type": "ip", "value": "svr-10.1.1.110", "description": "FRD Web 1"},
        {"type": "ip", "value": "svr-10.1.1.111", "description": "FRD Web 2"},
     ]},
    {"name": "grp-FRD-NH02-CDE-APP", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "FRD Detection Engine", "members": [
        {"type": "ip", "value": "svr-10.1.1.50", "description": "FRD Engine 1"},
        {"type": "ip", "value": "svr-10.1.1.51", "description": "FRD Engine 2"},
        {"type": "ip", "value": "svr-10.1.1.52", "description": "FRD Engine 3"},
     ]},
    {"name": "grp-FRD-NH02-CDE-BAT", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "BAT",
     "description": "FRD Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.1.1.60", "description": "FRD Batch 1"},
     ]},
    {"name": "grp-FRD-NH02-Swift-DB", "app_id": "FRD", "nh": "NH02", "sz": "Swift", "subtype": "DB",
     "description": "FRD Database (PCI CDE)", "members": [
        {"type": "ip", "value": "svr-10.1.2.20", "description": "FRD DB Primary"},
        {"type": "ip", "value": "svr-10.1.2.21", "description": "FRD DB Standby"},
     ]},
    {"name": "grp-FRD-NH02-Swift-MQ", "app_id": "FRD", "nh": "NH02", "sz": "Swift", "subtype": "MQ",
     "description": "FRD Event Stream", "members": [
        {"type": "ip", "value": "svr-10.1.1.55", "description": "FRD Kafka 1"},
        {"type": "ip", "value": "svr-10.1.1.56", "description": "FRD Kafka 2"},
     ]},

    # --- LND: Source NH09/GEN, Destination NH09/CPA ---
    {"name": "grp-LND-NH09-GEN-WEB", "app_id": "LND", "nh": "NH09", "sz": "GEN", "subtype": "WEB",
     "description": "LND Web Portal", "members": [
        {"type": "ip", "value": "svr-10.8.1.130", "description": "LND Web 1"},
        {"type": "ip", "value": "svr-10.8.1.131", "description": "LND Web 2"},
     ]},
    {"name": "grp-LND-NH09-GEN-APP", "app_id": "LND", "nh": "NH09", "sz": "GEN", "subtype": "APP",
     "description": "LND Loan Engine", "members": [
        {"type": "ip", "value": "svr-10.8.1.140", "description": "LND App 1"},
        {"type": "ip", "value": "svr-10.8.1.141", "description": "LND App 2"},
        {"type": "ip", "value": "svr-10.8.1.142", "description": "LND App 3"},
     ]},
    {"name": "grp-LND-NH09-GEN-BAT", "app_id": "LND", "nh": "NH09", "sz": "GEN", "subtype": "BAT",
     "description": "LND Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.8.1.160", "description": "LND Batch 1"},
     ]},
    {"name": "grp-LND-NH09-CPA-DB", "app_id": "LND", "nh": "NH09", "sz": "CPA", "subtype": "DB",
     "description": "LND Database", "members": [
        {"type": "ip", "value": "svr-10.8.2.30", "description": "LND DB Primary"},
        {"type": "ip", "value": "svr-10.8.2.31", "description": "LND DB Standby"},
     ]},
    {"name": "grp-LND-NH09-CPA-MQ", "app_id": "LND", "nh": "NH09", "sz": "CPA", "subtype": "MQ",
     "description": "LND Message Queue", "members": [
        {"type": "ip", "value": "svr-10.8.2.40", "description": "LND MQ 1"},
        {"type": "ip", "value": "svr-10.8.2.41", "description": "LND MQ 2"},
     ]},

    # --- WLT: Source NH14/PAA (WEB), NH10/PAA (APP/BAT), Destination NH10/3PY ---
    {"name": "grp-WLT-NH14-PAA-WEB", "app_id": "WLT", "nh": "NH14", "sz": "PAA", "subtype": "WEB",
     "description": "WLT Web Interface", "members": [
        {"type": "ip", "value": "svr-10.70.1.100", "description": "WLT Web 1"},
        {"type": "ip", "value": "svr-10.70.1.101", "description": "WLT Web 2"},
     ]},
    {"name": "grp-WLT-NH10-PAA-APP", "app_id": "WLT", "nh": "NH10", "sz": "PAA", "subtype": "APP",
     "description": "WLT Portfolio Engine", "members": [
        {"type": "ip", "value": "svr-10.9.1.20", "description": "WLT App 1"},
        {"type": "ip", "value": "svr-10.9.1.21", "description": "WLT App 2"},
        {"type": "ip", "value": "svr-10.9.1.22", "description": "WLT App 3"},
     ]},
    {"name": "grp-WLT-NH10-PAA-BAT", "app_id": "WLT", "nh": "NH10", "sz": "PAA", "subtype": "BAT",
     "description": "WLT Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.9.1.50", "description": "WLT Batch 1"},
     ]},
    {"name": "grp-WLT-NH10-3PY-DB", "app_id": "WLT", "nh": "NH10", "sz": "3PY", "subtype": "DB",
     "description": "WLT Database (PCI CDE)", "members": [
        {"type": "ip", "value": "svr-10.9.1.30", "description": "WLT DB Primary"},
        {"type": "ip", "value": "svr-10.9.1.31", "description": "WLT DB Replica"},
     ]},
    {"name": "grp-WLT-NH10-3PY-MQ", "app_id": "WLT", "nh": "NH10", "sz": "3PY", "subtype": "MQ",
     "description": "WLT Message Queue", "members": [
        {"type": "ip", "value": "svr-10.9.1.40", "description": "WLT MQ 1"},
        {"type": "ip", "value": "svr-10.9.1.41", "description": "WLT MQ 2"},
     ]},

    # --- CBK: Source NH08/CPA, Destination NH08/CDE ---
    {"name": "grp-CBK-NH08-CPA-WEB", "app_id": "CBK", "nh": "NH08", "sz": "CPA", "subtype": "WEB",
     "description": "CBK Web Portal", "members": [
        {"type": "ip", "value": "svr-10.7.1.10", "description": "CBK Web 1"},
        {"type": "ip", "value": "svr-10.7.1.11", "description": "CBK Web 2"},
     ]},
    {"name": "grp-CBK-NH08-CPA-APP", "app_id": "CBK", "nh": "NH08", "sz": "CPA", "subtype": "APP",
     "description": "CBK Core Engine", "members": [
        {"type": "ip", "value": "svr-10.7.1.20", "description": "CBK App 1"},
        {"type": "ip", "value": "svr-10.7.1.21", "description": "CBK App 2"},
        {"type": "ip", "value": "svr-10.7.1.22", "description": "CBK App 3"},
     ]},
    {"name": "grp-CBK-NH08-CPA-BAT", "app_id": "CBK", "nh": "NH08", "sz": "CPA", "subtype": "BAT",
     "description": "CBK Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.7.1.50", "description": "CBK Batch 1"},
     ]},
    {"name": "grp-CBK-NH08-CDE-DB", "app_id": "CBK", "nh": "NH08", "sz": "CDE", "subtype": "DB",
     "description": "CBK Database Cluster", "members": [
        {"type": "ip", "value": "svr-10.7.2.30", "description": "CBK DB Primary"},
        {"type": "ip", "value": "svr-10.7.2.31", "description": "CBK DB Standby"},
     ]},
    {"name": "grp-CBK-NH08-CDE-MQ", "app_id": "CBK", "nh": "NH08", "sz": "CDE", "subtype": "MQ",
     "description": "CBK Message Bus", "members": [
        {"type": "ip", "value": "svr-10.7.2.40", "description": "CBK MQ 1"},
        {"type": "ip", "value": "svr-10.7.2.41", "description": "CBK MQ 2"},
     ]},

    # --- SHARED: Cross-app infrastructure groups ---
    {"name": "grp-SHARED-NH14-PSE-API", "app_id": "SHARED", "nh": "NH14", "sz": "PSE", "subtype": "API",
     "description": "DMZ API Gateway (External)", "members": [
        {"type": "ip", "value": "svr-10.70.1.10", "description": "DMZ API 1"},
        {"type": "ip", "value": "svr-10.70.1.11", "description": "DMZ API 2"},
     ]},
    {"name": "grp-SHARED-NH01-UC-MON", "app_id": "SHARED", "nh": "NH01", "sz": "UC", "subtype": "MON",
     "description": "Monitoring Agents", "members": [
        {"type": "ip", "value": "svr-10.80.1.100", "description": "Monitor Agent 1"},
        {"type": "ip", "value": "svr-10.80.1.101", "description": "Monitor Agent 2"},
     ]},

    # --- EPT — Enterprise Portal (NH14/PAA WEB, NH01/CCS APP/API) ---
    {"name": "grp-EPT-NH14-PAA-WEB", "app_id": "EPT", "nh": "NH14", "sz": "PAA", "subtype": "WEB",
     "description": "EPT Web Frontend (PAA zone)", "members": [
        {"type": "ip", "value": "svr-10.70.1.20", "description": "EPT Web 1"},
        {"type": "ip", "value": "svr-10.70.1.21", "description": "EPT Web 2"},
     ]},
    {"name": "grp-EPT-NH01-CCS-APP", "app_id": "EPT", "nh": "NH01", "sz": "CCS", "subtype": "APP",
     "description": "EPT App Backend", "members": [
        {"type": "ip", "value": "svr-10.0.1.10", "description": "EPT App 1"},
        {"type": "ip", "value": "svr-10.0.1.11", "description": "EPT App 2"},
     ]},
    {"name": "grp-EPT-NH01-CCS-API", "app_id": "EPT", "nh": "NH01", "sz": "CCS", "subtype": "API",
     "description": "EPT API Gateway", "members": [
        {"type": "ip", "value": "svr-10.0.1.16", "description": "EPT API 1"},
     ]},

    # --- MBK — Mobile Banking (NH14/PAA WEB, NH07/CPA APP/API, NH07/CDE DB) ---
    {"name": "grp-MBK-NH14-PAA-WEB", "app_id": "MBK", "nh": "NH14", "sz": "PAA", "subtype": "WEB",
     "description": "MBK Mobile Web", "members": [
        {"type": "ip", "value": "svr-10.70.1.30", "description": "MBK Web 1"},
     ]},
    {"name": "grp-MBK-NH07-CPA-APP", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "APP",
     "description": "MBK App Engine", "members": [
        {"type": "ip", "value": "svr-10.6.1.168", "description": "MBK App 1"},
        {"type": "ip", "value": "svr-10.6.1.169", "description": "MBK App 2"},
     ]},
    {"name": "grp-MBK-NH07-CDE-DB", "app_id": "MBK", "nh": "NH07", "sz": "CDE", "subtype": "DB",
     "description": "MBK Database", "members": [
        {"type": "ip", "value": "svr-10.6.1.16", "description": "MBK DB Primary"},
     ]},
    {"name": "grp-MBK-NH07-CPA-API", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "API",
     "description": "MBK API Gateway", "members": [
        {"type": "ip", "value": "svr-10.6.1.184", "description": "MBK API 1"},
     ]},
]



# ============================================================
# Legacy Rules (using legacy IP addresses, for migration)
# Each app has rules for Production, Non-Production, Pre-Production
# ============================================================

SEED_LEGACY_RULES: list[dict[str, Any]] = []

def _build_legacy_rules() -> list[dict[str, Any]]:
    """Build comprehensive legacy rules for all apps across environments."""
    rules: list[dict[str, Any]] = []
    seq = 1000

    # App configs: (app_id, name, dist_id, legacy_dc, envs_with_rules)
    # Zone names use actual NGDC Security Zones: Production Fabric (STD, GEN, PAA, 3PY, CCS, CDE, CPA, Swift, PSE, UC)
    # and Non-Production Fabric (UGen, USTD, UPAA, UCPA, UCDE, UCCS, U3PY)
    app_configs = [
        ("CRM", "Customer Relationship Manager", "AD-1001", "DC_LEGACY_A",
         {"Production": ("pol-CRM-legacy", "LegacyFW-A", "STD", "GEN"),
          "Non-Production": ("pol-CRM-np-legacy", "LegacyFW-A-NP", "USTD", "UGen"),
          "Pre-Production": ("pol-CRM-pp-legacy", "LegacyFW-A-PP", "USTD", "UGen")}),
        ("HRM", "Human Resource Manager", "AD-1002", "DC_LEGACY_B",
         {"Production": ("pol-HRM-legacy", "LegacyFW-B", "GEN", "STD"),
          "Non-Production": ("pol-HRM-np-legacy", "LegacyFW-B-NP", "UGen", "USTD")}),
        ("TRD", "Trading Platform", "AD-1003", "DC_LEGACY_C",
         {"Production": ("pol-TRD-legacy", "LegacyFW-C", "CDE", "CPA"),
          "Non-Production": ("pol-TRD-np-legacy", "LegacyFW-C-NP", "UCDE", "UCPA"),
          "Pre-Production": ("pol-TRD-pp-legacy", "LegacyFW-C-PP", "UCDE", "UCPA")}),
        ("PAY", "Payment Gateway", "AD-1004", "DC_LEGACY_A",
         {"Production": ("pol-PAY-legacy", "LegacyFW-A", "CCS", "CDE"),
          "Pre-Production": ("pol-PAY-pp-legacy", "LegacyFW-A-PP", "UCCS", "UCDE")}),
        ("INS", "Insurance Portal", "AD-1005", "DC_LEGACY_D",
         {"Production": ("pol-INS-legacy", "LegacyFW-D", "STD", "PAA"),
          "Non-Production": ("pol-INS-np-legacy", "LegacyFW-D-NP", "USTD", "UPAA")}),
        ("KYC", "KYC Compliance", "AD-1006", "DC_LEGACY_F",
         {"Production": ("pol-KYC-legacy", "LegacyFW-F", "CCS", "CDE"),
          "Non-Production": ("pol-KYC-np-legacy", "LegacyFW-F-NP", "UCCS", "UCDE")}),
        ("FRD", "Fraud Detection", "AD-1007", "DC_LEGACY_E",
         {"Production": ("pol-FRD-legacy", "LegacyFW-E", "CDE", "Swift")}),
        ("LND", "Lending Platform", "AD-1008", "DC_LEGACY_D",
         {"Production": ("pol-LND-legacy", "LegacyFW-D", "GEN", "CPA"),
          "Non-Production": ("pol-LND-np-legacy", "LegacyFW-D-NP", "UGen", "UCPA")}),
        ("WLT", "Wealth Management", "AD-1009", "DC_LEGACY_B",
         {"Production": ("pol-WLT-legacy", "LegacyFW-B", "PAA", "3PY"),
          "Pre-Production": ("pol-WLT-pp-legacy", "LegacyFW-B-PP", "UPAA", "U3PY")}),
        ("CBK", "Core Banking", "AD-1010", "DC_LEGACY_A",
         {"Production": ("pol-CBK-legacy", "LegacyFW-A", "CPA", "CDE"),
          "Non-Production": ("pol-CBK-np-legacy", "LegacyFW-A-NP", "UCPA", "UCDE"),
          "Pre-Production": ("pol-CBK-pp-legacy", "LegacyFW-A-PP", "UCPA", "UCDE")}),
    ]

    # IP base per legacy DC
    dc_ip = {"DC_LEGACY_A": "10.25", "DC_LEGACY_B": "10.26", "DC_LEGACY_C": "10.27",
             "DC_LEGACY_D": "10.28", "DC_LEGACY_E": "10.29", "DC_LEGACY_F": "10.30"}

    for app_id, app_name, dist_id, legacy_dc, envs in app_configs:
        base = dc_ip[legacy_dc]
        for env_name, (policy, inventory, src_zone, dst_zone) in envs.items():
            # Rule 1: WEB -> APP (HTTPS)
            seq += 1
            rules.append({
                "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                "app_name": app_name, "inventory_item": inventory,
                "policy_name": policy, "environment": env_name,
                "rule_global": False, "rule_action": "Accept",
                "rule_source": f"svr-{base}.1.10\nsvr-{base}.1.11",
                "rule_source_expanded": f"svr-{base}.1.10\n  {base}.1.10 (Web Server 1)\nsvr-{base}.1.11\n  {base}.1.11 (Web Server 2)",
                "rule_source_zone": src_zone,
                "rule_destination": f"svr-{base}.2.10\nsvr-{base}.2.11\nsvr-{base}.2.12",
                "rule_destination_expanded": f"svr-{base}.2.10\n  {base}.2.10 (App Server 1)\nsvr-{base}.2.11\n  {base}.2.11 (App Server 2)\nsvr-{base}.2.12\n  {base}.2.12 (App Server 3)",
                "rule_destination_zone": dst_zone,
                "rule_service": "tcp/443",
                "rule_service_expanded": "tcp/443 (HTTPS)",
                "is_standard": True, "rn": 1, "rc": 1,
                "migration_status": "Not Started",
            })
            # Rule 2: APP -> DB (Oracle/SQL)
            seq += 1
            rules.append({
                "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                "app_name": app_name, "inventory_item": inventory,
                "policy_name": policy, "environment": env_name,
                "rule_global": False, "rule_action": "Accept",
                "rule_source": f"svr-{base}.2.10\nsvr-{base}.2.11\nsvr-{base}.2.12",
                "rule_source_expanded": f"svr-{base}.2.10\n  {base}.2.10 (App 1)\nsvr-{base}.2.11\n  {base}.2.11 (App 2)\nsvr-{base}.2.12\n  {base}.2.12 (App 3)",
                "rule_source_zone": src_zone,
                "rule_destination": f"svr-{base}.3.10\nsvr-{base}.3.11",
                "rule_destination_expanded": f"svr-{base}.3.10\n  {base}.3.10 (DB Primary)\nsvr-{base}.3.11\n  {base}.3.11 (DB Standby)",
                "rule_destination_zone": dst_zone,
                "rule_service": "tcp/1521\ntcp/1433",
                "rule_service_expanded": "tcp/1521 (Oracle)\ntcp/1433 (SQL Server)",
                "is_standard": True, "rn": 2, "rc": 1,
                "migration_status": "Not Started",
            })
            # Rule 3: APP -> MQ (if app has MQ)
            if app_id in ("TRD", "PAY", "FRD", "CBK"):
                seq += 1
                rules.append({
                    "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                    "app_name": app_name, "inventory_item": inventory,
                    "policy_name": policy, "environment": env_name,
                    "rule_global": False, "rule_action": "Accept",
                    "rule_source": f"svr-{base}.2.10\nsvr-{base}.2.11",
                    "rule_source_expanded": f"svr-{base}.2.10\n  App 1\nsvr-{base}.2.11\n  App 2",
                    "rule_source_zone": src_zone,
                    "rule_destination": f"svr-{base}.4.10\nsvr-{base}.4.11",
                    "rule_destination_expanded": f"svr-{base}.4.10\n  MQ Broker 1\nsvr-{base}.4.11\n  MQ Broker 2",
                    "rule_destination_zone": dst_zone,
                    "rule_service": "tcp/5672\ntcp/9092",
                    "rule_service_expanded": "tcp/5672 (AMQP)\ntcp/9092 (Kafka)",
                    "is_standard": True, "rn": 3, "rc": 1,
                    "migration_status": "Not Started",
                })
            # Rule 4: APP -> External API (non-standard, cross-zone)
            seq += 1
            rules.append({
                "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                "app_name": app_name, "inventory_item": inventory,
                "policy_name": policy, "environment": env_name,
                "rule_global": False, "rule_action": "Accept",
                "rule_source": f"svr-{base}.2.10",
                "rule_source_expanded": f"svr-{base}.2.10\n  App Server 1",
                "rule_source_zone": src_zone,
                "rule_destination": "svr-10.70.1.10\nsvr-10.70.1.11",
                "rule_destination_expanded": "svr-10.70.1.10\n  DMZ API 1\nsvr-10.70.1.11\n  DMZ API 2",
                "rule_destination_zone": "PSE",
                "rule_service": "tcp/443\ntcp/8443",
                "rule_service_expanded": "tcp/443 (HTTPS)\ntcp/8443 (Alt HTTPS)",
                "is_standard": False, "rn": 4, "rc": 1,
                "migration_status": "Not Started",
            })
            # Rule 5: Batch -> DB
            if app_id in ("CRM", "HRM", "TRD", "INS", "LND", "CBK"):
                seq += 1
                rules.append({
                    "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                    "app_name": app_name, "inventory_item": inventory,
                    "policy_name": policy, "environment": env_name,
                    "rule_global": False, "rule_action": "Accept",
                    "rule_source": f"svr-{base}.5.10",
                    "rule_source_expanded": f"svr-{base}.5.10\n  Batch Server 1",
                    "rule_source_zone": src_zone,
                    "rule_destination": f"svr-{base}.3.10",
                    "rule_destination_expanded": f"svr-{base}.3.10\n  DB Primary",
                    "rule_destination_zone": dst_zone,
                    "rule_service": "tcp/1521",
                    "rule_service_expanded": "tcp/1521 (Oracle)",
                    "is_standard": True, "rn": 5, "rc": 1,
                    "migration_status": "Not Started",
                })
            # Rule 6: Monitoring / Management access (range)
            seq += 1
            rules.append({
                "id": f"LR-{seq}", "app_id": app_id, "app_distributed_id": dist_id,
                "app_name": app_name, "inventory_item": inventory,
                "policy_name": policy, "environment": env_name,
                "rule_global": True, "rule_action": "Accept",
                "rule_source": "svr-10.80.1.100\nsvr-10.80.1.101",
                "rule_source_expanded": "svr-10.80.1.100\n  Monitor Agent 1\nsvr-10.80.1.101\n  Monitor Agent 2",
                "rule_source_zone": "UC",
                "rule_destination": f"rng-{base}.1.10-12\nsvr-{base}.3.10",
                "rule_destination_expanded": f"rng-{base}.1.10-12\n  Web/App range\nsvr-{base}.3.10\n  DB Primary",
                "rule_destination_zone": dst_zone,
                "rule_service": "tcp/161\ntcp/22\ntcp/10050",
                "rule_service_expanded": "tcp/161 (SNMP)\ntcp/22 (SSH)\ntcp/10050 (Zabbix)",
                "is_standard": True, "rn": 6, "rc": 1,
                "migration_status": "Not Started",
            })

    return rules


# ============================================================
# App-Based IP Mappings (Legacy DC -> NGDC, per app)
# ============================================================

SEED_IP_MAPPINGS: list[dict[str, Any]] = []

def _build_ip_mappings() -> list[dict[str, Any]]:
    """Build comprehensive app-based IP mappings covering ALL legacy rule IPs.

    Each legacy rule has source and destination IPs that may map to DIFFERENT
    NGDC zones/NHs.  We provide separate source-side and destination-side
    mappings so that `_lookup_ngdc_ip` can resolve every IP used in seed rules.

    Legacy rule IP pattern per app (base = dc_ip[legacy_dc]):
      Rule 1 WEB→APP : src {base}.1.10/.11     dst {base}.2.10/.11/.12
      Rule 2 APP→DB  : src {base}.2.10/.11/.12  dst {base}.3.10/.11
      Rule 3 APP→MQ  : src {base}.2.10/.11      dst {base}.4.10/.11
      Rule 4 APP→Ext : src {base}.2.10           dst 10.70.1.10/.11 (PSE)
      Rule 5 BAT→DB  : src {base}.5.10           dst {base}.3.10
      Rule 6 MON→ALL : src 10.80.1.100/.101 (UC) dst rng-{base}.1.10-12, svr-{base}.3.10
    """
    mappings: list[dict[str, Any]] = []
    idx = 0

    # Full mapping config per app.
    # Each entry: (app_id, legacy_dc, ngdc_dc, entries_list)
    # entries_list items: (legacy_ip, ngdc_ip, ngdc_group, desc, nh, sz)
    mapping_configs = [
        # ================================================================
        # CRM: DC_LEGACY_A, src_zone=STD, dst_zone=GEN
        # Source side: NH02/STD (CRM WEB/APP/BAT), Destination side: NH02/GEN
        # ================================================================
        ("CRM", "DC_LEGACY_A", "GAMMA_NGDC", [
            # Source IPs (STD zone)
            ("10.25.1.10", "svr-10.50.1.10", "grp-CRM-NH02-STD-WEB", "CRM Web 1", "NH02", "STD"),
            ("10.25.1.11", "svr-10.50.1.11", "grp-CRM-NH02-STD-WEB", "CRM Web 2", "NH02", "STD"),
            ("10.25.2.10", "svr-10.50.1.20", "grp-CRM-NH02-STD-APP", "CRM App 1", "NH02", "STD"),
            ("10.25.2.11", "svr-10.50.1.21", "grp-CRM-NH02-STD-APP", "CRM App 2", "NH02", "STD"),
            ("10.25.2.12", "svr-10.50.1.22", "grp-CRM-NH02-STD-APP", "CRM App 3", "NH02", "STD"),
            ("10.25.5.10", "svr-10.50.1.40", "grp-CRM-NH02-STD-BAT", "CRM Batch 1", "NH02", "STD"),
            # Destination IPs (GEN zone)
            ("10.25.3.10", "svr-10.50.1.30", "grp-CRM-NH02-GEN-DB", "CRM DB Primary", "NH02", "GEN"),
            ("10.25.3.11", "svr-10.50.1.31", "grp-CRM-NH02-GEN-DB", "CRM DB Standby", "NH02", "GEN"),
            ("10.25.4.10", "svr-10.50.1.42", "grp-CRM-NH02-GEN-MQ", "CRM MQ 1", "NH02", "GEN"),
            ("10.25.4.11", "svr-10.50.1.43", "grp-CRM-NH02-GEN-MQ", "CRM MQ 2", "NH02", "GEN"),
        ]),
        # ================================================================
        # HRM: DC_LEGACY_B, src_zone=GEN, dst_zone=STD
        # Source side: NH01/GEN, Destination side: NH01/STD
        # ================================================================
        ("HRM", "DC_LEGACY_B", "ALPHA_NGDC", [
            # Source IPs (GEN zone)
            ("10.26.1.10", "svr-10.0.2.130", "grp-HRM-NH01-GEN-WEB", "HRM Web 1", "NH01", "GEN"),
            ("10.26.1.11", "svr-10.0.2.131", "grp-HRM-NH01-GEN-WEB", "HRM Web 2", "NH01", "GEN"),
            ("10.26.2.10", "svr-10.0.2.140", "grp-HRM-NH01-GEN-APP", "HRM App 1", "NH01", "GEN"),
            ("10.26.2.11", "svr-10.0.2.141", "grp-HRM-NH01-GEN-APP", "HRM App 2", "NH01", "GEN"),
            ("10.26.2.12", "svr-10.0.2.142", "grp-HRM-NH01-GEN-APP", "HRM App 3", "NH01", "GEN"),
            ("10.26.5.10", "svr-10.0.2.160", "grp-HRM-NH01-GEN-BAT", "HRM Batch 1", "NH01", "GEN"),
            # Destination IPs (STD zone)
            ("10.26.3.10", "svr-10.0.2.150", "grp-HRM-NH01-STD-DB", "HRM DB Primary", "NH01", "STD"),
            ("10.26.3.11", "svr-10.0.2.151", "grp-HRM-NH01-STD-DB", "HRM DB Replica", "NH01", "STD"),
            ("10.26.4.10", "svr-10.0.2.162", "grp-HRM-NH01-STD-MQ", "HRM MQ 1", "NH01", "STD"),
            ("10.26.4.11", "svr-10.0.2.163", "grp-HRM-NH01-STD-MQ", "HRM MQ 2", "NH01", "STD"),
        ]),
        # ================================================================
        # TRD: DC_LEGACY_C, src_zone=CDE, dst_zone=CPA
        # Source side: NH06/CDE, Destination side: NH07/CPA
        # ================================================================
        ("TRD", "DC_LEGACY_C", "BETA_NGDC", [
            # Source IPs (CDE zone, NH06)
            ("10.27.1.10", "svr-172.16.20.10", "grp-TRD-NH06-CDE-WEB", "TRD Web 1", "NH06", "CDE"),
            ("10.27.1.11", "svr-172.16.20.11", "grp-TRD-NH06-CDE-WEB", "TRD Web 2", "NH06", "CDE"),
            ("10.27.2.10", "svr-172.16.20.20", "grp-TRD-NH06-CDE-APP", "TRD App 1", "NH06", "CDE"),
            ("10.27.2.11", "svr-172.16.20.21", "grp-TRD-NH06-CDE-APP", "TRD App 2", "NH06", "CDE"),
            ("10.27.2.12", "svr-172.16.20.22", "grp-TRD-NH06-CDE-APP", "TRD App 3", "NH06", "CDE"),
            ("10.27.5.10", "svr-172.16.20.50", "grp-TRD-NH06-CDE-BAT", "TRD Batch 1", "NH06", "CDE"),
            # Destination IPs (CPA zone, NH07)
            ("10.27.3.10", "svr-10.6.1.30", "grp-TRD-NH07-CPA-DB", "TRD DB Primary", "NH07", "CPA"),
            ("10.27.3.11", "svr-10.6.1.31", "grp-TRD-NH07-CPA-DB", "TRD DB Standby", "NH07", "CPA"),
            ("10.27.4.10", "svr-10.6.1.40", "grp-TRD-NH07-CPA-MQ", "TRD MQ Broker 1", "NH07", "CPA"),
            ("10.27.4.11", "svr-10.6.1.41", "grp-TRD-NH07-CPA-MQ", "TRD MQ Broker 2", "NH07", "CPA"),
        ]),
        # ================================================================
        # PAY: DC_LEGACY_A, src_zone=CCS, dst_zone=CDE
        # Source side: NH08/CCS, Destination side: NH07/CDE
        # ================================================================
        ("PAY", "DC_LEGACY_A", "GAMMA_NGDC", [
            # Source IPs (CCS zone, NH08)
            ("10.25.1.10", "svr-10.50.8.10", "grp-PAY-NH08-CCS-WEB", "PAY Web 1", "NH08", "CCS"),
            ("10.25.1.11", "svr-10.50.8.11", "grp-PAY-NH08-CCS-WEB", "PAY Web 2", "NH08", "CCS"),
            ("10.25.2.10", "svr-10.50.8.20", "grp-PAY-NH08-CCS-APP", "PAY App 1", "NH08", "CCS"),
            ("10.25.2.11", "svr-10.50.8.21", "grp-PAY-NH08-CCS-APP", "PAY App 2", "NH08", "CCS"),
            ("10.25.2.12", "svr-10.50.8.22", "grp-PAY-NH08-CCS-APP", "PAY App 3", "NH08", "CCS"),
            # Destination IPs (CDE zone, NH07)
            ("10.25.3.10", "svr-10.50.7.30", "grp-PAY-NH07-CDE-DB", "PAY DB Primary", "NH07", "CDE"),
            ("10.25.3.11", "svr-10.50.7.31", "grp-PAY-NH07-CDE-DB", "PAY DB Standby", "NH07", "CDE"),
            ("10.25.4.10", "svr-10.50.7.40", "grp-PAY-NH07-CDE-MQ", "PAY MQ 1", "NH07", "CDE"),
            ("10.25.4.11", "svr-10.50.7.41", "grp-PAY-NH07-CDE-MQ", "PAY MQ 2", "NH07", "CDE"),
            ("10.25.5.10", "svr-10.50.8.50", "grp-PAY-NH08-CCS-BAT", "PAY Batch 1", "NH08", "CCS"),
        ]),
        # ================================================================
        # INS: DC_LEGACY_D, src_zone=STD, dst_zone=PAA
        # Source side: NH04/STD, Destination side: NH14/PAA
        # ================================================================
        ("INS", "DC_LEGACY_D", "ALPHA_NGDC", [
            # Source IPs (STD zone, NH04)
            ("10.28.1.10", "svr-10.3.1.130", "grp-INS-NH04-STD-WEB", "INS Web 1", "NH04", "STD"),
            ("10.28.1.11", "svr-10.3.1.131", "grp-INS-NH04-STD-WEB", "INS Web 2", "NH04", "STD"),
            ("10.28.2.10", "svr-10.3.1.140", "grp-INS-NH04-STD-APP", "INS App 1", "NH04", "STD"),
            ("10.28.2.11", "svr-10.3.1.141", "grp-INS-NH04-STD-APP", "INS App 2", "NH04", "STD"),
            ("10.28.2.12", "svr-10.3.1.142", "grp-INS-NH04-STD-APP", "INS App 3", "NH04", "STD"),
            ("10.28.5.10", "svr-10.3.1.160", "grp-INS-NH04-STD-BAT", "INS Batch 1", "NH04", "STD"),
            # Destination IPs (PAA zone, NH14)
            ("10.28.3.10", "svr-10.70.4.30", "grp-INS-NH14-PAA-DB", "INS DB Primary", "NH14", "PAA"),
            ("10.28.3.11", "svr-10.70.4.31", "grp-INS-NH14-PAA-DB", "INS DB Standby", "NH14", "PAA"),
            ("10.28.4.10", "svr-10.70.4.40", "grp-INS-NH14-PAA-MQ", "INS MQ 1", "NH14", "PAA"),
            ("10.28.4.11", "svr-10.70.4.41", "grp-INS-NH14-PAA-MQ", "INS MQ 2", "NH14", "PAA"),
        ]),
        # ================================================================
        # KYC: DC_LEGACY_F, src_zone=CCS, dst_zone=CDE
        # Source side: NH05/CCS, Destination side: NH05/CDE
        # ================================================================
        ("KYC", "DC_LEGACY_F", "ALPHA_NGDC", [
            # Source IPs (CCS zone, NH05)
            ("10.30.1.10", "svr-10.4.1.130", "grp-KYC-NH05-CCS-WEB", "KYC Web 1", "NH05", "CCS"),
            ("10.30.1.11", "svr-10.4.1.131", "grp-KYC-NH05-CCS-WEB", "KYC Web 2", "NH05", "CCS"),
            ("10.30.2.10", "svr-10.4.1.140", "grp-KYC-NH05-CCS-APP", "KYC App 1", "NH05", "CCS"),
            ("10.30.2.11", "svr-10.4.1.141", "grp-KYC-NH05-CCS-APP", "KYC App 2", "NH05", "CCS"),
            ("10.30.2.12", "svr-10.4.1.142", "grp-KYC-NH05-CCS-APP", "KYC App 3", "NH05", "CCS"),
            # Destination IPs (CDE zone, NH05)
            ("10.30.3.10", "svr-10.4.2.10", "grp-KYC-NH05-CDE-DB", "KYC DB Primary", "NH05", "CDE"),
            ("10.30.3.11", "svr-10.4.2.11", "grp-KYC-NH05-CDE-DB", "KYC DB Standby", "NH05", "CDE"),
            ("10.30.4.10", "svr-10.4.2.20", "grp-KYC-NH05-CDE-MQ", "KYC MQ 1", "NH05", "CDE"),
            ("10.30.4.11", "svr-10.4.2.21", "grp-KYC-NH05-CDE-MQ", "KYC MQ 2", "NH05", "CDE"),
            ("10.30.5.10", "svr-10.4.1.160", "grp-KYC-NH05-CCS-BAT", "KYC Batch 1", "NH05", "CCS"),
        ]),
        # ================================================================
        # FRD: DC_LEGACY_E, src_zone=CDE, dst_zone=Swift
        # Source side: NH02/CDE, Destination side: NH02/Swift
        # ================================================================
        ("FRD", "DC_LEGACY_E", "ALPHA_NGDC", [
            # Source IPs (CDE zone, NH02)
            ("10.29.1.10", "svr-10.1.1.110", "grp-FRD-NH02-CDE-WEB", "FRD Web 1", "NH02", "CDE"),
            ("10.29.1.11", "svr-10.1.1.111", "grp-FRD-NH02-CDE-WEB", "FRD Web 2", "NH02", "CDE"),
            ("10.29.2.10", "svr-10.1.1.50", "grp-FRD-NH02-CDE-APP", "FRD Engine 1", "NH02", "CDE"),
            ("10.29.2.11", "svr-10.1.1.51", "grp-FRD-NH02-CDE-APP", "FRD Engine 2", "NH02", "CDE"),
            ("10.29.2.12", "svr-10.1.1.52", "grp-FRD-NH02-CDE-APP", "FRD Engine 3", "NH02", "CDE"),
            ("10.29.5.10", "svr-10.1.1.60", "grp-FRD-NH02-CDE-BAT", "FRD Batch 1", "NH02", "CDE"),
            # Destination IPs (Swift zone, NH02)
            ("10.29.3.10", "svr-10.1.2.20", "grp-FRD-NH02-Swift-DB", "FRD DB Primary", "NH02", "Swift"),
            ("10.29.3.11", "svr-10.1.2.21", "grp-FRD-NH02-Swift-DB", "FRD DB Standby", "NH02", "Swift"),
            ("10.29.4.10", "svr-10.1.1.55", "grp-FRD-NH02-Swift-MQ", "FRD Kafka 1", "NH02", "Swift"),
            ("10.29.4.11", "svr-10.1.1.56", "grp-FRD-NH02-Swift-MQ", "FRD Kafka 2", "NH02", "Swift"),
        ]),
        # ================================================================
        # LND: DC_LEGACY_D, src_zone=GEN, dst_zone=CPA
        # Source side: NH09/GEN, Destination side: NH09/CPA
        # ================================================================
        ("LND", "DC_LEGACY_D", "ALPHA_NGDC", [
            # Source IPs (GEN zone, NH09)
            ("10.28.1.10", "svr-10.8.1.130", "grp-LND-NH09-GEN-WEB", "LND Web 1", "NH09", "GEN"),
            ("10.28.1.11", "svr-10.8.1.131", "grp-LND-NH09-GEN-WEB", "LND Web 2", "NH09", "GEN"),
            ("10.28.2.10", "svr-10.8.1.140", "grp-LND-NH09-GEN-APP", "LND App 1", "NH09", "GEN"),
            ("10.28.2.11", "svr-10.8.1.141", "grp-LND-NH09-GEN-APP", "LND App 2", "NH09", "GEN"),
            ("10.28.2.12", "svr-10.8.1.142", "grp-LND-NH09-GEN-APP", "LND App 3", "NH09", "GEN"),
            ("10.28.5.10", "svr-10.8.1.160", "grp-LND-NH09-GEN-BAT", "LND Batch 1", "NH09", "GEN"),
            # Destination IPs (CPA zone, NH09)
            ("10.28.3.10", "svr-10.8.2.30", "grp-LND-NH09-CPA-DB", "LND DB Primary", "NH09", "CPA"),
            ("10.28.3.11", "svr-10.8.2.31", "grp-LND-NH09-CPA-DB", "LND DB Standby", "NH09", "CPA"),
            ("10.28.4.10", "svr-10.8.2.40", "grp-LND-NH09-CPA-MQ", "LND MQ 1", "NH09", "CPA"),
            ("10.28.4.11", "svr-10.8.2.41", "grp-LND-NH09-CPA-MQ", "LND MQ 2", "NH09", "CPA"),
        ]),
        # ================================================================
        # WLT: DC_LEGACY_B, src_zone=PAA, dst_zone=3PY
        # Source side: NH14/PAA, Destination side: NH10/3PY
        # ================================================================
        ("WLT", "DC_LEGACY_B", "ALPHA_NGDC", [
            # Source IPs (PAA zone, NH14)
            ("10.26.1.10", "svr-10.70.1.100", "grp-WLT-NH14-PAA-WEB", "WLT Web 1", "NH14", "PAA"),
            ("10.26.1.11", "svr-10.70.1.101", "grp-WLT-NH14-PAA-WEB", "WLT Web 2", "NH14", "PAA"),
            ("10.26.2.10", "svr-10.9.1.20", "grp-WLT-NH10-PAA-APP", "WLT App 1", "NH10", "PAA"),
            ("10.26.2.11", "svr-10.9.1.21", "grp-WLT-NH10-PAA-APP", "WLT App 2", "NH10", "PAA"),
            ("10.26.2.12", "svr-10.9.1.22", "grp-WLT-NH10-PAA-APP", "WLT App 3", "NH10", "PAA"),
            # Destination IPs (3PY zone, NH10)
            ("10.26.3.10", "svr-10.9.1.30", "grp-WLT-NH10-3PY-DB", "WLT DB Primary", "NH10", "3PY"),
            ("10.26.3.11", "svr-10.9.1.31", "grp-WLT-NH10-3PY-DB", "WLT DB Standby", "NH10", "3PY"),
            ("10.26.4.10", "svr-10.9.1.40", "grp-WLT-NH10-3PY-MQ", "WLT MQ 1", "NH10", "3PY"),
            ("10.26.4.11", "svr-10.9.1.41", "grp-WLT-NH10-3PY-MQ", "WLT MQ 2", "NH10", "3PY"),
            ("10.26.5.10", "svr-10.9.1.50", "grp-WLT-NH10-PAA-BAT", "WLT Batch 1", "NH10", "PAA"),
        ]),
        # ================================================================
        # CBK: DC_LEGACY_A, src_zone=CPA, dst_zone=CDE
        # Source side: NH08/CPA, Destination side: NH08/CDE
        # ================================================================
        ("CBK", "DC_LEGACY_A", "ALPHA_NGDC", [
            # Source IPs (CPA zone, NH08)
            ("10.25.1.10", "svr-10.7.1.10", "grp-CBK-NH08-CPA-WEB", "CBK Web 1", "NH08", "CPA"),
            ("10.25.1.11", "svr-10.7.1.11", "grp-CBK-NH08-CPA-WEB", "CBK Web 2", "NH08", "CPA"),
            ("10.25.2.10", "svr-10.7.1.20", "grp-CBK-NH08-CPA-APP", "CBK App 1", "NH08", "CPA"),
            ("10.25.2.11", "svr-10.7.1.21", "grp-CBK-NH08-CPA-APP", "CBK App 2", "NH08", "CPA"),
            ("10.25.2.12", "svr-10.7.1.22", "grp-CBK-NH08-CPA-APP", "CBK App 3", "NH08", "CPA"),
            ("10.25.5.10", "svr-10.7.1.50", "grp-CBK-NH08-CPA-BAT", "CBK Batch 1", "NH08", "CPA"),
            # Destination IPs (CDE zone, NH08)
            ("10.25.3.10", "svr-10.7.2.30", "grp-CBK-NH08-CDE-DB", "CBK DB Primary", "NH08", "CDE"),
            ("10.25.3.11", "svr-10.7.2.31", "grp-CBK-NH08-CDE-DB", "CBK DB Standby", "NH08", "CDE"),
            ("10.25.4.10", "svr-10.7.2.40", "grp-CBK-NH08-CDE-MQ", "CBK MQ 1", "NH08", "CDE"),
            ("10.25.4.11", "svr-10.7.2.41", "grp-CBK-NH08-CDE-MQ", "CBK MQ 2", "NH08", "CDE"),
        ]),
        # ================================================================
        # Shared / Cross-app IPs (PSE zone, UC zone)
        # Rule 4: APP→External API destinations (10.70.1.10/.11 in PSE)
        # Rule 6: Monitoring source IPs (10.80.1.100/.101 in UC)
        # ================================================================
        ("SHARED", "SHARED", "ALPHA_NGDC", [
            # PSE zone destinations (used by all apps Rule 4)
            ("10.70.1.10", "svr-10.70.1.10", "grp-SHARED-NH14-PSE-API", "DMZ API 1", "NH14", "PSE"),
            ("10.70.1.11", "svr-10.70.1.11", "grp-SHARED-NH14-PSE-API", "DMZ API 2", "NH14", "PSE"),
            # UC zone monitoring sources (used by all apps Rule 6)
            ("10.80.1.100", "svr-10.80.1.100", "grp-SHARED-NH01-UC-MON", "Monitor Agent 1", "NH01", "UC"),
            ("10.80.1.101", "svr-10.80.1.101", "grp-SHARED-NH01-UC-MON", "Monitor Agent 2", "NH01", "UC"),
        ]),
    ]

    for app_id, legacy_dc, ngdc_dc, entries in mapping_configs:
        for legacy_ip, ngdc_ip, ngdc_group, desc, nh, sz in entries:
            idx += 1
            mappings.append({
                "id": f"ipm-{idx:04d}",
                "app_id": app_id,
                "legacy_dc": legacy_dc,
                "ngdc_dc": ngdc_dc,
                "legacy_ip": legacy_ip,
                "ngdc_ip": ngdc_ip,
                "ngdc_group": ngdc_group,
                "legacy_desc": f"{desc} (Legacy)",
                "ngdc_desc": f"{desc} (NGDC)",
                "nh": nh,
                "sz": sz,
            })

    return mappings


def build_seed_migrations() -> list[dict[str, Any]]:
    """Build seed migration records for all apps."""
    from datetime import datetime, timedelta
    now = datetime.utcnow().isoformat()
    migrations = []
    apps_mig = [
        ("mig-001", "CRM", "DC_LEGACY_A", "GAMMA_NGDC", "In Progress", 35, 45, 16, 2, -60),
        ("mig-002", "HRM", "DC_LEGACY_B", "ALPHA_NGDC", "In Progress", 60, 32, 19, 1, -45),
        ("mig-003", "TRD", "DC_LEGACY_C", "BETA_NGDC", "Planning", 10, 58, 0, 0, -15),
        ("mig-004", "INS", "DC_LEGACY_D", "ALPHA_NGDC", "In Progress", 45, 28, 12, 3, -30),
        ("mig-005", "FRD", "DC_LEGACY_E", "ALPHA_NGDC", "Completed", 100, 22, 22, 0, -90),
        ("mig-006", "KYC", "DC_LEGACY_F", "ALPHA_NGDC", "In Progress", 25, 38, 9, 1, -20),
        ("mig-007", "PAY", "DC_LEGACY_A", "GAMMA_NGDC", "Planning", 5, 40, 0, 0, -10),
        ("mig-008", "LND", "DC_LEGACY_D", "ALPHA_NGDC", "In Progress", 50, 30, 15, 2, -35),
        ("mig-009", "WLT", "DC_LEGACY_B", "ALPHA_NGDC", "Planning", 0, 35, 0, 0, -5),
        ("mig-010", "CBK", "DC_LEGACY_A", "ALPHA_NGDC", "In Progress", 20, 55, 11, 4, -25),
    ]
    for mid, app, src, tgt, status, prog, total, migrated, failed, days in apps_mig:
        migrations.append({
            "migration_id": mid, "name": f"{app} Migration to NGDC",
            "application": app, "source_legacy_dc": src, "target_ngdc": tgt,
            "legacy_dc": src, "target_dc": tgt,
            "status": status, "progress": prog,
            "total_rules": total, "migrated_rules": migrated, "failed_rules": failed,
            "created_at": (datetime.utcnow() + timedelta(days=days)).isoformat(),
            "updated_at": now,
        })
    return migrations


def build_seed_chg_requests() -> list[dict[str, Any]]:
    """Build seed change requests aligned with NGDC rule IDs from _build_seed_rules."""
    from datetime import datetime, timedelta
    return [
        {"chg_id": "CHG10001", "rule_ids": ["R-3001", "R-3002"], "status": "Approved",
         "description": "CRM Web-to-App and App-to-DB rule deployment (NH02/CDE intra-zone)",
         "requested_by": "Team Eta", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-31)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-30)).isoformat()},
        {"chg_id": "CHG10002", "rule_ids": ["R-3005", "R-3006", "R-3007"], "status": "Approved",
         "description": "TRD Trading Platform NGDC rules - Web/App/DB connectivity (NH06/CDE)",
         "requested_by": "Team Xi", "approved_by": "Network Team",
         "created_at": (datetime.utcnow() + timedelta(days=-120)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-119)).isoformat()},
        {"chg_id": "CHG10003", "rule_ids": ["R-3009", "R-3010", "R-3011"], "status": "Approved",
         "description": "PAY Payment Processing NGDC rules (NH07/CPA)",
         "requested_by": "Team Epsilon", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-150)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-149)).isoformat()},
        {"chg_id": "CHG10004", "rule_ids": ["R-3038"], "status": "Pending",
         "description": "PAY to FRD fraud check cross-zone rule (CPA to CDE, LDF-003)",
         "requested_by": "Team Epsilon", "approved_by": None,
         "created_at": (datetime.utcnow() + timedelta(days=-10)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-10)).isoformat()},
        {"chg_id": "CHG10005", "rule_ids": ["R-3043", "R-3044"], "status": "Approved",
         "description": "Cross-NH CDE rules: CRM-to-WLT and WLT-to-TRD portfolio data (LDF-004)",
         "requested_by": "Team Eta", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-25)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-24)).isoformat()},
        {"chg_id": "CHG10006", "rule_ids": ["R-3050", "R-3051", "R-3052"], "status": "Pending",
         "description": "EPT Enterprise Portal PAA flow rules to CRM/CBK/PAY (LDF-006)",
         "requested_by": "Team Platform", "approved_by": None,
         "created_at": (datetime.utcnow() + timedelta(days=-4)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-4)).isoformat()},
        {"chg_id": "CHG10007", "rule_ids": ["R-3015", "R-3016", "R-3017", "R-3018"], "status": "Approved",
         "description": "CBK Core Banking full stack deployment (NH08/CCS)",
         "requested_by": "Team Theta", "approved_by": "Network Team",
         "created_at": (datetime.utcnow() + timedelta(days=-200)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-199)).isoformat()},
        {"chg_id": "CHG10008", "rule_ids": ["LR-1001", "LR-1002"], "status": "Approved",
         "description": "CRM Legacy rule migration batch - WEB and APP connectivity",
         "requested_by": "Migration Tool", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-60)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-59)).isoformat()},
    ]


def build_seed_reviews() -> list[dict[str, Any]]:
    """Build seed review requests aligned with NGDC rule IDs from _build_seed_rules.

    Covers lifecycle scenarios:
    - new_rule: Initial rule creation review
    - modification: Change to existing rule (with delta)
    - migration: Legacy-to-NGDC migration review (with delta)
    Statuses: Pending, Approved, Rejected
    """
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    reviews = [
        # 1. Approved new rule - CRM Web to App (R-3001, Deployed)
        {"id": "REV-seed-001", "rule_id": "R-3001",
         "rule_name": "CRM Web to App HTTPS", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Eta", "reviewer": "Security Team", "status": "Approved",
         "submitted_at": (now + timedelta(days=-35)).isoformat(),
         "reviewed_at": (now + timedelta(days=-34)).isoformat(),
         "comments": "CRM web-to-app HTTPS connectivity within NH02/CDE",
         "review_notes": "Approved - intra-NH/SZ traffic, LDF-002 compliant",
         "rule_summary": {"application": "CRM", "source": "grp-CRM-NH02-CDE-WEB",
                          "destination": "grp-CRM-NH02-CDE-APP", "ports": "TCP 443",
                          "environment": "Production"},
         "delta": None},
        # 2. Pending modification - TRD source IP added (R-3006)
        {"id": "REV-seed-002", "rule_id": "R-3006",
         "rule_name": "TRD App to DB Oracle", "request_type": "modification",
         "module": "firewall-management",
         "requestor": "Team Xi", "reviewer": None, "status": "Pending",
         "submitted_at": (now + timedelta(days=-1)).isoformat(),
         "reviewed_at": None,
         "comments": "Adding new app server svr-10.5.1.83 to TRD App group",
         "review_notes": None,
         "rule_summary": {"application": "TRD", "source": "grp-TRD-NH06-CDE-APP",
                          "destination": "grp-TRD-NH06-CDE-DB", "ports": "TCP 1521",
                          "environment": "Production"},
         "delta": {"added": {"rule_source": ["svr-10.5.1.83"]},
                   "removed": {}, "changed": {}}},
        # 3. Approved new rule - PAY App to MQ (R-3010, Certified)
        {"id": "REV-seed-003", "rule_id": "R-3010",
         "rule_name": "PAY App to MQ AMQP", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Epsilon", "reviewer": "Security Team", "status": "Approved",
         "submitted_at": (now + timedelta(days=-105)).isoformat(),
         "reviewed_at": (now + timedelta(days=-103)).isoformat(),
         "comments": "Payment message queue connectivity within NH07/CPA",
         "review_notes": "Approved - PCI controls verified, CPA zone compliance confirmed",
         "rule_summary": {"application": "PAY", "source": "grp-PAY-NH07-CPA-APP",
                          "destination": "grp-PAY-NH07-CPA-MQ", "ports": "TCP 5672",
                          "environment": "Production"},
         "delta": None},
        # 4. Rejected rule - HRM GEN to CRM CDE cross-zone blocked
        {"id": "REV-seed-004", "rule_id": "R-3030",
         "rule_name": "HRM App to CRM DB Cross-Zone", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Platform", "reviewer": "Security Team", "status": "Rejected",
         "submitted_at": (now + timedelta(days=-7)).isoformat(),
         "reviewed_at": (now + timedelta(days=-6)).isoformat(),
         "comments": "HRM needs access to CRM database for employee data sync",
         "review_notes": "REJECTED: GEN to CDE cross-zone traffic blocked per NGDC Prod Policy Matrix.",
         "rule_summary": {"application": "HRM", "source": "grp-HRM-NH01-GEN-APP",
                          "destination": "grp-CRM-NH02-CDE-DB", "ports": "TCP 1521",
                          "environment": "Production"},
         "delta": None},
        # 5. Pending migration review - FRD legacy to NGDC
        {"id": "REV-seed-005", "rule_id": "R-3012",
         "rule_name": "FRD Legacy Migration Rule", "request_type": "migration",
         "module": "migration-studio",
         "requestor": "Migration Tool", "reviewer": None, "status": "Pending",
         "submitted_at": (now + timedelta(hours=-6)).isoformat(),
         "reviewed_at": None,
         "comments": "Auto-generated migration from DC_LEGACY_E to ALPHA_NGDC with 1-1 IP mappings",
         "review_notes": None,
         "rule_summary": {"application": "FRD", "source": "grp-FRD-NH02-CDE-APP",
                          "destination": "grp-FRD-NH02-CDE-DB", "ports": "TCP 1521\nTCP 1433",
                          "environment": "Production"},
         "delta": {"added": {}, "removed": {},
                   "changed": {"rule_source": {"from": "10.29.2.10\n10.29.2.11", "to": "svr-10.1.2.10\nsvr-10.1.2.11"},
                               "rule_destination": {"from": "10.29.3.10", "to": "svr-10.1.2.20"},
                               "rule_source_zone": {"from": "Zone-E-Internal", "to": "CDE"},
                               "rule_destination_zone": {"from": "Zone-E-DB", "to": "CDE"}}}},
        # 6. Approved modification - CBK added API server (R-3017)
        {"id": "REV-seed-006", "rule_id": "R-3017",
         "rule_name": "CBK API Gateway Rule", "request_type": "modification",
         "module": "firewall-management",
         "requestor": "Team Theta", "reviewer": "Network Team", "status": "Approved",
         "submitted_at": (now + timedelta(days=-15)).isoformat(),
         "reviewed_at": (now + timedelta(days=-14)).isoformat(),
         "comments": "Adding new CBK API endpoint svr-10.7.1.41 to API group",
         "review_notes": "Approved - same NH08/CCS, intra-zone permitted",
         "rule_summary": {"application": "CBK", "source": "grp-CBK-NH08-CCS-API",
                          "destination": "grp-CBK-NH08-CCS-APP", "ports": "TCP 8443",
                          "environment": "Production"},
         "delta": {"added": {"rule_source": ["svr-10.7.1.41"]},
                   "removed": {}, "changed": {}}},
        # 7. Pending - cross-NH CDE exception request (R-3043)
        {"id": "REV-seed-007", "rule_id": "R-3043",
         "rule_name": "CRM to WLT Cross-NH CDE", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Eta", "reviewer": None, "status": "Pending",
         "submitted_at": (now + timedelta(hours=-3)).isoformat(),
         "reviewed_at": None,
         "comments": "CRM (NH02/CDE) needs to reach WLT (NH10/CDE) for portfolio data - LDF-004.",
         "review_notes": None,
         "rule_summary": {"application": "CRM", "source": "grp-CRM-NH02-CDE-APP",
                          "destination": "grp-WLT-NH10-CDE-API", "ports": "TCP 8443",
                          "environment": "Production"},
         "delta": None},
        # 8. Rejected - EPT PAA to CRM CDE blocked
        {"id": "REV-seed-008", "rule_id": "R-3050",
         "rule_name": "EPT PAA to CRM CDE", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Platform", "reviewer": "Security Team", "status": "Rejected",
         "submitted_at": (now + timedelta(days=-5)).isoformat(),
         "reviewed_at": (now + timedelta(days=-4)).isoformat(),
         "comments": "Enterprise Portal needs direct CRM database access",
         "review_notes": "REJECTED: PAA to CDE direct DB access blocked per policy. Use API tier instead.",
         "rule_summary": {"application": "EPT", "source": "grp-EPT-NH01-PAA-APP",
                          "destination": "grp-CRM-NH02-CDE-DB", "ports": "TCP 1521",
                          "environment": "Production"},
         "delta": None},
        # 9. Pending modification - LND service port change (R-3021)
        {"id": "REV-seed-009", "rule_id": "R-3021",
         "rule_name": "LND Batch to DB", "request_type": "modification",
         "module": "firewall-management",
         "requestor": "Team Iota", "reviewer": None, "status": "Pending",
         "submitted_at": (now + timedelta(hours=-1)).isoformat(),
         "reviewed_at": None,
         "comments": "Changing from Oracle to PostgreSQL - updating port from 1521 to 5432",
         "review_notes": None,
         "rule_summary": {"application": "LND", "source": "grp-LND-NH09-CCS-BAT",
                          "destination": "grp-LND-NH09-CCS-DB", "ports": "TCP 5432",
                          "environment": "Production"},
         "delta": {"added": {}, "removed": {},
                   "changed": {"rule_service": {"from": "TCP 1521", "to": "TCP 5432"}}}},
        # 10. Approved - INS to KYC GEN-to-GEN cross-NH (R-3031)
        {"id": "REV-seed-010", "rule_id": "R-3031",
         "rule_name": "INS to KYC GEN-to-GEN", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Kappa", "reviewer": "Network Team", "status": "Approved",
         "submitted_at": (now + timedelta(days=-12)).isoformat(),
         "reviewed_at": (now + timedelta(days=-11)).isoformat(),
         "comments": "Insurance needs KYC validation - both in GEN zone, LDF-001",
         "review_notes": "Approved - GEN to GEN cross-NH permitted per policy matrix (0 FW boundaries)",
         "rule_summary": {"application": "INS", "source": "grp-INS-NH04-GEN-APP",
                          "destination": "grp-KYC-NH05-GEN-API", "ports": "TCP 8443",
                          "environment": "Production"},
         "delta": None},
        # 11. Approved - CBK to PAY cross-zone (R-3039, LDF-003)
        {"id": "REV-seed-011", "rule_id": "R-3039",
         "rule_name": "CBK to PAY Payment Gateway", "request_type": "new_rule",
         "module": "design-studio",
         "requestor": "Team Theta", "reviewer": "Security Team", "status": "Approved",
         "submitted_at": (now + timedelta(days=-8)).isoformat(),
         "reviewed_at": (now + timedelta(days=-7)).isoformat(),
         "comments": "Core Banking needs Payment API for settlement - CCS to CPA cross-zone",
         "review_notes": "Approved - LDF-003 compliant, 1 FW boundary (egress NH08-CCS)",
         "rule_summary": {"application": "CBK", "source": "grp-CBK-NH08-CCS-APP",
                          "destination": "grp-PAY-NH07-CPA-API", "ports": "TCP 8443",
                          "environment": "Production"},
         "delta": None},
        # 12. Pending migration - HRM legacy
        {"id": "REV-seed-012", "rule_id": "LR-1013",
         "rule_name": "HRM Legacy Migration", "request_type": "migration",
         "module": "migration-studio",
         "requestor": "Migration Tool", "reviewer": None, "status": "Pending",
         "submitted_at": (now + timedelta(hours=-4)).isoformat(),
         "reviewed_at": None,
         "comments": "Auto-generated migration from DC_LEGACY_B to ALPHA_NGDC",
         "review_notes": None,
         "rule_summary": {"application": "HRM", "source": "grp-HRM-NH01-GEN-APP",
                          "destination": "grp-HRM-NH01-GEN-DB", "ports": "TCP 5432",
                          "environment": "Production"},
         "delta": {"added": {}, "removed": {},
                   "changed": {"rule_source": {"from": "10.26.2.10\n10.26.2.11", "to": "svr-10.0.2.140\nsvr-10.0.2.141"},
                               "rule_destination": {"from": "10.26.3.10\n10.26.3.11", "to": "svr-10.0.2.150\nsvr-10.0.2.151"},
                               "rule_source_zone": {"from": "Zone-B-App", "to": "GEN"},
                               "rule_destination_zone": {"from": "Zone-B-DB", "to": "GEN"}}}},
    ]
    return reviews


def build_seed_lifecycle_events() -> list[dict[str, Any]]:
    """Build seed lifecycle events matching the seed rules and reviews.

    Provides a realistic timeline so the Lifecycle Dashboard isn't empty on first load.
    Covers events from all modules: design-studio, firewall-management, migration-studio.
    """
    from datetime import datetime, timedelta
    import uuid
    now = datetime.utcnow()

    def _evt(rule_id: str, event_type: str, from_status: str | None,
             to_status: str | None, actor: str, module: str,
             details: str, days_ago: int, hours_ago: int = 0) -> dict[str, Any]:
        ts = (now + timedelta(days=-days_ago, hours=-hours_ago)).isoformat()
        return {
            "id": f"evt-seed-{uuid.uuid4().hex[:8]}",
            "rule_id": rule_id,
            "event_type": event_type,
            "from_status": from_status,
            "to_status": to_status,
            "actor": actor,
            "module": module,
            "details": details,
            "metadata": {},
            "timestamp": ts,
        }

    events = [
        # === Design Studio: CRM Web to App (R-3001) — Created → Submitted → Approved → Deployed ===
        _evt("R-3001", "created", None, "Draft", "Team Eta", "design-studio",
             "Rule created: CRM Web to App HTTPS", 36),
        _evt("R-3001", "submitted", "Draft", "Pending Review", "Team Eta", "design-studio",
             "Rule submitted for review", 35),
        _evt("R-3001", "approved", "Pending Review", "Approved", "Security Team", "design-studio",
             "Approved - intra-NH/SZ traffic, LDF-002 compliant", 34),
        _evt("R-3001", "deployed", "Approved", "Deployed", "system", "design-studio",
             "Rule deployed to firewall", 30),

        # === Design Studio: PAY App to MQ (R-3010) — Created → Submitted → Approved → Deployed → Certified ===
        _evt("R-3010", "created", None, "Draft", "Team Epsilon", "design-studio",
             "Rule created: PAY App to MQ AMQP", 110),
        _evt("R-3010", "submitted", "Draft", "Pending Review", "Team Epsilon", "design-studio",
             "Rule submitted for review", 105),
        _evt("R-3010", "approved", "Pending Review", "Approved", "Security Team", "design-studio",
             "Approved - PCI controls verified", 103),
        _evt("R-3010", "deployed", "Approved", "Deployed", "system", "design-studio",
             "Rule deployed to firewall", 101),
        _evt("R-3010", "certified", "Deployed", "Certified", "system", "design-studio",
             "Rule certified after testing", 100),

        # === Design Studio: HRM cross-zone rejected (R-3030) — Created → Submitted → Rejected ===
        _evt("R-3030", "created", None, "Draft", "Team Platform", "design-studio",
             "Rule created: HRM App to CRM DB Cross-Zone", 8),
        _evt("R-3030", "submitted", "Draft", "Pending Review", "Team Platform", "design-studio",
             "Rule submitted for review", 7),
        _evt("R-3030", "rejected", "Pending Review", "Rejected", "Security Team", "design-studio",
             "REJECTED: GEN to CDE cross-zone traffic blocked per policy", 6),

        # === Firewall Management: CBK API modification (R-3017) — Modified → Submitted → Approved ===
        _evt("R-3017", "submitted", "Deployed", "Pending Review", "Team Theta", "firewall-management",
             "Rule modification submitted: Adding new CBK API endpoint", 15),
        _evt("R-3017", "approved", "Pending Review", "Approved", "Network Team", "firewall-management",
             "Approved - same NH08/CCS, intra-zone permitted", 14),
        _evt("R-3017", "modified", None, None, "Network Team", "firewall-management",
             "Rule modification applied: CBK API server added", 14),

        # === Firewall Management: TRD modification pending (R-3006) ===
        _evt("R-3006", "submitted", "Deployed", "Pending Review", "Team Xi", "firewall-management",
             "Rule modification submitted: Adding new app server to TRD", 1),

        # === Firewall Management: LND port change pending (R-3021) ===
        _evt("R-3021", "submitted", "Certified", "Pending Review", "Team Iota", "firewall-management",
             "Rule modification submitted: Changing from Oracle to PostgreSQL", 0, 1),

        # === Migration Studio: FRD legacy migration pending (R-3012) ===
        _evt("R-3012", "submitted", "Deployed", "Pending Review", "Migration Tool", "migration-studio",
             "Migration review submitted for FRD legacy rule", 0, 6),

        # === Migration Studio: HRM legacy migration pending (LR-1013) ===
        _evt("LR-1013", "submitted", None, "Pending Review", "Migration Tool", "migration-studio",
             "Migration review submitted for HRM legacy rule", 0, 4),

        # === Design Studio: INS to KYC approved (R-3031) ===
        _evt("R-3031", "created", None, "Draft", "Team Kappa", "design-studio",
             "Rule created: INS to KYC GEN-to-GEN cross-NH", 14),
        _evt("R-3031", "submitted", "Draft", "Pending Review", "Team Kappa", "design-studio",
             "Rule submitted for review", 12),
        _evt("R-3031", "approved", "Pending Review", "Approved", "Network Team", "design-studio",
             "Approved - GEN to GEN cross-NH permitted per policy", 11),

        # === Design Studio: CBK to PAY approved (R-3039) ===
        _evt("R-3039", "submitted", "Draft", "Pending Review", "Team Theta", "design-studio",
             "Rule submitted for review: CBK to PAY Payment Gateway", 8),
        _evt("R-3039", "approved", "Pending Review", "Approved", "Security Team", "design-studio",
             "Approved - LDF-003 compliant, 1 FW boundary", 7),

        # === Design Studio: EPT PAA rejected (R-3050) ===
        _evt("R-3050", "submitted", "Draft", "Pending Review", "Team Platform", "design-studio",
             "Rule submitted for review: EPT PAA to CRM CDE", 5),
        _evt("R-3050", "rejected", "Pending Review", "Rejected", "Security Team", "design-studio",
             "REJECTED: PAA to CDE direct DB access blocked per policy", 4),

        # === Design Studio: CRM to WLT pending (R-3043) ===
        _evt("R-3043", "submitted", "Draft", "Pending Review", "Team Eta", "design-studio",
             "Rule submitted for review: CRM to WLT Cross-NH CDE", 0, 3),

        # === Additional deployed/certified rules with full lifecycle events ===
        # TRD Web to App (R-3005) — full lifecycle
        _evt("R-3005", "created", None, "Draft", "system", "design-studio",
             "Rule created: TRD Web to App", 125),
        _evt("R-3005", "deployed", "Approved", "Deployed", "system", "design-studio",
             "Rule deployed to firewall", 120),

        # PAY App to DB (R-3009) — full lifecycle
        _evt("R-3009", "created", None, "Draft", "system", "design-studio",
             "Rule created: PAY App to DB", 155),
        _evt("R-3009", "deployed", "Approved", "Deployed", "system", "design-studio",
             "Rule deployed to firewall", 150),

        # CBK App to DB (R-3015) — full lifecycle
        _evt("R-3015", "created", None, "Draft", "system", "design-studio",
             "Rule created: CBK App to DB", 205),
        _evt("R-3015", "deployed", "Approved", "Deployed", "system", "design-studio",
             "Rule deployed to firewall", 200),
    ]
    return events


# Build the data at module load time
SEED_LEGACY_RULES = _build_legacy_rules()
SEED_IP_MAPPINGS = _build_ip_mappings()
SEED_REVIEWS = build_seed_reviews()
SEED_LIFECYCLE_EVENTS = build_seed_lifecycle_events()
