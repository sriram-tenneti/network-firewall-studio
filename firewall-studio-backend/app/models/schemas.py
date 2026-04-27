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


class PortBinding(BaseModel):
    """Reference to a port — either by `port_id` into the global Port
    Catalog or an inline `{protocol, port, label}` spec for service /
    app -specific customs that don't belong in the shared library."""

    port_id: Optional[str] = None
    protocol: Optional[Literal["TCP", "UDP", "ICMP"]] = None
    port: Optional[int] = None
    label: Optional[str] = ""


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
    # Listener/ingress ports exposed by this presence. Used by the rule
    # builder's Port Picker as defaults when this app is chosen as the
    # destination. Empty = no defaults; picker falls back to the global
    # Port Catalog.
    ingress_ports: list[PortBinding] = []


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


class DeploymentMode(str, Enum):
    """How an Application or SharedService is deployed across DCs.

    - ALL_NGDC (default): present in every NGDC DC with the same
      `(NH, SZ)` tier definition. The portal auto-fans presences across
      all NGDC DCs whenever a new tier or DC is added.
    - SELECTIVE: per-DC presences must be created explicitly (legacy
      behaviour, primarily used for Heritage/Legacy DCs).
    - ALL_NGDC_WITH_EXCEPTIONS: ALL_NGDC minus a list of excluded DCs.
    """

    ALL_NGDC = "all_ngdc"
    SELECTIVE = "selective"
    ALL_NGDC_WITH_EXCEPTIONS = "all_ngdc_with_exceptions"


class TierSpec(BaseModel):
    """Tier definition shared by all NGDC presences of an App/SharedService.

    Each tier replicates as one presence per NGDC DC. Heritage/Legacy DCs
    get a single non-segmented presence per env (NH/SZ are optional).
    """

    nh_id: str
    sz_code: str
    has_ingress: bool = False
    label: Optional[str] = ""  # e.g. "web", "db", "mq"


class HeritageTierSpec(BaseModel):
    """Tier definition for apps/services that still live on Heritage
    infrastructure that doesn't have NH/SZ segmentation.

    A Heritage tier is bound to a specific Heritage DC (one tier per
    Heritage DC presence). The portal auto-materialises one
    AppPresence (with ``dc_type=Heritage``, no NH/SZ) per tier and
    derives groups using the flat ``grp-<APP>-HERITAGE-<DC>``
    convention. (Pre-rename name: ``LegacyTierSpec`` — alias kept for
    backward compat.)
    """

    dc_id: str
    has_ingress: bool = False
    label: Optional[str] = ""


# Backward-compatible alias — older payloads / imports may still
# reference ``LegacyTierSpec``.
LegacyTierSpec = HeritageTierSpec


class SharedService(BaseModel):
    """Centralized shared service (MQ, Kafka, DB, AppD, Splunk, Redis, …)
    available as a rule destination AND a rule source (e.g. Splunk
    scraping app endpoints, Kerberos→LDAP).

    Group naming:
      egress  → grp-<service_id>-<NH>-<SZ>           (per (DC, env))
      ingress → grp-<service_id>-<NH>-<SZ>-Ingress   (when offered as
                  a destination — the historical default for Shared
                  Services and the only mode supported on PR #57.)
    """

    service_id: str  # slug, e.g. "KAFKA"
    name: str
    category: SharedServiceCategory = SharedServiceCategory.OTHER
    owner: Optional[str] = ""
    # Owning team — used by the per-team scoping rules. Defaults to the
    # SNS team so seed services without an explicit owner remain visible
    # to operators.
    owner_team: Optional[str] = "SNS"
    description: Optional[str] = ""
    icon: Optional[str] = ""   # optional emoji/symbol used by the DnD sidebar
    color: Optional[str] = ""  # optional CSS color hint for the DnD sidebar
    environments: list[Environment] = [Environment.PRODUCTION]
    tags: list[str] = []
    # Mandatory primary DC. The Rule Builder uses this DC's presence
    # exclusively when the service is the source/destination. Defaults to
    # ALPHA_NGDC during migration; new services must pick one.
    primary_dc: str = "ALPHA_NGDC"
    deployment_mode: DeploymentMode = DeploymentMode.ALL_NGDC
    excluded_dcs: list[str] = []
    # Tier definition shared across NGDC DCs. Replicated as one
    # SharedServicePresence per NGDC DC during auto-fan.
    tiers: list[TierSpec] = []
    # Heritage tiers — one per Heritage DC the service still serves
    # from. Each materialises into a SharedServicePresence with no
    # NH/SZ; the rule pipeline detects heritage presences and falls
    # back to the flat ``grp-<SVC>-HERITAGE-<DC>`` group +
    # ``HERITAGE-<DC>`` VRF convention. ``legacy_tiers`` accepted as
    # an alias for back-compat with older payloads.
    heritage_tiers: list[HeritageTierSpec] = Field(
        default_factory=list, alias="legacy_tiers"
    )

    model_config = {"populate_by_name": True}
    # Ports standard for this service — port_ids pointing into the global
    # Port Catalog. Surfaced as defaults in the rule builder's Port Picker
    # when this service is chosen as destination.
    standard_ports: list[str] = []
    # Service-specific customs that don't belong in the shared library
    # (e.g. Oracle with non-standard TLS listener on 2484).
    additional_ports: list[PortBinding] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ApplicationProfile(BaseModel):
    """Top-level Application metadata — the App Management record.

    Presences (per-(DC, NH, SZ)) live in `app_presences`; this profile
    captures the cross-DC defaults: primary DC, deployment mode, tier
    matrix, owning team. The portal auto-materializes presences from the
    tier matrix whenever `deployment_mode` is ALL_NGDC.
    """

    app_distributed_id: str
    app_id: Optional[str] = None
    name: Optional[str] = ""
    owner: Optional[str] = ""
    owner_team: Optional[str] = ""
    description: Optional[str] = ""
    criticality: Optional[str] = "Medium"
    pci_scope: bool = False
    components: list[str] = []
    # Mandatory primary DC. Rules raised by/for this app default to its
    # primary DC; the Rule Builder hides other DCs from the LDF.
    primary_dc: str = "ALPHA_NGDC"
    deployment_mode: DeploymentMode = DeploymentMode.ALL_NGDC
    excluded_dcs: list[str] = []
    tiers: list[TierSpec] = []
    # Heritage tiers — same model as SharedService.heritage_tiers.
    # Apps in transition between Heritage DCs and NGDC may carry both.
    # ``legacy_tiers`` accepted as an alias for back-compat.
    heritage_tiers: list[HeritageTierSpec] = Field(
        default_factory=list, alias="legacy_tiers"
    )

    model_config = {"populate_by_name": True}


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


