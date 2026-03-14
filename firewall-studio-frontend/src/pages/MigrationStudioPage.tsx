import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { LegacyRuleDetailModal } from '@/components/migration-studio/LegacyRuleDetailModal';
import { MappingPanel } from '@/components/migration-studio/MappingPanel';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import { getLegacyRules, updateLegacyRule, getApplications, submitForReview } from '@/lib/api';
import type { LegacyRule, Application } from '@/types';
import type { Column } from '@/components/shared/DataTable';

export function MigrationStudioPage() {
  const [legacyRules, setLegacyRules] = useState<LegacyRule[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [activeTab, setActiveTab] = useState('All');
  const [showMapping, setShowMapping] = useState(false);
  const [mappingRules, setMappingRules] = useState<LegacyRule[]>([]);

  const detailModal = useModal<LegacyRule>();
  const { notification, showNotification } = useNotification();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, appsData] = await Promise.all([
        getLegacyRules(selectedApp || undefined),
        getApplications(),
      ]);
      setLegacyRules(rulesData);
      setApplications(appsData);
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
    Completed: legacyRules.filter(r => r.migration_status === 'Completed').length,
  };

  const handleAcceptMapping = async (ruleId: string) => {
    try {
      await updateLegacyRule(ruleId, { migration_status: 'Completed' });
      showNotification('Mapping accepted - rule migrated', 'success');
      loadData();
    } catch {
      showNotification('Failed to accept mapping', 'error');
    }
  };

  const handleStartMigration = async (ruleId: string) => {
    try {
      await updateLegacyRule(ruleId, { migration_status: 'In Progress' });
      showNotification('Migration started', 'success');
      detailModal.close();
      loadData();
    } catch {
      showNotification('Failed to start migration', 'error');
    }
  };

  const handleCustomize = (ruleId: string) => {
    const rule = legacyRules.find(r => r.id === ruleId);
    if (rule) detailModal.open(rule);
  };

  const handleSaveCustomization = async (ruleId: string, data: Partial<LegacyRule>) => {
    try {
      await updateLegacyRule(ruleId, data);
      showNotification('Customization saved successfully', 'success');
      detailModal.close();
      loadData();
    } catch {
      showNotification('Failed to save customization', 'error');
    }
  };

  const handleBulkAnalyze = () => {
    const nonStandard = legacyRules.filter(r => !r.is_standard && r.migration_status === 'Not Started');
    setMappingRules(nonStandard.slice(0, 10));
    setShowMapping(true);
    showNotification('Analyzing ' + nonStandard.length + ' non-standard rules', 'info');
  };

  const handleSubmitForReview = async () => {
    const inProgress = legacyRules.filter(r => r.migration_status === 'In Progress');
    for (const rule of inProgress) {
      try {
        await submitForReview(rule.id, 'Migration review for ' + rule.rule_name);
      } catch { /* continue */ }
    }
    showNotification(inProgress.length + ' rules submitted for review', 'success');
  };

  const columns: Column<LegacyRule>[] = [
    { key: 'app_id', header: 'App ID', sortable: true, width: '80px' },
    { key: 'app_distributed_id', header: 'App Name', sortable: true, width: '120px' },
    { key: 'rule_name', header: 'Rule Name', sortable: true, width: '200px' },
    { key: 'source_zone', header: 'Source Zone', sortable: true, width: '100px' },
    {
      key: 'source_entries', header: 'Sources', sortable: false, width: '150px',
      render: (_, row) => (
        <span className="font-mono text-xs">{row.source_entries?.slice(0, 2).join(', ')}{(row.source_entries?.length || 0) > 2 ? ' +' + ((row.source_entries?.length || 0) - 2) : ''}</span>
      ),
    },
    {
      key: 'destination_entries', header: 'Destinations', sortable: false, width: '150px',
      render: (_, row) => (
        <span className="font-mono text-xs">{row.destination_entries?.slice(0, 2).join(', ')}{(row.destination_entries?.length || 0) > 2 ? ' +' + ((row.destination_entries?.length || 0) - 2) : ''}</span>
      ),
    },
    {
      key: 'ports', header: 'Ports', sortable: false, width: '80px',
      render: (_, row) => <span className="text-xs">{row.ports?.join(', ') || 'N/A'}</span>,
    },
    {
      key: 'is_standard', header: 'Standard', sortable: true, width: '90px',
      render: (_, row) => <StatusBadge status={row.is_standard ? 'Yes' : 'No'} />,
    },
    {
      key: 'migration_status', header: 'Migration', sortable: true, width: '110px',
      render: (_, row) => <StatusBadge status={row.migration_status} />,
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '120px',
      render: (_, row) => (
        <div className="flex gap-1.5" onClick={e => e.stopPropagation()}>
          <button onClick={() => detailModal.open(row)} className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100">Details</button>
          {row.migration_status === 'Not Started' && !row.is_standard && (
            <button onClick={() => handleStartMigration(row.id)} className="px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100">Migrate</button>
          )}
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
    { id: 'Completed', label: 'Completed', count: counts.Completed },
  ];

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Migration to NGDC</h1>
          <p className="text-sm text-gray-500 mt-1">Analyze legacy rules, map to NGDC standards, and migrate with review workflow</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedApp}
            onChange={e => setSelectedApp(e.target.value)}
          >
            <option value="">All Applications</option>
            {applications.map(app => (
              <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
            ))}
          </select>
          <button onClick={handleBulkAnalyze} className="px-4 py-2 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-md hover:bg-amber-100">
            Bulk Analyze
          </button>
          <button onClick={handleSubmitForReview} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm">
            Submit for Review
          </button>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-3 mb-6">
        {[
          { label: 'Total Rules', value: counts.All, color: 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800' },
          { label: 'Non-Standard', value: counts['Non-Standard'], color: 'bg-gradient-to-br from-red-100 to-red-200 text-red-800' },
          { label: 'Standard', value: counts.Standard, color: 'bg-gradient-to-br from-green-100 to-green-200 text-green-800' },
          { label: 'Not Started', value: counts['Not Started'], color: 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-800' },
          { label: 'In Progress', value: counts['In Progress'], color: 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-800' },
          { label: 'Completed', value: counts.Completed, color: 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-800' },
        ].map(card => (
          <div key={card.label} className={'p-3 rounded-lg shadow-sm ' + card.color}>
            <div className="text-xl font-bold">{card.value}</div>
            <div className="text-xs font-medium mt-0.5">{card.label}</div>
          </div>
        ))}
      </div>

      {showMapping && mappingRules.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-800">Migration Mapping Analysis</h2>
            <button onClick={() => setShowMapping(false)} className="text-sm text-gray-500 hover:text-gray-700">Close Analysis</button>
          </div>
          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {mappingRules.map(rule => (
              <MappingPanel
                key={rule.id}
                rule={rule}
                onAcceptMapping={handleAcceptMapping}
                onCustomize={handleCustomize}
              />
            ))}
          </div>
        </div>
      )}

      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 pt-4">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </div>
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <DataTable
              data={filteredRules}
              columns={columns}
              keyField="id"
              searchFields={['app_id', 'app_distributed_id', 'rule_name', 'source_zone']}
              onRowClick={(row) => detailModal.open(row)}
              emptyMessage="No legacy rules found"
              defaultPageSize={50}
            />
          )}
        </div>
      </div>

      <LegacyRuleDetailModal
        isOpen={detailModal.isOpen}
        onClose={detailModal.close}
        rule={detailModal.data}
        onStartMigration={() => { if (detailModal.data) handleStartMigration(detailModal.data.id); }}
        onSaveCustomization={handleSaveCustomization}
      />
    </div>
  );
}
