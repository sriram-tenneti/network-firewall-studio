import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { ExceptionHandler } from '@/components/design-studio/ExceptionHandler';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import { getRules, getApplications, compileRule } from '@/lib/api';
import type { FirewallRule, Application, CompiledRule } from '@/types';
import type { Column } from '@/components/shared/DataTable';

export default function FirewallManagementPage() {
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const { notification, showNotification, clearNotification } = useNotification();
  const detailModal = useModal<FirewallRule>();
  const outputModal = useModal<{ app: string; rules: FirewallRule[]; compiled: CompiledRule[] }>();
  const [exceptions, setExceptions] = useState<Array<{id: string; type: 'ip' | 'subnet'; value: string; justification: string; status: 'Pending' | 'Approved' | 'Rejected'; requested_by: string; requested_at: string}>>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, appsData] = await Promise.all([getRules(selectedApp || undefined), getApplications()]);
      setRules(rulesData);
      setApplications(appsData);
    } catch {
      showNotification('Failed to load data', 'error');
    }
    setLoading(false);
  }, [selectedApp]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = rules.filter(r => {
    if (activeTab === 'non_standard') return r.compliance && !r.compliance.naming_valid;
    if (activeTab === 'standard') return r.compliance && r.compliance.naming_valid;
    return true;
  });

  const generateOutput = async () => {
    if (!selectedApp) {
      showNotification('Please select an application first', 'error');
      return;
    }
    const appRules = rules.filter(r => r.application === selectedApp);
    if (appRules.length === 0) {
      showNotification('No rules found for selected application', 'error');
      return;
    }
    try {
      const compiledResults = await Promise.all(
        appRules.slice(0, 10).map(r => compileRule(r.rule_id, 'generic').catch(() => null))
      );
      const validCompiled = compiledResults.filter((c): c is CompiledRule => c !== null);
      outputModal.open({ app: selectedApp, rules: appRules, compiled: validCompiled });
    } catch {
      showNotification('Failed to compile rules', 'error');
    }
  };

  const downloadOutput = (data: { app: string; rules: FirewallRule[]; compiled: CompiledRule[] }) => {
    const lines = [
      `# Firewall Rules Output - ${data.app}`,
      `# Generated: ${new Date().toISOString()}`,
      `# Total Rules: ${data.rules.length}`,
      '',
      '## Rules Summary',
      ...data.rules.map(r => `${r.rule_id} | ${r.source.group_name || r.source.ip_address || r.source.cidr || 'N/A'} -> ${r.destination.name} | ${r.status}`),
      '',
      '## Compiled Policies',
      ...data.compiled.map(c => `\n--- ${c.rule_id} (${c.vendor_format}) ---\n${c.compiled_text}`),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `firewall-rules-${data.app}-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
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

  const standardCount = rules.filter(r => r.compliance?.naming_valid).length;
  const nonStandardCount = rules.filter(r => r.compliance && !r.compliance.naming_valid).length;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const columns: Column<any>[] = [
    { key: 'rule_id', header: 'Rule ID', sortable: true, width: '100px' },
    { key: 'application', header: 'Application', sortable: true, width: '120px' },
    {
      key: 'source', header: 'Source', width: '180px',
      render: (_, row) => <span className="text-xs font-mono">{row.source.group_name || row.source.ip_address || row.source.cidr || 'N/A'}</span>,
    },
    {
      key: 'destination', header: 'Destination', width: '180px',
      render: (_, row) => <span className="text-xs font-mono">{row.destination.name}</span>,
    },
    {
      key: 'compliance', header: 'Compliance', width: '120px',
      render: (_, row) => (
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${row.compliance?.naming_valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {row.compliance?.naming_valid ? 'Standard' : 'Non-Standard'}
        </span>
      ),
    },
    {
      key: 'status', header: 'Status', sortable: true, width: '100px',
      render: (_, row) => <span className="text-xs capitalize">{row.status}</span>,
    },
    {
      key: 'actions', header: 'Actions', width: '80px',
      render: (_, row) => (
        <button onClick={() => detailModal.open(row)} className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">View</button>
      ),
    },
  ];

  const tabs = [
    { id: 'all', label: `All Rules (${rules.length})` },
    { id: 'standard', label: `Standard (${standardCount})` },
    { id: 'non_standard', label: `Non-Standard (${nonStandardCount})` },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Firewall Management</h1>
          <p className="text-sm text-gray-500 mt-1">Manage as-is rules, generate output per application, handle exceptions</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedApp}
            onChange={e => setSelectedApp(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Applications</option>
            {applications.map(app => (
              <option key={app.app_id} value={app.app_id}>{app.name} ({app.app_id})</option>
            ))}
          </select>
          <button
            onClick={generateOutput}
            disabled={!selectedApp}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 shadow-sm"
          >
            Generate Output
          </button>
        </div>
      </div>

      {/* Summary cards */}
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
          <DataTable columns={columns} data={filteredRules} keyField="rule_id" defaultPageSize={15} emptyMessage="No rules found" />
        )}
      </div>

      {/* Exceptions Section */}
      <div className="mt-8 p-4 bg-white border border-gray-200 rounded-lg">
        <ExceptionHandler
          ruleId={detailModal.data?.rule_id || ''}
          appId={selectedApp || 'all'}
          exceptions={exceptions}
          onAddException={handleAddException}
          onApproveException={handleApproveException}
          onRejectException={handleRejectException}
        />
      </div>

      {/* Rule Detail Modal */}
      <Modal isOpen={detailModal.isOpen} onClose={detailModal.close} title={`Rule: ${detailModal.data?.rule_id || ''}`} size="lg">
        {detailModal.data && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Application', detailModal.data.application],
                ['Environment', detailModal.data.environment],
                ['Source', detailModal.data.source.group_name || detailModal.data.source.ip_address || detailModal.data.source.cidr || 'N/A'],
                ['Destination', detailModal.data.destination.name],
                ['Status', detailModal.data.status],
                ['Compliance', detailModal.data.compliance?.naming_valid ? 'Standard' : 'Non-Standard'],
              ].map(([label, val]) => (
                <div key={String(label)} className="p-2 bg-gray-50 rounded">
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-sm font-medium text-gray-800">{String(val)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* Output Modal */}
      <Modal isOpen={outputModal.isOpen} onClose={outputModal.close} title={`Generated Output - ${outputModal.data?.app || ''}`} size="xl">
        {outputModal.data && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                <strong>{outputModal.data.rules.length}</strong> rules | <strong>{outputModal.data.compiled.length}</strong> compiled policies
              </p>
              <button
                onClick={() => outputModal.data && downloadOutput(outputModal.data)}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
              >
                Download Output
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {outputModal.data.compiled.map(c => (
                <div key={c.rule_id} className="mb-3 p-3 bg-gray-900 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400 font-medium">{c.rule_id} ({c.vendor_format})</span>
                    <button onClick={() => navigator.clipboard.writeText(c.compiled_text)} className="text-xs text-blue-400 hover:text-blue-300">Copy</button>
                  </div>
                  <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{c.compiled_text}</pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
