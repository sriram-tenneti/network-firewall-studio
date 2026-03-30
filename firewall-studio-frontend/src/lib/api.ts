import type {
  FirewallRule,
  LegacyRule,
  CompiledRule,
  ReviewRequest,
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
  MigrationHistoryEntry,
  RuleModification,
  NGDCRecommendation,
  BirthrightValidation,
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

export function transformRule(raw: RawBackendRule): FirewallRule {
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const createRule = (data: Record<string, any>) =>
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

// Legacy Rules (for Migration Studio & Firewall Management)
export const getLegacyRules = (appId?: string, excludeMigrated?: boolean, environment?: string, migrationOnly?: boolean) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  if (excludeMigrated) params.set('exclude_migrated', 'true');
  if (environment) params.set('environment', environment);
  if (migrationOnly) params.set('migration_only', 'true');
  const qs = params.toString();
  return fetchJSON<LegacyRule[]>(`/api/reference/legacy-rules${qs ? `?${qs}` : ''}`);
};
export const getLegacyRule = (ruleId: string) =>
  fetchJSON<LegacyRule>(`/api/reference/legacy-rules/${ruleId}`);
export const updateLegacyRule = (ruleId: string, data: Partial<LegacyRule>) =>
  fetchJSON<LegacyRule>(`/api/reference/legacy-rules/${ruleId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteLegacyRule = (ruleId: string) =>
  fetchJSON<{ message: string }>(`/api/reference/legacy-rules/${ruleId}`, { method: 'DELETE' });

export const clearAllLegacyRules = () =>
  fetchJSON<{ message: string; deleted: number }>('/api/reference/legacy-rules/clear-all', { method: 'DELETE' });

// JSON import for legacy rules
export const importLegacyRulesJSON = async (file: File): Promise<{ added: number; duplicates: number; total: number }> => {
  const formData = new FormData();
  formData.append('file', file);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300000);
  try {
    const res = await fetch(`${API_BASE}/api/reference/legacy-rules/import-json`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => null);
      throw new Error(errBody?.detail || `Import failed: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
};

// Export legacy rules as Excel (.xlsx)
export const exportLegacyRulesToExcel = (appId?: string) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  window.open(`${API_BASE}/api/reference/legacy-rules/export-excel${qs ? `?${qs}` : ''}`, '_blank');
};

