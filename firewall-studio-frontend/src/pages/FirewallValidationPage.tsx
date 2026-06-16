import { useState } from 'react';

interface ValidationResult {
  validation_id: string;
  source: string;
  source_type: string;
  destination: string;
  destination_type: string;
  ports: string;
  environment: string;
  policy_verdict: string;
  live_verdict: string;
  drift_detected: boolean;
  overall_verdict: string;
  policy_detail: string;
  matching_rules: { rule_id: string; source: string; destination: string; ports: string; action: string; status: string }[];
  live_results: { method: string; status: string; detail: string; port?: number }[];
}

interface BulkResult {
  total: number;
  pass_count: number;
  fail_count: number;
  drift_count: number;
  results: ValidationResult[];
}

const PROBE_METHODS = [
  { id: 'tcp_socket', name: 'TCP Socket', description: 'SYN probe for TCP ports' },
  { id: 'icmp_ping', name: 'ICMP Ping', description: 'Host reachability' },
  { id: 'http_probe', name: 'HTTP(S) Probe', description: 'HEAD request for web services' },
  { id: 'dns_lookup', name: 'DNS Lookup', description: 'Hostname resolution' },
];

export default function FirewallValidationPage() {
  const [mode, setMode] = useState<'single' | 'bulk'>('single');
  const [envFilter, setEnvFilter] = useState('');

  // Single mode state
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [ports, setPorts] = useState('');
  const [sourceType, setSourceType] = useState<string>('');
  const [destType, setDestType] = useState<string>('');
  const [liveCheck, setLiveCheck] = useState(true);
  const [selectedMethods, setSelectedMethods] = useState<string[]>(['tcp_socket', 'icmp_ping']);
  const [singleResult, setSingleResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bulk mode state
  const [bulkInput, setBulkInput] = useState('');
  const [bulkResults, setBulkResults] = useState<BulkResult | null>(null);

  // Auto-detect entity type
  const detectType = (value: string): string => {
    if (!value) return '';
    if (value.startsWith('grp-') || value.startsWith('g-')) return 'group';
    if (value.startsWith('vm-') || value.startsWith('svr-')) return 'vm';
    if (/^\d+\.\d+\.\d+\.\d+$/.test(value)) return 'ip';
    if (/^\d+\.\d+\.\d+\.\d+\/\d+$/.test(value)) return 'cidr';
    if (value.includes('.') && !value.match(/^\d/)) return 'fqdn';
    return 'ip';
  };

  const handleSingleValidate = async () => {
    if (!source || !destination) {
      setError('Source and destination are required');
      return;
    }
    setLoading(true);
    setError(null);
    setSingleResult(null);
    try {
      const res = await fetch('/api/validation/single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source,
          destination,
          ports,
          source_type: sourceType || detectType(source),
          destination_type: destType || detectType(destination),
          environment: envFilter,
          live_check: liveCheck,
          probe_methods: selectedMethods,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSingleResult(data);
    } catch (e) {
      setError((e as Error).message);
    }
    setLoading(false);
  };

  const handleBulkValidate = async () => {
    if (!bulkInput.trim()) {
      setError('Enter at least one check (source,destination,ports per line)');
      return;
    }
    setLoading(true);
    setError(null);
    setBulkResults(null);
    try {
      const lines = bulkInput.trim().split('\n').filter(l => l.trim());
      const checks = lines.map(line => {
        const parts = line.split(',').map(s => s.trim());
        return { source: parts[0] || '', destination: parts[1] || '', ports: parts[2] || '' };
      });
      const res = await fetch('/api/validation/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          checks,
          environment: envFilter,
          live_check: liveCheck,
          probe_methods: selectedMethods,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setBulkResults(data);
    } catch (e) {
      setError((e as Error).message);
    }
    setLoading(false);
  };

  const handleExport = async () => {
    const results = mode === 'single' && singleResult ? [singleResult] : (bulkResults?.results || []);
    if (!results.length) return;
    try {
      const res = await fetch('/api/validation/export/xlsx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ results }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'validation_results.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(`Export failed: ${(e as Error).message}`);
    }
  };

  const verdictColor = (verdict: string) => {
    if (verdict === 'REACHABLE' || verdict === 'PERMIT') return 'text-green-700 bg-green-50';
    if (verdict === 'UNREACHABLE' || verdict === 'DENY' || verdict === 'NO_RULE') return 'text-red-700 bg-red-50';
    if (verdict === 'TIMEOUT') return 'text-amber-700 bg-amber-50';
    return 'text-gray-700 bg-gray-50';
  };

  const toggleMethod = (id: string) => {
    setSelectedMethods(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      {error && (
        <div className="mb-4 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">&times;</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Firewall Validation</h1>
          <p className="text-sm text-gray-500 mt-1">Verify pass-through connectivity between source and destination — policy check + live probe</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white"
            value={envFilter}
            onChange={e => setEnvFilter(e.target.value)}
          >
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
          <div className="flex items-center border border-gray-300 rounded-md overflow-hidden">
            <button onClick={() => setMode('single')} className={`px-3 py-2 text-sm font-medium ${mode === 'single' ? 'bg-teal-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Single</button>
            <button onClick={() => setMode('bulk')} className={`px-3 py-2 text-sm font-medium border-l border-gray-300 ${mode === 'bulk' ? 'bg-teal-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>Bulk</button>
          </div>
        </div>
      </div>

      {/* Probe methods configuration */}
      <div className="mb-4 bg-white border rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-600 uppercase">Probe Configuration</span>
          <label className="flex items-center gap-2 text-xs">
            <input type="checkbox" checked={liveCheck} onChange={e => setLiveCheck(e.target.checked)} className="rounded" />
            <span>Enable Live Probe</span>
          </label>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {PROBE_METHODS.map(m => (
            <label key={m.id} className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs cursor-pointer ${
              selectedMethods.includes(m.id) ? 'border-teal-300 bg-teal-50 text-teal-800' : 'border-gray-200 text-gray-500'
            }`}>
              <input type="checkbox" checked={selectedMethods.includes(m.id)} onChange={() => toggleMethod(m.id)} className="rounded text-teal-600" />
              {m.name}
            </label>
          ))}
        </div>
      </div>

      {/* Single mode */}
      {mode === 'single' && (
        <div className="bg-white border rounded-lg shadow-sm p-4">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source (IP / Group / VM / FQDN)</label>
              <input
                type="text"
                value={source}
                onChange={e => { setSource(e.target.value); setSourceType(detectType(e.target.value)); }}
                placeholder="e.g. grp-CRM-WEB-NH14-PAA or 10.1.2.3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              {sourceType && <span className="text-xs text-gray-400 mt-1 block">Detected: {sourceType}</span>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Destination (IP / Group / VM / FQDN)</label>
              <input
                type="text"
                value={destination}
                onChange={e => { setDestination(e.target.value); setDestType(detectType(e.target.value)); }}
                placeholder="e.g. grp-PAY-DB-NH02-GEN or db.internal.corp"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              {destType && <span className="text-xs text-gray-400 mt-1 block">Detected: {destType}</span>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ports (comma-separated)</label>
              <input
                type="text"
                value={ports}
                onChange={e => setPorts(e.target.value)}
                placeholder="e.g. 443,8080,3306"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSingleValidate}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 disabled:opacity-50"
            >
              {loading ? 'Validating...' : 'Validate'}
            </button>
            {singleResult && (
              <button onClick={handleExport} className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100">
                Export XLSX
              </button>
            )}
          </div>

          {/* Single Result */}
          {singleResult && (
            <div className="mt-4 border-t border-gray-100 pt-4">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className={`p-3 rounded-lg ${verdictColor(singleResult.policy_verdict)}`}>
                  <div className="text-xs font-medium">Policy Verdict</div>
                  <div className="text-lg font-bold">{singleResult.policy_verdict}</div>
                  <div className="text-xs mt-1">{singleResult.policy_detail}</div>
                </div>
                <div className={`p-3 rounded-lg ${verdictColor(singleResult.live_verdict)}`}>
                  <div className="text-xs font-medium">Live Verdict</div>
                  <div className="text-lg font-bold">{singleResult.live_verdict}</div>
                </div>
                <div className={`p-3 rounded-lg ${singleResult.drift_detected ? 'text-orange-700 bg-orange-50' : 'text-gray-700 bg-gray-50'}`}>
                  <div className="text-xs font-medium">Drift Detection</div>
                  <div className="text-lg font-bold">{singleResult.drift_detected ? 'DRIFT DETECTED' : 'No Drift'}</div>
                  <div className="text-xs mt-1">{singleResult.drift_detected ? 'Policy and live state do not match' : 'Policy matches actual connectivity'}</div>
                </div>
              </div>

              {/* Matching Rules */}
              {singleResult.matching_rules.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs font-semibold text-gray-600 mb-2">Matching Rules</div>
                  <table className="w-full text-xs border border-gray-200 rounded">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left px-2 py-1">Rule ID</th>
                        <th className="text-left px-2 py-1">Source</th>
                        <th className="text-left px-2 py-1">Destination</th>
                        <th className="text-left px-2 py-1">Ports</th>
                        <th className="text-left px-2 py-1">Action</th>
                        <th className="text-left px-2 py-1">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {singleResult.matching_rules.map((r, idx) => (
                        <tr key={idx} className="border-t border-gray-100">
                          <td className="px-2 py-1 font-mono">{r.rule_id}</td>
                          <td className="px-2 py-1 font-mono">{r.source}</td>
                          <td className="px-2 py-1 font-mono">{r.destination}</td>
                          <td className="px-2 py-1">{r.ports}</td>
                          <td className="px-2 py-1">{r.action}</td>
                          <td className="px-2 py-1">{r.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Live probe results */}
              {singleResult.live_results.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-600 mb-2">Live Probe Results</div>
                  <div className="space-y-1">
                    {singleResult.live_results.map((lr, idx) => (
                      <div key={idx} className={`flex items-center gap-2 px-2 py-1 rounded text-xs ${
                        lr.status === 'REACHABLE' ? 'bg-green-50' : lr.status === 'UNREACHABLE' ? 'bg-red-50' : 'bg-amber-50'
                      }`}>
                        <span className={`w-2 h-2 rounded-full ${
                          lr.status === 'REACHABLE' ? 'bg-green-500' : lr.status === 'UNREACHABLE' ? 'bg-red-500' : 'bg-amber-500'
                        }`} />
                        <span className="font-medium">{lr.method}</span>
                        {lr.port && <span className="text-gray-500">:{lr.port}</span>}
                        <span className="text-gray-600">{lr.detail}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Bulk mode */}
      {mode === 'bulk' && (
        <div className="bg-white border rounded-lg shadow-sm p-4">
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Bulk Checks (one per line: source,destination,ports)
            </label>
            <textarea
              value={bulkInput}
              onChange={e => setBulkInput(e.target.value)}
              placeholder={`grp-CRM-WEB-NH14-PAA,grp-PAY-DB-NH02-GEN,443\n10.1.2.3,10.2.3.4,22,80\nvm-webserver,db.internal.corp,3306`}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleBulkValidate}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 disabled:opacity-50"
            >
              {loading ? 'Validating...' : `Validate ${bulkInput.trim().split('\n').filter(l => l.trim()).length} Checks`}
            </button>
            {bulkResults && (
              <button onClick={handleExport} className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100">
                Export XLSX
              </button>
            )}
          </div>

          {/* Bulk Results */}
          {bulkResults && (
            <div className="mt-4 border-t border-gray-100 pt-4">
              <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="p-3 rounded-lg bg-gray-50">
                  <div className="text-xs text-gray-500">Total</div>
                  <div className="text-xl font-bold">{bulkResults.total}</div>
                </div>
                <div className="p-3 rounded-lg bg-green-50">
                  <div className="text-xs text-green-600">Pass</div>
                  <div className="text-xl font-bold text-green-700">{bulkResults.pass_count}</div>
                </div>
                <div className="p-3 rounded-lg bg-red-50">
                  <div className="text-xs text-red-600">Fail</div>
                  <div className="text-xl font-bold text-red-700">{bulkResults.fail_count}</div>
                </div>
                <div className="p-3 rounded-lg bg-orange-50">
                  <div className="text-xs text-orange-600">Drift</div>
                  <div className="text-xl font-bold text-orange-700">{bulkResults.drift_count}</div>
                </div>
              </div>
              <div className="space-y-1">
                {bulkResults.results.map((r, idx) => (
                  <div key={idx} className={`flex items-center gap-3 px-3 py-2 rounded text-xs ${
                    r.overall_verdict === 'REACHABLE' || r.overall_verdict === 'PERMIT' ? 'bg-green-50' :
                    r.overall_verdict === 'UNREACHABLE' || r.overall_verdict === 'DENY' || r.overall_verdict === 'NO_RULE' ? 'bg-red-50' :
                    'bg-amber-50'
                  }`}>
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      r.overall_verdict === 'REACHABLE' || r.overall_verdict === 'PERMIT' ? 'bg-green-500' :
                      r.overall_verdict === 'UNREACHABLE' || r.overall_verdict === 'DENY' || r.overall_verdict === 'NO_RULE' ? 'bg-red-500' :
                      'bg-amber-500'
                    }`} />
                    <span className="font-mono flex-1">{r.source} → {r.destination}:{r.ports}</span>
                    <span className="font-medium">{r.overall_verdict}</span>
                    <span className="text-gray-400">{r.policy_verdict} / {r.live_verdict}</span>
                    {r.drift_detected && <span className="text-orange-600 font-semibold">DRIFT</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
