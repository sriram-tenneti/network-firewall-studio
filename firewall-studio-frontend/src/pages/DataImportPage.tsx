import { useState, useCallback, useEffect } from 'react';
import { importLegacyRulesExcel, getLegacyRules, importRulesToNGDC } from '@/lib/api';
import type { LegacyRule } from '@/types';

interface DataImportPageProps {
  context?: string;
}

export default function DataImportPage({ context }: DataImportPageProps) {
  const [file, setFile] = useState<File | null>(null);
  const [selectedEnv, setSelectedEnv] = useState<string>('Production');
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  // FM import state (for ngdc-import-rules context)
  const [fmRules, setFmRules] = useState<LegacyRule[]>([]);
  const [fmApps, setFmApps] = useState<{ value: string; label: string; ruleCount: number }[]>([]);
  const [selectedImportApps, setSelectedImportApps] = useState<Set<string>>(new Set());
  const [importingFromFM, setImportingFromFM] = useState(false);
  const [fmLoading, setFmLoading] = useState(false);
  const [importResult, setImportResult] = useState<{ imported: number; apps: number } | null>(null);
  const [envTab, setEnvTab] = useState<string>('Production');

  const isNGDCImport = context === 'ngdc-import-rules';
  const pageTitle = isNGDCImport
    ? 'Import Rules from Firewall Management'
    : context === 'firewall-management'
    ? 'Import Firewall Rules'
    : 'Data Import';

  // Load FM apps when this is the NGDC import page
  const loadFMApps = useCallback(async () => {
    setFmLoading(true);
    try {
      const rules = await getLegacyRules(undefined, false, envTab);
      setFmRules(rules);
      const appMap = new Map<string, { label: string; count: number }>();
      for (const r of rules) {
        const key = String(r.app_id);
        if (!appMap.has(key)) {
          appMap.set(key, { label: `${r.app_id} - ${r.app_name} (${r.app_distributed_id})`, count: 0 });
        }
        appMap.get(key)!.count++;
      }
      setFmApps(
        Array.from(appMap.entries())
          .map(([value, { label, count }]) => ({ value, label, ruleCount: count }))
          .sort((a, b) => a.label.localeCompare(b.label))
      );
    } catch { setFmApps([]); }
    setFmLoading(false);
  }, [envTab]);

  useEffect(() => {
    if (isNGDCImport) loadFMApps();
  }, [isNGDCImport, loadFMApps]);

  const toggleImportApp = (appId: string) => {
    setSelectedImportApps(prev => {
      const next = new Set(prev);
      if (next.has(appId)) next.delete(appId); else next.add(appId);
      return next;
    });
  };

  const selectAllImportApps = () => {
    if (selectedImportApps.size === fmApps.length) setSelectedImportApps(new Set());
    else setSelectedImportApps(new Set(fmApps.map(a => a.value)));
  };

  const handleImportFromFM = async () => {
    if (selectedImportApps.size === 0) return;
    setImportingFromFM(true);
    setError('');
    setImportResult(null);
    try {
      const res = await importRulesToNGDC(Array.from(selectedImportApps), envTab);
      setImportResult({ imported: res.imported, apps: selectedImportApps.size });
      setSelectedImportApps(new Set());
      loadFMApps();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import rules from Firewall Management');
    }
    setImportingFromFM(false);
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setError('');
    setResult(null);
    try {
      const res = await importLegacyRulesExcel(file);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const selectedRuleCount = fmRules.filter(r => selectedImportApps.has(String(r.app_id))).length;

  return (
    <div className="max-w-[1800px] mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isNGDCImport
              ? 'Select applications from Firewall Management to import their rules for NGDC migration'
              : 'Upload Excel (.xlsx) files to import rules into the system'}
          </p>
        </div>
        {!isNGDCImport && (
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedEnv} onChange={e => setSelectedEnv(e.target.value)}>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
        )}
      </div>

      {/* FM Import Section - Import from Firewall Management */}
      {isNGDCImport && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 mb-5">
            <p className="text-sm text-emerald-700">Select one or more applications to import their current Firewall Management rules for NGDC migration. These rules will be available for one-to-one DC mapping in Migration Studio.</p>
          </div>

          <div className="flex gap-1 mb-5 bg-gray-100 rounded-lg p-1 w-fit">
            {(['Production', 'Non-Production', 'Pre-Production'] as const).map(env => (
              <button key={env} onClick={() => { setEnvTab(env); setSelectedImportApps(new Set()); }}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${envTab === env ? 'bg-white shadow-sm text-emerald-700 border border-emerald-200' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}>
                {env}
              </button>
            ))}
          </div>

          {fmLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Loading applications from Firewall Management...</p>
            </div>
          ) : fmApps.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500">No applications found in Firewall Management for {envTab}.</p>
              <button onClick={loadFMApps} className="mt-3 px-4 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md hover:bg-emerald-100">
                Retry
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">{fmApps.length} Applications &middot; {fmRules.length} Rules ({envTab})</span>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
                    <input type="checkbox" checked={selectedImportApps.size === fmApps.length && fmApps.length > 0} onChange={selectAllImportApps} className="rounded border-gray-300 text-emerald-600" />
                    Select All
                  </label>
                  <button onClick={loadFMApps} className="text-xs text-emerald-600 hover:text-emerald-800">Refresh</button>
                </div>
              </div>
              <div className="max-h-96 overflow-y-auto border rounded-lg divide-y divide-gray-100">
                {fmApps.map(app => (
                  <label key={app.value} className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-emerald-50 transition-colors ${selectedImportApps.has(app.value) ? 'bg-emerald-50' : ''}`}>
                    <input type="checkbox" checked={selectedImportApps.has(app.value)} onChange={() => toggleImportApp(app.value)} className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                    <span className="text-sm text-gray-800 font-medium">{app.label}</span>
                    <span className="text-xs text-gray-400 ml-auto">{app.ruleCount} rule{app.ruleCount !== 1 ? 's' : ''}</span>
                  </label>
                ))}
              </div>

              {selectedImportApps.size > 0 && (
                <div className="mt-4 bg-gray-50 rounded-lg p-4 flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    <strong>{selectedImportApps.size}</strong> app(s) selected &middot; <strong>{selectedRuleCount}</strong> rules will be imported for NGDC migration
                  </span>
                  <button onClick={handleImportFromFM} disabled={importingFromFM}
                    className="px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 shadow-sm transition-colors">
                    {importingFromFM ? 'Importing...' : `Import ${selectedImportApps.size} App(s) to NGDC`}
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

      {/* Excel Import Section (for non-NGDC contexts) */}
      {!isNGDCImport && <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Import from Excel</h2>
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

    </div>
  );
}
