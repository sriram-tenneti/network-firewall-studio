import { useState, useEffect, useCallback } from 'react';
import { ArrowRight, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { ActionBar } from '@/components/layout/ActionBar';
import type { LegacyRule, Application, NGDCDataCenter } from '@/types';
import * as api from '@/lib/api';

export function MigrationStudioPage() {
  const [legacyRules, setLegacyRules] = useState<LegacyRule[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [ngdcDCs, setNgdcDCs] = useState<NGDCDataCenter[]>([]);
  const [selectedAppId, setSelectedAppId] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type }); setTimeout(() => setNotification(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      const [apps, dcs, rules] = await Promise.all([api.getApplications(), api.getNGDCDatacenters(), api.getLegacyRules()]);
      setApplications(apps); setNgdcDCs(dcs); setLegacyRules(rules);
    } catch (err) { console.error('Failed to load data:', err); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = legacyRules
    .filter(r => !selectedAppId || r.app_id === selectedAppId)
    .filter(r => filterStatus === 'all' || r.migration_status === filterStatus);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  };
  const toggleSelectAll = () => {
    if (selectedIds.size === filteredRules.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(filteredRules.map(r => r.id)));
  };

  const handleBulkMigrate = async () => {
    let count = 0;
    for (const id of selectedIds) {
      try { await api.updateLegacyRule(id, { migration_status: 'In Progress' }); count++; } catch { /* skip */ }
    }
    showNotification(`${count} rule(s) moved to In Progress`); setSelectedIds(new Set()); loadData();
  };
  const handleBulkComplete = async () => {
    let count = 0;
    for (const id of selectedIds) {
      try { await api.updateLegacyRule(id, { migration_status: 'Completed' }); count++; } catch { /* skip */ }
    }
    showNotification(`${count} rule(s) marked as Completed`); setSelectedIds(new Set()); loadData();
  };
  const handleBulkReview = async () => {
    let count = 0;
    for (const id of selectedIds) {
      try { await api.updateLegacyRule(id, { migration_status: 'Needs Review' }); count++; } catch { /* skip */ }
    }
    showNotification(`${count} rule(s) marked for Review`); setSelectedIds(new Set()); loadData();
  };

  const statusIcon = (status: string) => {
    if (status === 'Completed') return <CheckCircle className="h-3.5 w-3.5 text-green-600" />;
    if (status === 'Needs Review') return <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />;
    if (status === 'Not Started') return <XCircle className="h-3.5 w-3.5 text-slate-400" />;
    return <ArrowRight className="h-3.5 w-3.5 text-blue-600" />;
  };

  const statusCounts = { total: legacyRules.filter(r => !selectedAppId || r.app_id === selectedAppId).length,
    notStarted: legacyRules.filter(r => (!selectedAppId || r.app_id === selectedAppId) && r.migration_status === 'Not Started').length,
    inProgress: legacyRules.filter(r => (!selectedAppId || r.app_id === selectedAppId) && r.migration_status === 'In Progress').length,
    completed: legacyRules.filter(r => (!selectedAppId || r.app_id === selectedAppId) && r.migration_status === 'Completed').length,
    needsReview: legacyRules.filter(r => (!selectedAppId || r.app_id === selectedAppId) && r.migration_status === 'Needs Review').length,
  };

  void ngdcDCs;

  return (
    <div className="flex flex-col h-full">
      <ActionBar mode="migration" />

      {notification && (
        <div className={`mx-6 mt-3 rounded-lg px-4 py-2.5 text-sm font-medium shadow-sm ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
          notification.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>{notification.message}</div>
      )}

      {/* Filter Bar */}
      <div className="flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">App Distributed ID</label>
          <select value={selectedAppId} onChange={(e) => { setSelectedAppId(e.target.value); setSelectedIds(new Set()); }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium w-56">
            <option value="">All Applications</option>
            {applications.map(app => (<option key={app.app_id} value={app.app_id}>{app.app_distributed_id || app.app_id} - {app.name}</option>))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">Migration Status</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium">
            <option value="all">All Statuses</option>
            <option value="Not Started">Not Started</option><option value="In Progress">In Progress</option>
            <option value="Mapped">Mapped</option><option value="Needs Review">Needs Review</option><option value="Completed">Completed</option>
          </select>
        </div>
        <div className="ml-auto text-xs text-slate-500">{filteredRules.length} legacy rule(s)</div>
      </div>

      {/* Status Summary Cards */}
      <div className="grid grid-cols-5 gap-3 px-6 py-3 bg-slate-50 border-b border-slate-200">
        <div className="rounded-lg bg-white border border-slate-200 px-3 py-2 text-center">
          <div className="text-lg font-bold text-slate-800">{statusCounts.total}</div><div className="text-xs text-slate-500">Total</div></div>
        <div className="rounded-lg bg-white border border-slate-200 px-3 py-2 text-center">
          <div className="text-lg font-bold text-slate-400">{statusCounts.notStarted}</div><div className="text-xs text-slate-500">Not Started</div></div>
        <div className="rounded-lg bg-white border border-blue-200 px-3 py-2 text-center">
          <div className="text-lg font-bold text-blue-600">{statusCounts.inProgress}</div><div className="text-xs text-slate-500">In Progress</div></div>
        <div className="rounded-lg bg-white border border-amber-200 px-3 py-2 text-center">
          <div className="text-lg font-bold text-amber-600">{statusCounts.needsReview}</div><div className="text-xs text-slate-500">Needs Review</div></div>
        <div className="rounded-lg bg-white border border-green-200 px-3 py-2 text-center">
          <div className="text-lg font-bold text-green-600">{statusCounts.completed}</div><div className="text-xs text-slate-500">Completed</div></div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 border-b border-blue-200 bg-blue-50 px-6 py-2">
          <span className="text-sm font-semibold text-blue-800">{selectedIds.size} rule(s) selected</span>
          <button onClick={handleBulkMigrate} className="rounded-md bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700">Start Migration</button>
          <button onClick={handleBulkComplete} className="rounded-md bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700">Mark Complete</button>
          <button onClick={handleBulkReview} className="rounded-md bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-700">Flag for Review</button>
          <button onClick={() => setSelectedIds(new Set())} className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50">Clear Selection</button>
        </div>
      )}

      {/* Legacy Rules Table */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-3 py-2.5 text-left"><input type="checkbox" checked={selectedIds.size === filteredRules.length && filteredRules.length > 0} onChange={toggleSelectAll} className="rounded border-slate-300" /></th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Rule Name</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">App Dist ID</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Source Zone</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Source Entries</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Destination</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Ports</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Standard</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Migration Status</th>
                  <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Suggested Name</th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.length === 0 ? (
                  <tr><td colSpan={10} className="px-6 py-12 text-center text-sm text-slate-400">No legacy rules found. Select an application or adjust filters.</td></tr>
                ) : filteredRules.map(rule => (
                  <tr key={rule.id} className={`border-b border-slate-50 transition-colors cursor-pointer ${selectedIds.has(rule.id) ? 'bg-blue-50/50' : 'hover:bg-slate-50/50'}`}>
                    <td className="px-3 py-2"><input type="checkbox" checked={selectedIds.has(rule.id)} onChange={() => toggleSelect(rule.id)} className="rounded border-slate-300" /></td>
                    <td className="px-3 py-2">
                      <button onClick={() => setExpandedId(expandedId === rule.id ? null : rule.id)} className="text-left">
                        <div className="text-xs font-semibold text-slate-800">{rule.rule_name}</div>
                        <div className="text-xs text-slate-400">{rule.inventory}</div>
                      </button>
                    </td>
                    <td className="px-3 py-2 text-xs font-medium text-slate-700">{rule.app_distributed_id}</td>
                    <td className="px-3 py-2 text-xs text-slate-600">{rule.source_zone}</td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {rule.source_entries.slice(0, 2).map((s, i) => (<span key={i} className="mr-1 rounded bg-blue-50 border border-blue-200 px-1.5 py-0.5 text-blue-700 text-xs">{s}</span>))}
                      {rule.source_entries.length > 2 && <span className="text-xs text-slate-400">+{rule.source_entries.length - 2}</span>}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {rule.destination_entries.slice(0, 2).map((d, i) => (<span key={i} className="mr-1 rounded bg-orange-50 border border-orange-200 px-1.5 py-0.5 text-orange-700 text-xs">{d}</span>))}
                      {rule.destination_entries.length > 2 && <span className="text-xs text-slate-400">+{rule.destination_entries.length - 2}</span>}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">{rule.ports.join(', ')}</td>
                    <td className="px-3 py-2">{rule.is_standard
                      ? <span className="rounded-full bg-green-100 border border-green-300 px-2 py-0.5 text-xs font-medium text-green-700">Yes</span>
                      : <span className="rounded-full bg-red-100 border border-red-300 px-2 py-0.5 text-xs font-medium text-red-700">No</span>}</td>
                    <td className="px-3 py-2"><div className="flex items-center gap-1.5">{statusIcon(rule.migration_status)}<span className="text-xs font-medium text-slate-700">{rule.migration_status}</span></div></td>
                    <td className="px-3 py-2 text-xs text-slate-500 font-mono">{rule.suggested_standard_name || '-'}</td>
                  </tr>
                ))}
                {/* Expanded Detail Row */}
                {expandedId && filteredRules.filter(r => r.id === expandedId).map(rule => (
                  <tr key={`detail-${rule.id}`} className="bg-slate-50">
                    <td colSpan={10} className="px-6 py-4">
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <h4 className="text-xs font-bold text-slate-700 mb-2">Current (Non-Standard)</h4>
                          <div className="space-y-1 text-xs text-slate-600">
                            <div><span className="font-medium">Rule:</span> {rule.rule_name}</div>
                            <div><span className="font-medium">Policy Row:</span> {rule.policy_row}</div>
                            <div><span className="font-medium">Action:</span> {rule.rule_action}</div>
                            <div><span className="font-medium">Sources:</span> {rule.source_entries.join(', ')}</div>
                            <div><span className="font-medium">Expanded IPs:</span> {rule.source_expanded.join(', ')}</div>
                            <div><span className="font-medium">Destinations:</span> {rule.destination_entries.join(', ')}</div>
                            <div><span className="font-medium">Expanded Dest:</span> {rule.destination_expanded.join(', ')}</div>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-green-700 mb-2">Suggested Standard Mapping</h4>
                          <div className="space-y-1 text-xs text-slate-600">
                            <div><span className="font-medium">Standard Name:</span> <span className="font-mono text-green-700">{rule.suggested_standard_name || 'Pending analysis'}</span></div>
                            <div><span className="font-medium">Naming Convention:</span> grp-{'{AppID}'}-{'{NH}'}-{'{SZ}'}-{'{Subtype}'}</div>
                            <div className="flex items-center gap-2 pt-2">
                              <ArrowRight className="h-4 w-4 text-green-600" />
                              <span className="font-medium text-green-700">Map source entries into standardized group with proper naming</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
