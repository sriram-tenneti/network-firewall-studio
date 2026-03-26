import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Auto-prefix a value based on its entry type.
 * - 'ip' entries get 'svr-' prefix (server / host IP)
 * - 'group' entries get 'grp-' prefix
 * - 'subnet' / 'cidr' / 'range' entries get 'rng-' prefix
 *
 * If the value already has a recognized prefix (svr-, grp-, rng-, sub-, g-),
 * it is returned as-is.
 */
/**
 * Shorten an IP range to compact form.
 * e.g. "10.124.132.4-10.124.132.9" → "10.124.132.4-9"
 * If IPs share the first 3 octets, only the last octet of the end IP is kept.
 * If they share fewer octets, the differing octets of the end IP are kept.
 */
export function shortenIPRange(rangeStr: string): string {
  const m = rangeStr.match(/^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*-\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$/);
  if (!m) return rangeStr;
  const startParts = m[1].split('.');
  const endParts = m[2].split('.');
  // Find how many leading octets match
  let commonCount = 0;
  for (let i = 0; i < 4; i++) {
    if (startParts[i] === endParts[i]) commonCount++;
    else break;
  }
  if (commonCount === 0) return rangeStr; // completely different — keep full
  // Keep only the differing octets of the end IP
  const suffix = endParts.slice(commonCount).join('.');
  return `${m[1]}-${suffix}`;
}

export function autoPrefix(value: string, type: 'ip' | 'subnet' | 'cidr' | 'group' | 'range'): string {
  const v = value.trim();
  if (!v) return v;
  const vl = v.toLowerCase();
  // Already has a recognized prefix — return as-is
  if (vl.startsWith('svr-') || vl.startsWith('grp-') || vl.startsWith('rng-') || vl.startsWith('sub-') || vl.startsWith('g-')) {
    return v;
  }
  // Don't prefix if it looks like a plain IP (x.x.x.x) or CIDR (x.x.x.x/y)
  // but DO prefix named entries (e.g. "myserver", "APP01-web-src")
  const isPlainIP = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/.test(v);
  const isIPRange = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*-\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(v);
  if (isPlainIP || isIPRange) {
    // For raw IPs/CIDRs/ranges, add prefix
    if (type === 'group') return `grp-${v}`;
    if (type === 'subnet' || type === 'cidr' || type === 'range') {
      // Use short range format: rng-10.124.132.4-9 instead of rng-10.124.132.4-10.124.132.9
      const shortened = isIPRange ? shortenIPRange(v) : v;
      return `rng-${shortened}`;
    }
    return `svr-${v}`;
  }
  // Named value without prefix — add based on type
  if (type === 'group') return `grp-${v}`;
  if (type === 'subnet' || type === 'cidr' || type === 'range') return `rng-${v}`;
  return `svr-${v}`;
}
