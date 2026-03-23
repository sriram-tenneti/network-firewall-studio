import { useState, useCallback, useEffect } from 'react';
import { importLegacyRulesExcel, importNGDCMappingsExcel, getNGDCMappings, deleteNGDCMapping, createNGDCMapping, getRules, importRulesToNGDC, getImportedApps, createAppDCMapping, deleteAppDCMapping, getLegacyRules, clearAllLegacyRules } from '@/lib/api';
import type { FirewallRule, LegacyRule } from '@/types';

interface ImportedApp {
  app_id: string;
  app_name: string;
  app_distributed_id: string;
  rule_count: number;
  has_mapping: boolean;
  components: Record<string, unknown>[];
}

interface NewComponentForm {
  component: string;
  dc: string;
  nh: string;
  sz: string;
  cidr: string;
  notes: string;
}

interface DataImportPageProps {
  context?: string;
}

export default function DataImportPage({ context }: DataImportPageProps) {
  const [file, setFile] = useState<File | null>(null);
  const [selectedEnv, setSelectedEnv] = useState<string>('Production');
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [mappings, setMappings] = useState<Record<string, unknown>[]>([]);
  const [showMappings, setShowMappings] = useState(false);
  const [newMapping, setNewMapping] = useState({ legacy_name: '', legacy_dc: '', ngdc_name: '', ngdc_dc: '', ngdc_nh: '', ngdc_sz: '', type: 'group' });

  // Imported apps mapping state
  const [importedApps, setImportedApps] = useState<ImportedApp[]>([]);
  const [showAppMappings, setShowAppMappings] = useState(false);
  const [expandedAppId, setExpandedAppId] = useState<string | null>(null);
  const [addingComponentForApp, setAddingComponentForApp] = useState<string | null>(null);
  const [newComponentForm, setNewComponentForm] = useState<NewComponentForm>({
    component: 'APP', dc: 'ALPHA_NGDC', nh: '', sz: '', cidr: '', notes: ''
  });
  const [savingComponent, setSavingComponent] = useState(false);
  const [appFilter, setAppFilter] = useState<'all' | 'unmapped' | 'mapped'>('all');

  // Imported legacy rules display state
  const [importedRules, setImportedRules] = useState<LegacyRule[]>([]);
  const [showImportedRules, setShowImportedRules] = useState(false);
  const [rulesAppFilter, setRulesAppFilter] = useState<string>('');
  const [rulesSearchQuery, setRulesSearchQuery] = useState<string>('');
  const [clearing, setClearing] = useState(false);

  // NFR import state (for ngdc-import-rules context)
  const [nfrRules, setNfrRules] = useState<FirewallRule[]>([]);
  const [nfrApps, setNfrApps] = useState<{ value: string; label: string }[]>([]);
  const [selectedImportApps, setSelectedImportApps] = useState<Set<string>>(new Set());
  const [importingFromNFR, setImportingFromNFR] = useState(false);
  const [nfrLoading, setNfrLoading] = useState(false);
  const [importResult, setImportResult] = useState<{ imported: number; apps: number } | null>(null);

  const [nfrEnvFilter, setNfrEnvFilter] = useState<string>('');
  const isNGDCMappings = context === 'ngdc-mappings';
  const isNFRImport = context === 'ngdc-import-rules';
  const pageTitle = isNGDCMappings ? 'NGDC Organization Mappings' :
    isNFRImport ? 'Import Rules from Network Firewall Request' :
    context === 'ngdc-standardization' ? 'Import Legacy Rules for Migration' :
    context === 'firewall-management' ? 'Import Firewall Rules' :
    context === 'firewall-studio' ? 'Import Rules for Firewall Studio' :
    'Data Import';

  // Load NFR apps when this is the NFR import page
  const loadNFRApps = useCallback(async () => {
    setNfrLoading(true);
    try {
      const rules = await getRules();
      setNfrRules(rules);
      const filteredByEnv = nfrEnvFilter ? rules.filter((r: FirewallRule) => r.environment === nfrEnvFilter) : rules;
      const apps = Array.from(new Set(filteredByEnv.map((r: FirewallRule) => `${r.application}|${r.application_name || r.application}`))).map(key => {
        const [appId, appName] = (key as string).split('|');
        return { value: appId, label: `${appId} - ${appName}` };
      });
      setNfrApps(apps);
    } catch { setNfrApps([]); }
    setNfrLoading(false);
  }, [nfrEnvFilter]);

  useEffect(() => {
    if (isNFRImport) { setSelectedImportApps(new Set()); loadNFRApps(); }
  }, [isNFRImport, loadNFRApps]);

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

  const handleImportFromNFR = async () => {
    if (selectedImportApps.size === 0) return;
    setImportingFromNFR(true);
    setError('');
    setImportResult(null);
    try {
      const selectedAppIds = Array.from(selectedImportApps);
      const res = await importRulesToNGDC(selectedAppIds);
      setImportResult({ imported: res.imported, apps: selectedImportApps.size });
      setSelectedImportApps(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import rules from Network Request');
    }
    setImportingFromNFR(false);
  };

  const loadMappings = useCallback(async () => {
    try {
      const data = await getNGDCMappings();
      setMappings(data);
      setShowMappings(true);
    } catch { setError('Failed to load mappings'); }
  }, []);

  const loadImportedApps = useCallback(async () => {
    try {
      const apps = await getImportedApps();
      setImportedApps(apps);
      setShowAppMappings(true);
    } catch { /* ignore */ }
  }, []);

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setError('');
    setResult(null);
    try {
      const res = isNGDCMappings
        ? await importNGDCMappingsExcel(file)
        : await importLegacyRulesExcel(file);
      setResult(res);
      if (isNGDCMappings) loadMappings();
      // After legacy import, load imported apps for mapping and load rules
      if (!isNGDCMappings) {
        loadImportedApps();
        loadImportedRules();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleAddComponent = async (appId: string) => {
    setSavingComponent(true);
    try {
      await createAppDCMapping({
        app_id: appId,
        component: newComponentForm.component,
        dc: newComponentForm.dc,
        nh: newComponentForm.nh,
        sz: newComponentForm.sz,
        cidr: newComponentForm.cidr,
        notes: newComponentForm.notes,
        status: 'Active',
      });
      setAddingComponentForApp(null);
      setNewComponentForm({ component: 'APP', dc: 'ALPHA_NGDC', nh: '', sz: '', cidr: '', notes: '' });
      await loadImportedApps();
    } catch {
      setError('Failed to add component mapping');
    } finally {
      setSavingComponent(false);
    }
  };

  const handleDeleteComponent = async (mappingId: string) => {
    try {
      await deleteAppDCMapping(mappingId);
      await loadImportedApps();
    } catch {
      setError('Failed to delete component mapping');
    }
  };

  const loadImportedRules = useCallback(async () => {
    try {
      const rules = await getLegacyRules();
      setImportedRules(rules);
      setShowImportedRules(true);
    } catch { /* ignore */ }
  }, []);

  const exportImportedRulesToCSV = () => {
    const filtered = getFilteredImportedRules();
    if (filtered.length === 0) return;
    const headers = ['App ID', 'App Distributed ID', 'App Name', 'Inventory Item', 'Policy Name', 'Rule Global', 'Rule Action', 'Rule Source', 'Rule Source Expanded', 'Rule Source Zone', 'Rule Destination', 'Rule Destination Expanded', 'Rule Destination Zone', 'Rule Service', 'Rule Service Expanded', 'RN', 'RC', 'Migration Status'];
    const rows = filtered.map(r => [
      r.app_id, r.app_distributed_id, r.app_name, r.inventory_item, r.policy_name,
      r.rule_global ? 'TRUE' : 'FALSE', r.rule_action, r.rule_source, r.rule_source_expanded,
      r.rule_source_zone, r.rule_destination, r.rule_destination_expanded,
      r.rule_destination_zone, r.rule_service, r.rule_service_expanded, r.rn, r.rc, r.migration_status
    ]);
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${String(cell || '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `imported-legacy-rules-${rulesAppFilter || 'all'}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getFilteredImportedRules = () => {
    let filtered = importedRules;
    if (rulesAppFilter) filtered = filtered.filter(r => String(r.app_id) === rulesAppFilter);
    if (rulesSearchQuery.trim()) {
      const q = rulesSearchQuery.toLowerCase();
      filtered = filtered.filter(r =>
        String(r.app_id).toLowerCase().includes(q) ||
        (r.app_name || '').toLowerCase().includes(q) ||
        (r.rule_source || '').toLowerCase().includes(q) ||
        (r.rule_source_expanded || '').toLowerCase().includes(q) ||
        (r.rule_destination || '').toLowerCase().includes(q) ||
        (r.rule_destination_expanded || '').toLowerCase().includes(q) ||
        (r.rule_service || '').toLowerCase().includes(q) ||
        (r.rule_source_zone || '').toLowerCase().includes(q) ||
        (r.rule_destination_zone || '').toLowerCase().includes(q)
      );
    }
    return filtered;
  };

  const handleClearAllRules = async () => {
    if (!confirm('This will delete all non-migrated legacy rules. Rules already migrated or in-progress will be preserved. App DC mappings will NOT be affected. Continue?')) return;
    setClearing(true);
    try {
      const res = await clearAllLegacyRules();
      setImportedRules([]);
      setShowImportedRules(false);
      setResult(null);
      setError('');
      alert(`Cleared ${res.deleted} rules. You can now import fresh data.`);
    } catch {
      setError('Failed to clear rules');
    } finally {
      setClearing(false);
    }
  };

  const handleDeleteMapping = async (id: string) => {
    try {
      await deleteNGDCMapping(id);
      setMappings(prev => prev.filter(m => (m as Record<string, unknown>).id !== id));
    } catch { setError('Failed to delete mapping'); }
  };

  const handleAddMapping = async () => {
    try {
      const created = await createNGDCMapping(newMapping);
      setMappings(prev => [...prev, created]);
      setNewMapping({ legacy_name: '', legacy_dc: '', ngdc_name: '', ngdc_dc: '', ngdc_nh: '', ngdc_sz: '', type: 'group' });
    } catch { setError('Failed to add mapping'); }
  };

  return (
    <div className="max-w-[1800px] mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isNGDCMappings
              ? 'Manage organization-provided legacy-to-NGDC name mappings used during migration'
              : isNFRImport
              ? 'Select applications to import their Network Firewall Request rules for NGDC migration'
              : 'Upload Excel (.xlsx) files to import rules into the system'}
          </p>
        </div>
        {isNFRImport ? (
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={nfrEnvFilter} onChange={e => setNfrEnvFilter(e.target.value)}>
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
        ) : (
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedEnv} onChange={e => setSelectedEnv(e.target.value)}>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
        )}
      </div>

      {/* NFR Import Section - App Dropdown */}
      {isNFRImport && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-5">
            <p className="text-sm text-indigo-700">Select one or more applications to import their Network Firewall Request rules for NGDC migration. These rules will be copied and available for one-to-one DC mapping in Migration Studio.</p>
          </div>

          {nfrLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Loading applications from Network Firewall Request...</p>
            </div>
          ) : nfrApps.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500">No applications found in Network Firewall Request.</p>
              <button onClick={loadNFRApps} className="mt-3 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100">
                Retry
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">{nfrApps.length} Applications Available</span>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
                    <input type="checkbox" checked={selectedImportApps.size === nfrApps.length && nfrApps.length > 0} onChange={selectAllImportApps} className="rounded border-gray-300 text-indigo-600" />
                    Select All
                  </label>
                  <button onClick={loadNFRApps} className="text-xs text-indigo-600 hover:text-indigo-800">Refresh</button>
                </div>
              </div>
              <div className="max-h-80 overflow-y-auto border rounded-lg divide-y divide-gray-100">
                {nfrApps.map(app => (
                  <label key={app.value} className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-indigo-50 transition-colors ${selectedImportApps.has(app.value) ? 'bg-indigo-50' : ''}`}>
                    <input type="checkbox" checked={selectedImportApps.has(app.value)} onChange={() => toggleImportApp(app.value)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                    <span className="text-sm text-gray-800 font-medium">{app.label}</span>
                    <span className="text-xs text-gray-400 ml-auto">{nfrRules.filter(r => r.application === app.value && (!nfrEnvFilter || r.environment === nfrEnvFilter)).length} rules</span>
                  </label>
                ))}
              </div>

              {selectedImportApps.size > 0 && (
                <div className="mt-4 bg-gray-50 rounded-lg p-4 flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    <strong>{selectedImportApps.size}</strong> app(s) selected &middot; <strong>{nfrRules.filter(r => selectedImportApps.has(r.application) && (!nfrEnvFilter || r.environment === nfrEnvFilter)).length}</strong> rules will be imported for migration
                  </span>
                  <button onClick={handleImportFromNFR} disabled={importingFromNFR}
                    className="px-6 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 shadow-sm transition-colors">
                    {importingFromNFR ? 'Importing...' : `Import ${selectedImportApps.size} App(s)`}
                  </button>
                </div>
              )}
            </>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
          )}
          {importResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-sm font-semibold text-green-800 mb-1">Import Successful</h3>
              <p className="text-sm text-green-700">
                <strong>{importResult.imported}</strong> rules imported from <strong>{importResult.apps}</strong> app(s) for NGDC migration. Go to <strong>Migration Studio</strong> to map and migrate these rules.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Excel Import Section (for non-NFR contexts) */}
      {!isNFRImport && <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">
          {isNGDCMappings ? 'Import Mappings from Excel' : 'Import from Excel'}
        </h2>
        <div className="flex items-center gap-4">
          <label className="flex-1">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all">
              <input
                type="file"
                accept=".xlsx"
                className="hidden"
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
              <svg className="w-10 h-10 mx-auto text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <p className="text-sm text-gray-600">{file ? file.name : 'Click to select .xlsx file'}</p>
            </div>
          </label>
          <button
            onClick={handleImport}
            disabled={!file || importing}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {importing ? 'Importing...' : 'Import'}
          </button>
          <button
            onClick={handleClearAllRules}
            disabled={clearing}
            className="px-4 py-3 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 border border-red-200 disabled:opacity-50 transition-colors text-sm"
            title="Delete all imported rules and start fresh"
          >
            {clearing ? 'Clearing...' : 'Clear All & Re-import'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
        )}
        {result && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-semibold text-green-800 mb-2">Import Successful</h3>
            <div className="grid grid-cols-3 gap-3 text-xs">
              {result.imported !== undefined && <div className="bg-white rounded p-2"><span className="text-gray-500">Rules Imported:</span> <span className="font-bold text-green-700">{String(result.imported)}</span></div>}
              {result.total_rules !== undefined && <div className="bg-white rounded p-2"><span className="text-gray-500">Total Rules:</span> <span className="font-bold">{String(result.total_rules)}</span></div>}
              {result.groups_expanded !== undefined && <div className="bg-white rounded p-2"><span className="text-gray-500">Groups Expanded:</span> <span className="font-bold text-blue-700">{String(result.groups_expanded)}</span></div>}
              {result.duplicates_skipped !== undefined && <div className="bg-white rounded p-2"><span className="text-gray-500">Duplicates Skipped:</span> <span className="font-bold text-amber-700">{String(result.duplicates_skipped)}</span></div>}
            </div>
            <p className="text-xs text-green-600 mt-2">Source/destination groups have been expanded to show associated IPs, ranges, and subnets.</p>
          </div>
        )}
      </div>}

      {/* Imported Legacy Rules with Source/Destination Details */}
      {!isNGDCMappings && !isNFRImport && showImportedRules && importedRules.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">Imported Legacy Rules</h2>
              <p className="text-xs text-gray-500 mt-1">View source and destination details of imported rules. Use filters to narrow down, then export as CSV.</p>
            </div>
            <div className="flex items-center gap-3">
              <select className="px-2 py-1.5 text-xs border rounded-md" value={rulesAppFilter} onChange={e => setRulesAppFilter(e.target.value)}>
                <option value="">All Apps</option>
                {Array.from(new Set(importedRules.map(r => String(r.app_id)))).sort().map(appId => (
                  <option key={appId} value={appId}>{appId}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Search source, destination, service..."
                value={rulesSearchQuery}
                onChange={e => setRulesSearchQuery(e.target.value)}
                className="px-2 py-1.5 text-xs border rounded-md w-64"
              />
              <button onClick={exportImportedRulesToCSV} className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700">
                Export CSV
              </button>
              <button onClick={() => setShowImportedRules(false)} className="px-3 py-2 text-xs text-gray-500 border rounded-md hover:bg-gray-50">
                Hide
              </button>
            </div>
          </div>

          <div className="text-xs text-gray-500 mb-2">
            Showing <strong className="text-gray-700">{getFilteredImportedRules().length}</strong> of <strong className="text-gray-700">{importedRules.length}</strong> rules
          </div>

          <div className="overflow-x-auto max-h-[500px] overflow-y-auto border rounded-lg">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Rule ID</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">App ID</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">App Name</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Policy</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Action</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Rule Source</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap min-w-[180px]">Source Details</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Src Zone</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Rule Destination</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap min-w-[180px]">Destination Details</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Dst Zone</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Service</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-500 whitespace-nowrap">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {getFilteredImportedRules().slice(0, 200).map(rule => (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-2 py-1.5 font-mono text-gray-600">{rule.id}</td>
                    <td className="px-2 py-1.5 font-mono font-medium">{String(rule.app_id)}</td>
                    <td className="px-2 py-1.5 text-gray-700 max-w-[120px] truncate" title={rule.app_name}>{rule.app_name}</td>
                    <td className="px-2 py-1.5 text-gray-500 max-w-[100px] truncate" title={rule.policy_name}>{rule.policy_name}</td>
                    <td className="px-2 py-1.5">
                      <span className={`px-1.5 py-0.5 rounded font-medium ${rule.rule_action === 'Accept' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {rule.rule_action}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 max-w-[150px]">
                      <div className="font-mono text-blue-800" title={rule.rule_source}>
                        {(rule.rule_source || '').split('\n').filter(Boolean).slice(0, 2).join(', ')}
                        {(rule.rule_source || '').split('\n').filter(Boolean).length > 2 && <span className="text-gray-400"> +{(rule.rule_source || '').split('\n').filter(Boolean).length - 2}</span>}
                      </div>
                    </td>
                    <td className="px-2 py-1.5 max-w-[250px]">
                      {rule.rule_source_expanded ? (
                        <div className="text-gray-700 truncate" title={rule.rule_source_expanded}>
                          {rule.rule_source_expanded.substring(0, 100)}{rule.rule_source_expanded.length > 100 ? '...' : ''}
                        </div>
                      ) : (
                        <span className="text-gray-300 italic">—</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-gray-500">{rule.rule_source_zone}</td>
                    <td className="px-2 py-1.5 max-w-[150px]">
                      <div className="font-mono text-purple-800" title={rule.rule_destination}>
                        {(rule.rule_destination || '').split('\n').filter(Boolean).slice(0, 2).join(', ')}
                        {(rule.rule_destination || '').split('\n').filter(Boolean).length > 2 && <span className="text-gray-400"> +{(rule.rule_destination || '').split('\n').filter(Boolean).length - 2}</span>}
                      </div>
                    </td>
                    <td className="px-2 py-1.5 max-w-[250px]">
                      {rule.rule_destination_expanded ? (
                        <div className="text-gray-700 truncate" title={rule.rule_destination_expanded}>
                          {rule.rule_destination_expanded.substring(0, 100)}{rule.rule_destination_expanded.length > 100 ? '...' : ''}
                        </div>
                      ) : (
                        <span className="text-gray-300 italic">—</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-gray-500">{rule.rule_destination_zone}</td>
                    <td className="px-2 py-1.5 font-mono text-gray-600 max-w-[100px] truncate" title={rule.rule_service}>{rule.rule_service}</td>
                    <td className="px-2 py-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        rule.migration_status === 'Completed' ? 'bg-green-100 text-green-700' :
                        rule.migration_status === 'In Progress' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>{rule.migration_status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {getFilteredImportedRules().length > 200 && (
              <div className="px-3 py-2 bg-amber-50 text-xs text-amber-700 text-center border-t">
                Showing first 200 of {getFilteredImportedRules().length} rules. Use filters to narrow down or export all as CSV.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Load Rules Button (if not auto-loaded) */}
      {!isNGDCMappings && !isNFRImport && !showImportedRules && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6 text-center">
          <button onClick={loadImportedRules} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            Load Imported Rules
          </button>
          <p className="text-xs text-gray-500 mt-2">View imported legacy rules with source and destination details</p>
        </div>
      )}

      {/* Imported Apps - NGDC Mapping Section (shown after import or on demand) */}
      {!isNGDCMappings && !isNFRImport && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">App NGDC Mappings (DC / NH / SZ)</h2>
              <p className="text-xs text-gray-500 mt-1">Map imported apps to NGDC Data Centers, Neighbourhoods, and Security Zones. Add components (WEB, APP, DB, etc.) per app.</p>
            </div>
            <div className="flex items-center gap-3">
              <select className="px-2 py-1.5 text-xs border rounded-md" value={appFilter} onChange={e => setAppFilter(e.target.value as 'all' | 'unmapped' | 'mapped')}>
                <option value="all">All Apps</option>
                <option value="unmapped">Unmapped Only</option>
                <option value="mapped">Mapped Only</option>
              </select>
              <button onClick={loadImportedApps} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
                {showAppMappings ? 'Refresh' : 'Load Apps'}
              </button>
            </div>
          </div>

          {showAppMappings && importedApps.length > 0 && (
            <div className="space-y-2">
              <div className="flex gap-4 text-xs text-gray-500 mb-2">
                <span>Total: <strong className="text-gray-700">{importedApps.length}</strong></span>
                <span>Mapped: <strong className="text-green-700">{importedApps.filter(a => a.has_mapping).length}</strong></span>
                <span>Unmapped: <strong className="text-amber-700">{importedApps.filter(a => !a.has_mapping).length}</strong></span>
              </div>
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">App ID</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">App Name</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Dist ID</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Rules</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Components</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {importedApps
                      .filter(a => appFilter === 'all' || (appFilter === 'unmapped' ? !a.has_mapping : a.has_mapping))
                      .map(app => (
                      <>
                        <tr key={app.app_id} className={`hover:bg-gray-50 ${expandedAppId === app.app_id ? 'bg-blue-50' : ''}`}>
                          <td className="px-3 py-2 font-mono text-xs font-medium">{app.app_id}</td>
                          <td className="px-3 py-2 text-xs">{app.app_name}</td>
                          <td className="px-3 py-2 font-mono text-xs text-gray-500">{app.app_distributed_id}</td>
                          <td className="px-3 py-2 text-xs">{app.rule_count}</td>
                          <td className="px-3 py-2">
                            {app.has_mapping ? (
                              <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">Mapped ({app.components.length})</span>
                            ) : (
                              <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700">Unmapped</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-500">
                            {app.components.length > 0
                              ? app.components.map(c => String(c.component || '')).join(', ')
                              : <span className="text-gray-400 italic">None</span>}
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-1">
                              <button
                                onClick={() => setExpandedAppId(expandedAppId === app.app_id ? null : app.app_id)}
                                className="px-2 py-0.5 text-xs text-blue-700 bg-blue-50 rounded hover:bg-blue-100"
                              >
                                {expandedAppId === app.app_id ? 'Collapse' : 'Edit'}
                              </button>
                              <button
                                onClick={() => { setAddingComponentForApp(app.app_id); setExpandedAppId(app.app_id); }}
                                className="px-2 py-0.5 text-xs text-indigo-700 bg-indigo-50 rounded hover:bg-indigo-100"
                              >
                                + Component
                              </button>
                            </div>
                          </td>
                        </tr>
                        {/* Expanded: show existing components + add form */}
                        {expandedAppId === app.app_id && (
                          <tr key={`${app.app_id}-detail`}>
                            <td colSpan={7} className="px-4 py-3 bg-blue-50/50">
                              {app.components.length > 0 && (
                                <div className="mb-3">
                                  <h4 className="text-xs font-semibold text-gray-600 mb-2">Existing Component Mappings</h4>
                                  <table className="w-full text-xs">
                                    <thead><tr className="text-gray-500">
                                      <th className="px-2 py-1 text-left">Component</th>
                                      <th className="px-2 py-1 text-left">DC</th>
                                      <th className="px-2 py-1 text-left">NH</th>
                                      <th className="px-2 py-1 text-left">SZ</th>
                                      <th className="px-2 py-1 text-left">CIDR</th>
                                      <th className="px-2 py-1 text-left">Status</th>
                                      <th className="px-2 py-1 text-left">Actions</th>
                                    </tr></thead>
                                    <tbody>
                                      {app.components.map((c, idx) => (
                                        <tr key={idx} className="border-t border-gray-200">
                                          <td className="px-2 py-1"><span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">{String(c.component || '')}</span></td>
                                          <td className="px-2 py-1 font-mono">{String(c.dc || '')}</td>
                                          <td className="px-2 py-1 font-mono">{String(c.nh || '')}</td>
                                          <td className="px-2 py-1 font-mono">{String(c.sz || '')}</td>
                                          <td className="px-2 py-1 font-mono">{String(c.cidr || '')}</td>
                                          <td className="px-2 py-1"><span className={`px-1.5 py-0.5 rounded-full ${c.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{String(c.status || 'Active')}</span></td>
                                          <td className="px-2 py-1">
                                            <button onClick={() => handleDeleteComponent(String(c.id || ''))} className="text-red-500 hover:text-red-700">Delete</button>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              )}
                              {/* Add Component Form */}
                              {addingComponentForApp === app.app_id && (
                                <div className="p-3 bg-white border border-blue-200 rounded-lg">
                                  <h4 className="text-xs font-semibold text-blue-700 mb-2">Add Component for {app.app_id} - {app.app_name}</h4>
                                  <div className="grid grid-cols-7 gap-2">
                                    <select className="px-2 py-1.5 text-xs border rounded" value={newComponentForm.component} onChange={e => setNewComponentForm(p => ({ ...p, component: e.target.value }))}>
                                      {['WEB','APP','DB','MQ','BAT','API'].map(c => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                    <select className="px-2 py-1.5 text-xs border rounded" value={newComponentForm.dc} onChange={e => setNewComponentForm(p => ({ ...p, dc: e.target.value }))}>
                                      <option value="ALPHA_NGDC">ALPHA_NGDC</option>
                                      <option value="BETA_NGDC">BETA_NGDC</option>
                                      <option value="GAMMA_NGDC">GAMMA_NGDC</option>
                                    </select>
                                    <input className="px-2 py-1.5 text-xs border rounded" placeholder="NH (e.g. NH02,NH14)" value={newComponentForm.nh} onChange={e => setNewComponentForm(p => ({ ...p, nh: e.target.value }))} />
                                    <input className="px-2 py-1.5 text-xs border rounded" placeholder="SZ (e.g. CCS,PAA)" value={newComponentForm.sz} onChange={e => setNewComponentForm(p => ({ ...p, sz: e.target.value }))} />
                                    <input className="px-2 py-1.5 text-xs border rounded font-mono" placeholder="CIDR" value={newComponentForm.cidr} onChange={e => setNewComponentForm(p => ({ ...p, cidr: e.target.value }))} />
                                    <input className="px-2 py-1.5 text-xs border rounded" placeholder="Notes" value={newComponentForm.notes} onChange={e => setNewComponentForm(p => ({ ...p, notes: e.target.value }))} />
                                    <div className="flex gap-1">
                                      <button onClick={() => setAddingComponentForApp(null)} className="px-2 py-1 text-xs text-gray-600 border rounded hover:bg-gray-100">Cancel</button>
                                      <button onClick={() => handleAddComponent(app.app_id)} disabled={savingComponent || !newComponentForm.nh || !newComponentForm.sz}
                                        className="px-2 py-1 text-xs text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50">
                                        {savingComponent ? '...' : 'Add'}
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              )}
                              {!addingComponentForApp && app.components.length === 0 && (
                                <p className="text-xs text-gray-400 italic">No component mappings yet. Click "+ Component" to add DC/NH/SZ mapping for this app.</p>
                              )}
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {showAppMappings && importedApps.length === 0 && (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">No imported apps found. Import legacy rules first to see apps here.</p>
            </div>
          )}
        </div>
      )}

      {/* NGDC Mappings Table */}
      {isNGDCMappings && (
        <>
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Add Manual Mapping</h2>
            </div>
            <div className="grid grid-cols-7 gap-3 mb-3">
              <input placeholder="Legacy Name" value={newMapping.legacy_name} onChange={e => setNewMapping(p => ({ ...p, legacy_name: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="Legacy DC" value={newMapping.legacy_dc} onChange={e => setNewMapping(p => ({ ...p, legacy_dc: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="NGDC Name" value={newMapping.ngdc_name} onChange={e => setNewMapping(p => ({ ...p, ngdc_name: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="NGDC DC" value={newMapping.ngdc_dc} onChange={e => setNewMapping(p => ({ ...p, ngdc_dc: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="NH" value={newMapping.ngdc_nh} onChange={e => setNewMapping(p => ({ ...p, ngdc_nh: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="SZ" value={newMapping.ngdc_sz} onChange={e => setNewMapping(p => ({ ...p, ngdc_sz: e.target.value }))} className="px-3 py-2 border rounded-lg text-sm" />
              <button onClick={handleAddMapping} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">Add</button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Organization NGDC Mappings</h2>
              <button onClick={loadMappings} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                {showMappings ? 'Refresh' : 'Load Mappings'}
              </button>
            </div>
            {showMappings && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left">
                      <th className="px-3 py-2 font-medium text-gray-600">Legacy Name</th>
                      <th className="px-3 py-2 font-medium text-gray-600">Legacy DC</th>
                      <th className="px-3 py-2 font-medium text-gray-600">NGDC Name</th>
                      <th className="px-3 py-2 font-medium text-gray-600">NGDC DC</th>
                      <th className="px-3 py-2 font-medium text-gray-600">NH</th>
                      <th className="px-3 py-2 font-medium text-gray-600">SZ</th>
                      <th className="px-3 py-2 font-medium text-gray-600">Type</th>
                      <th className="px-3 py-2 font-medium text-gray-600">Status</th>
                      <th className="px-3 py-2 font-medium text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mappings.map((m, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono text-xs">{String(m.legacy_name || '')}</td>
                        <td className="px-3 py-2">{String(m.legacy_dc || '')}</td>
                        <td className="px-3 py-2 font-mono text-xs text-blue-700">{String(m.ngdc_name || '')}</td>
                        <td className="px-3 py-2">{String(m.ngdc_dc || '')}</td>
                        <td className="px-3 py-2">{String(m.ngdc_nh || '')}</td>
                        <td className="px-3 py-2">{String(m.ngdc_sz || '')}</td>
                        <td className="px-3 py-2">
                          <span className="px-2 py-0.5 rounded-full bg-gray-100 text-xs">{String(m.type || '')}</span>
                        </td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs ${m.status === 'Verified' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            {String(m.status || 'Pending')}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <button onClick={() => handleDeleteMapping(String(m.id))} className="text-red-500 hover:text-red-700 text-xs">Delete</button>
                        </td>
                      </tr>
                    ))}
                    {mappings.length === 0 && (
                      <tr><td colSpan={9} className="px-3 py-8 text-center text-gray-400">No mappings loaded. Click "Load Mappings" or import from Excel.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
