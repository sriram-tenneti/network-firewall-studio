export type RuleStatus = 'Draft' | 'Deployed' | 'Pending Review' | 'Certified' | 'Expired' | 'Deleted';
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

export interface NeighbourhoodRegistry {
  id: string;
  name: string;
  zone: string;
  environment: string;
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
}

export interface PredefinedDestination {
  name: string;
  security_zone: string;
  description: string | null;
  friendly_name?: string;
}

export interface Application {
  id: string;
  name: string;
  app_id: string;
  owner: string;
  nh: string;
  sz: string;
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
