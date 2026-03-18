import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { ExceptionHandler } from '@/components/design-studio/ExceptionHandler';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import { getLegacyRules, createRuleModification, compileLegacyRule, getGroups, checkDuplicates } from '@/lib/api';
import type { LegacyRule, CompiledRule, RuleDelta, FirewallGroup } from '@/types';
import type { Column } from '@/components/shared/DataTable';

interface ModifyState {
  rule_source: string;
  rule_destination: string;
  rule_service: string;
  rule_source_expanded: string;
  rule_destination_expanded: string;
  rule_service_expanded: string;
  rule_source_zone: string;
  rule_destination_zone: string;
  rule_action: string;
}

function DeltaView({ delta }: { delta: RuleDelta }) {
  const hasAdded = Object.keys(delta.added).length > 0;
  const hasRemoved = Object.keys(delta.removed).length > 0;
  const hasChanged = Object.keys(delta.changed).length > 0;
  if (!hasAdded && !hasRemoved && !hasChanged) {
    return <p className="text-sm text-gray-500 italic">No changes detected</p>;
  }
  return (
    <div className="space-y-3">
      {hasAdded && (
        <div>
          <h4 className="text-xs font-semibold text-green-700 mb-1">Added</h4>
          {Object.entries(delta.added).map(([field, values]) => (
            <div key={field} className="ml-2">
              <span className="text-xs text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
              {values.map((v, i) => (
                <div key={i} className="text-xs text-green-700 font-mono ml-2">+ {v}</div>
              ))}
            </div>
          ))}
        </div>
      )}
      {hasRemoved && (
        <div>
          <h4 className="text-xs font-semibold text-red-700 mb-1">Removed</h4>
          {Object.entries(delta.removed).map(([field, values]) => (
            <div key={field} className="ml-2">
              <span className="text-xs text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
              {values.map((v, i) => (
                <div key={i} className="text-xs text-red-700 font-mono ml-2">- {v}</div>
              ))}
            </div>
          ))}
        </div>
      )}
      {hasChanged && (
        <div>
          <h4 className="text-xs font-semibold text-blue-700 mb-1">Changed</h4>
          {Object.entries(delta.changed).map(([field, change]) => (
            <div key={field} className="ml-2 text-xs">
              <span className="text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
              <span className="text-red-600 line-through ml-1">{change.from}</span>
              <span className="mx-1">{'->'}</span>
              <span className="text-green-600">{change.to}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function computeLocalDelta(original: ModifyState, modified: ModifyState): RuleDelta {
  const delta: RuleDelta = { added: {}, removed: {}, changed: {} };
  const fields = Object.keys(original) as (keyof ModifyState)[];
  for (const field of fields) {
    const origVal = original[field] || '';
    const modVal = modified[field] || '';
    if (origVal !== modVal) {
      if (origVal.includes('\n') || modVal.includes('\n')) {
        const origLines = new Set(origVal.split('\n').filter(Boolean));
        const modLines = new Set(modVal.split('\n').filter(Boolean));
        const added = [...modLines].filter(l => !origLines.has(l));
        const removed = [...origLines].filter(l => !modLines.has(l));
        if (added.length) delta.added[field] = added;
        if (removed.length) delta.removed[field] = removed;
      } else {
        delta.changed[field] = { from: origVal, to: modVal };
      }
    }
  }
  return delta;
}

function FieldEditor({ label, value, onChange, onAddLine, onRemoveLine, appGroups }: {
  label: string; value: string;
  onChange: (v: string) => void; onAddLine: (v: string) => void; onRemoveLine: (v: string) => void;
  appGroups?: FirewallGroup[];
}) {
  const [newEntry, setNewEntry] = useState('');
  const lines = value.split('\n').filter(Boolean);
  return (
    <div className="border rounded-lg p-3">
      <label className="block text-xs font-semibold text-gray-700 mb-2">{label}</label>
      <div className="space-y-1 mb-2 max-h-40 overflow-y-auto">
        {lines.map((line, i) => (
          <div key={i} className="flex items-center gap-2 bg-gray-50 rounded px-2 py-1">
            <span className="font-mono text-xs flex-1">{line}</span>
            <button onClick={() => onRemoveLine(line)} className="text-xs text-red-500 hover:text-red-700 font-medium">Remove</button>
          </div>
        ))}
        {lines.length === 0 && <p className="text-xs text-gray-400 italic">No entries</p>}
      </div>
      <div className="flex gap-2">
        <input type="text" value={newEntry} onChange={e => setNewEntry(e.target.value)} placeholder="Add IP, range, or group name" className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded-md" onKeyDown={e => { if (e.key === 'Enter') { onAddLine(newEntry); setNewEntry(''); } }} />
        <button onClick={() => { onAddLine(newEntry); setNewEntry(''); }} className="px-3 py-1 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700">Add</button>
      </div>
      {appGroups && appGroups.length > 0 && (
        <div className="mt-2">
          <label className="text-xs text-gray-500">App Groups:</label>
          <select onChange={e => { if (e.target.value) { onAddLine(e.target.value); e.target.value = ''; } }} className="ml-2 px-2 py-1 text-xs border border-gray-300 rounded-md" defaultValue="">
            <option value="">Select group...</option>
            {appGroups.map(g => <option key={g.name} value={g.name}>{g.name} ({g.members.length} members)</option>)}
          </select>
        </div>
      )}
      <textarea value={value} onChange={e => onChange(e.target.value)} className="w-full mt-2 px-2 py-1 text-xs font-mono border border-gray-200 rounded bg-gray-50 h-16 resize-none" placeholder="Or edit directly (one entry per line)" />
    </div>
  );
}

export default function FirewallManagementPage() {
  const [rules, setRules] = useState<LegacyRule[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const { notification, showNotification, clearNotification } = useNotification();
  const detailModal = useModal<LegacyRule>();
  const [modifyRule, setModifyRule] = useState<LegacyRule | null>(null);
  const [modifyState, setModifyState] = useState<ModifyState | null>(null);
  const [originalState, setOriginalState] = useState<ModifyState | null>(null);
  const [modifyComments, setModifyComments] = useState('');
  const [showDelta, setShowDelta] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [compiledRule, setCompiledRule] = useState<CompiledRule | null>(null);
  const [compileVendor, setCompileVendor] = useState('generic');
  const [compiling, setCompiling] = useState(false);
  const [appGroups, setAppGroups] = useState<FirewallGroup[]>([]);
  const [exceptions, setExceptions] = useState<Array<{id: string; type: 'ip' | 'subnet'; value: string; justification: string; status: 'Pending' | 'Approved' | 'Rejected'; requested_by: string; requested_at: string}>>([]);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedExportApps, setSelectedExportApps] = useState<Set<string>>(new Set());

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
    if (!selectedApp) { showNotification('Please select an application first', 'error'); return; }
    const appRules = rules.filter(r => String(r.app_id) === selectedApp);
    if (appRules.length === 0) { showNotification('No rules found for selected application', 'error'); return; }
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

  const openModifyModal = async (rule: LegacyRule) => {
    const state: ModifyState = {
      rule_source: rule.rule_source || '',
      rule_destination: rule.rule_destination || '',
      rule_service: rule.rule_service || '',
      rule_source_expanded: rule.rule_source_expanded || '',
      rule_destination_expanded: rule.rule_destination_expanded || '',
      rule_service_expanded: rule.rule_service_expanded || '',
      rule_source_zone: rule.rule_source_zone || '',
      rule_destination_zone: rule.rule_destination_zone || '',
      rule_action: rule.rule_action || '',
    };
    setModifyRule(rule);
    setModifyState({ ...state });
    setOriginalState({ ...state });
    setModifyComments('');
    setShowDelta(false);
    setCompiledRule(null);
    try {
      const groups = await getGroups(String(rule.app_id));
      setAppGroups(groups);
    } catch {
      setAppGroups([]);
    }
  };

  const closeModifyModal = () => {
    setModifyRule(null);
    setModifyState(null);
    setOriginalState(null);
    setShowDelta(false);
    setAppGroups([]);
  };

  const handleModifyField = (field: keyof ModifyState, value: string) => {
    if (!modifyState) return;
    setModifyState({ ...modifyState, [field]: value });
  };

  const addLineToField = (field: keyof ModifyState, value: string) => {
    if (!modifyState || !value.trim()) return;
    const current = modifyState[field] || '';
    const lines = current.split('\n').filter(Boolean);
    if (!lines.includes(value.trim())) {
      lines.push(value.trim());
      setModifyState({ ...modifyState, [field]: lines.join('\n') });
    }
  };

  const removeLineFromField = (field: keyof ModifyState, lineToRemove: string) => {
    if (!modifyState) return;
    const current = modifyState[field] || '';
    const lines = current.split('\n').filter(l => l.trim() !== lineToRemove.trim());
    setModifyState({ ...modifyState, [field]: lines.join('\n') });
  };

  const handleSubmitModification = async () => {
    if (!modifyRule || !modifyState) return;
    setSubmitting(true);
    try {
      await createRuleModification(modifyRule.id, modifyState as unknown as Record<string, string>, modifyComments);
      showNotification('Modification submitted for review', 'success');
      closeModifyModal();
      loadData();
    } catch {
      showNotification('Failed to submit modification', 'error');
    }
    setSubmitting(false);
  };

  const handleCompile = async (ruleId: string) => {
    setCompiling(true);
    try {
      const result = await compileLegacyRule(ruleId, compileVendor);
      setCompiledRule(result);
    } catch {
      showNotification('Failed to compile rule', 'error');
    }
    setCompiling(false);
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

  // Duplicate detection (Req 10)
  const handleCheckDuplicates = async (rule: LegacyRule) => {
    try {
      const result = await checkDuplicates(rule.rule_source, rule.rule_destination, rule.rule_service, rule.id);
      if (result.count > 0) {
        showNotification(`Found ${result.count} duplicate(s) on source+destination+service`, 'error');
      } else {
        showNotification('No duplicates found', 'success');
      }
    } catch { showNotification('Failed to check duplicates', 'error'); }
  };

  // Per-rule export: export the rule + all rules under that App ID
  const handleExportRuleApp = (rule: LegacyRule) => {
    const appRules = rules.filter(r => String(r.app_id) === String(rule.app_id));
    if (appRules.length === 0) { showNotification('No rules found for this app', 'error'); return; }
    exportRulesToCSV(appRules, String(rule.app_id));
  };

  // Multi-app export with selection
  const handleMultiAppExport = () => {
    if (selectedExportApps.size === 0) { showNotification('Select at least one app to export', 'error'); return; }
    const exportRules = rules.filter(r => selectedExportApps.has(String(r.app_id)));
    exportRulesToCSV(exportRules, Array.from(selectedExportApps).join('-'));
    setShowExportModal(false);
  };

  const exportRulesToCSV = (exportRules: LegacyRule[], fileLabel: string) => {
    const headers = ['App ID', 'App Current Distributed ID', 'App Name', 'Inventory Item', 'Policy Name', 'Rule Global', 'Rule Action', 'Rule Source', 'Rule Source Expanded', 'Rule Source Zone', 'Rule Destination', 'Rule Destination Expanded', 'Rule Destination Zone', 'Rule Service', 'Rule Service Expanded', 'RN', 'RC'];
    const rows = exportRules.map(r => [
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
    a.download = `firewall-rules-${fileLabel}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification('Spreadsheet exported', 'success');
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
    { key: 'rule_source', header: 'Source', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_source || '').split('\n').filter(Boolean);
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_source_zone', header: 'Src Zone', sortable: true, width: '100px' },
    { key: 'rule_destination', header: 'Destination', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_destination || '').split('\n').filter(Boolean);
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_destination_zone', header: 'Dst Zone', sortable: true, width: '90px' },
    { key: 'rule_service', header: 'Service', sortable: false, width: '100px',
      render: (_, row) => <span className="text-xs">{row.rule_service || 'N/A'}</span>,
    },
    { key: 'is_standard', header: 'Std', sortable: true, width: '60px',
      render: (_, row) => (
        <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${row.is_standard ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {row.is_standard ? 'Y' : 'N'}
        </span>
      ),
    },
    { key: '_actions', header: 'Actions', width: '120px', sortable: false,
      render: (_, row) => (
        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
          <button onClick={() => detailModal.open(row)} className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">View</button>
          <button onClick={() => openModifyModal(row)} className="text-xs text-orange-600 hover:text-orange-800 font-medium">Modify</button>
          <button onClick={() => handleCheckDuplicates(row)} className="text-xs text-amber-600 hover:text-amber-800 font-medium">Dup?</button>
          <button onClick={() => handleExportRuleApp(row)} className="text-xs text-teal-600 hover:text-teal-800 font-medium">Export</button>
        </div>
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
          <p className="text-sm text-gray-500 mt-1">View and modify imported legacy rules, generate output per application, handle exceptions</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={selectedApp} onChange={e => setSelectedApp(e.target.value)} className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">All Applications</option>
            {appOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button onClick={() => setShowExportModal(true)} className="px-4 py-2 text-sm font-medium text-teal-700 bg-teal-50 border border-teal-200 rounded-lg hover:bg-teal-100">
            Export (Multi-App)
          </button>
          <button onClick={downloadSpreadsheet} disabled={!selectedApp} className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 shadow-sm">
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
            emptyMessage="No rules found. Import rules via Data Import page."
            searchPlaceholder="Search by IP, group, app, rule ID, zone, service..."
            searchFields={['id', 'app_id', 'app_distributed_id', 'app_name', 'rule_source', 'rule_source_expanded', 'rule_destination', 'rule_destination_expanded', 'rule_source_zone', 'rule_destination_zone', 'rule_service', 'inventory_item']}
            onRowClick={(row) => detailModal.open(row)}
          />
        )}
      </div>

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

      {/* Multi-App Export Modal */}
      <Modal isOpen={showExportModal} onClose={() => setShowExportModal(false)} title="Export Rules - Select Applications" size="lg">
        <div className="space-y-4">
          <p className="text-xs text-gray-600">Select single, multiple, or all applications to export their rules as a spreadsheet with expanded groups.</p>
          <div className="flex items-center justify-between">
            <button onClick={() => {
              if (selectedExportApps.size === appOptions.length) setSelectedExportApps(new Set());
              else setSelectedExportApps(new Set(appOptions.map(a => a.value)));
            }} className="text-xs font-medium text-indigo-600 hover:text-indigo-800">
              {selectedExportApps.size === appOptions.length ? 'Deselect All' : 'Select All'}
            </button>
            <span className="text-xs text-gray-500">{selectedExportApps.size} selected</span>
          </div>
          <div className="grid grid-cols-3 gap-2 max-h-60 overflow-y-auto">
            {appOptions.map(app => (
              <label key={app.value} className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors ${selectedExportApps.has(app.value) ? 'bg-teal-100 border border-teal-300' : 'bg-white border border-gray-200 hover:bg-gray-50'}`}>
                <input type="checkbox" checked={selectedExportApps.has(app.value)} onChange={() => {
                  setSelectedExportApps(prev => { const n = new Set(prev); if (n.has(app.value)) n.delete(app.value); else n.add(app.value); return n; });
                }} className="rounded border-gray-300 text-teal-600" />
                {app.label}
              </label>
            ))}
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t">
            <button onClick={() => setShowExportModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleMultiAppExport} disabled={selectedExportApps.size === 0} className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 disabled:opacity-50">
              Export {selectedExportApps.size} App(s)
            </button>
          </div>
        </div>
      </Modal>

      {/* View Detail Modal */}
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
            <div className="flex gap-3 pt-2">
              <button onClick={() => { detailModal.close(); openModifyModal(detailModal.data!); }} className="px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded-md hover:bg-orange-700">
                Modify Rule
              </button>
              <button onClick={detailModal.close} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">Close</button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modify Rule Modal */}
      <Modal isOpen={!!modifyRule} onClose={closeModifyModal} title={`Modify Rule: ${modifyRule?.id || ''}`} size="xl">
        {modifyRule && modifyState && originalState && (
          <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-700">
                Modify source, destination, or service entries below. Add or remove individual IPs, ranges, or groups. Preview the delta before submitting for review.
              </p>
            </div>

            <FieldEditor label="Source" value={modifyState.rule_source} onChange={(v) => handleModifyField('rule_source', v)} onAddLine={(v) => addLineToField('rule_source', v)} onRemoveLine={(v) => removeLineFromField('rule_source', v)} appGroups={appGroups} />

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Source Zone</label>
              <input type="text" value={modifyState.rule_source_zone} onChange={e => handleModifyField('rule_source_zone', e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500" />
            </div>

            <FieldEditor label="Destination" value={modifyState.rule_destination} onChange={(v) => handleModifyField('rule_destination', v)} onAddLine={(v) => addLineToField('rule_destination', v)} onRemoveLine={(v) => removeLineFromField('rule_destination', v)} appGroups={appGroups} />

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Destination Zone</label>
              <input type="text" value={modifyState.rule_destination_zone} onChange={e => handleModifyField('rule_destination_zone', e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500" />
            </div>

            <FieldEditor label="Service" value={modifyState.rule_service} onChange={(v) => handleModifyField('rule_service', v)} onAddLine={(v) => addLineToField('rule_service', v)} onRemoveLine={(v) => removeLineFromField('rule_service', v)} />

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Rule Action</label>
              <select value={modifyState.rule_action} onChange={e => handleModifyField('rule_action', e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md">
                <option value="Accept">Accept</option>
                <option value="DROP">DROP</option>
                <option value="Reject">Reject</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Modification Comments</label>
              <textarea value={modifyComments} onChange={e => setModifyComments(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md h-16 resize-none" placeholder="Describe the reason for modification..." />
            </div>

            {/* Compile Option */}
            <div className="border rounded-lg p-3 bg-gray-50">
              <div className="flex items-center gap-2 mb-2">
                <label className="text-xs font-medium text-gray-700">Compile Rule:</label>
                <select value={compileVendor} onChange={e => setCompileVendor(e.target.value)} className="px-2 py-1 text-xs border border-gray-300 rounded-md">
                  <option value="generic">Generic</option>
                  <option value="palo_alto">Palo Alto</option>
                  <option value="checkpoint">Check Point</option>
                  <option value="cisco_asa">Cisco ASA</option>
                </select>
                <button onClick={() => handleCompile(modifyRule.id)} disabled={compiling} className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50">
                  {compiling ? 'Compiling...' : 'Compile'}
                </button>
              </div>
              {compiledRule && (
                <div className="bg-gray-900 rounded p-3 mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400">Format: {compiledRule.vendor_format}</span>
                    <button onClick={() => navigator.clipboard.writeText(compiledRule.compiled_text)} className="text-xs text-blue-400 hover:text-blue-300">Copy</button>
                  </div>
                  <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{compiledRule.compiled_text}</pre>
                </div>
              )}
            </div>

            {/* Delta Preview */}
            {!showDelta ? (
              <button onClick={() => setShowDelta(true)} className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 w-full">
                Preview Changes (Delta)
              </button>
            ) : (
              <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <h3 className="text-sm font-semibold text-blue-800 mb-2">Change Delta</h3>
                <DeltaView delta={computeLocalDelta(originalState, modifyState)} />
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2 border-t">
              <button onClick={closeModifyModal} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
              <button onClick={handleSubmitModification} disabled={submitting} className="px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded-md hover:bg-orange-700 disabled:opacity-50">
                {submitting ? 'Submitting...' : 'Submit for Review'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
