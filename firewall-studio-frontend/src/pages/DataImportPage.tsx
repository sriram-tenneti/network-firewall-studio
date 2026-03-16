import { useState, useRef } from 'react';
import { Notification } from '@/components/shared/Notification';
import { useNotification } from '@/hooks/useNotification';
import { importLegacyRulesExcel } from '@/lib/api';

interface ImportJob {
  id: string;
  fileName: string;
  status: 'processing' | 'completed' | 'failed';
  added: number;
  duplicates: number;
  total: number;
  createdAt: string;
  error?: string;
}

export default function DataImportPage() {
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [importing, setImporting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { notification, showNotification, clearNotification } = useNotification();

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      showNotification('Only .xlsx files are supported', 'error');
      return;
    }

    const jobId = `imp-${Date.now()}`;
    const newJob: ImportJob = {
      id: jobId,
      fileName: file.name,
      status: 'processing',
      added: 0,
      duplicates: 0,
      total: 0,
      createdAt: new Date().toISOString(),
    };
    setJobs(prev => [newJob, ...prev]);
    setImporting(true);

    try {
      const result = await importLegacyRulesExcel(file);
      setJobs(prev => prev.map(j => j.id === jobId ? {
        ...j,
        status: 'completed' as const,
        added: result.added,
        duplicates: result.duplicates,
        total: result.total,
      } : j));
      showNotification(`Import complete: ${result.added} added, ${result.duplicates} duplicates skipped (${result.total} total)`, 'success');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Import failed';
      setJobs(prev => prev.map(j => j.id === jobId ? {
        ...j,
        status: 'failed' as const,
        error: errorMsg,
      } : j));
      showNotification(errorMsg, 'error');
    }
    setImporting(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const statusColors: Record<string, string> = {
    processing: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  const filteredJobs = jobs.filter(job => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return job.fileName.toLowerCase().includes(q) || job.status.toLowerCase().includes(q) || job.id.toLowerCase().includes(q);
  });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} onClose={clearNotification} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Import</h1>
          <p className="text-sm text-gray-500 mt-1">Import legacy firewall rules from Excel spreadsheets with automatic deduplication</p>
        </div>
      </div>

      {/* Import Card */}
      <div className="mb-8 p-6 bg-white border-2 border-dashed border-gray-300 rounded-xl hover:border-indigo-400 transition-colors">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-xl font-bold">
            XLS
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-1">Import Legacy Firewall Rules</h3>
          <p className="text-sm text-gray-500 mb-4">Upload an Excel (.xlsx) file with legacy rules. Duplicates will be automatically detected and skipped.</p>
          <p className="text-xs text-gray-400 mb-4">Expected columns: App ID, App Current Distributed ID, App Name, Inventory Item, Policy Name, Rule Global, Rule Action, Rule Source, Rule Source Expanded, Rule Source Zone, Rule Destination, Rule Destination Expanded, Rule Destination Zone, Rule Service, Rule Service Expanded, RN, RC</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
            id="excel-upload"
            disabled={importing}
          />
          <label htmlFor="excel-upload" className={`inline-block px-6 py-3 text-sm font-medium text-white rounded-lg shadow-sm cursor-pointer ${importing ? 'bg-gray-400' : 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700'}`}>
            {importing ? 'Importing...' : 'Choose Excel File'}
          </label>
        </div>
      </div>

      {/* Import History */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-800">Import History</h2>
      </div>
      {jobs.length > 0 && (
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by file name, status..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
          />
        </div>
      )}
      <div className="space-y-3">
        {filteredJobs.map(job => (
          <div key={job.id} className="p-4 bg-white border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-green-100 flex items-center justify-center text-xs font-bold text-green-700">
                  XLS
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">{job.fileName}</p>
                  <p className="text-xs text-gray-500">{new Date(job.createdAt).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {job.status === 'completed' && (
                  <span className="text-xs text-gray-600">{job.added} added, {job.duplicates} duplicates ({job.total} total)</span>
                )}
                {job.status === 'processing' && (
                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                )}
                {job.status === 'failed' && job.error && (
                  <span className="text-xs text-red-600">{job.error}</span>
                )}
                <span className={`px-2 py-0.5 text-xs font-medium rounded capitalize ${statusColors[job.status]}`}>{job.status}</span>
              </div>
            </div>
          </div>
        ))}
        {jobs.length === 0 && <p className="text-sm text-gray-500 italic text-center py-8">No import jobs yet. Upload an Excel file to get started.</p>}
      </div>
    </div>
  );
}
