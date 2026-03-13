import { useState, useEffect, useCallback } from 'react';
import { Plus, X } from 'lucide-react';
import { ActionBar } from '@/components/layout/ActionBar';
import { PolicyFlowCanvas } from '@/components/design-studio/PolicyFlowCanvas';
import { RuleLifecycleTable } from '@/components/design-studio/RuleLifecycleTable';
import { HistoryModal } from '@/components/design-studio/HistoryModal';
import { GroupManagementPanel } from '@/components/design-studio/GroupManagementPanel';
import type { SourceConfig, DestinationConfig, FirewallRule, PolicyValidationResult, PredefinedDestination, RuleHistoryEntry, NeighbourhoodRegistry, Application, NamingStandardsInfo, SecurityZone, FirewallGroup } from '@/types';
import * as api from '@/lib/api';

export function DesignStudioPage() {
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [predefinedDests, setPredefinedDests] = useState<PredefinedDestination[]>([]);
  const [neighbourhoods, setNeighbourhoods] = useState<NeighbourhoodRegistry[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [namingStandards, setNamingStandards] = useState<NamingStandardsInfo | null>(null);
  const [securityZones, setSecurityZones] = useState<SecurityZone[]>([]);
  const [groups, setGroups] = useState<FirewallGroup[]>([]);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [selectedAppFilter, setSelectedAppFilter] = useState<string>('');
  const [selectedRule, setSelectedRule] = useState<FirewallRule | null>(null);
  const [historyModal, setHistoryModal] = useState<{ ruleId: string; history: RuleHistoryEntry[] } | null>(null);
  const [showRuleForm, setShowRuleForm] = useState(false);
  const [showGroupPanel, setShowGroupPanel] = useState(false);
  const [policyResult, setPolicyResult] = useState<PolicyValidationResult | null>(null);
  const [sourceType, setSourceType] = useState<'group' | 'ip' | 'cidr'>('group');
  const [sourceGroup, setSourceGroup] = useState('');
  const [sourceIp, setSourceIp] = useState('');
  const [sourceCidr, setSourceCidr] = useState('');
  const [sourceZone, setSourceZone] = useState('GEN');
  const [destType, setDestType] = useState<'predefined' | 'group' | 'custom'>('predefined');
  const [destPredefined, setDestPredefined] = useState('');
  const [destGroup, setDestGroup] = useState('');
  const [destCustomIp, setDestCustomIp] = useState('');
  const [destZone, setDestZone] = useState('CDE');
  const [destPorts, setDestPorts] = useState('TCP 8443');
  const [ruleApp, setRuleApp] = useState('');
  const [ruleEnv, setRuleEnv] = useState('Production');

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      const [rulesData, destsData, nhData, appsData, nsData, szData, grpData] = await Promise.all([
        api.getRules(), api.getPredefinedDestinations(), api.getNeighbourhoods(),
        api.getApplications(), api.getNamingStandards(), api.getSecurityZones(), api.getGroups(),
      ]);
      setRules(rulesData); setPredefinedDests(destsData); setNeighbourhoods(nhData);
      setApplications(appsData); setNamingStandards(nsData); setSecurityZones(szData); setGroups(grpData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = selectedAppFilter
    ? rules.filter(r => r.application === selectedAppFilter && r.status !== 'Deleted')
    : rules.filter(r => r.status !== 'Deleted');

  const filteredGroups = selectedAppFilter
    ? groups.filter(g => g.app_id === selectedAppFilter || !g.app_id)
    : groups;

  const buildSourceConfig = (): SourceConfig => {
    if (sourceType === 'group') return { source_type: 'Group', ip_address: null, cidr: null, group_name: sourceGroup, ports: destPorts, neighbourhood: null, security_zone: sourceZone };
    if (sourceType === 'cidr') return { source_type: 'Subnet', ip_address: null, cidr: sourceCidr, group_name: null, ports: destPorts, neighbourhood: null, security_zone: sourceZone };
    return { source_type: 'Single IP', ip_address: sourceIp, cidr: null, group_name: null, ports: destPorts, neighbourhood: null, security_zone: sourceZone };
  };

  const buildDestConfig = (): DestinationConfig => {
    if (destType === 'predefined') {
      const pd = predefinedDests.find(d => d.name === destPredefined);
      return { name: destPredefined, security_zone: pd?.security_zone || destZone, dest_ip: null, ports: destPorts, is_predefined: true };
    }
    if (destType === 'group') return { name: destGroup, security_zone: destZone, dest_ip: null, ports: destPorts, is_predefined: false };
    return { name: destCustomIp || 'Custom', security_zone: destZone, dest_ip: destCustomIp, ports: destPorts, is_predefined: false };
  };

  const handleValidate = async () => {
    try {
      const result = await api.validatePolicy({ source: buildSourceConfig(), destination: buildDestConfig(), application: ruleApp || selectedAppFilter || 'ORD', environment: ruleEnv });
      setPolicyResult(result);
    } catch (err) {
      console.error('Validation failed:', err);
    }
  };

  const handleCreateRule = async () => {
    try {
      await api.createRule({ application: ruleApp || selectedAppFilter || 'ORD', environment: ruleEnv, datacenter: 'ALPHA_NGDC', source: buildSourceConfig(), destination: buildDestConfig(), owner: 'System' });
      showNotification('Rule created successfully'); setShowRuleForm(false); loadData();
    } catch {
      showNotification('Failed to create rule', 'error');
    }
  };

  const handleModifyRule = (rule: FirewallRule) => {
    if (rule.source.group_name) { setSourceType('group'); setSourceGroup(rule.source.group_name); }
    else if (rule.source.cidr) { setSourceType('cidr'); setSourceCidr(rule.source.cidr); }
    else { setSourceType('ip'); setSourceIp(rule.source.ip_address || ''); }
    setSourceZone(rule.source.security_zone || 'GEN');
    if (rule.destination.is_predefined) { setDestType('predefined'); setDestPredefined(rule.destination.name); }
    else if (rule.destination.name.startsWith('grp-')) { setDestType('group'); setDestGroup(rule.destination.name); }
    else { setDestType('custom'); setDestCustomIp(rule.destination.dest_ip || ''); }
    setDestZone(rule.destination.security_zone || 'CDE');
    setDestPorts(rule.destination.ports || 'TCP 8443');
    setRuleApp(rule.application || '');
    setSelectedRule(rule); setShowRuleForm(true); setPolicyResult(null);
    showNotification(`Loaded rule ${rule.rule_id} for editing`, 'info');
  };

  const handleCertify = async (ruleId: string) => {
    try {
      await api.certifyRule(ruleId);
      showNotification(`Rule ${ruleId} certified`);
      loadData();
    } catch {
      showNotification('Failed to certify rule', 'error');
    }
  };

  const handleDelete = async (ruleId: string) => {
    try {
      await api.deleteRule(ruleId);
      showNotification(`Rule ${ruleId} deleted`);
      setSelectedRule(null);
      loadData();
    } catch {
      showNotification('Failed to delete rule', 'error');
    }
  };

  const handleSubmit = async (ruleId: string) => {
    try {
      await api.submitRule(ruleId);
      showNotification(`Rule ${ruleId} submitted for review`);
      setSelectedRule(null);
      loadData();
    } catch {
      showNotification('Failed to submit rule', 'error');
    }
  };

  const handleSaveDraft = async (ruleId: string) => {
    try {
      await api.saveDraft(ruleId, { source: buildSourceConfig(), destination: buildDestConfig() });
      showNotification(`Rule ${ruleId} draft saved`);
      loadData();
    } catch {
      showNotification('Failed to save draft', 'error');
    }
  };

  const handleViewHistory = async (ruleId: string) => {
    try {
      const history = await api.getRuleHistory(ruleId);
      setHistoryModal({ ruleId, history });
    } catch {
      showNotification('Failed to load history', 'error');
    }
  };

  const handleRequestReview = async (ruleId: string) => {
    showNotification(`Review requested for rule ${ruleId}`, 'info');
  };

  // Keep references alive for future use
  void neighbourhoods; void namingStandards; void securityZones;

  return (
    <div className="flex flex-col h-full">
      <ActionBar mode="design" />

      {notification && (
        <div className={`mx-6 mt-3 rounded-lg px-4 py-2.5 text-sm font-medium shadow-sm ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
          notification.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>{notification.message}</div>
      )}

      {/* Top toolbar */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => { setShowRuleForm(!showRuleForm); setSelectedRule(null); }}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors">
            <Plus className="h-4 w-4" />
            {showRuleForm ? 'Close Rule Form' : 'Create New Rule'}
          </button>
          <button onClick={() => setShowGroupPanel(!showGroupPanel)}
            className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors">
            {showGroupPanel ? 'Hide Groups' : 'Manage Groups'}
          </button>
        </div>
        <div className="text-xs text-slate-500">{filteredRules.length} rule(s) {selectedAppFilter ? `for ${selectedAppFilter}` : 'total'}</div>
      </div>

      {/* Rule Creation Form */}
      {showRuleForm && (
        <div className="mx-6 mt-4 rounded-xl border border-blue-200 bg-blue-50/30 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-800">{selectedRule ? `Edit Rule: ${selectedRule.rule_id}` : 'New Firewall Rule'}</h3>
            <button onClick={() => { setShowRuleForm(false); setSelectedRule(null); }} className="text-slate-400 hover:text-slate-600"><X className="h-4 w-4" /></button>
          </div>
          <div className="grid grid-cols-3 gap-6">
            {/* SOURCE */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-blue-700 uppercase tracking-wide">Source</h4>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Source Type</label>
                <select value={sourceType} onChange={(e) => setSourceType(e.target.value as 'group' | 'ip' | 'cidr')} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="group">Group</option><option value="ip">Single IP</option><option value="cidr">Subnet (CIDR)</option>
                </select></div>
              {sourceType === 'group' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">Source Group</label>
                <select value={sourceGroup} onChange={(e) => setSourceGroup(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="">Select a group...</option>
                  {filteredGroups.map(g => (<option key={g.name} value={g.name}>{g.name}</option>))}
                  {predefinedDests.map(pd => (<option key={`src-${pd.name}`} value={pd.name}>{pd.name}</option>))}
                </select></div>)}
              {sourceType === 'ip' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">IP Address</label>
                <input type="text" value={sourceIp} onChange={(e) => setSourceIp(e.target.value)} placeholder="192.168.1.10" className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm" /></div>)}
              {sourceType === 'cidr' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">Subnet (CIDR)</label>
                <input type="text" value={sourceCidr} onChange={(e) => setSourceCidr(e.target.value)} placeholder="10.1.0.0/24" className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm" /></div>)}
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Source Security Zone</label>
                <select value={sourceZone} onChange={(e) => setSourceZone(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="GEN">GEN - General</option><option value="CDE">CDE - Card Holder Data</option><option value="CCS">CCS - Critical Core Services</option>
                  <option value="CPA">CPA - Critical Payment Apps</option><option value="DMZ">DMZ - Demilitarized Zone</option><option value="RST">RST - Restricted</option><option value="PSE">PSE - Prod Simulation</option>
                </select></div>
            </div>
            {/* DESTINATION */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-orange-700 uppercase tracking-wide">Destination</h4>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Destination Type</label>
                <select value={destType} onChange={(e) => setDestType(e.target.value as 'predefined' | 'group' | 'custom')} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="predefined">Predefined Destination</option><option value="group">Group</option><option value="custom">Custom IP</option>
                </select></div>
              {destType === 'predefined' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">Predefined Destination</label>
                <select value={destPredefined} onChange={(e) => setDestPredefined(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="">Select destination...</option>
                  {predefinedDests.map(pd => (<option key={pd.name} value={pd.name}>{pd.friendly_name || pd.name} ({pd.security_zone})</option>))}
                </select></div>)}
              {destType === 'group' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">Destination Group</label>
                <select value={destGroup} onChange={(e) => setDestGroup(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="">Select a group...</option>
                  {filteredGroups.map(g => (<option key={g.name} value={g.name}>{g.name}</option>))}
                </select></div>)}
              {destType === 'custom' && (<div><label className="block text-xs font-medium text-slate-600 mb-1">Destination IP</label>
                <input type="text" value={destCustomIp} onChange={(e) => setDestCustomIp(e.target.value)} placeholder="10.1.2.50" className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm" /></div>)}
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Destination Security Zone</label>
                <select value={destZone} onChange={(e) => setDestZone(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="GEN">GEN - General</option><option value="CDE">CDE - Card Holder Data</option><option value="CCS">CCS - Critical Core Services</option>
                  <option value="CPA">CPA - Critical Payment Apps</option><option value="DMZ">DMZ - Demilitarized Zone</option><option value="RST">RST - Restricted</option><option value="PSE">PSE - Prod Simulation</option>
                </select></div>
            </div>
            {/* PORTS & CONTEXT */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-green-700 uppercase tracking-wide">Ports &amp; Context</h4>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Port / Protocol</label>
                <select value={destPorts} onChange={(e) => setDestPorts(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option>TCP 8443</option><option>TCP 443</option><option>TCP 1521</option><option>TCP 8080</option><option>TCP 22</option>
                  <option>TCP 3306</option><option>TCP 5432</option><option>TCP 3270</option><option>UDP 53</option><option>ANY</option>
                </select></div>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Application</label>
                <select value={ruleApp} onChange={(e) => setRuleApp(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option value="">Select application...</option>
                  {applications.map(app => (<option key={app.app_id} value={app.app_id}>{app.app_distributed_id || app.app_id} - {app.name}</option>))}
                </select></div>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Environment</label>
                <select value={ruleEnv} onChange={(e) => setRuleEnv(e.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm">
                  <option>Production</option><option>Non-Production</option><option>Pre-Production</option><option>Development</option><option>DR</option>
                </select></div>
              <div className="flex items-center gap-2 pt-2">
                <button onClick={handleValidate} className="rounded-md border border-blue-300 bg-white px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-50 transition-colors">Validate Policy</button>
                <button onClick={handleCreateRule} className="rounded-md bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors">{selectedRule ? 'Update Rule' : 'Create Rule'}</button>
                {selectedRule && (<button onClick={() => { setSelectedRule(null); setShowRuleForm(false); }} className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">Cancel</button>)}
              </div>
            </div>
          </div>
          {policyResult && (<div className="mt-4"><PolicyFlowCanvas source={buildSourceConfig()} destination={buildDestConfig()} policyResult={policyResult} onValidate={handleValidate} onDrop={() => {}} /></div>)}
        </div>
      )}

      {/* Group Management Panel */}
      {showGroupPanel && (<div className="mx-6 mt-4"><GroupManagementPanel appFilter={selectedAppFilter} onNotification={showNotification} /></div>)}

      {/* Rule Lifecycle Table with checkbox selection */}
      <div className="flex-1 overflow-y-auto p-4">
        <RuleLifecycleTable rules={filteredRules} applications={applications} selectedAppFilter={selectedAppFilter} onAppFilterChange={setSelectedAppFilter}
          onModify={handleModifyRule} onCertify={handleCertify} onDelete={handleDelete} onSubmit={handleSubmit}
          onViewHistory={handleViewHistory} onSaveDraft={handleSaveDraft} onRequestReview={handleRequestReview} />
      </div>

      {historyModal && (<HistoryModal ruleId={historyModal.ruleId} history={historyModal.history} onClose={() => setHistoryModal(null)} />)}
    </div>
  );
}
