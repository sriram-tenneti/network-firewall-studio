import { useState, useCallback } from 'react';
import { importLegacyRulesExcel, importNGDCMappingsExcel, getNGDCMappings, deleteNGDCMapping, createNGDCMapping } from '@/lib/api';

interface DataImportPageProps {
  context?: string;
}

export default function DataImportPage({ context }: DataImportPageProps) {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [mappings, setMappings] = useState<Record<string, unknown>[]>([]);
  const [showMappings, setShowMappings] = useState(false);
  const [newMapping, setNewMapping] = useState({ legacy_name: '', legacy_dc: '', ngdc_name: '', ngdc_dc: '', ngdc_nh: '', ngdc_sz: '', type: 'group' });

  const isNGDCMappings = context === 'ngdc-mappings';
  const pageTitle = isNGDCMappings ? 'NGDC Organization Mappings' :
    context === 'ngdc-standardization' ? 'Import Legacy Rules for Migration' :
    context === 'firewall-management' ? 'Import Firewall Rules' :
    context === 'firewall-studio' ? 'Import Rules for Firewall Studio' :
    'Data Import';

  const loadMappings = useCallback(async () => {
    try {
      const data = await getNGDCMappings();
      setMappings(data);
      setShowMappings(true);
    } catch { setError('Failed to load mappings'); }
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {isNGDCMappings
            ? 'Manage organization-provided legacy-to-NGDC name mappings used during migration'
            : 'Upload Excel (.xlsx) files to import rules into the system'}
        </p>
      </div>

      {/* Import Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
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
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
        )}
        {result && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            Import successful: {JSON.stringify(result)}
          </div>
        )}
      </div>

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