class SourceEntityKind(str, Enum):
    """Source of a rule request. Apps remain the dominant case but
    Shared Services (e.g. Splunk → app APIs, Kerberos → LDAP) can also
    raise rules now."""

    APP = "app"
    SHARED_SERVICE = "shared_service"


class RuleRequestCreate(BaseModel):
    """Logical rule request submitted in Studio — fans out into per-DC
    PhysicalRule records.

    By default the engine emits ONE PhysicalRule per (src tier × dst tier)
    in the **source's primary DC** (egress side). Destination groups are
    resolved against the destination's primary DC; the destination team
    is responsible for east-west routing across their other DCs. Toggle
    `include_cross_dc=true` to override this and fan out across DCs (rare
    DR / active-active patterns).
    """

    # Source entity. Both `application_ref` and `source_ref` are accepted
    # for back-compat — `application_ref` is the legacy app id field.
    source_kind: SourceEntityKind = SourceEntityKind.APP
    source_ref: Optional[str] = None  # app_distributed_id OR service_id
    application_ref: Optional[str] = ""  # legacy alias for app sources
    destination_kind: DestinationEntityKind
    destination_ref: Optional[str] = None  # app_distributed_id OR service_id
    environment: Environment = Environment.PRODUCTION
    ports: str = "TCP 8080"
    action: Literal["ACCEPT", "DROP"] = "ACCEPT"
    description: str = ""
    src_members_override: list[MemberSpec] = []
    dst_members_override: list[MemberSpec] = []
    requested_dcs: Optional[list[str]] = None  # optional DC scoping
    # Optional per-presence scoping. Each entry identifies one (DC, NH, SZ)
    # presence. When non-empty, only those presences participate in the
    # fan-out — this lets the builder ask "which SZ for the source" when an
    # app is present in multiple NH/SZ combinations.
    source_presences: Optional[list[dict]] = None
    destination_presences: Optional[list[dict]] = None
    # Power-user toggle: when true, fan out across all DCs (cross-DC
    # rules). Default behaviour collapses to source's primary DC × dest's
    # primary DC.
    include_cross_dc: bool = False
    # Power-user override: explicitly target a destination DC (DR cutover
    # scenarios). When set, supersedes destination's primary_dc.
    destination_dc_override: Optional[str] = None
    owner: str = ""
    owner_team: Optional[str] = ""


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


