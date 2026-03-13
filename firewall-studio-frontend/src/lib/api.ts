import type {
  FirewallRule,
  MigrationDetails,
  MigrationMapping,
  MigrationRuleLifecycle,
  NGDCDataCenter,
  SecurityZone,
  PredefinedDestination,
  PolicyValidationResult,
  CHGRequest,
  RuleHistoryEntry,
  SourceConfig,
  DestinationConfig,
  NeighbourhoodRegistry,
  Application,
  NamingStandardsInfo,
  FirewallGroup,
  GroupMember,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Transform flat backend rule data to structured frontend FirewallRule
interface RawBackendRule {
  rule_id: string;
  source: string;
  source_zone: string;
  destination: string;
  destination_zone: string;
  port: string;
  protocol: string;
  action: string;
  description: string;
  application: string;
  status: string;
  is_group_to_group: boolean;
  environment: string;
  datacenter: string;
  created_at: string;
  updated_at: string;
  certified_date: string | null;
  expiry_date: string | null;
}

function parseSourceConfig(src: string, srcZone: string, port: string): SourceConfig {
  const isGroup = src.startsWith('grp-');
  const isServer = src.startsWith('svr-');
  const isRange = src.startsWith('rng-');
  const isCidr = /\/\d+$/.test(src);

  if (isGroup || isServer || isRange) {
    return {
      source_type: 'Group',
      ip_address: null,
      cidr: null,
      group_name: src,
      ports: port,
      neighbourhood: null,
      security_zone: srcZone,
    };
  } else if (isCidr) {
    return {
      source_type: 'Subnet',
      ip_address: null,
      cidr: src,
      group_name: null,
      ports: port,
      neighbourhood: null,
      security_zone: srcZone,
    };
  } else {
    return {
      source_type: 'Single IP',
      ip_address: src,
      cidr: null,
      group_name: null,
      ports: port,
      neighbourhood: null,
      security_zone: srcZone,
    };
  }
}

function parseDestConfig(dst: string, dstZone: string, port: string): DestinationConfig {
  return {
    name: dst,
    security_zone: dstZone,
    dest_ip: /^\d/.test(dst) ? dst : null,
    ports: port,
    is_predefined: dst.startsWith('grp-'),
  };
}

function transformRule(raw: RawBackendRule): FirewallRule {
  const src = raw.source;
  const isNamingValid = src.startsWith('grp-') || src.startsWith('svr-') || src.startsWith('rng-');
  const dstNamingValid = raw.destination.startsWith('grp-') || raw.destination.startsWith('svr-') || raw.destination.startsWith('rng-');
  return {
    id: raw.rule_id,
    rule_id: raw.rule_id,
    application: raw.application,
    environment: raw.environment,
    datacenter: raw.datacenter,
    source: parseSourceConfig(raw.source, raw.source_zone, raw.port),
    destination: parseDestConfig(raw.destination, raw.destination_zone, raw.port),
    policy_result: 'Permitted',
    status: raw.status as FirewallRule['status'],
    compliance: {
      naming_valid: isNamingValid && dstNamingValid,
      group_to_group: raw.is_group_to_group,
      requires_exception: !raw.is_group_to_group,
    },
    expiry: raw.expiry_date,
    owner: 'System',
    created_at: raw.created_at,
    updated_at: raw.updated_at,
    certified_at: raw.certified_date,
    certified_by: raw.certified_date ? 'System' : null,
  };
}

// Firewall Rules
export const getRules = async (application?: string, status?: string): Promise<FirewallRule[]> => {
  const params = new URLSearchParams();
  if (application) params.set('application', application);
  if (status) params.set('status', status);
  const qs = params.toString();
  const rawRules = await fetchJSON<RawBackendRule[]>(`/api/rules${qs ? `?${qs}` : ''}`);
  return rawRules.map(transformRule);
};

export const getRule = (ruleId: string) => fetchJSON<FirewallRule>(`/api/rules/${ruleId}`);

export const createRule = (data: {
  application: string;
  environment: string;
  datacenter: string;
  source: SourceConfig;
  destination: DestinationConfig;
  owner: string;
}) =>
  fetchJSON<FirewallRule>('/api/rules', { method: 'POST', body: JSON.stringify(data) });

export const updateRule = (ruleId: string, data: Partial<{
  source: SourceConfig;
  destination: DestinationConfig;
  owner: string;
}>) =>
  fetchJSON<FirewallRule>(`/api/rules/${ruleId}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteRule = (ruleId: string) =>
  fetchJSON<{ message: string }>(`/api/rules/${ruleId}`, { method: 'DELETE' });

export const certifyRule = (ruleId: string, user = 'Jon') =>
  fetchJSON<FirewallRule>(`/api/rules/${ruleId}/certify?user=${user}`, { method: 'POST' });

export const submitRule = (ruleId: string) =>
  fetchJSON<Record<string, unknown>>(`/api/rules/${ruleId}/submit`, { method: 'POST' });

export const getRuleHistory = (ruleId: string) =>
  fetchJSON<RuleHistoryEntry[]>(`/api/rules/${ruleId}/history`);

export const saveDraft = (ruleId: string, data: { source: SourceConfig; destination: DestinationConfig }) =>
  fetchJSON<Record<string, unknown>>(`/api/rules/${ruleId}`, {
    method: 'PUT',
    body: JSON.stringify({
      source: data.source.group_name || data.source.cidr || data.source.ip_address || '',
      source_zone: data.source.security_zone || '',
      destination: data.destination.name || '',
      destination_zone: data.destination.security_zone || '',
      port: data.source.ports || data.destination.ports || '',
    }),
  });

// Migrations
export const getMigrations = () => fetchJSON<MigrationDetails[]>('/api/migrations');

export const getMigration = (id: string) => fetchJSON<MigrationDetails>(`/api/migrations/${id}`);

export const createMigration = (data: {
  application: string;
  source_legacy_dc: string;
  target_ngdc: string;
  map_to_standard_groups: boolean;
  map_to_subnet_cidr: boolean;
}) =>
  fetchJSON<MigrationDetails>('/api/migrations', { method: 'POST', body: JSON.stringify(data) });

export const getMigrationMappings = (id: string) =>
  fetchJSON<MigrationMapping[]>(`/api/migrations/${id}/mappings`);

export const getMigrationRuleLifecycle = (id: string) =>
  fetchJSON<MigrationRuleLifecycle[]>(`/api/migrations/${id}/rule-lifecycle`);

export const validateMigration = (id: string) =>
  fetchJSON<{ validation_passed: boolean; message: string; auto_mapped: number; conflicts: number }>(`/api/migrations/${id}/validate`, { method: 'POST' });

export const submitMigration = (id: string) =>
  fetchJSON<{ migration: MigrationDetails; chg: CHGRequest }>(`/api/migrations/${id}/submit`, { method: 'POST' });

// Reference Data
export const getNGDCDatacenters = () => fetchJSON<NGDCDataCenter[]>('/api/reference/ngdc-datacenters');
export const getSecurityZones = () => fetchJSON<SecurityZone[]>('/api/reference/security-zones');
export const getPredefinedDestinations = () => fetchJSON<PredefinedDestination[]>('/api/reference/predefined-destinations');
export const getNeighbourhoods = () => fetchJSON<NeighbourhoodRegistry[]>('/api/reference/neighbourhoods');
export const getLegacyDatacenters = () => fetchJSON<{ name: string; code: string }[]>('/api/reference/legacy-datacenters');
export const getApplications = () => fetchJSON<Application[]>('/api/reference/applications');
export const getEnvironments = () => fetchJSON<string[]>('/api/reference/environments');
export const getCHGRequests = () => fetchJSON<CHGRequest[]>('/api/reference/chg-requests');

// Naming Standards
export const getNamingStandards = () => fetchJSON<NamingStandardsInfo>('/api/reference/naming-standards');

export const validateNaming = (name: string) =>
  fetchJSON<{ valid: boolean; error?: string; parsed?: Record<string, string> }>(
    '/api/reference/naming-standards/validate',
    { method: 'POST', body: JSON.stringify({ name }) }
  );

export const generateName = (data: {
  type: 'group' | 'server' | 'subnet';
  app_id: string;
  nh: string;
  sz: string;
  subtype?: string;
  server_name?: string;
  descriptor?: string;
}) =>
  fetchJSON<{ name: string }>(
    '/api/reference/naming-standards/generate',
    { method: 'POST', body: JSON.stringify(data) }
  );

export const suggestStandardName = (legacy_name: string, app_id: string, nh: string, sz: string) =>
  fetchJSON<{ suggested_name: string; confidence: string }>(
    '/api/reference/naming-standards/suggest',
    { method: 'POST', body: JSON.stringify({ legacy_name, app_id, nh, sz }) }
  );

export const determineSecurityZone = (data: {
  paa_zone: boolean;
  exposure: string;
  pci_pan: boolean;
  pci_track_data: boolean;
  pci_cvv_pin: boolean;
  deployment_type: string;
  critical_payment: boolean;
  data_classification: string;
  criticality_rating: number;
  environment: string;
}) =>
  fetchJSON<{ zone: string; zone_name: string; reasoning: string[] }>(
    '/api/reference/naming-standards/determine-zone',
    { method: 'POST', body: JSON.stringify(data) }
  );

// Policy Validation
export const validatePolicy = (data: {
  source: SourceConfig;
  destination: DestinationConfig;
  application: string;
  environment: string;
}) =>
  fetchJSON<PolicyValidationResult>('/api/policy/validate', { method: 'POST', body: JSON.stringify(data) });

// Org Config
export const getOrgConfig = () => fetchJSON<Record<string, unknown>>('/api/reference/org-config');
export const updateOrgConfig = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/org-config', { method: 'PUT', body: JSON.stringify(data) });

// Policy Matrix
export const getPolicyMatrix = () => fetchJSON<Record<string, unknown>[]>('/api/reference/policy-matrix');
export const createPolicyEntry = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/policy-matrix', { method: 'POST', body: JSON.stringify(data) });
export const deletePolicyEntry = (sourceZone: string, destZone: string) =>
  fetchJSON<{ message: string }>(`/api/reference/policy-matrix/${sourceZone}/${destZone}`, { method: 'DELETE' });

// CRUD: Neighbourhoods
export const createNeighbourhood = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/neighbourhoods', { method: 'POST', body: JSON.stringify(data) });
export const updateNeighbourhood = (nhId: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/neighbourhoods/${nhId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteNeighbourhood = (nhId: string) =>
  fetchJSON<{ message: string }>(`/api/reference/neighbourhoods/${nhId}`, { method: 'DELETE' });

// CRUD: Security Zones
export const createSecurityZone = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/security-zones', { method: 'POST', body: JSON.stringify(data) });
export const updateSecurityZone = (code: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/security-zones/${code}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteSecurityZone = (code: string) =>
  fetchJSON<{ message: string }>(`/api/reference/security-zones/${code}`, { method: 'DELETE' });

// CRUD: Applications
export const createApplication = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/applications', { method: 'POST', body: JSON.stringify(data) });
export const updateApplication = (appId: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/applications/${appId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteApplication = (appId: string) =>
  fetchJSON<{ message: string }>(`/api/reference/applications/${appId}`, { method: 'DELETE' });

// CRUD: Datacenters
export const createNGDCDatacenter = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/ngdc-datacenters', { method: 'POST', body: JSON.stringify(data) });
export const updateNGDCDatacenter = (code: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/ngdc-datacenters/${code}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteNGDCDatacenter = (code: string) =>
  fetchJSON<{ message: string }>(`/api/reference/ngdc-datacenters/${code}`, { method: 'DELETE' });

export const createLegacyDatacenter = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/legacy-datacenters', { method: 'POST', body: JSON.stringify(data) });
export const updateLegacyDatacenter = (code: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/legacy-datacenters/${code}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteLegacyDatacenter = (code: string) =>
  fetchJSON<{ message: string }>(`/api/reference/legacy-datacenters/${code}`, { method: 'DELETE' });

// CRUD: Predefined Destinations
export const createPredefinedDestination = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/predefined-destinations', { method: 'POST', body: JSON.stringify(data) });
export const updatePredefinedDestination = (name: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/predefined-destinations/${name}`, { method: 'PUT', body: JSON.stringify(data) });
export const deletePredefinedDestination = (name: string) =>
  fetchJSON<{ message: string }>(`/api/reference/predefined-destinations/${name}`, { method: 'DELETE' });

// CRUD: Environments
export const createEnvironment = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/environments', { method: 'POST', body: JSON.stringify(data) });
export const deleteEnvironment = (code: string) =>
  fetchJSON<{ message: string }>(`/api/reference/environments/${code}`, { method: 'DELETE' });

// Naming Standards CRUD
export const updateNamingStandards = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/naming-standards', { method: 'PUT', body: JSON.stringify(data) });

// Groups CRUD
export const getGroups = (appId?: string) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  return fetchJSON<FirewallGroup[]>(`/api/reference/groups${qs ? `?${qs}` : ''}`);
};
export const getGroup = (name: string) => fetchJSON<FirewallGroup>(`/api/reference/groups/${name}`);
export const createGroup = (data: Record<string, unknown>) =>
  fetchJSON<FirewallGroup>('/api/reference/groups', { method: 'POST', body: JSON.stringify(data) });
export const updateGroup = (name: string, data: Record<string, unknown>) =>
  fetchJSON<FirewallGroup>(`/api/reference/groups/${name}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteGroup = (name: string) =>
  fetchJSON<{ message: string }>(`/api/reference/groups/${name}`, { method: 'DELETE' });
export const addGroupMember = (groupName: string, member: GroupMember) =>
  fetchJSON<FirewallGroup>(`/api/reference/groups/${groupName}/members`, { method: 'POST', body: JSON.stringify(member) });
export const removeGroupMember = (groupName: string, memberValue: string) =>
  fetchJSON<FirewallGroup>(`/api/reference/groups/${groupName}/members/${memberValue}`, { method: 'DELETE' });
