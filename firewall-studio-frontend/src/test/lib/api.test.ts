import { describe, it, expect, vi, beforeEach } from 'vitest';
import { transformRule } from '@/lib/api';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

describe('transformRule', () => {
  const rawRule = {
    rule_id: 'R001',
    source: 'grp-CRM-NH02-GEN-APP',
    source_zone: 'GEN',
    destination: 'grp-CRM-NH02-CDE-DB',
    destination_zone: 'CDE',
    port: '443',
    protocol: 'TCP',
    action: 'Allow',
    description: 'Test rule',
    application: 'CRM',
    status: 'Draft',
    is_group_to_group: true,
    environment: 'Production',
    datacenter: 'NGDC-East',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    certified_date: null,
    expiry_date: null,
  };

  it('transforms rule_id to id', () => {
    const result = transformRule(rawRule);
    expect(result.id).toBe('R001');
    expect(result.rule_id).toBe('R001');
  });

  it('transforms source to SourceConfig', () => {
    const result = transformRule(rawRule);
    expect(result.source.source_type).toBe('Group');
    expect(result.source.group_name).toBe('grp-CRM-NH02-GEN-APP');
    expect(result.source.security_zone).toBe('GEN');
    expect(result.source.ports).toBe('443');
  });

  it('transforms destination to DestinationConfig', () => {
    const result = transformRule(rawRule);
    expect(result.destination.name).toBe('grp-CRM-NH02-CDE-DB');
    expect(result.destination.security_zone).toBe('CDE');
  });

  it('sets compliance info', () => {
    const result = transformRule(rawRule);
    expect(result.compliance?.naming_valid).toBe(true);
    expect(result.compliance?.group_to_group).toBe(true);
    expect(result.compliance?.requires_exception).toBe(false);
  });

  it('maps status correctly', () => {
    const result = transformRule(rawRule);
    expect(result.status).toBe('Draft');
  });

  it('handles certified_date as null', () => {
    const result = transformRule(rawRule);
    expect(result.certified_at).toBeNull();
    expect(result.certified_by).toBeNull();
  });

  it('handles certified_date when present', () => {
    const certifiedRule = { ...rawRule, certified_date: '2024-06-01T00:00:00Z' };
    const result = transformRule(certifiedRule);
    expect(result.certified_at).toBe('2024-06-01T00:00:00Z');
    expect(result.certified_by).toBe('System');
  });

  it('handles plain IP source', () => {
    const ipRule = { ...rawRule, source: '10.0.0.1' };
    const result = transformRule(ipRule);
    expect(result.source.source_type).toBe('Single IP');
    expect(result.source.ip_address).toBe('10.0.0.1');
  });

  it('handles CIDR source', () => {
    const cidrRule = { ...rawRule, source: '10.0.0.0/24' };
    const result = transformRule(cidrRule);
    expect(result.source.source_type).toBe('Subnet');
    expect(result.source.cidr).toBe('10.0.0.0/24');
  });

  it('handles svr- prefix source', () => {
    const svrRule = { ...rawRule, source: 'svr-10.0.0.1' };
    const result = transformRule(svrRule);
    expect(result.source.source_type).toBe('Group');
    expect(result.source.group_name).toBe('svr-10.0.0.1');
  });

  it('handles rng- prefix source', () => {
    const rngRule = { ...rawRule, source: 'rng-10.0.0.1-5' };
    const result = transformRule(rngRule);
    expect(result.source.source_type).toBe('Group');
    expect(result.source.group_name).toBe('rng-10.0.0.1-5');
  });

  it('sets naming_valid false for non-standard names', () => {
    const badRule = { ...rawRule, source: '10.0.0.1', destination: '10.0.0.2' };
    const result = transformRule(badRule);
    expect(result.compliance?.naming_valid).toBe(false);
  });

  it('sets requires_exception for non-group-to-group', () => {
    const nonG2G = { ...rawRule, is_group_to_group: false };
    const result = transformRule(nonG2G);
    expect(result.compliance?.requires_exception).toBe(true);
  });

  it('sets destination is_predefined for grp- prefix', () => {
    const result = transformRule(rawRule);
    expect(result.destination.is_predefined).toBe(true);
  });

  it('sets dest_ip for numeric destinations', () => {
    const ipDestRule = { ...rawRule, destination: '10.0.0.5' };
    const result = transformRule(ipDestRule);
    expect(result.destination.dest_ip).toBe('10.0.0.5');
  });

  it('sets dest_ip null for named destinations', () => {
    const result = transformRule(rawRule);
    expect(result.destination.dest_ip).toBeNull();
  });

  it('preserves environment and datacenter', () => {
    const result = transformRule(rawRule);
    expect(result.environment).toBe('Production');
    expect(result.datacenter).toBe('NGDC-East');
  });

  it('preserves timestamps', () => {
    const result = transformRule(rawRule);
    expect(result.created_at).toBe('2024-01-01T00:00:00Z');
    expect(result.updated_at).toBe('2024-01-02T00:00:00Z');
  });

  it('sets policy_result to Permitted', () => {
    const result = transformRule(rawRule);
    expect(result.policy_result).toBe('Permitted');
  });

  it('sets owner to System', () => {
    const result = transformRule(rawRule);
    expect(result.owner).toBe('System');
  });
});

