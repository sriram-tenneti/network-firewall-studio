import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import { getLegacyRules, updateLegacyRule, submitLegacyRulesForReview, migrateRulesToNGDC } from '@/lib/api';
import type { LegacyRule } from '@/types';
import type { Column } from '@/components/shared/DataTable';

export function MigrationStudioPage() {
  const [legacyRules, setLegacyRules] = useState<LegacyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('All');
  const [selectedRuleIds, setSelectedRuleIds] = useState<Set<string>>(new Set());

  const detailModal = useModal<LegacyRule>();
  const { notification, showNotification } = useNotification();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const rulesData = await getLegacyRules(selectedApp || undefined, true);
      setLegacyRules(rulesData);
    } catch {
      showNotification('Failed to load migration data', 'error');
    }
    setLoading(false);
  }, [selectedApp, showNotification]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = legacyRules.filter(r => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Non-Standard') return !r.is_standard;
    if (activeTab === 'Standard') return r.is_standard;
    return r.migration_status === activeTab;
  });

  const counts = {
    All: legacyRules.length,
    'Non-Standard': legacyRules.filter(r => !r.is_standard).length,
    Standard: legacyRules.filter(r => r.is_standard).length,
    'Not Started': legacyRules.filter(r => r.migration_status === 'Not Started').length,
    'In Progress': legacyRules.filter(r => r.migration_status === 'In Progress').length,
  };

  const appOptions = Array.from(new Set(legacyRules.map(r => `${r.app_id}|${r.app_distributed_id}|${r.app_name}`))).map(key => {
    const [appId, distId, appName] = key.split('|');
    return { value: String(appId), label: `${appId} - ${appName} (${distId})` };
  });

  const toggleSelection = (ruleId: string) => {
    setSelectedRuleIds(prev => {
      const next = new Set(prev);
      if (next.has(ruleId)) next.delete(ruleId);
      else next.add(ruleId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedRuleIds.size === filteredRules.length) {
      setSelectedRuleIds(new Set());
    } else {
      setSelectedRuleIds(new Set(filteredRules.map(r => r.id)));
    }
  };

  const handleSubmitForReview = async () => {
    if (selectedRuleIds.size === 0) {
      showNotification('Select rules to submit for review', 'error');
      return;
    }
    try {
      const result = await submitLegacyRulesForReview(Array.from(selectedRuleIds));
      showNotification(`${result.submitted} rules submitted for review`, 'success');
      setSelectedRuleIds(new Set());
      loadData();
    } catch {
      showNotification('Failed to submit for review', 'error');
    }
  };

  const handleMigrateSelected = async () => {
    if (selectedRuleIds.size === 0) {
      showNotification('Select rules to migrate', 'error');
      return;
    }
    try {
      const result = await migrateRulesToNGDC(Array.from(selectedRuleIds));
      showNotification(`${result.migrated} rules migrated to NGDC`, 'success');
      setSelectedRuleIds(new Set());
      loadData();
    } catch {
      showNotification('Failed to migrate rules', 'error');
    }
  };

  const handleStartMigration = async (ruleId: string) => {
    try {
      await updateLegacyRule(ruleId, { migration_status: 'In Progress' });
      showNotification('Migration started', 'success');
      detailModal.close();
      loadData();
    } catch {
      showNotification('Failed to start migration', 'error');
    }
  };

  const parseExpandedTree = (text: string): string[] => {
    if (!text) return [];
    return text.split('\n').map(line => line.replace(/\t/g, '  '));
  };

  const columns: Column<LegacyRule>[] = [
    {
      key: '_select', header: '', sortable: false, width: '40px',
      render: (_, row) => (
        <input
          type="checkbox"
          checked={selectedRuleIds.has(row.id)}
          onChange={() => toggleSelection(row.id)}
          onClick={e => e.stopPropagation()}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      ),
    },
    { key: 'id', header: 'Rule ID', sortable: true, width: '80px' },
    { key: 'app_id', header: 'App ID', sortable: true, width: '70px',
      render: (_, row) => <span className="text-xs">{String(row.app_id)}</span>,
    },
    { key: 'app_distributed_id', header: 'Dist ID', sortable: true, width: '70px' },
    { key: 'app_name', header: 'App Name', sortable: true, width: '110px' },
    { key: 'inventory_item', header: 'Inventory', sortable: true, width: '120px' },
    { key: 'policy_name', header: 'Policy', sortable: true, width: '90px' },
    { key: 'rule_action', header: 'Action', sortable: true, width: '70px',
      render: (_, row) => (
        <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${row.rule_action === 'Accept' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {row.rule_action}
        </span>
      ),
    },
    {
      key: 'rule_source', header: 'Source', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_source || '').split('\n').filter(Boolean);
        return (
          <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>
        );
      },
    },
    { key: 'rule_source_zone', header: 'Src Zone', sortable: true, width: '100px' },
    {
      key: 'rule_destination', header: 'Destination', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_destination || '').split('\n').filter(Boolean);
        return (
          <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>
        );
      },
    },
    { key: 'rule_destination_zone', header: 'Dst Zone', sortable: true, width: '90px' },
    {
      key: 'rule_service', header: 'Service', sortable: false, width: '100px',
      render: (_, row) => <span className="text-xs">{row.rule_service || 'N/A'}</span>,
    },
    {
      key: 'migration_status', header: 'Status', sortable: true, width: '100px',
      render: (_, row) => <StatusBadge status={row.migration_status} />,
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '80px',
      render: (_, row) => (
        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
          <button onClick={() => detailModal.open(row)} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">View</button>
        </div>
      ),
    },
  ];

  const tabs = [
    { id: 'All', label: 'All Rules', count: counts.All },
    { id: 'Non-Standard', label: 'Non-Standard', count: counts['Non-Standard'] },
    { id: 'Standard', label: 'Standard', count: counts.Standard },
    { id: 'Not Started', label: 'Not Started', count: counts['Not Started'] },
    { id: 'In Progress', label: 'In Progress', count: counts['In Progress'] },
  ];

  return (
    <div className="p-6 max-w-[1800px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Migration to NGDC</h1>
          <p className="text-sm text-gray-500 mt-1">Analyze legacy rules, map to NGDC standards, and submit for review</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedApp}
            onChange={e => setSelectedApp(e.target.value)}
          >
            <option value="">All Applications</option>
            {appOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {selectedRuleIds.size > 0 && (
            <>
              <span className="text-sm text-gray-600 font-medium">{selectedRuleIds.size} selected</span>
              <button onClick={handleSubmitForReview} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm">
                Submit for Review
              </button>
              <button onClick={handleMigrateSelected} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 shadow-sm">
                Migrate to NGDC
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Total Rules', value: counts.All, color: 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800' },
          { label: 'Non-Standard', value: counts['Non-Standard'], color: 'bg-gradient-to-br from-red-100 to-red-200 text-red-800' },
          { label: 'Standard', value: counts.Standard, color: 'bg-gradient-to-br from-green-100 to-green-200 text-green-800' },
          { label: 'Not Started', value: counts['Not Started'], color: 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-800' },
          { label: 'In Progress', value: counts['In Progress'], color: 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-800' },
        ].map(card => (
          <div key={card.label} className={'p-3 rounded-lg shadow-sm ' + card.color}>
            <div className="text-xl font-bold">{card.value}</div>
            <div className="text-xs font-medium mt-0.5">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 pt-4 flex items-center justify-between">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
          <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
            <input type="checkbox" checked={selectedRuleIds.size === filteredRules.length && filteredRules.length > 0} onChange={toggleSelectAll} className="rounded border-gray-300 text-blue-600" />
            Select All
          </label>
        </div>
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <DataTable
              data={filteredRules}
              columns={columns}
              keyField="id"
              searchPlaceholder="Search by IP, group, app, rule ID, zone, service..."
              searchFields={['id', 'app_id', 'app_distributed_id', 'app_name', 'rule_source', 'rule_source_expanded', 'rule_destination', 'rule_destination_expanded', 'rule_source_zone', 'rule_destination_zone', 'rule_service', 'inventory_item']}
              onRowClick={(row) => detailModal.open(row)}
              emptyMessage="No legacy rules found for migration"
              defaultPageSize={50}
            />
          )}
        </div>
      </div>

      {/* Detail Modal with Expanded IPs */}
      <Modal isOpen={detailModal.isOpen} onClose={detailModal.close} title={`Rule Details: ${detailModal.data?.id || ''}`} size="xl">
        {detailModal.data && (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-3">
              {([
                ['Rule ID', detailModal.data.id],
                ['App ID', String(detailModal.data.app_id)],
                ['App Distributed ID', detailModal.data.app_distributed_id],
                ['App Name', detailModal.data.app_name],
                ['Inventory Item', detailModal.data.inventory_item],
                ['Policy Name', detailModal.data.policy_name],
                ['Rule Global', detailModal.data.rule_global ? 'Yes' : 'No'],
                ['Rule Action', detailModal.data.rule_action],
                ['Source Zone', detailModal.data.rule_source_zone],
                ['Destination Zone', detailModal.data.rule_destination_zone],
                ['Service', detailModal.data.rule_service],
                ['Migration Status', detailModal.data.migration_status],
                ['RN', String(detailModal.data.rn)],
                ['RC', String(detailModal.data.rc)],
              ] as [string, string][]).map(([label, val]) => (
                <div key={label} className="p-2 bg-gray-50 rounded">
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-sm font-medium text-gray-800 break-all">{val}</p>
                </div>
              ))}
            </div>

            {/* Source Expanded */}
            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-blue-50 border-b">
                <h3 className="text-sm font-semibold text-blue-800">Source (Expanded IPs/Groups)</h3>
              </div>
              <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
                {parseExpandedTree(detailModal.data.rule_source_expanded).map((line, i) => {
                  const indent = line.length - line.trimStart().length;
                  return (
                    <div key={i} className="font-mono text-xs text-green-400" style={{ paddingLeft: `${indent * 8}px` }}>
                      {line.trim()}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Destination Expanded */}
            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-purple-50 border-b">
                <h3 className="text-sm font-semibold text-purple-800">Destination (Expanded IPs/Groups)</h3>
              </div>
              <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
                {parseExpandedTree(detailModal.data.rule_destination_expanded).map((line, i) => {
                  const indent = line.length - line.trimStart().length;
                  return (
                    <div key={i} className="font-mono text-xs text-purple-400" style={{ paddingLeft: `${indent * 8}px` }}>
                      {line.trim()}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Service Expanded */}
            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-amber-50 border-b">
                <h3 className="text-sm font-semibold text-amber-800">Service (Expanded)</h3>
              </div>
              <div className="p-3 bg-gray-900">
                {(detailModal.data.rule_service_expanded || '').split('\n').map((line, i) => (
                  <div key={i} className="font-mono text-xs text-amber-400">{line}</div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              {detailModal.data.migration_status === 'Not Started' && (
                <button onClick={() => handleStartMigration(detailModal.data!.id)} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700">
                  Start Migration
                </button>
              )}
              <button onClick={detailModal.close} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
