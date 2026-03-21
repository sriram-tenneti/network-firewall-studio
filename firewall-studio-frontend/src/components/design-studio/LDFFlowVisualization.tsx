import { useState, useEffect } from 'react';
import { compileEgressIngress, getFirewallDevices } from '@/lib/api';

interface BoundaryDevice {
  device_id: string; device_name: string; nh: string; sz: string;
  role: string; direction: string; compiled: string;
}

export interface EgressIngressResult {
  rule_id: string; vendor_format: string; boundaries: number;
  flow_rule: string; note: string;
  requires_egress: boolean; requires_ingress: boolean;
  devices: BoundaryDevice[];
  egress_compiled: string; ingress_compiled: string;
  source_zone: string; destination_zone: string;
  source_nh: string; destination_nh: string;
}

interface FWDevice {
  device_id: string; name: string; vendor: string; dc: string;
  nh?: string; sz?: string; type: string; status: string;
  mgmt_ip?: string; ha_pair?: string; capabilities?: string[];
}

interface LDFFlowVisualizationProps {
  ruleId: string;
  vendor?: string;
  /** Pre-loaded boundary data (skip API call) */
  boundaryData?: EgressIngressResult | null;
  compact?: boolean;
}

const VENDOR_LABELS: Record<string, string> = {
  palo_alto: 'Palo Alto', checkpoint: 'Check Point', cisco_asa: 'Cisco ASA', generic: 'Generic',
};

const LDF_RULE_LABELS: Record<string, string> = {
  'LDF-001': 'GEN/STD zones across NHs - No firewall boundary',
  'LDF-002': 'Same NH, same SZ - No firewall boundary',
  'LDF-003': 'Segmented zone to different zone/NH - 1 boundary (egress)',
  'LDF-004': 'Same segmented zone, different NHs - 2 boundaries (egress+ingress)',
  'LDF-005': 'Same NH, different segmented zones - 1 boundary',
  'LDF-006': 'PAA flow (internet to internal) - 2 boundaries',
};

function determineLDFRule(data: EgressIngressResult): string {
  const { boundaries, source_zone, destination_zone, source_nh, destination_nh } = data;
  const segmented = new Set(['CPA', 'CDE', 'CCS', 'PAA', '3PY', 'Swift', 'PSE', 'UC', 'UCPA', 'UCDE', 'UCCS', 'UPAA', 'U3PY']);
  const srcSeg = segmented.has(source_zone);
  const dstSeg = segmented.has(destination_zone);

  if (boundaries === 0) {
    if (source_nh === destination_nh) return 'LDF-002';
    return 'LDF-001';
  }
  if (boundaries === 1) {
    if (source_nh === destination_nh) return 'LDF-005';
    return 'LDF-003';
  }
  // boundaries === 2
  if (source_zone === 'PAA' || destination_zone === 'PAA') return 'LDF-006';
  if (srcSeg && dstSeg && source_zone === destination_zone) return 'LDF-004';
  return 'LDF-006';
}

