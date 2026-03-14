export type RuleStatus = 'Draft' | 'Pending Review' | 'Approved' | 'Rejected' | 'Deployed' | 'Certified' | 'Expired' | 'Deleted';
export type PolicyResult = 'Permitted' | 'Blocked' | 'Exception Required' | 'Needs Review';
export type MigrationStatus = 'Auto-Mapped' | 'Needs Review' | 'New Group' | 'Conflict' | 'Blocked' | 'Draft' | 'Policy Review';
export type MappingStatus = 'Automapped' | 'Needs Review' | 'Blocked';
export type SourceType = 'Single IP' | 'Subnet' | 'Group';

export interface SourceConfig {
  source_type: SourceType;
  ip_address: string | null;
  cidr: string | null;
  group_name: string | null;
  ports: string;
  neighbourhood: string | null;
  neighbourhood_name?: string | null;
  security_zone: string | null;
}

export interface DestinationConfig {
  name: string;
  friendly_name?: string | null;
  security_zone: string | null;
  dest_ip: string | null;
  ports: string;
  is_predefined: boolean;
  dest_type?: string | null;
}

export interface RuleCompliance {
  naming_valid: boolean;
  naming_errors?: string[];
  group_to_group: boolean;
  requires_exception: boolean;
}

export interface FirewallRule {
  id: string;
  rule_id: string;
  application: string;
  application_name?: string;
  environment: string;
  datacenter: string;
  source: SourceConfig;
  destination: DestinationConfig;
  policy_result: PolicyResult;
  status: RuleStatus;
  compliance?: RuleCompliance;
  expiry: string | null;
  owner: string;
  created_at: string;
  updated_at: string;
  certified_at: string | null;
  certified_by: string | null;
}

export interface MigrationDetails {
  id: string;
  application: string;
  source_legacy_dc: string;
  target_ngdc: string;
  map_to_standard_groups: boolean;
  map_to_subnet_cidr: boolean;
  status: string;
  created_at: string;
}

export interface MigrationMapping {
  id: string;
  migration_id: string;
  legacy_source: string;
  legacy_source_detail: string | null;
  legacy_group: string | null;
  ngdc_target: string;
  ngdc_target_detail: string | null;
  mapping_status: MigrationStatus;
  trust_zones_automapped: number;
  related_policies: string[];
  naming_compliant?: boolean;
}

export interface MigrationRuleLifecycle {
  id: string;
  migration_id: string;
  rule_id: string;
  source: string;
  source_ip: string | null;
  mapping_status: string;
  ngdc_target: string;
  destination_detail: string | null;
  naming_compliant?: boolean;
}

export interface Neighbourhood {
  name: string;
  nh_id?: string;
  zone?: string;
  subnets: string[];
}

export interface IPRange {
  cidr: string;
  description: string;
  dc: string;
}

export interface NeighbourhoodRegistry {
  id?: string;
  nh_id: string;
  name: string;
  zone: string;
  environment: string;
  description?: string;
  ip_ranges?: IPRange[];
}

export interface NGDCDataCenter {
  name: string;
  code: string;
  neighbourhoods: Neighbourhood[];
  ip_groups: { name: string; entries: { name: string; ip?: string; cidr?: string }[] }[];
  rule_count: number;
}

export interface SecurityZone {
  name: string;
  code: string;
  description: string;
  risk_level?: string;
  pci_scope?: boolean;
  ip_ranges?: IPRange[];
}

export interface PredefinedDestination {
  name: string;
  security_zone: string;
  description: string | null;
  friendly_name?: string;
}

export interface Application {
  id?: string;
  name: string;
  app_id: string;
  app_distributed_id?: string;
  owner: string;
  nh: string;
  sz: string;
  criticality?: number;
  pci_scope?: boolean;
}

export interface OrgConfig {
  org_name: string;
  org_code: string;
  servicenow_instance: string;
  servicenow_api_path: string;
  gitops_repo: string;
  gitops_branch: string;
  approval_required: boolean;
  auto_certify_birthright: boolean;
  notification_email: string;
  notification_slack_channel: string;
  max_rule_expiry_days: number;
  enforce_group_to_group: boolean;
}

export interface PolicyMatrixEntry {
  source_zone: string;
  dest_zone: string;
  default_action: string;
  requires_exception: boolean;
  description: string;
}

export interface EnvironmentEntry {
  code: string;
  name: string;
  description: string;
}

export interface NamingStandardsInfo {
  prefixes: Record<string, { description: string; pattern: string; example: string }>;
  valid_nh_ids: string[];
  valid_sz_codes: string[];
  valid_subtypes: Record<string, string>;
  enforcement_rules: string[];
}

export interface PolicyValidationResult {
  result: PolicyResult;
  message: string;
  details: string[];
  ngdc_zone_check: boolean;
  birthright_compliant: boolean;
  naming_compliant?: boolean;
  group_to_group_compliant?: boolean;
}

export interface CHGRequest {
  id: string;
  chg_number: string;
  rule_ids: string[];
  migration_id: string | null;
  status: string;
  created_at: string;
  description: string;
}

export interface RuleHistoryEntry {
  id: string;
  rule_id: string;
  action: string;
  timestamp: string;
  user: string;
  details: string;
}

export interface GroupMember {
  type: 'ip' | 'cidr' | 'group' | 'range';
  value: string;
  description: string;
}

export interface FirewallGroup {
  name: string;
  app_id: string;
  nh: string;
  sz: string;
  subtype: string;
  description: string;
  members: GroupMember[];
  created_at?: string;
  updated_at?: string;
}

// Compiled firewall rule in deployable format
export interface CompiledRule {
  rule_id: string;
  vendor_format: 'generic' | 'palo_alto' | 'checkpoint' | 'cisco_asa';
  compiled_text: string;
  source_objects: string[];
  destination_objects: string[];
  services: string[];
  action: string;
  logging: boolean;
  comment: string;
}

// Review/Approval workflow
export interface ReviewRequest {
  id: string;
  rule_id: string;
  rule_name: string;
  request_type: 'new_rule' | 'modify_rule' | 'delete_rule' | 'migration' | 'certification';
  requestor: string;
  reviewer: string | null;
  status: 'Pending' | 'Approved' | 'Rejected' | 'Withdrawn';
  submitted_at: string;
  reviewed_at: string | null;
  comments: string;
  review_notes: string | null;
  rule_summary: {
    application: string;
    source: string;
    destination: string;
    ports: string;
    environment: string;
  };
}

// Legacy non-standard rule for migration
export interface LegacyRule {
  id: string;
  app_id: string;
  app_distributed_id: string;
  rule_name: string;
  inventory: string;
  policy_row: string;
  rule_status: string;
  rule_action: string;
  source_zone: string;
  source_entries: string[];
  source_expanded: string[];
  destination_entries: string[];
  destination_expanded: string[];
  ports: string[];
  is_standard: boolean;
  migration_status: 'Not Started' | 'In Progress' | 'Mapped' | 'Needs Review' | 'Completed';
  suggested_standard_name?: string;
}
