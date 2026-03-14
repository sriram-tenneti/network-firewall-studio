import { Modal } from '../shared/Modal';
import { StatusBadge } from '../shared/StatusBadge';
import type { LegacyRule } from '@/types';

interface LegacyRuleDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  rule: LegacyRule | null;
  onStartMigration?: () => void;
}

export function LegacyRuleDetailModal({ isOpen, onClose, rule, onStartMigration }: LegacyRuleDetailModalProps) {
  if (!rule) return null;

  const rows: [string, string | React.ReactNode][] = [
    ['Rule ID', rule.id],
    ['App ID', rule.app_id],
    ['App Distributed ID', rule.app_distributed_id],
    ['Rule Name', rule.rule_name],
    ['Inventory', rule.inventory],
    ['Policy Row', rule.policy_row],
    ['Rule Status', rule.rule_status],
    ['Rule Action', rule.rule_action],
    ['Source Zone', rule.source_zone],
    ['Source Entries', rule.source_entries?.join(', ') || 'N/A'],
    ['Source Expanded', rule.source_expanded?.join(', ') || 'N/A'],
    ['Destination Entries', rule.destination_entries?.join(', ') || 'N/A'],
    ['Destination Expanded', rule.destination_expanded?.join(', ') || 'N/A'],
    ['Ports', rule.ports?.join(', ') || 'N/A'],
    ['Is Standard', <StatusBadge key="std" status={rule.is_standard ? 'Yes' : 'No'} />],
    ['Migration Status', <StatusBadge key="ms" status={rule.migration_status} />],
    ['Suggested Standard Name', rule.suggested_standard_name || 'N/A'],
  ];

  const isNonStandard = !rule.is_standard;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Legacy Rule: ${rule.rule_name}`} size="lg">
      {isNonStandard && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-amber-600 text-lg">!</span>
            <div>
              <h4 className="text-sm font-semibold text-amber-800">Non-Standard Rule Detected</h4>
              <p className="text-xs text-amber-700 mt-1">
                This rule does not conform to NGDC naming standards. Migration is recommended to ensure compliance with security zone requirements and group-to-group enforcement.
              </p>
              {rule.suggested_standard_name && (
                <p className="text-xs text-amber-700 mt-1">
                  <span className="font-medium">Suggested Standard Name:</span> <code className="bg-amber-100 px-1 rounded">{rule.suggested_standard_name}</code>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="divide-y divide-gray-100">
        {rows.map(([label, value]) => (
          <div key={label} className="flex py-2.5 px-1">
            <div className="w-44 text-sm font-medium text-gray-500 flex-shrink-0">{label}</div>
            <div className="text-sm text-gray-900 flex-1 break-all">{value}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Migration Recommendations</h4>
        <ul className="text-xs text-gray-600 space-y-1.5">
          {isNonStandard ? (
            <>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">&#8226;</span>
                <span>Rename source/destination groups to NGDC naming convention (grp-AppID-NH-SZ-subtype)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">&#8226;</span>
                <span>Map existing IPs/subnets to appropriate neighbourhood and security zone</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">&#8226;</span>
                <span>Verify policy compliance against NGDC policy matrix</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">&#8226;</span>
                <span>Submit migrated rule for SNS review and approval</span>
              </li>
            </>
          ) : (
            <li className="flex items-start gap-2">
              <span className="text-green-500 mt-0.5">&#8226;</span>
              <span>This rule already follows standard naming conventions. Verify security zone mapping and submit for certification.</span>
            </li>
          )}
        </ul>
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        {onStartMigration && rule.migration_status !== 'Completed' && (
          <button onClick={onStartMigration} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
            {rule.migration_status === 'Not Started' ? 'Start Migration' : 'Continue Migration'}
          </button>
        )}
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
