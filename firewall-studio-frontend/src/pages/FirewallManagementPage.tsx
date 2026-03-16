import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { ExceptionHandler } from '@/components/design-studio/ExceptionHandler';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import { getLegacyRules } from '@/lib/api';
import type { LegacyRule } from '@/types';
import type { Column } from '@/components/shared/DataTable';

export default function FirewallManagementPage() {
  const [rules, setRules] = useState<LegacyRule[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const { notification, showNotification, clearNotification } = useNotification();
  const detailModal = useModal<LegacyRule>();
  const [exceptions, setExceptions] = useState<Array<{id: string; type: 'ip' | 'subnet'; value: string; justification: string; status: 'Pending' | 'Approved' | 'Rejected'; requested_by: string; requested_at: string}>>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const rulesData = await getLegacyRules(selectedApp || undefined, true);
      setRules(rulesData);
    } catch {
      showNotification('Failed to load data', 'error');
    }
    setLoading(false);
  }, [selectedApp, showNotification]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = rules.filter(r => {
    if (activeTab === 'non_standard') return !r.is_standard;
    if (activeTab === 'standard') return r.is_standard;
    return true;
  });

  const standardCount = rules.filter(r => r.is_standard).length;
  const nonStandardCount = rules.filter(r => !r.is_standard).length;

  const appOptions = Array.from(new Set(rules.map(r => `${r.app_id}|${r.app_distributed_id}|${r.app_name}`))).map(key => {
    const [appId, distId, appName] = key.split('|');
    return { value: String(appId), label: `${appId} - ${appName} (${distId})` };
  });

  const parseExpandedTree = (text: string): string[] => {
    if (!text) return [];
    return text.split('\n').map(line => line.replace(/\t/g, '  '));
  };

  const downloadSpreadsheet = () => {
    if (!selectedApp) {
      showNotification('Please select an application first', 'error');
      return;
    }
    const appRules = rules.filter(r => String(r.app_id) === selectedApp);
    if (appRules.length === 0) {
      showNotification('No rules found for selected application', 'error');
      return;
    }
    const headers = ['App ID', 'App Current Distributed ID', 'App Name', 'Inventory Item', 'Policy Name', 'Rule Global', 'Rule Action', 'Rule Source', 'Rule Source Expanded', 'Rule Source Zone', 'Rule Destination', 'Rule Destination Expanded', 'Rule Destination Zone', 'Rule Service', 'Rule Service Expanded', 'RN', 'RC'];
    const rows = appRules.map(r => [
      r.app_id, r.app_distributed_id, r.app_name, r.inventory_item, r.policy_name,
      r.rule_global ? 'TRUE' : 'FALSE', r.rule_action, r.rule_source, r.rule_source_expanded,
      r.rule_source_zone, r.rule_destination, r.rule_destination_expanded,
      r.rule_destination_zone, r.rule_service, r.rule_service_expanded, r.rn, r.rc
    ]);
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `firewall-rules-${selectedApp}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification('Spreadsheet downloaded', 'success');
  };

  const handleAddException = (data: { type: string; value: string; justification: string }) => {
    const newException = {
      id: `exc-${Date.now()}`,
      type: data.type as 'ip' | 'subnet',
      value: data.value,
      justification: data.justification,
      status: 'Pending' as const,
      requested_by: 'Current User',
      requested_at: new Date().toISOString(),
    };
    setExceptions(prev => [...prev, newException]);
    showNotification('Exception submitted for approval', 'success');
  };

  const handleApproveException = (id: string) => {
    setExceptions(prev => prev.map(e => e.id === id ? { ...e, status: 'Approved' as const } : e));
    showNotification('Exception approved', 'success');
  };

  const handleRejectException = (id: string) => {
    setExceptions(prev => prev.map(e => e.id === id ? { ...e, status: 'Rejected' as const } : e));
    showNotification('Exception rejected', 'info');
  };

  const columns: Column<LegacyRule>[] = [
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
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_source_zone', header: 'Src Zone', sortable: true, width: '100px' },
    {
      key: 'rule_destination', header: 'Destination', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_destination || '').split('\n').filter(Boolean);
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_destination_zone', header: 'Dst Zone', sortable: true, width: '90px' },
    {
      key: 'rule_service', header: 'Service', sortable: false, width: '100px',
      render: (_, row) => <span className="text-xs">{row.rule_service || 'N/A'}</span>,
    },
    {
      key: 'is_standard', header: 'Standard', sortable: true, width: '90px',
      render: (_, row) => (
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${row.is_standard ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {row.is_standard ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      key: '_actions', header: 'Actions', width: '80px', sortable: false,
      render: (_, row) => (
        <button onClick={(e) => { e.stopPropagation(); detailModal.open(row); }} className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">View</button>
      ),
    },
  ];

  const tabs = [
    { id: 'all', label: `All Rules (${rules.length})` },
    { id: 'standard', label: `Standard (${standardCount})` },
    { id: 'non_standard', label: `Non-Standard (${nonStandardCount})` },
  ];

  return (
    <div className="p-6 max-w-[1800px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Firewall Management</h1>
          <p className="text-sm text-gray-500 mt-1">Manage legacy/existing firewall rules, generate output per application, handle exceptions</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedApp}
            onChange={e => setSelectedApp(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Applications</option>
            {appOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button
            onClick={downloadSpreadsheet}
            disabled={!selectedApp}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 shadow-sm"
          >
            Export Spreadsheet
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Rules', value: rules.length, color: 'from-slate-100 to-slate-200 text-slate-800' },
          { label: 'Standard', value: standardCount, color: 'from-green-100 to-green-200 text-green-800' },
          { label: 'Non-Standard', value: nonStandardCount, color: 'from-red-100 to-red-200 text-red-800' },
          { label: 'Exceptions', value: exceptions.length, color: 'from-amber-100 to-amber-200 text-amber-800' },
        ].map(card => (
          <div key={card.label} className={`p-4 rounded-lg bg-gradient-to-br ${card.color}`}>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="text-sm font-medium mt-1">{card.label}</div>
          </div>
        ))}
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={filteredRules}
            keyField="id"
            defaultPageSize={15}
            emptyMessage="No rules found"
            searchPlaceholder="Search by IP, group, app, rule ID, zone, service..."
            searchFields={['id', 'app_id', 'app_distributed_id', 'app_name', 'rule_source', 'rule_source_expanded', 'rule_destination', 'rule_destination_expanded', 'rule_source_zone', 'rule_destination_zone', 'rule_service', 'inventory_item']}
            onRowClick={(row) => detailModal.open(row)}
          />
        )}
      </div>

      {/* Exceptions Section */}
      <div className="mt-8 p-4 bg-white border border-gray-200 rounded-lg">
        <ExceptionHandler
          ruleId={detailModal.data?.id || ''}
          appId={selectedApp || 'all'}
          exceptions={exceptions}
          onAddException={handleAddException}
          onApproveException={handleApproveException}
          onRejectException={handleRejectException}
        />
      </div>

      {/* Rule Detail Modal with Expanded IPs */}
      <Modal isOpen={detailModal.isOpen} onClose={detailModal.close} title={`Rule: ${detailModal.data?.id || ''}`} size="xl">
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
                ['Standard', detailModal.data.is_standard ? 'Yes' : 'No'],
                ['RN', String(detailModal.data.rn)],
                ['RC', String(detailModal.data.rc)],
              ] as [string, string][]).map(([label, val]) => (
                <div key={label} className="p-2 bg-gray-50 rounded">
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-sm font-medium text-gray-800 break-all">{val}</p>
                </div>
              ))}
            </div>

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
          </div>
        )}
      </Modal>
    </div>
  );
}
