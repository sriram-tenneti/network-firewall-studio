import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, Users, X, Save } from 'lucide-react';
import type { FirewallGroup, GroupMember } from '@/types';
import * as api from '@/lib/api';
import { autoPrefix } from '@/lib/utils';

interface GroupManagementPanelProps {
  appFilter: string;
  onNotification: (message: string, type: 'success' | 'error' | 'info') => void;
  appDCMappings?: Record<string, unknown>[];
}

export function GroupManagementPanel({ appFilter, onNotification, appDCMappings = [] }: GroupManagementPanelProps) {
  const [groups, setGroups] = useState<FirewallGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<FirewallGroup | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newMemberValue, setNewMemberValue] = useState('');
  const [newMemberType, setNewMemberType] = useState<'ip' | 'cidr' | 'group' | 'range'>('ip');
  const [newMemberDesc, setNewMemberDesc] = useState('');
  const [newGroupAppId, setNewGroupAppId] = useState(appFilter || '');
  const [newGroupDc, setNewGroupDc] = useState('');
  const [newGroupNh, setNewGroupNh] = useState('');
  const [newGroupSz, setNewGroupSz] = useState('');
  const [newGroupSubtype, setNewGroupSubtype] = useState('APP');
  const [newGroupDesc, setNewGroupDesc] = useState('');

  // Derive DC/NH/SZ options from app DC mappings for the selected app
  const appMappingsForApp = appDCMappings.filter(m => String(m.app_id || '') === newGroupAppId);
  const dcOptions = [...new Set(appMappingsForApp.map(m => String(m.dc || '')).filter(Boolean))];
  const nhOptions = [...new Set(appMappingsForApp.map(m => String(m.nh || '')).filter(Boolean))];
  const szOptions = [...new Set(appMappingsForApp.map(m => String(m.sz || '')).filter(Boolean))];

  const loadGroups = async () => {
    try {
      const data = await api.getGroups(appFilter || undefined);
      setGroups(data);
    } catch (err) {
      console.error('Failed to load groups:', err);
    }
  };

  useEffect(() => { loadGroups(); }, [appFilter]);

  const handleCreateGroup = async () => {
    const name = `grp-${newGroupAppId}-${newGroupNh}-${newGroupSz}-${newGroupSubtype}`;
    try {
      const group = await api.createGroup({
        name, app_id: newGroupAppId, nh: newGroupNh, sz: newGroupSz,
        subtype: newGroupSubtype, description: newGroupDesc, members: [],
      });
      onNotification(`Group ${group.name} created`, 'success');
      setShowCreateForm(false);
      setNewGroupDesc('');
      loadGroups();
    } catch {
      onNotification('Failed to create group', 'error');
    }
  };

  const handleAddMember = async () => {
    if (!selectedGroup || !newMemberValue) return;
    try {
      const prefixedValue = autoPrefix(newMemberValue, newMemberType);
      const member: GroupMember = { type: newMemberType, value: prefixedValue, description: newMemberDesc };
      await api.addGroupMember(selectedGroup.name, member);
      onNotification(`Added ${prefixedValue} to ${selectedGroup.name}`, 'success');
      setNewMemberValue('');
      setNewMemberDesc('');
      loadGroups();
      const updated = await api.getGroup(selectedGroup.name);
      setSelectedGroup(updated);
    } catch {
      onNotification('Failed to add member', 'error');
    }
  };

  const handleRemoveMember = async (memberValue: string) => {
    if (!selectedGroup) return;
    try {
      await api.removeGroupMember(selectedGroup.name, memberValue);
      onNotification(`Removed ${memberValue} from ${selectedGroup.name}`, 'success');
      loadGroups();
      const updated = await api.getGroup(selectedGroup.name);
      setSelectedGroup(updated);
    } catch {
      onNotification('Failed to remove member', 'error');
    }
  };

  const handleDeleteGroup = async (groupName: string) => {
    try {
      await api.deleteGroup(groupName);
      onNotification(`Group ${groupName} deleted`, 'success');
      if (selectedGroup?.name === groupName) setSelectedGroup(null);
      loadGroups();
    } catch {
      onNotification('Failed to delete group', 'error');
    }
  };

  return (
    <div className="rounded-xl border border-indigo-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-indigo-100 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <Users className="h-3.5 w-3.5 text-indigo-600" />
          <span className="text-xs font-bold text-indigo-800">Groups</span>
          <span className="rounded-full bg-indigo-100 px-1.5 text-xs text-indigo-600">{groups.length}</span>
        </div>
        <button
          onClick={() => { setShowCreateForm(!showCreateForm); setSelectedGroup(null); }}
          className="rounded bg-indigo-600 p-1 text-white hover:bg-indigo-700"
          title="Create new group"
        >
          <Plus className="h-3 w-3" />
        </button>
      </div>

      {showCreateForm && (
        <div className="border-b border-indigo-100 bg-indigo-50/50 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-800">New Group</span>
            <button onClick={() => setShowCreateForm(false)} className="text-slate-400 hover:text-slate-600">
              <X className="h-3 w-3" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <div>
              <label className="text-xs text-slate-500">App ID</label>
              <input value={newGroupAppId} onChange={(e) => { setNewGroupAppId(e.target.value); setNewGroupDc(''); setNewGroupNh(''); setNewGroupSz(''); }}
                className="w-full rounded border border-slate-300 px-2 py-1 text-xs" placeholder="CRM" />
            </div>
            <div>
              <label className="text-xs text-slate-500">DC {dcOptions.length > 0 && `(${dcOptions.length})`}</label>
              {dcOptions.length > 0 ? (
                <select value={newGroupDc} onChange={(e) => setNewGroupDc(e.target.value)}
                  className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs">
                  <option value="">-- Select DC --</option>
                  {dcOptions.map(dc => <option key={dc} value={dc}>{dc}</option>)}
                </select>
              ) : (
                <select value={newGroupDc} onChange={(e) => setNewGroupDc(e.target.value)}
                  className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs">
                  <option value="">-- Select DC --</option>
                  <option value="ALPHA_NGDC">ALPHA_NGDC</option>
                  <option value="BETA_NGDC">BETA_NGDC</option>
                  <option value="GAMMA_NGDC">GAMMA_NGDC</option>
                </select>
              )}
            </div>
            <div>
              <label className="text-xs text-slate-500">NH {nhOptions.length > 0 && `(${nhOptions.length})`}</label>
              {nhOptions.length > 0 ? (
                <select value={newGroupNh} onChange={(e) => setNewGroupNh(e.target.value)}
                  className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs">
                  <option value="">-- Select NH --</option>
                  {nhOptions.map(nh => <option key={nh} value={nh}>{nh}</option>)}
                </select>
              ) : (
                <input value={newGroupNh} onChange={(e) => setNewGroupNh(e.target.value)}
                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs" placeholder="NH01" />
              )}
            </div>
            <div>
              <label className="text-xs text-slate-500">SZ {szOptions.length > 0 && `(${szOptions.length})`}</label>
              {szOptions.length > 0 ? (
                <select value={newGroupSz} onChange={(e) => setNewGroupSz(e.target.value)}
                  className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs">
                  <option value="">-- Select SZ --</option>
                  {szOptions.map(sz => <option key={sz} value={sz}>{sz}</option>)}
                </select>
              ) : (
                <input value={newGroupSz} onChange={(e) => setNewGroupSz(e.target.value)}
                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs" placeholder="GEN" />
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <div>
              <label className="text-xs text-slate-500">Component</label>
              <select value={newGroupSubtype} onChange={(e) => setNewGroupSubtype(e.target.value)}
                className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs">
                <option value="WEB">WEB</option>
                <option value="APP">APP</option>
                <option value="DB">DB</option>
                <option value="MQ">MQ</option>
                <option value="BAT">BAT</option>
                <option value="API">API</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500">Description</label>
              <input value={newGroupDesc} onChange={(e) => setNewGroupDesc(e.target.value)}
                className="w-full rounded border border-slate-300 px-2 py-1 text-xs" placeholder="Group description" />
            </div>
          </div>
          <div className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600 font-mono">
            grp-{newGroupAppId}-{newGroupNh}-{newGroupSz}-{newGroupSubtype}
          </div>
          <button onClick={handleCreateGroup}
            className="w-full rounded bg-indigo-600 px-2 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700">
            <Save className="inline h-3 w-3 mr-1" />Create Group
          </button>
        </div>
      )}

      <div className="max-h-48 overflow-y-auto">
        {groups.length === 0 && (
          <div className="px-3 py-4 text-center text-xs text-slate-400">
            {appFilter ? `No groups for ${appFilter}` : 'No groups found'}
          </div>
        )}
        {groups.map((group) => (
          <div
            key={group.name}
            onClick={() => { setSelectedGroup(group); setShowCreateForm(false); }}
            className={`flex items-center justify-between border-b border-slate-50 px-3 py-2 cursor-pointer transition-colors ${
              selectedGroup?.name === group.name ? 'bg-indigo-50' : 'hover:bg-slate-50'
            }`}
          >
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-slate-700 truncate font-mono">{group.name}</div>
              <div className="text-xs text-slate-400">{group.members.length} member(s)</div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={(e) => { e.stopPropagation(); setSelectedGroup(group); setShowCreateForm(false); }}
                className="rounded p-0.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50">
                <Edit className="h-3 w-3" />
              </button>
              <button onClick={(e) => { e.stopPropagation(); handleDeleteGroup(group.name); }}
                className="rounded p-0.5 text-slate-400 hover:text-red-600 hover:bg-red-50">
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedGroup && !showCreateForm && (
        <div className="border-t border-indigo-200 bg-indigo-50/30 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-800 font-mono truncate">{selectedGroup.name}</span>
            <button onClick={() => setSelectedGroup(null)} className="text-slate-400 hover:text-slate-600">
              <X className="h-3 w-3" />
            </button>
          </div>
          {selectedGroup.description && (
            <div className="text-xs text-slate-500">{selectedGroup.description}</div>
          )}
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {selectedGroup.members.length === 0 && (
              <div className="text-xs text-slate-400 italic">No members yet</div>
            )}
            {selectedGroup.members.map((m) => (
              <div key={m.value} className="flex items-center justify-between rounded bg-white px-2 py-1 border border-slate-200">
                <div className="flex items-center gap-1.5">
                  <span className={`rounded px-1 text-xs font-bold ${
                    m.type === 'ip' ? 'bg-blue-100 text-blue-700' :
                    m.type === 'cidr' ? 'bg-purple-100 text-purple-700' :
                    m.type === 'range' ? 'bg-amber-100 text-amber-700' :
                    'bg-green-100 text-green-700'
                  }`}>{m.type.toUpperCase()}</span>
                  <span className="text-xs font-mono text-slate-700">{m.value}</span>
                </div>
                <button onClick={() => handleRemoveMember(m.value)}
                  className="rounded p-0.5 text-slate-400 hover:text-red-600">
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <select value={newMemberType} onChange={(e) => setNewMemberType(e.target.value as 'ip' | 'cidr' | 'group' | 'range')}
                className="rounded border border-slate-300 bg-white px-1.5 py-1 text-xs">
                <option value="ip">IP</option>
                <option value="cidr">CIDR</option>
                <option value="range">IP Range</option>
                <option value="group">Nested Group</option>
              </select>
              <input value={newMemberValue} onChange={(e) => setNewMemberValue(e.target.value)}
                placeholder={newMemberType === 'ip' ? '10.1.1.5' : newMemberType === 'cidr' ? '10.1.1.0/24' : newMemberType === 'range' ? '10.1.1.1-10.1.1.254' : 'grp-APP-NH01-GEN-WEB'}
                className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs font-mono" />
            </div>
            <div className="flex items-center gap-1.5">
              <input value={newMemberDesc} onChange={(e) => setNewMemberDesc(e.target.value)}
                placeholder="Description (optional)"
                className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs" />
              <button onClick={handleAddMember}
                disabled={!newMemberValue}
                className={`rounded px-2 py-1 text-xs font-semibold ${
                  newMemberValue ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-200 text-slate-400'
                }`}>
                <Plus className="inline h-3 w-3" /> Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
