import { useCallback, useEffect, useMemo, useState } from 'react';
import SharedServicesSidebar from './SharedServicesSidebar';
import PortPicker from './PortPicker';
import type {
  Application,
  AppPresence,
  DestinationEntityKind,
  Environment,
  PhysicalRuleExpansion,
  RuleExpansionPreview,
  RuleRequestRecord,
  SharedService,
  SharedServicePresence,
} from '@/types';
import * as api from '@/lib/api';

interface RuleRequestBuilderProps {
  applications: Application[];
  onSubmitted?: (requestId?: string) => void;
}

const ENVIRONMENTS: Environment[] = ['Production', 'Non-Production', 'Pre-Production'];
const ACTIONS: ('ACCEPT' | 'DROP')[] = ['ACCEPT', 'DROP'];

interface DestRef {
  kind: DestinationEntityKind;
  ref: string;
  label: string;
  hint?: string;
}

export default function RuleRequestBuilder({ applications, onSubmitted }: RuleRequestBuilderProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [environment, setEnvironment] = useState<Environment>('Production');
  const [srcApp, setSrcApp] = useState<string>('');
  const [dest, setDest] = useState<DestRef | null>(null);
  const [ports, setPorts] = useState('TCP 443');
  const [action, setAction] = useState<'ACCEPT' | 'DROP'>('ACCEPT');
  const [description, setDescription] = useState('');
  const [includeCrossDc, setIncludeCrossDc] = useState(false);

  const [services, setServices] = useState<SharedService[]>([]);
  const [ssPresences, setSsPresences] = useState<Record<string, SharedServicePresence[]>>({});
  const [appPresences, setAppPresences] = useState<AppPresence[]>([]);
  const [preview, setPreview] = useState<RuleExpansionPreview | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedRecord, setSubmittedRecord] = useState<RuleRequestRecord | null>(null);

  const loadRefs = useCallback(async () => {
    try {
      const [svcs, aps] = await Promise.all([
        api.getSharedServices(),
        api.getAppPresences(),
      ]);
      setServices(svcs);
      setAppPresences(aps);
      const entries = await Promise.all(
        svcs.map(async (s) => [s.service_id, await api.getSharedServicePresences(s.service_id)] as const),
      );
      const m: Record<string, SharedServicePresence[]> = {};
      for (const [k, v] of entries) m[k] = v;
      setSsPresences(m);
    } catch {
      /* handled inline */
    }
  }, []);

  useEffect(() => { void loadRefs(); }, [loadRefs]);

  // Apps that have at least one ingress-enabled presence → eligible as destination
  const appsWithIngress = useMemo(() => {
    const ids = new Set(
      appPresences
        .filter((p) => p.has_ingress && p.environment === environment)
        .map((p) => p.app_distributed_id),
    );
    return applications.filter((a) => a.app_distributed_id && ids.has(a.app_distributed_id));
  }, [appPresences, applications, environment]);

  const unifiedDestinations: DestRef[] = useMemo(() => {
    const svc = services
      .filter((s) => (s.environments || []).includes(environment))
      .map<DestRef>((s) => ({
        kind: 'shared_service',
        ref: s.service_id,
        label: `${s.icon ?? '🧩'} ${s.name}`,
        hint: `${s.category} · Shared Service`,
      }));
    const apps = appsWithIngress.map<DestRef>((a) => ({
      kind: 'app_ingress',
      ref: a.app_distributed_id || a.app_id,
      label: `🏢 ${a.app_distributed_id || a.app_id} — ${a.app_name ?? ''}`,
      hint: 'Application (Ingress)',
    }));
    return [...svc, ...apps];
  }, [services, appsWithIngress, environment]);

  const srcOptions = useMemo(() => applications.filter((a) => a.app_distributed_id), [applications]);

  // Preview fan-out when inputs change
  useEffect(() => {
    setPreview(null);
    if (!srcApp || !dest?.ref) return;
    let cancelled = false;
    void (async () => {
      try {
        const p = await api.previewRuleExpansion({
          application_ref: srcApp,
          destination_kind: dest.kind,
          destination_ref: dest.ref,
          environment,
          ports,
          action,
          include_cross_dc: includeCrossDc,
        });
        if (!cancelled) setPreview(p);
      } catch (e) {
        if (!cancelled) setPreview({ physical_rules: [], warnings: [`Preview failed: ${(e as Error).message}`] });
      }
    })();
    return () => { cancelled = true; };
  }, [srcApp, dest, environment, ports, action, includeCrossDc]);

  const onDropDestination = (e: React.DragEvent) => {
    e.preventDefault();
    const sid = e.dataTransfer.getData('application/x-shared-service');
    if (!sid) return;
    const s = services.find((x) => x.service_id === sid);
    if (s) setDest({
      kind: 'shared_service',
      ref: s.service_id,
      label: `${s.icon ?? '🧩'} ${s.name}`,
      hint: `${s.category} · Shared Service`,
    });
  };

  const submit = async () => {
    if (!srcApp || !dest?.ref) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const r = await api.createRuleRequest({
        application_ref: srcApp,
        destination_kind: dest.kind,
        destination_ref: dest.ref,
        environment,
        ports,
        action,
        description,
        include_cross_dc: includeCrossDc,
      });
      setSubmittedRecord(r);
      onSubmitted?.(r.request_id);
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setStep(1); setSrcApp(''); setDest(null); setPorts('TCP 443');
    setAction('ACCEPT'); setDescription(''); setIncludeCrossDc(false);
    setPreview(null); setSubmittedRecord(null); setSubmitError(null);
  };

  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-12 lg:col-span-3">
        <SharedServicesSidebar
          services={services}
          presences={ssPresences}
          environment={environment}
          selectedServiceId={dest?.kind === 'shared_service' ? dest.ref : null}
          onSelect={(s) => setDest({
            kind: 'shared_service',
            ref: s.service_id,
            label: `${s.icon ?? '🧩'} ${s.name}`,
            hint: `${s.category} · Shared Service`,
          })}
        />
      </div>

      <div className="col-span-12 lg:col-span-9 space-y-4">
        {/* Stepper */}
        <div className="flex items-center gap-2 text-sm">
          {[
            { n: 1, label: 'Source & Destination' },
            { n: 2, label: 'Ports & Action' },
            { n: 3, label: 'Fan-out Preview' },
          ].map((s, idx) => (
            <div key={s.n} className="flex items-center gap-2">
              <button
                onClick={() => setStep(s.n as 1 | 2 | 3)}
                className={`w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center ${step === s.n ? 'bg-indigo-600 text-white' : step > s.n ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'}`}>
                {s.n}
              </button>
              <span className={`text-xs ${step === s.n ? 'text-indigo-700 font-semibold' : 'text-gray-600'}`}>{s.label}</span>
              {idx < 2 && <span className="text-gray-300">›</span>}
            </div>
          ))}
        </div>

        {step === 1 && (
          <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Environment</label>
                <select value={environment} onChange={(e) => setEnvironment(e.target.value as Environment)}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  {ENVIRONMENTS.map((e) => <option key={e} value={e}>{e}</option>)}
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Source Application</label>
                <select value={srcApp} onChange={(e) => setSrcApp(e.target.value)}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  <option value="">— select source app —</option>
                  {srcOptions.map((a) => (
                    <option key={a.app_distributed_id || a.app_id} value={a.app_distributed_id || a.app_id}>
                      {a.app_distributed_id || a.app_id} — {a.app_name ?? ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Destination (Apps with Ingress ∪ Shared Services)</label>
              <select value={dest?.ref ?? ''}
                onChange={(e) => {
                  const d = unifiedDestinations.find((x) => x.ref === e.target.value);
                  setDest(d ?? null);
                }}
                className="w-full border rounded px-2 py-1.5 text-sm">
                <option value="">— select destination —</option>
                <optgroup label="Shared Services">
                  {unifiedDestinations.filter((d) => d.kind === 'shared_service')
                    .map((d) => <option key={`ss-${d.ref}`} value={d.ref}>{d.label}</option>)}
                </optgroup>
                <optgroup label="Applications (with Ingress)">
                  {unifiedDestinations.filter((d) => d.kind === 'app_ingress')
                    .map((d) => <option key={`ai-${d.ref}`} value={d.ref}>{d.label}</option>)}
                </optgroup>
              </select>

              {/* DnD drop zone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={onDropDestination}
                className={`mt-2 border-2 border-dashed rounded-xl p-4 text-center transition ${dest ? 'border-indigo-300 bg-indigo-50' : 'border-gray-300 bg-gray-50 hover:bg-indigo-50/60'}`}>
                {dest ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider text-gray-500">Destination</div>
                    <div className="text-lg font-semibold text-gray-900">{dest.label}</div>
                    {dest.hint && <div className="text-xs text-gray-500 mt-0.5">{dest.hint}</div>}
                    <div className="mt-2">
                      <button onClick={() => setDest(null)}
                        className="text-xs text-rose-600 hover:text-rose-800">Clear</button>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-gray-500">
                    Drag a <span className="font-semibold text-indigo-600">Shared Service</span> from the sidebar,
                    or pick one above.
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end">
              <button disabled={!srcApp || !dest} onClick={() => setStep(2)}
                className="px-4 py-1.5 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-gray-300">
                Next: Ports & Action
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Ports</label>
                <PortPicker value={ports} onChange={setPorts} placeholder="Search/pick ports (HTTPS, Oracle, Mongo, Kafka, …)" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Action</label>
                <select value={action} onChange={(e) => setAction(e.target.value as 'ACCEPT' | 'DROP')}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  {ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="Business justification / ticket / context" />
            </div>
            <label className="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" checked={includeCrossDc} onChange={(e) => setIncludeCrossDc(e.target.checked)} />
              Also fan-out cross-DC pairs (when same-DC pairings do not exist)
            </label>
            <div className="flex justify-between">
              <button onClick={() => setStep(1)} className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50">Back</button>
              <button onClick={() => setStep(3)}
                className="px-4 py-1.5 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700">
                Next: Preview fan-out
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-gray-900">Multi-DC Fan-out Preview</div>
                <div className="text-xs text-gray-500">
                  {srcApp} → {dest?.label} · {environment} · {ports}
                </div>
              </div>
              <button onClick={() => void (async () => {
                const p = await api.previewRuleExpansion({
                  application_ref: srcApp,
                  destination_kind: dest!.kind,
                  destination_ref: dest!.ref,
                  environment, ports, action,
                  include_cross_dc: includeCrossDc,
                });
                setPreview(p);
              })()}
                className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50">
                Recompute
              </button>
            </div>

            {preview?.warnings?.length ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
                <div className="font-semibold mb-1">Warnings</div>
                <ul className="list-disc pl-5 space-y-0.5">
                  {preview.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            ) : null}

            <FanOutTable rows={preview?.physical_rules || []} />

            {submittedRecord ? (
              <div className="rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 via-white to-teal-50 p-4 text-sm shadow-md">
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-emerald-600 text-white text-sm font-bold">✓</span>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-emerald-900">Rule Request submitted — now in <span className="text-amber-700">Pending Review</span></div>
                    <div className="text-[11px] text-emerald-700">Scroll down to the <strong>Rule Requests</strong> panel to Approve / Reject / Deploy / Certify.</div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                  <div className="bg-white border border-emerald-200 rounded-lg p-2">
                    <div className="text-[10px] uppercase font-bold text-emerald-700 mb-0.5">Rule Request ID</div>
                    <code className="font-mono text-sm text-emerald-900 font-bold">{submittedRecord.request_id}</code>
                  </div>
                  <div className="bg-white border border-indigo-200 rounded-lg p-2">
                    <div className="text-[10px] uppercase font-bold text-indigo-700 mb-0.5">Fan-out</div>
                    <div className="text-sm text-indigo-900 font-bold">{submittedRecord.expansion?.length ?? 0} PhysicalRule(s) across {new Set((submittedRecord.expansion||[]).map(p => p.src_dc)).size} DC(s)</div>
                  </div>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="px-2 py-1 bg-slate-50 text-[10px] uppercase font-bold text-gray-700 border-b border-gray-200">Generated Physical Rule IDs (per DC)</div>
                  <div className="max-h-40 overflow-y-auto">
                    {(submittedRecord.expansion || []).map((p, i) => (
                      <div key={i} className="px-2 py-1 flex items-center gap-2 text-[11px] border-b border-gray-50">
                        <code className="font-mono text-indigo-700 font-bold">{p.rule_id ?? `${submittedRecord.request_id}-P${String(i+1).padStart(2,'0')}`}</code>
                        <span className="px-1.5 py-0.5 rounded-full border bg-orange-50 text-orange-700 border-orange-200 text-[9px] font-semibold">{p.src_dc}{p.cross_dc ? ` → ${p.dst_dc}` : ''}</span>
                        <span className="font-mono text-[10px] text-sky-700">{p.src_group_ref}</span>
                        <span className="text-gray-300">→</span>
                        <span className="font-mono text-[10px] text-rose-700">{p.dst_group_ref}</span>
                        <span className="ml-auto px-1.5 py-0.5 rounded border bg-white text-gray-600 border-gray-200 text-[9px] font-mono">{p.ports}</span>
                        <span className="px-1.5 py-0.5 rounded border bg-amber-50 text-amber-700 border-amber-200 text-[9px]">{p.lifecycle_status || 'Pending Review'}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-3 flex gap-2">
                  <button onClick={reset} className="text-xs px-3 py-1.5 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800">
                    Submit another
                  </button>
                  <button
                    onClick={() => {
                      const el = document.getElementById('rule-requests-panel');
                      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }}
                    className="text-xs px-3 py-1.5 rounded-lg border border-emerald-300 bg-white text-emerald-800 hover:bg-emerald-50"
                  >
                    Jump to Review queue ↓
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-500">
                  {preview ? `${preview.physical_rules.length} physical rule(s) will be generated.` : 'Computing…'}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setStep(2)} className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50">Back</button>
                  <button onClick={() => void submit()}
                    disabled={submitting || !preview || preview.physical_rules.length === 0}
                    className="px-4 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-gray-300">
                    {submitting ? 'Submitting…' : 'Submit Rule Request'}
                  </button>
                </div>
              </div>
            )}
            {submitError && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">{submitError}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function FanOutTable({ rows }: { rows: PhysicalRuleExpansion[] }) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-xs text-gray-500">
        No physical rules — source and destination have no matching DC/environment presences.
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden">
      <table className="min-w-full text-xs">
        <thead className="bg-gray-50 text-gray-600">
          <tr>
            <th className="px-2 py-1.5 text-left">Src DC</th>
            <th className="px-2 py-1.5 text-left">→</th>
            <th className="px-2 py-1.5 text-left">Dst DC</th>
            <th className="px-2 py-1.5 text-left">Src Group</th>
            <th className="px-2 py-1.5 text-left">Dst Group</th>
            <th className="px-2 py-1.5 text-left">Ports</th>
            <th className="px-2 py-1.5 text-left">Action</th>
            <th className="px-2 py-1.5 text-left">Flags</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
              <td className="px-2 py-1.5 font-mono">{r.src_dc}</td>
              <td className="px-2 py-1.5 text-gray-400">→</td>
              <td className="px-2 py-1.5 font-mono">{r.dst_dc}</td>
              <td className="px-2 py-1.5 font-mono text-indigo-700">{r.src_group_ref}</td>
              <td className="px-2 py-1.5 font-mono text-indigo-700">{r.dst_group_ref}</td>
              <td className="px-2 py-1.5 font-mono">{r.ports}</td>
              <td className="px-2 py-1.5">
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${r.action === 'ACCEPT' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                  {r.action}
                </span>
              </td>
              <td className="px-2 py-1.5">
                {r.cross_dc && <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-50 text-amber-700 border border-amber-200">cross-DC</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
