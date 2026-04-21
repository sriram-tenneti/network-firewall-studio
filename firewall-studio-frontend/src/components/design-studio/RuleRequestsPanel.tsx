import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Environment, PhysicalRuleExpansion, RuleRequestRecord } from '@/types';
import * as api from '@/lib/api';

interface RuleRequestsPanelProps {
  environment?: Environment | '';
  onChanged?: () => void;
}

const STATUSES: (RuleRequestRecord['status'] | 'All')[] = ['All', 'Pending', 'Approved', 'Rejected', 'Deployed', 'Certified'];

export default function RuleRequestsPanel({ environment = '', onChanged }: RuleRequestsPanelProps) {
  const [items, setItems] = useState<RuleRequestRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<(typeof STATUSES)[number]>('Pending');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listRuleRequests({
        environment: environment || undefined,
        status: statusFilter === 'All' ? undefined : statusFilter,
      });
      setItems(res);
    } catch (e) {
      setError((e as Error).message);
    }
    setLoading(false);
  }, [environment, statusFilter]);

  useEffect(() => { void load(); }, [load]);

  const act = async (id: string, to: RuleRequestRecord['status']) => {
    try {
      await api.setRuleRequestStatus(id, to, note || undefined);
      setNote('');
      await load();
      onChanged?.();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const filtered = useMemo(() => items, [items]);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-gray-900">Rule Requests</div>
          <div className="text-xs text-gray-500">Multi-DC fan-out requests. Approve/Reject/Certify entire requests or inspect per-DC physical rules.</div>
        </div>
        <div className="flex items-center gap-2">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            className="text-xs border rounded px-2 py-1">
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={() => void load()} className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50">Refresh</button>
        </div>
      </div>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700 mb-2">{error}</div>}

      {loading ? (
        <div className="text-xs text-gray-400 p-4 text-center">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="text-xs text-gray-400 p-4 text-center italic">No rule requests match the current filter.</div>
      ) : (
        <div className="space-y-2">
          {filtered.map((r) => {
            const open = expanded === r.request_id;
            return (
              <div key={r.request_id} className="border border-gray-200 rounded-lg">
                <div className="p-2.5 flex items-center gap-2 flex-wrap bg-slate-50">
                  <code className="text-[11px] font-mono text-gray-700">{r.request_id}</code>
                  <span className="text-[11px] font-semibold text-gray-900">{r.application_ref}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-[11px] font-semibold text-indigo-700">{r.destination_kind}:{r.destination_ref}</span>
                  <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded border border-gray-200 bg-white text-gray-600">{r.environment}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded border border-gray-200 bg-white text-gray-600 font-mono">{r.ports}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusStyle(r.status)}`}>{r.status}</span>
                  <span className="ml-auto text-[10px] text-gray-500">{r.expansion?.length ?? 0} physical rule(s)</span>
                  <button onClick={() => setExpanded(open ? null : r.request_id)}
                    className="text-[11px] px-2 py-0.5 rounded border border-gray-300 bg-white hover:bg-gray-50">
                    {open ? 'Hide' : 'Inspect'}
                  </button>
                </div>
                {open && (
                  <div className="p-3 space-y-2">
                    {r.description && <div className="text-xs text-gray-700">{r.description}</div>}
                    <FanOutCompact rows={r.expansion || []} />
                    <div className="flex items-center gap-2">
                      <input value={note} onChange={(e) => setNote(e.target.value)}
                        placeholder="Review note (optional)"
                        className="flex-1 text-xs border rounded px-2 py-1" />
                      {r.status === 'Pending' && (
                        <>
                          <button onClick={() => void act(r.request_id, 'Approved')}
                            className="text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700">Approve</button>
                          <button onClick={() => void act(r.request_id, 'Rejected')}
                            className="text-xs px-2 py-1 rounded bg-rose-600 text-white hover:bg-rose-700">Reject</button>
                        </>
                      )}
                      {r.status === 'Approved' && (
                        <button onClick={() => void act(r.request_id, 'Deployed')}
                          className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700">Mark Deployed</button>
                      )}
                      {r.status === 'Deployed' && (
                        <button onClick={() => void act(r.request_id, 'Certified')}
                          className="text-xs px-2 py-1 rounded bg-purple-600 text-white hover:bg-purple-700">Certify</button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function statusStyle(s: RuleRequestRecord['status']): string {
  switch (s) {
    case 'Pending': return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'Approved': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'Rejected': return 'bg-rose-50 text-rose-700 border-rose-200';
    case 'Deployed': return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'Certified': return 'bg-purple-50 text-purple-700 border-purple-200';
    default: return 'bg-gray-50 text-gray-700 border-gray-200';
  }
}

function FanOutCompact({ rows }: { rows: PhysicalRuleExpansion[] }) {
  if (rows.length === 0) return <div className="text-[11px] text-gray-400 italic">No physical rules.</div>;
  return (
    <div className="rounded border border-gray-200 overflow-hidden">
      <table className="min-w-full text-[11px]">
        <thead className="bg-gray-50 text-gray-600">
          <tr>
            <th className="px-2 py-1 text-left">Src DC</th>
            <th className="px-2 py-1 text-left">Dst DC</th>
            <th className="px-2 py-1 text-left">Src Group</th>
            <th className="px-2 py-1 text-left">Dst Group</th>
            <th className="px-2 py-1 text-left">Ports</th>
            <th className="px-2 py-1 text-left">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-gray-100">
              <td className="px-2 py-1 font-mono">{r.src_dc}</td>
              <td className="px-2 py-1 font-mono">{r.dst_dc}</td>
              <td className="px-2 py-1 font-mono text-indigo-700">{r.src_group_ref}</td>
              <td className="px-2 py-1 font-mono text-indigo-700">{r.dst_group_ref}</td>
              <td className="px-2 py-1 font-mono">{r.ports}</td>
              <td className="px-2 py-1">{r.action}{r.cross_dc ? ' · cross-DC' : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
