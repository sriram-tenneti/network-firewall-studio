import { useState } from 'react';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import type { ADUserGroup, ADUser, ADConfig } from '@/types';

const INITIAL_GROUPS: ADUserGroup[] = [
  { id: 'g1', group_name: 'FW-Admins', access_type: 'Admin', description: 'Full administrative access to all features', member_count: 5, applications: ['*'] },
  { id: 'g2', group_name: 'FW-Approvers', access_type: 'Approver', description: 'Can review and approve/reject rule requests', member_count: 12, applications: ['*'] },
  { id: 'g3', group_name: 'FW-Operators', access_type: 'Operator', description: 'Can create and modify firewall rules', member_count: 25, applications: ['APP01', 'APP02', 'APP03'] },
  { id: 'g4', group_name: 'FW-Viewers', access_type: 'Viewer', description: 'Read-only access to view rules and reports', member_count: 50, applications: ['*'] },
  { id: 'g5', group_name: 'FW-Auditors', access_type: 'Auditor', description: 'Audit access with full read and export capabilities', member_count: 8, applications: ['*'] },
];

const INITIAL_USERS: ADUser[] = [
  { id: 'u1', username: 'admin.user', display_name: 'Admin User', email: 'admin@corp.local', groups: ['FW-Admins'], access_type: 'Admin', last_login: '2025-01-20T08:00:00Z', is_active: true },
  { id: 'u2', username: 'john.approver', display_name: 'John Approver', email: 'john.a@corp.local', groups: ['FW-Approvers'], access_type: 'Approver', last_login: '2025-01-19T14:30:00Z', is_active: true },
  { id: 'u3', username: 'jane.operator', display_name: 'Jane Operator', email: 'jane.o@corp.local', groups: ['FW-Operators'], access_type: 'Operator', last_login: '2025-01-20T09:15:00Z', is_active: true },
  { id: 'u4', username: 'bob.viewer', display_name: 'Bob Viewer', email: 'bob.v@corp.local', groups: ['FW-Viewers'], access_type: 'Viewer', last_login: '2025-01-18T16:00:00Z', is_active: true },
  { id: 'u5', username: 'audit.user', display_name: 'Audit User', email: 'audit@corp.local', groups: ['FW-Auditors'], access_type: 'Auditor', last_login: null, is_active: false },
];

