import { useState, useEffect, useMemo } from 'react';
import type { Application, BirthrightValidation } from '@/types';
import * as api from '@/lib/api';

interface DragDropRuleBuilderProps {
  applications: Application[];
  onRuleCreated: () => void;
}

const NEIGHBOURHOODS = [
  { id: 'NH01', name: 'Technology Enablement Services' },
  { id: 'NH02', name: 'Core Banking' },
  { id: 'NH03', name: 'Digital Channels' },
  { id: 'NH04', name: 'Wealth Management' },
  { id: 'NH05', name: 'Enterprise Services' },
  { id: 'NH06', name: 'Wholesale Banking' },
  { id: 'NH07', name: 'Global Payments and Liquidity' },
  { id: 'NH08', name: 'Data and Analytics' },
  { id: 'NH09', name: 'Assisted Channels' },
  { id: 'NH10', name: 'Consumer Lending' },
  { id: 'NH11', name: 'Production Mainframe' },
  { id: 'NH12', name: 'Non-Production Mainframe' },
  { id: 'NH13', name: 'Non-Production Shared' },
  { id: 'NH14', name: 'DMZ' },
  { id: 'NH15', name: 'Non-Production DMZ' },
  { id: 'NH16', name: 'Pre-Production (Non-Prod Shared)' },
  { id: 'NH17', name: 'Pre-Production DMZ' },
];

const PROD_ZONES = [
  { code: 'STD', name: 'Standard' },
  { code: 'GEN', name: 'General' },
  { code: 'PAA', name: 'PAA Zone' },
  { code: 'CDE', name: 'Cardholder Data Environment' },
  { code: 'CPA', name: 'Critical Payment Application' },
  { code: 'CCS', name: 'Common Card Services' },
  { code: '3PY', name: 'Third Party' },
  { code: 'Swift', name: 'Swift' },
  { code: 'PSE', name: 'Payment Security Environment' },
  { code: 'UC', name: 'Unified Communications' },
];

const NONPROD_ZONES = [
  { code: 'UGEN', name: 'UAT General' },
  { code: 'USTD', name: 'UAT Standard' },
  { code: 'UCCS', name: 'UAT Common Card Services' },
  { code: 'UPAA', name: 'UAT PAA' },
  { code: 'UCPA', name: 'UAT Critical Payment' },
  { code: 'UCDE', name: 'UAT Cardholder Data Env' },
  { code: 'U3PY', name: 'UAT Third Party' },
];

const DATACENTERS = [
  { code: 'ALPHA_NGDC', name: 'Alpha NGDC' },
  { code: 'BETA_NGDC', name: 'Beta NGDC' },
  { code: 'GAMMA_NGDC', name: 'Gamma NGDC' },
];

const SUBTYPES = [
  { code: 'APP', name: 'Application Servers' },
  { code: 'WEB', name: 'Web Servers' },
  { code: 'DB', name: 'Database Servers' },
  { code: 'BAT', name: 'Batch Servers' },
  { code: 'MQ', name: 'Message Queue' },
  { code: 'API', name: 'API Servers' },
  { code: 'LB', name: 'Load Balancers' },
  { code: 'MON', name: 'Monitoring' },
  { code: 'MFR', name: 'Mainframe' },
  { code: 'SVC', name: 'Services' },
];

const PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'ANY'];

const COMMON_PORTS = [
  { value: '443', label: 'HTTPS (443)' },
  { value: '80', label: 'HTTP (80)' },
  { value: '8443', label: 'Alt HTTPS (8443)' },
  { value: '8080', label: 'Alt HTTP (8080)' },
  { value: '1433', label: 'MSSQL (1433)' },
  { value: '1521', label: 'Oracle (1521)' },
  { value: '3306', label: 'MySQL (3306)' },
  { value: '5432', label: 'PostgreSQL (5432)' },
  { value: '1414', label: 'MQ (1414)' },
  { value: '9092', label: 'Kafka (9092)' },
  { value: '22', label: 'SSH (22)' },
  { value: '3389', label: 'RDP (3389)' },
];

