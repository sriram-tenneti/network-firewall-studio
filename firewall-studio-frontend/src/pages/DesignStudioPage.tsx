import { useState, useEffect, useCallback } from 'react';
import { Plus } from 'lucide-react';
import { ActionBar } from '@/components/layout/ActionBar';
import { SourcePanel } from '@/components/design-studio/SourcePanel';
import { PolicyFlowCanvas } from '@/components/design-studio/PolicyFlowCanvas';
import { RuleLifecycleTable } from '@/components/design-studio/RuleLifecycleTable';
import { HistoryModal } from '@/components/design-studio/HistoryModal';
import { GroupManagementPanel } from '@/components/design-studio/GroupManagementPanel';
import type { SourceConfig, DestinationConfig, FirewallRule, PolicyValidationResult, PredefinedDestination, RuleHistoryEntry, NeighbourhoodRegistry, Application, NamingStandardsInfo } from '@/types';
import * as api from '@/lib/api';

export function DesignStudioPage() {
  const [source, setSource] = useState<SourceConfig>({
    source_type: 'Single IP',
    ip_address: '192.168.1.10',
    cidr: null,
    group_name: null,
    ports: 'TCP 8080',
    neighbourhood: 'Retail Digital - NON-PROD',
    security_zone: 'GEN',
  });

  const [destination, setDestination] = useState<DestinationConfig>({
    name: 'DIGITAL CHANNELS - PROD',
    security_zone: 'CDE',
    dest_ip: '10.1.2.50',
    ports: 'TCP 8443',
    is_predefined: true,
  });

  const [policyResult, setPolicyResult] = useState<PolicyValidationResult | null>(null);
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [predefinedDests, setPredefinedDests] = useState<PredefinedDestination[]>([]);
  const [neighbourhoods, setNeighbourhoods] = useState<NeighbourhoodRegistry[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [namingStandards, setNamingStandards] = useState<NamingStandardsInfo | null>(null);
  const [historyModal, setHistoryModal] = useState<{ ruleId: string; history: RuleHistoryEntry[] } | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [selectedAppFilter, setSelectedAppFilter] = useState<string>('');
  const [selectedRule, setSelectedRule] = useState<FirewallRule | null>(null);
  const [showGroupPanel, setShowGroupPanel] = useState(false);

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      const [rulesData, destsData, nhData, appsData, nsData] = await Promise.all([
        api.getRules(),
        api.getPredefinedDestinations(),
        api.getNeighbourhoods(),
        api.getApplications(),
        api.getNamingStandards(),
      ]);
      setRules(rulesData);
      setPredefinedDests(destsData);
      setNeighbourhoods(nhData);
      setApplications(appsData);
      setNamingStandards(nsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = selectedAppFilter
    ? rules.filter(r => r.application === selectedAppFilter && r.status !== 'Deleted')
    : rules.filter(r => r.status !== 'Deleted');

  const handleValidate = async () => {
    try {
      const result = await api.validatePolicy({
        source,
        destination,
        application: selectedAppFilter || 'ORD',
        environment: 'Production',
      });
      setPolicyResult(result);
    } catch (err) {
      console.error('Validation failed:', err);
    }
  };

  const handleDrop = (dest: { name: string; security_zone: string }) => {
    setDestination({ ...destination, name: dest.name, security_zone: dest.security_zone, is_predefined: true });
    setPolicyResult(null);
  };

  const handleCreateRule = async () => {
    try {
      await api.createRule({
        application: selectedAppFilter || 'ORD',
        environment: 'Production',
        datacenter: 'EAST_NGDC',
        source,
        destination,
        owner: 'Jon',
      });
      showNotification('Rule created successfully');
      loadData();
    } catch {
      showNotification('Failed to create rule', 'error');
    }
  };

  const handleModifyRule = (rule: FirewallRule) => {
    setSource(rule.source);
    setDestination(rule.destination);
    setSelectedRule(rule);
    setPolicyResult(null);
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
      await api.saveDraft(ruleId, { source, destination });
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

  const handleDragStart = (e: React.DragEvent, dest: PredefinedDestination) => {
    e.dataTransfer.setData('application/json', JSON.stringify({ name: dest.name, security_zone: dest.security_zone }));
    e.dataTransfer.effectAllowed = 'copy';
  };

  return (
    <div className="flex flex-col h-full">
      <ActionBar mode="design" />

      {/* Notification */}
      {notification && (
        <div className={`mx-6 mt-3 rounded-lg px-4 py-2.5 text-sm font-medium shadow-sm ${
          notification.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
          notification.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Rule Builder Section */}
      <div className="flex flex-1 gap-4 overflow-hidden p-4">
        {/* Left Panel: Source + Groups */}
        <div className="w-64 flex-shrink-0 overflow-y-auto space-y-3">
          <SourcePanel source={source} onChange={setSource} neighbourhoods={neighbourhoods} applications={applications} namingStandards={namingStandards} />
          <button
            onClick={() => setShowGroupPanel(!showGroupPanel)}
            className="w-full rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
          >
            {showGroupPanel ? 'Hide Group Management' : 'Manage Groups'}
          </button>
          {showGroupPanel && (
            <GroupManagementPanel
              appFilter={selectedAppFilter}
              onNotification={showNotification}
            />
          )}
        </div>

        {/* Center: Policy Flow + Create Button */}
        <div className="flex-1 overflow-y-auto space-y-4">
          <PolicyFlowCanvas
            source={source}
            destination={destination}
            policyResult={policyResult}
            onValidate={handleValidate}
            onDrop={handleDrop}
          />
          {/* Create Rule Button */}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={handleCreateRule}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
              {selectedRule ? `Update Rule ${selectedRule.rule_id}` : 'Create New Rule'}
            </button>
            {selectedRule && (
              <button
                onClick={() => { setSelectedRule(null); setPolicyResult(null); }}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancel Edit
              </button>
            )}
          </div>
        </div>

        {/* Right Panel: Destination */}
        <div className="w-64 flex-shrink-0 overflow-y-auto">
          <div className="flex flex-col rounded-xl border-2 border-orange-200 bg-orange-50/50 shadow-sm">
            <div className="rounded-t-xl bg-gradient-to-r from-amber-600 to-orange-500 px-4 py-3">
              <h3 className="text-base font-bold text-white">Destination</h3>
            </div>
            <div className="space-y-4 p-4">
              <div>
                <h4 className="mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Predefined Destinations</h4>
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {predefinedDests.map((pd) => (
                    <div
                      key={pd.name}
                      draggable
                      onDragStart={(e) => handleDragStart(e, pd)}
                      onClick={() => setDestination({
                        name: pd.name,
                        security_zone: pd.security_zone,
                        dest_ip: destination.dest_ip,
                        ports: destination.ports,
                        is_predefined: true,
                      })}
                      className={`flex items-start gap-2 rounded-lg px-3 py-2 text-left text-sm cursor-grab active:cursor-grabbing transition-all ${
                        destination.name === pd.name
                          ? 'bg-orange-100 border-2 border-orange-400 shadow-sm'
                          : 'bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-slate-800 text-xs truncate">{pd.name}</div>
                        <div className="text-xs text-slate-500">{pd.description || 'Security Zone'}</div>
                      </div>
                      <span className={`rounded-full border px-1.5 py-0.5 text-xs font-bold flex-shrink-0 ${
                        pd.security_zone === 'CDE' ? 'bg-orange-100 text-orange-700 border-orange-300' :
                        pd.security_zone === 'GEN' ? 'bg-green-100 text-green-700 border-green-300' :
                        pd.security_zone === 'DMZ' ? 'bg-purple-100 text-purple-700 border-purple-300' :
                        pd.security_zone === 'RST' ? 'bg-red-100 text-red-700 border-red-300' :
                        pd.security_zone === 'EXT' ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
                        'bg-slate-100 text-slate-700 border-slate-300'
                      }`}>
                        {pd.security_zone}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">Custom Destination</h4>
                <div className="space-y-2">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">Dest IP:</label>
                    <input
                      type="text"
                      value={destination.dest_ip || ''}
                      onChange={(e) => setDestination({ ...destination, dest_ip: e.target.value })}
                      placeholder="10.1.2.50"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">Ports:</label>
                    <select
                      value={destination.ports}
                      onChange={(e) => setDestination({ ...destination, ports: e.target.value })}
                      className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm"
                    >
                      <option>TCP 8443</option>
                      <option>TCP 443</option>
                      <option>TCP 1521</option>
                      <option>TCP 8080</option>
                      <option>TCP 22</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Collapsible Rule Lifecycle Table */}
      <div className="p-4 pt-0">
        <RuleLifecycleTable
          rules={filteredRules}
          applications={applications}
          selectedAppFilter={selectedAppFilter}
          onAppFilterChange={setSelectedAppFilter}
          onModify={handleModifyRule}
          onCertify={handleCertify}
          onDelete={handleDelete}
          onSubmit={handleSubmit}
          onViewHistory={handleViewHistory}
          onSaveDraft={handleSaveDraft}
          onRequestReview={handleRequestReview}
        />
      </div>

      {/* History Modal */}
      {historyModal && (
        <HistoryModal
          ruleId={historyModal.ruleId}
          history={historyModal.history}
          onClose={() => setHistoryModal(null)}
        />
      )}
    </div>
  );
}
