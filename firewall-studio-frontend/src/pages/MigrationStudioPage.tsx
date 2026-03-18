import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import {
  getLegacyRules, submitLegacyRulesForReview,
  migrateRulesToNGDC, getNGDCRecommendations, compileLegacyRule,
  validateBirthright, getGroups, importRulesToNGDC,
  createMigrationGroup,
} from '@/lib/api';
import type { LegacyRule, NGDCRecommendation, IPMapping, CompiledRule, BirthrightValidation, FirewallGroup } from '@/types';
import type { Column } from '@/components/shared/DataTable';

function BirthrightPanel({ validation }: { validation: BirthrightValidation | null }) {
  if (!validation) return null;
  return (
    <div className="border rounded-lg overflow-hidden">
      <div className={`px-3 py-2 border-b ${validation.compliant ? 'bg-green-50' : 'bg-red-50'}`}>
        <h3 className={`text-sm font-semibold ${validation.compliant ? 'text-green-800' : 'text-red-800'}`}>
          Birthright Validation: {validation.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">{validation.summary}</p>
      </div>
      <div className="p-3 space-y-2">
        {validation.violations.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-red-700 mb-1">Violations ({validation.violations.length})</h4>
            {validation.violations.map((v, i) => (
              <div key={i} className="text-xs bg-red-50 rounded px-2 py-1 mb-1">
                <span className="font-medium">{v.matrix}</span>: {v.rule} - <span className="text-red-700">{v.action}</span>
                <div className="text-gray-500">{v.reason}</div>
              </div>
            ))}
          </div>
        )}
        {validation.warnings.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-amber-700 mb-1">Warnings ({validation.warnings.length})</h4>
            {validation.warnings.map((v, i) => (
              <div key={i} className="text-xs bg-amber-50 rounded px-2 py-1 mb-1">
                <span className="font-medium">{v.matrix}</span>: {v.rule} - {v.reason}
              </div>
            ))}
          </div>
        )}
        {validation.permitted.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-green-700 mb-1">Permitted ({validation.permitted.length})</h4>
            {validation.permitted.map((v, i) => (
              <div key={i} className="text-xs bg-green-50 rounded px-2 py-1 mb-1">
                <span className="font-medium">{v.matrix}</span>: {v.rule} - {v.reason}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface GroupProvisioningSectionProps {
  compiledRule: CompiledRule | null;
}

function GroupProvisioningSection({ compiledRule }: GroupProvisioningSectionProps) {
  if (!compiledRule) return null;
  const raw = compiledRule as unknown as Record<string, unknown>;
  if (!raw.group_provisioning) return null;
  const gp = raw.group_provisioning as {
    status: string; message?: string; provisioned_count?: number; total_groups?: number;
    provisioned?: { name: string; members: string[]; device_command: string }[];
    violations?: string[];
  };
  return (
    <div className="border-t border-gray-700 mt-3 pt-3">
      <h4 className="text-xs font-semibold text-blue-300 mb-2">Group Submission to Firewall Device</h4>
      <div className="flex items-center gap-3 text-xs mb-2">
        <span className={`px-2 py-0.5 rounded-full font-medium ${
          gp.status === 'success' ? 'bg-green-900 text-green-300' :
          gp.status === 'partial' ? 'bg-amber-900 text-amber-300' : 'bg-red-900 text-red-300'
        }`}>
          {gp.status === 'success' ? 'All Groups Submitted' : gp.status === 'partial' ? 'Partial' : 'Failed'}
        </span>
        <span className="text-gray-400">{gp.provisioned_count ?? 0}/{gp.total_groups ?? 0} groups</span>
      </div>
      {gp.message && (
        <p className="text-xs text-gray-400 italic mb-2">{gp.message}</p>
      )}
      {(gp.provisioned ?? []).map((g, i) => (
        <div key={i} className="bg-gray-800 rounded p-2 mb-1 text-xs">
          <span className="text-gray-300 font-medium">{g.name}</span>
          <span className="text-gray-500 ml-2">({g.members.length} members)</span>
          <pre className="text-blue-400 font-mono mt-1 text-[10px]">{g.device_command}</pre>
        </div>
      ))}
      {(gp.violations?.length ?? 0) > 0 && (
        <div className="bg-red-900/30 rounded p-2 mt-1">
          <span className="text-xs text-red-400 font-medium">NGDC Violations:</span>
          {(gp.violations ?? []).map((v, i) => (
            <div key={i} className="text-xs text-red-300 ml-2">- {v}</div>
          ))}
        </div>
      )}
    </div>
  );
}

export function MigrationStudioPage() {
  const [legacyRules, setLegacyRules] = useState<LegacyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('All');
  const [selectedRuleIds, setSelectedRuleIds] = useState<Set<string>>(new Set());
  const detailModal = useModal<LegacyRule>();
  const { notification, showNotification } = useNotification();

  // Migration popup state
  const [migrateRule, setMigrateRule] = useState<LegacyRule | null>(null);
  const [recommendation, setRecommendation] = useState<NGDCRecommendation | null>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [customMappings, setCustomMappings] = useState<IPMapping[]>([]);
  const [customDestMappings, setCustomDestMappings] = useState<IPMapping[]>([]);
  const [selectedNh, setSelectedNh] = useState('');
  const [selectedSz, setSelectedSz] = useState('');
  const [compiledRule, setCompiledRule] = useState<CompiledRule | null>(null);
  const [compileVendor, setCompileVendor] = useState('generic');
  const [compiling, setCompiling] = useState(false);
  const [birthrightResult, setBirthrightResult] = useState<BirthrightValidation | null>(null);
  const [validatingBirthright, setValidatingBirthright] = useState(false);
  const [migrateComments, setMigrateComments] = useState('');
  const [submittingMigration, setSubmittingMigration] = useState(false);
  const [appGroups, setAppGroups] = useState<FirewallGroup[]>([]);
  const [migrationStep, setMigrationStep] = useState<'review' | 'mapping' | 'compile' | 'submit'>('review');

  // Import from NFR state
  const [showImportPanel, setShowImportPanel] = useState(false);
  const [nfrApps, setNfrApps] = useState<{ value: string; label: string }[]>([]);
  const [selectedImportApps, setSelectedImportApps] = useState<Set<string>>(new Set());
  const [importing, setImporting] = useState(false);
  // New group creation during migration
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState<{ type: string; value: string }[]>([{ type: 'ip', value: '' }]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const rulesData = await getLegacyRules(selectedApp || undefined, true);
      setLegacyRules(rulesData);
    } catch {
      showNotification('Failed to load migration data', 'error');
    }
    setLoading(false);
  }, [selectedApp, showNotification]);

  useEffect(() => { loadData(); }, [loadData]);

  const filteredRules = legacyRules.filter(r => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Non-Standard') return !r.is_standard;
    if (activeTab === 'Standard') return r.is_standard;
    return r.migration_status === activeTab;
  });

  const counts = {
    All: legacyRules.length,
    'Non-Standard': legacyRules.filter(r => !r.is_standard).length,
    Standard: legacyRules.filter(r => r.is_standard).length,
    'Not Started': legacyRules.filter(r => r.migration_status === 'Not Started').length,
    'In Progress': legacyRules.filter(r => r.migration_status === 'In Progress').length,
  };

  const appOptions = Array.from(new Set(legacyRules.map(r => `${r.app_id}|${r.app_distributed_id}|${r.app_name}`))).map(key => {
    const [appId, distId, appName] = key.split('|');
    return { value: String(appId), label: `${appId} - ${appName} (${distId})` };
  });

  const toggleSelection = (ruleId: string) => {
    setSelectedRuleIds(prev => {
      const next = new Set(prev);
      if (next.has(ruleId)) next.delete(ruleId); else next.add(ruleId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedRuleIds.size === filteredRules.length) setSelectedRuleIds(new Set());
    else setSelectedRuleIds(new Set(filteredRules.map(r => r.id)));
  };

  const handleSubmitForReview = async () => {
    if (selectedRuleIds.size === 0) { showNotification('Select rules to submit for review', 'error'); return; }
    try {
      const result = await submitLegacyRulesForReview(Array.from(selectedRuleIds));
      showNotification(`${result.submitted} rules submitted for review`, 'success');
      setSelectedRuleIds(new Set()); loadData();
    } catch { showNotification('Failed to submit for review', 'error'); }
  };

  const handleMigrateSelected = async () => {
    if (selectedRuleIds.size === 0) { showNotification('Select rules to migrate', 'error'); return; }
    try {
      const result = await migrateRulesToNGDC(Array.from(selectedRuleIds));
      showNotification(`${result.migrated} rules migrated to NGDC`, 'success');
      setSelectedRuleIds(new Set()); loadData();
    } catch { showNotification('Failed to migrate rules', 'error'); }
  };

  const openMigratePopup = async (rule: LegacyRule) => {
    setMigrateRule(rule); setLoadingRec(true); setCompiledRule(null);
    setBirthrightResult(null); setMigrateComments(''); setMigrationStep('review');
    try {
      const rec = await getNGDCRecommendations(rule.id);
      setRecommendation(rec);
      setCustomMappings(rec.source_mappings.map(m => ({ ...m })));
      setCustomDestMappings(rec.destination_mappings.map(m => ({ ...m })));
      setSelectedNh(rec.recommended_nh); setSelectedSz(rec.recommended_sz);
    } catch { setRecommendation(null); showNotification('Failed to load NGDC recommendations', 'error'); }
    try { const groups = await getGroups(String(rule.app_id)); setAppGroups(groups); }
    catch { setAppGroups([]); }
    setLoadingRec(false);
  };

  const closeMigratePopup = () => {
    setMigrateRule(null); setRecommendation(null); setCustomMappings([]);
    setCustomDestMappings([]); setCompiledRule(null); setBirthrightResult(null); setAppGroups([]);
  };

  const handleCompileMigration = async () => {
    if (!migrateRule) return; setCompiling(true);
    try {
      const result = await compileLegacyRule(migrateRule.id, compileVendor);
      setCompiledRule(result); setMigrationStep('compile');
    } catch { showNotification('Failed to compile rule', 'error'); }
    setCompiling(false);
  };

  const handleValidateBirthright = async () => {
    if (!migrateRule) return; setValidatingBirthright(true);
    try {
      const result = await validateBirthright({
        source_zone: migrateRule.rule_source_zone,
        destination_zone: migrateRule.rule_destination_zone,
        action: migrateRule.rule_action,
        service: migrateRule.rule_service,
        app_id: String(migrateRule.app_id),
      });
      setBirthrightResult(result);
    } catch { showNotification('Failed to validate birthright', 'error'); }
    setValidatingBirthright(false);
  };

  const handleSubmitMigrationForReview = async () => {
    if (!migrateRule) return; setSubmittingMigration(true);
    try {
      await submitLegacyRulesForReview([migrateRule.id]);
      showNotification('Migration submitted for review', 'success');
      closeMigratePopup(); loadData();
    } catch { showNotification('Failed to submit migration for review', 'error'); }
    setSubmittingMigration(false);
  };

  const updateSourceMapping = (index: number, field: string, value: string) => {
    setCustomMappings(prev => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };
  const updateDestMapping = (index: number, field: string, value: string) => {
    setCustomDestMappings(prev => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };

  const parseExpandedTree = (text: string): string[] => {
    if (!text) return [];
    return text.split('\n').map(line => line.replace(/\t/g, '  '));
  };

  // Import from Network Firewall Request
  const handleLoadNfrApps = async () => {
    try {
      const allRules = await getLegacyRules(undefined, true);
      const apps = Array.from(new Set(allRules.map(r => `${r.app_id}|${r.app_distributed_id}|${r.app_name}`))).map(key => {
        const [appId, distId, appName] = key.split('|');
        return { value: String(appId), label: `${appId} - ${appName} (${distId})` };
      });
      setNfrApps(apps);
      setShowImportPanel(true);
    } catch { showNotification('Failed to load NFR applications', 'error'); }
  };

  const handleImportFromNFR = async () => {
    if (selectedImportApps.size === 0) { showNotification('Select at least one application to import', 'error'); return; }
    setImporting(true);
    try {
      const result = await importRulesToNGDC(Array.from(selectedImportApps));
      showNotification(`Imported ${result.imported} rules from Network Firewall Request`, 'success');
      setShowImportPanel(false);
      setSelectedImportApps(new Set());
      loadData();
    } catch { showNotification('Failed to import rules from NFR', 'error'); }
    setImporting(false);
  };

  const toggleImportApp = (appId: string) => {
    setSelectedImportApps(prev => {
      const next = new Set(prev);
      if (next.has(appId)) next.delete(appId); else next.add(appId);
      return next;
    });
  };

  const selectAllImportApps = () => {
    if (selectedImportApps.size === nfrApps.length) setSelectedImportApps(new Set());
    else setSelectedImportApps(new Set(nfrApps.map(a => a.value)));
  };

  // Create new group during migration
  const handleCreateMigrationGroup = async () => {
    if (!newGroupName.trim() || !migrateRule) { showNotification('Group name is required', 'error'); return; }
    const validMembers = newGroupMembers.filter(m => m.value.trim());
    if (validMembers.length === 0) { showNotification('Add at least one member', 'error'); return; }
    try {
      await createMigrationGroup({
        name: newGroupName,
        app_id: String(migrateRule.app_id),
        members: validMembers,
        nh: selectedNh,
        sz: selectedSz,
      });
      showNotification(`Group "${newGroupName}" created successfully`, 'success');
      setShowNewGroupModal(false);
      setNewGroupName('');
      setNewGroupMembers([{ type: 'ip', value: '' }]);
      // Refresh groups
      const groups = await getGroups(String(migrateRule.app_id));
      setAppGroups(groups);
    } catch { showNotification('Failed to create migration group', 'error'); }
  };

  const columns: Column<LegacyRule>[] = [
    {
      key: '_select', header: '', sortable: false, width: '40px',
      render: (_, row) => (
        <input type="checkbox" checked={selectedRuleIds.has(row.id)} onChange={() => toggleSelection(row.id)}
          onClick={e => e.stopPropagation()} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
      ),
    },
    { key: 'id', header: 'Rule ID', sortable: true, width: '80px' },
    { key: 'app_id', header: 'App ID', sortable: true, width: '70px',
      render: (_, row) => <span className="text-xs">{String(row.app_id)}</span>,
    },
    { key: 'app_distributed_id', header: 'Dist ID', sortable: true, width: '70px' },
    { key: 'app_name', header: 'App Name', sortable: true, width: '110px' },
    { key: 'inventory_item', header: 'Inventory', sortable: true, width: '120px' },
    { key: 'policy_name', header: 'Policy', sortable: true, width: '90px' },
    { key: 'rule_action', header: 'Action', sortable: true, width: '70px',
      render: (_, row) => (
        <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${row.rule_action === 'Accept' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {row.rule_action}
        </span>
      ),
    },
    {
      key: 'rule_source', header: 'Source', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_source || '').split('\n').filter(Boolean);
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_source_zone', header: 'Src Zone', sortable: true, width: '100px' },
    {
      key: 'rule_destination', header: 'Destination', sortable: false, width: '150px',
      render: (_, row) => {
        const entries = (row.rule_destination || '').split('\n').filter(Boolean);
        return <span className="font-mono text-xs">{entries.slice(0, 2).join(', ')}{entries.length > 2 ? ` +${entries.length - 2}` : ''}</span>;
      },
    },
    { key: 'rule_destination_zone', header: 'Dst Zone', sortable: true, width: '90px' },
    {
      key: 'rule_service', header: 'Service', sortable: false, width: '100px',
      render: (_, row) => <span className="text-xs">{row.rule_service || 'N/A'}</span>,
    },
    {
      key: 'migration_status', header: 'Status', sortable: true, width: '100px',
      render: (_, row) => <StatusBadge status={row.migration_status} />,
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '130px',
      render: (_, row) => (
        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
          <button onClick={() => detailModal.open(row)} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">View</button>
          <button onClick={() => openMigratePopup(row)} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100">Migrate</button>
        </div>
      ),
    },
  ];

  const tabs = [
    { id: 'All', label: 'All Rules', count: counts.All },
    { id: 'Non-Standard', label: 'Non-Standard', count: counts['Non-Standard'] },
    { id: 'Standard', label: 'Standard', count: counts.Standard },
    { id: 'Not Started', label: 'Not Started', count: counts['Not Started'] },
    { id: 'In Progress', label: 'In Progress', count: counts['In Progress'] },
  ];

  const migrationSteps = [
    { id: 'review', label: '1. Review' },
    { id: 'mapping', label: '2. IP Mapping' },
    { id: 'compile', label: '3. Compile' },
    { id: 'submit', label: '4. Submit' },
  ];

  return (
    <div className="p-6 max-w-[1800px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Migration to NGDC</h1>
          <p className="text-sm text-gray-500 mt-1">Analyze legacy rules, map to NGDC standards, validate birthright, and submit for review</p>
        </div>
        <div className="flex items-center gap-3">
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
            <option value="">All Applications</option>
            {appOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button onClick={handleLoadNfrApps} className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100">
            Import Rules
          </button>
          {selectedRuleIds.size > 0 && (
            <>
              <span className="text-sm text-gray-600 font-medium">{selectedRuleIds.size} selected</span>
              <button onClick={handleSubmitForReview} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm">
                Submit for Review
              </button>
              <button onClick={handleMigrateSelected} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 shadow-sm">
                Migrate to NGDC
              </button>
            </>
          )}
        </div>
      </div>

      {/* Import Rules Panel */}
      {showImportPanel && (
        <div className="mb-6 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-indigo-800">Import Rules from Network Firewall Request</h3>
            <div className="flex gap-2">
              <button onClick={selectAllImportApps} className="px-3 py-1 text-xs font-medium text-indigo-600 hover:text-indigo-800">
                {selectedImportApps.size === nfrApps.length ? 'Deselect All' : 'Select All'}
              </button>
              <button onClick={() => setShowImportPanel(false)} className="px-3 py-1 text-xs font-medium text-gray-500 hover:text-gray-700">Close</button>
            </div>
          </div>
          <p className="text-xs text-indigo-600 mb-3">Select applications from Network Firewall Request to import their rules for NGDC standardization and migration.</p>
          <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto mb-3">
            {nfrApps.map(app => (
              <label key={app.value} className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors ${selectedImportApps.has(app.value) ? 'bg-indigo-100 border border-indigo-300' : 'bg-white border border-gray-200 hover:bg-gray-50'}`}>
                <input type="checkbox" checked={selectedImportApps.has(app.value)} onChange={() => toggleImportApp(app.value)} className="rounded border-gray-300 text-indigo-600" />
                {app.label}
              </label>
            ))}
            {nfrApps.length === 0 && <p className="col-span-4 text-xs text-gray-400 italic py-4 text-center">No applications found in Network Firewall Request</p>}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-indigo-600">{selectedImportApps.size} application(s) selected</span>
            <button onClick={handleImportFromNFR} disabled={importing || selectedImportApps.size === 0}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 shadow-sm">
              {importing ? 'Importing...' : `Import ${selectedImportApps.size} App(s)`}
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Total Rules', value: counts.All, color: 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800' },
          { label: 'Non-Standard', value: counts['Non-Standard'], color: 'bg-gradient-to-br from-red-100 to-red-200 text-red-800' },
          { label: 'Standard', value: counts.Standard, color: 'bg-gradient-to-br from-green-100 to-green-200 text-green-800' },
          { label: 'Not Started', value: counts['Not Started'], color: 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-800' },
          { label: 'In Progress', value: counts['In Progress'], color: 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-800' },
        ].map(card => (
          <div key={card.label} className={'p-3 rounded-lg shadow-sm ' + card.color}>
            <div className="text-xl font-bold">{card.value}</div>
            <div className="text-xs font-medium mt-0.5">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 pt-4 flex items-center justify-between">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
          <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
            <input type="checkbox" checked={selectedRuleIds.size === filteredRules.length && filteredRules.length > 0} onChange={toggleSelectAll} className="rounded border-gray-300 text-blue-600" />
            Select All
          </label>
        </div>
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <DataTable data={filteredRules} columns={columns} keyField="id"
              searchPlaceholder="Search by IP, group, app, rule ID, zone, service..."
              searchFields={['id', 'app_id', 'app_distributed_id', 'app_name', 'rule_source', 'rule_source_expanded', 'rule_destination', 'rule_destination_expanded', 'rule_source_zone', 'rule_destination_zone', 'rule_service', 'inventory_item']}
              onRowClick={(row) => detailModal.open(row)} emptyMessage="No legacy rules found for migration" defaultPageSize={50} />
          )}
        </div>
      </div>

      {/* Detail Modal with Expanded IPs */}
      <Modal isOpen={detailModal.isOpen} onClose={detailModal.close} title={`Rule Details: ${detailModal.data?.id || ''}`} size="xl">
        {detailModal.data && (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-3">
              {([
                ['Rule ID', detailModal.data.id],
                ['App ID', String(detailModal.data.app_id)],
                ['App Distributed ID', detailModal.data.app_distributed_id],
                ['App Name', detailModal.data.app_name],
                ['Inventory Item', detailModal.data.inventory_item],
                ['Policy Name', detailModal.data.policy_name],
                ['Rule Global', detailModal.data.rule_global ? 'Yes' : 'No'],
                ['Rule Action', detailModal.data.rule_action],
                ['Source Zone', detailModal.data.rule_source_zone],
                ['Destination Zone', detailModal.data.rule_destination_zone],
                ['Service', detailModal.data.rule_service],
                ['Migration Status', detailModal.data.migration_status],
                ['RN', String(detailModal.data.rn)],
                ['RC', String(detailModal.data.rc)],
              ] as [string, string][]).map(([label, val]) => (
                <div key={label} className="p-2 bg-gray-50 rounded">
                  <span className="text-xs text-gray-500">{label}</span>
                  <p className="text-sm font-medium text-gray-800 break-all">{val}</p>
                </div>
              ))}
            </div>

            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-blue-50 border-b">
                <h3 className="text-sm font-semibold text-blue-800">Source (Expanded IPs/Groups)</h3>
              </div>
              <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
                {parseExpandedTree(detailModal.data.rule_source_expanded).map((line, i) => {
                  const indent = line.length - line.trimStart().length;
                  return (
                    <div key={i} className="font-mono text-xs text-green-400" style={{ paddingLeft: `${indent * 8}px` }}>
                      {line.trim()}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-purple-50 border-b">
                <h3 className="text-sm font-semibold text-purple-800">Destination (Expanded IPs/Groups)</h3>
              </div>
              <div className="p-3 bg-gray-900 max-h-60 overflow-y-auto">
                {parseExpandedTree(detailModal.data.rule_destination_expanded).map((line, i) => {
                  const indent = line.length - line.trimStart().length;
                  return (
                    <div key={i} className="font-mono text-xs text-purple-400" style={{ paddingLeft: `${indent * 8}px` }}>
                      {line.trim()}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-amber-50 border-b">
                <h3 className="text-sm font-semibold text-amber-800">Service (Expanded)</h3>
              </div>
              <div className="p-3 bg-gray-900">
                {(detailModal.data.rule_service_expanded || '').split('\n').map((line, i) => (
                  <div key={i} className="font-mono text-xs text-amber-400">{line}</div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-2 justify-end">
              <button onClick={detailModal.close} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Migration Popup - Multi-Step Workflow */}
      <Modal isOpen={!!migrateRule} onClose={closeMigratePopup} title={`Migrate Rule: ${migrateRule?.id || ''}`} size="xl">
        {migrateRule && (
          <div className="space-y-4 max-h-[80vh] overflow-y-auto pr-1">
            {/* Step Indicator */}
            <div className="flex gap-1">
              {migrationSteps.map((step) => (
                <button key={step.id} onClick={() => setMigrationStep(step.id as typeof migrationStep)}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                    migrationStep === step.id ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}>
                  {step.label}
                </button>
              ))}
            </div>

            {loadingRec ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                <span className="ml-3 text-sm text-gray-500">Loading NGDC recommendations...</span>
              </div>
            ) : (
              <>
                {/* Step 1: Review NGDC Recommendations */}
                {migrationStep === 'review' && recommendation && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <h3 className="text-sm font-semibold text-blue-800 mb-2">NGDC Recommendations</h3>
                      {recommendation.nh_sz_source && (
                        <div className="mb-2 flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 text-[10px] rounded font-medium ${
                            recommendation.nh_sz_source === 'app_dc_mapping' ? 'bg-green-100 text-green-700' :
                            recommendation.nh_sz_source === 'application_config' ? 'bg-blue-100 text-blue-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {recommendation.nh_sz_source === 'app_dc_mapping' ? 'From App-DC Mapping Table' :
                             recommendation.nh_sz_source === 'application_config' ? 'From App Config' : 'Default'}
                          </span>
                          {recommendation.recommended_dc && (
                            <span className="text-[10px] text-gray-500">DC: {recommendation.recommended_dc}</span>
                          )}
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs text-gray-500">Recommended Neighbourhood</label>
                          <select value={selectedNh} onChange={e => setSelectedNh(e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md mt-1">
                            {recommendation.available_nhs.map(nh => (
                              <option key={nh.nh_id} value={nh.nh_id}>{nh.nh_id} - {nh.name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">Recommended Security Zone</label>
                          <select value={selectedSz} onChange={e => setSelectedSz(e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md mt-1">
                            {recommendation.available_szs.map(sz => (
                              <option key={sz.code} value={sz.code}>{sz.code} - {sz.name}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-gray-600">
                        <span className="font-medium">Naming Standard:</span> {recommendation.naming_standard}
                      </div>
                      {/* Mapping Summary */}
                      {recommendation.mapping_summary && (
                        <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-500">
                          <span>Mappings: {recommendation.mapping_summary.total} total</span>
                          {recommendation.mapping_summary.from_mapping_table > 0 && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded">{recommendation.mapping_summary.from_mapping_table} from table</span>}
                          {recommendation.mapping_summary.from_existing_groups > 0 && <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">{recommendation.mapping_summary.from_existing_groups} from groups</span>}
                          {recommendation.mapping_summary.auto_generated > 0 && <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">{recommendation.mapping_summary.auto_generated} auto-generated</span>}
                        </div>
                      )}
                    </div>

                    {appGroups.length > 0 && (
                      <div className="border rounded-lg p-3">
                        <h4 className="text-xs font-semibold text-gray-700 mb-2">Available Groups for App {migrateRule.app_id}</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {appGroups.map(g => (
                            <div key={g.name} className="px-2 py-1 bg-gray-50 rounded text-xs">
                              <span className="font-medium">{g.name}</span>
                              <span className="text-gray-400 ml-1">({g.members.length} members)</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="border rounded-lg p-3">
                      <h4 className="text-xs font-semibold text-gray-700 mb-1">Service/Port Analysis</h4>
                      <div className="space-y-1">
                        {(recommendation.service_recommendations?.length ?? 0) > 0
                          ? recommendation.service_recommendations!.map((sr, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <span className="font-mono px-2 py-0.5 bg-gray-100 rounded min-w-[80px]">{sr.service}</span>
                              {sr.description && <span className="text-gray-600">{sr.description}</span>}
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                sr.risk_level === 'high' ? 'bg-red-100 text-red-700' :
                                sr.risk_level === 'medium' ? 'bg-amber-100 text-amber-700' :
                                'bg-green-100 text-green-700'
                              }`}>{sr.risk_level}</span>
                              {sr.risk_level !== 'low' && <span className="text-[10px] text-gray-400 italic">{sr.recommendation}</span>}
                            </div>
                          ))
                          : recommendation.service_entries.map((svc, i) => (
                            <span key={i} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-mono">{svc}</span>
                          ))
                        }
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button onClick={handleValidateBirthright} disabled={validatingBirthright}
                        className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100 disabled:opacity-50">
                        {validatingBirthright ? 'Validating...' : 'Validate Birthright'}
                      </button>
                    </div>
                    <BirthrightPanel validation={birthrightResult} />

                    <div className="flex justify-end">
                      <button onClick={() => setMigrationStep('mapping')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                        Next: IP Mapping
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 2: One-to-One IP Mapping */}
                {migrationStep === 'mapping' && (
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <h3 className="text-sm font-semibold text-green-800 mb-1">Source IP Mapping (Legacy to NGDC)</h3>
                      <p className="text-xs text-green-600">Map each legacy source entry to its NGDC equivalent. You can customize each mapping.</p>
                    </div>
                    <div className="space-y-2">
                      {customMappings.map((mapping, i) => (
                        <div key={i} className="grid grid-cols-[1fr,auto,1fr,auto] gap-2 items-center bg-gray-50 rounded-lg p-2">
                          <div>
                            <label className="text-xs text-gray-500">Legacy</label>
                            <div className="font-mono text-xs text-red-600 bg-white rounded px-2 py-1 border">{mapping.legacy}</div>
                          </div>
                          <div className="text-gray-400 text-lg font-bold">&rarr;</div>
                          <div>
                            <label className="text-xs text-gray-500">NGDC Target</label>
                            <input type="text" value={mapping.ngdc_recommended}
                              onChange={e => updateSourceMapping(i, 'ngdc_recommended', e.target.value)}
                              disabled={!mapping.customizable}
                              className="w-full font-mono text-xs text-green-700 rounded px-2 py-1 border border-gray-300 disabled:bg-gray-100" />
                          </div>
                          <div className="flex flex-col items-end gap-0.5">
                            <span className={`px-1.5 py-0.5 text-xs rounded ${
                              mapping.type === 'group' ? 'bg-blue-100 text-blue-700' :
                              mapping.type === 'server' ? 'bg-purple-100 text-purple-700' :
                              mapping.type === 'range' ? 'bg-amber-100 text-amber-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>{mapping.type}</span>
                            {mapping.mapping_source && (
                              <span className={`px-1 py-0.5 text-[9px] rounded ${
                                mapping.mapping_source === 'ngdc_mapping_table' ? 'bg-green-50 text-green-600' :
                                mapping.mapping_source === 'existing_group' ? 'bg-blue-50 text-blue-600' :
                                'bg-gray-50 text-gray-400'
                              }`}>
                                {mapping.mapping_source === 'ngdc_mapping_table' ? 'table' :
                                 mapping.mapping_source === 'existing_group' ? 'group' : 'auto'}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {customMappings.length === 0 && (
                        <p className="text-xs text-gray-400 italic py-4 text-center">No source mappings available</p>
                      )}
                    </div>

                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mt-4">
                      <h3 className="text-sm font-semibold text-purple-800 mb-1">Destination IP Mapping (Legacy to NGDC)</h3>
                    </div>
                    <div className="space-y-2">
                      {customDestMappings.map((mapping, i) => (
                        <div key={i} className="grid grid-cols-[1fr,auto,1fr,auto] gap-2 items-center bg-gray-50 rounded-lg p-2">
                          <div>
                            <label className="text-xs text-gray-500">Legacy</label>
                            <div className="font-mono text-xs text-red-600 bg-white rounded px-2 py-1 border">{mapping.legacy}</div>
                          </div>
                          <div className="text-gray-400 text-lg font-bold">&rarr;</div>
                          <div>
                            <label className="text-xs text-gray-500">NGDC Target</label>
                            <input type="text" value={mapping.ngdc_recommended}
                              onChange={e => updateDestMapping(i, 'ngdc_recommended', e.target.value)}
                              disabled={!mapping.customizable}
                              className="w-full font-mono text-xs text-green-700 rounded px-2 py-1 border border-gray-300 disabled:bg-gray-100" />
                          </div>
                          <div className="flex flex-col items-end gap-0.5">
                            <span className={`px-1.5 py-0.5 text-xs rounded ${
                              mapping.type === 'group' ? 'bg-blue-100 text-blue-700' :
                              mapping.type === 'server' ? 'bg-purple-100 text-purple-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>{mapping.type}</span>
                            {mapping.mapping_source && (
                              <span className={`px-1 py-0.5 text-[9px] rounded ${
                                mapping.mapping_source === 'ngdc_mapping_table' ? 'bg-green-50 text-green-600' :
                                mapping.mapping_source === 'existing_group' ? 'bg-blue-50 text-blue-600' :
                                'bg-gray-50 text-gray-400'
                              }`}>
                                {mapping.mapping_source === 'ngdc_mapping_table' ? 'table' :
                                 mapping.mapping_source === 'existing_group' ? 'group' : 'auto'}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {customDestMappings.length === 0 && (
                        <p className="text-xs text-gray-400 italic py-4 text-center">No destination mappings available</p>
                      )}
                    </div>

                    <div className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-semibold text-gray-700">Groups for App {migrateRule.app_id}</h4>
                        <button onClick={() => setShowNewGroupModal(true)} className="px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded hover:bg-emerald-100">
                          + Create New Group
                        </button>
                      </div>
                      {appGroups.length > 0 ? (
                        <select className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md" defaultValue="">
                          <option value="">Select a group to use in mapping...</option>
                          {appGroups.map(g => (
                            <option key={g.name} value={g.name}>{g.name} ({g.members.length} members)</option>
                          ))}
                        </select>
                      ) : (
                        <p className="text-xs text-gray-400 italic">No groups exist. Create one to organize IPs during migration.</p>
                      )}
                    </div>

                    <div className="flex justify-between">
                      <button onClick={() => setMigrationStep('review')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                        Back
                      </button>
                      <button onClick={() => setMigrationStep('compile')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                        Next: Compile
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 3: Compile */}
                {migrationStep === 'compile' && (
                  <div className="space-y-4">
                    <div className="border rounded-lg p-3 bg-gray-50">
                      <div className="flex items-center gap-2 mb-2">
                        <label className="text-xs font-medium text-gray-700">Vendor Format:</label>
                        <select value={compileVendor} onChange={e => setCompileVendor(e.target.value)} className="px-2 py-1 text-xs border border-gray-300 rounded-md">
                          <option value="generic">Generic</option>
                          <option value="palo_alto">Palo Alto</option>
                          <option value="checkpoint">Check Point</option>
                          <option value="cisco_asa">Cisco ASA</option>
                        </select>
                        <button onClick={handleCompileMigration} disabled={compiling}
                          className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50">
                          {compiling ? 'Compiling...' : 'Compile Rule'}
                        </button>
                      </div>
                      {compiledRule && (
                        <div className="bg-gray-900 rounded p-3 mt-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-400">Format: {compiledRule.vendor_format}</span>
                            <button onClick={() => navigator.clipboard.writeText(compiledRule.compiled_text)} className="text-xs text-blue-400 hover:text-blue-300">Copy</button>
                          </div>
                          <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{compiledRule.compiled_text}</pre>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                            <div><span className="text-gray-500">Sources:</span> <span className="text-gray-300">{compiledRule.source_objects?.join(', ')}</span></div>
                            <div><span className="text-gray-500">Destinations:</span> <span className="text-gray-300">{compiledRule.destination_objects?.join(', ')}</span></div>
                            <div><span className="text-gray-500">Services:</span> <span className="text-gray-300">{compiledRule.services?.join(', ')}</span></div>
                            <div><span className="text-gray-500">Action:</span> <span className="text-gray-300">{compiledRule.action}</span></div>
                          </div>
                        </div>
                      )}

                      {/* Group Submission to Firewall Device (inline with compile) */}
                      <GroupProvisioningSection compiledRule={compiledRule} />

                      {!compiledRule && !compiling && (
                        <p className="text-xs text-gray-500 italic">Click &quot;Compile Rule&quot; to generate vendor-specific output and submit groups to firewall device.</p>
                      )}
                    </div>

                    <div className="flex justify-between">
                      <button onClick={() => setMigrationStep('mapping')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                        Back
                      </button>
                      <button onClick={() => setMigrationStep('submit')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                        Next: Submit
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 4: Submit for Review */}
                {migrationStep === 'submit' && (
                  <div className="space-y-4">
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <h3 className="text-sm font-semibold text-amber-800 mb-1">Migration Summary</h3>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div><span className="text-gray-500">Rule:</span> {migrateRule.id}</div>
                        <div><span className="text-gray-500">App:</span> {migrateRule.app_name} ({migrateRule.app_id})</div>
                        <div><span className="text-gray-500">Neighbourhood:</span> {selectedNh}</div>
                        <div><span className="text-gray-500">Security Zone:</span> {selectedSz}</div>
                        <div><span className="text-gray-500">Source Mappings:</span> {customMappings.length}</div>
                        <div><span className="text-gray-500">Dest Mappings:</span> {customDestMappings.length}</div>
                        <div><span className="text-gray-500">Birthright:</span> {birthrightResult ? (birthrightResult.compliant ? 'Compliant' : 'Non-Compliant') : 'Not validated'}</div>
                        <div><span className="text-gray-500">Compiled:</span> {compiledRule ? 'Yes' : 'No'}</div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Migration Comments</label>
                      <textarea value={migrateComments} onChange={e => setMigrateComments(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md h-20 resize-none"
                        placeholder="Describe the migration rationale, any customizations made..." />
                    </div>

                    <div className="flex justify-between">
                      <button onClick={() => setMigrationStep('compile')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                        Back
                      </button>
                      <button onClick={handleSubmitMigrationForReview} disabled={submittingMigration}
                        className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 shadow-sm">
                        {submittingMigration ? 'Submitting...' : 'Submit Migration for Review'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </Modal>

      {/* Create New Group During Migration Modal */}
      <Modal isOpen={showNewGroupModal} onClose={() => setShowNewGroupModal(false)} title="Create New Group for Migration" size="lg">
        <div className="space-y-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <p className="text-xs text-emerald-700">Create a new NGDC-compliant group to organize IPs during migration. The group will follow NGDC naming standards.</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Group Name (NGDC Standard)</label>
            <input type="text" value={newGroupName} onChange={e => setNewGroupName(e.target.value)}
              placeholder="e.g., grp-NH01-UGEN-app-servers" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-700">Members</label>
              <button onClick={() => setNewGroupMembers(prev => [...prev, { type: 'ip', value: '' }])}
                className="text-xs text-blue-600 hover:text-blue-800">+ Add Member</button>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {newGroupMembers.map((member, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <select value={member.type} onChange={e => setNewGroupMembers(prev => prev.map((m, j) => j === i ? { ...m, type: e.target.value } : m))}
                    className="px-2 py-1 text-xs border border-gray-300 rounded-md w-24">
                    <option value="ip">IP</option>
                    <option value="cidr">CIDR/Subnet</option>
                    <option value="range">Range</option>
                  </select>
                  <input type="text" value={member.value} onChange={e => setNewGroupMembers(prev => prev.map((m, j) => j === i ? { ...m, value: e.target.value } : m))}
                    placeholder={member.type === 'ip' ? '10.0.0.1' : member.type === 'cidr' ? '10.0.0.0/24' : '10.0.0.1-10.0.0.10'}
                    className="flex-1 px-2 py-1 text-xs font-mono border border-gray-300 rounded-md" />
                  {newGroupMembers.length > 1 && (
                    <button onClick={() => setNewGroupMembers(prev => prev.filter((_, j) => j !== i))}
                      className="text-xs text-red-500 hover:text-red-700">Remove</button>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t">
            <button onClick={() => setShowNewGroupModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button onClick={handleCreateMigrationGroup} className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700">
              Create Group
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