const ACCESS_COLORS: Record<string, string> = {
  Admin: 'bg-red-100 text-red-700 border-red-200',
  Approver: 'bg-purple-100 text-purple-700 border-purple-200',
  Operator: 'bg-blue-100 text-blue-700 border-blue-200',
  Viewer: 'bg-gray-100 text-gray-700 border-gray-200',
  Auditor: 'bg-amber-100 text-amber-700 border-amber-200',
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('ad_groups');
  const [groups, setGroups] = useState<ADUserGroup[]>(INITIAL_GROUPS);
  const [users] = useState<ADUser[]>(INITIAL_USERS);
  const [adConfig, setAdConfig] = useState<ADConfig>({
    server_url: 'ldaps://ad.corp.local:636',
    base_dn: 'DC=corp,DC=local',
    bind_user: 'svc_firewall@corp.local',
    search_filter: '(&(objectClass=user)(memberOf=CN=FW-*))',
    group_mapping: { 'FW-Admins': 'Admin', 'FW-Approvers': 'Approver', 'FW-Operators': 'Operator', 'FW-Viewers': 'Viewer', 'FW-Auditors': 'Auditor' },
    sync_interval_minutes: 30,
    is_connected: false,
    last_sync: null,
  });
  const { notification, showNotification, clearNotification } = useNotification();
  const groupModal = useModal<ADUserGroup>();
  const [editGroup, setEditGroup] = useState<Partial<ADUserGroup>>({});

  const handleTestConnection = () => {
    showNotification('Testing AD connection...', 'info');
    setTimeout(() => {
      setAdConfig(prev => ({ ...prev, is_connected: true, last_sync: new Date().toISOString() }));
      showNotification('AD connection successful! Synced 100 users.', 'success');
    }, 2000);
  };

  const handleSaveConfig = () => {
    showNotification('AD configuration saved', 'success');
  };

  const handleSaveGroup = () => {
    if (editGroup.id) {
      setGroups(prev => prev.map(g => g.id === editGroup.id ? { ...g, ...editGroup } as ADUserGroup : g));
    } else {
      const newGroup: ADUserGroup = {
        id: `g${Date.now()}`,
        group_name: editGroup.group_name || '',
        access_type: (editGroup.access_type || 'Viewer') as ADUserGroup['access_type'],
        description: editGroup.description || '',
        member_count: 0,
        applications: editGroup.applications || [],
      };
      setGroups(prev => [...prev, newGroup]);
    }
    groupModal.close();
    showNotification('Group saved', 'success');
  };

  const tabs = [
    { id: 'ad_groups', label: 'User Groups' },
    { id: 'ad_users', label: 'Users' },
    { id: 'ad_config', label: 'AD Configuration' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Active Directory integration, user groups, and access control</p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {/* AD Groups */}
        {activeTab === 'ad_groups' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => { setEditGroup({}); groupModal.open(null as unknown as ADUserGroup); }}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
              >
                + Add Group
              </button>
            </div>
            <div className="space-y-3">
              {groups.map(group => (
                <div key={group.id} className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 text-xs font-semibold rounded-full border ${ACCESS_COLORS[group.access_type]}`}>
                        {group.access_type}
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-800">{group.group_name}</h3>
                        <p className="text-xs text-gray-500">{group.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-bold text-gray-800">{group.member_count}</p>
                        <p className="text-xs text-gray-500">members</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-600">{group.applications.includes('*') ? 'All Apps' : group.applications.join(', ')}</p>
                      </div>
                      <button
                        onClick={() => { setEditGroup(group); groupModal.open(group); }}
                        className="px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded"
                      >Edit</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AD Users */}
        {activeTab === 'ad_users' && (
          <div className="space-y-3">
            {users.map(user => (
              <div key={user.id} className="p-4 bg-white border border-gray-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {user.display_name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{user.display_name}</p>
                    <p className="text-xs text-gray-500">{user.email} | {user.username}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${ACCESS_COLORS[user.access_type]}`}>{user.access_type}</span>
                  <span className="text-xs text-gray-500">{user.groups.join(', ')}</span>
                  <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="text-xs text-gray-400">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* AD Configuration */}
        {activeTab === 'ad_config' && (
          <div className="max-w-2xl space-y-6">
            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800">Connection Status</h3>
                <span className={`px-3 py-1 text-xs font-medium rounded-full ${adConfig.is_connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {adConfig.is_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {adConfig.last_sync && <p className="text-xs text-gray-500">Last sync: {new Date(adConfig.last_sync).toLocaleString()}</p>}
            </div>

            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
              <h3 className="text-sm font-semibold text-gray-800">LDAP Configuration</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Server URL</label>
                  <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.server_url} onChange={e => setAdConfig({...adConfig, server_url: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Base DN</label>
                  <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.base_dn} onChange={e => setAdConfig({...adConfig, base_dn: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Bind User</label>
                  <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.bind_user} onChange={e => setAdConfig({...adConfig, bind_user: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Sync Interval (min)</label>
                  <input type="number" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.sync_interval_minutes} onChange={e => setAdConfig({...adConfig, sync_interval_minutes: Number(e.target.value)})} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Search Filter</label>
                <input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={adConfig.search_filter} onChange={e => setAdConfig({...adConfig, search_filter: e.target.value})} />
              </div>
            </div>

            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-3">
              <h3 className="text-sm font-semibold text-gray-800">Group-to-Role Mapping</h3>
              {Object.entries(adConfig.group_mapping).map(([adGroup, role]) => (
                <div key={adGroup} className="flex items-center gap-3">
                  <span className="flex-1 text-sm text-gray-700 font-mono">{adGroup}</span>
                  <span className="text-gray-400">&rarr;</span>
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${ACCESS_COLORS[role]}`}>{role}</span>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button onClick={handleTestConnection} className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100">Test Connection</button>
              <button onClick={handleSaveConfig} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">Save Configuration</button>
            </div>
          </div>
        )}
      </div>

      {/* Group Edit Modal */}
      <Modal isOpen={groupModal.isOpen} onClose={groupModal.close} title={editGroup.id ? 'Edit Group' : 'Add Group'} size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Group Name</label>
            <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editGroup.group_name || ''} onChange={e => setEditGroup({...editGroup, group_name: e.target.value})} placeholder="FW-GroupName" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Access Type</label>
            <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editGroup.access_type || 'Viewer'} onChange={e => setEditGroup({...editGroup, access_type: e.target.value as ADUserGroup['access_type']})}>
              <option value="Admin">Admin</option>
              <option value="Approver">Approver</option>
              <option value="Operator">Operator</option>
              <option value="Viewer">Viewer</option>
              <option value="Auditor">Auditor</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <textarea className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" rows={2} value={editGroup.description || ''} onChange={e => setEditGroup({...editGroup, description: e.target.value})} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={groupModal.close} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleSaveGroup} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