export function LDFFlowVisualization({ ruleId, vendor = 'generic', boundaryData, compact = false }: LDFFlowVisualizationProps) {
  const [data, setData] = useState<EgressIngressResult | null>(boundaryData ?? null);
  const [loading, setLoading] = useState(!boundaryData);
  const [allDevices, setAllDevices] = useState<FWDevice[]>([]);

  useEffect(() => {
    if (boundaryData) { setData(boundaryData); setLoading(false); return; }
    if (!ruleId) return;
    setLoading(true);
    compileEgressIngress(ruleId, vendor)
      .then(d => setData(d as unknown as EgressIngressResult))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [ruleId, vendor, boundaryData]);

  useEffect(() => {
    getFirewallDevices()
      .then(d => setAllDevices(d as unknown as FWDevice[]))
      .catch(() => setAllDevices([]));
  }, []);

  if (loading) {
    return (
      <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50 animate-pulse">
        <div className="h-4 w-48 bg-indigo-200 rounded mb-2" />
        <div className="h-20 bg-indigo-100 rounded" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
        <p className="text-xs text-gray-500 italic">Logical Data Flow analysis not available for this rule.</p>
      </div>
    );
  }

  const ldfRule = determineLDFRule(data);
  const ldfDescription = LDF_RULE_LABELS[ldfRule] || 'Unknown LDF rule';
  const egressDevices = data.devices.filter(d => d.direction === 'egress');
  const ingressDevices = data.devices.filter(d => d.direction === 'ingress');
  const boundaryDevices = data.devices.filter(d => d.direction === 'boundary');

  // Look up full device details from allDevices
  const enrichDevice = (dev: BoundaryDevice): BoundaryDevice & Partial<FWDevice> => {
    const full = allDevices.find(fd => fd.device_id === dev.device_id);
    return { ...dev, ...full };
  };

  const _boundaryColor = data.boundaries === 0 ? 'green' : data.boundaries === 1 ? 'amber' : 'red';
  void _boundaryColor;

  return (
    <div className={`border rounded-lg overflow-hidden ${data.boundaries === 0 ? 'border-green-200' : data.boundaries === 1 ? 'border-amber-200' : 'border-red-200'}`}>
      {/* Header */}
      <div className={`px-4 py-3 ${data.boundaries === 0 ? 'bg-green-50' : data.boundaries === 1 ? 'bg-amber-50' : 'bg-red-50'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className={`text-sm font-bold ${data.boundaries === 0 ? 'text-green-800' : data.boundaries === 1 ? 'text-amber-800' : 'text-red-800'}`}>
              Logical Data Flow
            </h3>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
              data.boundaries === 0 ? 'bg-green-200 text-green-800' :
              data.boundaries === 1 ? 'bg-amber-200 text-amber-800' :
              'bg-red-200 text-red-800'
            }`}>
              {data.boundaries} {data.boundaries === 1 ? 'Boundary' : 'Boundaries'}
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 text-xs font-mono font-bold">{ldfRule}</span>
        </div>
        <p className="text-xs mt-1 opacity-80">{ldfDescription}</p>
      </div>

      {/* Flow Diagram */}
      <div className="px-4 py-4 bg-white">
        <div className="flex items-center justify-center gap-0 overflow-x-auto">
          {/* Source Node */}
          <div className="flex-shrink-0 w-32 text-center">
            <div className="border-2 border-blue-400 bg-blue-50 rounded-lg p-2.5 shadow-sm">
              <div className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider mb-0.5">Source</div>
              <div className="text-sm font-bold text-blue-800">{data.source_nh}</div>
              <div className="text-xs text-blue-600">{data.source_zone}</div>
            </div>
          </div>

          {/* Flow Arrow */}
          <div className="flex-shrink-0 w-8 flex items-center justify-center">
            <svg width="32" height="20" viewBox="0 0 32 20"><path d="M0 10 H24 M24 4 L32 10 L24 16" fill="none" stroke="#94a3b8" strokeWidth="2" /></svg>
          </div>

          {data.boundaries === 0 ? (
            /* Direct connection - no firewall */
            <>
              <div className="flex-shrink-0 px-3 py-1.5 bg-green-100 border border-green-300 rounded-full">
                <span className="text-xs font-semibold text-green-700">Direct (No FW)</span>
              </div>
              <div className="flex-shrink-0 w-8 flex items-center justify-center">
                <svg width="32" height="20" viewBox="0 0 32 20"><path d="M0 10 H24 M24 4 L32 10 L24 16" fill="none" stroke="#94a3b8" strokeWidth="2" /></svg>
              </div>
            </>
          ) : (
            <>
              {/* Egress Firewall */}
              {(egressDevices.length > 0 || data.requires_egress) && (
                <>
                  <div className="flex-shrink-0 w-40 text-center">
                    <div className="border-2 border-orange-400 bg-orange-50 rounded-lg p-2.5 shadow-sm relative">
                      <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-orange-500 text-white text-[9px] font-bold rounded-full uppercase">Egress</div>
                      {egressDevices.length > 0 ? egressDevices.map((dev, i) => {
                        const enriched = enrichDevice(dev);
                        return (
                          <div key={i} className="mt-1.5">
                            <div className="text-xs font-bold text-orange-800">{enriched.name || dev.device_name}</div>
                            <div className="text-[10px] text-orange-600">{dev.device_id}</div>
                            {enriched.vendor && <div className="text-[10px] text-gray-500">{VENDOR_LABELS[enriched.vendor] || enriched.vendor}</div>}
                            <div className="text-[10px] text-gray-400">{dev.nh}/{dev.sz}</div>
                          </div>
                        );
                      }) : (
                        <div className="mt-1.5 text-xs text-orange-600 italic">Egress FW Required</div>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0 w-8 flex items-center justify-center">
                    <svg width="32" height="20" viewBox="0 0 32 20"><path d="M0 10 H24 M24 4 L32 10 L24 16" fill="none" stroke="#94a3b8" strokeWidth="2" /></svg>
                  </div>
                </>
              )}

              {/* Boundary Device (for single boundary scenarios without separate egress/ingress) */}
              {boundaryDevices.length > 0 && egressDevices.length === 0 && ingressDevices.length === 0 && (
                <>
                  <div className="flex-shrink-0 w-40 text-center">
                    <div className="border-2 border-purple-400 bg-purple-50 rounded-lg p-2.5 shadow-sm relative">
                      <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-purple-500 text-white text-[9px] font-bold rounded-full uppercase">Boundary</div>
                      {boundaryDevices.map((dev, i) => {
                        const enriched = enrichDevice(dev);
                        return (
                          <div key={i} className="mt-1.5">
                            <div className="text-xs font-bold text-purple-800">{enriched.name || dev.device_name}</div>
                            <div className="text-[10px] text-purple-600">{dev.device_id}</div>
                            {enriched.vendor && <div className="text-[10px] text-gray-500">{VENDOR_LABELS[enriched.vendor] || enriched.vendor}</div>}
                            <div className="text-[10px] text-gray-400">{dev.nh}/{dev.sz}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <div className="flex-shrink-0 w-8 flex items-center justify-center">
                    <svg width="32" height="20" viewBox="0 0 32 20"><path d="M0 10 H24 M24 4 L32 10 L24 16" fill="none" stroke="#94a3b8" strokeWidth="2" /></svg>
                  </div>
                </>
              )}

              {/* Ingress Firewall */}
              {(ingressDevices.length > 0 || data.requires_ingress) && (
                <>
                  <div className="flex-shrink-0 w-40 text-center">
                    <div className="border-2 border-cyan-400 bg-cyan-50 rounded-lg p-2.5 shadow-sm relative">
                      <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-cyan-500 text-white text-[9px] font-bold rounded-full uppercase">Ingress</div>
                      {ingressDevices.length > 0 ? ingressDevices.map((dev, i) => {
                        const enriched = enrichDevice(dev);
                        return (
                          <div key={i} className="mt-1.5">
                            <div className="text-xs font-bold text-cyan-800">{enriched.name || dev.device_name}</div>
                            <div className="text-[10px] text-cyan-600">{dev.device_id}</div>
                            {enriched.vendor && <div className="text-[10px] text-gray-500">{VENDOR_LABELS[enriched.vendor] || enriched.vendor}</div>}
                            <div className="text-[10px] text-gray-400">{dev.nh}/{dev.sz}</div>
                          </div>
                        );
                      }) : (
                        <div className="mt-1.5 text-xs text-cyan-600 italic">Ingress FW Required</div>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0 w-8 flex items-center justify-center">
                    <svg width="32" height="20" viewBox="0 0 32 20"><path d="M0 10 H24 M24 4 L32 10 L24 16" fill="none" stroke="#94a3b8" strokeWidth="2" /></svg>
                  </div>
                </>
              )}
            </>
          )}

          {/* Destination Node */}
          <div className="flex-shrink-0 w-32 text-center">
            <div className="border-2 border-purple-400 bg-purple-50 rounded-lg p-2.5 shadow-sm">
              <div className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider mb-0.5">Destination</div>
              <div className="text-sm font-bold text-purple-800">{data.destination_nh}</div>
              <div className="text-xs text-purple-600">{data.destination_zone}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Explanation & Note */}
      <div className={`px-4 py-2 text-xs border-t ${data.boundaries === 0 ? 'bg-green-50 border-green-200 text-green-700' : data.boundaries === 1 ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
        <span className="font-medium">Flow Rule:</span> {data.flow_rule}
        {data.note && <span className="ml-2 opacity-80">| {data.note}</span>}
      </div>

      {/* Device-Specific Compiled Rules (expandable) */}
      {!compact && data.devices.length > 0 && (
        <DeviceCompiledRules devices={data.devices} allDevices={allDevices} />
      )}
    </div>
  );
}

function DeviceCompiledRules({ devices, allDevices }: { devices: BoundaryDevice[]; allDevices: FWDevice[] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-gray-200">
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 transition-colors">
        <span className="text-xs font-semibold text-gray-600">Device-Specific Compiled Rules ({devices.length})</span>
        <span className="text-xs text-gray-400">{expanded ? '\u25B2 Collapse' : '\u25BC Expand'}</span>
      </button>
      {expanded && (
        <div className="p-3 space-y-2 bg-gray-50">
          {devices.map((dev, i) => {
            const full = allDevices.find(fd => fd.device_id === dev.device_id);
            return (
              <div key={i} className="bg-gray-900 rounded-lg p-3 overflow-x-auto">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      dev.direction === 'egress' ? 'bg-orange-500 text-white' :
                      dev.direction === 'ingress' ? 'bg-cyan-500 text-white' :
                      'bg-purple-500 text-white'
                    }`}>{dev.direction.toUpperCase()}</span>
                    <span className="text-xs text-gray-200 font-medium">{full?.name || dev.device_name}</span>
                    <span className="text-[10px] text-gray-500">({dev.device_id})</span>
                    {full?.vendor && <span className="text-[10px] text-gray-400 px-1.5 py-0.5 bg-gray-800 rounded">{VENDOR_LABELS[full.vendor] || full.vendor}</span>}
                  </div>
                  <button onClick={() => navigator.clipboard.writeText(dev.compiled)} className="text-xs text-blue-400 hover:text-blue-300">Copy</button>
                </div>
                <div className="flex items-center gap-3 text-[10px] text-gray-500 mb-1.5">
                  <span>NH: {dev.nh}</span>
                  <span>SZ: {dev.sz}</span>
                  <span>Role: {dev.role}</span>
                  {full?.dc && <span>DC: {full.dc}</span>}
                  {full?.mgmt_ip && <span>Mgmt: {full.mgmt_ip}</span>}
                  {full?.status && <span className={`px-1 py-0.5 rounded ${full.status === 'Active' ? 'bg-green-900 text-green-400' : 'bg-yellow-900 text-yellow-400'}`}>{full.status}</span>}
                </div>
                <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{dev.compiled}</pre>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
