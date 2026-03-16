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
  modification_id?: string;
  delta?: RuleDelta;
  rule_summary: {
    application: string;
    source: string;
    destination: string;
    ports: string;
    environment: string;
  };
}

export interface RuleDelta {
  added: Record<string, string[]>;
  removed: Record<string, string[]>;
  changed: Record<string, { from: string; to: string }>;
}

export interface RuleModification {
  id: string;
  rule_id: string;
  original: Record<string, string>;
  modified: Record<string, string>;
  delta: RuleDelta;
  comments: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  created_at: string;
  reviewed_at: string | null;
  reviewer: string | null;
  review_notes: string | null;
}

export interface NGDCRecommendation {
  rule_id: string;
  rule: LegacyRule;
  recommended_nh: string;
  recommended_nh_name: string;
  recommended_sz: string;
  recommended_sz_name: string;
  source_mappings: IPMapping[];
  destination_mappings: IPMapping[];
  service_entries: string[];
  naming_standard: string;
  available_nhs: { nh_id: string; name: string }[];
  available_szs: { code: string; name: string }[];
}

export interface IPMapping {
  legacy: string;
  ngdc_recommended: string;
  type: 'group' | 'server' | 'range' | 'other';
  existing_group: string | null;
  customizable: boolean;
}

export interface BirthrightValidation {
  compliant: boolean;
  violations: BirthrightEntry[];
  warnings: BirthrightEntry[];
  permitted: BirthrightEntry[];
  summary: string;
}

export interface BirthrightEntry {
  matrix: string;
  rule: string;
  action: string;
  reason: string;
}

export interface LegacyRule {
  id: string;
  app_id: number | string;
  app_distributed_id: string;
  app_name: string;
  inventory_item: string;
  policy_name: string;
  rule_global: boolean;
  rule_action: string;
  rule_source: string;
  rule_source_expanded: string;
  rule_source_zone: string;
  rule_destination: string;
  rule_destination_expanded: string;
  rule_destination_zone: string;
  rule_service: string;
  rule_service_expanded: string;
  rn: number;
  rc: number;
  is_standard: boolean;
  migration_status: 'Not Started' | 'In Progress' | 'Mapped' | 'Needs Review' | 'Completed';
  migrated_at?: string;
}

export interface MigrationHistoryEntry {
  id: string;
  rule_id: string;
  action: string;
  from_status: string;
  to_status: string;
  details: string;
  timestamp: string;
  user: string;
}

// AD User Integration
export interface ADUserGroup {
  id: string;
  group_name: string;
  access_type: 'Admin' | 'Approver' | 'Operator' | 'Viewer' | 'Auditor';
  description: string;
  member_count: number;
  applications: string[];
}

export interface ADUser {
  id: string;
  username: string;
  display_name: string;
  email: string;
  groups: string[];
  access_type: string;
  last_login: string | null;
  is_active: boolean;
}

export interface ADConfig {
  server_url: string;
  base_dn: string;
  bind_user: string;
  search_filter: string;
  group_mapping: Record<string, string>;
  sync_interval_minutes: number;
  is_connected: boolean;
  last_sync: string | null;
}

// Data Source Import
export interface DataImportJob {
  id: string;
  source_type: 'json' | 'csv' | 'xlsx' | 'mongodb';
  source_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_records: number;
  imported_records: number;
  failed_records: number;
  target: 'legacy_rules' | 'firewall_rules' | 'groups';
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

// Firewall Management (as-is rules)
export interface AsIsRule {
  id: string;
  app_id: string;
  app_name: string;
  rule_name: string;
  source: string;
  source_zone: string;
  destination: string;
  destination_zone: string;
  port: string;
  protocol: string;
  action: string;
  is_standard: boolean;
  compliance_status: 'Compliant' | 'Non-Compliant' | 'Pending Review';
  last_reviewed: string | null;
  request_type: 'existing' | 'new' | 'modification';
  output_generated: boolean;
}

// Exception request for individual IPs/subnets
export interface ExceptionRequest {
  id: string;
  rule_id: string;
  exception_type: 'ip' | 'subnet';
  value: string;
  justification: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  requested_by: string;
  requested_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}
