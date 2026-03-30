import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import { StatusBadge } from '../shared/StatusBadge';
import { getRealGroup } from '@/lib/api';
import type { FirewallRule, FirewallGroup } from '@/types';

interface RuleDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  rule: FirewallRule | null;
  onEdit?: () => void;
  onCompile?: () => void;
  onSubmitReview?: () => void;
}

function getVal(obj: unknown, key: string): string {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  if (typeof obj === 'object' && obj !== null) return (obj as Record<string, string>)[key] || '';
  return '';
}

/**
 * Detect entry type from naming convention:
 *   svr- = IP, grp-/g- = GROUP, rng- = RANGE, sub- = SUBNET
 */
function detectType(value: string): 'ip' | 'group' | 'range' | 'subnet' {
  const vl = value.trim().toLowerCase();
  if (vl.startsWith('grp-') || vl.startsWith('g-')) return 'group';
  if (vl.startsWith('rng-')) return 'range';
  if (vl.startsWith('sub-') || vl.includes('/')) return 'subnet';
  return 'ip';
}

const typeBadgeColors: Record<string, string> = {
  ip: 'bg-blue-100 text-blue-700',
  group: 'bg-emerald-100 text-emerald-700',
  range: 'bg-orange-100 text-orange-700',
  subnet: 'bg-purple-100 text-purple-700',
};
const typeBadgeLabels: Record<string, string> = {
  ip: 'IP',
  group: 'GROUP',
  range: 'RANGE',
  subnet: 'SUBNET',
};

/** Render hierarchical expanded source/destination with type badges and indentation */
function ExpandedHierarchy({ text, color }: { text: string; color: string }) {
  if (!text) return <p className="text-xs text-gray-400 italic">No data</p>;
  const lines = text.split('\n');
  return (
    <div className="space-y-0.5">
      {lines.map((line, i) => {
        if (!line.trim()) return null;
        const indent = line.length - line.trimStart().length;
        const tabCount = (line.match(/\t/g) || []).length;
        const totalIndent = indent + tabCount;
        const v = line.trim();
        const type = detectType(v);
        const isGroupMember = totalIndent >= 2;
        return (
          <div key={i} className={`flex items-center gap-2 ${isGroupMember ? 'ml-6 pl-3 border-l-2 border-gray-600' : ''}`}>
            <span className={`px-1.5 py-0.5 text-[9px] font-bold uppercase rounded ${typeBadgeColors[type] || 'bg-gray-100 text-gray-600'}`}>
              {typeBadgeLabels[type] || type}
            </span>
            <span className={`font-mono text-xs ${color}`}>{v}</span>
          </div>
        );
      })}
    </div>
  );
}

