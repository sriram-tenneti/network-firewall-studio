import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import { getGroups, createGroup, addGroupMember, removeGroupMember } from '@/lib/api';
import type { FirewallGroup, GroupMember } from '@/types';

interface GroupManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  appId?: string;
  applications?: { app_id: string; name: string }[];
}

export function GroupManagerModal({ isOpen, onClose, appId, applications = [] }: GroupManagerModalProps) {
  const [groups, setGroups] = useState<FirewallGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<FirewallGroup | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [filterAppId, setFilterAppId] = useState(appId || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [newGroup, setNewGroup] = useState({ name: '', app_id: appId || '', nh: '', sz: 'Standard', subtype: 'src', description: '' });
  const [newMember, setNewMember] = useState({ type: 'ip' as GroupMember['type'], value: '', description: '' });

  useEffect(() => {
    if (isOpen) {
      setFilterAppId(appId || '');
      loadGroups(appId || '');
    }
  }, [isOpen, appId]);

  const loadGroups = async (forAppId?: string) => {
    setLoading(true);
    try {
      const data = await getGroups(forAppId || undefined);
      setGroups(data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleAppFilterChange = (newAppId: string) => {
    setFilterAppId(newAppId);
    setSelectedGroup(null);
    loadGroups(newAppId);
    setNewGroup(prev => ({ ...prev, app_id: newAppId }));
  };

  const filteredGroups = groups.filter(g => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return g.name.toLowerCase().includes(q) || g.app_id.toLowerCase().includes(q) || g.description.toLowerCase().includes(q) || (g.members || []).some(m => m.value.toLowerCase().includes(q));
  });

  const handleCreateGroup = async () => {
    try {
      await createGroup(newGroup);
      setShowCreate(false);
      setNewGroup({ name: '', app_id: '', nh: '', sz: 'Standard', subtype: 'src', description: '' });
      loadGroups();
    } catch { /* ignore */ }
  };

  const handleAddMember = async () => {
    if (!selectedGroup || !newMember.value) return;
    try {
      const updated = await addGroupMember(selectedGroup.name, newMember);
      setSelectedGroup(updated);
      setNewMember({ type: 'ip', value: '', description: '' });
      loadGroups();
    } catch { /* ignore */ }
  };

  const handleRemoveMember = async (memberValue: string) => {
    if (!selectedGroup) return;
    try {
      const updated = await removeGroupMember(selectedGroup.name, memberValue);
      setSelectedGroup(updated);
      loadGroups();
    } catch { /* ignore */ }
  };

  const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Group Management" subtitle={filterAppId ? `Filtered by ${filterAppId}` : 'All Applications'} size="xl">
      <div className="flex gap-4 min-h-[400px]">
        {/* Left panel - Group list */}
        <div className="w-1/3 border-r pr-4">
          {/* App ID filter */}
          <div className="mb-3">
            <select
              value={filterAppId}
              onChange={e => handleAppFilterChange(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md bg-white focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Applications</option>
              {applications.map(app => (
                <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
              ))}
            </select>
          </div>
          {/* Search within groups */}
          <div className="mb-3">
            <input
              type="text"
              placeholder="Search groups, IPs, subnets..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Groups ({filteredGroups.length})</h3>
            <button onClick={() => setShowCreate(!showCreate)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              {showCreate ? 'Cancel' : '+ New'}
            </button>
          </div>

          {showCreate && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg space-y-2">
              <input className={inputClass} placeholder="Group name (e.g. grp-APP-NH01-STD-src)" value={newGroup.name} onChange={e => setNewGroup({ ...newGroup, name: e.target.value })} />
              <div className="grid grid-cols-2 gap-2">
                <input className={inputClass} placeholder="App ID" value={newGroup.app_id} onChange={e => setNewGroup({ ...newGroup, app_id: e.target.value })} />
                <input className={inputClass} placeholder="NH (e.g. NH01)" value={newGroup.nh} onChange={e => setNewGroup({ ...newGroup, nh: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <select className={inputClass} value={newGroup.sz} onChange={e => setNewGroup({ ...newGroup, sz: e.target.value })}>
                  <option value="Standard">Standard</option>
                  <option value="CCS">CCS</option>
                  <option value="CDE">CDE</option>
                  <option value="CPA">CPA</option>
                </select>
                <select className={inputClass} value={newGroup.subtype} onChange={e => setNewGroup({ ...newGroup, subtype: e.target.value })}>
                  <option value="src">Source</option>
                  <option value="dst">Destination</option>
                  <option value="both">Both</option>
                </select>
              </div>
              <input className={inputClass} placeholder="Description" value={newGroup.description} onChange={e => setNewGroup({ ...newGroup, description: e.target.value })} />
              <button onClick={handleCreateGroup} className="w-full px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">Create Group</button>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            </div>
          ) : (
            <div className="space-y-1 max-h-[280px] overflow-y-auto">
              {filteredGroups.map(g => (
                <button
                  key={g.name}
                  onClick={() => setSelectedGroup(g)}
                  className={`w-full text-left p-2 rounded-md text-xs transition-colors ${
                    selectedGroup?.name === g.name ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="font-medium truncate">{g.name}</div>
                  <div className="text-gray-500 mt-0.5">{g.members?.length || 0} members</div>
                </button>
              ))}
              {groups.length === 0 && <p className="text-xs text-gray-400 text-center py-4">No groups found</p>}
            </div>
          )}
        </div>

        {/* Right panel - Group details */}
        <div className="flex-1 pl-2">
          {selectedGroup ? (
            <>
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-800">{selectedGroup.name}</h3>
                <p className="text-xs text-gray-500 mt-1">{selectedGroup.description}</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  <span>App: {selectedGroup.app_id}</span>
                  <span>NH: {selectedGroup.nh}</span>
                  <span>SZ: {selectedGroup.sz}</span>
                  <span>Type: {selectedGroup.subtype}</span>
                </div>
              </div>

              {/* Add member form */}
              <div className="flex gap-2 mb-3">
                <select className="px-2 py-1.5 border border-gray-300 rounded-md text-xs" value={newMember.type} onChange={e => setNewMember({ ...newMember, type: e.target.value as GroupMember['type'] })}>
                  <option value="ip">IP Address</option>
                  <option value="cidr">Subnet (CIDR)</option>
                  <option value="range">IP Range</option>
                  <option value="group">Nested Group</option>
                </select>
                <input className="flex-1 px-2 py-1.5 border border-gray-300 rounded-md text-xs" placeholder={newMember.type === 'cidr' ? '10.0.1.0/24' : newMember.type === 'range' ? '10.0.1.1-10.0.1.50' : '10.0.1.1'} value={newMember.value} onChange={e => setNewMember({ ...newMember, value: e.target.value })} />
                <input className="w-32 px-2 py-1.5 border border-gray-300 rounded-md text-xs" placeholder="Description" value={newMember.description} onChange={e => setNewMember({ ...newMember, description: e.target.value })} />
                <button onClick={handleAddMember} className="px-3 py-1.5 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 whitespace-nowrap">Add</button>
              </div>

              {/* Members list */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Type</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Value</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Description</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {(selectedGroup.members || []).map((m, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-3 py-2">
                          <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${
                            m.type === 'ip' ? 'bg-blue-100 text-blue-700' :
                            m.type === 'cidr' ? 'bg-green-100 text-green-700' :
                            m.type === 'range' ? 'bg-amber-100 text-amber-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {m.type.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-3 py-2 font-mono">{m.value}</td>
                        <td className="px-3 py-2 text-gray-500">{m.description}</td>
                        <td className="px-3 py-2 text-right">
                          <button onClick={() => handleRemoveMember(m.value)} className="text-red-500 hover:text-red-700 font-medium">Remove</button>
                        </td>
                      </tr>
                    ))}
                    {(!selectedGroup.members || selectedGroup.members.length === 0) && (
                      <tr><td colSpan={4} className="px-3 py-4 text-center text-gray-400">No members in this group</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-gray-400">
              Select a group to view and manage its members
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end mt-4 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