// Excel import for legacy rules (supports large files up to 50K+ rows)
export const importLegacyRulesExcel = async (file: File, environment?: string): Promise<Record<string, unknown>> => {
  const formData = new FormData();
  formData.append('file', file);
  if (environment) formData.append('environment', environment);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300000); // 5 min timeout for large files
  try {
    const res = await fetch(`${API_BASE}/api/reference/legacy-rules/import`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => null);
      throw new Error(errBody?.detail || `Import failed: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
};

// Migration operations
export const migrateRulesToNGDC = (ruleIds: string[]) =>
  fetchJSON<{ migrated: number; rules: LegacyRule[] }>('/api/reference/legacy-rules/migrate', { method: 'POST', body: JSON.stringify({ rule_ids: ruleIds }) });
export const submitLegacyRulesForReview = (ruleIds: string[], comments?: string) =>
  fetchJSON<{ submitted: number; reviews: ReviewRequest[] }>('/api/reference/legacy-rules/submit-for-review', { method: 'POST', body: JSON.stringify({ rule_ids: ruleIds, comments }) });
export const getMigratedRules = () =>
  fetchJSON<LegacyRule[]>('/api/reference/legacy-rules/migrated');
export const getMigrationHistory = () =>
  fetchJSON<MigrationHistoryEntry[]>('/api/reference/migration-history');

// Rule Compiler
export const compileRule = (ruleId: string, vendor: string = 'generic') =>
  fetchJSON<CompiledRule>(`/api/rules/${ruleId}/compile?vendor=${vendor}`, { method: 'POST' });

// Legacy Rule Compiler
export const compileLegacyRule = (ruleId: string, vendor: string = 'generic') =>
  fetchJSON<CompiledRule>(`/api/reference/legacy-rules/${ruleId}/compile?vendor=${vendor}`, { method: 'POST' });

// Rule Modification with Delta Tracking
export const createRuleModification = (ruleId: string, modifications: Record<string, string>, comments: string = '') =>
  fetchJSON<RuleModification>(`/api/reference/legacy-rules/${ruleId}/modify`, {
    method: 'POST', body: JSON.stringify({ modifications, comments })
  });

export const getRuleModifications = (ruleId?: string) => {
  const params = new URLSearchParams();
  if (ruleId) params.set('rule_id', ruleId);
  const qs = params.toString();
  return fetchJSON<RuleModification[]>(`/api/reference/rule-modifications${qs ? `?${qs}` : ''}`);
};

export const approveRuleModification = (modId: string, notes: string = '') =>
  fetchJSON<RuleModification>(`/api/reference/rule-modifications/${modId}/approve`, {
    method: 'POST', body: JSON.stringify({ notes })
  });

export const rejectRuleModification = (modId: string, notes: string) =>
  fetchJSON<RuleModification>(`/api/reference/rule-modifications/${modId}/reject`, {
    method: 'POST', body: JSON.stringify({ notes })
  });

// NGDC Recommendations
export const getNGDCRecommendations = (ruleId: string) =>
  fetchJSON<NGDCRecommendation>(`/api/reference/legacy-rules/${ruleId}/ngdc-recommendations`);

// Birthright Validation
export const validateBirthright = (data: Record<string, unknown>) =>
  fetchJSON<BirthrightValidation>('/api/reference/birthright/validate', {
    method: 'POST', body: JSON.stringify(data)
  });

export const getBirthrightMatrix = () =>
  fetchJSON<Record<string, unknown[]>>('/api/reference/birthright/matrix');

export const updateBirthrightMatrix = (matrixType: string, entries: unknown[]) =>
  fetchJSON<unknown[]>(`/api/reference/birthright/matrix/${matrixType}`, {
    method: 'PUT', body: JSON.stringify({ entries })
  });

export const addBirthrightEntry = (matrixType: string, entry: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/birthright/matrix/${matrixType}`, {
    method: 'POST', body: JSON.stringify(entry)
  });

// Review & Approval
export const getReviewRequests = (status?: string) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  const qs = params.toString();
  return fetchJSON<ReviewRequest[]>(`/api/reviews${qs ? `?${qs}` : ''}`);
};
export const submitForReview = (ruleId: string, comments: string = '', module: string = 'design-studio') =>
  fetchJSON<ReviewRequest>('/api/reviews', { method: 'POST', body: JSON.stringify({ rule_id: ruleId, comments, module }) });
export const approveReview = (reviewId: string, notes: string = '') =>
  fetchJSON<ReviewRequest>(`/api/reviews/${reviewId}/approve`, { method: 'POST', body: JSON.stringify({ notes }) });
export const rejectReview = (reviewId: string, notes: string) =>
  fetchJSON<ReviewRequest>(`/api/reviews/${reviewId}/reject`, { method: 'POST', body: JSON.stringify({ notes }) });

// Rule Lifecycle
export const transitionRuleStatus = (ruleId: string, newStatus: string, module: string = 'studio', reviewer: string = 'system') =>
  fetchJSON<FirewallRule>(`/api/rules/${ruleId}/lifecycle-transition`, {
    method: 'POST', body: JSON.stringify({ new_status: newStatus, module, reviewer })
  });
export const getValidTransitions = (ruleId: string) =>
  fetchJSON<{ rule_id: string; current_status: string; valid_transitions: string[] }>(`/api/rules/${ruleId}/valid-transitions`);
export const getLifecycleSummary = () =>
  fetchJSON<Record<string, unknown>>('/api/rules/lifecycle/summary');

// NGDC Organization Mappings
export const getNGDCMappings = () => fetchJSON<Record<string, unknown>[]>('/api/reference/ngdc-mappings');
export const createNGDCMapping = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/ngdc-mappings', { method: 'POST', body: JSON.stringify(data) });
export const updateNGDCMapping = (id: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/ngdc-mappings/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteNGDCMapping = (id: string) =>
  fetchJSON<{ message: string }>(`/api/reference/ngdc-mappings/${id}`, { method: 'DELETE' });
export const importNGDCMappingsExcel = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/reference/ngdc-mappings/import`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};
export const bulkSaveNGDCMappings = (mappings: Record<string, unknown>[]) =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/ngdc-mappings/bulk', { method: 'POST', body: JSON.stringify({ mappings }) });

// Group Provisioning to Firewall Device
export const provisionGroups = (appId: string, deviceType = 'palo_alto') =>
  fetchJSON<Record<string, unknown>>(`/api/reference/groups/provision/${appId}`, { method: 'POST', body: JSON.stringify({ device_type: deviceType }) });
export const getProvisioningHistory = (appId?: string) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  return fetchJSON<Record<string, unknown>[]>(`/api/reference/provisioning-history${qs ? `?${qs}` : ''}`);
};

// Enhanced Compile with Group Expansion
export const compileRuleExpanded = (ruleId: string, vendor = 'generic', expandGroups = true) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/rules/${ruleId}/compile-expanded`, {
    method: 'POST', body: JSON.stringify({ vendor, expand_groups: expandGroups })
  });

