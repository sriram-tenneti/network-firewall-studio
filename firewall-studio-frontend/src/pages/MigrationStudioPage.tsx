import { useState, useEffect, useCallback } from 'react';
import { Edit, Trash2, Shield, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { ActionBar } from '@/components/layout/ActionBar';
import { MigrationDetailsForm } from '@/components/migration-studio/MigrationDetailsForm';
import { MigrationPlannerTable } from '@/components/migration-studio/MigrationPlannerTable';
import { MigrationRuleTable } from '@/components/migration-studio/MigrationRuleTable';
import { MigrationFirewallPlanner } from '@/components/migration-studio/MigrationFirewallPlanner';
import { NGDCSidebar } from '@/components/migration-studio/NGDCSidebar';
import { StatusBadge } from '@/components/ui/status-badge';
import type { MigrationDetails, MigrationRuleLifecycle, NGDCDataCenter, Application, FirewallRule } from '@/types';
import * as api from '@/lib/api';

export function MigrationStudioPage() {
  const [, setMigrations] = useState<MigrationDetails[]>([]);
  const [selectedMigration, setSelectedMigration] = useState<MigrationDetails | null>(null);
  const [mappings, setMappings] = useState<Record<string, unknown>[]>([]);
  const [ruleLifecycle, setRuleLifecycle] = useState<MigrationRuleLifecycle[]>([]);
  const [ngdcDCs, setNgdcDCs] = useState<NGDCDataCenter[]>([]);
  const [legacyDCs, setLegacyDCs] = useState<{ name: string; code: string }[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedDC, setSelectedDC] = useState('EAST_NGDC');
  const [filterStatus, setFilterStatus] = useState('all');
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [chgNumber, setChgNumber] = useState<string | undefined>(undefined);
  const [validationResult, setValidationResult] = useState<{ validation_passed: boolean; message: string; auto_mapped: number; conflicts: number } | null>(null);
  const [selectedAppId, setSelectedAppId] = useState('');
  const [existingRules, setExistingRules] = useState<FirewallRule[]>([]);
  const [rulesCollapsed, setRulesCollapsed] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadReferenceData = useCallback(async () => {
    try {
      const [dcs, legacy, apps] = await Promise.all([
        api.getNGDCDatacenters(),
        api.getLegacyDatacenters(),
        api.getApplications(),
      ]);
      setNgdcDCs(dcs);
      setLegacyDCs(legacy);
      setApplications(apps);
    } catch (err) {
      console.error('Failed to load reference data:', err);
    }
  }, []);

  const loadMigrations = useCallback(async () => {
    try {
      const data = await api.getMigrations();
      setMigrations(data);
      if (data.length > 0 && !selectedMigration) {
        setSelectedMigration(data[0]);
        loadMigrationDetails(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load migrations:', err);
    }
  }, []);

  const loadMigrationDetails = async (migrationId: string) => {
    try {
      const [mapData, rlData] = await Promise.all([
        api.getMigrationMappings(migrationId).catch(() => []),
        api.getMigrationRuleLifecycle(migrationId).catch(() => []),
      ]);
      setMappings(mapData as Record<string, unknown>[]);
      setRuleLifecycle(rlData);
    } catch (err) {
      console.error('Failed to load migration details:', err);
    }
  };

  const loadExistingRules = useCallback(async (appId: string) => {
    if (!appId) { setExistingRules([]); return; }
    try {
      const rules = await api.getRules(appId);
      setExistingRules(rules);
    } catch (err) {
      console.error('Failed to load existing rules:', err);
    }
  }, []);

  useEffect(() => {
    loadReferenceData();
    loadMigrations();
  }, [loadReferenceData, loadMigrations]);

  useEffect(() => {
    loadExistingRules(selectedAppId);
  }, [selectedAppId, loadExistingRules]);

  const handleCreateMigration = async (data: {
    application: string;
    source_legacy_dc: string;
    target_ngdc: string;
    map_to_standard_groups: boolean;
    map_to_subnet_cidr: boolean;
  }) => {
    try {
      const migration = await api.createMigration(data);
      setSelectedMigration(migration);
      showNotification(`Migration ${migration.id} created for ${data.application}`);
      loadMigrations();
      loadMigrationDetails(migration.id);
    } catch {
      showNotification('Failed to create migration', 'error');
    }
  };

  const handleValidateMigration = async () => {
    if (!selectedMigration) return;
    try {
      const result = await api.validateMigration(selectedMigration.id);
      setValidationResult(result);
      showNotification(result.message, result.validation_passed ? 'success' : 'info');
    } catch {
      showNotification('Validation failed', 'error');
    }
  };

  const handleSubmitMigration = async () => {
    if (!selectedMigration) return;
    try {
      const result = await api.submitMigration(selectedMigration.id);
      setChgNumber(result.chg.chg_number);
      showNotification(`Migration submitted - ServiceNow ${result.chg.chg_number} created`);
      loadMigrations();
    } catch {
      showNotification('Failed to submit migration', 'error');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await api.deleteRule(ruleId);
      showNotification(`Rule ${ruleId} deleted`);
      setConfirmDeleteId(null);
      loadExistingRules(selectedAppId);
    } catch {
      showNotification('Failed to delete rule', 'error');
    }
  };

  const handleCertifyRule = async (ruleId: string) => {
    try {
      await api.certifyRule(ruleId);
      showNotification(`Rule ${ruleId} certified`);
      loadExistingRules(selectedAppId);
    } catch {
      showNotification('Failed to certify rule', 'error');
    }
  };

  const handleRequestReview = (ruleId: string) => {
    showNotification(`Review requested for migration rule ${ruleId}`, 'info');
  };

  // Mock migration planner rules for the firewall planner view
  const firewallPlannerRules = [
    { source: '192.168.2.0/24', destination: 'PSA_GEN_PROD', status: 'Automapped' as const, details: '' },
    { source: '10.100.0.0/16', destination: 'PSA_GEN', status: 'Needs Review' as const, details: '' },
    { source: 'Server Farm 1', destination: 'PSA_PROD_APP1', status: 'Blocked' as const, details: '2 conflicts' },
    { source: '10.0.0.1:22', destination: '10.0.0.0:22 8443', status: 'Blocked' as const, details: '' },
  ];

  return (
    <div className="flex flex-col h-full">
      <ActionBar mode="migration" />

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

      {/* Top bar: Application ID & DC Scope */}
      <div className="flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">Application ID</label>
          <select
            value={selectedAppId}
            onChange={(e) => setSelectedAppId(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium w-48"
          >
            <option value="">All Applications</option>
            {applications.map((app) => (
              <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">Data Center Scope:</label>
          <select
            value={selectedDC}
            onChange={(e) => setSelectedDC(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium"
          >
            {ngdcDCs.map((dc) => (
              <option key={dc.code} value={dc.code}>{dc.name}</option>
            ))}
          </select>
        </div>
        {selectedAppId && (
          <div className="ml-auto text-xs text-slate-500">
            {existingRules.length} existing rule(s) for {selectedAppId}
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex flex-1 gap-4 overflow-hidden p-4">
        {/* Left: Migration Details + Planner Tables */}
        <div className="flex-1 space-y-4 overflow-y-auto">
          {/* Collapsible Existing Rules Panel with inline actions */}
          {selectedAppId && existingRules.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <button
                onClick={() => setRulesCollapsed(!rulesCollapsed)}
                className="flex w-full items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors rounded-t-xl"
              >
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-800">Existing Rules for {selectedAppId}</h3>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                    {existingRules.length}
                  </span>
                </div>
                {rulesCollapsed ? (
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                ) : (
                  <ChevronUp className="h-4 w-4 text-slate-400" />
                )}
              </button>
              {!rulesCollapsed && (
                <div className="overflow-x-auto max-h-64 overflow-y-auto border-t border-slate-100">
                  <table className="w-full">
                    <thead className="sticky top-0 z-10">
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500">Rule ID</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500">Source</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500">Destination</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500">Status</th>
                        <th className="px-3 py-2 text-right text-xs font-semibold text-slate-500">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {existingRules.map((rule) => {
                        const isConfirming = confirmDeleteId === rule.rule_id;
                        return (
                          <tr
                            key={rule.rule_id}
                            className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors"
                          >
                            <td className="px-3 py-2 text-xs font-semibold text-slate-700">{rule.rule_id}</td>
                            <td className="px-3 py-2 text-xs text-slate-600">
                              <span className="rounded bg-blue-50 border border-blue-200 px-1.5 py-0.5 text-blue-700 font-medium">
                                {rule.source.group_name || rule.source.ip_address || rule.source.cidr || '-'}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-xs text-slate-600">
                              <span className="rounded bg-orange-50 border border-orange-200 px-1.5 py-0.5 text-orange-700 font-medium">
                                {rule.destination.name}
                              </span>
                            </td>
                            <td className="px-3 py-2"><StatusBadge status={rule.status} /></td>
                            <td className="px-3 py-2">
                              <div className="flex items-center justify-end gap-1">
                                <button
                                  onClick={() => handleRequestReview(rule.rule_id)}
                                  className="rounded p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                                  title="Review rule"
                                >
                                  <Eye className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => showNotification(`Loaded rule ${rule.rule_id} for migration review`, 'info')}
                                  className="rounded p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 transition-colors"
                                  title="Edit rule"
                                >
                                  <Edit className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => handleCertifyRule(rule.rule_id)}
                                  className="rounded p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                                  title="Certify rule"
                                >
                                  <Shield className="h-3.5 w-3.5" />
                                </button>
                                {isConfirming ? (
                                  <div className="flex items-center gap-1">
                                    <button
                                      onClick={() => handleDeleteRule(rule.rule_id)}
                                      className="rounded bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700"
                                    >
                                      Confirm
                                    </button>
                                    <button
                                      onClick={() => setConfirmDeleteId(null)}
                                      className="rounded bg-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-300"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => setConfirmDeleteId(rule.rule_id)}
                                    className="rounded p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                                    title="Delete rule"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                )}
                              </div>
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

          <div className="flex gap-4">
            {/* Migration Details Form */}
            <div className="w-80 flex-shrink-0">
              <MigrationDetailsForm
                applications={applications.map(a => a.app_id)}
                legacyDCs={legacyDCs}
                ngdcDCs={ngdcDCs.map(dc => ({ name: dc.name, code: dc.code }))}
                onSubmit={handleCreateMigration}
                existingMigration={selectedMigration}
              />
            </div>

            {/* Migration Planner Table */}
            <div className="flex-1">
              <MigrationPlannerTable
                mappings={mappings}
                filterStatus={filterStatus}
                onFilterChange={setFilterStatus}
              />
            </div>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div className={`flex items-center gap-3 rounded-xl px-5 py-3 ${
              validationResult.validation_passed
                ? 'bg-emerald-50 border border-emerald-200'
                : 'bg-amber-50 border border-amber-200'
            }`}>
              <div className="flex items-center gap-4">
                <span className="text-sm font-bold text-slate-700">Migration Summary</span>
                <span className="text-sm text-slate-600">{validationResult.auto_mapped} Auto-Mapped</span>
                <span className="text-sm text-slate-600">{validationResult.conflicts} Conflict</span>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={handleValidateMigration}
                  className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
                >
                  Validate Migration
                </button>
                <button className="rounded-lg border border-slate-300 bg-white px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
                  Save Draft
                </button>
              </div>
            </div>
          )}

          {/* Firewall Migration Planner */}
          <MigrationFirewallPlanner
            applicationId={selectedAppId || selectedMigration?.application || 'CRMApp'}
            dcScope={selectedDC}
            rules={firewallPlannerRules}
            onValidate={handleValidateMigration}
            onDryRun={() => showNotification('Dry run completed - no changes applied', 'info')}
            onMigrateGenerate={() => showNotification('Rules generated successfully')}
            onSubmit={handleSubmitMigration}
            chgNumber={chgNumber}
          />

          {/* Rule Lifecycle Migration */}
          <MigrationRuleTable
            rules={ruleLifecycle}
            onValidate={handleValidateMigration}
            onDryRun={() => showNotification('Dry run completed', 'info')}
            onMigrate={() => showNotification('Migration & deploy initiated')}
            onDelete={() => showNotification('Deleted')}
          />
        </div>

        {/* Right: NGDC Sidebar */}
        <NGDCSidebar
          datacenters={ngdcDCs}
          selectedDC={selectedDC}
          onSelectDC={setSelectedDC}
        />
      </div>
    </div>
  );
}
