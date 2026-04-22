import { useCallback, useEffect, useMemo, useState } from 'react';
import { Modal } from '@/components/shared/Modal';
import { Notification } from '@/components/shared/Notification';
import { useNotification } from '@/hooks/useNotification';
import type {
  Environment,
  MemberSpec,
  MemberTypeKind,
  SharedService,
  SharedServiceCategory,
  SharedServicePresence,
  NGDCDataCenter,
  NeighbourhoodRegistry,
  SecurityZone,
} from '@/types';
import * as api from '@/lib/api';

const ENVIRONMENTS: Environment[] = ['Production', 'Non-Production', 'Pre-Production'];
const CATEGORIES: SharedServiceCategory[] = [
  'Messaging', 'Database', 'Observability', 'Identity', 'Cache', 'Other',
];
const CATEGORY_STYLES: Record<SharedServiceCategory, { bg: string; text: string; border: string; ring: string; iconBg: string }> = {
  Messaging:    { bg: 'bg-sky-50/70',    text: 'text-sky-700',    border: 'border-sky-100',    ring: 'ring-sky-200',    iconBg: 'bg-gradient-to-br from-sky-100 to-sky-200' },
  Database:     { bg: 'bg-pink-50/70',   text: 'text-pink-700',   border: 'border-pink-100',   ring: 'ring-pink-200',   iconBg: 'bg-gradient-to-br from-pink-100 to-rose-200' },
  Observability:{ bg: 'bg-orange-50/70', text: 'text-orange-700', border: 'border-orange-100', ring: 'ring-orange-200', iconBg: 'bg-gradient-to-br from-amber-100 to-orange-200' },
  Identity:     { bg: 'bg-violet-50/70', text: 'text-violet-700', border: 'border-violet-100', ring: 'ring-violet-200', iconBg: 'bg-gradient-to-br from-violet-100 to-purple-200' },
  Cache:        { bg: 'bg-rose-50/70',   text: 'text-rose-700',   border: 'border-rose-100',   ring: 'ring-rose-200',   iconBg: 'bg-gradient-to-br from-rose-100 to-red-200' },
  Other:        { bg: 'bg-slate-50/70',  text: 'text-slate-700',  border: 'border-slate-100',  ring: 'ring-slate-200',  iconBg: 'bg-gradient-to-br from-slate-100 to-slate-200' },
};

const MEMBER_TYPES: MemberTypeKind[] = ['ip', 'cidr', 'subnet', 'range', 'group'];

function emptyService(): Partial<SharedService> {
  return {
    service_id: '',
    name: '',
    category: 'Other',
    owner: '',
    description: '',
    icon: '🧩',
    color: '#64748b',
    environments: ['Production'],
    tags: [],
  };
}

function emptyPresence(serviceId: string): Partial<SharedServicePresence> & { members: MemberSpec[] } {
  return {
    service_id: serviceId,
    dc_id: '',
    dc_type: 'NGDC',
    environment: 'Production',
    nh_id: '',
    sz_code: '',
    members: [],
  };
}

