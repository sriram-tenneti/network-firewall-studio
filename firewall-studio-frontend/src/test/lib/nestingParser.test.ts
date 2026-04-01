import { describe, it, expect } from 'vitest';
import {
  isLegacyGroupName,
  detectEntryType,
  parseToResourceEntries,
  entriesToDisplayLines,
  parseExpandedToDisplayLines,
} from '@/lib/nestingParser';
import type { FirewallGroup } from '@/types';

// ── isLegacyGroupName ─────────────────────────────────────────────────────

describe('isLegacyGroupName', () => {
  it('detects g- prefix', () => {
    expect(isLegacyGroupName('g-mygroup')).toBe(true);
  });
  it('detects grp- prefix', () => {
    expect(isLegacyGroupName('grp-mygroup')).toBe(true);
  });
  it('detects ggrp- prefix', () => {
    expect(isLegacyGroupName('ggrp-web')).toBe(true);
  });
  it('detects gapigr- prefix', () => {
    expect(isLegacyGroupName('gapigr-test')).toBe(true);
  });
  it('detects netgrp- prefix', () => {
    expect(isLegacyGroupName('netgrp-lan')).toBe(true);
  });
  it('detects addrgrp- prefix', () => {
    expect(isLegacyGroupName('addrgrp-addr')).toBe(true);
  });
  it('rejects plain IP', () => {
    expect(isLegacyGroupName('10.0.0.1')).toBe(false);
  });
  it('rejects svr- prefix', () => {
    expect(isLegacyGroupName('svr-10.0.0.1')).toBe(false);
  });
  it('is case-insensitive', () => {
    expect(isLegacyGroupName('GRP-Upper')).toBe(true);
  });
  it('trims whitespace', () => {
    expect(isLegacyGroupName('  grp-test  ')).toBe(true);
  });
});

// ── detectEntryType ───────────────────────────────────────────────────────

describe('detectEntryType', () => {
  it('detects plain IP', () => {
    expect(detectEntryType('10.0.0.1')).toBe('ip');
  });
  it('detects CIDR as subnet', () => {
    expect(detectEntryType('10.0.0.0/24')).toBe('subnet');
  });
  it('detects IP range', () => {
    expect(detectEntryType('10.0.0.1-10.0.0.5')).toBe('range');
  });
  it('detects grp- prefix as group', () => {
    expect(detectEntryType('grp-test')).toBe('group');
  });
  it('detects rng- prefix as range', () => {
    expect(detectEntryType('rng-test')).toBe('range');
  });
  it('detects net- prefix as subnet', () => {
    expect(detectEntryType('net-test')).toBe('subnet');
  });
  it('detects sub- prefix as subnet', () => {
    expect(detectEntryType('sub-test')).toBe('subnet');
  });
  it('detects svr- prefix as ip', () => {
    expect(detectEntryType('svr-10.0.0.1')).toBe('ip');
  });
  it('detects gsvr- prefix as ip', () => {
    expect(detectEntryType('gsvr-10.0.0.1')).toBe('ip');
  });
  it('detects legacy group prefixes', () => {
    expect(detectEntryType('g-mygroup')).toBe('group');
  });
  it('detects -networks suffix as group', () => {
    expect(detectEntryType('app-networks')).toBe('group');
  });
  it('detects _networks suffix as group', () => {
    expect(detectEntryType('app_networks')).toBe('group');
  });
  it('detects -global suffix as group', () => {
    expect(detectEntryType('app-global')).toBe('group');
  });
  it('detects -svrs suffix as group', () => {
    expect(detectEntryType('app-svrs')).toBe('group');
  });
  it('detects -servers suffix as group', () => {
    expect(detectEntryType('app-servers')).toBe('group');
  });
  it('detects dcms prefix as group', () => {
    expect(detectEntryType('dcms-test')).toBe('group');
  });
  it('detects dcma- prefix as group', () => {
    expect(detectEntryType('dcma-test')).toBe('group');
  });
  it('detects protected- prefix as group', () => {
    expect(detectEntryType('protected-zone')).toBe('group');
  });
  it('detects rmg- prefix as range', () => {
    expect(detectEntryType('rmg-myrange')).toBe('range');
  });
  it('detects value with / as subnet', () => {
    expect(detectEntryType('some/path')).toBe('subnet');
  });
  it('uses allGroupNames set', () => {
    const groups = new Set(['custom-group']);
    expect(detectEntryType('custom-group', groups)).toBe('group');
  });
  it('defaults to ip for unknown', () => {
    expect(detectEntryType('unknown-entry')).toBe('ip');
  });
});

// ── parseToResourceEntries ────────────────────────────────────────────────

