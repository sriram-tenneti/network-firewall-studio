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

// Firewall Rules
export const getRules = (application?: string, status?: string) => {
  const params = new URLSearchParams();
  if (application) params.set('application', application);
  if (status) params.set('status', status);
  const qs = params.toString();
  return fetchJSON<FirewallRule[]>(`/api/rules${qs ? `?${qs}` : ''}`);
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
  fetchJSON<{ rule: FirewallRule; chg: CHGRequest }>(`/api/rules/${ruleId}/submit`, { method: 'POST' });

export const getRuleHistory = (ruleId: string) =>
  fetchJSON<RuleHistoryEntry[]>(`/api/rules/${ruleId}/history`);

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
