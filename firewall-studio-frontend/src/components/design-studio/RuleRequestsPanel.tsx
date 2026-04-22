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
    <div className="space-y-2">
      <div className="text-[10px] uppercase tracking-widest font-bold text-indigo-700">Per-DC Logical Data Flow (LDF)</div>
      <div className="grid gap-2 md:grid-cols-2">
        {rows.map((r, i) => (
          <div key={i} className="p-2.5 rounded-lg border border-indigo-100 bg-gradient-to-br from-indigo-50/60 via-white to-purple-50/60 shadow-sm">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] px-1.5 py-0.5 rounded-full border bg-orange-50 text-orange-700 border-orange-200 font-semibold">{r.src_dc}{r.cross_dc ? ` → ${r.dst_dc}` : ''}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded-full border bg-white text-gray-700 border-gray-200 font-mono">{r.ports}</span>
              {r.cross_dc && <span className="text-[9px] px-1.5 py-0.5 rounded-full border bg-amber-50 text-amber-700 border-amber-200 font-semibold">cross-DC</span>}
            </div>
            <div className="flex items-stretch gap-1.5">
              <div className="flex-1 min-w-0 p-1.5 bg-white border border-sky-200 rounded">
                <div className="text-[8px] uppercase font-bold text-sky-600">Source · {r.src_dc}</div>
                <div className="font-mono text-[10px] font-semibold text-sky-800 truncate">{r.src_group_ref}</div>
              </div>
              <div className="flex flex-col items-center justify-center px-0.5">
                <svg className="w-7 h-3 text-indigo-400" viewBox="0 0 40 16" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2 8h32M28 3l6 5-6 5"/>
                </svg>
                <div className="text-[8px] font-bold text-indigo-600">{r.action}</div>
              </div>
              <div className="flex-1 min-w-0 p-1.5 bg-white border border-rose-200 rounded">
                <div className="text-[8px] uppercase font-bold text-rose-600">Dest · {r.dst_dc}</div>
                <div className="font-mono text-[10px] font-semibold text-rose-800 truncate">{r.dst_group_ref}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
