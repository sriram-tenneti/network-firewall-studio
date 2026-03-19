"""Organization configuration, naming standards, and enforcement rules.

This module contains all configurable organization-level settings.
Update these values to match your organization's constructs.
When MongoDB is integrated, these will be stored in the database instead.
"""

# =====================================================================
# ORGANIZATION CONFIGURATION
# Central configuration for the organization's firewall management
# =====================================================================
ORG_CONFIG = {
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


# =====================================================================
# NAMING STANDARDS
# Defines the naming conventions for groups, servers, and ranges.
# All firewall objects must follow these patterns.
# =====================================================================
NAMING_STANDARDS = {
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
# ENVIRONMENTS
# Supported deployment environments
# =====================================================================
ENVIRONMENTS = [
    {"name": "Production", "code": "PROD", "description": "Live production environment"},
    {"name": "Non-Production", "code": "NON-PROD", "description": "Shared non-production for testing"},
    {"name": "Pre-Production", "code": "PRE-PROD", "description": "Staging environment"},
    {"name": "Development", "code": "DEV", "description": "Development and sandbox"},
    {"name": "Staging", "code": "STG", "description": "Final validation before production"},
    {"name": "DR", "code": "DR", "description": "Disaster recovery"},
]


# =====================================================================
# PREDEFINED DESTINATIONS
# Common destination groups used across rules
# =====================================================================
PREDEFINED_DESTINATIONS = [
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
