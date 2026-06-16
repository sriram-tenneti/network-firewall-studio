import { useCallback, useEffect, useMemo, useState } from 'react';
import type { RuleRequestRecord, Application } from '@/types';
import * as api from '@/lib/api';
import { useTeam } from '@/contexts/TeamContext';
import RuleRequestBuilder from '@/components/design-studio/RuleRequestBuilder';
import GroupChangeRequestBuilder from '@/components/design-studio/GroupChangeRequestBuilder';
import GroupChangeRequestsPanel from '@/components/design-studio/GroupChangeRequestsPanel';

const STATUSES = ['All', 'Pending', 'Approved', 'Rejected', 'Deployed', 'Certified'] as const;

export default function RequestHistoryPage() {
  const { team, isGodView } = useTeam();
  const [items, setItems] = useState<RuleRequestRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [envFilter, setEnvFilter] = useState<string>('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [showGroupRequest, setShowGroupRequest] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [groupReloadKey, setGroupReloadKey] = useState(0);
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, any>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reqs, apps] = await Promise.all([
        api.listRuleRequests({ environment: (envFilter as any) || undefined, team: isGodView ? undefined : team }),
        api.getApplications(isGodView ? undefined : { team }),
      ]);
      setItems(reqs);
      setApplications(apps);
    } catch (e) {
      setError((e as Error).message);
    }
    setLoading(false);
  }, [envFilter, team, isGodView]);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    if (statusFilter === 'All') return items;
    return items.filter(i => i.status === statusFilter);
  }, [items, statusFilter]);

  const handleStatusChange = async (requestId: string, newStatus: string) => {
    try {
      await api.setRuleRequestStatus(requestId, newStatus, note || undefined);
      setNote('');
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleValidate = async (requestId: string) => {
    setValidatingId(requestId);
    try {
      const res = await fetch(`/api/validation/request/${requestId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ live_check: true }),
      });
      const data = await res.json();
      setValidationResults(prev => ({ ...prev, [requestId]: data }));
    } catch (e) {
      setError(`Validation failed: ${(e as Error).message}`);
    }
    setValidatingId(null);
  };

  const handleExportXlsx = (requestId: string) => {
    window.open(`/api/rules/requests/${requestId}/export-xlsx`, '_blank');
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      {error && (
        <div className="mb-4 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">&times;</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Request History</h1>
          <p className="text-sm text-gray-500 mt-1">Track all rule requests and group change requests with full audit trail</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white"
            value={envFilter}
            onChange={e => setEnvFilter(e.target.value)}
          >
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
          <button
            onClick={() => { setShowNewRequest(true); setShowGroupRequest(false); }}
            className="px-4 py-2 text-sm font-medium text-white bg-rose-600 rounded-md hover:bg-rose-700"
          >
            + New Rule Request
          </button>
          <button
            onClick={() => { setShowGroupRequest(true); setShowNewRequest(false); }}
            className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100"
          >
            + Group Change
          </button>
        </div>
      </div>

      {/* New Rule Request Builder */}
      {showNewRequest && (
        <div className="mb-6 bg-white border rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-rose-800">New Rule Request</h3>
            <button onClick={() => setShowNewRequest(false)} className="text-gray-400 hover:text-gray-600">&times;</button>
          </div>
          <RuleRequestBuilder
            applications={applications as any}
            onSubmitted={() => { setShowNewRequest(false); load(); }}
          />
        </div>
      )}

      {/* Group Change Request Builder */}
      {showGroupRequest && (
        <div className="mb-6 bg-white border rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-purple-800">New Group Change Request</h3>
            <button onClick={() => setShowGroupRequest(false)} className="text-gray-400 hover:text-gray-600">&times;</button>
          </div>
          <GroupChangeRequestBuilder
            environment={envFilter}
            onSubmitted={() => { setShowGroupRequest(false); setGroupReloadKey(k => k + 1); load(); }}
          />
        </div>
      )}

      {/* Status filter tabs */}
      <div className="flex items-center gap-1 mb-4 border-b border-gray-200 pb-2">
        {STATUSES.map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 text-xs font-medium rounded-t-md transition-all ${
              statusFilter === s
                ? 'bg-rose-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {s} {s === 'All' ? `(${items.length})` : `(${items.filter(i => i.status === s).length})`}
          </button>
        ))}
      </div>

      {/* Rule Requests Table */}
      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 py-3 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">Rule Requests</h3>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-600" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">No rule requests found</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filtered.map(req => (
              <div key={req.request_id} id={`rule-request-row-${req.request_id}`} className="px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <button onClick={() => setExpanded(expanded === req.request_id ? null : req.request_id)} className="text-gray-400 hover:text-gray-600">
                      {expanded === req.request_id ? '▼' : '▶'}
                    </button>
                    <div>
                      <span className="font-mono text-xs text-gray-800">{req.request_id}</span>
                      <span className="ml-2 text-xs text-gray-500">{req.source_ref || req.application_ref} → {req.destination_ref || req.destination_kind}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      req.status === 'Approved' ? 'bg-green-100 text-green-800' :
                      req.status === 'Deployed' ? 'bg-blue-100 text-blue-800' :
                      req.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                      req.status === 'Certified' ? 'bg-purple-100 text-purple-800' :
                      'bg-amber-100 text-amber-800'
                    }`}>{req.status}</span>
                    <span className="text-xs text-gray-400">{req.environment}</span>
                    <span className="text-xs text-gray-400">{req.ports}</span>
                  </div>
                </div>

                {expanded === req.request_id && (
                  <div className="mt-3 ml-8 space-y-3">
                    {/* Expansion details */}
                    {req.expansion && req.expansion.length > 0 && (
                      <div className="bg-gray-50 rounded p-3">
                        <div className="text-xs font-medium text-gray-600 mb-2">Expanded Physical Rules ({req.expansion.length})</div>
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-gray-500 border-b">
                              <th className="text-left py-1">Rule ID</th>
                              <th className="text-left py-1">Source Group</th>
                              <th className="text-left py-1">Dest Group</th>
                              <th className="text-left py-1">Ports</th>
                              <th className="text-left py-1">DC</th>
                              <th className="text-left py-1">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {req.expansion.map((rule, idx) => (
                              <tr key={idx} className="border-b border-gray-100">
                                <td className="py-1 font-mono">{rule.rule_id}</td>
                                <td className="py-1 font-mono">{rule.src_group_ref}</td>
                                <td className="py-1 font-mono">{rule.dst_group_ref}</td>
                                <td className="py-1">{rule.ports}</td>
                                <td className="py-1">{rule.src_dc || rule.dst_dc || '-'}</td>
                                <td className="py-1">{rule.lifecycle_status || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {req.status === 'Pending' && (
                        <>
                          <button onClick={() => handleStatusChange(req.request_id!, 'Approved')} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100">Approve</button>
                          <button onClick={() => handleStatusChange(req.request_id!, 'Rejected')} className="px-2 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100">Reject</button>
                        </>
                      )}
                      {req.status === 'Approved' && (
                        <button onClick={() => handleStatusChange(req.request_id!, 'Deployed')} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Deploy</button>
                      )}
                      {req.status === 'Deployed' && (
                        <button onClick={() => handleStatusChange(req.request_id!, 'Certified')} className="px-2 py-1 text-xs font-medium text-purple-700 bg-purple-50 rounded hover:bg-purple-100">Certify</button>
                      )}
                      {/* Validate button — always available */}
                      <button
                        onClick={() => handleValidate(req.request_id!)}
                        disabled={validatingId === req.request_id}
                        className="px-2 py-1 text-xs font-medium text-teal-700 bg-teal-50 rounded hover:bg-teal-100 disabled:opacity-50"
                      >
                        {validatingId === req.request_id ? 'Validating...' : 'Validate'}
                      </button>
                      {/* Export XLSX */}
                      <button
                        onClick={() => handleExportXlsx(req.request_id!)}
                        className="px-2 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 rounded hover:bg-indigo-100"
                      >
                        Export XLSX
                      </button>
                    </div>

                    {/* Validation results inline */}
                    {validationResults[req.request_id!] && (
                      <div className="bg-teal-50 border border-teal-200 rounded p-3 mt-2">
                        <div className="text-xs font-medium text-teal-800 mb-1">
                          Validation Results — {validationResults[req.request_id!].pass_count} pass / {validationResults[req.request_id!].fail_count} fail
                        </div>
                        <div className="space-y-1">
                          {(validationResults[req.request_id!].results || []).slice(0, 10).map((r: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-2 text-xs">
                              <span className={`w-2 h-2 rounded-full ${
                                r.overall_verdict === 'REACHABLE' || r.overall_verdict === 'PERMIT' ? 'bg-green-500' :
                                r.overall_verdict === 'UNREACHABLE' || r.overall_verdict === 'DENY' ? 'bg-red-500' :
                                'bg-yellow-500'
                              }`} />
                              <span className="font-mono">{r.source} → {r.destination}:{r.ports}</span>
                              <span className="text-gray-500">{r.overall_verdict}</span>
                              {r.drift_detected && <span className="text-orange-600 font-semibold">DRIFT</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Note input for status changes */}
                    {(req.status === 'Pending' || req.status === 'Approved') && (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          placeholder="Add note (optional)..."
                          value={expanded === req.request_id ? note : ''}
                          onChange={e => setNote(e.target.value)}
                          className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded"
                        />
                      </div>
                    )}

                    {/* Timestamps */}
                    <div className="text-xs text-gray-400">
                      Created: {req.created_at || 'N/A'} · Updated: {req.updated_at || 'N/A'}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Group Change Requests Section */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Group Change Requests</h2>
        <GroupChangeRequestsPanel
          environment={envFilter}
          reloadKey={groupReloadKey}
          onChanged={() => { load(); setGroupReloadKey(k => k + 1); }}
        />
      </div>
    </div>
  );
}
