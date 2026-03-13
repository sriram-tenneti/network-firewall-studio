from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class RuleStatus(str, Enum):
    DRAFT = "Draft"
    DEPLOYED = "Deployed"
    PENDING_REVIEW = "Pending Review"
    CERTIFIED = "Certified"
    EXPIRED = "Expired"
    DELETED = "Deleted"


class PolicyResult(str, Enum):
    PERMITTED = "Permitted"
    BLOCKED = "Blocked"
    EXCEPTION_REQUIRED = "Exception Required"
    NEEDS_REVIEW = "Needs Review"


class MigrationStatus(str, Enum):
    AUTO_MAPPED = "Auto-Mapped"
    NEEDS_REVIEW = "Needs Review"
    NEW_GROUP = "New Group"
    CONFLICT = "Conflict"
    BLOCKED = "Blocked"
    DRAFT = "Draft"
    POLICY_REVIEW = "Policy Review"


class MappingStatus(str, Enum):
    AUTOMAPPED = "Automapped"
    NEEDS_REVIEW = "Needs Review"
    BLOCKED = "Blocked"


class SourceType(str, Enum):
    SINGLE_IP = "Single IP"
    SUBNET = "Subnet"
    GROUP = "Group"


# ---- Firewall Design Studio Models ----

class SourceConfig(BaseModel):
    source_type: SourceType = SourceType.SINGLE_IP
    ip_address: Optional[str] = None
    cidr: Optional[str] = None
    group_name: Optional[str] = None
    ports: str = "TCP 8080"
    neighbourhood: Optional[str] = None
    security_zone: Optional[str] = None


class DestinationConfig(BaseModel):
    name: str
    security_zone: Optional[str] = None
    dest_ip: Optional[str] = None
    ports: str = "TCP 8443"
    is_predefined: bool = True


class FirewallRule(BaseModel):
    id: Optional[str] = None
    rule_id: str
    application: str = "Ordering System"
    environment: str = "Production"
    datacenter: str = "DC1"
    source: SourceConfig
    destination: DestinationConfig
    policy_result: PolicyResult = PolicyResult.PERMITTED
    status: RuleStatus = RuleStatus.DRAFT
    expiry: Optional[str] = None
    owner: str = "Jane Smith"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    certified_at: Optional[str] = None
    certified_by: Optional[str] = None


class FirewallRuleCreate(BaseModel):
    application: str = "Ordering System"
    environment: str = "Production"
    datacenter: str = "DC1"
    source: SourceConfig
    destination: DestinationConfig
    owner: str = "Jane Smith"


class FirewallRuleUpdate(BaseModel):
    source: Optional[SourceConfig] = None
    destination: Optional[DestinationConfig] = None
    status: Optional[RuleStatus] = None
    owner: Optional[str] = None
    expiry: Optional[str] = None


# ---- Migration Studio Models ----

class MigrationDetails(BaseModel):
    id: Optional[str] = None
    application: str
    source_legacy_dc: str
    target_ngdc: str
    map_to_standard_groups: bool = True
    map_to_subnet_cidr: bool = False
    status: str = "Draft"
    created_at: Optional[str] = None


class MigrationMapping(BaseModel):
    id: Optional[str] = None
    migration_id: str
    legacy_source: str
    legacy_source_detail: Optional[str] = None
    legacy_group: Optional[str] = None
    ngdc_target: str
    ngdc_target_detail: Optional[str] = None
    mapping_status: MigrationStatus = MigrationStatus.AUTO_MAPPED
    trust_zones_automapped: int = 0
    related_policies: list[str] = []


class MigrationRuleLifecycle(BaseModel):
    id: Optional[str] = None
    migration_id: str
    rule_id: str
    source: str
    source_ip: Optional[str] = None
    mapping_status: str = "Draft"
    ngdc_target: str
    destination_detail: Optional[str] = None


class MigrationCreate(BaseModel):
    application: str
    source_legacy_dc: str
    target_ngdc: str
    map_to_standard_groups: bool = True
    map_to_subnet_cidr: bool = False


# ---- NGDC Reference Data Models ----

class Neighbourhood(BaseModel):
    name: str
    subnets: list[str] = []


class NGDCDataCenter(BaseModel):
    name: str
    code: str
    neighbourhoods: list[Neighbourhood] = []
    ip_groups: list[dict] = []
    rule_count: int = 0


class SecurityZone(BaseModel):
    name: str
    code: str
    description: str = ""


class PredefinedDestination(BaseModel):
    name: str
    security_zone: str
    description: Optional[str] = None


# ---- Policy Validation ----

class PolicyValidationRequest(BaseModel):
    source: SourceConfig
    destination: DestinationConfig
    application: str = ""
    environment: str = "Production"


class PolicyValidationResult(BaseModel):
    result: PolicyResult
    message: str
    details: list[str] = []
    ngdc_zone_check: bool = True
    birthright_compliant: bool = True


# ---- CHG Request ----

class CHGRequest(BaseModel):
    id: Optional[str] = None
    chg_number: str
    rule_ids: list[str] = []
    migration_id: Optional[str] = None
    status: str = "Open"
    created_at: Optional[str] = None
    description: str = ""


# ---- History ----

class RuleHistoryEntry(BaseModel):
    id: Optional[str] = None
    rule_id: str
    action: str
    timestamp: str
    user: str
    details: str = ""
