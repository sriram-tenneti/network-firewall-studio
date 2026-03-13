import { useState, useEffect, useCallback } from 'react';
import { ActionBar } from '@/components/layout/ActionBar';
import { MigrationDetailsForm } from '@/components/migration-studio/MigrationDetailsForm';
import { MigrationPlannerTable } from '@/components/migration-studio/MigrationPlannerTable';
import { MigrationRuleTable } from '@/components/migration-studio/MigrationRuleTable';
import { MigrationFirewallPlanner } from '@/components/migration-studio/MigrationFirewallPlanner';
import { NGDCSidebar } from '@/components/migration-studio/NGDCSidebar';
import type { MigrationDetails, MigrationMapping, MigrationRuleLifecycle, NGDCDataCenter, Application } from '@/types';
import * as api from '@/lib/api';

export function MigrationStudioPage() {
  const [, setMigrations] = useState<MigrationDetails[]>([]);
  const [selectedMigration, setSelectedMigration] = useState<MigrationDetails | null>(null);
  const [mappings, setMappings] = useState<MigrationMapping[]>([]);
  const [ruleLifecycle, setRuleLifecycle] = useState<MigrationRuleLifecycle[]>([]);
  const [ngdcDCs, setNgdcDCs] = useState<NGDCDataCenter[]>([]);
  const [legacyDCs, setLegacyDCs] = useState<{ name: string; code: string }[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedDC, setSelectedDC] = useState('EAST_NGDC');
  const [filterStatus, setFilterStatus] = useState('all');
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [chgNumber, setChgNumber] = useState<string | undefined>(undefined);
  const [validationResult, setValidationResult] = useState<{ validation_passed: boolean; message: string; auto_mapped: number; conflicts: number } | null>(null);

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
        api.getMigrationMappings(migrationId),
        api.getMigrationRuleLifecycle(migrationId),
      ]);
      setMappings(mapData);
      setRuleLifecycle(rlData);
    } catch (err) {
      console.error('Failed to load migration details:', err);
    }
  };

  useEffect(() => {
    loadReferenceData();
    loadMigrations();
  }, [loadReferenceData, loadMigrations]);

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

  // Mock migration planner rules for the firewall planner view
  const firewallPlannerRules = [
    { source: '192.168.2.0/24', destination: 'PSA_GEN_PROD', status: 'Automapped' as const, details: '' },
    { source: '10.100.0.0/16', destination: 'PSA_GEN', status: 'Needs Review' as const, details: '' },
    { source: 'Server Farm 1', destination: 'PSA_PROD_APP1', status: 'Blocked' as const, details: '2 conflicts' },
    { source: '10.0.0.1:22', destination: '10.0.0.0:22 8443', status: 'Blocked' as const, details: '' },
  ];

  return (
    <div className="flex flex-col h-full">
      <ActionBar
        mode="migration"
        onAdd={() => setSelectedMigration(null)}
        onCertify={handleValidateMigration}
        onViewHistory={() => {}}
      />

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
          <input
            type="text"
            value={selectedMigration?.application || 'CRMApp'}
            readOnly
            className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-medium w-48"
          />
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
      </div>

      {/* Main content */}
      <div className="flex flex-1 gap-4 overflow-hidden p-4">
        {/* Left: Migration Details + Planner Tables */}
        <div className="flex-1 space-y-4 overflow-y-auto">
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
            applicationId={selectedMigration?.application || 'CRMApp'}
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
