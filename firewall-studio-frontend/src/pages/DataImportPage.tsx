import { useState } from 'react';
import { Notification } from '@/components/shared/Notification';
import { Modal } from '@/components/shared/Modal';
import { useNotification } from '@/hooks/useNotification';
import type { DataImportJob } from '@/types';

const IMPORT_TARGETS = [
  { value: 'legacy_rules', label: 'Legacy Rules', desc: 'Import existing legacy firewall rules for migration' },
  { value: 'firewall_rules', label: 'Firewall Rules', desc: 'Import standard firewall rules' },
  { value: 'groups', label: 'Groups', desc: 'Import firewall group definitions' },
];

const SOURCE_TYPES = [
  { value: 'csv', label: 'Spreadsheet (CSV/Excel)', icon: 'XLS', color: 'from-green-500 to-emerald-600' },
  { value: 'json', label: 'JSON File', icon: 'JSON', color: 'from-blue-500 to-indigo-600' },
  { value: 'mongodb', label: 'MongoDB Collection', icon: 'MDB', color: 'from-emerald-600 to-green-700' },
];

export default function DataImportPage() {
  const [jobs, setJobs] = useState<DataImportJob[]>([
    { id: 'imp-001', source_type: 'csv', source_name: 'legacy_rules_export.csv', status: 'completed', total_records: 245, imported_records: 240, failed_records: 5, target: 'legacy_rules', created_at: '2025-01-15T10:00:00Z', completed_at: '2025-01-15T10:05:00Z', error_message: null },
    { id: 'imp-002', source_type: 'json', source_name: 'ngdc_groups.json', status: 'completed', total_records: 50, imported_records: 50, failed_records: 0, target: 'groups', created_at: '2025-01-16T14:00:00Z', completed_at: '2025-01-16T14:01:00Z', error_message: null },
  ]);
  const [showImport, setShowImport] = useState(false);
  const [sourceType, setSourceType] = useState<string>('csv');
  const [target, setTarget] = useState<string>('legacy_rules');
  const [fileName, setFileName] = useState<string>('');
  const [mongoUri, setMongoUri] = useState('');
  const [mongoCollection, setMongoCollection] = useState('');
  const [previewData, setPreviewData] = useState<string[][]>([]);
  const { notification, showNotification, clearNotification } = useNotification();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setPreviewData([
        ['rule_001', 'APP01', '10.0.1.0/24', '10.0.2.0/24', '443', 'TCP', 'Allow'],
        ['rule_002', 'APP01', 'grp-APP01-NH01-STD-web', 'grp-APP01-NH01-STD-db', '3306', 'TCP', 'Allow'],
        ['rule_003', 'APP02', '172.16.0.0/16', '10.0.3.5', '8080', 'TCP', 'Allow'],
      ]);
    }
  };

  const startImport = () => {
    const newJob: DataImportJob = {
      id: `imp-${Date.now()}`,
      source_type: sourceType as DataImportJob['source_type'],
      source_name: sourceType === 'mongodb' ? `${mongoCollection}@mongo` : fileName,
      status: 'processing',
      total_records: 0,
      imported_records: 0,
      failed_records: 0,
      target: target as DataImportJob['target'],
      created_at: new Date().toISOString(),
      completed_at: null,
      error_message: null,
    };
    setJobs(prev => [newJob, ...prev]);
    setShowImport(false);
    showNotification('Import job started', 'success');

    setTimeout(() => {
      setJobs(prev => prev.map(j => j.id === newJob.id ? {
        ...j, status: 'completed' as const, total_records: 150, imported_records: 148, failed_records: 2, completed_at: new Date().toISOString()
      } : j));
      showNotification('Import completed: 148/150 records imported', 'success');
    }, 3000);
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    processing: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Import</h1>
          <p className="text-sm text-gray-500 mt-1">Import firewall rules from spreadsheets, JSON files, or MongoDB collections</p>
        </div>
        <button
          onClick={() => setShowImport(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg hover:from-indigo-700 hover:to-blue-700 shadow-sm"
        >
          + New Import
        </button>
      </div>

      {/* Source type cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {SOURCE_TYPES.map(src => (
          <div
            key={src.value}
            onClick={() => { setSourceType(src.value); setShowImport(true); }}
            className="p-5 bg-white border border-gray-200 rounded-xl hover:shadow-md cursor-pointer transition-shadow group"
          >
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${src.color} flex items-center justify-center text-white text-xs font-bold mb-3`}>
              {src.icon}
            </div>
            <h3 className="text-sm font-semibold text-gray-800 group-hover:text-indigo-700">{src.label}</h3>
            <p className="text-xs text-gray-500 mt-1">Click to import from {src.label.toLowerCase()}</p>
          </div>
        ))}
      </div>

      {/* Import history */}
      <h2 className="text-lg font-semibold text-gray-800 mb-3">Import History</h2>
      <div className="space-y-3">
        {jobs.map(job => (
          <div key={job.id} className="p-4 bg-white border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-600">
                  {SOURCE_TYPES.find(s => s.value === job.source_type)?.icon || 'F'}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">{job.source_name}</p>
                  <p className="text-xs text-gray-500">Target: {IMPORT_TARGETS.find(t => t.value === job.target)?.label || job.target} | {new Date(job.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {job.status === 'completed' && (
                  <span className="text-xs text-gray-600">{job.imported_records}/{job.total_records} records ({job.failed_records} failed)</span>
                )}
                {job.status === 'processing' && (
                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                )}
                <span className={`px-2 py-0.5 text-xs font-medium rounded capitalize ${statusColors[job.status]}`}>{job.status}</span>
              </div>
            </div>
          </div>
        ))}
        {jobs.length === 0 && <p className="text-sm text-gray-500 italic text-center py-8">No import jobs yet. Click &quot;New Import&quot; to get started.</p>}
      </div>

      {/* Import Modal */}
      <Modal isOpen={showImport} onClose={() => setShowImport(false)} title="Import Data" size="lg">
        <div className="space-y-5">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">Source Type</label>
            <div className="flex gap-2">
              {SOURCE_TYPES.map(src => (
                <button
                  key={src.value}
                  onClick={() => setSourceType(src.value)}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border rounded-lg transition-colors ${sourceType === src.value ? 'bg-indigo-50 border-indigo-300 text-indigo-700' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                >
                  <span className="text-xs font-bold">{src.icon}</span>
                  <span>{src.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">Import Target</label>
            <select
              value={target}
              onChange={e => setTarget(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
            >
              {IMPORT_TARGETS.map(t => (
                <option key={t.value} value={t.value}>{t.label} - {t.desc}</option>
              ))}
            </select>
          </div>

          {sourceType === 'mongodb' ? (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">MongoDB Connection URI</label>
                <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg" value={mongoUri} onChange={e => setMongoUri(e.target.value)} placeholder="mongodb://localhost:27017/firewall_db" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Collection Name</label>
                <input type="text" className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg" value={mongoCollection} onChange={e => setMongoCollection(e.target.value)} placeholder="legacy_rules" />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Upload File</label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
                <input type="file" accept={sourceType === 'csv' ? '.csv,.xlsx,.xls' : '.json'} onChange={handleFileSelect} className="hidden" id="file-upload" />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <p className="text-sm text-gray-600">{fileName || 'Click to upload or drag and drop'}</p>
                  <p className="text-xs text-gray-400 mt-1">{sourceType === 'csv' ? 'CSV, XLS, XLSX' : 'JSON'} files supported</p>
                </label>
              </div>
            </div>
          )}

          {previewData.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Preview (first 3 rows)</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="bg-gray-50">{['Rule ID', 'App', 'Source', 'Destination', 'Port', 'Protocol', 'Action'].map(h => <th key={h} className="px-2 py-1 text-left font-medium text-gray-600">{h}</th>)}</tr></thead>
                  <tbody>{previewData.map((row, i) => <tr key={i} className="border-t">{row.map((cell, j) => <td key={j} className="px-2 py-1 text-gray-700">{cell}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button onClick={() => setShowImport(false)} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button onClick={startImport} className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">Start Import</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