export function DragDropRuleBuilder({ applications, onRuleCreated }: DragDropRuleBuilderProps) {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    application: '', environment: 'Production', datacenter: 'ALPHA_NGDC',
    src_nh: '', src_sz: '', src_subtype: 'APP', src_custom: '',
    dst_nh: '', dst_sz: '', dst_subtype: 'APP', dst_custom: '',
    port: '443', customPort: '', protocol: 'TCP', action: 'Allow', description: '',
  });
  const [birthrightResult, setBirthrightResult] = useState<BirthrightValidation | null>(null);
  const [validatingBR, setValidatingBR] = useState(false);

  const zones = useMemo(() => form.environment === 'Production' ? PROD_ZONES : NONPROD_ZONES, [form.environment]);

  const srcName = useMemo(() => {
    if (!form.application || !form.src_nh || !form.src_sz) return '';
    return `grp-${form.application}-${form.src_nh}-${form.src_sz}-${form.src_subtype}`;
  }, [form.application, form.src_nh, form.src_sz, form.src_subtype]);

  const dstName = useMemo(() => {
    if (!form.application || !form.dst_nh || !form.dst_sz) return '';
    return `grp-${form.application}-${form.dst_nh}-${form.dst_sz}-${form.dst_subtype}`;
  }, [form.application, form.dst_nh, form.dst_sz, form.dst_subtype]);

  const effectivePort = form.port === 'custom' ? form.customPort : form.port;

  useEffect(() => {
    if (!form.src_sz || !form.dst_sz) { setBirthrightResult(null); return; }
    const timer = setTimeout(async () => {
      setValidatingBR(true);
      try {
        const result = await api.validateBirthright({
          source_zone: form.src_sz, destination_zone: form.dst_sz,
          source_sz: form.src_sz, destination_sz: form.dst_sz,
          source_nh: form.src_nh, destination_nh: form.dst_nh,
          source_dc: form.datacenter, destination_dc: form.datacenter,
          environment: form.environment,
        });
        setBirthrightResult(result);
      } catch { setBirthrightResult(null); }
      setValidatingBR(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [form.src_sz, form.dst_sz, form.src_nh, form.dst_nh, form.datacenter, form.environment]);

  const canStep1 = form.application && form.environment && form.datacenter;
  const canStep2 = form.src_nh && form.src_sz && form.dst_nh && form.dst_sz;
  const canStep3 = effectivePort && form.protocol;
  const canSubmit = canStep1 && canStep2 && canStep3;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      await api.createRule({
        application: form.application, environment: form.environment, datacenter: form.datacenter,
        source: form.src_custom || srcName, source_zone: form.src_sz,
        destination: form.dst_custom || dstName, destination_zone: form.dst_sz,
        port: effectivePort, protocol: form.protocol, action: form.action,
        description: form.description, is_group_to_group: true,
      });
      onRuleCreated();
      setStep(1);
      setForm({ application: '', environment: 'Production', datacenter: 'ALPHA_NGDC',
        src_nh: '', src_sz: '', src_subtype: 'APP', src_custom: '',
        dst_nh: '', dst_sz: '', dst_subtype: 'APP', dst_custom: '',
        port: '443', customPort: '', protocol: 'TCP', action: 'Allow', description: '' });
      setBirthrightResult(null);
    } catch { /* handled by parent */ }
    setSubmitting(false);
  };

  const upd = (field: string, value: string) => setForm(prev => ({ ...prev, [field]: value }));
  const sel = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors';
  const lbl = 'block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5';

  const stepClass = (s: number) => {
    if (step === s) return 'border-blue-600 text-blue-700 bg-white';
    if (step > s) return 'border-green-500 text-green-700 bg-green-50/50';
    return 'border-transparent text-gray-500 hover:text-gray-700';
  };
  const dotClass = (s: number) => {
    if (step === s) return 'bg-blue-600 text-white';
    if (step > s) return 'bg-green-500 text-white';
    return 'bg-gray-300 text-white';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      {/* Step indicators */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {[{ num: 1, label: 'Application & Environment' }, { num: 2, label: 'Source & Destination' }, { num: 3, label: 'Connection & Review' }].map(s => (
          <button key={s.num} onClick={() => setStep(s.num)}
            className={'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ' + stepClass(s.num)}>
            <span className={'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ' + dotClass(s.num)}>
              {step > s.num ? '\u2713' : s.num}
            </span>
            <span className="hidden sm:inline">{s.label}</span>
          </button>
        ))}
      </div>

      <div className="p-6">
        {/* Step 1: Application & Environment */}
        {step === 1 && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-5">
              <div>
                <label className={lbl}>Application</label>
                <select className={sel} value={form.application} onChange={e => upd('application', e.target.value)}>
                  <option value="">Select Application...</option>
                  {applications.map(app => (
                    <option key={app.app_id} value={app.app_id}>{app.app_id} - {app.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={lbl}>Environment</label>
                <select className={sel} value={form.environment} onChange={e => { upd('environment', e.target.value); upd('src_sz', ''); upd('dst_sz', ''); }}>
                  <option value="Production">Production</option>
                  <option value="Non-Production">Non-Production</option>
                  <option value="Pre-Production">Pre-Production</option>
                </select>
              </div>
              <div>
                <label className={lbl}>Datacenter</label>
                <select className={sel} value={form.datacenter} onChange={e => upd('datacenter', e.target.value)}>
                  {DATACENTERS.map(dc => (
                    <option key={dc.code} value={dc.code}>{dc.name}</option>
                  ))}
                </select>
              </div>
            </div>
            {form.application && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-sm text-blue-800 font-medium">
                  Building rule for <strong>{form.application}</strong> in <strong>{form.environment}</strong> at <strong>{DATACENTERS.find(d => d.code === form.datacenter)?.name}</strong>
                </span>
              </div>
            )}
            <div className="flex justify-end">
              <button onClick={() => setStep(2)} disabled={!canStep1}
                className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
                Next: Source &amp; Destination &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Source & Destination */}
        {step === 2 && (
          <div className="space-y-5">
            <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-start">
              {/* Source panel */}
              <div className="border border-blue-200 rounded-xl p-4 bg-blue-50/30">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs font-bold">SRC</span>
                  <h3 className="text-sm font-bold text-blue-800">Source</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className={lbl}>Neighbourhood</label>
                    <select className={sel} value={form.src_nh} onChange={e => upd('src_nh', e.target.value)}>
                      <option value="">Select Neighbourhood...</option>
                      {NEIGHBOURHOODS.map(nh => (<option key={nh.id} value={nh.id}>{nh.id} - {nh.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Security Zone</label>
                    <select className={sel} value={form.src_sz} onChange={e => upd('src_sz', e.target.value)}>
                      <option value="">Select Zone...</option>
                      {zones.map(z => (<option key={z.code} value={z.code}>{z.code} - {z.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Subtype</label>
                    <select className={sel} value={form.src_subtype} onChange={e => upd('src_subtype', e.target.value)}>
                      {SUBTYPES.map(s => (<option key={s.code} value={s.code}>{s.code} - {s.name}</option>))}
                    </select>
                  </div>
                  {srcName && (
                    <div className="p-2 bg-white border border-blue-200 rounded-lg">
                      <div className="text-[10px] font-semibold text-gray-500 uppercase mb-0.5">Generated Name</div>
                      <code className="text-xs font-mono text-blue-700 break-all">{srcName}</code>
                    </div>
                  )}
                  <div>
                    <label className="text-[10px] text-gray-500">Or override with custom name:</label>
                    <input className={sel + ' mt-1'} placeholder="e.g. grp-APP01-NH01-GEN-APP" value={form.src_custom} onChange={e => upd('src_custom', e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Arrow connector */}
              <div className="flex flex-col items-center justify-center pt-12 gap-2">
                <div className="w-px h-8 bg-gray-300" />
                <div className="w-10 h-10 rounded-full bg-amber-100 border-2 border-amber-400 flex items-center justify-center">
                  <span className="text-amber-700 text-lg font-bold">&rarr;</span>
                </div>
                <div className="text-[10px] text-gray-400 font-semibold uppercase">Policy</div>
                {validatingBR && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600" />}
                {birthrightResult && !validatingBR && (
                  <span className={'px-2 py-0.5 rounded-full text-[10px] font-bold ' + (birthrightResult.compliant ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700')}>
                    {birthrightResult.compliant ? 'PERMITTED' : 'BLOCKED'}
                  </span>
                )}
                <div className="w-px h-8 bg-gray-300" />
              </div>

              {/* Destination panel */}
              <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/30">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">DST</span>
                  <h3 className="text-sm font-bold text-emerald-800">Destination</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className={lbl}>Neighbourhood</label>
                    <select className={sel} value={form.dst_nh} onChange={e => upd('dst_nh', e.target.value)}>
                      <option value="">Select Neighbourhood...</option>
                      {NEIGHBOURHOODS.map(nh => (<option key={nh.id} value={nh.id}>{nh.id} - {nh.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Security Zone</label>
                    <select className={sel} value={form.dst_sz} onChange={e => upd('dst_sz', e.target.value)}>
                      <option value="">Select Zone...</option>
                      {zones.map(z => (<option key={z.code} value={z.code}>{z.code} - {z.name}</option>))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Subtype</label>
                    <select className={sel} value={form.dst_subtype} onChange={e => upd('dst_subtype', e.target.value)}>
                      {SUBTYPES.map(s => (<option key={s.code} value={s.code}>{s.code} - {s.name}</option>))}
                    </select>
                  </div>
                  {dstName && (
                    <div className="p-2 bg-white border border-emerald-200 rounded-lg">
                      <div className="text-[10px] font-semibold text-gray-500 uppercase mb-0.5">Generated Name</div>
                      <code className="text-xs font-mono text-emerald-700 break-all">{dstName}</code>
                    </div>
                  )}
                  <div>
                    <label className="text-[10px] text-gray-500">Or override with custom name:</label>
                    <input className={sel + ' mt-1'} placeholder="e.g. grp-APP01-NH02-CCS-DB" value={form.dst_custom} onChange={e => upd('dst_custom', e.target.value)} />
                  </div>
                </div>
              </div>
            </div>

            {birthrightResult && !validatingBR && (
              <div className="space-y-2">
                {/* Policy Status */}
                <div className={'p-3 rounded-lg border text-sm ' + (
                  birthrightResult.firewall_request_required ? 'bg-amber-50 border-amber-200' :
                  birthrightResult.compliant ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                )}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={'font-bold text-xs ' + (
                      birthrightResult.firewall_request_required ? 'text-amber-700' :
                      birthrightResult.compliant ? 'text-green-700' : 'text-red-700'
                    )}>
                      Policy: {birthrightResult.matrix_used || ''}
                    </span>
                    <span className={'text-xs ' + (
                      birthrightResult.firewall_request_required ? 'text-amber-600' :
                      birthrightResult.compliant ? 'text-green-600' : 'text-red-600'
                    )}>
                      {birthrightResult.firewall_request_required
                        ? 'Firewall rule required for this cross-zone traffic'
                        : birthrightResult.compliant ? 'Permitted' : 'Blocked by policy'}
                    </span>
                  </div>
                  {birthrightResult.permitted.length > 0 && (
                    <ul className="text-xs text-green-700 list-disc list-inside mt-1">
                      {birthrightResult.permitted.map((p, i) => (<li key={i}>{p.rule} &mdash; {p.reason}</li>))}
                    </ul>
                  )}
                  {birthrightResult.warnings.length > 0 && (
                    <ul className="text-xs text-amber-700 list-disc list-inside mt-1">
                      {birthrightResult.warnings.map((w, i) => (<li key={i}>{w.rule} &mdash; {w.reason}</li>))}
                    </ul>
                  )}
                </div>

                {/* Firewall Device Hops — rule required */}
                {birthrightResult.firewall_devices_needed && birthrightResult.firewall_devices_needed.length > 0 && (
                  <div className="p-3 rounded-lg border border-amber-300 bg-amber-50 text-sm">
                    <div className="font-bold text-xs text-amber-800 mb-1">Firewall Rule Required — {birthrightResult.firewall_devices_needed.length} device{birthrightResult.firewall_devices_needed.length > 1 ? 's' : ''}</div>
                    <div className="flex flex-wrap gap-2">
                      {birthrightResult.firewall_devices_needed.map((dev, i) => (
                        <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white border border-amber-300 text-xs font-mono text-amber-800">
                          {dev}
                        </span>
                      ))}
                    </div>
                    <div className="text-[10px] text-amber-600 mt-1">
                      DC: {DATACENTERS.find(d => d.code === form.datacenter)?.name || form.datacenter}
                    </div>
                  </div>
                )}

                {/* Informational FW path — same SZ cross NH (permitted, no rule required) */}
                {birthrightResult.firewall_path_info && birthrightResult.firewall_path_info.length > 0 && !birthrightResult.firewall_request_required && (
                  <div className="p-3 rounded-lg border border-blue-200 bg-blue-50/50 text-sm">
                    <div className="font-bold text-xs text-blue-700 mb-1">Traffic Path (informational — no firewall rule required)</div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-1 rounded bg-blue-100 border border-blue-200 text-xs font-mono text-blue-800">{form.src_nh} {form.src_sz}</span>
                      {birthrightResult.firewall_path_info.map((fw, i) => (
                        <span key={i} className="inline-flex items-center gap-1">
                          <span className="text-gray-400">&rarr;</span>
                          <span className="px-2 py-1 rounded bg-white border border-blue-200 text-xs font-mono text-blue-700">{fw}</span>
                        </span>
                      ))}
                      <span className="text-gray-400">&rarr;</span>
                      <span className="px-2 py-1 rounded bg-purple-100 border border-purple-200 text-xs font-mono text-purple-800">{form.dst_nh} {form.dst_sz}</span>
                    </div>
                    <div className="text-[10px] text-blue-500 mt-1">
                      DC: {DATACENTERS.find(d => d.code === form.datacenter)?.name || form.datacenter} — Permitted per birthright
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-between">
              <button onClick={() => setStep(1)} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                &larr; Back
              </button>
              <button onClick={() => setStep(3)} disabled={!canStep2}
                className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
                Next: Connection Details &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Connection & Review */}
        {step === 3 && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-5">
              <div>
                <label className={lbl}>Port</label>
                <select className={sel} value={form.port} onChange={e => upd('port', e.target.value)}>
                  {COMMON_PORTS.map(p => (<option key={p.value} value={p.value}>{p.label}</option>))}
                  <option value="custom">Custom Port...</option>
                </select>
                {form.port === 'custom' && (
                  <input className={sel + ' mt-2'} placeholder="e.g. 8443, 9090-9095" value={form.customPort} onChange={e => upd('customPort', e.target.value)} />
                )}
              </div>
              <div>
                <label className={lbl}>Protocol</label>
                <select className={sel} value={form.protocol} onChange={e => upd('protocol', e.target.value)}>
                  {PROTOCOLS.map(p => (<option key={p} value={p}>{p}</option>))}
                </select>
              </div>
              <div>
                <label className={lbl}>Action</label>
                <select className={sel} value={form.action} onChange={e => upd('action', e.target.value)}>
                  <option value="Allow">Allow</option>
                  <option value="Deny">Deny</option>
                </select>
              </div>
            </div>

            <div>
              <label className={lbl}>Description (optional)</label>
              <textarea className={sel + ' h-16 resize-none'} placeholder="Brief description of this rule..." value={form.description} onChange={e => upd('description', e.target.value)} />
            </div>

            {/* Review summary */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Rule Summary</h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Application:</span>
                  <span className="font-medium text-gray-900">{form.application || '\u2014'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Environment:</span>
                  <span className="font-medium text-gray-900">{form.environment}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Datacenter:</span>
                  <span className="font-medium text-gray-900">{DATACENTERS.find(d => d.code === form.datacenter)?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Protocol/Port:</span>
                  <span className="font-medium text-gray-900">{form.protocol}/{effectivePort}</span>
                </div>
                <div className="col-span-2 border-t border-gray-200 pt-2 mt-1">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="text-[10px] text-gray-500 font-semibold uppercase">Source</div>
                      <code className="text-xs font-mono text-blue-700">{form.src_custom || srcName || '\u2014'}</code>
                      <div className="text-[10px] text-gray-400">{form.src_nh} / {form.src_sz}</div>
                    </div>
                    <span className="text-gray-400 text-lg font-bold">&rarr;</span>
                    <div className="flex-1 text-right">
                      <div className="text-[10px] text-gray-500 font-semibold uppercase">Destination</div>
                      <code className="text-xs font-mono text-emerald-700">{form.dst_custom || dstName || '\u2014'}</code>
                      <div className="text-[10px] text-gray-400">{form.dst_nh} / {form.dst_sz}</div>
                    </div>
                  </div>
                </div>
                {birthrightResult && (
                  <div className="col-span-2 mt-1 space-y-1">
                    <span className={'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ' + (
                      birthrightResult.firewall_request_required ? 'bg-amber-100 text-amber-700' :
                      birthrightResult.compliant ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    )}>
                      {birthrightResult.firewall_request_required
                        ? 'Firewall Rule Required'
                        : birthrightResult.compliant ? 'Policy: Permitted' : 'Policy: Blocked'}
                    </span>
                    {birthrightResult.firewall_devices_needed && birthrightResult.firewall_devices_needed.length > 0 && (
                      <div className="text-[10px] text-blue-700 font-mono">
                        {birthrightResult.firewall_devices_needed.join(' → ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between">
              <button onClick={() => setStep(2)} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                &larr; Back
              </button>
              <button onClick={handleSubmit} disabled={!canSubmit || submitting}
                className="px-6 py-2.5 text-sm font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm">
                {submitting ? 'Creating...' : 'Create Firewall Rule'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