// Data Mode (Seed vs Live)
export const getDataMode = () => fetchJSON<{ mode: string }>('/api/reference/data-mode');
export const setDataMode = (mode: string) =>
  fetchJSON<{ mode: string }>('/api/reference/data-mode', { method: 'POST', body: JSON.stringify({ mode }) });
export const resetSeedData = () =>
  fetchJSON<{ message: string; current_mode: string }>('/api/reference/data-mode/reset-seed', { method: 'POST' });

// Auto-populate NH/SZ/DC filtered by environment + app
export const getFilteredNhSzDc = (environment: string, appId?: string) => {
  const params = new URLSearchParams({ environment });
  if (appId) params.append('app_id', appId);
  return fetchJSON<{
    neighbourhoods: NeighbourhoodRegistry[];
    security_zones: SecurityZone[];
    datacenters: NGDCDataCenter[];
  }>(`/api/reference/filtered-nh-sz-dc?${params}`);
};

// Clear all imported app data
export const clearAppManagement = () =>
  fetchJSON<{ message: string }>('/api/reference/applications/clear', { method: 'POST' });

// App Management delta-based import
export const importAppManagement = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/reference/applications/import`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<{ added: number; updated: number; skipped: number; total: number; overrides: { app_distributed_id: string; app_id: string }[] }>;
};

// Imported Apps from Legacy Rules (with mapping status)
export const getImportedApps = () =>
  fetchJSON<{ app_id: string; app_name: string; app_distributed_id: string; rule_count: number; has_mapping: boolean; components: Record<string, unknown>[] }[]>(
    '/api/reference/legacy-rules/imported-apps'
  );

// App-to-DC/NH/SZ Organization Mappings
export const getAppDCMappings = () => fetchJSON<Record<string, unknown>[]>('/api/reference/app-dc-mappings');
export const getAppDCMapping = (appId: string) => fetchJSON<Record<string, unknown>>(`/api/reference/app-dc-mappings/${appId}`);
export const createAppDCMapping = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/app-dc-mappings', { method: 'POST', body: JSON.stringify(data) });
export const updateAppDCMapping = (id: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/app-dc-mappings/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteAppDCMapping = (id: string) =>
  fetchJSON<{ message: string }>(`/api/reference/app-dc-mappings/${id}`, { method: 'DELETE' });
export const importAppDCMappingsExcel = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/reference/app-dc-mappings/import`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};

// NGDC Compliance Check
export const checkNGDCCompliance = (ruleIds: string[]) =>
  fetchJSON<{ compliant: boolean; issues: string[]; rule_id: string }[]>(
    '/api/reference/legacy-rules/check-compliance',
    { method: 'POST', body: JSON.stringify({ rule_ids: ruleIds }) }
  );

// Duplicate Detection
export const checkDuplicates = (source: string, destination: string, service: string, excludeId = '') =>
  fetchJSON<{ duplicates: { id: string; type: string; app_id: string; source: string; destination: string; service: string }[]; count: number }>(
    '/api/reference/check-duplicates',
    { method: 'POST', body: JSON.stringify({ source, destination, service, exclude_id: excludeId }) }
  );

// Import Rules to NGDC Standardization from Network Firewall Request
export const importRulesToNGDC = (appIds: string[], environment?: string) =>
  fetchJSON<{ imported: number; rules: LegacyRule[] }>(
    '/api/reference/legacy-rules/import-to-ngdc',
    { method: 'POST', body: JSON.stringify({ app_ids: appIds, environment }) }
  );

// Auto-Import Compliant Rules to Firewall Studio
export const autoImportCompliantToStudio = () =>
  fetchJSON<{ imported: number; skipped_non_compliant: number; already_imported: number; total_studio_rules: number }>(
    '/api/reference/legacy-rules/auto-import-to-studio',
    { method: 'POST' }
  );