export function RuleDetailModal({ isOpen, onClose, rule, onEdit, onCompile, onSubmitReview }: RuleDetailModalProps) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, FirewallGroup>>({});
  const [loadingGroups, setLoadingGroups] = useState(false);

  useEffect(() => {
    if (!rule || !isOpen) { setExpandedGroups({}); return; }
    const groupNames: string[] = [];
    const srcVal = getVal(rule.source, 'group_name') || getVal(rule.source, 'ip_address') || (typeof rule.source === 'string' ? rule.source : '');
    const dstVal = getVal(rule.destination, 'name') || (typeof rule.destination === 'string' ? rule.destination : '');
    for (const v of [srcVal, dstVal]) {
      v.split(',').map(s => s.trim()).filter(s => s.startsWith('grp-') || s.startsWith('g-')).forEach(g => groupNames.push(g));
    }
    if (groupNames.length === 0) return;
    setLoadingGroups(true);
    Promise.allSettled(groupNames.map(n => getRealGroup(n)))
      .then(results => {
        const map: Record<string, FirewallGroup> = {};
        results.forEach((r, i) => { if (r.status === 'fulfilled') map[groupNames[i]] = r.value; });
        setExpandedGroups(map);
      })
      .finally(() => setLoadingGroups(false));
  }, [rule, isOpen]);

  if (!rule) return null;

  const srcGroup = getVal(rule.source, 'group_name') || getVal(rule.source, 'ip_address') || (typeof rule.source === 'string' ? rule.source : '');
  const srcZone = getVal(rule.source, 'security_zone');
  const srcPorts = getVal(rule.source, 'ports');
  const srcDC = getVal(rule.source, 'datacenter') || rule.datacenter || '';
  const srcNH = getVal(rule.source, 'neighbourhood') || getVal(rule.source, 'nh') || '';
  const srcSZ = getVal(rule.source, 'sz') || srcZone;
  const dstName = getVal(rule.destination, 'name') || (typeof rule.destination === 'string' ? rule.destination : '');
  const dstZone = getVal(rule.destination, 'security_zone');
  const dstPorts = getVal(rule.destination, 'ports');
  const dstDC = getVal(rule.destination, 'datacenter') || rule.datacenter || '';
  const dstNH = getVal(rule.destination, 'neighbourhood') || getVal(rule.destination, 'nh') || '';
  const dstSZ = getVal(rule.destination, 'sz') || dstZone;

  // Check if rule has expanded source/dest (LegacyRule-style)
  const legacyRule = rule as unknown as Record<string, string>;
  const srcExpanded = legacyRule.rule_source_expanded || '';
  const dstExpanded = legacyRule.rule_destination_expanded || '';

  const rows: [string, string | React.ReactNode][] = [
    ['Rule ID', rule.rule_id],
    ['Application', `${rule.application}${rule.application_name ? ` - ${rule.application_name}` : ''}`],
    ['Status', <StatusBadge key="s" status={rule.status} />],
    ['Environment', rule.environment],
    ['Datacenter', rule.datacenter],
    ['Source', srcGroup],
    ['Source Zone', srcZone],
    ['Source DC', srcDC],
    ['Source NH', srcNH],
    ['Source SZ', srcSZ],
    ['Source Ports', srcPorts],
    ['Destination', dstName],
    ['Destination Zone', dstZone],
    ['Destination DC', dstDC],
    ['Destination NH', dstNH],
    ['Destination SZ', dstSZ],
    ['Destination Ports', dstPorts],
    ['Policy Result', rule.policy_result ? <StatusBadge key="p" status={rule.policy_result} /> : 'N/A'],
    ['Owner', rule.owner || 'N/A'],
    ['Created', rule.created_at ? new Date(rule.created_at).toLocaleString() : 'N/A'],
    ['Updated', rule.updated_at ? new Date(rule.updated_at).toLocaleString() : 'N/A'],
    ['Certified', rule.certified_at ? new Date(rule.certified_at).toLocaleString() : 'Not Certified'],
    ['Expiry', rule.expiry || 'N/A'],
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Rule Details: ${rule.rule_id}`} size="lg">
      <div className="divide-y divide-gray-100">
        {rows.map(([label, value]) => (
          <div key={label} className="flex py-2.5 px-1">
            <div className="w-40 text-sm font-medium text-gray-500 flex-shrink-0">{label}</div>
            <div className="text-sm text-gray-900 flex-1">{value}</div>
          </div>
        ))}
      </div>

      {/* Hierarchical Source Expanded */}
      {srcExpanded && (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-blue-50 border-b">
            <h4 className="text-sm font-semibold text-blue-800">Source (Expanded IPs/Groups)</h4>
          </div>
          <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
            <ExpandedHierarchy text={srcExpanded} color="text-green-400" />
          </div>
        </div>
      )}

      {/* Hierarchical Destination Expanded */}
      {dstExpanded && (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-purple-50 border-b">
            <h4 className="text-sm font-semibold text-purple-800">Destination (Expanded IPs/Groups)</h4>
          </div>
          <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
            <ExpandedHierarchy text={dstExpanded} color="text-purple-400" />
          </div>
        </div>
      )}

      {/* Expanded Group Members */}
      {(Object.keys(expandedGroups).length > 0 || loadingGroups) && (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-emerald-50 border-b">
            <h4 className="text-sm font-semibold text-emerald-800">Group Members (Expanded)</h4>
          </div>
          <div className="p-3 space-y-3">
            {loadingGroups ? (
              <p className="text-xs text-gray-500 italic">Loading group members...</p>
            ) : (
              Object.entries(expandedGroups).map(([name, group]) => (
                <div key={name} className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="px-3 py-2 bg-gray-50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-emerald-100 text-emerald-700">GROUP</span>
                      <span className="text-xs font-mono font-medium text-gray-800">{name}</span>
                    </div>
                    <span className="text-[10px] text-gray-500">{group.members.length} member{group.members.length !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="px-3 py-2 bg-gray-900">
                    {group.members.length > 0 ? group.members.map((m, i) => (
                      <div key={i} className="flex items-center gap-2 py-0.5">
                        <span className={`px-1 py-0.5 text-[8px] font-bold uppercase rounded ${
                          m.type === 'ip' ? 'bg-blue-100 text-blue-700' :
                          m.type === 'range' ? 'bg-orange-100 text-orange-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>{m.type}</span>
                        <span className="text-xs font-mono text-green-400">{m.value}</span>
                      </div>
                    )) : (
                      <p className="text-xs text-gray-500 italic">No members</p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {rule.compliance && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Compliance</h4>
          <div className="flex gap-4 text-xs">
            <span className={rule.compliance.naming_valid ? 'text-green-600' : 'text-red-600'}>
              Naming: {rule.compliance.naming_valid ? 'Valid' : 'Invalid'}
            </span>
            <span className={rule.compliance.group_to_group ? 'text-green-600' : 'text-amber-600'}>
              Group-to-Group: {rule.compliance.group_to_group ? 'Yes' : 'No'}
            </span>
            {rule.compliance.requires_exception && (
              <span className="text-red-600">Exception Required</span>
            )}
          </div>
          {rule.compliance.naming_errors && rule.compliance.naming_errors.length > 0 && (
            <ul className="mt-2 text-xs text-red-600 list-disc list-inside">
              {rule.compliance.naming_errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
      )}

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        {onEdit && rule.status === 'Draft' && (
          <button onClick={onEdit} className="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-md hover:bg-amber-600">Edit</button>
        )}
        {onCompile && (rule.status === 'Approved' || rule.status === 'Deployed' || rule.status === 'Certified') && (
          <button onClick={onCompile} className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700">Compile</button>
        )}
        {onSubmitReview && rule.status === 'Draft' && (
          <button onClick={onSubmitReview} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">Submit for Review</button>
        )}
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
