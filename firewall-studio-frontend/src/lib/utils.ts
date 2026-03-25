import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Auto-prefix a value based on its entry type.
 * - 'ip' entries get 'svr-' prefix (server / host IP)
 * - 'group' entries get 'grp-' prefix
 * - 'subnet' / 'cidr' entries get 'net-' prefix (NGDC standard for subnets)
 * - 'range' entries get 'rng-' prefix (IP ranges xx.xx.xx.xx-xy)
 *
 * If the value already has a recognized prefix (svr-, grp-, rng-, net-, sub-, g-),
 * it is returned as-is (sub- normalized to net-).
 */
export function autoPrefix(value: string, type: 'ip' | 'subnet' | 'cidr' | 'group' | 'range'): string {
  const v = value.trim();
  if (!v) return v;
  const vl = v.toLowerCase();
  // Normalize legacy sub- prefix to NGDC net-
  if (vl.startsWith('sub-')) return `net-${v.slice(4)}`;
  // Already has a recognized prefix — return as-is
  if (vl.startsWith('svr-') || vl.startsWith('grp-') || vl.startsWith('rng-') || vl.startsWith('net-') || vl.startsWith('g-')) {
    return v;
  }
  // Detect raw IP patterns
  const isPlainIP = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(v);
  const isCIDR = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/.test(v);
  const isIPRange = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*-\s*\d{1,3}(\.\d{1,3}){0,3}$/.test(v);
  if (isCIDR) {
    // CIDR notation = subnet (net- prefix)
    if (type === 'group') return `grp-${v}`;
    return `net-${v}`;
  }
  if (isIPRange) {
    // IP range = range (rng- prefix)
    if (type === 'group') return `grp-${v}`;
    return `rng-${v}`;
  }
  if (isPlainIP) {
    // Plain IP = server (svr- prefix)
    if (type === 'group') return `grp-${v}`;
    if (type === 'subnet' || type === 'cidr') return `net-${v}`;
    if (type === 'range') return `rng-${v}`;
    return `svr-${v}`;
  }
  // Named value without prefix — add based on type
  if (type === 'group') return `grp-${v}`;
  if (type === 'subnet' || type === 'cidr') return `net-${v}`;
  if (type === 'range') return `rng-${v}`;
  return `svr-${v}`;
}