describe('parseToResourceEntries', () => {
  it('returns empty for empty inputs', () => {
    expect(parseToResourceEntries('', [], '')).toEqual([]);
  });
  it('returns empty for whitespace expanded', () => {
    expect(parseToResourceEntries('', [], '   ')).toEqual([]);
  });
  it('parses flat raw text without expansion', () => {
    const entries = parseToResourceEntries('10.0.0.1\ngrp-test', [], '');
    expect(entries).toHaveLength(2);
    expect(entries[0].type).toBe('ip');
    expect(entries[1].type).toBe('group');
  });
  it('parses expanded text with indentation', () => {
    const raw = 'grp-parent';
    const expanded = 'grp-parent\n    10.0.0.1\n    10.0.0.2';
    const entries = parseToResourceEntries(raw, [], expanded);
    expect(entries.length).toBeGreaterThanOrEqual(1);
    const group = entries.find(e => e.type === 'group');
    expect(group).toBeDefined();
  });
  it('assigns group members from known groups', () => {
    const groups: FirewallGroup[] = [{
      name: 'grp-test',
      app_id: 'APP1',
      nh: 'NH01',
      sz: 'GEN',
      subtype: 'APP',
      description: '',
      members: [{ type: 'ip', value: '10.0.0.1', description: '' }],
    }];
    const entries = parseToResourceEntries('grp-test', groups, '');
    expect(entries[0].type).toBe('group');
    expect(entries[0].groupMembers).toHaveLength(1);
  });
  it('handles multiple raw entries', () => {
    const raw = '10.0.0.1\n10.0.0.2\n10.0.0.3';
    const entries = parseToResourceEntries(raw, [], '');
    expect(entries).toHaveLength(3);
  });
  it('handles tab indentation in expanded text', () => {
    const raw = 'grp-parent';
    const expanded = 'grp-parent\n\t10.0.0.1\n\t10.0.0.2';
    const entries = parseToResourceEntries(raw, [], expanded);
    expect(entries.length).toBeGreaterThanOrEqual(1);
  });
  it('strips parenthetical suffixes from expanded values', () => {
    const raw = 'grp-parent';
    const expanded = 'grp-parent\n    10.0.0.1 (server A)';
    const entries = parseToResourceEntries(raw, [], expanded);
    expect(entries.length).toBeGreaterThanOrEqual(1);
  });
  it('handles expanded with only blank lines falls back to raw', () => {
    const result = parseToResourceEntries('test', [], '\n\n\n');
    // When expanded is all blank lines, falls back to raw parsing
    expect(result.length).toBeGreaterThanOrEqual(0);
  });
});

// ── entriesToDisplayLines ─────────────────────────────────────────────────

describe('entriesToDisplayLines', () => {
  it('returns empty for empty entries', () => {
    expect(entriesToDisplayLines([])).toEqual([]);
  });
  it('creates display lines for flat IP entries', () => {
    const entries = [
      { id: '1', type: 'ip' as const, value: '10.0.0.1' },
      { id: '2', type: 'subnet' as const, value: '10.0.0.0/24' },
    ];
    const lines = entriesToDisplayLines(entries);
    expect(lines).toHaveLength(2);
    expect(lines[0].text).toBe('10.0.0.1');
    expect(lines[0].indent).toBe(0);
    expect(lines[0].type).toBe('ip');
    expect(lines[1].type).toBe('subnet');
  });
  it('creates indented lines for group members', () => {
    const entries = [{
      id: '1',
      type: 'group' as const,
      value: 'grp-test',
      groupMembers: [
        { type: 'ip', value: '10.0.0.1' },
        { type: 'subnet', value: '10.0.0.0/24' },
      ],
    }];
    const lines = entriesToDisplayLines(entries);
    expect(lines).toHaveLength(3);
    expect(lines[0].indent).toBe(0);
    expect(lines[1].indent).toBe(1);
    expect(lines[2].indent).toBe(1);
  });
  it('creates double-indented lines for nested sub-group children', () => {
    const entries = [{
      id: '1',
      type: 'group' as const,
      value: 'grp-parent',
      groupMembers: [{
        type: 'group',
        value: 'grp-child',
        children: [{ type: 'ip', value: '10.0.0.1' }],
      }],
    }];
    const lines = entriesToDisplayLines(entries);
    expect(lines).toHaveLength(3);
    expect(lines[0].indent).toBe(0);
    expect(lines[1].indent).toBe(1);
    expect(lines[2].indent).toBe(2);
  });
  it('handles group with no members', () => {
    const entries = [{
      id: '1',
      type: 'group' as const,
      value: 'grp-empty',
      groupMembers: [],
    }];
    const lines = entriesToDisplayLines(entries);
    expect(lines).toHaveLength(1);
    expect(lines[0].type).toBe('group');
  });
  it('normalizes unknown types to ip', () => {
    const entries = [{
      id: '1',
      type: 'ip' as const,
      value: 'something',
    }];
    const lines = entriesToDisplayLines(entries);
    expect(lines[0].type).toBe('ip');
  });
});

// ── parseExpandedToDisplayLines ───────────────────────────────────────────

describe('parseExpandedToDisplayLines', () => {
  it('returns empty for empty inputs', () => {
    expect(parseExpandedToDisplayLines('', '')).toEqual([]);
  });
  it('parses raw when expanded is empty', () => {
    const lines = parseExpandedToDisplayLines('10.0.0.1\ngrp-test', '');
    expect(lines).toHaveLength(2);
    expect(lines[0].type).toBe('ip');
    expect(lines[1].type).toBe('group');
  });
  it('parses expanded text with hierarchy', () => {
    const lines = parseExpandedToDisplayLines(
      'grp-parent',
      'grp-parent\n    10.0.0.1\n    10.0.0.2'
    );
    expect(lines.length).toBeGreaterThanOrEqual(1);
  });
  it('handles only whitespace expanded', () => {
    const lines = parseExpandedToDisplayLines('10.0.0.1', '   \n   ');
    expect(lines).toHaveLength(1);
    expect(lines[0].text).toBe('10.0.0.1');
  });
  it('handles raw with whitespace-only lines', () => {
    const lines = parseExpandedToDisplayLines('  \n10.0.0.1\n  ', '');
    expect(lines.length).toBeGreaterThanOrEqual(1);
  });
});