// Get Expanded Rule (groups expanded to IPs/ranges)
export const getExpandedRule = (ruleId: string) =>
  fetchJSON<LegacyRule>(`/api/reference/legacy-rules/${ruleId}/expanded`);

// Create Migration Group
export const createMigrationGroup = (data: { name: string; app_id: string; members: { type: string; value: string }[]; nh?: string; sz?: string }) =>
  fetchJSON<Record<string, unknown>>('/api/reference/migration-groups', { method: 'POST', body: JSON.stringify(data) });

// IP Mappings (Legacy DC <-> NGDC one-to-one)
export const getIPMappings = (legacyDc?: string, appId?: string) => {
  const params = new URLSearchParams();
  if (legacyDc) params.set('legacy_dc', legacyDc);
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  return fetchJSON<Record<string, unknown>[]>(`/api/reference/ip-mappings${qs ? `?${qs}` : ''}`);
};
export const createIPMapping = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/ip-mappings', { method: 'POST', body: JSON.stringify(data) });
export const updateIPMapping = (id: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/ip-mappings/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteIPMapping = (id: string) =>
  fetchJSON<{ message: string }>(`/api/reference/ip-mappings/${id}`, { method: 'DELETE' });
export const lookupIPMapping = (legacyIp: string, legacyDc?: string) =>
  fetchJSON<{ found: boolean; mapping?: Record<string, unknown>; message?: string }>(
    '/api/reference/ip-mappings/lookup',
    { method: 'POST', body: JSON.stringify({ legacy_ip: legacyIp, legacy_dc: legacyDc || '' }) }
  );

// Firewall Boundary Analysis
export const getFirewallBoundaries = (srcNh: string, srcSz: string, dstNh: string, dstSz: string) => {
  const sp = new URLSearchParams({ src_nh: srcNh, src_sz: srcSz, dst_nh: dstNh, dst_sz: dstSz });
  return fetchJSON<{
    boundaries: number; flow_rule: string; note: string;
    requires_egress: boolean; requires_ingress: boolean;
    devices: { role: string; direction: string; device_id: string; device_name: string; nh: string; sz: string }[];
  }>(`/api/reference/firewall-boundaries?${sp.toString()}`);
};

export const getLogicalFlowRules = () =>
  fetchJSON<{ rules: Record<string, unknown>[]; segmented_zones: string[] }>('/api/reference/logical-flow-rules');

// Egress/Ingress Compilation (with boundary analysis)
export const compileEgressIngress = (ruleId: string, vendor = 'generic') =>
  fetchJSON<Record<string, unknown>>(`/api/reference/compile/egress-ingress/${ruleId}?vendor=${vendor}`, { method: 'POST' });

// Resolved Policy Matrix
export const getResolvedPolicyMatrix = (params?: {
  src_dc?: string; src_nh?: string; src_sz?: string;
  dst_dc?: string; dst_nh?: string; dst_sz?: string;
  environment?: string;
}) => {
  const sp = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => { if (v) sp.set(k, v); });
  }
  const qs = sp.toString();
  return fetchJSON<Record<string, unknown>[]>(`/api/reference/policy-matrix/resolved${qs ? `?${qs}` : ''}`);
};

// Pre-Prod Policy Matrix
export const getPreprodMatrix = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/policy-matrix/preprod');

// All Policy Matrices (heritage, ngdc_prod, nonprod, combined)
export const getAllPolicyMatrices = () =>
  fetchJSON<{ heritage_dc: Record<string, unknown>[]; ngdc_prod: Record<string, unknown>[]; nonprod: Record<string, unknown>[]; combined: Record<string, unknown>[] }>('/api/reference/policy-matrix/all');