class SZNamingMode(str, Enum):
    """Determines how source / destination groups are named for presences
    inside this Security Zone.

    - APP_SCOPED (default): a dedicated SZ where each app owns its own
      egress/ingress IPs. Group names embed the app distributed-id, e.g.
      `grp-AD-1003-NH06-CDE` — matches today's convention for
      CCS/CDE/PAA/CPA-style PCI/Critical zones.
    - ZONE_SCOPED: a shared cluster zone (STD, GEN, Shared, OpenShift,
      VMware tenant pools, …) where the *cluster CIDR* is the source for
      every app in the SZ. Group names drop the app token and become
      simply `grp-<NH>-<SZ>` (e.g. `grp-NH02-GEN`). This is critical for
      rule-existence validation — without it, every app generates a
      duplicate group with identical members and the dedup engine can't
      collapse rules properly.
    """

    APP_SCOPED = "app_scoped"
    ZONE_SCOPED = "zone_scoped"


class SecurityZone(BaseModel):
    name: str
    code: str
    description: str = ""
    # Defaults to APP_SCOPED. STD / GEN (and any explicit "Shared" zones
    # configured by SNS) flip to ZONE_SCOPED in the seed/migration so
    # group naming + dedup behave correctly.
    naming_mode: SZNamingMode = SZNamingMode.APP_SCOPED


# ---- Deployment Artifacts (post-approval exports) ----

class DeploymentArtifactKind(str, Enum):
    JSON_MANIFEST = "json_manifest"
    XLSX_MANIFEST = "xlsx_manifest"
    DEVICE_CONFIG_PAN_OS = "device_config_pan_os"
    DEVICE_CONFIG_FORTINET = "device_config_fortinet"
    DEVICE_CONFIG_CISCO = "device_config_cisco"
    DEVICE_CONFIG_CHECKPOINT = "device_config_checkpoint"


class DedupVerdict(str, Enum):
    """Outcome of pre-submit / migration rule-existence validation."""

    NEW = "new"                       # green — no overlap with existing rules
    IDENTICAL = "identical"           # red — exact match exists
    SUBSET = "subset"                 # red — covered by a broader rule
    OVERLAP = "overlap"               # amber — partial overlap; allow w/ warning
    CONFLICT = "conflict"             # red — same key but different action
    BIRTHRIGHT_COVERED = "birthright" # red — covered by a birthright/baseline rule


class DedupMatch(BaseModel):
    verdict: DedupVerdict
    matched_rule_id: Optional[str] = None
    matched_request_id: Optional[str] = None
    message: str = ""
    details: list[str] = []


# ---- ITSM Connector (ServiceNow / Generic REST) ----

class ITSMConnectorKind(str, Enum):
    SERVICENOW = "servicenow"
    JIRA = "jira"
    GENERIC_REST = "generic_rest"


class ITSMAuthMode(str, Enum):
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    VAULT = "vault"  # secret material is fetched from HashiCorp Vault path


class ITSMConnector(BaseModel):
    """Connector profile for posting approved rules to ServiceNow /
    internal CHG/CR systems."""

    connector_id: str
    name: str
    kind: ITSMConnectorKind = ITSMConnectorKind.GENERIC_REST
    enabled: bool = True
    environments: list[Environment] = [Environment.PRODUCTION]
    base_url: str = ""
    # ServiceNow Table API table name (e.g. "change_request"). For Jira
    # it's the project key. Generic REST ignores this if `submit_path`
    # is set.
    table: Optional[str] = "change_request"
    submit_path: Optional[str] = None        # POST path; falls back to
                                              # /api/now/table/<table> for SN
    status_path_template: Optional[str] = None  # e.g. "/api/now/table/change_request/{ticket_id}"
    auth_mode: ITSMAuthMode = ITSMAuthMode.API_KEY
    auth_secret_ref: Optional[str] = None    # env var or Vault path
    vault_path: Optional[str] = None          # populated when auth_mode = VAULT
    vault_field: Optional[str] = None
    payload_template: dict = {}              # static fields merged into POST body
    field_mapping: dict = {}                 # {"short_description": "$rule.title"} etc.
    status_field: str = "state"              # response JSON field that holds ticket status
    closed_states: list[str] = ["Closed", "Closed Complete", "Closed Successful", "Resolved"]
    rejected_states: list[str] = ["Cancelled", "Closed Incomplete", "Closed Rejected"]
    # Auto-submit RuleRequest to this connector when SNS approves it.
    auto_submit_on_approval: bool = False
    # Polling interval (seconds) for status sync. Phase A is manual via
    # /refresh-status; Phase B will run a background worker.
    poll_interval_seconds: int = 900
    notes: Optional[str] = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ExternalTicketRef(BaseModel):
    """Captured on a RuleRequest after it's submitted to an ITSM."""

    connector_id: str
    external_system: str               # e.g. "servicenow"
    ticket_id: str                     # e.g. "CHG0123456"
    ticket_url: Optional[str] = None
    raw_status: Optional[str] = None   # raw status string returned by tool
    mapped_status: Optional[str] = None  # "Submitted" | "In Progress" | "Closed" | "Rejected"
    submitted_at: Optional[str] = None
    last_synced_at: Optional[str] = None


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
