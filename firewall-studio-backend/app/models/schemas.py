from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime


# ---- Revamp: Shared Services, Presences, Multi-DC Fan-out ----
# These models are additive; they augment (do not replace) the existing
# egress/ingress architecture. See docs/ARCHITECTURE_PROPOSAL for context.

class Environment(str, Enum):
    PRODUCTION = "Production"
    NON_PRODUCTION = "Non-Production"
    PRE_PRODUCTION = "Pre-Production"


class MemberType(str, Enum):
    IP = "ip"
    CIDR = "cidr"
    SUBNET = "subnet"
    RANGE = "range"
    GROUP = "group"


class MemberSpec(BaseModel):
    """Unified membership shape used by all group-like owners (apps,
    shared services, ad-hoc destinations)."""

    type: MemberType = MemberType.IP
    value: str
    description: Optional[str] = ""
    dc_id: Optional[str] = None  # empty => valid in any DC the parent is in


class AppPresence(BaseModel):
    """DC+env-specific presence of an Application."""

    app_distributed_id: str
    dc_id: str
    dc_type: Literal["NGDC", "Legacy"] = "NGDC"
    environment: Environment = Environment.PRODUCTION
    nh_id: str
    sz_code: str
    has_ingress: bool = False
    egress_members: list[MemberSpec] = []
    ingress_members: list[MemberSpec] = []


class SharedServiceCategory(str, Enum):
    MESSAGING = "Messaging"
    DATABASE = "Database"
    OBSERVABILITY = "Observability"
    IDENTITY = "Identity"
    CACHE = "Cache"
    OTHER = "Other"


class SharedServicePresence(BaseModel):
    """DC+env-specific presence of a Shared Service."""

    service_id: str
    dc_id: str
    dc_type: Literal["NGDC", "Legacy"] = "NGDC"
    environment: Environment = Environment.PRODUCTION
    nh_id: str
    sz_code: str
    members: list[MemberSpec] = []


class SharedService(BaseModel):
    """Centralized shared service (MQ, Kafka, DB, AppD, Splunk, Redis, …)
    available as a rule destination.

    Group naming: grp-<service_id>-<NH>-<SZ>
    """

    service_id: str  # slug, e.g. "KAFKA"
    name: str
    category: SharedServiceCategory = SharedServiceCategory.OTHER
    owner: Optional[str] = ""
    description: Optional[str] = ""
    icon: Optional[str] = ""   # optional emoji/symbol used by the DnD sidebar
    color: Optional[str] = ""  # optional CSS color hint for the DnD sidebar
    environments: list[Environment] = [Environment.PRODUCTION]
    tags: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ---- Revamp: Extended Group shape ----

class FirewallGroupOwnerKind(str, Enum):
    APP_EGRESS = "app_egress"
    APP_INGRESS = "app_ingress"
    SHARED_SERVICE = "shared_service"
    ADHOC_DESTINATION = "adhoc_destination"


class FirewallGroupModel(BaseModel):
    """Unified firewall group shape (new schema — existing groups are
    auto-tagged during migration)."""

    name: str
    owner_kind: FirewallGroupOwnerKind = FirewallGroupOwnerKind.APP_EGRESS
    owner_ref: Optional[str] = None  # app_distributed_id OR service_id
    dc_id: Optional[str] = None
    environment: Environment = Environment.PRODUCTION
    nh_id: Optional[str] = None
    sz_code: Optional[str] = None
    direction: Literal["egress", "ingress"] = "egress"
    members: list[MemberSpec] = []
    description: Optional[str] = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ---- Revamp: Multi-DC rule fan-out ----

class DestinationEntityKind(str, Enum):
    APP_INGRESS = "app_ingress"
    SHARED_SERVICE = "shared_service"
    ADHOC = "adhoc"


class RuleRequestCreate(BaseModel):
    """Logical rule request submitted in Studio — fans out into per-DC
    PhysicalRule records.
    """

    application_ref: str  # source app_distributed_id
    destination_kind: DestinationEntityKind
    destination_ref: Optional[str] = None  # app_distributed_id OR service_id
    environment: Environment = Environment.PRODUCTION
    ports: str = "TCP 8080"
    action: Literal["ACCEPT", "DROP"] = "ACCEPT"
    description: str = ""
    src_members_override: list[MemberSpec] = []
    dst_members_override: list[MemberSpec] = []
    requested_dcs: Optional[list[str]] = None  # optional DC scoping
    include_cross_dc: bool = False
    owner: str = ""


class PhysicalRule(BaseModel):
    rule_id: str
    request_id: str
    src_dc: str
    dst_dc: str
    src_group_ref: str
    dst_group_ref: str
    src_nh: Optional[str] = None
    src_sz: Optional[str] = None
    dst_nh: Optional[str] = None
    dst_sz: Optional[str] = None
    ports: str = ""
    action: str = "ACCEPT"
    environment: Environment = Environment.PRODUCTION
    policy_result: Optional[str] = None  # filled from PolicyResult at fan-out
    compiled_text: Optional[str] = None
    lifecycle_status: str = "Submitted"


class RuleRequestRecord(BaseModel):
    request_id: str
    application_ref: str
    destination_kind: DestinationEntityKind
    destination_ref: Optional[str] = None
    environment: Environment
    ports: str
    action: str = "ACCEPT"
    description: str = ""
    owner: str = ""
    status: str = "Draft"  # Draft | Submitted | Approved | Rejected
    expansion: list[PhysicalRule] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
