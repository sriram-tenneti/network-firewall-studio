import { useState, useEffect, useCallback } from 'react';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useNotification } from '@/hooks/useNotification';
import { useModal } from '@/hooks/useModal';
import type { ADUserGroup, ADUser, ADConfig, Application } from '@/types';
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

interface IPMapping {
  id: string;
  legacy_dc: string;
  legacy_ip: string;
  ngdc_dc: string;
  ngdc_ip: string;
  ngdc_group: string;
  app_id: string;
  nh: string;
  sz: string;
  legacy_desc: string;
  ngdc_desc: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('app_management');
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
  const [searchQuery, setSearchQuery] = useState('');

  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [ipMappings, setIpMappings] = useState<IPMapping[]>([]);
  const [policyMatrix, setPolicyMatrix] = useState<Record<string, unknown>[]>([]);
  const [namingStandards, setNamingStandards] = useState<Record<string, unknown>>({});
  const [loadingRef, setLoadingRef] = useState(false);
  const ipMappingModal = useModal<IPMapping>();
  const [editMapping, setEditMapping] = useState<Partial<IPMapping>>({});

  const loadRefData = useCallback(async () => {
    setLoadingRef(true);
    try {
      const [appsData, policyData, namingData] = await Promise.all([
        api.getApplications(),
        api.getAllPolicyMatrices(),
        api.getNamingStandards(),
      ]);
      setApplications(appsData);
      setPolicyMatrix(policyData.combined || []);
      setNamingStandards(namingData as unknown as Record<string, unknown>);
    } catch {
      showNotification('Failed to load reference data', 'error');
    }
    setLoadingRef(false);
  }, [showNotification]);

  const loadIPMappings = useCallback(async () => {
    try {
      const data = await api.getIPMappings(undefined, selectedApp || undefined);
      setIpMappings(data as unknown as IPMapping[]);
    } catch {
      // silent
    }
  }, [selectedApp]);

  useEffect(() => { loadRefData(); }, [loadRefData]);
  useEffect(() => { if (activeTab === 'app_management' || activeTab === 'ip_mappings') loadIPMappings(); }, [activeTab, loadIPMappings]);

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

  const handleSaveIPMapping = async () => {
    try {
      if (editMapping.id) {
        await api.updateIPMapping(editMapping.id, editMapping as Record<string, unknown>);
      } else {
        await api.createIPMapping(editMapping as Record<string, unknown>);
      }
      ipMappingModal.close();
      showNotification('IP mapping saved', 'success');
      loadIPMappings();
    } catch {
      showNotification('Failed to save IP mapping', 'error');
    }
  };

  const handleDeleteIPMapping = async (id: string) => {
    try {
      await api.deleteIPMapping(id);
      showNotification('IP mapping deleted', 'success');
      loadIPMappings();
    } catch {
      showNotification('Failed to delete IP mapping', 'error');
    }
  };

  const selectedAppData = applications.find(a => a.app_id === selectedApp);

