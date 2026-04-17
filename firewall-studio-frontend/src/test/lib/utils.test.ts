import { describe, it, expect } from 'vitest';
import { cn, shortenIPRange, autoPrefix } from '@/lib/utils';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });
  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible');
  });
  it('deduplicates tailwind classes', () => {
    const result = cn('p-4', 'p-2');
    expect(result).toBe('p-2');
  });
  it('handles empty input', () => {
    expect(cn()).toBe('');
  });
  it('handles undefined and null', () => {
    expect(cn(undefined, null, 'test')).toBe('test');
  });
});

describe('shortenIPRange', () => {
  it('shortens range with 3 common octets', () => {
    expect(shortenIPRange('10.124.132.4-10.124.132.9')).toBe('10.124.132.4-9');
  });
  it('shortens range with 2 common octets', () => {
    expect(shortenIPRange('10.124.1.1-10.124.2.1')).toBe('10.124.1.1-2.1');
  });
  it('returns original if no common octets', () => {
    expect(shortenIPRange('10.0.0.1-192.168.1.1')).toBe('10.0.0.1-192.168.1.1');
  });
  it('returns original for non-range strings', () => {
    expect(shortenIPRange('not-a-range')).toBe('not-a-range');
  });
  it('returns original for single IP', () => {
    expect(shortenIPRange('10.0.0.1')).toBe('10.0.0.1');
  });
  it('shortens range with 1 common octet', () => {
    expect(shortenIPRange('10.0.0.1-10.1.2.3')).toBe('10.0.0.1-1.2.3');
  });
  it('handles all 4 octets the same (edge case)', () => {
    const result = shortenIPRange('10.0.0.1-10.0.0.1');
    expect(result).toContain('10.0.0.1');
  });
});

describe('autoPrefix', () => {
  it('prefixes IP with svr-', () => {
    expect(autoPrefix('10.0.0.1', 'ip')).toBe('svr-10.0.0.1');
  });
  it('prefixes group with grp-', () => {
    expect(autoPrefix('mygroup', 'group')).toBe('grp-mygroup');
  });
  it('prefixes subnet with net-', () => {
    expect(autoPrefix('mysubnet', 'subnet')).toBe('net-mysubnet');
  });
  it('prefixes CIDR with net-', () => {
    expect(autoPrefix('10.0.0.0/24', 'cidr')).toBe('net-10.0.0.0/24');
  });
  it('prefixes range with rng-', () => {
    expect(autoPrefix('myrange', 'range')).toBe('rng-myrange');
  });
  it('returns empty for empty string', () => {
    expect(autoPrefix('', 'ip')).toBe('');
  });
  it('returns empty for whitespace', () => {
    expect(autoPrefix('   ', 'ip')).toBe('');
  });
  it('keeps existing svr- prefix', () => {
    expect(autoPrefix('svr-10.0.0.1', 'ip')).toBe('svr-10.0.0.1');
  });
  it('keeps existing grp- prefix', () => {
    expect(autoPrefix('grp-mygroup', 'group')).toBe('grp-mygroup');
  });
  it('keeps existing rng- prefix', () => {
    expect(autoPrefix('rng-myrange', 'range')).toBe('rng-myrange');
  });
  it('keeps existing net- prefix', () => {
    expect(autoPrefix('net-mysubnet', 'subnet')).toBe('net-mysubnet');
  });
  it('normalizes sub- to net-', () => {
    expect(autoPrefix('sub-mysubnet', 'subnet')).toBe('net-mysubnet');
  });
  it('keeps g- prefix', () => {
    expect(autoPrefix('g-mygroup', 'group')).toBe('g-mygroup');
  });
  it('keeps gsvr- prefix', () => {
    expect(autoPrefix('gsvr-10.0.0.1', 'ip')).toBe('gsvr-10.0.0.1');
  });
  it('detects plain IP and prefixes as svr-', () => {
    expect(autoPrefix('192.168.1.1', 'ip')).toBe('svr-192.168.1.1');
  });
  it('detects CIDR and prefixes as net-', () => {
    expect(autoPrefix('10.0.0.0/8', 'subnet')).toBe('net-10.0.0.0/8');
  });
  it('detects IP range and prefixes as rng- with shortening', () => {
    const result = autoPrefix('10.124.132.4-10.124.132.9', 'range');
    expect(result).toBe('rng-10.124.132.4-9');
  });
  it('prefixes plain IP as grp- when type is group', () => {
    expect(autoPrefix('10.0.0.1', 'group')).toBe('grp-10.0.0.1');
  });
  it('prefixes CIDR as grp- when type is group', () => {
    expect(autoPrefix('10.0.0.0/24', 'group')).toBe('grp-10.0.0.0/24');
  });
  it('prefixes IP range as grp- when type is group', () => {
    expect(autoPrefix('10.0.0.1-10.0.0.5', 'group')).toBe('grp-10.0.0.1-10.0.0.5');
  });
  it('prefixes plain IP as net- when type is subnet', () => {
    expect(autoPrefix('10.0.0.1', 'subnet')).toBe('net-10.0.0.1');
  });
  it('prefixes plain IP as rng- when type is range', () => {
    expect(autoPrefix('10.0.0.1', 'range')).toBe('rng-10.0.0.1');
  });
});
