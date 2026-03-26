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
  validateBirthright, getGroups,
  createMigrationGroup, getApplications, lookupIPMapping,
  getIPMappings, importIPMappings, compileEgressIngress,
  getFilteredNhSzDc,
} from '@/lib/api';
import { LDFFlowVisualization, type EgressIngressResult } from '@/components/design-studio/LDFFlowVisualization';
import type { LegacyRule, NGDCRecommendation, IPMapping, CompiledRule, BirthrightValidation, FirewallGroup, ComponentGroup, NeighbourhoodRegistry, SecurityZone, NGDCDataCenter, Application } from '@/types';
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
  const [selectedEnv, setSelectedEnv] = useState<string>('');
  const [activeTab, setActiveTab] = useState('All');
  const [viewMode, setViewMode] = useState<'table' | 'builder' | 'group-mappings'>('table');
  const [allIPMappings, setAllIPMappings] = useState<Record<string, unknown>[]>([]);
  const [groupMappingsFilter] = useState('');
  const [loadingMappings, setLoadingMappings] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
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
  const [migrationStep, setMigrationStep] = useState<'review' | 'mapping' | 'compile' | 'submit' | 'change'>('review');
  const [chgNumber, setChgNumber] = useState('');
  const [chgSubmitting, setChgSubmitting] = useState(false);
  const [chgSubmitted, setChgSubmitted] = useState(false);
  const [boundaryAnalysis, setBoundaryAnalysis] = useState<Record<string, unknown> | null>(null);
  const [boundaryLoading, setBoundaryLoading] = useState(false);
  const [componentGroups, setComponentGroups] = useState<ComponentGroup[]>([]);
  const [isModifyMode, setIsModifyMode] = useState(false);
  const [originalRuleSnapshot, setOriginalRuleSnapshot] = useState<Record<string, unknown> | null>(null);

  // Auto-populated NH/SZ/DC from environment + app selection
  const [filteredNHs, setFilteredNHs] = useState<NeighbourhoodRegistry[]>([]);
  const [filteredSZs, setFilteredSZs] = useState<SecurityZone[]>([]);
  const [filteredDCs, setFilteredDCs] = useState<NGDCDataCenter[]>([]);

  // New group creation during migration
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState<{ type: string; value: string }[]>([{ type: 'ip', value: '' }]);

  // Load applications list on mount (always), but only load rules when an app is explicitly selected
  const loadApps = useCallback(async () => {
    try {
      const appsData = await getApplications();
      setApplications(appsData);
    } catch { /* ignore */ }
  }, []);

  const loadData = useCallback(async () => {
    if (!selectedApp) {
      // No app selected — don't auto-load all rules
      setLegacyRules([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [rulesData, appsData] = await Promise.all([
        getLegacyRules(selectedApp, true, undefined, true),
        getApplications(),
      ]);
      setLegacyRules(rulesData);
      void appsData;  // apps used for appOptions via legacyRules
    } catch {
      showNotification('Failed to load migration data', 'error');
    }
    setLoading(false);
  }, [selectedApp, showNotification]);

  useEffect(() => { loadApps(); }, [loadApps]);
  useEffect(() => { loadData(); }, [loadData]);

  const loadIPMappings = useCallback(async (appFilter?: string) => {
    setLoadingMappings(true);
    try {
      const data = await getIPMappings(undefined, appFilter || undefined);
      setAllIPMappings(data);
    } catch { setAllIPMappings([]); }
    setLoadingMappings(false);
  }, []);

  useEffect(() => { if (viewMode === 'group-mappings') loadIPMappings(groupMappingsFilter); }, [viewMode, groupMappingsFilter, loadIPMappings]);

  // Auto-populate NH/SZ/DC when environment or app changes
  useEffect(() => {
    if (!selectedEnv) { setFilteredNHs([]); setFilteredSZs([]); setFilteredDCs([]); return; }
    getFilteredNhSzDc(selectedEnv, selectedApp || undefined)
      .then(data => {
        setFilteredNHs(data.neighbourhoods || []);
        setFilteredSZs(data.security_zones || []);
        setFilteredDCs(data.datacenters || []);
      })
      .catch(() => { setFilteredNHs([]); setFilteredSZs([]); setFilteredDCs([]); });
  }, [selectedEnv, selectedApp]);

  // Auto-validate birthright when migration popup opens with a rule
  useEffect(() => {
    if (!migrateRule || !recommendation) return;
    const srcZone = migrateRule.rule_source_zone;
    const dstZone = migrateRule.rule_destination_zone;
    if (!srcZone && !dstZone) return;
    setValidatingBirthright(true);
    validateBirthright({
      source_zone: srcZone, destination_zone: dstZone,
      action: migrateRule.rule_action, service: migrateRule.rule_service,
      app_id: String(migrateRule.app_id),
    }).then(result => setBirthrightResult(result))
      .catch(() => setBirthrightResult(null))
      .finally(() => setValidatingBirthright(false));
  }, [migrateRule, recommendation]);

  const envFilteredRules = legacyRules.filter(r => {
    if (selectedEnv && (r as unknown as Record<string, string>).environment !== selectedEnv) return false;
    return true;
  });

  const filteredRules = envFilteredRules.filter(r => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Non-Standard') return !r.is_standard;
    if (activeTab === 'Standard') return r.is_standard;
    if (activeTab === 'Migrated') return r.migration_status === 'Mapped' || r.migration_status === 'Completed';
    return r.migration_status === activeTab;
  });

  const counts = {
    All: envFilteredRules.length,
    'Non-Standard': envFilteredRules.filter(r => !r.is_standard).length,
    Standard: envFilteredRules.filter(r => r.is_standard).length,
    'Not Started': envFilteredRules.filter(r => r.migration_status === 'Not Started').length,
    'In Progress': envFilteredRules.filter(r => r.migration_status === 'In Progress').length,
  };

  // Build app options from applications list (not from loaded rules, since rules need app selection first)
  const appOptions = applications.map(a => ({
    value: a.app_distributed_id || String(a.app_id),
    label: `${a.app_distributed_id || a.app_id} - ${a.name}`,
  })).sort((a, b) => a.label.localeCompare(b.label));

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
      const [rec, groups] = await Promise.all([
        getNGDCRecommendations(rule.id),
        getGroups(String(rule.app_id)).catch(() => [] as FirewallGroup[]),
      ]);
      setRecommendation(rec);
      setSelectedNh(rec.recommended_nh); setSelectedSz(rec.recommended_sz);
      setAppGroups(groups);
      setComponentGroups((rec.component_groups || []) as ComponentGroup[]);

      // Enrich mappings with 1-1 IP lookup table for auto-population
      const enrichMapping = async (m: IPMapping): Promise<IPMapping> => {
        if (m.mapping_source === 'ngdc_mapping_table' || m.mapping_source === 'existing_group') return m;
        // For auto-generated mappings, try the 1-1 IP mapping table
        try {
          const result = await lookupIPMapping(m.legacy);
          if (result.found && result.mapping) {
            const mp = result.mapping as Record<string, string>;
            return {
              ...m,
              ngdc_recommended: mp.ngdc_ip || mp.ngdc_name || m.ngdc_recommended,
              mapping_source: 'ngdc_mapping_table',
              mapping_id: mp.id || null,
              ngdc_nh: mp.ngdc_nh || m.ngdc_nh,
              ngdc_sz: mp.ngdc_sz || m.ngdc_sz,
              existing_group: mp.ngdc_group || m.existing_group,
            };
          }
        } catch { /* IP not found in mapping table, keep auto-generated */ }
        // Also try to match against existing groups
        const matchingGroup = groups.find(g =>
          g.members.some(mem => mem.value === m.legacy || m.legacy.includes(mem.value))
        );
        if (matchingGroup) {
          return { ...m, existing_group: matchingGroup.name, mapping_source: 'existing_group', ngdc_recommended: matchingGroup.name };
        }
        return m;
      };

      const [enrichedSrc, enrichedDst] = await Promise.all([
        Promise.all(rec.source_mappings.map(m => enrichMapping({ ...m }))),
        Promise.all(rec.destination_mappings.map(m => enrichMapping({ ...m }))),
      ]);
      setCustomMappings(enrichedSrc);
      setCustomDestMappings(enrichedDst);
    } catch { setRecommendation(null); showNotification('Failed to load NGDC recommendations', 'error'); }
    setLoadingRec(false);
  };

  const closeMigratePopup = () => {
    setMigrateRule(null); setRecommendation(null); setCustomMappings([]);
    setCustomDestMappings([]); setCompiledRule(null); setBirthrightResult(null); setAppGroups([]); setComponentGroups([]); setIsModifyMode(false); setOriginalRuleSnapshot(null); setChgNumber(''); setChgSubmitted(false);
  };

  const handleCompileMigration = async () => {
    if (!migrateRule) return; setCompiling(true);
    try {
      const result = await compileLegacyRule(migrateRule.id, compileVendor);
      setCompiledRule(result); setMigrationStep('compile');
      // Also load boundary analysis
      setBoundaryLoading(true);
      try {
        const ba = await compileEgressIngress(migrateRule.id, compileVendor);
        setBoundaryAnalysis(ba as Record<string, unknown>);
      } catch { setBoundaryAnalysis(null); }
      setBoundaryLoading(false);
    } catch { showNotification('Failed to compile rule', 'error'); }
    setCompiling(false);
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

  const _updateSourceMapping = (index: number, field: string, value: string) => {
    setCustomMappings(prev => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };
  void _updateSourceMapping;
  const _updateDestMapping = (index: number, field: string, value: string) => {
    setCustomDestMappings(prev => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };
  void _updateDestMapping;

  const parseExpandedTree = (text: string): string[] => {
    if (!text) return [];
    return text.split('\n').map(line => line.replace(/\t/g, '  '));
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
      key: 'migration_status', header: 'Mig Status', sortable: true, width: '100px',
      render: (_, row) => <StatusBadge status={row.migration_status} />,
    },
    {
      key: 'rule_status' as keyof LegacyRule, header: 'Rule Status', sortable: true, width: '100px',
      render: (_, row) => <StatusBadge status={row.rule_status || 'Deployed'} />,
    },
    {
      key: 'rule_migration_status' as keyof LegacyRule, header: 'Migration', sortable: true, width: '100px',
      render: (_, row) => <StatusBadge status={row.rule_migration_status || 'Yet to Migrate'} />,
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '160px',
      render: (_, row) => {
        const migStatus = row.rule_migration_status || 'Yet to Migrate';
        const isMigrationDeployed = migStatus === 'Migration Deployed';
        // In Migration: Migrate allowed if not yet migrated; Modify allowed if migrated
        const canMigrate = !isMigrationDeployed && (row.migration_status === 'Not Started' || row.migration_status === 'In Progress');
        const canModify = isMigrationDeployed || row.migration_status === 'Completed' || row.migration_status === 'Mapped';
        return (
          <div className="flex gap-1" onClick={e => e.stopPropagation()}>
            <button onClick={() => detailModal.open(row)} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">View</button>
            {canMigrate ? (
              <button onClick={() => openMigratePopup(row)} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100">Migrate</button>
            ) : canModify ? (
              <button onClick={() => { setIsModifyMode(true); setOriginalRuleSnapshot({ source: row.rule_source, destination: row.rule_destination, source_zone: row.rule_source_zone, destination_zone: row.rule_destination_zone, service: row.rule_service, action: row.rule_action }); openMigratePopup(row); }} className="px-2 py-1 text-xs font-medium text-amber-700 bg-amber-50 rounded hover:bg-amber-100">Modify</button>
            ) : null}
          </div>
        );
      },
    },
  ];

  const tabs = [
    { id: 'All', label: 'All Rules', count: counts.All },
    { id: 'Non-Standard', label: 'Non-Standard', count: counts['Non-Standard'] },
    { id: 'Standard', label: 'Standard', count: counts.Standard },
    { id: 'Not Started', label: 'Not Started', count: counts['Not Started'] },
    { id: 'In Progress', label: 'In Progress', count: counts['In Progress'] },
    { id: 'Migrated', label: 'Migrated', count: legacyRules.filter(r => r.migration_status === 'Mapped' || r.migration_status === 'Completed').length },
  ];

  const handleSubmitChange = async () => {
    if (!migrateRule) return;
    setChgSubmitting(true);
    try {
      // Placeholder: In production, this would call ServiceNow API to create a CHG
      const placeholderCHG = `CHG${String(Date.now()).slice(-7)}`;
      setChgNumber(placeholderCHG);
      setChgSubmitted(true);
      showNotification(`Change ${placeholderCHG} submitted successfully. Rule will be deployed upon CHG closure.`, 'success');
    } catch {
      showNotification('Failed to submit change request', 'error');
    }
    setChgSubmitting(false);
  };

  const handleDeployAfterCHG = async () => {
    if (!migrateRule || !chgNumber) return;
    try {
      await migrateRulesToNGDC([migrateRule.id]);
      showNotification(`Rule deployed via ${chgNumber}. Now visible in Design Studio.`, 'success');
      closeMigratePopup();
      loadData();
    } catch {
      showNotification('Failed to deploy rule', 'error');
    }
  };

  const migrationSteps = [
    { id: 'review', label: '1. Review' },
    { id: 'mapping', label: '2. Group Mapping' },
    { id: 'compile', label: '3. Compile' },
    { id: 'submit', label: '4. Submit' },
    { id: 'change', label: '5. Change' },
  ];

  return (
    <div className="p-6 max-w-[1800px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Migration to NGDC</h1>
          {/* Tabs include Migrated for modify */}
          <p className="text-sm text-gray-500 mt-1">Analyze legacy rules, map to NGDC standards, validate birthright, and submit for review</p>
        </div>
        <div className="flex items-center gap-3">
          <select className={`px-3 py-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white ${!selectedApp ? 'border-amber-400 ring-1 ring-amber-300' : 'border-gray-300'}`}
            value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
            <option value="">-- Select Application (Distributed ID) --</option>
            {appOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedEnv} onChange={e => setSelectedEnv(e.target.value)}>
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
          <div className="flex items-center border border-gray-300 rounded-md overflow-hidden">
            <button onClick={() => setViewMode('table')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'table' ? 'bg-green-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Table View</button>
            <button onClick={() => setViewMode('group-mappings')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'group-mappings' ? 'bg-green-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Group Mappings</button>
          </div>
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

      {viewMode === 'group-mappings' ? (
        <div className="bg-white border rounded-lg shadow-sm">
          <div className="px-4 py-3 border-b flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">Group Mappings Reference (Legacy DC &rarr; NGDC)</h2>
              <p className="text-xs text-gray-500 mt-0.5">Browse all group-level mappings. IPs are auto-recommended into groups. Filter by app to find relevant groups for migration.</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => loadIPMappings(groupMappingsFilter)} className="px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100">Refresh</button>
              <label className="px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded hover:bg-emerald-100 cursor-pointer">
                Import CSV
                <input type="file" accept=".csv,.json" className="hidden" onChange={async (e) => {
                  const file = e.target.files?.[0]; if (!file) return;
                  try {
                    const text = await file.text();
                    let records: Record<string, unknown>[];
                    if (file.name.endsWith('.json')) { records = JSON.parse(text); }
                    else {
                      const lines = text.trim().split('\n');
                      const headers = lines[0].split(',').map(h => h.trim());
                      records = lines.slice(1).map(line => {
                        const vals = line.split(',').map(v => v.trim());
                        const obj: Record<string, unknown> = {};
                        headers.forEach((h, i) => { obj[h] = vals[i] || ''; });
                        return obj;
                      });
                    }
                    const result = await importIPMappings(records, groupMappingsFilter || undefined);
                    showNotification(`Imported ${result.added} IP mappings (total: ${result.total})`, 'success');
                    loadIPMappings(groupMappingsFilter);
                  } catch { showNotification('Failed to import IP mappings', 'error'); }
                  e.target.value = '';
                }} />
              </label>
            </div>
          </div>
          <div className="p-4">
            {loadingMappings ? (
              <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
            ) : allIPMappings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">App ID</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Legacy IP</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Legacy DC</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">&rarr;</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">NGDC IP</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">NGDC Name</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">NGDC Group</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">NH</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">SZ</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Component</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {allIPMappings.map((m, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-3 py-1.5 font-medium">{String(m.app_id || '')}</td>
                        <td className="px-3 py-1.5 font-mono text-red-600">{String(m.legacy_ip || '')}</td>
                        <td className="px-3 py-1.5 text-gray-500">{String(m.legacy_dc || '')}</td>
                        <td className="px-3 py-1.5 text-gray-400">&rarr;</td>
                        <td className="px-3 py-1.5 font-mono text-green-600">{String(m.ngdc_ip || '')}</td>
                        <td className="px-3 py-1.5 font-mono text-green-700">{String(m.ngdc_name || '')}</td>
                        <td className="px-3 py-1.5">
                          {m.ngdc_group ? <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">{String(m.ngdc_group)}</span> : <span className="text-gray-300">-</span>}
                        </td>
                        <td className="px-3 py-1.5">{String(m.ngdc_nh || '')}</td>
                        <td className="px-3 py-1.5">{String(m.ngdc_sz || '')}</td>
                        <td className="px-3 py-1.5">{String(m.component || '')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <p className="text-sm">No group mappings found{groupMappingsFilter ? ` for app ${groupMappingsFilter}` : ''}.</p>
                <p className="text-xs mt-1">Import mappings using CSV/JSON or check seeded data.</p>
              </div>
            )}
          </div>
          <div className="px-4 py-2 border-t bg-gray-50 text-xs text-gray-500">
            {allIPMappings.length} mapping{allIPMappings.length !== 1 ? 's' : ''} loaded.
            Naming: svr-xx.xx.xx.xx (IPs), net-xx.xx.xx.xx/xx (subnets), rng-xx.xx.xx.xx-xy (ranges), grp-APP-NH-SZ-TIER (groups)
          </div>
        </div>
      ) : !selectedApp ? (
        <div className="bg-white border border-amber-200 rounded-lg shadow-sm p-12 text-center">
          <div className="text-4xl mb-3">&#128269;</div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Select an Application to Begin Migration</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">Choose an application by its Distributed ID from the dropdown above. Rules imported via Firewall Management will appear here for the selected application.</p>
          <div className="mt-4">
            <select className="px-4 py-2 border border-amber-400 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white min-w-[300px]"
              value={selectedApp} onChange={e => setSelectedApp(e.target.value)}>
              <option value="">-- Select Application (Distributed ID) --</option>
              {appOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      ) : (
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
      )}

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
                  const v = line.trim();
                  const vl = v.toLowerCase();
                  const eType = vl.startsWith('grp-') || vl.startsWith('g-') ? 'GRP' : vl.startsWith('rng-') ? 'RNG' : vl.startsWith('net-') || vl.startsWith('sub-') ? 'NET' : /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d/.test(v) ? 'NET' : /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*-\s*\d/.test(v) ? 'RNG' : 'IP';
                  const badgeColor = eType === 'GRP' ? 'bg-emerald-100 text-emerald-700' : eType === 'RNG' ? 'bg-orange-100 text-orange-700' : eType === 'NET' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700';
                  const isChild = indent >= 2;
                  return (
                    <div key={i} className={`flex items-center gap-2 ${isChild ? 'ml-6 pl-3 border-l-2 border-gray-600' : ''}`}>
                      <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${badgeColor}`}>{eType}</span>
                      <span className="font-mono text-xs text-green-400">{v}</span>
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
                  const v = line.trim();
                  const vl = v.toLowerCase();
                  const eType = vl.startsWith('grp-') || vl.startsWith('g-') ? 'GRP' : vl.startsWith('rng-') ? 'RNG' : vl.startsWith('net-') || vl.startsWith('sub-') ? 'NET' : /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d/.test(v) ? 'NET' : /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*-\s*\d/.test(v) ? 'RNG' : 'IP';
                  const badgeColor = eType === 'GRP' ? 'bg-emerald-100 text-emerald-700' : eType === 'RNG' ? 'bg-orange-100 text-orange-700' : eType === 'NET' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700';
                  const isChild = indent >= 2;
                  return (
                    <div key={i} className={`flex items-center gap-2 ${isChild ? 'ml-6 pl-3 border-l-2 border-gray-600' : ''}`}>
                      <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${badgeColor}`}>{eType}</span>
                      <span className="font-mono text-xs text-purple-400">{v}</span>
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
                {/* Step 1: Side-by-Side Legacy → NGDC Review */}
                {migrationStep === 'review' && recommendation && (
                  <div className="space-y-4">
                    {/* Side-by-Side: Legacy (Left) vs NGDC (Right) */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* LEFT: Legacy Rule */}
                      <div className="border border-red-200 rounded-lg overflow-hidden">
                        <div className="px-3 py-2 bg-red-50 border-b border-red-200">
                          <h3 className="text-sm font-semibold text-red-800">Legacy Rule (Current)</h3>
                          <p className="text-[10px] text-red-600">Source datacenter: {migrateRule.inventory_item}</p>
                        </div>
                        <div className="p-3 space-y-3 text-xs">
                          <div className="grid grid-cols-2 gap-2">
                            <div><span className="text-gray-500">Rule ID:</span> <span className="font-medium">{migrateRule.id}</span></div>
                            <div><span className="text-gray-500">App:</span> <span className="font-medium">{migrateRule.app_name} ({migrateRule.app_id})</span></div>
                            <div><span className="text-gray-500">Action:</span> <span className={`font-medium ${migrateRule.rule_action === 'Accept' ? 'text-green-700' : 'text-red-700'}`}>{migrateRule.rule_action}</span></div>
                            <div><span className="text-gray-500">Policy:</span> <span className="font-medium">{migrateRule.policy_name}</span></div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-red-700 mb-1">Source ({migrateRule.rule_source_zone})</h4>
                            <div className="bg-gray-900 rounded p-2 max-h-32 overflow-y-auto">
                              {(migrateRule.rule_source || '').split('\n').filter(Boolean).map((s, i) => (
                                <div key={i} className="font-mono text-red-400 text-[11px]">{s.trim()}</div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-red-700 mb-1">Destination ({migrateRule.rule_destination_zone})</h4>
                            <div className="bg-gray-900 rounded p-2 max-h-32 overflow-y-auto">
                              {(migrateRule.rule_destination || '').split('\n').filter(Boolean).map((d, i) => (
                                <div key={i} className="font-mono text-red-400 text-[11px]">{d.trim()}</div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-red-700 mb-1">Service</h4>
                            <div className="flex flex-wrap gap-1">
                              {(migrateRule.rule_service || '').split('\n').filter(Boolean).map((s, i) => (
                                <span key={i} className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-mono text-[10px]">{s.trim()}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* RIGHT: NGDC Recommended */}
                      <div className="border border-green-200 rounded-lg overflow-hidden">
                        <div className="px-3 py-2 bg-green-50 border-b border-green-200">
                          <h3 className="text-sm font-semibold text-green-800">NGDC Target (Auto-Populated)</h3>
                          <div className="flex items-center gap-2 mt-0.5">
                            {recommendation.nh_sz_source && (
                              <span className={`px-1.5 py-0.5 text-[9px] rounded font-medium ${
                                recommendation.nh_sz_source === 'app_dc_mapping' ? 'bg-green-100 text-green-700' :
                                recommendation.nh_sz_source === 'application_config' ? 'bg-blue-100 text-blue-700' :
                                'bg-gray-100 text-gray-600'
                              }`}>
                                {recommendation.nh_sz_source === 'app_dc_mapping' ? 'App-DC Table' :
                                 recommendation.nh_sz_source === 'application_config' ? 'App Config' : 'Default'}
                              </span>
                            )}
                            {recommendation.recommended_dc && (
                              <span className="text-[9px] text-gray-500">DC: {recommendation.recommended_dc}</span>
                            )}
                          </div>
                        </div>
                        <div className="p-3 space-y-3 text-xs">
                          {/* Direction-specific NH/SZ from rule zones */}
                          <div className="grid grid-cols-2 gap-2">
                            <div className="border border-green-200 rounded p-2 bg-green-50/50">
                              <label className="text-[10px] text-gray-500 font-semibold">Source NH / SZ</label>
                              <div className="mt-0.5 font-mono text-[11px] text-green-800 font-medium">
                                {recommendation.source_nh || recommendation.recommended_nh} / {recommendation.source_sz || recommendation.recommended_sz}
                              </div>
                              {recommendation.source_dc && (
                                <div className="text-[9px] text-gray-500 mt-0.5">DC: {recommendation.source_dc}</div>
                              )}
                            </div>
                            <div className="border border-green-200 rounded p-2 bg-green-50/50">
                              <label className="text-[10px] text-gray-500 font-semibold">Destination NH / SZ</label>
                              <div className="mt-0.5 font-mono text-[11px] text-green-800 font-medium">
                                {recommendation.destination_nh || recommendation.recommended_nh} / {recommendation.destination_sz || recommendation.recommended_sz}
                              </div>
                              {recommendation.destination_dc && (
                                <div className="text-[9px] text-gray-500 mt-0.5">DC: {recommendation.destination_dc}</div>
                              )}
                            </div>
                          </div>

                          {/* Filtered NH/SZ/DC from environment + app selection */}
                          {(filteredNHs.length > 0 || filteredSZs.length > 0 || filteredDCs.length > 0) && (
                            <div className="border border-blue-200 rounded p-2 bg-blue-50/50">
                              <label className="text-[10px] text-blue-600 font-semibold">Available (Env + App Filtered)</label>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {filteredNHs.map(nh => <span key={nh.nh_id} className="px-1 py-0.5 text-[9px] bg-blue-100 text-blue-700 rounded">{nh.nh_id}</span>)}
                                {filteredSZs.map(sz => <span key={sz.code} className="px-1 py-0.5 text-[9px] bg-indigo-100 text-indigo-700 rounded">{sz.code}</span>)}
                                {filteredDCs.map(dc => <span key={dc.dc_id} className="px-1 py-0.5 text-[9px] bg-purple-100 text-purple-700 rounded">{dc.dc_id}</span>)}
                              </div>
                            </div>
                          )}

                          <div>
                            <h4 className="font-semibold text-green-700 mb-1">Source (NGDC Mapped)</h4>
                            <div className="bg-gray-900 rounded p-2 max-h-32 overflow-y-auto">
                              {customMappings.length > 0 ? customMappings.map((m, i) => (
                                <div key={i} className="flex items-center gap-1 mb-0.5">
                                  <span className="font-mono text-green-400 text-[11px]">{m.ngdc_recommended}</span>
                                  <span className={`px-1 py-0 text-[8px] rounded ${
                                    m.mapping_source === 'ngdc_mapping_table' ? 'bg-green-900 text-green-300' :
                                    m.mapping_source === 'existing_group' ? 'bg-blue-900 text-blue-300' :
                                    'bg-gray-700 text-gray-400'
                                  }`}>{m.mapping_source === 'ngdc_mapping_table' ? 'table' : m.mapping_source === 'existing_group' ? 'group' : 'auto'}</span>
                                </div>
                              )) : <span className="text-gray-500 italic text-[10px]">No source entries</span>}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-green-700 mb-1">Destination (NGDC Mapped)</h4>
                            <div className="bg-gray-900 rounded p-2 max-h-32 overflow-y-auto">
                              {customDestMappings.length > 0 ? customDestMappings.map((m, i) => (
                                <div key={i} className="flex items-center gap-1 mb-0.5">
                                  <span className="font-mono text-green-400 text-[11px]">{m.ngdc_recommended}</span>
                                  <span className={`px-1 py-0 text-[8px] rounded ${
                                    m.mapping_source === 'ngdc_mapping_table' ? 'bg-green-900 text-green-300' :
                                    m.mapping_source === 'existing_group' ? 'bg-blue-900 text-blue-300' :
                                    'bg-gray-700 text-gray-400'
                                  }`}>{m.mapping_source === 'ngdc_mapping_table' ? 'table' : m.mapping_source === 'existing_group' ? 'group' : 'auto'}</span>
                                </div>
                              )) : <span className="text-gray-500 italic text-[10px]">No destination entries</span>}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-green-700 mb-1">Naming Standard</h4>
                            <span className="font-mono text-green-600 text-[10px] bg-green-50 px-1.5 py-0.5 rounded">{recommendation.naming_standard}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Mapping Summary Bar */}
                    {recommendation.mapping_summary && (
                      <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg border text-[10px]">
                        <span className="font-semibold text-gray-600">Group Mapping Sources:</span>
                        <span className="text-gray-500">{recommendation.mapping_summary.total} total</span>
                        {recommendation.mapping_summary.from_mapping_table > 0 && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-medium">{recommendation.mapping_summary.from_mapping_table} from 1-1 table</span>}
                        {recommendation.mapping_summary.from_existing_groups > 0 && <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">{recommendation.mapping_summary.from_existing_groups} from groups</span>}
                        {recommendation.mapping_summary.auto_generated > 0 && <span className="px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded font-medium">{recommendation.mapping_summary.auto_generated} auto-generated</span>}
                      </div>
                    )}

                    {/* Available Groups */}
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

                    {/* Service/Port Analysis */}
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

                    {/* Birthright Validation (Auto-validated) */}
                    {validatingBirthright && (
                      <div className="flex items-center gap-2 text-sm text-purple-600 animate-pulse">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600" />
                        Auto-validating birthright...
                      </div>
                    )}
                    <BirthrightPanel validation={birthrightResult} />

                    <div className="flex justify-end">
                      <button onClick={() => setMigrationStep('mapping')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                        Next: Group Mapping
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 2: Component-Level Group Mapping */}
                {migrationStep === 'mapping' && (
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-sm font-semibold text-green-800">Component Group Mapping (Legacy to NGDC)</h3>
                        {componentGroups[0]?.environment && (
                          <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${
                            componentGroups[0].environment === 'Production' ? 'bg-red-100 text-red-700' :
                            componentGroups[0].environment === 'Pre-Production' ? 'bg-amber-100 text-amber-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>{componentGroups[0].environment}</span>
                        )}
                      </div>
                      <p className="text-xs text-green-600">All IPs for each component are automatically grouped into NGDC groups. Legacy may or may not have groups — in NGDC, all IPs must be in groups. You can customize group names below.</p>
                    </div>

                    {/* Source Component Groups */}
                    {(() => {
                      const srcGroups = componentGroups.filter(g => g.direction === 'source');
                      return srcGroups.length > 0 ? (
                        <div className="space-y-3">
                          <h4 className="text-xs font-semibold text-green-700 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-green-500" /> Source Component Groups ({srcGroups.length})
                          </h4>
                          {srcGroups.map((cg, i) => (
                            <div key={`src-${i}`} className="border border-green-200 rounded-lg p-3 bg-white">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-indigo-100 text-indigo-700">{cg.component}</span>
                                  <span className="text-[10px] text-gray-500">{cg.ip_count} IP{cg.ip_count !== 1 ? 's' : ''}</span>
                                  <span className="text-[10px] font-mono text-gray-400">{cg.dc}/{cg.nh}/{cg.sz}</span>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-3">
                                {/* Legacy side: show group name if exists, otherwise show raw IPs directly */}
                                <div className="bg-amber-50 border border-amber-200 rounded p-2">
                                  <label className="text-[10px] font-semibold text-amber-700 uppercase">Legacy</label>
                                  {cg.legacy_group ? (
                                    <div className="text-xs font-mono text-amber-800 mt-0.5">
                                      <span className="px-1.5 py-0.5 bg-amber-100 rounded">{cg.legacy_group}</span>
                                      <div className="mt-1.5">
                                        <label className="text-[9px] text-amber-600">Members:</label>
                                        <div className="flex flex-wrap gap-1 mt-0.5">
                                          {cg.ips.map((ip, j) => (
                                            <span key={j} className="px-1 py-0.5 text-[9px] font-mono bg-amber-100 text-amber-700 rounded">{ip}</span>
                                          ))}
                                        </div>
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="mt-0.5">
                                      <div className="flex flex-wrap gap-1">
                                        {cg.ips.map((ip, j) => (
                                          <span key={j} className="px-1.5 py-0.5 text-[10px] font-mono bg-amber-100 text-amber-800 rounded">{ip}</span>
                                        ))}
                                      </div>
                                      <div className="text-[9px] text-amber-500 italic mt-1">Individual IPs (no legacy group)</div>
                                    </div>
                                  )}
                                </div>
                                {/* NGDC side: always show recommended group with NGDC-mapped IPs */}
                                <div className="bg-green-50 border border-green-200 rounded p-2">
                                  <label className="text-[10px] font-semibold text-green-600 uppercase">NGDC Group</label>
                                  <input type="text" value={cg.ngdc_group}
                                    onChange={e => {
                                      const updated = [...componentGroups];
                                      const idx = updated.findIndex(g => g === cg);
                                      if (idx >= 0) { updated[idx] = { ...cg, ngdc_group: e.target.value }; setComponentGroups(updated); }
                                    }}
                                    disabled={!cg.customizable}
                                    className="w-full font-mono text-xs text-green-700 rounded px-2 py-1 border border-green-300 mt-0.5 disabled:bg-gray-100" />
                                  <div className="mt-1.5">
                                    <label className="text-[9px] text-green-600">NGDC IPs to be associated:</label>
                                    <div className="flex flex-wrap gap-1 mt-0.5">
                                      {(cg.ngdc_ips || cg.ips).map((ip, j) => (
                                        <span key={j} className="px-1 py-0.5 text-[9px] font-mono bg-green-100 text-green-700 rounded">{ip}</span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              {cg.cidr && <div className="mt-1 text-[10px] text-gray-400">CIDR: {cg.cidr}</div>}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic py-2 text-center">No source component groups detected</p>
                      );
                    })()}

                    {/* Destination Component Groups */}
                    {(() => {
                      const dstGroups = componentGroups.filter(g => g.direction === 'destination');
                      return dstGroups.length > 0 ? (
                        <div className="space-y-3">
                          <h4 className="text-xs font-semibold text-purple-700 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-purple-500" /> Destination Component Groups ({dstGroups.length})
                          </h4>
                          {dstGroups.map((cg, i) => (
                            <div key={`dst-${i}`} className="border border-purple-200 rounded-lg p-3 bg-white">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-indigo-100 text-indigo-700">{cg.component}</span>
                                  <span className="text-[10px] text-gray-500">{cg.ip_count} IP{cg.ip_count !== 1 ? 's' : ''}</span>
                                  <span className="text-[10px] font-mono text-gray-400">{cg.dc}/{cg.nh}/{cg.sz}</span>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-3">
                                {/* Legacy side: show group name if exists, otherwise show raw IPs directly */}
                                <div className="bg-amber-50 border border-amber-200 rounded p-2">
                                  <label className="text-[10px] font-semibold text-amber-700 uppercase">Legacy</label>
                                  {cg.legacy_group ? (
                                    <div className="text-xs font-mono text-amber-800 mt-0.5">
                                      <span className="px-1.5 py-0.5 bg-amber-100 rounded">{cg.legacy_group}</span>
                                      <div className="mt-1.5">
                                        <label className="text-[9px] text-amber-600">Members:</label>
                                        <div className="flex flex-wrap gap-1 mt-0.5">
                                          {cg.ips.map((ip, j) => (
                                            <span key={j} className="px-1 py-0.5 text-[9px] font-mono bg-amber-100 text-amber-700 rounded">{ip}</span>
                                          ))}
                                        </div>
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="mt-0.5">
                                      <div className="flex flex-wrap gap-1">
                                        {cg.ips.map((ip, j) => (
                                          <span key={j} className="px-1.5 py-0.5 text-[10px] font-mono bg-amber-100 text-amber-800 rounded">{ip}</span>
                                        ))}
                                      </div>
                                      <div className="text-[9px] text-amber-500 italic mt-1">Individual IPs (no legacy group)</div>
                                    </div>
                                  )}
                                </div>
                                {/* NGDC side: always show recommended group with NGDC-mapped IPs */}
                                <div className="bg-green-50 border border-green-200 rounded p-2">
                                  <label className="text-[10px] font-semibold text-green-600 uppercase">NGDC Group</label>
                                  <input type="text" value={cg.ngdc_group}
                                    onChange={e => {
                                      const updated = [...componentGroups];
                                      const idx = updated.findIndex(g => g === cg);
                                      if (idx >= 0) { updated[idx] = { ...cg, ngdc_group: e.target.value }; setComponentGroups(updated); }
                                    }}
                                    disabled={!cg.customizable}
                                    className="w-full font-mono text-xs text-green-700 rounded px-2 py-1 border border-green-300 mt-0.5 disabled:bg-gray-100" />
                                  <div className="mt-1.5">
                                    <label className="text-[9px] text-green-600">NGDC IPs to be associated:</label>
                                    <div className="flex flex-wrap gap-1 mt-0.5">
                                      {(cg.ngdc_ips || cg.ips).map((ip, j) => (
                                        <span key={j} className="px-1 py-0.5 text-[9px] font-mono bg-green-100 text-green-700 rounded">{ip}</span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              {cg.cidr && <div className="mt-1 text-[10px] text-gray-400">CIDR: {cg.cidr}</div>}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic py-2 text-center">No destination component groups detected</p>
                      );
                    })()}

                    {/* Existing App Groups + Create New */}
                    <div className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-semibold text-gray-700">Existing Groups for App {migrateRule.app_id}</h4>
                        <button onClick={() => setShowNewGroupModal(true)} className="px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded hover:bg-emerald-100">
                          + Create New Group
                        </button>
                      </div>
                      {appGroups.length > 0 ? (
                        <div className="space-y-1">
                          {appGroups.map(g => (
                            <div key={g.name} className="flex items-center justify-between px-2 py-1 bg-gray-50 rounded text-xs">
                              <span className="font-mono text-gray-700">{g.name}</span>
                              <span className="text-gray-400">{g.members.length} members</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic">No existing groups. Component groups above will be auto-created during compile.</p>
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
                          <option value="fortigate">FortiGate</option>
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

                    {/* Logical Data Flow Visualization */}
                    {migrateRule?.id && (
                      <LDFFlowVisualization ruleId={migrateRule.id} vendor={compileVendor} boundaryData={boundaryAnalysis as EgressIngressResult | null} />
                    )}

                    {/* Firewall Boundary Analysis (Egress/Ingress) */}
                    {(boundaryAnalysis || boundaryLoading) && (
                      <div className="border rounded-lg p-3 bg-purple-50 border-purple-200">
                        <h4 className="text-xs font-semibold text-purple-800 mb-2 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" />
                          Firewall Boundary Analysis
                        </h4>
                        {boundaryLoading && <p className="text-xs text-gray-400 animate-pulse">Analyzing boundaries...</p>}
                        {boundaryAnalysis && !boundaryLoading && (() => {
                          const ba = boundaryAnalysis as Record<string, unknown>;
                          const boundaries = ba.boundaries as number;
                          const devices = (ba.devices || []) as Array<Record<string, string>>;
                          return (
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                  boundaries === 0 ? 'bg-green-100 text-green-700' :
                                  boundaries === 1 ? 'bg-amber-100 text-amber-700' :
                                  'bg-red-100 text-red-700'
                                }`}>
                                  {boundaries} {boundaries === 1 ? 'Boundary' : 'Boundaries'}
                                </span>
                                <span className="text-[10px] text-gray-500">{ba.flow_rule as string}</span>
                              </div>
                              <div className="grid grid-cols-2 gap-1 text-[10px]">
                                                <div className="p-1 bg-blue-50 rounded"><span className="text-blue-600 font-medium">Src:</span> {ba.source_dc ? `${ba.source_dc as string}/` : ''}{ba.source_nh as string}/{ba.source_zone as string}</div>
                                                <div className="p-1 bg-purple-50 rounded"><span className="text-purple-600 font-medium">Dst:</span> {ba.destination_dc ? `${ba.destination_dc as string}/` : ''}{ba.destination_nh as string}/{ba.destination_zone as string}</div>
                              </div>
                              <p className="text-[10px] text-gray-500 italic">{ba.note as string}</p>
                              {devices.length > 0 && devices.map((dev, i) => (
                                <div key={i} className="bg-white border border-gray-200 rounded p-2">
                                  <div className="flex items-center gap-1 mb-1">
                                    <span className={`px-1 py-0.5 text-[9px] font-bold uppercase rounded ${
                                      dev.direction === 'egress' ? 'bg-orange-100 text-orange-700' :
                                      dev.direction === 'ingress' ? 'bg-cyan-100 text-cyan-700' :
                                      'bg-gray-100 text-gray-700'
                                    }`}>{dev.direction}</span>
                                    <span className="text-[10px] font-medium text-gray-800">{dev.device_name}</span>
                                  </div>
                                  <pre className="text-[10px] text-green-600 font-mono bg-gray-50 rounded px-2 py-1 overflow-x-auto whitespace-pre-wrap">{dev.compiled}</pre>
                                  <button onClick={() => navigator.clipboard.writeText(dev.compiled)}
                                    className="text-[9px] text-blue-500 hover:text-blue-700 mt-0.5">Copy</button>
                                </div>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    )}

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

                {/* Step 4: Submit for Review - Complete Info for Reviewer */}
                {migrationStep === 'submit' && (
                  <div className="space-y-4">
                    {/* Modify mode banner */}
                    {isModifyMode && (
                      <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg">
                        <h4 className="text-xs font-semibold text-amber-800">MODIFY MODE - Review changes to existing migrated rule</h4>
                      </div>
                    )}

                    {/* Full context header for reviewer */}
                    <div className="grid grid-cols-2 gap-2">
                      {([
                        ['Rule ID', migrateRule.id],
                        ['Application', `${migrateRule.app_name} (${migrateRule.app_id})`],
                        ['Dist ID', migrateRule.app_distributed_id || 'N/A'],
                        ['Policy', migrateRule.policy_name || 'N/A'],
                        ['Source NH / SZ', `${recommendation?.source_nh || selectedNh} / ${recommendation?.source_sz || selectedSz}`],
                        ['Dest NH / SZ', `${recommendation?.destination_nh || selectedNh} / ${recommendation?.destination_sz || selectedSz}`],
                        ['Source Zone (Legacy)', migrateRule.rule_source_zone || 'N/A'],
                        ['Dest Zone (Legacy)', migrateRule.rule_destination_zone || 'N/A'],
                        ['Action', migrateRule.rule_action || 'allow'],
                        ['Service', migrateRule.rule_service || 'N/A'],
                        ['Birthright', birthrightResult ? (birthrightResult.compliant ? 'Compliant' : 'Non-Compliant') : 'Pending'],
                        ['Standard', migrateRule.is_standard ? 'Yes' : 'No'],
                      ] as [string, string][]).map(([label, val]) => (
                        <div key={label} className="p-2 bg-amber-50 rounded border border-amber-200">
                          <span className="text-[10px] text-amber-600">{label}</span>
                          <div className="text-xs font-medium text-amber-900 truncate">{val}</div>
                        </div>
                      ))}
                    </div>

                    {/* Source & Destination Details */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                        <h4 className="text-xs font-semibold text-blue-700 mb-1">Source</h4>
                        <pre className="text-[10px] font-mono text-blue-800 whitespace-pre-wrap max-h-20 overflow-y-auto">{migrateRule.rule_source || 'N/A'}</pre>
                      </div>
                      <div className="border border-purple-200 rounded-lg p-3 bg-purple-50">
                        <h4 className="text-xs font-semibold text-purple-700 mb-1">Destination</h4>
                        <pre className="text-[10px] font-mono text-purple-800 whitespace-pre-wrap max-h-20 overflow-y-auto">{migrateRule.rule_destination || 'N/A'}</pre>
                      </div>
                    </div>

                    {/* Component Group Mapping Summary for Reviewer */}
                    {componentGroups.length > 0 && (
                      <div className="border border-green-200 rounded-lg p-3 bg-green-50">
                        <h4 className="text-xs font-semibold text-green-800 mb-2">Component Group Mapping</h4>
                        <div className="space-y-1.5">
                          {componentGroups.map((cg, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs bg-white rounded px-2 py-1 border border-green-100">
                              <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${cg.direction === 'source' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>{cg.direction}</span>
                              <span className="font-bold text-indigo-700">{cg.component}</span>
                              <span className="text-gray-400">|</span>
                              <span className="text-red-600 font-mono">{cg.legacy_group || 'No group'}</span>
                              <span className="text-gray-400">&rarr;</span>
                              <span className="text-green-600 font-mono">{cg.ngdc_group}</span>
                              <span className="text-gray-400 ml-auto">{cg.ip_count} IPs | {cg.dc}/{cg.nh}/{cg.sz}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Delta - Changes Only */}
                    <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                      <h3 className="text-sm font-semibold text-blue-800 mb-3">{isModifyMode ? 'Modification Delta (Before vs After)' : 'Changes (Delta)'}</h3>
                      <div className="space-y-3">
                        {/* Original snapshot delta for modify mode */}
                        {isModifyMode && originalRuleSnapshot && (
                          <div>
                            <h4 className="text-xs font-semibold text-amber-700 mb-1">Original Rule (Before Modification)</h4>
                            <div className="ml-2 text-xs space-y-0.5">
                              {Object.entries(originalRuleSnapshot).map(([key, val]) => (
                                <div key={key} className="flex items-center gap-1">
                                  <span className="text-gray-500 capitalize w-24">{key.replace(/_/g, ' ')}:</span>
                                  <span className="text-red-600 font-mono line-through">{String(val || 'N/A')}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {/* Zone Changes */}
                        {recommendation && (
                          <div>
                            <h4 className="text-xs font-semibold text-blue-700 mb-1">Zone & Classification</h4>
                            <div className="ml-2 text-xs space-y-0.5">
                              <div>
                                <span className="text-gray-500">Source Zone:</span>
                                <span className="text-red-600 line-through ml-1">{migrateRule.rule_source_zone || 'N/A'}</span>
                                <span className="mx-1">&rarr;</span>
                                <span className="text-green-600">{recommendation.source_sz || selectedSz} ({recommendation.source_nh || selectedNh})</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Destination Zone:</span>
                                <span className="text-red-600 line-through ml-1">{migrateRule.rule_destination_zone || 'N/A'}</span>
                                <span className="mx-1">&rarr;</span>
                                <span className="text-green-600">{recommendation.destination_sz || selectedSz} ({recommendation.destination_nh || selectedNh})</span>
                              </div>
                            </div>
                          </div>
                        )}
                        {/* Birthright */}
                        {birthrightResult && (
                          <div>
                            <h4 className={`text-xs font-semibold mb-1 ${birthrightResult.compliant ? 'text-green-700' : 'text-red-700'}`}>
                              Birthright: {birthrightResult.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
                            </h4>
                            <p className="ml-2 text-[10px] text-gray-600">{birthrightResult.summary}</p>
                            {birthrightResult.violations.map((v, i) => (
                              <div key={i} className="ml-2 text-xs text-red-600">- {v.rule}: {v.reason}</div>
                            ))}
                          </div>
                        )}
                        {/* Compiled Rule Preview */}
                        {compiledRule && (
                          <div>
                            <h4 className="text-xs font-semibold text-indigo-700 mb-1">Compiled Rule ({compiledRule.vendor_format})</h4>
                            <pre className="ml-2 text-[10px] text-gray-700 font-mono bg-white rounded p-2 border border-gray-200 max-h-24 overflow-y-auto whitespace-pre-wrap">{compiledRule.compiled_text}</pre>
                          </div>
                        )}
                        {/* LDF Summary */}
                        {boundaryAnalysis && (
                          <div>
                            <h4 className="text-xs font-semibold text-purple-700 mb-1">LDF / Firewall Boundaries</h4>
                            <div className="ml-2 text-xs text-gray-600">
                              <span className="font-medium">{(boundaryAnalysis as Record<string, unknown>).boundaries as number} boundaries</span>
                              {' — '}{(boundaryAnalysis as Record<string, unknown>).flow_rule as string}
                            </div>
                          </div>
                        )}
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

                {/* Step 5: Submit Change - After approval, submit CHG and deploy */}
                {migrationStep === 'change' && (
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h3 className="text-sm font-semibold text-blue-800 mb-1">Submit Change Request</h3>
                      <p className="text-xs text-blue-600">Rule has been approved. Submit a ServiceNow Change Request (CHG) to deploy this rule to production firewalls.</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-gray-50 rounded-lg border">
                        <span className="text-[10px] text-gray-500 uppercase">Rule ID</span>
                        <div className="text-sm font-medium">{migrateRule?.id}</div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg border">
                        <span className="text-[10px] text-gray-500 uppercase">Application</span>
                        <div className="text-sm font-medium">{migrateRule?.app_name} ({migrateRule?.app_id})</div>
                      </div>
                    </div>

                    {!chgSubmitted ? (
                      <div className="space-y-3">
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <h4 className="text-xs font-semibold text-amber-800 mb-1">CHG Template</h4>
                          <div className="text-xs text-amber-700 space-y-1">
                            <div>Type: Normal Change</div>
                            <div>Category: Firewall Rule Deployment</div>
                            <div>Environment: {migrateRule ? (migrateRule as unknown as Record<string, string>).environment || 'Production' : 'Production'}</div>
                            <div>CI: Firewall Management System</div>
                            <div>Impact: Low | Risk: Low</div>
                          </div>
                        </div>
                        <div className="flex justify-between">
                          <button onClick={() => setMigrationStep('submit')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                            Back
                          </button>
                          <button onClick={handleSubmitChange} disabled={chgSubmitting}
                            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 shadow-sm">
                            {chgSubmitting ? 'Submitting CHG...' : 'Submit Change Request'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="p-4 bg-green-50 border-2 border-green-400 rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">&#9989;</span>
                            <span className="font-bold text-green-800">Change Request Submitted</span>
                          </div>
                          <div className="text-sm text-green-700">
                            <div>CHG Number: <strong className="font-mono">{chgNumber}</strong></div>
                            <div className="mt-1">Status: Approved &mdash; Ready for Deployment</div>
                          </div>
                        </div>
                        <div className="flex justify-between">
                          <div className="text-xs text-gray-500 self-center">CHG {chgNumber} approved. Click Deploy to push rule to firewalls.</div>
                          <button onClick={handleDeployAfterCHG}
                            className="px-6 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700 shadow-sm">
                            Deploy Rule via {chgNumber}
                          </button>
                        </div>
                      </div>
                    )}
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