// App Environment Assignments
export const getAppEnvAssignments = (appId?: string) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  return fetchJSON<Record<string, unknown>[]>(`/api/reference/app-env-assignments${qs ? `?${qs}` : ''}`);
};
export const updateAppEnvAssignment = (appId: string, environment: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/app-env-assignments/${appId}/${environment}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteAppEnvAssignment = (appId: string, environment: string) =>
  fetchJSON<{ message: string }>(`/api/reference/app-env-assignments/${appId}/${environment}`, { method: 'DELETE' });

// Firewall Device Patterns (generic naming patterns + DC vendor map)
export const getFirewallDevicePatterns = () =>
  fetchJSON<{ patterns: Record<string, unknown>[]; dc_vendor_map: Record<string, Record<string, string>> }>('/api/reference/firewall-device-patterns');

// Firewall Devices
export const getFirewallDevices = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/firewall-devices');
export const getFirewallDevice = (deviceId: string) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/firewall-devices/${deviceId}`);
export const createFirewallDevice = (data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>('/api/reference/firewall-devices', { method: 'POST', body: JSON.stringify(data) });
export const updateFirewallDevice = (deviceId: string, data: Record<string, unknown>) =>
  fetchJSON<Record<string, unknown>>(`/api/reference/firewall-devices/${deviceId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteFirewallDevice = (deviceId: string) =>
  fetchJSON<{ message: string }>(`/api/reference/firewall-devices/${deviceId}`, { method: 'DELETE' });

// IP Mappings Import
export const importIPMappings = (mappings: Record<string, unknown>[], appId?: string) =>
  fetchJSON<{ added: number; total: number }>('/api/reference/ip-mappings/import', {
    method: 'POST', body: JSON.stringify({ mappings, app_id: appId }),
  });

// Bulk Save App-DC Mappings
export const bulkSaveAppDCMappings = (mappings: Record<string, unknown>[]) =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/app-dc-mappings/bulk', {
    method: 'POST', body: JSON.stringify({ mappings }),
  });

// Standalone JSON Seed Export
export const exportSeedJSON = () =>
  fetchJSON<{
    neighbourhoods: Record<string, unknown>[];
    security_zones: Record<string, unknown>[];
    datacenters: Record<string, unknown>[];
    policy_matrix: { production: Record<string, unknown>[]; non_production: Record<string, unknown>[]; pre_production: Record<string, unknown>[] };
    app_dc_mappings: Record<string, unknown>[];
    applications: Record<string, unknown>[];
    firewall_devices: Record<string, unknown>[];
  }>('/api/reference/export/seed-json');

// NGDC Prod Matrix
export const getNgdcProdMatrix = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/policy-matrix/ngdc-prod');

// NonProd Matrix
export const getNonprodMatrix = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/policy-matrix/nonprod');

// ---- Separate JSON Storage (user-data/) — Migration Data & Studio Rules ----

export const getUserDataSummary = () =>
  fetchJSON<{ migration_data: Record<string, number>; studio_rules_count: number; data_directory: string }>('/api/reference/user-data/summary');

export const getMigrationData = () =>
  fetchJSON<{ migration_history: Record<string, unknown>[]; migration_mappings: Record<string, unknown>[]; migration_reviews: Record<string, unknown>[]; migrated_rules: Record<string, unknown>[] }>('/api/reference/user-data/migration');

export const clearMigrationData = () =>
  fetchJSON<{ status: string; cleared_counts: Record<string, number> }>('/api/reference/user-data/migration', { method: 'DELETE' });

export const getStudioRules = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/user-data/studio-rules');

export const clearStudioRules = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/studio-rules', { method: 'DELETE' });

export const deleteStudioRule = (ruleId: string) =>
  fetchJSON<{ status: string; rule_id: string }>(`/api/reference/user-data/studio-rules/${ruleId}`, { method: 'DELETE' });

// ---- Cleanup Endpoints (individual + one-click reset) ----

export const clearAllUserData = () =>
  fetchJSON<{ status: string; counts: Record<string, number> }>('/api/reference/user-data/all', { method: 'DELETE' });

export const clearReviews = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/reviews', { method: 'DELETE' });

export const clearGroups = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/groups', { method: 'DELETE' });

export const clearFirewallRules = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/firewall-rules', { method: 'DELETE' });

export const clearModifications = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/modifications', { method: 'DELETE' });

export const clearLegacyRulesForce = () =>
  fetchJSON<{ status: string; count: number }>('/api/reference/user-data/legacy-rules', { method: 'DELETE' });

export const clearDataByApp = (appId: string) =>
  fetchJSON<{ status: string; app_id: string; counts: Record<string, number> }>(`/api/reference/user-data/by-app/${encodeURIComponent(appId)}`, { method: 'DELETE' });

export const clearDataByEnv = (environment: string) =>
  fetchJSON<{ status: string; environment: string; counts: Record<string, number> }>(`/api/reference/user-data/by-env/${encodeURIComponent(environment)}`, { method: 'DELETE' });

