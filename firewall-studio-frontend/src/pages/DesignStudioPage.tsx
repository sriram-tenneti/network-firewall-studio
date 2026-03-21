import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
// RuleFormModal kept only for editing existing draft rules
import { RuleFormModal } from '@/components/design-studio/RuleFormModal';
import { RuleDetailModal } from '@/components/design-studio/RuleDetailModal';
import { RuleCompilerView } from '@/components/design-studio/RuleCompilerView';
import { GroupManagerModal } from '@/components/design-studio/GroupManagerModal';
import { RuleModifyModal } from '@/components/design-studio/RuleModifyModal';
import type { RuleModification } from '@/components/design-studio/RuleModifyModal';
import { DragDropRuleBuilder } from '@/components/design-studio/DragDropRuleBuilder';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import type { FirewallRule, Application } from '@/types';
import type { Column } from '@/components/shared/DataTable';
import * as api from '@/lib/api';

export function DesignStudioPage() {
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [selectedEnv, setSelectedEnv] = useState<string>('');
  const [activeTab, setActiveTab] = useState('All');
  const [viewMode, setViewMode] = useState<'table' | 'builder'>('table');

  const editModal = useModal<FirewallRule>();
  const detailModal = useModal<FirewallRule>();
  const modifyModal = useModal<FirewallRule>();
  const compilerModal = useModal<string>();
  const groupModal = useModal();
  const deleteConfirm = useModal<string>();
  const { notification, showNotification } = useNotification();

  // Auto-import result state
  const [autoImportResult, setAutoImportResult] = useState<{ imported: number; skipped_non_compliant: number } | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, appsData] = await Promise.all([
        api.getRules(),
        api.getApplications(),
      ]);
      setRules(rulesData);
      setApplications(appsData);
    } catch {
      showNotification('Failed to load data', 'error');
    }
    setLoading(false);
  }, [showNotification]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-import non-standard legacy rules from NFR on page load (silent)
  useEffect(() => {
    let mounted = true;
    const doAutoImport = async () => {
      try {
        const result = await api.autoImportCompliantToStudio();
        if (mounted && result.imported > 0) {
          setAutoImportResult({ imported: result.imported, skipped_non_compliant: result.skipped_non_compliant });
          loadData();
        }
      } catch { /* silent */ }
    };
    doAutoImport();
    return () => { mounted = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredRules = rules.filter(r => {
    if (r.status === 'Deleted') return false;
    if (selectedApp && r.application !== selectedApp) return false;
    if (selectedEnv && r.environment !== selectedEnv) return false;
    if (activeTab === 'All') return true;
    return r.status === activeTab;
  });

  const statusCounts = {
    All: rules.filter(r => r.status !== 'Deleted' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
    Draft: rules.filter(r => r.status === 'Draft' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
    'Pending Review': rules.filter(r => r.status === 'Pending Review' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
    Approved: rules.filter(r => r.status === 'Approved' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
    Deployed: rules.filter(r => r.status === 'Deployed' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
    Certified: rules.filter(r => r.status === 'Certified' && (!selectedApp || r.application === selectedApp) && (!selectedEnv || r.environment === selectedEnv)).length,
  };

  const handleEdit = async (data: Record<string, string | boolean>) => {
    if (!editModal.data) return;
    try {
      await api.updateRule(editModal.data.rule_id, data);
      showNotification('Rule updated successfully', 'success');
      loadData();
    } catch {
      showNotification('Failed to update rule', 'error');
    }
  };

  const handleModify = async (ruleId: string, changes: RuleModification) => {
    try {
      const srcValue = changes.source_entries.map(e => e.value).join(',');
      const dstValue = changes.destination_entries.map(e => e.value).join(',');
      await api.updateRule(ruleId, {
        source: { source_type: 'Group', ip_address: null, cidr: null, group_name: srcValue, ports: changes.ports, neighbourhood: null, security_zone: '' },
        destination: { name: dstValue, security_zone: '', dest_ip: null, ports: changes.ports, is_predefined: false },
      });
      showNotification('Rule modified successfully', 'success');
      loadData();
    } catch {
      showNotification('Failed to modify rule', 'error');
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm.data) return;
    try {
      await api.deleteRule(deleteConfirm.data);
      showNotification('Rule deleted', 'success');
      deleteConfirm.close();
      loadData();
    } catch {
      showNotification('Failed to delete rule', 'error');
    }
  };

  const handleSubmitReview = async (ruleId: string) => {
    try {
      await api.submitForReview(ruleId, 'Submitted for SNS review');
      showNotification('Rule submitted for review', 'success');
      detailModal.close();
      loadData();
    } catch {
      showNotification('Failed to submit for review', 'error');
    }
  };

  const handleCertify = async (ruleId: string) => {
    try {
      await api.certifyRule(ruleId);
      showNotification('Rule certified', 'success');
      loadData();
    } catch {
      showNotification('Failed to certify rule', 'error');
    }
  };



  function getSourceDisplay(rule: FirewallRule): string {
    if (typeof rule.source === 'string') return rule.source;
    if (rule.source && typeof rule.source === 'object') {
      const s = rule.source as unknown as Record<string, string>;
      return s.group_name || s.ip_address || s.cidr || '';
    }
    return '';
  }

  function getDestDisplay(rule: FirewallRule): string {
    if (typeof rule.destination === 'string') return rule.destination;
    if (rule.destination && typeof rule.destination === 'object') {
      const d = rule.destination as unknown as Record<string, string>;
      return d.name || d.dest_ip || '';
    }
    return '';
  }

  const columns: Column<FirewallRule>[] = [
    { key: 'rule_id', header: 'Rule ID', sortable: true, width: '100px' },
    { key: 'application', header: 'App ID', sortable: true, width: '90px' },
    {
      key: 'source', header: 'Source', sortable: false, width: '180px',
      render: (_, row) => <span className="font-mono text-xs truncate block">{getSourceDisplay(row)}</span>,
    },
    {
      key: 'destination', header: 'Destination', sortable: false, width: '180px',
      render: (_, row) => <span className="font-mono text-xs truncate block">{getDestDisplay(row)}</span>,
    },
    { key: 'environment', header: 'Environment', sortable: true, width: '110px' },
    {
      key: 'policy_result', header: 'Policy', sortable: true, width: '120px',
      render: (_, row) => row.policy_result ? <StatusBadge status={row.policy_result} /> : <span className="text-gray-400 text-xs">N/A</span>,
    },
    {
      key: 'status', header: 'Status', sortable: true, width: '120px',
      render: (_, row) => <StatusBadge status={row.status} />,
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '220px',
      render: (_, row) => (
        <div className="flex gap-1.5" onClick={e => e.stopPropagation()}>
          <button onClick={() => detailModal.open(row)} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">View</button>
          {row.status === 'Draft' && (
            <>
              <button onClick={() => editModal.open(row)} className="px-2 py-1 text-xs font-medium text-amber-700 bg-amber-50 rounded hover:bg-amber-100">Edit</button>
              <button onClick={() => handleSubmitReview(row.rule_id)} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100">Submit</button>
            </>
          )}
          {(row.status !== 'Deleted') && (
            <button onClick={() => modifyModal.open(row)} className="px-2 py-1 text-xs font-medium text-teal-700 bg-teal-50 rounded hover:bg-teal-100">modify</button>
          )}
          {(row.status === 'Approved' || row.status === 'Deployed') && (
            <button onClick={() => handleCertify(row.rule_id)} className="px-2 py-1 text-xs font-medium text-purple-700 bg-purple-50 rounded hover:bg-purple-100">Certify</button>
          )}
          {(row.status === 'Approved' || row.status === 'Deployed' || row.status === 'Certified') && (
            <button onClick={() => compilerModal.open(row.rule_id)} className="px-2 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 rounded hover:bg-indigo-100">Compile</button>
          )}
          {row.status === 'Draft' && (
            <button onClick={() => deleteConfirm.open(row.rule_id)} className="px-2 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100">Del</button>
          )}
        </div>
      ),
    },
  ];

  const tabs = [
    { id: 'All', label: 'All', count: statusCounts.All },
    { id: 'Draft', label: 'Draft', count: statusCounts.Draft },
    { id: 'Pending Review', label: 'Pending Review', count: statusCounts['Pending Review'] },
    { id: 'Approved', label: 'Approved', count: statusCounts.Approved },
    { id: 'Deployed', label: 'Deployed', count: statusCounts.Deployed },
    { id: 'Certified', label: 'Certified', count: statusCounts.Certified },
  ];

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      {/* Auto-import result banner */}
      {autoImportResult && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between">
          <span className="text-sm text-emerald-800">
            Auto-imported {autoImportResult.imported} NGDC-compliant rule(s) from Network Firewall Request.
            {autoImportResult.skipped_non_compliant > 0 && ` (${autoImportResult.skipped_non_compliant} non-compliant skipped)`}
          </span>
          <button onClick={() => setAutoImportResult(null)} className="text-xs text-emerald-600 hover:text-emerald-800">Dismiss</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Firewall Studio</h1>
          <p className="text-sm text-gray-500 mt-1">Create, manage, and compile firewall rules with NGDC compliance</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedApp}
            onChange={e => setSelectedApp(e.target.value)}
          >
            <option value="">All Applications</option>
            {applications.map(app => (
              <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
            ))}
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedEnv}
            onChange={e => setSelectedEnv(e.target.value)}
          >
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
          <button onClick={() => groupModal.open()} className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100">
            Manage Groups
          </button>
          <div className="flex items-center border border-gray-300 rounded-md overflow-hidden">
            <button onClick={() => setViewMode('table')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Table View</button>
            <button onClick={() => setViewMode('builder')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'builder' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Visual Builder</button>
          </div>
          <button onClick={() => setViewMode('builder')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm">
            + New Rule
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-6 gap-3 mb-6">
        {[
          { label: 'Total', value: statusCounts.All, color: 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800' },
          { label: 'Draft', value: statusCounts.Draft, color: 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-800' },
          { label: 'Pending', value: statusCounts['Pending Review'], color: 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-800' },
          { label: 'Approved', value: statusCounts.Approved, color: 'bg-gradient-to-br from-green-100 to-green-200 text-green-800' },
          { label: 'Deployed', value: statusCounts.Deployed, color: 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800' },
          { label: 'Certified', value: statusCounts.Certified, color: 'bg-gradient-to-br from-purple-100 to-purple-200 text-purple-800' },
        ].map(card => (
          <div key={card.label} className={`p-3 rounded-lg shadow-sm ${card.color}`}>
            <div className="text-xl font-bold">{card.value}</div>
            <div className="text-xs font-medium mt-0.5">{card.label}</div>
          </div>
        ))}
      </div>

      {viewMode === 'builder' ? (
        <div className="bg-white border rounded-lg shadow-sm p-4">
          <DragDropRuleBuilder applications={applications} onRuleCreated={loadData} />
        </div>
      ) : (
      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 pt-4">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
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
              keyField="rule_id"
              searchPlaceholder="Search by IP, group, app, rule ID..."
              searchFields={['rule_id', 'application', 'environment', 'source', 'destination']}
              onRowClick={(row) => detailModal.open(row)}
              emptyMessage="No firewall rules found"
              defaultPageSize={50}
            />
          )}
        </div>
      </div>
      )}

      {/* Modals */}
      <RuleFormModal isOpen={editModal.isOpen} onClose={editModal.close} onSave={handleEdit} rule={editModal.data} applications={applications} mode="edit" existingRules={rules} />

      <RuleDetailModal
        isOpen={detailModal.isOpen}
        onClose={detailModal.close}
        rule={detailModal.data}
        onEdit={() => { if (detailModal.data) { detailModal.close(); editModal.open(detailModal.data); } }}
        onCompile={() => { if (detailModal.data) { detailModal.close(); compilerModal.open(detailModal.data.rule_id); } }}
        onSubmitReview={() => { if (detailModal.data) { handleSubmitReview(detailModal.data.rule_id); } }}
      />

      <RuleModifyModal isOpen={modifyModal.isOpen} onClose={modifyModal.close} rule={modifyModal.data} onSave={handleModify} />
      <RuleCompilerView isOpen={compilerModal.isOpen} onClose={compilerModal.close} ruleId={compilerModal.data} />
      <GroupManagerModal isOpen={groupModal.isOpen} onClose={groupModal.close} appId={selectedApp || undefined} applications={applications.map(a => ({ app_id: a.app_id, name: a.name }))} environment={selectedEnv || undefined} />

      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        onClose={deleteConfirm.close}
        onConfirm={handleDelete}
        title="Delete Rule"
        message={`Are you sure you want to delete rule ${deleteConfirm.data}? This action cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
      />

    </div>
  );
}