// Test fetchJSON indirectly through exported functions
describe('API functions (fetch-based)', () => {
  it('getRules calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getRules } = await import('@/lib/api');
    const rules = await getRules();
    expect(rules).toEqual([]);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/rules'),
      expect.any(Object)
    );
  });

  it('getRules passes application filter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getRules } = await import('@/lib/api');
    await getRules('CRM');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('application=CRM'),
      expect.any(Object)
    );
  });

  it('getMigrations calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getMigrations } = await import('@/lib/api');
    await getMigrations();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/migrations'),
      expect.any(Object)
    );
  });

  it('getSecurityZones calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getSecurityZones } = await import('@/lib/api');
    await getSecurityZones();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/reference/security-zones'),
      expect.any(Object)
    );
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });
    const { getNGDCDatacenters } = await import('@/lib/api');
    await expect(getNGDCDatacenters()).rejects.toThrow('API error: 500');
  });

  it('validatePolicy sends POST', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ result: 'Permitted' }),
    });
    const { validatePolicy } = await import('@/lib/api');
    await validatePolicy({
      source: { source_type: 'Group', ip_address: null, cidr: null, group_name: 'grp-test', ports: '443', neighbourhood: null, security_zone: 'GEN' },
      destination: { name: 'grp-dest', security_zone: 'CDE', dest_ip: null, ports: '443', is_predefined: true },
      application: 'CRM',
      environment: 'Production',
    });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/policy/validate'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('createRule sends POST with body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ rule_id: 'R001' }),
    });
    const { createRule } = await import('@/lib/api');
    await createRule({ source: '10.0.0.1', destination: '10.0.0.2' });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/rules'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('deleteRule sends DELETE', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: 'deleted' }),
    });
    const { deleteRule } = await import('@/lib/api');
    await deleteRule('R001');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/rules/R001'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  it('getGroups calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getGroups } = await import('@/lib/api');
    await getGroups();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/reference/groups'),
      expect.any(Object)
    );
  });

  it('getGroups passes appId filter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getGroups } = await import('@/lib/api');
    await getGroups('CRM');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('app_id=CRM'),
      expect.any(Object)
    );
  });

  it('getLegacyRules calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getLegacyRules } = await import('@/lib/api');
    await getLegacyRules();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/reference/legacy-rules'),
      expect.any(Object)
    );
  });

  it('getLegacyRules passes filters', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    const { getLegacyRules } = await import('@/lib/api');
    await getLegacyRules('CRM', true, 'Production');
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('app_id=CRM');
    expect(url).toContain('exclude_migrated=true');
    expect(url).toContain('environment=Production');
  });
});