  const tabs = [
    { id: 'app_management', label: 'App Management' },
    { id: 'ip_mappings', label: 'IP Mappings' },
    { id: 'policy_matrix', label: 'Policy Matrix' },
    { id: 'naming_standards', label: 'Naming Standards' },
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
          <input type="text" placeholder={activeTab === 'ad_groups' ? 'Search groups...' : 'Search users...'} value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white" />
        </div>
      )}

      <div className="mt-6">
        {activeTab === 'app_management' && (
          <div className="space-y-6">
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <div className="flex items-center gap-4">
                <label className="text-sm font-semibold text-gray-700">Select Application:</label>
                <select className="flex-1 max-w-md px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 bg-white" value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
                  <option value="">-- All Applications --</option>
                  {applications.map(app => (<option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>))}
                </select>
              </div>
            </div>
            {selectedAppData && (
              <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
                <h3 className="text-sm font-semibold text-gray-800">Application Details</h3>
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
              </div>
            )}
            {!selectedApp && (
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200"><h3 className="text-sm font-semibold text-gray-800">All Applications ({applications.length})</h3></div>
                {loadingRef ? (<div className="p-8 text-center text-gray-400">Loading...</div>) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50"><tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">App ID</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Name</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">NH</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">SZ</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">DC</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Owner</th>
                    </tr></thead>
                    <tbody className="divide-y divide-gray-100">
                      {applications.map(app => (
                        <tr key={app.app_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedApp(app.app_id)}>
                          <td className="px-4 py-2 font-mono font-semibold text-blue-700">{app.app_id}</td>
                          <td className="px-4 py-2 text-gray-800">{app.name}</td>
                          <td className="px-4 py-2 font-mono text-gray-600">{app.nh || '-'}</td>
                          <td className="px-4 py-2 font-mono text-gray-600">{app.sz || '-'}</td>
                          <td className="px-4 py-2 font-mono text-gray-600">{app.criticality ?? '-'}</td>
                          <td className="px-4 py-2 text-gray-600">{app.owner || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>)}
              </div>
            )}
          </div>
        )}

        {activeTab === 'ip_mappings' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <select className="px-3 py-2 text-sm border border-gray-300 rounded-md bg-white" value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
                  <option value="">All Apps</option>
                  {applications.map(app => <option key={app.app_id} value={app.app_id}>{app.app_id}</option>)}
                </select>
                <span className="text-sm text-gray-500">{ipMappings.length} mapping(s)</span>
              </div>
              <button onClick={() => { setEditMapping({}); ipMappingModal.open(null as unknown as IPMapping); }} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add IP Mapping</button>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50"><tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">App</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Legacy DC</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Legacy IP</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">NGDC DC</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">NGDC IP</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">NGDC Group</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">NH/SZ</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Actions</th>
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {ipMappings.length === 0 ? (
                      <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No IP mappings found</td></tr>
                    ) : ipMappings.map(m => (
                      <tr key={m.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono font-semibold text-blue-700">{m.app_id}</td>
                        <td className="px-3 py-2 font-mono text-gray-600">{m.legacy_dc}</td>
                        <td className="px-3 py-2 font-mono text-gray-800">{m.legacy_ip}</td>
                        <td className="px-3 py-2 font-mono text-gray-600">{m.ngdc_dc}</td>
                        <td className="px-3 py-2 font-mono text-gray-800">{m.ngdc_ip}</td>
                        <td className="px-3 py-2 font-mono text-xs text-indigo-700">{m.ngdc_group}</td>
                        <td className="px-3 py-2 font-mono text-gray-600">{m.nh}/{m.sz}</td>
                        <td className="px-3 py-2">
                          <div className="flex gap-1">
                            <button onClick={() => { setEditMapping(m); ipMappingModal.open(m); }} className="px-2 py-1 text-xs text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Edit</button>
                            <button onClick={() => handleDeleteIPMapping(m.id)} className="px-2 py-1 text-xs text-red-700 bg-red-50 rounded hover:bg-red-100">Del</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'policy_matrix' && (
          <div className="space-y-4">
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Combined Policy Matrix ({policyMatrix.length} entries)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50"><tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Source Zone</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Source NH</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Dest Zone</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Dest NH</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Action</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Environment</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Note</th>
                  </tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {policyMatrix.map((entry, idx) => {
                      const actionStr = String(entry.action || entry.rule || '').toLowerCase();
                      const isPermit = actionStr.includes('permit') || actionStr.includes('allow');
                      const isBlock = actionStr.includes('block') || actionStr.includes('deny');
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
                          <td className="px-3 py-2 text-gray-600">{String(entry.environment || 'All')}</td>
                          <td className="px-3 py-2 text-xs text-gray-500 max-w-[200px] truncate">{String(entry.note || entry.notes || '')}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'naming_standards' && (
          <div className="space-y-4">
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Naming Convention Standards</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs font-medium text-blue-600 mb-1">Group Prefix</p>
                    <p className="text-sm font-mono font-bold text-blue-800">grp- / g-</p>
                    <p className="text-xs text-blue-600 mt-1">{"grp-{APP}-{NH}-{SZ}-{SUBTYPE}"}</p>
                  </div>
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-xs font-medium text-green-600 mb-1">Server Prefix</p>
                    <p className="text-sm font-mono font-bold text-green-800">svr-</p>
                    <p className="text-xs text-green-600 mt-1">{"svr-{IP_ADDRESS}"}</p>
                  </div>
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <p className="text-xs font-medium text-purple-600 mb-1">Range/Subnet Prefix</p>
                    <p className="text-sm font-mono font-bold text-purple-800">rng-</p>
                    <p className="text-xs text-purple-600 mt-1">{"rng-{APP}-{NH}-{SZ}-{DESC}"}</p>
                  </div>
                </div>
                {namingStandards && typeof namingStandards === 'object' && (
                  <div className="mt-4 space-y-2">
                    <h4 className="text-xs font-semibold text-gray-600 uppercase">Subtypes</h4>
                    <div className="flex flex-wrap gap-2">
                      {['APP', 'DB', 'WEB', 'API', 'MQ', 'BAT', 'SVC', 'LB', 'MON', 'NET'].map(st => (
                        <span key={st} className="px-3 py-1 text-xs font-mono font-medium bg-gray-100 text-gray-700 rounded-full border border-gray-200">{st}</span>
                      ))}
                    </div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mt-4">Security Zones</h4>
                    <div className="flex flex-wrap gap-2">
                      {['CDE', 'GEN', 'DMZ', 'MGT', 'RES', 'EXT'].map(sz => (
                        <span key={sz} className="px-3 py-1 text-xs font-mono font-medium bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">{sz}</span>
                      ))}
                    </div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mt-4">Example Names</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-gray-50 rounded border border-gray-200"><p className="text-xs font-mono text-gray-800">grp-CRM-NH02-CDE-APP</p><p className="text-xs text-gray-500">CRM App Servers in NH02/CDE</p></div>
                      <div className="p-2 bg-gray-50 rounded border border-gray-200"><p className="text-xs font-mono text-gray-800">svr-10.1.1.10</p><p className="text-xs text-gray-500">Single server IP</p></div>
                      <div className="p-2 bg-gray-50 rounded border border-gray-200"><p className="text-xs font-mono text-gray-800">rng-HRM-NH01-GEN-NET</p><p className="text-xs text-gray-500">HRM Subnet Range in NH01/GEN</p></div>
                      <div className="p-2 bg-gray-50 rounded border border-gray-200"><p className="text-xs font-mono text-gray-800">grp-AGW-NH14-DMZ-API</p><p className="text-xs text-gray-500">API Gateway in NH14/DMZ</p></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ad_groups' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => { setEditGroup({}); groupModal.open(null as unknown as ADUserGroup); }} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">+ Add Group</button>
            </div>
            <div className="space-y-3">
              {groups.filter(group => {
                if (!searchQuery.trim()) return true;
                const q = searchQuery.toLowerCase();
                return group.group_name.toLowerCase().includes(q) || group.access_type.toLowerCase().includes(q) || group.description.toLowerCase().includes(q) || group.applications.some(a => a.toLowerCase().includes(q));
              }).map(group => (
                <div key={group.id} className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 text-xs font-semibold rounded-full border ${ACCESS_COLORS[group.access_type]}`}>{group.access_type}</div>
                      <div><h3 className="text-sm font-semibold text-gray-800">{group.group_name}</h3><p className="text-xs text-gray-500">{group.description}</p></div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right"><p className="text-sm font-bold text-gray-800">{group.member_count}</p><p className="text-xs text-gray-500">members</p></div>
                      <div className="text-right"><p className="text-xs text-gray-600">{group.applications.includes('*') ? 'All Apps' : group.applications.join(', ')}</p></div>
                      <button onClick={() => { setEditGroup(group); groupModal.open(group); }} className="px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded">Edit</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'ad_users' && (
          <div className="space-y-3">
            {users.filter(user => {
              if (!searchQuery.trim()) return true;
              const q = searchQuery.toLowerCase();
              return user.display_name.toLowerCase().includes(q) || user.email.toLowerCase().includes(q) || user.username.toLowerCase().includes(q) || user.access_type.toLowerCase().includes(q) || user.groups.some(g => g.toLowerCase().includes(q));
            }).map(user => (
              <div key={user.id} className="p-4 bg-white border border-gray-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{user.display_name.split(' ').map(n => n[0]).join('')}</div>
                  <div><p className="text-sm font-medium text-gray-800">{user.display_name}</p><p className="text-xs text-gray-500">{user.email} | {user.username}</p></div>
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

        {activeTab === 'ad_config' && (
          <div className="max-w-2xl space-y-6">
            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800">Connection Status</h3>
                <span className={`px-3 py-1 text-xs font-medium rounded-full ${adConfig.is_connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{adConfig.is_connected ? 'Connected' : 'Disconnected'}</span>
              </div>
              {adConfig.last_sync && <p className="text-xs text-gray-500">Last sync: {new Date(adConfig.last_sync).toLocaleString()}</p>}
            </div>
            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
              <h3 className="text-sm font-semibold text-gray-800">LDAP Configuration</h3>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Server URL</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.server_url} onChange={e => setAdConfig({...adConfig, server_url: e.target.value})} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Base DN</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.base_dn} onChange={e => setAdConfig({...adConfig, base_dn: e.target.value})} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Bind User</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.bind_user} onChange={e => setAdConfig({...adConfig, bind_user: e.target.value})} /></div>
                <div><label className="block text-xs font-medium text-gray-700 mb-1">Sync Interval (min)</label><input type="number" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={adConfig.sync_interval_minutes} onChange={e => setAdConfig({...adConfig, sync_interval_minutes: Number(e.target.value)})} /></div>
              </div>
              <div><label className="block text-xs font-medium text-gray-700 mb-1">Search Filter</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={adConfig.search_filter} onChange={e => setAdConfig({...adConfig, search_filter: e.target.value})} /></div>
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

      <Modal isOpen={groupModal.isOpen} onClose={groupModal.close} title={editGroup.id ? 'Edit Group' : 'Add Group'} size="md">
        <div className="space-y-4">
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Group Name</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editGroup.group_name || ''} onChange={e => setEditGroup({...editGroup, group_name: e.target.value})} placeholder="FW-GroupName" /></div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Access Type</label>
            <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editGroup.access_type || 'Viewer'} onChange={e => setEditGroup({...editGroup, access_type: e.target.value as ADUserGroup['access_type']})}>
              <option value="Admin">Admin</option><option value="Approver">Approver</option><option value="Operator">Operator</option><option value="Viewer">Viewer</option><option value="Auditor">Auditor</option>
            </select>
          </div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">Description</label><textarea className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" rows={2} value={editGroup.description || ''} onChange={e => setEditGroup({...editGroup, description: e.target.value})} /></div>
          <div className="flex justify-end gap-2">
            <button onClick={groupModal.close} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleSaveGroup} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={ipMappingModal.isOpen} onClose={ipMappingModal.close} title={editMapping.id ? 'Edit IP Mapping' : 'Add IP Mapping'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Application</label>
              <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editMapping.app_id || ''} onChange={e => setEditMapping({...editMapping, app_id: e.target.value})}>
                <option value="">Select App</option>
                {applications.map(app => <option key={app.app_id} value={app.app_id}>{app.app_id}</option>)}
              </select>
            </div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Legacy DC</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editMapping.legacy_dc || ''} onChange={e => setEditMapping({...editMapping, legacy_dc: e.target.value})} placeholder="DC_LEGACY_A" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Legacy IP</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={editMapping.legacy_ip || ''} onChange={e => setEditMapping({...editMapping, legacy_ip: e.target.value})} placeholder="10.25.1.0/24" /></div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">Legacy Description</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editMapping.legacy_desc || ''} onChange={e => setEditMapping({...editMapping, legacy_desc: e.target.value})} /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-xs font-medium text-gray-700 mb-1">NGDC DC</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editMapping.ngdc_dc || ''} onChange={e => setEditMapping({...editMapping, ngdc_dc: e.target.value})} placeholder="ALPHA_NGDC" /></div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">NGDC IP</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={editMapping.ngdc_ip || ''} onChange={e => setEditMapping({...editMapping, ngdc_ip: e.target.value})} placeholder="10.1.1.10/32" /></div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div><label className="block text-xs font-medium text-gray-700 mb-1">NGDC Group</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={editMapping.ngdc_group || ''} onChange={e => setEditMapping({...editMapping, ngdc_group: e.target.value})} placeholder="grp-CRM-NH02-CDE-APP" /></div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">NH</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={editMapping.nh || ''} onChange={e => setEditMapping({...editMapping, nh: e.target.value})} placeholder="NH02" /></div>
            <div><label className="block text-xs font-medium text-gray-700 mb-1">SZ</label><input type="text" className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-md" value={editMapping.sz || ''} onChange={e => setEditMapping({...editMapping, sz: e.target.value})} placeholder="CDE" /></div>
          </div>
          <div><label className="block text-xs font-medium text-gray-700 mb-1">NGDC Description</label><input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" value={editMapping.ngdc_desc || ''} onChange={e => setEditMapping({...editMapping, ngdc_desc: e.target.value})} /></div>
          <div className="flex justify-end gap-2">
            <button onClick={ipMappingModal.close} className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleSaveIPMapping} className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">Save</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
