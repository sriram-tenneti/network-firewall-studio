import { useState, useEffect, useCallback } from 'react';
import {
  getAppEnvAssignments, getOrgConfig, getPolicyMatrix, getNamingStandards,
  updateOrgConfig, createPolicyEntry, deletePolicyEntry, updateNamingStandards,
} from '@/lib/api';
import { Shield, Server, Settings, FileText, ChevronRight, Save, Plus, Trash2, RefreshCw } from 'lucide-react';

type AdminTab = 'app-assignments' | 'naming-standards' | 'policy-matrix' | 'org-config';

const ADMIN_TABS: { key: AdminTab; label: string; icon: React.ReactNode; description: string }[] = [
  { key: 'app-assignments', label: 'App-Environment Assignments', icon: <Server className="h-4 w-4" />, description: '27 apps x 3 environments = 81 DC/NH/SZ assignments' },
  { key: 'naming-standards', label: 'Naming Standards', icon: <FileText className="h-4 w-4" />, description: 'NGDC naming conventions and enforcement rules' },
  { key: 'policy-matrix', label: 'Policy Matrix', icon: <Shield className="h-4 w-4" />, description: 'Zone-to-zone traffic policies (Permit/Block/Exception)' },
  { key: 'org-config', label: 'Organization Config', icon: <Settings className="h-4 w-4" />, description: 'Global org settings, ServiceNow, GitOps integration' },
];

const ENV_COLORS: Record<string, string> = {
  'Production': 'bg-red-100 text-red-700 border-red-200',
  'Non-Production': 'bg-blue-100 text-blue-700 border-blue-200',
  'Pre-Production': 'bg-amber-100 text-amber-700 border-amber-200',
};