export const getDataSummaryByApp = () =>
  fetchJSON<{ app_id: string; legacy: number; firewall: number; reviews: number; studio: number; total: number }[]>('/api/reference/user-data/summary/by-app');

export const getDataSummaryByEnv = () =>
  fetchJSON<{ environment: string; legacy: number; firewall: number; reviews: number; studio: number; total: number }[]>('/api/reference/user-data/summary/by-env');

// ---- Hide Seed Data Toggle ----

export const getHideSeed = () =>
  fetchJSON<{ hide_seed: boolean }>('/api/reference/hide-seed');

export const setHideSeed = (hide: boolean) =>
  fetchJSON<{ hide_seed: boolean }>('/api/reference/hide-seed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hide }) });

export const getRealRules = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/rules/real');

export const getRealGroups = (appId?: string) => {
  const params = new URLSearchParams();
  if (appId) params.set('app_id', appId);
  const qs = params.toString();
  return fetchJSON<FirewallGroup[]>(`/api/reference/groups/real${qs ? `?${qs}` : ''}`);
};

export const getRealGroup = (name: string) =>
  fetchJSON<FirewallGroup>(`/api/reference/groups/real/${name}`);

export const getRealReviews = () =>
  fetchJSON<Record<string, unknown>[]>('/api/reference/reviews/real');

/** Helper: check localStorage for hide-seed preference */
export const isHideSeedEnabled = (): boolean =>
  typeof window !== 'undefined' && localStorage.getItem('nfs_hide_seed') === 'true';

// ---- Lifecycle Management ----

export const getLifecycleDashboard = () =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/dashboard');

export const getLifecycleStates = () =>
  fetchJSON<{ ngdc: Record<string, string[]>; legacy: Record<string, string[]> }>('/api/lifecycle/states');

export const getLifecycleTransitions = (ruleId: string, isLegacy = false) =>
  fetchJSON<{ rule_id: string; current_status: string; valid_transitions: string[] }>(
    `/api/lifecycle/transitions/${ruleId}?is_legacy=${isLegacy}`
  );

export const transitionLifecycle = (ruleId: string, newStatus: string, actor = 'system', module = 'studio', comments = '', isLegacy = false) =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/transition', {
    method: 'POST',
    body: JSON.stringify({ rule_id: ruleId, new_status: newStatus, actor, module, comments, is_legacy: isLegacy }),
  });

export const softDeleteRule = (ruleId: string, reason = '', isLegacy = false, actor = 'system') =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/soft-delete', {
    method: 'POST',
    body: JSON.stringify({ rule_id: ruleId, reason, is_legacy: isLegacy, actor }),
  });

export const restoreDeletedRule = (ruleId: string, isLegacy = false, actor = 'system') =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/restore', {
    method: 'POST',
    body: JSON.stringify({ rule_id: ruleId, is_legacy: isLegacy, actor }),
  });

export const checkCertificationExpiry = (daysAhead = 30) =>
  fetchJSON<Record<string, unknown>>(`/api/lifecycle/certification/check?days_ahead=${daysAhead}`);

export const runAutoExpire = () =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/certification/auto-expire', { method: 'POST' });

export const bulkCertifyRules = (ruleIds: string[], actor = 'system') =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/certification/bulk-certify', {
    method: 'POST',
    body: JSON.stringify({ rule_ids: ruleIds, actor }),
  });

export const bulkDecommissionRules = (ruleIds: string[], reason = '', actor = 'system') =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/decommission/bulk', {
    method: 'POST',
    body: JSON.stringify({ rule_ids: ruleIds, reason, actor }),
  });

export const getLifecycleEvents = (ruleId?: string, eventType?: string, limit = 100) => {
  const params = new URLSearchParams();
  if (ruleId) params.set('rule_id', ruleId);
  if (eventType) params.set('event_type', eventType);
  params.set('limit', String(limit));
  return fetchJSON<Record<string, unknown>[]>(`/api/lifecycle/events?${params}`);
};

export const getLifecycleTimeline = (ruleId: string) =>
  fetchJSON<Record<string, unknown>[]>(`/api/lifecycle/timeline/${ruleId}`);

export const createLifecycleEvent = (ruleId: string, eventType: string, details = '', actor = 'system') =>
  fetchJSON<Record<string, unknown>>('/api/lifecycle/events', {
    method: 'POST',
    body: JSON.stringify({ rule_id: ruleId, event_type: eventType, details, actor }),
  });
