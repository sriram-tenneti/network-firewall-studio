import { useState, useEffect, useCallback } from 'react';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import type { ADUserGroup, ADUser, ADConfig, Application, AppDCMapping } from '@/types';
import * as api from '@/lib/api';

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
  const [activeTab, setActiveTab] = useState('app_management');
  const [groups, setGroups] = useState<ADUserGroup[]>(INITIAL_GROUPS);
  const [users, setUsers] = useState<ADUser[]>(INITIAL_USERS);
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
  const [searchQuery, setSearchQuery] = useState('');
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [policyMatrix, setPolicyMatrix] = useState<Record<string, unknown>[]>([]);
  const [namingStandards, setNamingStandards] = useState<Record<string, unknown>>({});

  // App-DC Mappings state
  const [appDCMappings, setAppDCMappings] = useState<AppDCMapping[]>([]);
  const [showAddMapping, setShowAddMapping] = useState(false);
  const [newMappingForm, setNewMappingForm] = useState<Partial<AppDCMapping>>({ app_id: '', component: 'APP', dc: 'ALPHA_NGDC', nh: '', sz: '', cidr: '', status: 'Active', notes: '' });
  const [editingMappingId, setEditingMappingId] = useState<string | null>(null);
  const [editMappingForm, setEditMappingForm] = useState<Partial<AppDCMapping>>({});

  // Policy matrix environment filter
  const [policyEnvFilter, setPolicyEnvFilter] = useState<string>('all');
  const [prodMatrix, setProdMatrix] = useState<Record<string, unknown>[]>([]);
  const [nonprodMatrix, setNonprodMatrix] = useState<Record<string, unknown>[]>([]);
  const [preprodMatrix, setPreprodMatrix] = useState<Record<string, unknown>[]>([]);
  const [loadingRef, setLoadingRef] = useState(false);

  // Firewall Devices state
  const [fwDevices, setFwDevices] = useState<Record<string, unknown>[]>([]);
  const [editingDeviceId, setEditingDeviceId] = useState<string | null>(null);
  const [editDeviceForm, setEditDeviceForm] = useState<Record<string, unknown>>({});
  const [showAddDevice, setShowAddDevice] = useState(false);
  const [newDeviceForm, setNewDeviceForm] = useState<Record<string, unknown>>({ device_id: '', name: '', vendor: 'palo_alto', dc: 'ALPHA_NGDC', nh: '', sz: '', type: 'segmentation', status: 'Active', mgmt_ip: '', capabilities: '' });
  const [deviceFilter, setDeviceFilter] = useState({ dc: '', type: '', vendor: '' });

  // Edit states for App Management
  const [editingAppId, setEditingAppId] = useState<string | null>(null);
  const [editAppForm, setEditAppForm] = useState<Partial<Application>>({});
  const [showAddApp, setShowAddApp] = useState(false);
  const [newAppForm, setNewAppForm] = useState<Partial<Application>>({ app_id: '', name: '', nh: '', sz: '', owner: '' });

  // Edit states for Policy Matrix
  const [editingPolicyIdx, setEditingPolicyIdx] = useState<number | null>(null);
  const [editPolicyForm, setEditPolicyForm] = useState<Record<string, unknown>>({});
  const [showAddPolicy, setShowAddPolicy] = useState(false);
  const [newPolicyForm, setNewPolicyForm] = useState<Record<string, unknown>>({ source_zone: '', source_nh: 'Any', dest_zone: '', dest_nh: 'Any', action: 'Permit', environment: 'All', note: '' });

  // Edit states for Naming Standards
  const [editingNaming, setEditingNaming] = useState(false);
  const [editNamingForm, setEditNamingForm] = useState<Record<string, string>>({
    group_prefix: 'grp-', server_prefix: 'svr-', range_prefix: 'rng-',
    group_pattern: '{APP}-{NH}-{SZ}-{SUBTYPE}', server_pattern: '{IP_ADDRESS}', range_pattern: '{APP}-{NH}-{SZ}-{DESC}',
  });

  // Edit states for Users
  const userModal = useModal<ADUser>();
  const [editUser, setEditUser] = useState<Partial<ADUser>>({});

  const loadRefData = useCallback(async () => {
    setLoadingRef(true);
    try {
      const [appsData, policyData, namingData, devicesData, dcMappings, prodMtx, nprodMtx, pprodMtx] = await Promise.all([
        api.getApplications(),
        api.getAllPolicyMatrices(),
        api.getNamingStandards(),
        api.getFirewallDevices(),
        api.getAppDCMappings(),
        api.getNgdcProdMatrix(),
        api.getNonprodMatrix(),
        api.getPreprodMatrix(),
      ]);
      setApplications(appsData);
      setPolicyMatrix(policyData.combined || []);
      setNamingStandards(namingData as unknown as Record<string, unknown>);
      setFwDevices(devicesData);
      setAppDCMappings(dcMappings as unknown as AppDCMapping[]);
      setProdMatrix(prodMtx);
      setNonprodMatrix(nprodMtx);
      setPreprodMatrix(pprodMtx);
    } catch {
      showNotification('Failed to load reference data', 'error');
    }
    setLoadingRef(false);
  }, [showNotification]);

  useEffect(() => { loadRefData(); }, [loadRefData]);

  const handleTestConnection = () => {
    showNotification('Testing AD connection...', 'info');
    setTimeout(() => {
      setAdConfig(prev => ({ ...prev, is_connected: true, last_sync: new Date().toISOString() }));
      showNotification('AD connection successful! Synced 100 users.', 'success');
    }, 2000);
  };

  const handleSaveConfig = () => { showNotification('AD configuration saved', 'success'); };

  const handleSaveGroup = () => {
    if (editGroup.id) {
      setGroups(prev => prev.map(g => g.id === editGroup.id ? { ...g, ...editGroup } as ADUserGroup : g));
    } else {
      const newGroup: ADUserGroup = {
        id: `g${Date.now()}`, group_name: editGroup.group_name || '',
        access_type: (editGroup.access_type || 'Viewer') as ADUserGroup['access_type'],
        description: editGroup.description || '', member_count: 0, applications: editGroup.applications || [],
      };
      setGroups(prev => [...prev, newGroup]);
    }
    groupModal.close();
    showNotification('Group saved', 'success');
  };

  const handleDeleteGroup = (id: string) => {
    setGroups(prev => prev.filter(g => g.id !== id));
    showNotification('Group deleted', 'success');
  };

  const handleSaveApp = async () => {
    if (!editingAppId) return;
    try {
      await api.updateApplication(editingAppId, editAppForm as Record<string, unknown>);
      showNotification('Application updated', 'success');
      setEditingAppId(null);
      loadRefData();
    } catch {
      showNotification('Failed to update application', 'error');
    }
  };

  const handleAddApp = async () => {
    try {
      await api.createApplication(newAppForm as Record<string, unknown>);
      showNotification('Application added', 'success');
      setShowAddApp(false);
      setNewAppForm({ app_id: '', name: '', nh: '', sz: '', owner: '' });
      loadRefData();
    } catch {
      showNotification('Failed to add application', 'error');
    }
  };

  const handleDeleteApp = async (appId: string) => {
    try {
      await api.deleteApplication(appId);
      showNotification('Application deleted', 'success');
      if (selectedApp === appId) setSelectedApp('');
      loadRefData();
    } catch {
      showNotification('Failed to delete application', 'error');
    }
  };

  const handleSavePolicy = async () => {
    try {
      await api.updateNamingStandards({
        ...namingStandards,
        policy_matrix: policyMatrix.map((p, i) => i === editingPolicyIdx ? editPolicyForm : p),
      });
      showNotification('Policy entry updated', 'success');
      setEditingPolicyIdx(null);
      loadRefData();
    } catch {
      showNotification('Failed to update policy', 'error');
    }
  };

  const handleAddPolicy = async () => {
    try {
      await api.createPolicyEntry(newPolicyForm);
      showNotification('Policy entry added', 'success');
      setShowAddPolicy(false);
      setNewPolicyForm({ source_zone: '', source_nh: 'Any', dest_zone: '', dest_nh: 'Any', action: 'Permit', environment: 'All', note: '' });
      loadRefData();
    } catch {
      showNotification('Failed to add policy entry', 'error');
    }
  };

  const handleDeletePolicy = async (idx: number) => {
    try {
      const e = policyMatrix[idx];
      await api.deletePolicyEntry(String(e.source_zone || e.src_zone || ''), String(e.dest_zone || e.dst_zone || ''));
      showNotification('Policy entry deleted', 'success');
      loadRefData();
    } catch {
      showNotification('Failed to delete policy entry', 'error');
    }
  };

  const handleSaveNaming = async () => {
    try {
      await api.updateNamingStandards({ ...namingStandards, prefixes: editNamingForm });
      showNotification('Naming standards saved', 'success');
      setEditingNaming(false);
      loadRefData();
    } catch {
      showNotification('Failed to save naming standards', 'error');
    }
  };

  const handleSaveUser = () => {
    if (editUser.id) {
      setUsers(prev => prev.map(u => u.id === editUser.id ? { ...u, ...editUser } as ADUser : u));
    } else {
      const nu: ADUser = {
        id: `u${Date.now()}`, username: editUser.username || '',
        display_name: editUser.display_name || '', email: editUser.email || '',
        groups: editUser.groups || [],
        access_type: (editUser.access_type || 'Viewer') as ADUser['access_type'],
        last_login: null, is_active: true,
      };
      setUsers(prev => [...prev, nu]);
    }
    userModal.close();
    showNotification('User saved', 'success');
  };

  const handleDeleteUser = (id: string) => {
    setUsers(prev => prev.filter(u => u.id !== id));
    showNotification('User deleted', 'success');
  };

  const selectedAppData = applications.find(a => a.app_id === selectedApp);
  const inp = 'w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500';

  // App DC Mapping helpers
  const selectedAppMappings = appDCMappings.filter(m => m.app_id === selectedApp);

  const handleAddMapping = async () => {
    try {
      const data = { ...newMappingForm, app_id: selectedApp || newMappingForm.app_id };
      await api.createAppDCMapping(data as Record<string, unknown>);
      setShowAddMapping(false);
      setNewMappingForm({ app_id: '', component: 'APP', dc: 'ALPHA_NGDC', nh: '', sz: '', cidr: '', status: 'Active', notes: '' });
      loadRefData();
      showNotification('Component mapping added', 'success');
    } catch { showNotification('Failed to add mapping', 'error'); }
  };

  const handleSaveMapping = async () => {
    if (!editingMappingId) return;
    try {
      await api.updateAppDCMapping(editingMappingId, editMappingForm as Record<string, unknown>);
      setEditingMappingId(null);
      loadRefData();
      showNotification('Mapping updated', 'success');
    } catch { showNotification('Failed to update mapping', 'error'); }
  };

  const handleDeleteMapping = async (id: string) => {
    try {
      await api.deleteAppDCMapping(id);
      loadRefData();
      showNotification('Mapping deleted', 'success');
    } catch { showNotification('Failed to delete mapping', 'error'); }
  };

  // Policy matrix filtered by environment
  const filteredPolicyMatrix = policyEnvFilter === 'all' ? policyMatrix
    : policyEnvFilter === 'production' ? prodMatrix
    : policyEnvFilter === 'non_production' ? nonprodMatrix
    : policyEnvFilter === 'pre_production' ? preprodMatrix
    : policyMatrix;

  const handleSaveDevice = async () => {
    if (!editingDeviceId) return;
    try {
      await api.updateFirewallDevice(editingDeviceId, editDeviceForm);
      setEditingDeviceId(null);
      loadRefData();
      showNotification('Device updated', 'success');
    } catch { showNotification('Failed to update device', 'error'); }
  };

  const handleAddDevice = async () => {
    try {
      const capsStr = (newDeviceForm.capabilities as string) || '';
      const caps = capsStr ? capsStr.split(',').map((c: string) => c.trim()) : [];
      await api.createFirewallDevice({ ...newDeviceForm, capabilities: caps });
      setShowAddDevice(false);
      setNewDeviceForm({ device_id: '', name: '', vendor: 'palo_alto', dc: 'ALPHA_NGDC', nh: '', sz: '', type: 'segmentation', status: 'Active', mgmt_ip: '', capabilities: '' });
      loadRefData();
      showNotification('Device added', 'success');
    } catch { showNotification('Failed to add device', 'error'); }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    if (!confirm(`Delete device ${deviceId}?`)) return;
    try {
      await api.deleteFirewallDevice(deviceId);
      loadRefData();
      showNotification('Device deleted', 'success');
    } catch { showNotification('Failed to delete device', 'error'); }
  };

  const filteredDevices = fwDevices.filter(d => {
    if (deviceFilter.dc && d.dc !== deviceFilter.dc) return false;
    if (deviceFilter.type && d.type !== deviceFilter.type) return false;
    if (deviceFilter.vendor && d.vendor !== deviceFilter.vendor) return false;
    return true;
  });

  const tabs = [
    { id: 'app_management', label: 'App Management' },
    { id: 'policy_matrix', label: 'Policy Matrix' },
    { id: 'naming_standards', label: 'Naming Standards' },
    { id: 'fw_devices', label: 'Firewall Devices' },
    { id: 'ad_groups', label: 'User Groups' },
    { id: 'ad_users', label: 'Users' },
    { id: 'ad_config', label: 'AD Configuration' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin &amp; Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Application management, policy matrix, naming standards, AD integration</p>
      </div>
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {(activeTab === 'ad_groups' || activeTab === 'ad_users') && (
        <div className="mt-4">
          <input type="text" placeholder={activeTab === 'ad_groups' ? 'Search groups...' : 'Search users...'}
            value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white" />
        </div>
      )}

      <div className="mt-6">
        {/* ── App Management Tab ── */}
        {activeTab === 'app_management' && (
          <div className="space-y-6">
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <label className="text-sm font-semibold text-gray-700">Select Application:</label>
                  <select className="flex-1 max-w-md px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 bg-white"
                    value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
                    <option value="">-- All Applications --</option>
                    {applications.map(app => (
                      <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
                    ))}
                  </select>
                </div>
                <button onClick={() => setShowAddApp(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add Application</button>
              </div>
            </div>

            {showAddApp && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
                <h3 className="text-sm font-semibold text-blue-800">Add New Application</h3>
                <div className="grid grid-cols-5 gap-3">
                  <input className={inp} placeholder="App ID" value={newAppForm.app_id || ''} onChange={e => setNewAppForm({ ...newAppForm, app_id: e.target.value })} />
                  <input className={inp} placeholder="Name" value={newAppForm.name || ''} onChange={e => setNewAppForm({ ...newAppForm, name: e.target.value })} />
                  <input className={inp} placeholder="NH" value={newAppForm.nh || ''} onChange={e => setNewAppForm({ ...newAppForm, nh: e.target.value })} />
                  <input className={inp} placeholder="SZ" value={newAppForm.sz || ''} onChange={e => setNewAppForm({ ...newAppForm, sz: e.target.value })} />
                  <input className={inp} placeholder="Owner" value={newAppForm.owner || ''} onChange={e => setNewAppForm({ ...newAppForm, owner: e.target.value })} />
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowAddApp(false)} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button onClick={handleAddApp} disabled={!newAppForm.app_id || !newAppForm.name}
                    className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-40">Save</button>
                </div>
              </div>
            )}

            {selectedAppData && (
              <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-800">Application Details</h3>
                  <div className="flex gap-2">
                    {editingAppId === selectedApp ? (<>
                      <button onClick={() => setEditingAppId(null)} className="px-3 py-1 text-xs text-gray-600 border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
                      <button onClick={handleSaveApp} className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700">Save</button>
                    </>) : (<>
                      <button onClick={() => { setEditingAppId(selectedApp); setEditAppForm(selectedAppData); }}
                        className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Edit</button>
                      <button onClick={() => handleDeleteApp(selectedApp)}
                        className="px-3 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100">Delete</button>
                    </>)}
                  </div>
                </div>
                {editingAppId === selectedApp ? (
                  <div className="grid grid-cols-4 gap-4">
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">App ID</label>
                      <p className="text-sm font-semibold text-gray-800">{selectedAppData.app_id}</p></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                      <input className={inp} value={editAppForm.name || ''} onChange={e => setEditAppForm({ ...editAppForm, name: e.target.value })} /></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">NH</label>
                      <input className={inp} value={editAppForm.nh || ''} onChange={e => setEditAppForm({ ...editAppForm, nh: e.target.value })} /></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">SZ</label>
                      <input className={inp} value={editAppForm.sz || ''} onChange={e => setEditAppForm({ ...editAppForm, sz: e.target.value })} /></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Owner</label>
                      <input className={inp} value={editAppForm.owner || ''} onChange={e => setEditAppForm({ ...editAppForm, owner: e.target.value })} /></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Criticality</label>
                      <input className={inp} value={String(editAppForm.criticality ?? '')} onChange={e => setEditAppForm({ ...editAppForm, criticality: Number(e.target.value) || 0 })} /></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">PCI Scope</label>
                      <select className={inp} value={editAppForm.pci_scope ? 'true' : 'false'} onChange={e => setEditAppForm({ ...editAppForm, pci_scope: e.target.value === 'true' })}>
                        <option value="true">Yes</option><option value="false">No</option>
                      </select></div>
                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Dist ID</label>
                      <input className={inp} value={String(editAppForm.app_distributed_id ?? '')} onChange={e => setEditAppForm({ ...editAppForm, app_distributed_id: e.target.value })} /></div>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-4 gap-4">
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">App ID</label><p className="text-sm font-semibold text-gray-800">{selectedAppData.app_id}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Name</label><p className="text-sm text-gray-800">{selectedAppData.name}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Neighbourhood</label><p className="text-sm font-mono text-gray-800">{selectedAppData.nh || 'N/A'}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Security Zone</label><p className="text-sm font-mono text-gray-800">{selectedAppData.sz || 'N/A'}</p></div>
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Owner</label><p className="text-sm text-gray-800">{selectedAppData.owner || 'N/A'}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Criticality</label><p className="text-sm text-gray-800">{selectedAppData.criticality ?? 'N/A'}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">PCI Scope</label><p className="text-sm text-gray-800">{selectedAppData.pci_scope ? 'Yes' : 'No'}</p></div>
                      <div><label className="block text-xs font-medium text-gray-500 mb-1">Dist ID</label><p className="text-sm font-mono text-gray-800">{selectedAppData.app_distributed_id ?? 'N/A'}</p></div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* DC/SZ Component Mappings for selected app */}
            {selectedApp && (
              <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-800">DC / NH / SZ Component Mappings ({selectedAppMappings.length})</h3>
                  <button onClick={() => { setShowAddMapping(true); setNewMappingForm({ ...newMappingForm, app_id: selectedApp }); }}
                    className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700">+ Add Mapping</button>
                </div>
                {showAddMapping && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
                    <div className="grid grid-cols-7 gap-2">
                      <select className="px-2 py-1 text-xs border rounded" value={newMappingForm.component || 'APP'} onChange={e => setNewMappingForm({ ...newMappingForm, component: e.target.value as AppDCMapping['component'] })}>
                        {['WEB','APP','DB','MQ','BAT','API'].map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                      <select className="px-2 py-1 text-xs border rounded" value={newMappingForm.dc || ''} onChange={e => setNewMappingForm({ ...newMappingForm, dc: e.target.value })}>
                        <option value="ALPHA_NGDC">ALPHA_NGDC</option><option value="BETA_NGDC">BETA_NGDC</option><option value="GAMMA_NGDC">GAMMA_NGDC</option>
                      </select>
                      <input className="px-2 py-1 text-xs border rounded" placeholder="NH" value={newMappingForm.nh || ''} onChange={e => setNewMappingForm({ ...newMappingForm, nh: e.target.value })} />
                      <input className="px-2 py-1 text-xs border rounded" placeholder="SZ" value={newMappingForm.sz || ''} onChange={e => setNewMappingForm({ ...newMappingForm, sz: e.target.value })} />
                      <input className="px-2 py-1 text-xs border rounded" placeholder="CIDR" value={newMappingForm.cidr || ''} onChange={e => setNewMappingForm({ ...newMappingForm, cidr: e.target.value })} />
                      <input className="px-2 py-1 text-xs border rounded" placeholder="Notes" value={newMappingForm.notes || ''} onChange={e => setNewMappingForm({ ...newMappingForm, notes: e.target.value })} />
                      <div className="flex gap-1">
                        <button onClick={() => setShowAddMapping(false)} className="px-2 py-1 text-xs text-gray-600 border rounded hover:bg-gray-100">Cancel</button>
                        <button onClick={handleAddMapping} className="px-2 py-1 text-xs text-white bg-indigo-600 rounded hover:bg-indigo-700">Add</button>
                      </div>
                    </div>
                  </div>
                )}
                {selectedAppMappings.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50"><tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Component</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">DC</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">NH</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">SZ</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">CIDR</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Notes</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Actions</th>
                      </tr></thead>
                      <tbody className="divide-y divide-gray-100">
                        {selectedAppMappings.map(m => {
                          const mid = m.id || `${m.app_id}-${m.component}-${m.dc}`;
                          if (editingMappingId === mid) {
                            return (
                              <tr key={mid} className="bg-blue-50">
                                <td className="px-3 py-1"><select className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.component || ''} onChange={e => setEditMappingForm({ ...editMappingForm, component: e.target.value as AppDCMapping['component'] })}>
                                  {['WEB','APP','DB','MQ','BAT','API'].map(c => <option key={c} value={c}>{c}</option>)}
                                </select></td>
                                <td className="px-3 py-1"><select className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.dc || ''} onChange={e => setEditMappingForm({ ...editMappingForm, dc: e.target.value })}>
                                  <option value="ALPHA_NGDC">ALPHA</option><option value="BETA_NGDC">BETA</option><option value="GAMMA_NGDC">GAMMA</option>
                                </select></td>
                                <td className="px-3 py-1"><input className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.nh || ''} onChange={e => setEditMappingForm({ ...editMappingForm, nh: e.target.value })} /></td>
                                <td className="px-3 py-1"><input className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.sz || ''} onChange={e => setEditMappingForm({ ...editMappingForm, sz: e.target.value })} /></td>
                                <td className="px-3 py-1"><input className="w-full px-1 py-1 text-xs border rounded font-mono" value={editMappingForm.cidr || ''} onChange={e => setEditMappingForm({ ...editMappingForm, cidr: e.target.value })} /></td>
                                <td className="px-3 py-1"><select className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.status || 'Active'} onChange={e => setEditMappingForm({ ...editMappingForm, status: e.target.value as AppDCMapping['status'] })}>
                                  <option value="Active">Active</option><option value="Inactive">Inactive</option>
                                </select></td>
                                <td className="px-3 py-1"><input className="w-full px-1 py-1 text-xs border rounded" value={editMappingForm.notes || ''} onChange={e => setEditMappingForm({ ...editMappingForm, notes: e.target.value })} /></td>
                                <td className="px-3 py-1"><div className="flex gap-1">
                                  <button onClick={() => setEditingMappingId(null)} className="px-2 py-0.5 text-xs text-gray-600 border rounded hover:bg-gray-100">Cancel</button>
                                  <button onClick={handleSaveMapping} className="px-2 py-0.5 text-xs text-white bg-indigo-600 rounded hover:bg-indigo-700">Save</button>
                                </div></td>
                              </tr>
                            );
                          }
                          return (
                            <tr key={mid} className="hover:bg-gray-50">
                              <td className="px-3 py-2"><span className="px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700">{m.component}</span></td>
                              <td className="px-3 py-2 font-mono text-xs text-gray-700">{m.dc}</td>
                              <td className="px-3 py-2 font-mono text-xs text-gray-700">{m.nh}</td>
                              <td className="px-3 py-2 font-mono text-xs text-gray-700">{m.sz}</td>
                              <td className="px-3 py-2 font-mono text-xs text-gray-600">{m.cidr}</td>
                              <td className="px-3 py-2"><span className={`px-2 py-0.5 text-xs rounded-full ${m.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{m.status}</span></td>
                              <td className="px-3 py-2 text-xs text-gray-500 max-w-[150px] truncate">{m.notes || ''}</td>
                              <td className="px-3 py-2"><div className="flex gap-1">
                                <button onClick={() => { setEditingMappingId(mid); setEditMappingForm({ ...m }); }} className="px-2 py-0.5 text-xs text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Edit</button>
                                <button onClick={() => handleDeleteMapping(mid)} className="px-2 py-0.5 text-xs text-red-700 bg-red-50 rounded hover:bg-red-100">Del</button>
                              </div></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 italic">No component mappings yet. Click &quot;+ Add Mapping&quot; to define DC/NH/SZ placement for each component.</p>
                )}
              </div>
            )}

            {!selectedApp && (
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-800">All Applications ({applications.length})</h3>
                </div>
                {loadingRef ? (<div className="p-8 text-center text-gray-400">Loading...</div>) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50"><tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">App ID</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Name</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">NH</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">SZ</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Owner</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Actions</th>
                      </tr></thead>
                      <tbody className="divide-y divide-gray-100">
                        {applications.map(app => (
                          <tr key={app.app_id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-mono font-semibold text-blue-700 cursor-pointer" onClick={() => setSelectedApp(app.app_id)}>{app.app_id}</td>
                            <td className="px-4 py-2 text-gray-800">{app.name}</td>
                            <td className="px-4 py-2 font-mono text-gray-600">{app.nh || '-'}</td>
                            <td className="px-4 py-2 font-mono text-gray-600">{app.sz || '-'}</td>
                            <td className="px-4 py-2 text-gray-600">{app.owner || '-'}</td>
                            <td className="px-4 py-2">
                              <div className="flex gap-1">
                                <button onClick={() => { setSelectedApp(app.app_id); setEditingAppId(app.app_id); setEditAppForm(app); }}
                                  className="px-2 py-1 text-xs text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Edit</button>
                                <button onClick={() => handleDeleteApp(app.app_id)}
                                  className="px-2 py-1 text-xs text-red-700 bg-red-50 rounded hover:bg-red-100">Delete</button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Policy Matrix Tab ── */}
        {activeTab === 'policy_matrix' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h3 className="text-sm font-semibold text-gray-800">Policy Matrix ({filteredPolicyMatrix.length} entries)</h3>
                <select className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-indigo-500"
                  value={policyEnvFilter} onChange={e => setPolicyEnvFilter(e.target.value)}>
                  <option value="all">All Environments (Combined)</option>
                  <option value="production">Production</option>
                  <option value="non_production">Non-Production</option>
                  <option value="pre_production">Pre-Production</option>
                </select>
              </div>
              <button onClick={() => setShowAddPolicy(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add Policy Entry</button>
            </div>

            {showAddPolicy && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
                <h3 className="text-sm font-semibold text-blue-800">Add Policy Entry</h3>
                <div className="grid grid-cols-7 gap-2">
                  <input className={inp} placeholder="Source Zone" value={String(newPolicyForm.source_zone || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, source_zone: e.target.value })} />
                  <input className={inp} placeholder="Source NH" value={String(newPolicyForm.source_nh || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, source_nh: e.target.value })} />
                  <input className={inp} placeholder="Dest Zone" value={String(newPolicyForm.dest_zone || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, dest_zone: e.target.value })} />
                  <input className={inp} placeholder="Dest NH" value={String(newPolicyForm.dest_nh || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, dest_nh: e.target.value })} />
                  <select className={inp} value={String(newPolicyForm.action || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, action: e.target.value })}>
                    <option value="Permit">Permit</option><option value="Block">Block</option><option value="Conditional">Conditional</option>
                  </select>
                  <input className={inp} placeholder="Environment" value={String(newPolicyForm.environment || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, environment: e.target.value })} />
                  <input className={inp} placeholder="Note" value={String(newPolicyForm.note || '')} onChange={e => setNewPolicyForm({ ...newPolicyForm, note: e.target.value })} />
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowAddPolicy(false)} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button onClick={handleAddPolicy} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
                </div>
              </div>
            )}

            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50"><tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Source Zone</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Source NH</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Dest Zone</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Dest NH</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Action</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">FW Traversal</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Environment</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Note</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Actions</th>
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredPolicyMatrix.map((entry, idx) => {
                      const isEditing = editingPolicyIdx === idx;
                      const actionStr = String((isEditing ? editPolicyForm.action : entry.action) || entry.rule || '').toLowerCase();
                      const isPermit = actionStr.includes('permit') || actionStr.includes('allow');
                      const isBlock = actionStr.includes('block') || actionStr.includes('deny');

                      if (isEditing) {
                        return (
                          <tr key={idx} className="bg-blue-50">
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.source_zone || editPolicyForm.src_zone || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, source_zone: e.target.value, src_zone: e.target.value })} /></td>
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.source_nh || editPolicyForm.src_nh || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, source_nh: e.target.value, src_nh: e.target.value })} /></td>
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.dest_zone || editPolicyForm.dst_zone || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, dest_zone: e.target.value, dst_zone: e.target.value })} /></td>
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.dest_nh || editPolicyForm.dst_nh || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, dest_nh: e.target.value, dst_nh: e.target.value })} /></td>
                            <td className="px-3 py-2">
                              <select className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.action || editPolicyForm.rule || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, action: e.target.value, rule: e.target.value })}>
                                <option value="Permit">Permit</option><option value="Block">Block</option><option value="Conditional">Conditional</option>
                              </select>
                            </td>
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.environment || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, environment: e.target.value })} /></td>
                            <td className="px-3 py-2"><input className="w-full px-2 py-1 text-xs border rounded" value={String(editPolicyForm.note || editPolicyForm.notes || '')} onChange={e => setEditPolicyForm({ ...editPolicyForm, note: e.target.value, notes: e.target.value })} /></td>
                            <td className="px-3 py-2">
                              <div className="flex gap-1">
                                <button onClick={() => setEditingPolicyIdx(null)} className="px-2 py-1 text-xs text-gray-600 border rounded hover:bg-gray-100">Cancel</button>
                                <button onClick={handleSavePolicy} className="px-2 py-1 text-xs text-white bg-indigo-600 rounded hover:bg-indigo-700">Save</button>
                              </div>
                            </td>
                          </tr>
                        );
                      }

                      return (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-3 py-2 font-mono text-gray-800">{String(entry.source_zone || entry.src_zone || '')}</td>
                          <td className="px-3 py-2 font-mono text-gray-600">{String(entry.source_nh || entry.src_nh || 'Any')}</td>
                          <td className="px-3 py-2 font-mono text-gray-800">{String(entry.dest_zone || entry.dst_zone || '')}</td>
                          <td className="px-3 py-2 font-mono text-gray-600">{String(entry.dest_nh || entry.dst_nh || 'Any')}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${isPermit ? 'bg-green-100 text-green-700' : isBlock ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                              {String(entry.action || entry.rule || 'N/A')}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-600">{String(entry.firewall_traversal || 'N/A')}</td>
                          <td className="px-3 py-2 text-gray-600">{String(entry.environment || 'All')}</td>
                          <td className="px-3 py-2 text-xs text-gray-500 max-w-[200px] truncate">{String(entry.note || entry.notes || '')}</td>
                          <td className="px-3 py-2">
                            <div className="flex gap-1">
                              <button onClick={() => { setEditingPolicyIdx(idx); setEditPolicyForm({ ...entry }); }}
                                className="px-2 py-1 text-xs text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Edit</button>
                              <button onClick={() => handleDeletePolicy(idx)}
                                className="px-2 py-1 text-xs text-red-700 bg-red-50 rounded hover:bg-red-100">Delete</button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── Naming Standards Tab ── */}
        {activeTab === 'naming_standards' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-800">Naming Convention Standards</h3>
              {editingNaming ? (
                <div className="flex gap-2">
                  <button onClick={() => setEditingNaming(false)} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button onClick={handleSaveNaming} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
                </div>
              ) : (
                <button onClick={() => setEditingNaming(true)}
                  className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100">Edit Standards</button>
              )}
            </div>
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs font-medium text-blue-600 mb-1">Group Prefix</p>
                    {editingNaming
                      ? <input className={inp + ' font-mono'} value={editNamingForm.group_prefix} onChange={e => setEditNamingForm({ ...editNamingForm, group_prefix: e.target.value })} />
                      : <p className="text-sm font-mono font-bold text-blue-800">{editNamingForm.group_prefix || 'grp-'}</p>}
                    <p className="text-xs text-blue-600 mt-1">
                      {editingNaming
                        ? <input className="w-full px-2 py-1 text-xs border rounded" value={editNamingForm.group_pattern} onChange={e => setEditNamingForm({ ...editNamingForm, group_pattern: e.target.value })} />
                        : editNamingForm.group_pattern}
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-xs font-medium text-green-600 mb-1">Server Prefix</p>
                    {editingNaming
                      ? <input className={inp + ' font-mono'} value={editNamingForm.server_prefix} onChange={e => setEditNamingForm({ ...editNamingForm, server_prefix: e.target.value })} />
                      : <p className="text-sm font-mono font-bold text-green-800">{editNamingForm.server_prefix || 'svr-'}</p>}
                    <p className="text-xs text-green-600 mt-1">
                      {editingNaming
                        ? <input className="w-full px-2 py-1 text-xs border rounded" value={editNamingForm.server_pattern} onChange={e => setEditNamingForm({ ...editNamingForm, server_pattern: e.target.value })} />
                        : editNamingForm.server_pattern}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <p className="text-xs font-medium text-purple-600 mb-1">Range Prefix</p>
                    {editingNaming
                      ? <input className={inp + ' font-mono'} value={editNamingForm.range_prefix} onChange={e => setEditNamingForm({ ...editNamingForm, range_prefix: e.target.value })} />
                      : <p className="text-sm font-mono font-bold text-purple-800">{editNamingForm.range_prefix || 'rng-'}</p>}
                    <p className="text-xs text-purple-600 mt-1">
                      {editingNaming
                        ? <input className="w-full px-2 py-1 text-xs border rounded" value={editNamingForm.range_pattern} onChange={e => setEditNamingForm({ ...editNamingForm, range_pattern: e.target.value })} />
                        : editNamingForm.range_pattern}
                    </p>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <h4 className="text-xs font-semibold text-gray-600 uppercase">Subtypes</h4>
                  <div className="flex flex-wrap gap-2">
                    {['APP', 'DB', 'WEB', 'API', 'MQ', 'BAT', 'SVC', 'LB', 'MON', 'NET'].map(st => (
                      <span key={st} className="px-3 py-1 text-xs font-mono font-medium bg-gray-100 text-gray-700 rounded-full border border-gray-200">{st}</span>
                    ))}
                  </div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mt-4">Security Zones</h4>
                  <div className="flex flex-wrap gap-2">
                    {['CDE', 'GEN', 'DMZ', 'MGT', 'RES', 'EXT', 'PAA', 'CPA', 'CCS', '3PY'].map(sz => (
                      <span key={sz} className="px-3 py-1 text-xs font-mono font-medium bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">{sz}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Firewall Devices Tab ── */}
        {activeTab === 'fw_devices' && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex items-center gap-3 flex-wrap">
              <select className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white" value={deviceFilter.dc} onChange={e => setDeviceFilter(f => ({ ...f, dc: e.target.value }))}>
                <option value="">All DCs</option>
                <option value="ALPHA_NGDC">ALPHA_NGDC</option>
                <option value="BETA_NGDC">BETA_NGDC</option>
                <option value="GAMMA_NGDC">GAMMA_NGDC</option>
              </select>
              <select className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white" value={deviceFilter.type} onChange={e => setDeviceFilter(f => ({ ...f, type: e.target.value }))}>
                <option value="">All Types</option>
                <option value="perimeter">Perimeter</option>
                <option value="segmentation">Segmentation</option>
                <option value="dmz">DMZ</option>
                <option value="paa">PAA</option>
              </select>
              <select className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white" value={deviceFilter.vendor} onChange={e => setDeviceFilter(f => ({ ...f, vendor: e.target.value }))}>
                <option value="">All Vendors</option>
                <option value="palo_alto">Palo Alto</option>
                <option value="checkpoint">Check Point</option>
                <option value="cisco_asa">Cisco ASA</option>
              </select>
              <span className="text-xs text-gray-500 ml-auto">{filteredDevices.length} devices</span>
              <button onClick={() => setShowAddDevice(!showAddDevice)}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add Device</button>
            </div>

            {/* Add Device Form */}
            {showAddDevice && (
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg space-y-3">
                <h4 className="text-sm font-semibold text-indigo-800">Add New Firewall Device</h4>
                <div className="grid grid-cols-4 gap-3">
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">Device ID</label>
                    <input type="text" className={inp} value={newDeviceForm.device_id as string} onChange={e => setNewDeviceForm(f => ({ ...f, device_id: e.target.value }))} placeholder="fw-PA-NH01-CPA" /></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
                    <input type="text" className={inp} value={newDeviceForm.name as string} onChange={e => setNewDeviceForm(f => ({ ...f, name: e.target.value }))} placeholder="Palo Alto NH01 CPA" /></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">Vendor</label>
                    <select className={inp} value={newDeviceForm.vendor as string} onChange={e => setNewDeviceForm(f => ({ ...f, vendor: e.target.value }))}>
                      <option value="palo_alto">Palo Alto</option><option value="checkpoint">Check Point</option><option value="cisco_asa">Cisco ASA</option>
                    </select></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">DC</label>
                    <select className={inp} value={newDeviceForm.dc as string} onChange={e => setNewDeviceForm(f => ({ ...f, dc: e.target.value }))}>
                      <option value="ALPHA_NGDC">ALPHA_NGDC</option><option value="BETA_NGDC">BETA_NGDC</option><option value="GAMMA_NGDC">GAMMA_NGDC</option>
                    </select></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">NH</label>
                    <input type="text" className={inp} value={newDeviceForm.nh as string} onChange={e => setNewDeviceForm(f => ({ ...f, nh: e.target.value }))} placeholder="NH01" /></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">SZ</label>
                    <input type="text" className={inp} value={newDeviceForm.sz as string} onChange={e => setNewDeviceForm(f => ({ ...f, sz: e.target.value }))} placeholder="CPA" /></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                    <select className={inp} value={newDeviceForm.type as string} onChange={e => setNewDeviceForm(f => ({ ...f, type: e.target.value }))}>
                      <option value="perimeter">Perimeter</option><option value="segmentation">Segmentation</option><option value="dmz">DMZ</option><option value="paa">PAA</option>
                    </select></div>
                  <div><label className="block text-xs font-medium text-gray-700 mb-1">Mgmt IP</label>
                    <input type="text" className={inp} value={newDeviceForm.mgmt_ip as string} onChange={e => setNewDeviceForm(f => ({ ...f, mgmt_ip: e.target.value }))} placeholder="10.x.x.x" /></div>
                </div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Capabilities (comma-separated)</label>
                  <input type="text" className={inp} value={newDeviceForm.capabilities as string} onChange={e => setNewDeviceForm(f => ({ ...f, capabilities: e.target.value }))} placeholder="L7 inspection, URL filtering" /></div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowAddDevice(false)} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button onClick={handleAddDevice} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Add Device</button>
                </div>
              </div>
            )}

            {/* Devices Table */}
            {loadingRef ? (
              <p className="text-sm text-gray-400 animate-pulse">Loading devices...</p>
            ) : (
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Device ID</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Name</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Vendor</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">DC</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">NH</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">SZ</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Type</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Status</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Mgmt IP</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {filteredDevices.map(dev => {
                      const devId = dev.device_id as string;
                      const isEditing = editingDeviceId === devId;
                      return (
                        <tr key={devId} className={isEditing ? 'bg-indigo-50' : 'hover:bg-gray-50'}>
                          <td className="px-3 py-2 font-mono font-medium text-gray-800">{devId}</td>
                          <td className="px-3 py-2">{isEditing
                            ? <input type="text" className="px-2 py-1 text-xs border rounded w-full" value={(editDeviceForm.name as string) || ''} onChange={e => setEditDeviceForm(f => ({ ...f, name: e.target.value }))} />
                            : (dev.name as string)}</td>
                          <td className="px-3 py-2">{isEditing
                            ? <select className="px-2 py-1 text-xs border rounded" value={(editDeviceForm.vendor as string) || ''} onChange={e => setEditDeviceForm(f => ({ ...f, vendor: e.target.value }))}>
                                <option value="palo_alto">Palo Alto</option><option value="checkpoint">Check Point</option><option value="cisco_asa">Cisco ASA</option>
                              </select>
                            : <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                dev.vendor === 'palo_alto' ? 'bg-blue-100 text-blue-700' :
                                dev.vendor === 'checkpoint' ? 'bg-purple-100 text-purple-700' :
                                'bg-amber-100 text-amber-700'
                              }`}>{dev.vendor === 'palo_alto' ? 'Palo Alto' : dev.vendor === 'checkpoint' ? 'Check Point' : 'Cisco ASA'}</span>}</td>
                          <td className="px-3 py-2">{dev.dc as string}</td>
                          <td className="px-3 py-2">{isEditing
                            ? <input type="text" className="px-2 py-1 text-xs border rounded w-16" value={(editDeviceForm.nh as string) || ''} onChange={e => setEditDeviceForm(f => ({ ...f, nh: e.target.value }))} />
                            : (dev.nh as string || '-')}</td>
                          <td className="px-3 py-2">{isEditing
                            ? <input type="text" className="px-2 py-1 text-xs border rounded w-16" value={(editDeviceForm.sz as string) || ''} onChange={e => setEditDeviceForm(f => ({ ...f, sz: e.target.value }))} />
                            : (dev.sz as string || '-')}</td>
                          <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            dev.type === 'perimeter' ? 'bg-red-100 text-red-700' :
                            dev.type === 'segmentation' ? 'bg-green-100 text-green-700' :
                            dev.type === 'dmz' ? 'bg-orange-100 text-orange-700' :
                            'bg-cyan-100 text-cyan-700'
                          }`}>{dev.type as string}</span></td>
                          <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            dev.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>{dev.status as string}</span></td>
                          <td className="px-3 py-2 font-mono text-gray-500">{isEditing
                            ? <input type="text" className="px-2 py-1 text-xs border rounded w-24" value={(editDeviceForm.mgmt_ip as string) || ''} onChange={e => setEditDeviceForm(f => ({ ...f, mgmt_ip: e.target.value }))} />
                            : (dev.mgmt_ip as string || '-')}</td>
                          <td className="px-3 py-2">
                            {isEditing ? (
                              <div className="flex gap-1">
                                <button onClick={handleSaveDevice} className="px-2 py-1 text-xs font-medium text-white bg-green-600 rounded hover:bg-green-700">Save</button>
                                <button onClick={() => setEditingDeviceId(null)} className="px-2 py-1 text-xs text-gray-600 border rounded hover:bg-gray-50">Cancel</button>
                              </div>
                            ) : (
                              <div className="flex gap-1">
                                <button onClick={() => { setEditingDeviceId(devId); setEditDeviceForm({ ...dev }); }} className="px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded">Edit</button>
                                <button onClick={() => handleDeleteDevice(devId)} className="px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded">Delete</button>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── User Groups Tab ── */}
        {activeTab === 'ad_groups' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => { setEditGroup({}); groupModal.open(null as unknown as ADUserGroup); }}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add Group</button>
            </div>
            <div className="space-y-3">
              {groups.filter(g => {
                if (!searchQuery.trim()) return true;
                const q = searchQuery.toLowerCase();
                return g.group_name.toLowerCase().includes(q) || g.access_type.toLowerCase().includes(q) || g.description.toLowerCase().includes(q);
              }).map(group => (
                <div key={group.id} className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 text-xs font-semibold rounded-full border ${ACCESS_COLORS[group.access_type]}`}>{group.access_type}</div>
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
                      <button onClick={() => { setEditGroup(group); groupModal.open(group); }}
                        className="px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded">Edit</button>
                      <button onClick={() => handleDeleteGroup(group.id)}
                        className="px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded">Delete</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Users Tab ── */}
        {activeTab === 'ad_users' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => { setEditUser({}); userModal.open(null as unknown as ADUser); }}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add User</button>
            </div>
            <div className="space-y-3">
              {users.filter(u => {
                if (!searchQuery.trim()) return true;
                const q = searchQuery.toLowerCase();
                return u.display_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || u.username.toLowerCase().includes(q);
              }).map(user => (
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
                    <button onClick={() => { setEditUser(user); userModal.open(user); }}
                      className="px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded">Edit</button>
                    <button onClick={() => handleDeleteUser(user.id)}
                      className="px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── AD Configuration Tab ── */}
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
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Server URL</label>
                  <input type="text" className={inp} value={adConfig.server_url} onChange={e => setAdConfig({ ...adConfig, server_url: e.target.value })} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Base DN</label>
                  <input type="text" className={inp} value={adConfig.base_dn} onChange={e => setAdConfig({ ...adConfig, base_dn: e.target.value })} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Bind User</label>
                  <input type="text" className={inp} value={adConfig.bind_user} onChange={e => setAdConfig({ ...adConfig, bind_user: e.target.value })} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Sync Interval (min)</label>
                  <input type="number" className={inp} value={adConfig.sync_interval_minutes} onChange={e => setAdConfig({ ...adConfig, sync_interval_minutes: Number(e.target.value) })} /></div>
              </div>
              <div><label className="block text-xs font-medium text-gray-700 mb-1">Search Filter</label>
                <input type="text" className={inp + ' font-mono'} value={adConfig.search_filter} onChange={e => setAdConfig({ ...adConfig, search_filter: e.target.value })} /></div>
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
              <button onClick={handleTestConnection}
                className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100">Test Connection</button>
              <button onClick={handleSaveConfig}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">Save Configuration</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Group Modal ── */}
      <Modal isOpen={groupModal.isOpen} onClose={groupModal.close} title={editGroup.id ? 'Edit Group' : 'Add Group'} size="md">
        <div className="space-y-4">
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Group Name</label>
            <input type="text" className={inp} value={editGroup.group_name || ''} onChange={e => setEditGroup({ ...editGroup, group_name: e.target.value })} placeholder="FW-GroupName" /></div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Access Type</label>
            <select className={inp} value={editGroup.access_type || 'Viewer'} onChange={e => setEditGroup({ ...editGroup, access_type: e.target.value as ADUserGroup['access_type'] })}>
              <option value="Admin">Admin</option><option value="Approver">Approver</option><option value="Operator">Operator</option><option value="Viewer">Viewer</option><option value="Auditor">Auditor</option>
            </select></div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <textarea className={inp} rows={2} value={editGroup.description || ''} onChange={e => setEditGroup({ ...editGroup, description: e.target.value })} /></div>
          <div className="flex justify-end gap-2">
            <button onClick={groupModal.close} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleSaveGroup} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
          </div>
        </div>
      </Modal>

      {/* ── User Modal ── */}
      <Modal isOpen={userModal.isOpen} onClose={userModal.close} title={editUser.id ? 'Edit User' : 'Add User'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Username</label>
              <input type="text" className={inp} value={editUser.username || ''} onChange={e => setEditUser({ ...editUser, username: e.target.value })} placeholder="john.doe" /></div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Display Name</label>
              <input type="text" className={inp} value={editUser.display_name || ''} onChange={e => setEditUser({ ...editUser, display_name: e.target.value })} placeholder="John Doe" /></div>
          </div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Email</label>
            <input type="email" className={inp} value={editUser.email || ''} onChange={e => setEditUser({ ...editUser, email: e.target.value })} placeholder="john@corp.local" /></div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Access Type</label>
            <select className={inp} value={editUser.access_type || 'Viewer'} onChange={e => setEditUser({ ...editUser, access_type: e.target.value as ADUser['access_type'] })}>
              <option value="Admin">Admin</option><option value="Approver">Approver</option><option value="Operator">Operator</option><option value="Viewer">Viewer</option><option value="Auditor">Auditor</option>
            </select></div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Groups (comma-separated)</label>
            <input type="text" className={inp} value={(editUser.groups || []).join(', ')} onChange={e => setEditUser({ ...editUser, groups: e.target.value.split(',').map(g => g.trim()).filter(Boolean) })} placeholder="FW-Admins, FW-Operators" /></div>
          {editUser.id && (
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-700">Active</label>
              <input type="checkbox" checked={editUser.is_active ?? true} onChange={e => setEditUser({ ...editUser, is_active: e.target.checked })} className="rounded border-gray-300 text-indigo-600" />
            </div>
          )}
          <div className="flex justify-end gap-2">
            <button onClick={userModal.close} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleSaveUser} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