export default function SharedServicesTab() {
  const { notification, showNotification, clearNotification } = useNotification();
  const showSuccess = useCallback((m: string) => showNotification(m, 'success'), [showNotification]);
  const showError = useCallback((m: string) => showNotification(m, 'error'), [showNotification]);
  const [services, setServices] = useState<SharedService[]>([]);
  const [presencesByService, setPresencesByService] = useState<Record<string, SharedServicePresence[]>>({});
  const [envFilter, setEnvFilter] = useState<'all' | Environment>('all');
  const [catFilter, setCatFilter] = useState<'all' | SharedServiceCategory>('all');
  const [q, setQ] = useState('');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);

  // reference data for presence dropdowns
  const [datacenters, setDatacenters] = useState<NGDCDataCenter[]>([]);
  const [neighbourhoods, setNeighbourhoods] = useState<NeighbourhoodRegistry[]>([]);
  const [securityZones, setSecurityZones] = useState<SecurityZone[]>([]);

  // service edit
  const [editing, setEditing] = useState<Partial<SharedService> | null>(null);
  const [creatingNew, setCreatingNew] = useState(false);

  // presence edit
  const [editingPresence, setEditingPresence] = useState<
    (Partial<SharedServicePresence> & { members: MemberSpec[] }) | null
  >(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [svcs, dcs, nhs, szs] = await Promise.all([
        api.getSharedServices(),
        api.getNGDCDatacenters().catch(() => [] as NGDCDataCenter[]),
        api.getNeighbourhoods().catch(() => [] as NeighbourhoodRegistry[]),
        api.getSecurityZones().catch(() => [] as SecurityZone[]),
      ]);
      setServices(svcs);
      setDatacenters(dcs);
      setNeighbourhoods(nhs);
      setSecurityZones(szs);
      const entries = await Promise.all(
        svcs.map(async (s) => [s.service_id, await api.getSharedServicePresences(s.service_id)] as const),
      );
      const map: Record<string, SharedServicePresence[]> = {};
      for (const [k, v] of entries) map[k] = v;
      setPresencesByService(map);
    } catch (e) {
      showError(`Failed to load shared services: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => { void loadAll(); }, [loadAll]);

  const filtered = useMemo(() => {
    return services.filter((s) => {
      if (envFilter !== 'all' && !(s.environments || []).includes(envFilter)) return false;
      if (catFilter !== 'all' && s.category !== catFilter) return false;
      if (q) {
        const ql = q.toLowerCase();
        const hay = `${s.service_id} ${s.name} ${s.description ?? ''}`.toLowerCase();
        if (!hay.includes(ql)) return false;
      }
      return true;
    });
  }, [services, envFilter, catFilter, q]);

  const saveService = async () => {
    if (!editing) return;
    try {
      if (creatingNew) {
        await api.createSharedService(editing);
        showSuccess(`Shared service "${editing.service_id}" created`);
      } else {
        await api.updateSharedService(editing.service_id!, editing);
        showSuccess(`Shared service "${editing.service_id}" updated`);
      }
      setEditing(null);
      setCreatingNew(false);
      void loadAll();
    } catch (e) {
      showError(`Save failed: ${(e as Error).message}`);
    }
  };

  const removeService = async (svc: SharedService) => {
    if (!window.confirm(`Delete shared service "${svc.service_id}"? This also removes its presences and derived groups.`)) return;
    try {
      await api.deleteSharedService(svc.service_id);
      showSuccess(`Deleted ${svc.service_id}`);
      void loadAll();
    } catch (e) {
      showError(`Delete failed: ${(e as Error).message}`);
    }
  };

  const savePresence = async () => {
    if (!editingPresence?.service_id) return;
    const p = editingPresence;
    if (!p.dc_id || !p.environment || !p.nh_id || !p.sz_code) {
      showError('DC, Environment, NH, and SZ are required');
      return;
    }
    try {
      await api.upsertSharedServicePresence(p.service_id as string, {
        dc_id: p.dc_id,
        dc_type: p.dc_type ?? 'NGDC',
        environment: p.environment,
        nh_id: p.nh_id,
        sz_code: p.sz_code,
        members: p.members,
      });
      showSuccess(`Presence saved for ${p.service_id} @ ${p.dc_id}`);
      setEditingPresence(null);
      void loadAll();
    } catch (e) {
      showError(`Presence save failed: ${(e as Error).message}`);
    }
  };

  const removePresence = async (p: SharedServicePresence) => {
    if (!window.confirm(`Remove presence ${p.service_id} @ ${p.dc_id} (${p.environment})?`)) return;
    try {
      await api.deleteSharedServicePresence(p.service_id, p.dc_id, p.environment, p.nh_id, p.sz_code);
      showSuccess('Presence deleted');
      void loadAll();
    } catch (e) {
      showError(`Delete failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="mt-4">
      {notification && (
        <Notification message={notification.message} type={notification.type} onClose={clearNotification} />
      )}

      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Environment</label>
          <select value={envFilter} onChange={(e) => setEnvFilter(e.target.value as 'all' | Environment)}
            className="border border-gray-300 rounded px-2 py-1 text-sm">
            <option value="all">All environments</option>
            {ENVIRONMENTS.map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
          <select value={catFilter} onChange={(e) => setCatFilter(e.target.value as 'all' | SharedServiceCategory)}
            className="border border-gray-300 rounded px-2 py-1 text-sm">
            <option value="all">All categories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs font-medium text-gray-600 mb-1">Search</label>
          <input type="text" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Search name / id / description"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
        </div>
        <button onClick={() => { setEditing(emptyService()); setCreatingNew(true); }}
          className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded shadow">
          + Add Shared Service
        </button>
        <button onClick={() => void loadAll()}
          className="px-3 py-2 border border-gray-300 text-sm rounded hover:bg-gray-50">
          Refresh
        </button>
      </div>

      {loading && <div className="text-sm text-gray-500">Loading…</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((s) => {
          const style = CATEGORY_STYLES[s.category] ?? CATEGORY_STYLES.Other;
          const presList = presencesByService[s.service_id] || [];
          const presCount = presList.length;
          const isOpen = !!expanded[s.service_id];
          return (
            <div key={s.service_id}
              className={`rounded-xl border ${style.border} bg-white shadow-sm hover:shadow-md transition`}>
              <div className={`p-4 rounded-t-xl ${style.bg}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-lg ${style.iconBg} ${style.text} ring-1 ${style.ring} flex items-center justify-center text-xl shadow-sm`}>
                      {s.icon || '🧩'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <code className={`text-[11px] font-mono ${style.text}`}>{s.service_id}</code>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${style.border} ${style.text} bg-white`}>
                          {s.category}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-gray-900">{s.name}</div>
                      {s.description && <div className="text-xs text-gray-600 mt-0.5 line-clamp-2">{s.description}</div>}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <button className="text-xs text-indigo-700 hover:text-indigo-900"
                      onClick={() => { setEditing({ ...s }); setCreatingNew(false); }}>Edit</button>
                    <button className="text-xs text-rose-600 hover:text-rose-800"
                      onClick={() => void removeService(s)}>Delete</button>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {(s.environments || []).map((e) => (
                    <span key={e} className="text-[10px] px-1.5 py-0.5 rounded bg-white text-gray-700 border border-gray-200">
                      {e}
                    </span>
                  ))}
                  {(s.tags || []).map((t) => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-white text-gray-500 border border-dashed border-gray-300">
                      #{t}
                    </span>
                  ))}
                </div>
              </div>
              <div className="p-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-600">
                    <span className="font-semibold">{presCount}</span> presence{presCount === 1 ? '' : 's'}
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50"
                      onClick={() => setExpanded((m) => ({ ...m, [s.service_id]: !m[s.service_id] }))}>
                      {isOpen ? 'Hide' : 'View'} presences
                    </button>
                    <button
                      className="text-xs px-2 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700"
                      onClick={() => setEditingPresence(emptyPresence(s.service_id))}>
                      + Presence
                    </button>
                  </div>
                </div>
                {isOpen && (
                  <div className="mt-2 space-y-1.5">
                    {presList.length === 0 && (
                      <div className="text-xs text-gray-400 italic">No presences yet.</div>
                    )}
                    {presList.map((p) => (
                      <div key={`${p.dc_id}-${p.environment}-${p.nh_id}-${p.sz_code}`}
                        className="flex items-center justify-between gap-2 rounded border border-gray-200 bg-gray-50 px-2 py-1.5">
                        <div className="min-w-0">
                          <div className="text-xs font-mono text-gray-800 truncate">
                            {p.dc_id} · {p.environment} · {p.nh_id} · {p.sz_code}
                          </div>
                          <div className="text-[11px] text-gray-500 truncate">
                            {(p.members || []).length} member{(p.members || []).length === 1 ? '' : 's'}
                            {p.members?.[0] ? ` · e.g. ${p.members[0].value}` : ''}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <button className="text-[11px] text-indigo-600 hover:text-indigo-900"
                            onClick={() => setEditingPresence({ ...p, members: [...(p.members || [])] })}>Edit</button>
                          <button className="text-[11px] text-rose-600 hover:text-rose-900"
                            onClick={() => void removePresence(p)}>Delete</button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {!loading && filtered.length === 0 && (
          <div className="text-sm text-gray-500 italic col-span-full">No shared services match the filters.</div>
        )}
      </div>

      {/* Service edit modal */}
      <Modal isOpen={!!editing} onClose={() => { setEditing(null); setCreatingNew(false); }}
        title={creatingNew ? 'Add Shared Service' : `Edit ${editing?.service_id ?? ''}`}>
        {editing && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Service ID (slug)</label>
                <input disabled={!creatingNew} value={editing.service_id || ''}
                  onChange={(e) => setEditing((s) => ({ ...(s || {}), service_id: e.target.value.toUpperCase() }))}
                  className="w-full border rounded px-2 py-1 text-sm disabled:bg-gray-100" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
                <select value={editing.category || 'Other'}
                  onChange={(e) => setEditing((s) => ({ ...(s || {}), category: e.target.value as SharedServiceCategory }))}
                  className="w-full border rounded px-2 py-1 text-sm">
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Display Name</label>
              <input value={editing.name || ''}
                onChange={(e) => setEditing((s) => ({ ...(s || {}), name: e.target.value }))}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <textarea rows={2} value={editing.description || ''}
                onChange={(e) => setEditing((s) => ({ ...(s || {}), description: e.target.value }))}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Owner</label>
                <input value={editing.owner || ''}
                  onChange={(e) => setEditing((s) => ({ ...(s || {}), owner: e.target.value }))}
                  className="w-full border rounded px-2 py-1 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Icon (emoji)</label>
                <input value={editing.icon || ''}
                  onChange={(e) => setEditing((s) => ({ ...(s || {}), icon: e.target.value }))}
                  className="w-full border rounded px-2 py-1 text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Environments</label>
              <div className="flex flex-wrap gap-2">
                {ENVIRONMENTS.map((env) => {
                  const on = (editing.environments || []).includes(env);
                  return (
                    <label key={env} className={`text-xs px-2 py-1 rounded border cursor-pointer ${on ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-700 border-gray-300'}`}>
                      <input type="checkbox" className="hidden" checked={on}
                        onChange={(e) => {
                          const curr = editing.environments || [];
                          setEditing((s) => ({
                            ...(s || {}),
                            environments: e.target.checked ? [...curr, env] : curr.filter((x) => x !== env),
                          }));
                        }} />
                      {env}
                    </label>
                  );
                })}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tags (comma separated)</label>
              <input value={(editing.tags || []).join(', ')}
                onChange={(e) => setEditing((s) => ({ ...(s || {}), tags: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) }))}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => { setEditing(null); setCreatingNew(false); }}
                className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50">Cancel</button>
              <button onClick={() => void saveService()}
                className="px-3 py-1.5 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700">
                {creatingNew ? 'Create' : 'Save'}
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Presence edit modal */}
      <Modal isOpen={!!editingPresence} onClose={() => setEditingPresence(null)}
        title={`Presence · ${editingPresence?.service_id ?? ''}`} size="lg">
        {editingPresence && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Environment</label>
                <select value={editingPresence.environment || 'Production'}
                  onChange={(e) => setEditingPresence((p) => ({ ...(p!), environment: e.target.value as Environment }))}
                  className="w-full border rounded px-2 py-1 text-sm">
                  {ENVIRONMENTS.map((e) => <option key={e} value={e}>{e}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Data Center</label>
                <select value={editingPresence.dc_id || ''}
                  onChange={(e) => setEditingPresence((p) => ({ ...(p!), dc_id: e.target.value }))}
                  className="w-full border rounded px-2 py-1 text-sm">
                  <option value="">— select DC —</option>
                  {datacenters.map((d) => <option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Neighbourhood</label>
                <select value={editingPresence.nh_id || ''}
                  onChange={(e) => setEditingPresence((p) => ({ ...(p!), nh_id: e.target.value }))}
                  className="w-full border rounded px-2 py-1 text-sm">
                  <option value="">— select NH —</option>
                  {neighbourhoods.map((n) => <option key={n.nh_id} value={n.nh_id}>{n.nh_id} — {n.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Security Zone</label>
                <select value={editingPresence.sz_code || ''}
                  onChange={(e) => setEditingPresence((p) => ({ ...(p!), sz_code: e.target.value }))}
                  className="w-full border rounded px-2 py-1 text-sm">
                  <option value="">— select SZ —</option>
                  {securityZones.map((z) => <option key={z.code} value={z.code}>{z.code} — {z.name}</option>)}
                </select>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-medium text-gray-600">Members (IP / CIDR / Subnet / Range / Group)</label>
                <button className="text-xs text-indigo-600 hover:text-indigo-900"
                  onClick={() => setEditingPresence((p) => ({
                    ...(p!),
                    members: [...p!.members, { type: 'ip', value: '', description: '' }],
                  }))}>+ Add member</button>
              </div>
              <div className="space-y-1.5 max-h-64 overflow-y-auto">
                {editingPresence.members.length === 0 && (
                  <div className="text-xs text-gray-400 italic">No members yet.</div>
                )}
                {editingPresence.members.map((m, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 items-center">
                    <select value={m.type}
                      onChange={(e) => setEditingPresence((p) => {
                        const mem = [...p!.members]; mem[i] = { ...mem[i], type: e.target.value as MemberTypeKind };
                        return { ...(p!), members: mem };
                      })}
                      className="col-span-2 border rounded px-1 py-1 text-xs uppercase">
                      {MEMBER_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <input value={m.value} placeholder="value"
                      onChange={(e) => setEditingPresence((p) => {
                        const mem = [...p!.members]; mem[i] = { ...mem[i], value: e.target.value };
                        return { ...(p!), members: mem };
                      })}
                      className="col-span-5 border rounded px-2 py-1 text-xs font-mono" />
                    <input value={m.description || ''} placeholder="description"
                      onChange={(e) => setEditingPresence((p) => {
                        const mem = [...p!.members]; mem[i] = { ...mem[i], description: e.target.value };
                        return { ...(p!), members: mem };
                      })}
                      className="col-span-4 border rounded px-2 py-1 text-xs" />
                    <button className="col-span-1 text-xs text-rose-600 hover:text-rose-800"
                      onClick={() => setEditingPresence((p) => ({
                        ...(p!), members: p!.members.filter((_, j) => j !== i),
                      }))}>✕</button>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setEditingPresence(null)}
                className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50">Cancel</button>
              <button onClick={() => void savePresence()}
                className="px-3 py-1.5 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700">Save presence</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
