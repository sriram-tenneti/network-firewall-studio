"""Seed data definitions for the Network Firewall Studio.

All reference data constants are defined here and imported by database.py.
Comprehensive test data for multiple apps, environments, firewall devices.
IP naming: svr-xx.xx.xx.xx for IPs, rng-xx.xx.xx.xx-xy for ranges.
Each app has multiple components (WEB, APP, DB, MQ, BAT, API) across zones within its NH.
"""

from datetime import datetime, timedelta
from typing import Any


# ============================================================
# Neighbourhoods (with CIDR ranges per NH)
# ============================================================

SEED_NEIGHBOURHOODS = [
    {"nh_id": "NH01", "name": "Platform Services", "environment": "Production",
     "cidr": "10.0.0.0/16",
     "description": "Platform and infrastructure services", "ip_ranges": [
        {"cidr": "10.0.1.0/24", "description": "NH01 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "10.0.2.0/24", "description": "NH01 East Secondary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.50.0/24", "description": "NH01 West Primary", "dc": "BETA_NGDC"},
        {"cidr": "10.50.50.0/24", "description": "NH01 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH01-sz04", "cidr": "10.0.1.0/25", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH01-sz05", "cidr": "10.0.1.128/25", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH01-sz06", "cidr": "10.0.2.0/25", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH01-gen", "cidr": "10.0.2.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH02", "name": "Team Eta", "environment": "Production",
     "cidr": "10.1.0.0/16",
     "description": "Data processing and analytics platforms", "ip_ranges": [
        {"cidr": "10.1.1.0/24", "description": "NH02 East App Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "10.1.2.0/24", "description": "NH02 East DB Tier", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.1.0/24", "description": "NH02 West App", "dc": "BETA_NGDC"},
        {"cidr": "10.50.1.0/24", "description": "NH02 Central App", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH02-sz04", "cidr": "10.1.1.0/25", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH02-sz05", "cidr": "10.1.1.128/25", "transit_vni": 8051, "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH02-sz06", "cidr": "10.1.2.0/25", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH02-gen", "cidr": "10.1.2.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH03", "name": "Team Delta", "environment": "Production",
     "cidr": "10.2.0.0/16",
     "description": "Web application and API hosting", "ip_ranges": [
        {"cidr": "10.2.1.0/24", "description": "NH03 East Web Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "10.2.2.0/24", "description": "NH03 East App Servers", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.3.0/24", "description": "NH03 West Web", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH03-sz04", "cidr": "10.2.1.0/25", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH03-sz05", "cidr": "10.2.1.128/25", "description": "Card Holder Data"},
        {"zone": "GEN", "vrf_id": "NH03-gen", "cidr": "10.2.2.0/24", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH04", "name": "Team Kappa", "environment": "Production",
     "cidr": "10.3.0.0/16",
     "description": "Insurance and risk management", "ip_ranges": [
        {"cidr": "10.3.1.0/24", "description": "NH04 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.4.0/24", "description": "NH04 West Primary", "dc": "BETA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH04-sz04", "cidr": "10.3.1.0/25", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH04-gen", "cidr": "10.3.1.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH05", "name": "Team Lambda", "environment": "Production",
     "cidr": "10.4.0.0/16",
     "description": "Enterprise compliance and KYC", "ip_ranges": [
        {"cidr": "10.4.1.0/24", "description": "NH05 East App", "dc": "ALPHA_NGDC"},
        {"cidr": "10.4.2.0/24", "description": "NH05 East DB", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH05-sz04", "cidr": "10.4.1.0/25", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH05-gen", "cidr": "10.4.1.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH06", "name": "Team Xi", "environment": "Production",
     "cidr": "10.5.0.0/16",
     "description": "Trading platforms", "ip_ranges": [
        {"cidr": "10.5.1.0/24", "description": "NH06 East Primary", "dc": "ALPHA_NGDC"},
        {"cidr": "172.16.6.0/24", "description": "NH06 West Primary", "dc": "BETA_NGDC"},
        {"cidr": "172.16.20.0/24", "description": "NH06 Central Primary", "dc": "GAMMA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH06-sz04", "cidr": "10.5.1.0/26", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH06-sz05", "cidr": "10.5.1.64/26", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH06-sz06", "cidr": "10.5.1.128/26", "description": "Critical Payment Applications"},
        {"zone": "GEN", "vrf_id": "NH06-gen", "cidr": "10.5.1.192/26", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH07", "name": "Team Epsilon", "environment": "Production",
     "cidr": "10.6.0.0/16",
     "description": "Payment processing", "ip_ranges": [
        {"cidr": "10.6.1.0/24", "description": "NH07 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CDE", "vrf_id": "NH07-sz05", "cidr": "10.6.1.0/25", "description": "Card Holder Data"},
        {"zone": "CPA", "vrf_id": "NH07-sz06", "cidr": "10.6.1.128/25", "description": "Critical Payment Applications"},
     ]},
    {"nh_id": "NH08", "name": "Team Theta", "environment": "Production",
     "cidr": "10.7.0.0/16",
     "description": "Core banking services", "ip_ranges": [
        {"cidr": "10.7.1.0/24", "description": "NH08 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH08-sz04", "cidr": "10.7.1.0/25", "description": "Critical Core Services"},
        {"zone": "CDE", "vrf_id": "NH08-sz05", "cidr": "10.7.1.128/25", "description": "Card Holder Data"},
     ]},
    {"nh_id": "NH09", "name": "Team Iota", "environment": "Production",
     "cidr": "10.8.0.0/16",
     "description": "Digital lending", "ip_ranges": [
        {"cidr": "10.8.1.0/24", "description": "NH09 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CCS", "vrf_id": "NH09-sz04", "cidr": "10.8.1.0/25", "description": "Critical Core Services"},
        {"zone": "GEN", "vrf_id": "NH09-gen", "cidr": "10.8.1.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH10", "name": "Team Mu", "environment": "Production",
     "cidr": "10.9.0.0/16",
     "description": "Wealth management", "ip_ranges": [
        {"cidr": "10.9.1.0/24", "description": "NH10 East Primary", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "CDE", "vrf_id": "NH10-sz05", "cidr": "10.9.1.0/25", "description": "Card Holder Data"},
        {"zone": "GEN", "vrf_id": "NH10-gen", "cidr": "10.9.1.128/25", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH14", "name": "DMZ Services", "environment": "Production",
     "cidr": "10.70.0.0/16",
     "description": "External-facing DMZ", "ip_ranges": [
        {"cidr": "10.70.1.0/24", "description": "NH14 East DMZ", "dc": "ALPHA_NGDC"},
        {"cidr": "10.70.2.0/24", "description": "NH14 East External", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "DMZ", "vrf_id": "NH14-sz01", "cidr": "10.70.1.0/24", "description": "Demilitarized Zone"},
        {"zone": "GEN", "vrf_id": "NH14-gen", "cidr": "10.70.2.0/24", "transit_vni": 4000, "description": "Standard/General"},
     ]},
    {"nh_id": "NH15", "name": "Management Zone", "environment": "Production",
     "cidr": "10.80.0.0/16",
     "description": "Network management and monitoring", "ip_ranges": [
        {"cidr": "10.80.1.0/24", "description": "NH15 East Mgmt", "dc": "ALPHA_NGDC"},
     ],
     "security_zones": [
        {"zone": "MGT", "vrf_id": "NH15-sz02", "cidr": "10.80.1.0/24", "description": "Management Zone"},
     ]},
]


# ============================================================
# Security Zones (with CIDR ranges)
# ============================================================

SEED_SECURITY_ZONES = [
    {"code": "CCS", "name": "Critical Core Services", "risk_level": "Critical", "pci_scope": True,
     "cidr": "varies per NH", "description": "Houses critical core banking and financial services"},
    {"code": "CDE", "name": "Card Holder Data Environment", "risk_level": "Critical", "pci_scope": True,
     "cidr": "varies per NH", "description": "PCI DSS scope - cardholder data processing and storage"},
    {"code": "CPA", "name": "Critical Payment Applications", "risk_level": "Critical", "pci_scope": True,
     "cidr": "varies per NH", "description": "Payment processing applications and APIs"},
    {"code": "GEN", "name": "General Zone", "risk_level": "Low", "pci_scope": False,
     "cidr": "varies per NH", "description": "General-purpose compute, non-sensitive workloads"},
    {"code": "DMZ", "name": "Demilitarized Zone", "risk_level": "High", "pci_scope": False,
     "cidr": "10.70.0.0/16", "description": "External-facing services, API gateways, WAFs"},
    {"code": "MGT", "name": "Management Zone", "risk_level": "High", "pci_scope": False,
     "cidr": "10.80.0.0/16", "description": "Network management, monitoring, jump boxes"},
    {"code": "DEV", "name": "Development Zone", "risk_level": "Low", "pci_scope": False,
     "cidr": "10.200.0.0/16", "description": "Development and sandbox environments"},
    {"code": "UAT", "name": "User Acceptance Testing", "risk_level": "Low", "pci_scope": False,
     "cidr": "10.201.0.0/16", "description": "UAT environments for integration testing"},
    {"code": "SIT", "name": "System Integration Testing", "risk_level": "Low", "pci_scope": False,
     "cidr": "10.202.0.0/16", "description": "SIT environments for system testing"},
    {"code": "STG", "name": "Staging Zone", "risk_level": "Medium", "pci_scope": False,
     "cidr": "10.203.0.0/16", "description": "Pre-production staging with sanitized data"},
    {"code": "DR", "name": "Disaster Recovery", "risk_level": "High", "pci_scope": True,
     "cidr": "10.90.0.0/16", "description": "DR site with replicated critical systems"},
    {"code": "EXT", "name": "External Zone", "risk_level": "Critical", "pci_scope": False,
     "cidr": "0.0.0.0/0", "description": "External/internet-facing endpoints"},
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
     "owner": "Team Eta", "nh": "NH02", "sz": "CDE", "criticality": "High", "pci_scope": True,
     "components": ["WEB", "APP", "DB", "BAT", "API"],
     "description": "CRM platform for customer data management"},
    {"app_id": "HRM", "name": "Human Resource Manager", "app_distributed_id": "AD-1002",
     "owner": "Team Platform", "nh": "NH01", "sz": "GEN", "criticality": "Medium", "pci_scope": False,
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "HR management and employee portal"},
    {"app_id": "TRD", "name": "Trading Platform", "app_distributed_id": "AD-1003",
     "owner": "Team Xi", "nh": "NH06", "sz": "CDE", "criticality": "Critical", "pci_scope": True,
     "components": ["WEB", "APP", "DB", "MQ", "API", "BAT"],
     "description": "Real-time trading and market data"},
    {"app_id": "PAY", "name": "Payment Gateway", "app_distributed_id": "AD-1004",
     "owner": "Team Epsilon", "nh": "NH07", "sz": "CPA", "criticality": "Critical", "pci_scope": True,
     "components": ["APP", "DB", "MQ", "API"],
     "description": "Payment processing and settlement"},
    {"app_id": "INS", "name": "Insurance Portal", "app_distributed_id": "AD-1005",
     "owner": "Team Kappa", "nh": "NH04", "sz": "GEN", "criticality": "High", "pci_scope": False,
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "Insurance policy management"},
    {"app_id": "KYC", "name": "KYC Compliance", "app_distributed_id": "AD-1006",
     "owner": "Team Lambda", "nh": "NH05", "sz": "GEN", "criticality": "High", "pci_scope": False,
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Know Your Customer compliance platform"},
    {"app_id": "FRD", "name": "Fraud Detection", "app_distributed_id": "AD-1007",
     "owner": "Team Eta", "nh": "NH02", "sz": "CDE", "criticality": "Critical", "pci_scope": True,
     "components": ["APP", "DB", "MQ", "API"],
     "description": "Real-time fraud detection engine"},
    {"app_id": "LND", "name": "Lending Platform", "app_distributed_id": "AD-1008",
     "owner": "Team Iota", "nh": "NH09", "sz": "CCS", "criticality": "High", "pci_scope": False,
     "components": ["WEB", "APP", "DB", "BAT"],
     "description": "Digital lending and loan origination"},
    {"app_id": "WLT", "name": "Wealth Management", "app_distributed_id": "AD-1009",
     "owner": "Team Mu", "nh": "NH10", "sz": "CDE", "criticality": "High", "pci_scope": True,
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Portfolio and wealth management"},
    {"app_id": "CBK", "name": "Core Banking", "app_distributed_id": "AD-1010",
     "owner": "Team Theta", "nh": "NH08", "sz": "CCS", "criticality": "Critical", "pci_scope": True,
     "components": ["APP", "DB", "MQ", "API", "BAT"],
     "description": "Core banking transaction engine"},
    {"app_id": "EPT", "name": "Enterprise Portal", "app_distributed_id": "AD-1011",
     "owner": "Team Platform", "nh": "NH01", "sz": "PAA", "criticality": "High", "pci_scope": False,
     "components": ["WEB", "APP", "API"],
     "description": "Internet-facing enterprise portal (PAA zone)"},
    {"app_id": "MBK", "name": "Mobile Banking", "app_distributed_id": "AD-1012",
     "owner": "Team Epsilon", "nh": "NH07", "sz": "CPA", "criticality": "Critical", "pci_scope": True,
     "components": ["WEB", "APP", "DB", "API"],
     "description": "Mobile banking application"},
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
# Firewall Devices
# ============================================================

SEED_FIREWALL_DEVICES = [
    # ================================================================
    # ALPHA_NGDC (US-East) — Primary DC
    # Vendor: Palo Alto (perimeter, segmentation, PAA, DMZ)
    # ================================================================

    # --- Perimeter / DC-level devices ---
    {"device_id": "fw-PA-ALPHA-001", "name": "Palo Alto Alpha Primary", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.0.254.1", "ha_pair": "fw-PA-ALPHA-002",
     "capabilities": ["L7 inspection", "URL filtering", "Threat prevention"]},
    {"device_id": "fw-PA-ALPHA-002", "name": "Palo Alto Alpha Secondary", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.0.254.2", "ha_pair": "fw-PA-ALPHA-001",
     "capabilities": ["L7 inspection", "URL filtering", "Threat prevention"]},
    {"device_id": "fw-PA-ALPHA-DMZ", "name": "Palo Alto Alpha DMZ", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "dmz", "status": "Active",
     "mgmt_ip": "10.70.254.1",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF integration"]},

    # --- ALPHA NH-specific segmentation firewalls ---
    # Each NH that hosts a segmented zone (CPA, CDE, CCS) gets its own firewall.
    # GEN/STD zones do NOT have per-NH firewalls.

    # NH01 — CPA, CDE, CCS (Platform Services)
    {"device_id": "fw-PA-NH01-CPA", "name": "NH01 CPA Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.0.253.11",
     "capabilities": ["Micro-segmentation", "East-West", "CPA enforcement"]},
    {"device_id": "fw-PA-NH01-CDE", "name": "NH01 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.0.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-PA-NH01-CCS", "name": "NH01 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH01", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.0.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH02 — CPA, CDE, CCS (Team Eta / Data Processing)
    {"device_id": "fw-PA-NH02-CPA", "name": "NH02 CPA Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.1.253.11",
     "capabilities": ["Micro-segmentation", "East-West", "CPA enforcement"]},
    {"device_id": "fw-PA-NH02-CDE", "name": "NH02 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.1.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-PA-NH02-CCS", "name": "NH02 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH02", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.1.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH03 — CDE, CCS (Team Delta / Web & API)
    {"device_id": "fw-PA-NH03-CDE", "name": "NH03 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH03", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.2.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-PA-NH03-CCS", "name": "NH03 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH03", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.2.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH04 — CCS (Team Kappa / Insurance)
    {"device_id": "fw-CP-NH04-CCS", "name": "NH04 CCS Segmentation FW", "vendor": "checkpoint",
     "dc": "ALPHA_NGDC", "nh": "NH04", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.3.253.13",
     "capabilities": ["Micro-segmentation", "CCS enforcement"]},

    # NH05 — CCS (Team Lambda / Compliance)
    {"device_id": "fw-CP-NH05-CCS", "name": "NH05 CCS Segmentation FW", "vendor": "checkpoint",
     "dc": "ALPHA_NGDC", "nh": "NH05", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.4.253.13",
     "capabilities": ["Micro-segmentation", "CCS enforcement"]},

    # NH06 — CPA, CDE, CCS (Team Xi / Trading)
    {"device_id": "fw-PA-NH06-CPA", "name": "NH06 CPA Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.5.253.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-PA-NH06-CDE", "name": "NH06 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.5.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-PA-NH06-CCS", "name": "NH06 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH06", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.5.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH07 — CPA, CDE (Team Epsilon / Payments)
    {"device_id": "fw-PA-NH07-CPA", "name": "NH07 CPA Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.6.253.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-PA-NH07-CDE", "name": "NH07 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH07", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.6.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},

    # NH08 — CCS, CDE (Team Theta / Core Banking)
    {"device_id": "fw-PA-NH08-CCS", "name": "NH08 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.7.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},
    {"device_id": "fw-PA-NH08-CDE", "name": "NH08 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH08", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.7.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},

    # NH09 — CCS (Team Iota / Lending)
    {"device_id": "fw-PA-NH09-CCS", "name": "NH09 CCS Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH09", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.8.253.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH10 — CDE (Team Mu / Wealth)
    {"device_id": "fw-PA-NH10-CDE", "name": "NH10 CDE Segmentation FW", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "nh": "NH10", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.9.253.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},

    # --- ALPHA PAA devices ---
    {"device_id": "fw-PA-PAA-001", "name": "PAA Perimeter FW (Alpha)", "vendor": "palo_alto",
     "dc": "ALPHA_NGDC", "type": "paa", "status": "Active",
     "mgmt_ip": "10.0.252.1",
     "capabilities": ["L7 inspection", "SSL decryption", "WAF", "PAA enforcement"]},

    # ================================================================
    # BETA_NGDC (US-West) — Secondary DC
    # Vendor: Check Point (perimeter), Palo Alto (segmentation)
    # NHs present in BETA: NH01, NH02, NH03, NH04, NH06
    # ================================================================

    # --- Perimeter ---
    {"device_id": "fw-CP-BETA-001", "name": "Check Point Beta Primary", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "172.16.254.1", "ha_pair": "fw-CP-BETA-002",
     "capabilities": ["Stateful inspection", "IPS", "VPN"]},
    {"device_id": "fw-CP-BETA-002", "name": "Check Point Beta Secondary", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "172.16.254.2", "ha_pair": "fw-CP-BETA-001",
     "capabilities": ["Stateful inspection", "IPS", "VPN"]},
    {"device_id": "fw-CP-BETA-DMZ", "name": "Check Point Beta DMZ", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "type": "dmz", "status": "Active",
     "mgmt_ip": "172.16.70.1",
     "capabilities": ["Stateful inspection", "SSL inspection", "IPS"]},

    # --- BETA NH segmentation firewalls ---
    # NH01 in BETA
    {"device_id": "fw-CP-BETA-NH01-CPA", "name": "Beta NH01 CPA Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH01", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.50.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-CP-BETA-NH01-CDE", "name": "Beta NH01 CDE Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH01", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.50.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-CP-BETA-NH01-CCS", "name": "Beta NH01 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH01", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.50.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH02 in BETA
    {"device_id": "fw-CP-BETA-NH02-CDE", "name": "Beta NH02 CDE Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH02", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.1.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-CP-BETA-NH02-CCS", "name": "Beta NH02 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH02", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.1.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH03 in BETA
    {"device_id": "fw-CP-BETA-NH03-CCS", "name": "Beta NH03 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH03", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.3.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH04 in BETA
    {"device_id": "fw-CP-BETA-NH04-CCS", "name": "Beta NH04 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH04", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.4.13",
     "capabilities": ["Micro-segmentation", "CCS enforcement"]},

    # NH06 in BETA
    {"device_id": "fw-CP-BETA-NH06-CPA", "name": "Beta NH06 CPA Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH06", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.6.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-CP-BETA-NH06-CDE", "name": "Beta NH06 CDE Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH06", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.6.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},
    {"device_id": "fw-CP-BETA-NH06-CCS", "name": "Beta NH06 CCS Seg FW", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "nh": "NH06", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.6.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # --- BETA PAA ---
    {"device_id": "fw-CP-BETA-PAA-001", "name": "PAA Perimeter FW (Beta)", "vendor": "checkpoint",
     "dc": "BETA_NGDC", "type": "paa", "status": "Active",
     "mgmt_ip": "172.16.252.1",
     "capabilities": ["Stateful inspection", "SSL inspection", "PAA enforcement"]},

    # ================================================================
    # GAMMA_NGDC (US-Central) — Tertiary DC
    # Vendor: Cisco ASA (perimeter), Palo Alto (segmentation)
    # NHs present in GAMMA: NH01, NH02, NH06
    # ================================================================

    # --- Perimeter ---
    {"device_id": "fw-ASA-GAMMA-001", "name": "Cisco ASA Gamma Primary", "vendor": "cisco_asa",
     "dc": "GAMMA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.50.254.1", "ha_pair": "fw-ASA-GAMMA-002",
     "capabilities": ["Stateful inspection", "VPN", "NAT"]},
    {"device_id": "fw-ASA-GAMMA-002", "name": "Cisco ASA Gamma Secondary", "vendor": "cisco_asa",
     "dc": "GAMMA_NGDC", "type": "perimeter", "status": "Active",
     "mgmt_ip": "10.50.254.2", "ha_pair": "fw-ASA-GAMMA-001",
     "capabilities": ["Stateful inspection", "VPN", "NAT"]},
    {"device_id": "fw-ASA-GAMMA-DMZ", "name": "Cisco ASA Gamma DMZ", "vendor": "cisco_asa",
     "dc": "GAMMA_NGDC", "type": "dmz", "status": "Active",
     "mgmt_ip": "10.50.70.1",
     "capabilities": ["Stateful inspection", "NAT", "ACL filtering"]},

    # --- GAMMA NH segmentation firewalls ---
    # NH01 in GAMMA
    {"device_id": "fw-PA-GAMMA-NH01-CPA", "name": "Gamma NH01 CPA Seg FW", "vendor": "palo_alto",
     "dc": "GAMMA_NGDC", "nh": "NH01", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.50.50.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-PA-GAMMA-NH01-CCS", "name": "Gamma NH01 CCS Seg FW", "vendor": "palo_alto",
     "dc": "GAMMA_NGDC", "nh": "NH01", "sz": "CCS", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.50.50.13",
     "capabilities": ["Micro-segmentation", "Core Services enforcement"]},

    # NH02 in GAMMA
    {"device_id": "fw-PA-GAMMA-NH02-CDE", "name": "Gamma NH02 CDE Seg FW", "vendor": "palo_alto",
     "dc": "GAMMA_NGDC", "nh": "NH02", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "10.50.1.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},

    # NH06 in GAMMA
    {"device_id": "fw-PA-GAMMA-NH06-CPA", "name": "Gamma NH06 CPA Seg FW", "vendor": "palo_alto",
     "dc": "GAMMA_NGDC", "nh": "NH06", "sz": "CPA", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.20.11",
     "capabilities": ["Micro-segmentation", "CPA enforcement"]},
    {"device_id": "fw-PA-GAMMA-NH06-CDE", "name": "Gamma NH06 CDE Seg FW", "vendor": "palo_alto",
     "dc": "GAMMA_NGDC", "nh": "NH06", "sz": "CDE", "type": "segmentation", "status": "Active",
     "mgmt_ip": "172.16.20.12",
     "capabilities": ["Micro-segmentation", "PCI CDE enforcement"]},

    # --- GAMMA PAA ---
    {"device_id": "fw-ASA-GAMMA-PAA-001", "name": "PAA Perimeter FW (Gamma)", "vendor": "cisco_asa",
     "dc": "GAMMA_NGDC", "type": "paa", "status": "Active",
     "mgmt_ip": "10.50.252.1",
     "capabilities": ["Stateful inspection", "NAT", "PAA enforcement"]},
]


# ============================================================
# Logical Data Flow Rules
# Determines how many firewall boundaries a rule must cross
# based on source/destination NH and SZ placement.
# ============================================================

SEGMENTED_ZONES = {"CPA", "CDE", "CCS", "PAA"}
# STD/GEN zones do NOT have per-NH firewalls

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
    {"heritage_zone": "Default", "new_dc_zone": "CCS",
     "action": "Blocked - Exception Required", "reason": "Heritage DC to CCS requires exception approval"},
    {"heritage_zone": "Default", "new_dc_zone": "CDE",
     "action": "Blocked - Exception Required", "reason": "Heritage DC to CDE requires PCI exception"},
    {"heritage_zone": "Default", "new_dc_zone": "CPA",
     "action": "Blocked", "reason": "Heritage DC to CPA not permitted"},
    {"heritage_zone": "Default", "new_dc_zone": "GEN",
     "action": "Permitted", "reason": "Heritage DC to General zone is allowed during migration"},
    {"heritage_zone": "Default", "new_dc_zone": "DMZ",
     "action": "Blocked", "reason": "Heritage DC to DMZ not permitted directly"},
]

SEED_NGDC_PROD_MATRIX = [
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "CCS", "dst_sz": "CCS",
     "action": "Permitted", "reason": "Same DC, same NH, CCS to CCS intra-zone traffic allowed"},
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "CDE", "dst_sz": "CDE",
     "action": "Permitted", "reason": "Same DC, same NH, CDE intra-zone traffic allowed"},
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Same", "dst_nh": "Same",
     "src_sz": "CCS", "dst_sz": "CDE",
     "action": "Permitted", "reason": "Same DC, same NH, CCS to CDE allowed with controls"},
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Different", "dst_nh": "Different",
     "src_sz": "CDE", "dst_sz": "CDE",
     "action": "Blocked - Exception Required", "reason": "Cross-NH CDE traffic requires exception"},
    {"src_dc": "Same", "dst_dc": "Same", "src_nh": "Different", "dst_nh": "Different",
     "src_sz": "CCS", "dst_sz": "CPA",
     "action": "Blocked", "reason": "Cross-NH CCS to CPA blocked"},
    {"src_dc": "Different", "dst_dc": "Different", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "CDE", "dst_sz": "CDE",
     "action": "Blocked - Exception Required", "reason": "Cross-DC CDE traffic requires exception and encryption"},
    {"src_dc": "Any", "dst_dc": "Any", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "GEN", "dst_sz": "GEN",
     "action": "Permitted", "reason": "General zone traffic permitted"},
    {"src_dc": "Any", "dst_dc": "Any", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "GEN", "dst_sz": "CDE",
     "action": "Blocked", "reason": "GEN to CDE not permitted"},
    {"src_dc": "Any", "dst_dc": "Any", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "DMZ", "dst_sz": "CDE",
     "action": "Blocked", "reason": "DMZ to CDE not permitted directly"},
    {"src_dc": "Any", "dst_dc": "Any", "src_nh": "Any", "dst_nh": "Any",
     "src_sz": "DMZ", "dst_sz": "GEN",
     "action": "Permitted", "reason": "DMZ to GEN allowed through proxy"},
]

SEED_NONPROD_MATRIX = [
    {"source_zone": "DEV", "dest_zone": "DEV", "action": "Permitted", "reason": "Dev to Dev allowed"},
    {"source_zone": "DEV", "dest_zone": "SIT", "action": "Permitted", "reason": "Dev to SIT allowed"},
    {"source_zone": "DEV", "dest_zone": "UAT", "action": "Blocked", "reason": "Dev to UAT not allowed"},
    {"source_zone": "SIT", "dest_zone": "SIT", "action": "Permitted", "reason": "SIT intra-zone allowed"},
    {"source_zone": "SIT", "dest_zone": "UAT", "action": "Permitted", "reason": "SIT to UAT allowed"},
    {"source_zone": "UAT", "dest_zone": "UAT", "action": "Permitted", "reason": "UAT intra-zone allowed"},
    {"source_zone": "Any", "dest_zone": "CDE", "action": "Blocked", "reason": "Non-prod to CDE blocked"},
    {"source_zone": "Any", "dest_zone": "CPA", "action": "Blocked", "reason": "Non-prod to CPA blocked"},
    {"source_zone": "GEN", "dest_zone": "GEN", "action": "Permitted", "reason": "GEN intra-zone allowed"},
]

SEED_PREPROD_MATRIX = [
    {"source_zone": "STG", "dest_zone": "STG", "action": "Permitted", "reason": "Staging intra-zone allowed"},
    {"source_zone": "STG", "dest_zone": "GEN", "action": "Permitted", "reason": "Staging to GEN allowed"},
    {"source_zone": "STG", "dest_zone": "CDE", "action": "Blocked - Exception Required",
     "reason": "Staging to CDE requires exception with data masking"},
    {"source_zone": "GEN", "dest_zone": "STG", "action": "Permitted", "reason": "GEN to staging allowed"},
    {"source_zone": "Any", "dest_zone": "CPA", "action": "Blocked", "reason": "Pre-prod to CPA blocked"},
]

SEED_POLICY_MATRIX = SEED_NGDC_PROD_MATRIX + [
    {"env": "Non-Production", "entries": SEED_NONPROD_MATRIX},
    {"env": "Pre-Production", "entries": SEED_PREPROD_MATRIX},
]


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
    # --- CRM (NH02, CDE) ---
    {"name": "grp-CRM-NH02-CDE-WEB", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "WEB",
     "description": "CRM Web Servers", "members": [
        {"type": "ip", "value": "svr-10.1.1.10", "description": "CRM Web 1"},
        {"type": "ip", "value": "svr-10.1.1.11", "description": "CRM Web 2"},
     ]},
    {"name": "grp-CRM-NH02-CDE-APP", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "CRM Application Servers", "members": [
        {"type": "ip", "value": "svr-10.1.1.20", "description": "CRM App 1"},
        {"type": "ip", "value": "svr-10.1.1.21", "description": "CRM App 2"},
        {"type": "ip", "value": "svr-10.1.1.22", "description": "CRM App 3"},
     ]},
    {"name": "grp-CRM-NH02-CDE-DB", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "CRM Database Servers", "members": [
        {"type": "ip", "value": "svr-10.1.2.10", "description": "CRM DB Primary"},
        {"type": "ip", "value": "svr-10.1.2.11", "description": "CRM DB Standby"},
     ]},
    {"name": "grp-CRM-NH02-CDE-BAT", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "BAT",
     "description": "CRM Batch Servers", "members": [
        {"type": "ip", "value": "svr-10.1.1.30", "description": "CRM Batch 1"},
     ]},
    {"name": "grp-CRM-NH02-CDE-API", "app_id": "CRM", "nh": "NH02", "sz": "CDE", "subtype": "API",
     "description": "CRM API Gateway", "members": [
        {"type": "ip", "value": "svr-10.1.1.40", "description": "CRM API 1"},
        {"type": "ip", "value": "svr-10.1.1.41", "description": "CRM API 2"},
     ]},

    # --- HRM (NH01, GEN) ---
    {"name": "grp-HRM-NH01-GEN-WEB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "WEB",
     "description": "HRM Web Servers", "members": [
        {"type": "ip", "value": "svr-10.0.2.130", "description": "HRM Web 1"},
        {"type": "ip", "value": "svr-10.0.2.131", "description": "HRM Web 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-APP", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "APP",
     "description": "HRM Application Servers", "members": [
        {"type": "ip", "value": "svr-10.0.2.140", "description": "HRM App 1"},
        {"type": "ip", "value": "svr-10.0.2.141", "description": "HRM App 2"},
     ]},
    {"name": "grp-HRM-NH01-GEN-DB", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "DB",
     "description": "HRM Database", "members": [
        {"type": "ip", "value": "svr-10.0.2.150", "description": "HRM DB Primary"},
        {"type": "ip", "value": "svr-10.0.2.151", "description": "HRM DB Replica"},
     ]},
    {"name": "grp-HRM-NH01-GEN-BAT", "app_id": "HRM", "nh": "NH01", "sz": "GEN", "subtype": "BAT",
     "description": "HRM Batch Servers", "members": [
        {"type": "ip", "value": "svr-10.0.2.160", "description": "HRM Batch 1"},
     ]},

    # --- TRD (NH06, CDE) ---
    {"name": "grp-TRD-NH06-CDE-WEB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "WEB",
     "description": "TRD Web Frontend", "members": [
        {"type": "ip", "value": "svr-10.5.1.65", "description": "TRD Web 1"},
        {"type": "ip", "value": "svr-10.5.1.66", "description": "TRD Web 2"},
     ]},
    {"name": "grp-TRD-NH06-CDE-APP", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "APP",
     "description": "TRD Application Servers", "members": [
        {"type": "ip", "value": "svr-10.5.1.70", "description": "TRD App 1"},
        {"type": "ip", "value": "svr-10.5.1.71", "description": "TRD App 2"},
        {"type": "ip", "value": "svr-10.5.1.72", "description": "TRD App 3"},
     ]},
    {"name": "grp-TRD-NH06-CDE-DB", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "DB",
     "description": "TRD Database Cluster", "members": [
        {"type": "ip", "value": "svr-10.5.1.80", "description": "TRD DB Primary"},
        {"type": "ip", "value": "svr-10.5.1.81", "description": "TRD DB Standby"},
     ]},
    {"name": "grp-TRD-NH06-CDE-MQ", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "MQ",
     "description": "TRD Message Queue", "members": [
        {"type": "ip", "value": "svr-10.5.1.85", "description": "TRD MQ Broker 1"},
        {"type": "ip", "value": "svr-10.5.1.86", "description": "TRD MQ Broker 2"},
     ]},
    {"name": "grp-TRD-NH06-CDE-API", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "API",
     "description": "TRD API Layer", "members": [
        {"type": "ip", "value": "svr-10.5.1.90", "description": "TRD API 1"},
     ]},
    {"name": "grp-TRD-NH06-CDE-BAT", "app_id": "TRD", "nh": "NH06", "sz": "CDE", "subtype": "BAT",
     "description": "TRD Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.5.1.95", "description": "TRD Batch 1"},
     ]},

    # --- PAY (NH07, CPA) ---
    {"name": "grp-PAY-NH07-CPA-APP", "app_id": "PAY", "nh": "NH07", "sz": "CPA", "subtype": "APP",
     "description": "PAY Transaction Processors", "members": [
        {"type": "ip", "value": "svr-10.6.1.130", "description": "PAY App 1"},
        {"type": "ip", "value": "svr-10.6.1.131", "description": "PAY App 2"},
        {"type": "range", "value": "rng-10.6.1.132-140", "description": "PAY App Pool"},
     ]},
    {"name": "grp-PAY-NH07-CPA-DB", "app_id": "PAY", "nh": "NH07", "sz": "CPA", "subtype": "DB",
     "description": "PAY Database", "members": [
        {"type": "ip", "value": "svr-10.6.1.150", "description": "PAY DB Primary"},
        {"type": "ip", "value": "svr-10.6.1.151", "description": "PAY DB Standby"},
     ]},
    {"name": "grp-PAY-NH07-CPA-MQ", "app_id": "PAY", "nh": "NH07", "sz": "CPA", "subtype": "MQ",
     "description": "PAY Message Queue", "members": [
        {"type": "ip", "value": "svr-10.6.1.160", "description": "PAY MQ 1"},
     ]},
    {"name": "grp-PAY-NH07-CPA-API", "app_id": "PAY", "nh": "NH07", "sz": "CPA", "subtype": "API",
     "description": "PAY API Endpoint", "members": [
        {"type": "ip", "value": "svr-10.6.1.170", "description": "PAY API 1"},
        {"type": "ip", "value": "svr-10.6.1.171", "description": "PAY API 2"},
     ]},

    # --- INS (NH04, GEN) ---
    {"name": "grp-INS-NH04-GEN-WEB", "app_id": "INS", "nh": "NH04", "sz": "GEN", "subtype": "WEB",
     "description": "INS Web Portal", "members": [
        {"type": "ip", "value": "svr-10.3.1.130", "description": "INS Web 1"},
        {"type": "ip", "value": "svr-10.3.1.131", "description": "INS Web 2"},
     ]},
    {"name": "grp-INS-NH04-GEN-APP", "app_id": "INS", "nh": "NH04", "sz": "GEN", "subtype": "APP",
     "description": "INS Application Servers", "members": [
        {"type": "ip", "value": "svr-10.3.1.140", "description": "INS App 1"},
        {"type": "ip", "value": "svr-10.3.1.141", "description": "INS App 2"},
     ]},
    {"name": "grp-INS-NH04-GEN-DB", "app_id": "INS", "nh": "NH04", "sz": "GEN", "subtype": "DB",
     "description": "INS Database", "members": [
        {"type": "ip", "value": "svr-10.3.1.150", "description": "INS DB Primary"},
     ]},
    {"name": "grp-INS-NH04-GEN-BAT", "app_id": "INS", "nh": "NH04", "sz": "GEN", "subtype": "BAT",
     "description": "INS Batch Jobs", "members": [
        {"type": "ip", "value": "svr-10.3.1.160", "description": "INS Batch 1"},
     ]},

    # --- KYC (NH05, GEN) ---
    {"name": "grp-KYC-NH05-GEN-WEB", "app_id": "KYC", "nh": "NH05", "sz": "GEN", "subtype": "WEB",
     "description": "KYC Web Interface", "members": [
        {"type": "ip", "value": "svr-10.4.1.130", "description": "KYC Web 1"},
     ]},
    {"name": "grp-KYC-NH05-GEN-APP", "app_id": "KYC", "nh": "NH05", "sz": "GEN", "subtype": "APP",
     "description": "KYC Application", "members": [
        {"type": "ip", "value": "svr-10.4.1.140", "description": "KYC App 1"},
        {"type": "ip", "value": "svr-10.4.1.141", "description": "KYC App 2"},
     ]},
    {"name": "grp-KYC-NH05-GEN-DB", "app_id": "KYC", "nh": "NH05", "sz": "GEN", "subtype": "DB",
     "description": "KYC Database", "members": [
        {"type": "ip", "value": "svr-10.4.2.10", "description": "KYC DB Primary"},
        {"type": "ip", "value": "svr-10.4.2.11", "description": "KYC DB Replica"},
     ]},
    {"name": "grp-KYC-NH05-GEN-API", "app_id": "KYC", "nh": "NH05", "sz": "GEN", "subtype": "API",
     "description": "KYC API", "members": [
        {"type": "ip", "value": "svr-10.4.1.150", "description": "KYC API 1"},
     ]},

    # --- FRD (NH02, CDE) ---
    {"name": "grp-FRD-NH02-CDE-APP", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "APP",
     "description": "FRD Detection Engine", "members": [
        {"type": "ip", "value": "svr-10.1.1.50", "description": "FRD Engine 1"},
        {"type": "ip", "value": "svr-10.1.1.51", "description": "FRD Engine 2"},
     ]},
    {"name": "grp-FRD-NH02-CDE-DB", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "DB",
     "description": "FRD Database", "members": [
        {"type": "ip", "value": "svr-10.1.2.20", "description": "FRD DB Primary"},
        {"type": "ip", "value": "svr-10.1.2.21", "description": "FRD DB Standby"},
     ]},
    {"name": "grp-FRD-NH02-CDE-MQ", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "MQ",
     "description": "FRD Event Stream", "members": [
        {"type": "ip", "value": "svr-10.1.1.55", "description": "FRD Kafka 1"},
        {"type": "ip", "value": "svr-10.1.1.56", "description": "FRD Kafka 2"},
     ]},
    {"name": "grp-FRD-NH02-CDE-API", "app_id": "FRD", "nh": "NH02", "sz": "CDE", "subtype": "API",
     "description": "FRD API", "members": [
        {"type": "ip", "value": "svr-10.1.1.60", "description": "FRD API 1"},
     ]},

    # --- LND (NH09, CCS) ---
    {"name": "grp-LND-NH09-CCS-WEB", "app_id": "LND", "nh": "NH09", "sz": "CCS", "subtype": "WEB",
     "description": "LND Web Portal", "members": [
        {"type": "ip", "value": "svr-10.8.1.10", "description": "LND Web 1"},
     ]},
    {"name": "grp-LND-NH09-CCS-APP", "app_id": "LND", "nh": "NH09", "sz": "CCS", "subtype": "APP",
     "description": "LND Loan Engine", "members": [
        {"type": "ip", "value": "svr-10.8.1.20", "description": "LND App 1"},
        {"type": "ip", "value": "svr-10.8.1.21", "description": "LND App 2"},
     ]},
    {"name": "grp-LND-NH09-CCS-DB", "app_id": "LND", "nh": "NH09", "sz": "CCS", "subtype": "DB",
     "description": "LND Database", "members": [
        {"type": "ip", "value": "svr-10.8.1.30", "description": "LND DB Primary"},
     ]},
    {"name": "grp-LND-NH09-CCS-BAT", "app_id": "LND", "nh": "NH09", "sz": "CCS", "subtype": "BAT",
     "description": "LND Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.8.1.40", "description": "LND Batch 1"},
     ]},

    # --- WLT (NH10, CDE) ---
    {"name": "grp-WLT-NH10-CDE-WEB", "app_id": "WLT", "nh": "NH10", "sz": "CDE", "subtype": "WEB",
     "description": "WLT Web Interface", "members": [
        {"type": "ip", "value": "svr-10.9.1.10", "description": "WLT Web 1"},
     ]},
    {"name": "grp-WLT-NH10-CDE-APP", "app_id": "WLT", "nh": "NH10", "sz": "CDE", "subtype": "APP",
     "description": "WLT Portfolio Engine", "members": [
        {"type": "ip", "value": "svr-10.9.1.20", "description": "WLT App 1"},
        {"type": "ip", "value": "svr-10.9.1.21", "description": "WLT App 2"},
     ]},
    {"name": "grp-WLT-NH10-CDE-DB", "app_id": "WLT", "nh": "NH10", "sz": "CDE", "subtype": "DB",
     "description": "WLT Database", "members": [
        {"type": "ip", "value": "svr-10.9.1.30", "description": "WLT DB Primary"},
        {"type": "ip", "value": "svr-10.9.1.31", "description": "WLT DB Replica"},
     ]},
    {"name": "grp-WLT-NH10-CDE-API", "app_id": "WLT", "nh": "NH10", "sz": "CDE", "subtype": "API",
     "description": "WLT API", "members": [
        {"type": "ip", "value": "svr-10.9.1.40", "description": "WLT API 1"},
     ]},

    # --- CBK (NH08, CCS) ---
    {"name": "grp-CBK-NH08-CCS-APP", "app_id": "CBK", "nh": "NH08", "sz": "CCS", "subtype": "APP",
     "description": "CBK Core Engine", "members": [
        {"type": "ip", "value": "svr-10.7.1.10", "description": "CBK App 1"},
        {"type": "ip", "value": "svr-10.7.1.11", "description": "CBK App 2"},
        {"type": "ip", "value": "svr-10.7.1.12", "description": "CBK App 3"},
     ]},
    {"name": "grp-CBK-NH08-CCS-DB", "app_id": "CBK", "nh": "NH08", "sz": "CCS", "subtype": "DB",
     "description": "CBK Database Cluster", "members": [
        {"type": "ip", "value": "svr-10.7.1.20", "description": "CBK DB Primary"},
        {"type": "ip", "value": "svr-10.7.1.21", "description": "CBK DB Standby"},
        {"type": "ip", "value": "svr-10.7.1.22", "description": "CBK DB Archive"},
     ]},
    {"name": "grp-CBK-NH08-CCS-MQ", "app_id": "CBK", "nh": "NH08", "sz": "CCS", "subtype": "MQ",
     "description": "CBK Message Bus", "members": [
        {"type": "ip", "value": "svr-10.7.1.30", "description": "CBK MQ 1"},
        {"type": "ip", "value": "svr-10.7.1.31", "description": "CBK MQ 2"},
     ]},
    {"name": "grp-CBK-NH08-CCS-API", "app_id": "CBK", "nh": "NH08", "sz": "CCS", "subtype": "API",
     "description": "CBK API Gateway", "members": [
        {"type": "ip", "value": "svr-10.7.1.40", "description": "CBK API 1"},
     ]},
    {"name": "grp-CBK-NH08-CCS-BAT", "app_id": "CBK", "nh": "NH08", "sz": "CCS", "subtype": "BAT",
     "description": "CBK Batch Processing", "members": [
        {"type": "ip", "value": "svr-10.7.1.50", "description": "CBK Batch 1"},
        {"type": "ip", "value": "svr-10.7.1.51", "description": "CBK Batch 2"},
     ]},

    # --- EPT (NH01, PAA) - Enterprise Portal (PAA zone, internet-facing) ---
    {"name": "grp-EPT-NH01-PAA-WEB", "app_id": "EPT", "nh": "NH01", "sz": "PAA", "subtype": "WEB",
     "description": "EPT Web Frontend (PAA)", "members": [
        {"type": "ip", "value": "svr-10.0.3.10", "description": "EPT Web 1"},
        {"type": "ip", "value": "svr-10.0.3.11", "description": "EPT Web 2"},
     ]},
    {"name": "grp-EPT-NH01-PAA-APP", "app_id": "EPT", "nh": "NH01", "sz": "PAA", "subtype": "APP",
     "description": "EPT App Backend (PAA)", "members": [
        {"type": "ip", "value": "svr-10.0.3.20", "description": "EPT App 1"},
        {"type": "ip", "value": "svr-10.0.3.21", "description": "EPT App 2"},
     ]},
    {"name": "grp-EPT-NH01-PAA-API", "app_id": "EPT", "nh": "NH01", "sz": "PAA", "subtype": "API",
     "description": "EPT API Gateway (PAA)", "members": [
        {"type": "ip", "value": "svr-10.0.3.30", "description": "EPT API 1"},
     ]},

    # --- MBK (NH07, CPA) - Mobile Banking ---
    {"name": "grp-MBK-NH07-CPA-WEB", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "WEB",
     "description": "MBK Mobile Web", "members": [
        {"type": "ip", "value": "svr-10.6.1.170", "description": "MBK Web 1"},
     ]},
    {"name": "grp-MBK-NH07-CPA-APP", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "APP",
     "description": "MBK App Engine", "members": [
        {"type": "ip", "value": "svr-10.6.1.180", "description": "MBK App 1"},
        {"type": "ip", "value": "svr-10.6.1.181", "description": "MBK App 2"},
     ]},
    {"name": "grp-MBK-NH07-CPA-DB", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "DB",
     "description": "MBK Database", "members": [
        {"type": "ip", "value": "svr-10.6.1.190", "description": "MBK DB Primary"},
     ]},
    {"name": "grp-MBK-NH07-CPA-API", "app_id": "MBK", "nh": "NH07", "sz": "CPA", "subtype": "API",
     "description": "MBK API Gateway", "members": [
        {"type": "ip", "value": "svr-10.6.1.200", "description": "MBK API 1"},
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
    app_configs = [
        ("CRM", "Customer Relationship Manager", "AD-1001", "DC_LEGACY_A",
         {"Production": ("pol-CRM-legacy", "LegacyFW-A", "Zone-A-Internal", "Zone-A-DB"),
          "Non-Production": ("pol-CRM-np-legacy", "LegacyFW-A-NP", "Zone-A-Dev", "Zone-A-Dev-DB"),
          "Pre-Production": ("pol-CRM-pp-legacy", "LegacyFW-A-PP", "Zone-A-STG", "Zone-A-STG-DB")}),
        ("HRM", "Human Resource Manager", "AD-1002", "DC_LEGACY_B",
         {"Production": ("pol-HRM-legacy", "LegacyFW-B", "Zone-B-Internal", "Zone-B-DB"),
          "Non-Production": ("pol-HRM-np-legacy", "LegacyFW-B-NP", "Zone-B-Dev", "Zone-B-Dev-DB")}),
        ("TRD", "Trading Platform", "AD-1003", "DC_LEGACY_C",
         {"Production": ("pol-TRD-legacy", "LegacyFW-C", "Zone-C-Trade", "Zone-C-Trade-DB"),
          "Non-Production": ("pol-TRD-np-legacy", "LegacyFW-C-NP", "Zone-C-Dev", "Zone-C-Dev-DB"),
          "Pre-Production": ("pol-TRD-pp-legacy", "LegacyFW-C-PP", "Zone-C-STG", "Zone-C-STG-DB")}),
        ("PAY", "Payment Gateway", "AD-1004", "DC_LEGACY_A",
         {"Production": ("pol-PAY-legacy", "LegacyFW-A", "Zone-A-Pay", "Zone-A-Pay-DB"),
          "Pre-Production": ("pol-PAY-pp-legacy", "LegacyFW-A-PP", "Zone-A-STG-Pay", "Zone-A-STG-Pay-DB")}),
        ("INS", "Insurance Portal", "AD-1005", "DC_LEGACY_D",
         {"Production": ("pol-INS-legacy", "LegacyFW-D", "Zone-D-Internal", "Zone-D-DB"),
          "Non-Production": ("pol-INS-np-legacy", "LegacyFW-D-NP", "Zone-D-Dev", "Zone-D-Dev-DB")}),
        ("KYC", "KYC Compliance", "AD-1006", "DC_LEGACY_F",
         {"Production": ("pol-KYC-legacy", "LegacyFW-F", "Zone-F-Internal", "Zone-F-DB"),
          "Non-Production": ("pol-KYC-np-legacy", "LegacyFW-F-NP", "Zone-F-Dev", "Zone-F-Dev-DB")}),
        ("FRD", "Fraud Detection", "AD-1007", "DC_LEGACY_E",
         {"Production": ("pol-FRD-legacy", "LegacyFW-E", "Zone-E-Internal", "Zone-E-DB")}),
        ("LND", "Lending Platform", "AD-1008", "DC_LEGACY_D",
         {"Production": ("pol-LND-legacy", "LegacyFW-D", "Zone-D-Lending", "Zone-D-Lending-DB"),
          "Non-Production": ("pol-LND-np-legacy", "LegacyFW-D-NP", "Zone-D-Dev-Lend", "Zone-D-Dev-Lend-DB")}),
        ("WLT", "Wealth Management", "AD-1009", "DC_LEGACY_B",
         {"Production": ("pol-WLT-legacy", "LegacyFW-B", "Zone-B-Wealth", "Zone-B-Wealth-DB"),
          "Pre-Production": ("pol-WLT-pp-legacy", "LegacyFW-B-PP", "Zone-B-STG-W", "Zone-B-STG-W-DB")}),
        ("CBK", "Core Banking", "AD-1010", "DC_LEGACY_A",
         {"Production": ("pol-CBK-legacy", "LegacyFW-A", "Zone-A-Core", "Zone-A-Core-DB"),
          "Non-Production": ("pol-CBK-np-legacy", "LegacyFW-A-NP", "Zone-A-Dev-Core", "Zone-A-Dev-Core-DB"),
          "Pre-Production": ("pol-CBK-pp-legacy", "LegacyFW-A-PP", "Zone-A-STG-Core", "Zone-A-STG-Core-DB")}),
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
                "rule_source": f"{base}.1.10\n{base}.1.11",
                "rule_source_expanded": f"svr-{base}.1.10\n  {base}.1.10 (Web Server 1)\nsvr-{base}.1.11\n  {base}.1.11 (Web Server 2)",
                "rule_source_zone": src_zone,
                "rule_destination": f"{base}.2.10\n{base}.2.11\n{base}.2.12",
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
                "rule_source": f"{base}.2.10\n{base}.2.11\n{base}.2.12",
                "rule_source_expanded": f"svr-{base}.2.10\n  {base}.2.10 (App 1)\nsvr-{base}.2.11\n  {base}.2.11 (App 2)\nsvr-{base}.2.12\n  {base}.2.12 (App 3)",
                "rule_source_zone": src_zone,
                "rule_destination": f"{base}.3.10\n{base}.3.11",
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
                    "rule_source": f"{base}.2.10\n{base}.2.11",
                    "rule_source_expanded": f"svr-{base}.2.10\n  App 1\nsvr-{base}.2.11\n  App 2",
                    "rule_source_zone": src_zone,
                    "rule_destination": f"{base}.4.10\n{base}.4.11",
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
                "rule_source": f"{base}.2.10",
                "rule_source_expanded": f"svr-{base}.2.10\n  App Server 1",
                "rule_source_zone": src_zone,
                "rule_destination": f"10.70.1.10\n10.70.1.11",
                "rule_destination_expanded": "svr-10.70.1.10\n  DMZ API 1\nsvr-10.70.1.11\n  DMZ API 2",
                "rule_destination_zone": "Zone-DMZ",
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
                    "rule_source": f"{base}.5.10",
                    "rule_source_expanded": f"svr-{base}.5.10\n  Batch Server 1",
                    "rule_source_zone": src_zone,
                    "rule_destination": f"{base}.3.10",
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
                "rule_source": f"10.80.1.100\n10.80.1.101",
                "rule_source_expanded": "svr-10.80.1.100\n  Monitor Agent 1\nsvr-10.80.1.101\n  Monitor Agent 2",
                "rule_source_zone": "Zone-MGT",
                "rule_destination": f"{base}.1.10\n{base}.2.10\n{base}.3.10",
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
    """Build comprehensive app-based IP mappings."""
    mappings: list[dict[str, Any]] = []
    idx = 0

    # Mapping config: (app_id, legacy_dc, ngdc_dc, nh, sz, legacy_base, ngdc_entries)
    mapping_configs = [
        # CRM: DC_LEGACY_A -> GAMMA_NGDC
        ("CRM", "DC_LEGACY_A", "GAMMA_NGDC", "NH02", "CDE", "10.25", [
            ("10.25.1.10", "svr-10.50.1.10", "grp-CRM-NH02-CDE-WEB", "CRM Web 1"),
            ("10.25.1.11", "svr-10.50.1.11", "grp-CRM-NH02-CDE-WEB", "CRM Web 2"),
            ("10.25.2.10", "svr-10.50.1.20", "grp-CRM-NH02-CDE-APP", "CRM App 1"),
            ("10.25.2.11", "svr-10.50.1.21", "grp-CRM-NH02-CDE-APP", "CRM App 2"),
            ("10.25.2.12", "svr-10.50.1.22", "grp-CRM-NH02-CDE-APP", "CRM App 3"),
            ("10.25.3.10", "svr-10.50.1.30", "grp-CRM-NH02-CDE-DB", "CRM DB Primary"),
            ("10.25.3.11", "svr-10.50.1.31", "grp-CRM-NH02-CDE-DB", "CRM DB Standby"),
            ("10.25.5.10", "svr-10.50.1.40", "grp-CRM-NH02-CDE-BAT", "CRM Batch 1"),
        ]),
        # HRM: DC_LEGACY_B -> ALPHA_NGDC
        ("HRM", "DC_LEGACY_B", "ALPHA_NGDC", "NH01", "GEN", "10.26", [
            ("10.26.1.10", "svr-10.0.2.130", "grp-HRM-NH01-GEN-WEB", "HRM Web 1"),
            ("10.26.1.11", "svr-10.0.2.131", "grp-HRM-NH01-GEN-WEB", "HRM Web 2"),
            ("10.26.2.10", "svr-10.0.2.140", "grp-HRM-NH01-GEN-APP", "HRM App 1"),
            ("10.26.2.11", "svr-10.0.2.141", "grp-HRM-NH01-GEN-APP", "HRM App 2"),
            ("10.26.3.10", "svr-10.0.2.150", "grp-HRM-NH01-GEN-DB", "HRM DB Primary"),
            ("10.26.3.11", "svr-10.0.2.151", "grp-HRM-NH01-GEN-DB", "HRM DB Replica"),
            ("10.26.5.10", "svr-10.0.2.160", "grp-HRM-NH01-GEN-BAT", "HRM Batch 1"),
        ]),
        # TRD: DC_LEGACY_C -> BETA_NGDC
        ("TRD", "DC_LEGACY_C", "BETA_NGDC", "NH06", "CDE", "10.27", [
            ("10.27.1.10", "svr-172.16.20.10", "grp-TRD-NH06-CDE-WEB", "TRD Web 1"),
            ("10.27.1.11", "svr-172.16.20.11", "grp-TRD-NH06-CDE-WEB", "TRD Web 2"),
            ("10.27.2.10", "svr-172.16.20.20", "grp-TRD-NH06-CDE-APP", "TRD App 1"),
            ("10.27.2.11", "svr-172.16.20.21", "grp-TRD-NH06-CDE-APP", "TRD App 2"),
            ("10.27.3.10", "svr-172.16.20.30", "grp-TRD-NH06-CDE-DB", "TRD DB Primary"),
            ("10.27.3.11", "svr-172.16.20.31", "grp-TRD-NH06-CDE-DB", "TRD DB Standby"),
            ("10.27.4.10", "svr-172.16.20.40", "grp-TRD-NH06-CDE-MQ", "TRD MQ 1"),
        ]),
        # PAY: DC_LEGACY_A -> GAMMA_NGDC
        ("PAY", "DC_LEGACY_A", "GAMMA_NGDC", "NH07", "CPA", "10.25", [
            ("10.25.10.10", "svr-10.50.6.130", "grp-PAY-NH07-CPA-APP", "PAY App 1"),
            ("10.25.10.11", "svr-10.50.6.131", "grp-PAY-NH07-CPA-APP", "PAY App 2"),
            ("10.25.11.10", "svr-10.50.6.150", "grp-PAY-NH07-CPA-DB", "PAY DB Primary"),
            ("10.25.12.10", "svr-10.50.6.160", "grp-PAY-NH07-CPA-MQ", "PAY MQ 1"),
        ]),
        # INS: DC_LEGACY_D -> ALPHA_NGDC
        ("INS", "DC_LEGACY_D", "ALPHA_NGDC", "NH04", "GEN", "10.28", [
            ("10.28.1.10", "svr-10.3.1.130", "grp-INS-NH04-GEN-WEB", "INS Web 1"),
            ("10.28.1.11", "svr-10.3.1.131", "grp-INS-NH04-GEN-WEB", "INS Web 2"),
            ("10.28.2.10", "svr-10.3.1.140", "grp-INS-NH04-GEN-APP", "INS App 1"),
            ("10.28.3.10", "svr-10.3.1.150", "grp-INS-NH04-GEN-DB", "INS DB Primary"),
            ("10.28.5.10", "svr-10.3.1.160", "grp-INS-NH04-GEN-BAT", "INS Batch 1"),
        ]),
        # KYC: DC_LEGACY_F -> ALPHA_NGDC
        ("KYC", "DC_LEGACY_F", "ALPHA_NGDC", "NH05", "GEN", "10.30", [
            ("10.30.1.10", "svr-10.4.1.130", "grp-KYC-NH05-GEN-WEB", "KYC Web 1"),
            ("10.30.2.10", "svr-10.4.1.140", "grp-KYC-NH05-GEN-APP", "KYC App 1"),
            ("10.30.2.11", "svr-10.4.1.141", "grp-KYC-NH05-GEN-APP", "KYC App 2"),
            ("10.30.3.10", "svr-10.4.2.10", "grp-KYC-NH05-GEN-DB", "KYC DB Primary"),
        ]),
        # FRD: DC_LEGACY_E -> ALPHA_NGDC
        ("FRD", "DC_LEGACY_E", "ALPHA_NGDC", "NH02", "CDE", "10.29", [
            ("10.29.2.10", "svr-10.1.1.50", "grp-FRD-NH02-CDE-APP", "FRD Engine 1"),
            ("10.29.2.11", "svr-10.1.1.51", "grp-FRD-NH02-CDE-APP", "FRD Engine 2"),
            ("10.29.3.10", "svr-10.1.2.20", "grp-FRD-NH02-CDE-DB", "FRD DB Primary"),
            ("10.29.4.10", "svr-10.1.1.55", "grp-FRD-NH02-CDE-MQ", "FRD Kafka 1"),
        ]),
        # LND: DC_LEGACY_D -> ALPHA_NGDC
        ("LND", "DC_LEGACY_D", "ALPHA_NGDC", "NH09", "CCS", "10.28", [
            ("10.28.10.10", "svr-10.8.1.10", "grp-LND-NH09-CCS-WEB", "LND Web 1"),
            ("10.28.11.10", "svr-10.8.1.20", "grp-LND-NH09-CCS-APP", "LND App 1"),
            ("10.28.12.10", "svr-10.8.1.30", "grp-LND-NH09-CCS-DB", "LND DB Primary"),
            ("10.28.13.10", "svr-10.8.1.40", "grp-LND-NH09-CCS-BAT", "LND Batch 1"),
        ]),
        # WLT: DC_LEGACY_B -> ALPHA_NGDC
        ("WLT", "DC_LEGACY_B", "ALPHA_NGDC", "NH10", "CDE", "10.26", [
            ("10.26.10.10", "svr-10.9.1.10", "grp-WLT-NH10-CDE-WEB", "WLT Web 1"),
            ("10.26.11.10", "svr-10.9.1.20", "grp-WLT-NH10-CDE-APP", "WLT App 1"),
            ("10.26.11.11", "svr-10.9.1.21", "grp-WLT-NH10-CDE-APP", "WLT App 2"),
            ("10.26.12.10", "svr-10.9.1.30", "grp-WLT-NH10-CDE-DB", "WLT DB Primary"),
        ]),
        # CBK: DC_LEGACY_A -> ALPHA_NGDC (note: different target than CRM)
        ("CBK", "DC_LEGACY_A", "ALPHA_NGDC", "NH08", "CCS", "10.25", [
            ("10.25.20.10", "svr-10.7.1.10", "grp-CBK-NH08-CCS-APP", "CBK App 1"),
            ("10.25.20.11", "svr-10.7.1.11", "grp-CBK-NH08-CCS-APP", "CBK App 2"),
            ("10.25.21.10", "svr-10.7.1.20", "grp-CBK-NH08-CCS-DB", "CBK DB Primary"),
            ("10.25.21.11", "svr-10.7.1.21", "grp-CBK-NH08-CCS-DB", "CBK DB Standby"),
            ("10.25.22.10", "svr-10.7.1.30", "grp-CBK-NH08-CCS-MQ", "CBK MQ 1"),
        ]),
        # EPT: DC_LEGACY_B -> ALPHA_NGDC (PAA zone)
        ("EPT", "DC_LEGACY_B", "ALPHA_NGDC", "NH01", "PAA", "10.26", [
            ("10.26.30.10", "svr-10.0.3.10", "grp-EPT-NH01-PAA-WEB", "EPT Web 1"),
            ("10.26.30.11", "svr-10.0.3.11", "grp-EPT-NH01-PAA-WEB", "EPT Web 2"),
            ("10.26.31.10", "svr-10.0.3.20", "grp-EPT-NH01-PAA-APP", "EPT App 1"),
            ("10.26.31.11", "svr-10.0.3.21", "grp-EPT-NH01-PAA-APP", "EPT App 2"),
            ("10.26.32.10", "svr-10.0.3.30", "grp-EPT-NH01-PAA-API", "EPT API 1"),
        ]),
        # MBK: DC_LEGACY_C -> ALPHA_NGDC
        ("MBK", "DC_LEGACY_C", "ALPHA_NGDC", "NH07", "CPA", "10.27", [
            ("10.27.30.10", "svr-10.6.1.170", "grp-MBK-NH07-CPA-WEB", "MBK Web 1"),
            ("10.27.31.10", "svr-10.6.1.180", "grp-MBK-NH07-CPA-APP", "MBK App 1"),
            ("10.27.31.11", "svr-10.6.1.181", "grp-MBK-NH07-CPA-APP", "MBK App 2"),
            ("10.27.32.10", "svr-10.6.1.190", "grp-MBK-NH07-CPA-DB", "MBK DB Primary"),
            ("10.27.33.10", "svr-10.6.1.200", "grp-MBK-NH07-CPA-API", "MBK API 1"),
        ]),
    ]

    for app_id, legacy_dc, ngdc_dc, nh, sz, _, entries in mapping_configs:
        for legacy_ip, ngdc_ip, ngdc_group, desc in entries:
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
    """Build seed change requests."""
    from datetime import datetime, timedelta
    return [
        {"chg_id": "CHG10001", "rule_ids": ["LR-1001"], "status": "Approved",
         "description": "CRM Web to App HTTPS rule migration",
         "requested_by": "Team Eta", "approved_by": "Security Team",
         "created_at": (datetime.utcnow() + timedelta(days=-31)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-30)).isoformat()},
        {"chg_id": "CHG10002", "rule_ids": ["LR-1007", "LR-1008"], "status": "Pending",
         "description": "HRM Production rules migration batch",
         "requested_by": "Team Platform", "approved_by": None,
         "created_at": (datetime.utcnow() + timedelta(days=-5)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-5)).isoformat()},
        {"chg_id": "CHG10003", "rule_ids": ["LR-1013", "LR-1014", "LR-1015"], "status": "Pending",
         "description": "TRD Trading Platform migration - Production rules",
         "requested_by": "Team Xi", "approved_by": None,
         "created_at": (datetime.utcnow() + timedelta(days=-2)).isoformat(),
         "updated_at": (datetime.utcnow() + timedelta(days=-2)).isoformat()},
    ]


# Build the data at module load time
SEED_LEGACY_RULES = _build_legacy_rules()
SEED_IP_MAPPINGS = _build_ip_mappings()
