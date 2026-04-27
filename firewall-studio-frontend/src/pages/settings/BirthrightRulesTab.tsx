import { useEffect, useState } from 'react';
import * as api from '@/lib/api';
import type { BirthrightRule } from '@/types';

const empty: BirthrightRule = {
  birthright_id: '',
  scope_dc: '*',
  scope_nh: '*',
  scope_sz: '*',
  destination_kind: 'shared_service',
  destination_ref: '',
  ports: '',
  description: '',
};

export default function BirthrightRulesTab() {
  const [items, setItems] = useState<BirthrightRule[]>([]);
  const [editing, setEditing] = useState<BirthrightRule | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await api.listBirthrightRules());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { void load(); }, []);

  const save = async () => {
    if (!editing) return;
    try {
      await api.upsertBirthrightRule(editing);
      setEditing(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const remove = async (id?: string) => {
    if (!id) return;
    if (!confirm(`Delete birthright rule ${id}?`)) return;
    try {
      await api.deleteBirthrightRule(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Birthright Rules</h3>
          <p className="text-xs text-gray-500">
            Implicit / pre-approved rules every workload gets. The validation engine blocks
            new requests already covered by a birthright (e.g. DNS, NTP, Splunk forwarder, AppD).
          </p>
        </div>
        <button onClick={() => setEditing({ ...empty })}
          className="text-xs px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700">
          + New birthright
        </button>
      </div>

      {error && <div className="rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">{error}</div>}

      {loading ? (
        <div className="text-xs text-gray-400 italic">Loading…</div>
      ) : items.length === 0 ? (
        <div className="text-xs text-gray-400 italic">No birthright rules.</div>
      ) : (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Scope (DC · NH · SZ)</th>
                <th className="text-left p-2">Destination</th>
                <th className="text-left p-2">Ports</th>
                <th className="text-left p-2">Description</th>
                <th className="text-right p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((b) => (
                <tr key={b.birthright_id} className="border-t border-gray-100">
                  <td className="p-2 font-mono">{b.birthright_id}</td>
                  <td className="p-2 font-mono text-[10px]">
                    {(b.scope_dc || '*')} · {(b.scope_nh || '*')} · {(b.scope_sz || '*')}
                  </td>
                  <td className="p-2">
                    <span className="text-[10px] uppercase mr-1 px-1 rounded bg-emerald-100 border border-emerald-200">{b.destination_kind}</span>
                    <span className="font-mono">{b.destination_ref}</span>
                  </td>
                  <td className="p-2 font-mono text-[10px]">{b.ports}</td>
                  <td className="p-2 text-gray-700">{b.description}</td>
                  <td className="p-2 text-right space-x-2">
                    <button onClick={() => setEditing({ ...b })}
                      className="text-[11px] px-2 py-0.5 rounded border border-gray-300 hover:bg-gray-50">Edit</button>
                    <button onClick={() => void remove(b.birthright_id)}
                      className="text-[11px] px-2 py-0.5 rounded border border-rose-200 text-rose-700 hover:bg-rose-50">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <div className="border border-emerald-200 bg-emerald-50/40 rounded-lg p-4 space-y-3">
          <div className="text-sm font-semibold text-emerald-900">{editing.birthright_id ? 'Edit' : 'New'} birthright</div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <label className="space-y-1">
              <span className="text-gray-700">Birthright ID (optional)</span>
              <input value={editing.birthright_id || ''}
                onChange={(e) => setEditing({ ...editing, birthright_id: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono"
                placeholder="auto-generated if blank" />
            </label>
            <label className="space-y-1">
              <span className="text-gray-700">Destination kind</span>
              <select value={editing.destination_kind}
                onChange={(e) => setEditing({ ...editing, destination_kind: e.target.value as BirthrightRule['destination_kind'] })}
                className="w-full border rounded px-2 py-1">
                <option value="shared_service">shared_service</option>
                <option value="app_ingress">app_ingress</option>
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-gray-700">Scope DC (* = all)</span>
              <input value={editing.scope_dc || '*'}
                onChange={(e) => setEditing({ ...editing, scope_dc: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono" />
            </label>
            <label className="space-y-1">
              <span className="text-gray-700">Scope NH (* = all)</span>
              <input value={editing.scope_nh || '*'}
                onChange={(e) => setEditing({ ...editing, scope_nh: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono" />
            </label>
            <label className="space-y-1">
              <span className="text-gray-700">Scope SZ (* = all)</span>
              <input value={editing.scope_sz || '*'}
                onChange={(e) => setEditing({ ...editing, scope_sz: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono" />
            </label>
            <label className="space-y-1">
              <span className="text-gray-700">Destination ref</span>
              <input value={editing.destination_ref}
                onChange={(e) => setEditing({ ...editing, destination_ref: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono"
                placeholder="DNS / NTP / SPLUNK / AD-1003 etc." />
            </label>
            <label className="space-y-1 col-span-2">
              <span className="text-gray-700">Ports</span>
              <input value={editing.ports}
                onChange={(e) => setEditing({ ...editing, ports: e.target.value })}
                className="w-full border rounded px-2 py-1 font-mono"
                placeholder="UDP 53, TCP 53" />
            </label>
            <label className="space-y-1 col-span-2">
              <span className="text-gray-700">Description</span>
              <input value={editing.description || ''}
                onChange={(e) => setEditing({ ...editing, description: e.target.value })}
                className="w-full border rounded px-2 py-1" />
            </label>
          </div>
          <div className="flex items-center justify-end gap-2">
            <button onClick={() => setEditing(null)}
              className="text-xs px-3 py-1 rounded border border-gray-300 hover:bg-gray-50">Cancel</button>
            <button onClick={() => void save()}
              className="text-xs px-3 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700">Save</button>
          </div>
        </div>
      )}
    </div>
  );
}