interface AppEnvAssignment {
  app_id: string;
  environment: string;
  dc: string;
  nh: string;
  sz: string;
  criticality: number;
  pci_scope: boolean;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>('app-assignments');
  const [loading, setLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  // App-Environment state
  const [assignments, setAssignments] = useState<AppEnvAssignment[]>([]);
  const [envFilter, setEnvFilter] = useState<string>('');
  const [appFilter, setAppFilter] = useState<string>('');

  // Naming standards state
  const [namingStandards, setNamingStandards] = useState<Record<string, unknown>>({});

  // Policy matrix state
  const [policyMatrix, setPolicyMatrix] = useState<Record<string, unknown>[]>([]);
  const [newPolicyRow, setNewPolicyRow] = useState({ source_zone: '', dest_zone: '', default_action: 'Permitted', requires_exception: false, description: '' });
  const [showAddPolicy, setShowAddPolicy] = useState(false);

  // Org config state
  const [orgConfig, setOrgConfig] = useState<Record<string, unknown>>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'app-assignments': {
          const data = await getAppEnvAssignments();
          setAssignments(data as unknown as AppEnvAssignment[]);
          break;
        }
        case 'naming-standards': {
          const data = await getNamingStandards();
          setNamingStandards(data as unknown as Record<string, unknown>);
          break;
        }
        case 'policy-matrix': {
          const data = await getPolicyMatrix();
          setPolicyMatrix(data);
          break;
        }
        case 'org-config': {
          const data = await getOrgConfig();
          setOrgConfig(data);
          break;
        }
      }
    } catch (e) { console.error('Failed to load data', e); }
    setLoading(false);
  }, [activeTab]);

  useEffect(() => { loadData(); }, [loadData]);

  const showSaveMsg = () => { setSaveMsg('Saved!'); setTimeout(() => setSaveMsg(''), 2000); };

  // Filter assignments
  const filteredAssignments = assignments.filter(a => {
    if (envFilter && a.environment !== envFilter) return false;
    if (appFilter && !a.app_id.toLowerCase().includes(appFilter.toLowerCase())) return false;
    return true;
  });

  // Unique app IDs for stats
  const uniqueApps = [...new Set(assignments.map(a => a.app_id))];

  const handleSaveOrgConfig = async () => {
    try {
      const result = await updateOrgConfig(orgConfig);
      setOrgConfig(result);
      showSaveMsg();
    } catch (e) { console.error(e); alert('Save failed'); }
  };

  const handleSaveNamingStandards = async () => {
    try {
      const result = await updateNamingStandards(namingStandards);
      setNamingStandards(result as unknown as Record<string, unknown>);
      showSaveMsg();
    } catch (e) { console.error(e); alert('Save failed'); }
  };

  const handleAddPolicy = async () => {
    try {
      await createPolicyEntry(newPolicyRow);
      setShowAddPolicy(false);
      setNewPolicyRow({ source_zone: '', dest_zone: '', default_action: 'Permitted', requires_exception: false, description: '' });
      loadData();
      showSaveMsg();
    } catch (e) { console.error(e); alert('Add policy failed'); }
  };

  const handleDeletePolicy = async (sourceZone: string, destZone: string) => {
    if (!confirm(`Delete policy ${sourceZone} -> ${destZone}?`)) return;
    try {
      await deletePolicyEntry(sourceZone, destZone);
      loadData();
    } catch (e) { console.error(e); alert('Delete failed'); }
  };

  const renderAppAssignments = () => (
    <div>
      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-slate-800">{uniqueApps.length}</div>
          <div className="text-xs text-slate-500">Applications</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-slate-800">{assignments.length}</div>
          <div className="text-xs text-slate-500">Total Assignments</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-red-600">{assignments.filter(a => a.environment === 'Production').length}</div>
          <div className="text-xs text-slate-500">Production</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-blue-600">{assignments.filter(a => a.environment === 'Non-Production').length}</div>
          <div className="text-xs text-slate-500">Non-Production</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter by App ID..."
          value={appFilter}
          onChange={e => setAppFilter(e.target.value)}
          className="px-3 py-2 text-sm border rounded-lg w-48"
        />
        <select value={envFilter} onChange={e => setEnvFilter(e.target.value)} className="px-3 py-2 text-sm border rounded-lg">
          <option value="">All Environments</option>
          <option value="Production">Production</option>
          <option value="Non-Production">Non-Production</option>
          <option value="Pre-Production">Pre-Production</option>
        </select>
        <span className="text-xs text-slate-400 ml-auto">{filteredAssignments.length} of {assignments.length} assignments</span>
      </div>

      {/* Table */}
      <div className="overflow-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b">
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-24">App ID</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-36">Environment</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-28">Datacenter</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-20">NH</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-24">SZ</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-20">Crit.</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600 w-20">PCI</th>
            </tr>
          </thead>
          <tbody>
            {filteredAssignments.map((a, i) => (
              <tr key={`${a.app_id}-${a.environment}-${i}`} className="border-b hover:bg-slate-50/50">
                <td className="px-3 py-2 font-medium text-slate-800">{a.app_id}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${ENV_COLORS[a.environment] || 'bg-gray-100 text-gray-700'}`}>
                    {a.environment}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-600 font-mono text-xs">{a.dc}</td>
                <td className="px-3 py-2 text-slate-700 font-mono">{a.nh}</td>
                <td className="px-3 py-2">
                  <span className="px-1.5 py-0.5 text-xs font-medium rounded bg-purple-50 text-purple-700 border border-purple-200">{a.sz}</span>
                </td>
                <td className="px-3 py-2">
                  <span className={`text-xs font-bold ${a.criticality <= 2 ? 'text-red-600' : a.criticality <= 3 ? 'text-amber-600' : 'text-green-600'}`}>
                    {a.criticality}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span className={`w-2 h-2 inline-block rounded-full ${a.pci_scope ? 'bg-red-500' : 'bg-green-500'}`} />
                  <span className="ml-1 text-xs text-slate-500">{a.pci_scope ? 'Yes' : 'No'}</span>
                </td>
              </tr>
            ))}
            {filteredAssignments.length === 0 && (
              <tr><td colSpan={7} className="px-3 py-8 text-center text-slate-400">No assignments found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderNamingStandards = () => {
    const prefixes = (namingStandards.prefixes || {}) as Record<string, { description: string; pattern: string; example: string }>;
    const validNhIds = (namingStandards.valid_nh_ids || []) as string[];
    const validSzCodes = (namingStandards.valid_sz_codes || []) as string[];
    const validSubtypes = (namingStandards.valid_subtypes || {}) as Record<string, string>;
    const enforcementRules = (namingStandards.enforcement_rules || []) as string[];

    return (
      <div className="space-y-6">
        {/* Prefixes */}
        <div className="bg-white rounded-lg border p-5">
          <h3 className="font-semibold text-slate-700 mb-3">Naming Prefixes</h3>
          <div className="overflow-auto rounded border">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b">
                  <th className="px-3 py-2 text-left font-medium text-slate-600 w-24">Prefix</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Description</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Pattern</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600">Example</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(prefixes).map(([prefix, info]) => (
                  <tr key={prefix} className="border-b hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono font-bold text-indigo-600">{prefix}</td>
                    <td className="px-3 py-2 text-slate-700">{info.description}</td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-500">{info.pattern}</td>
                    <td className="px-3 py-2 font-mono text-xs text-green-700">{info.example}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Valid NH IDs and SZ Codes */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-lg border p-5">
            <h3 className="font-semibold text-slate-700 mb-3">Valid Neighbourhood IDs ({validNhIds.length})</h3>
            <div className="flex flex-wrap gap-1.5">
              {validNhIds.map(nh => (
                <span key={nh} className="px-2 py-1 text-xs font-mono bg-blue-50 text-blue-700 rounded border border-blue-200">{nh}</span>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg border p-5">
            <h3 className="font-semibold text-slate-700 mb-3">Valid Security Zone Codes ({validSzCodes.length})</h3>
            <div className="flex flex-wrap gap-1.5">
              {validSzCodes.map(sz => (
                <span key={sz} className="px-2 py-1 text-xs font-mono bg-purple-50 text-purple-700 rounded border border-purple-200">{sz}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Valid Subtypes */}
        <div className="bg-white rounded-lg border p-5">
          <h3 className="font-semibold text-slate-700 mb-3">Valid Subtypes ({Object.keys(validSubtypes).length})</h3>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(validSubtypes).map(([code, desc]) => (
              <div key={code} className="flex items-center gap-2 text-sm">
                <span className="font-mono font-bold text-slate-700 w-12">{code}</span>
                <span className="text-slate-500">{desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Enforcement Rules */}
        <div className="bg-white rounded-lg border p-5">
          <h3 className="font-semibold text-slate-700 mb-3">Enforcement Rules ({enforcementRules.length})</h3>
          <ul className="space-y-1.5">
            {enforcementRules.map((rule, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                {rule}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex gap-3">
          <button onClick={handleSaveNamingStandards} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 flex items-center gap-1.5">
            <Save className="h-4 w-4" />Save Naming Standards
          </button>
          {saveMsg && <span className="text-sm text-green-600 font-medium self-center">{saveMsg}</span>}
        </div>
      </div>
    );
  };

  const renderPolicyMatrix = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">{policyMatrix.length} policy entries</div>
        <button onClick={() => setShowAddPolicy(!showAddPolicy)} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500 flex items-center gap-1">
          <Plus className="h-4 w-4" />Add Policy
        </button>
      </div>

      {showAddPolicy && (
        <div className="bg-white rounded-lg border p-4 space-y-3">
          <h4 className="font-semibold text-slate-700">Add New Policy Entry</h4>
          <div className="grid grid-cols-4 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-500">Source Zone</label>
              <input type="text" value={newPolicyRow.source_zone} onChange={e => setNewPolicyRow({ ...newPolicyRow, source_zone: e.target.value })}
                className="w-full rounded border px-2 py-1.5 text-sm" placeholder="e.g. CDE" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500">Dest Zone</label>
              <input type="text" value={newPolicyRow.dest_zone} onChange={e => setNewPolicyRow({ ...newPolicyRow, dest_zone: e.target.value })}
                className="w-full rounded border px-2 py-1.5 text-sm" placeholder="e.g. GEN" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500">Action</label>
              <select value={newPolicyRow.default_action} onChange={e => setNewPolicyRow({ ...newPolicyRow, default_action: e.target.value })}
                className="w-full rounded border px-2 py-1.5 text-sm">
                <option value="Permitted">Permitted</option>
                <option value="Blocked">Blocked</option>
                <option value="Exception Required">Exception Required</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500">Description</label>
              <input type="text" value={newPolicyRow.description} onChange={e => setNewPolicyRow({ ...newPolicyRow, description: e.target.value })}
                className="w-full rounded border px-2 py-1.5 text-sm" placeholder="Optional" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-sm">
              <input type="checkbox" checked={newPolicyRow.requires_exception} onChange={e => setNewPolicyRow({ ...newPolicyRow, requires_exception: e.target.checked })} className="rounded" />
              Requires Exception
            </label>
            <div className="ml-auto flex gap-2">
              <button onClick={() => setShowAddPolicy(false)} className="rounded px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100">Cancel</button>
              <button onClick={handleAddPolicy} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500">Add</button>
            </div>
          </div>
        </div>
      )}

      <div className="overflow-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b">
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600">Source Zone</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600">Dest Zone</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600">Action</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600">Exception</th>
              <th className="px-3 py-2.5 text-left font-semibold text-slate-600">Description</th>
              <th className="px-3 py-2.5 text-right font-semibold text-slate-600 w-16">Del</th>
            </tr>
          </thead>
          <tbody>
            {policyMatrix.map((row, i) => {
              const action = String(row.action || row.default_action || '');
              const actionColor = action.startsWith('Permitted') ? 'bg-green-100 text-green-700' : action.includes('Blocked') ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700';
              return (
                <tr key={i} className="border-b hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-slate-700">{String(row.source_zone)}</td>
                  <td className="px-3 py-2 font-mono text-slate-700">{String(row.dest_zone)}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${actionColor}`}>{action}</span>
                  </td>
                  <td className="px-3 py-2">
                    {(row.requires_exception || String(row.action || row.default_action || '').includes('Exception')) ? <span className="text-xs text-red-600 font-medium">Yes</span> : <span className="text-xs text-slate-400">No</span>}
                  </td>
                  <td className="px-3 py-2 text-slate-500 text-xs">{String(row.reason || row.description || '')}</td>
                  <td className="px-3 py-2 text-right">
                    <button onClick={() => handleDeletePolicy(String(row.source_zone), String(row.dest_zone))} className="p-1 text-red-400 hover:text-red-600">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
            {policyMatrix.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-8 text-center text-slate-400">No policy entries</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderOrgConfig = () => {
    const fields = [
      { key: 'org_name', label: 'Organization Name' }, { key: 'org_code', label: 'Org Code' },
      { key: 'servicenow_instance', label: 'ServiceNow Instance' }, { key: 'servicenow_api_path', label: 'ServiceNow API Path' },
      { key: 'gitops_repo', label: 'GitOps Repository' }, { key: 'gitops_branch', label: 'GitOps Branch' },
      { key: 'notification_email', label: 'Notification Email' }, { key: 'notification_slack_channel', label: 'Slack Channel' },
      { key: 'max_rule_expiry_days', label: 'Max Rule Expiry (days)', type: 'number' },
    ];
    const boolFields = [
      { key: 'approval_required', label: 'Approval Required' },
      { key: 'auto_certify_birthright', label: 'Auto-Certify Birthright Rules' },
      { key: 'enforce_group_to_group', label: 'Enforce Group-to-Group' },
    ];
    return (
      <div className="bg-white rounded-lg border p-6 space-y-6">
        <h3 className="text-lg font-semibold text-slate-700">Organization Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          {fields.map(f => (
            <div key={f.key}>
              <label className="text-xs font-medium text-slate-500">{f.label}</label>
              <input type={f.type === 'number' ? 'number' : 'text'} value={String(orgConfig[f.key] ?? '')}
                onChange={e => setOrgConfig(prev => ({ ...prev, [f.key]: f.type === 'number' ? parseInt(e.target.value) : e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-4">
          {boolFields.map(f => (
            <label key={f.key} className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={Boolean(orgConfig[f.key])}
                onChange={e => setOrgConfig(prev => ({ ...prev, [f.key]: e.target.checked }))} className="rounded" />
              {f.label}
            </label>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleSaveOrgConfig} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 flex items-center gap-1.5">
            <Save className="h-4 w-4" />Save Configuration
          </button>
          {saveMsg && <span className="text-sm text-green-600 font-medium">{saveMsg}</span>}
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) return <div className="flex items-center justify-center py-16 text-slate-400">Loading...</div>;
    switch (activeTab) {
      case 'app-assignments': return renderAppAssignments();
      case 'naming-standards': return renderNamingStandards();
      case 'policy-matrix': return renderPolicyMatrix();
      case 'org-config': return renderOrgConfig();
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-white overflow-y-auto flex-shrink-0">
        <div className="p-4">
          <h2 className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-3">Admin Panel</h2>
          <p className="text-xs text-slate-400 mb-4">App-specific configuration and management</p>
          {ADMIN_TABS.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm mb-1 transition-colors text-left ${
                activeTab === t.key ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-50'
              }`}>
              {t.icon}
              <div className="flex-1 min-w-0">
                <div className="truncate">{t.label}</div>
                <div className="text-[10px] text-slate-400 truncate">{t.description}</div>
              </div>
              <ChevronRight className="h-3 w-3 opacity-40 flex-shrink-0" />
            </button>
          ))}
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl font-bold text-slate-800">{ADMIN_TABS.find(t => t.key === activeTab)?.label}</h2>
            <p className="text-sm text-slate-500 mt-0.5">{ADMIN_TABS.find(t => t.key === activeTab)?.description}</p>
          </div>
          <button onClick={loadData} className="rounded border px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 flex items-center gap-1.5">
            <RefreshCw className="h-3.5 w-3.5" />Refresh
          </button>
        </div>
        {renderContent()}
      </div>
    </div>
  );
}
