import { useMemo, useState } from 'react';
import * as api from '@/lib/api';
import type { LegacyTransition, LegacyClassifiedSide } from '@/lib/api';

/**
 * Migration Standardizer Panel
 *
 * Two views over the same legacy-rule input:
 *
 *   1. **Transition view (default).** For every imported legacy rule we
 *      classify the source/destination atoms (IP / CIDR / group / FQDN)
 *      against App Management + group registry, then propose the canonical
 *      NGDC equivalent: target groups, VRF (`<NH>-<SZ>`), DC, plus the App
 *      Management presence updates and group change requests needed to
 *      land the rule cleanly. SNS sees the diff side-by-side.
 *
 *   2. **Standardizer view (legacy).** The original normalize+dedup output
 *      with verdict per rule. Useful when you only care about catching
 *      duplicates rather than the full from->to transition.
 */
interface Decision {
  origin_legacy_rule_id: string;
  verdict: string;
  block: boolean;
  physical_rule: Record<string, unknown> | null;
  dedup_match: Record<string, unknown> | null;
  warnings: string[];
}

const VERDICT_STYLE: Record<string, string> = {
  new: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  merge: 'bg-amber-50 text-amber-800 border-amber-200',
  identical: 'bg-rose-50 text-rose-700 border-rose-200',
  subset: 'bg-rose-50 text-rose-700 border-rose-200',
  conflict: 'bg-rose-50 text-rose-700 border-rose-200',
  overlap: 'bg-amber-50 text-amber-800 border-amber-200',
  unclassifiable: 'bg-gray-100 text-gray-700 border-gray-200',
};

type ViewMode = 'transition' | 'standardize';

export default function StandardizerPanel() {
  const [text, setText] = useState<string>(
    'LEG-001, 10.10.0.0/22, g-ORACLE-NH02-CCS, TCP 1521-1530, ALLOW, Production',
  );
  const [running, setRunning] = useState(false);
  const [view, setView] = useState<ViewMode>('transition');
  const [transitionResult, setTransitionResult] = useState<{
    counters: { total: number; new: number; merge: number; conflict: number; overlap: number; unclassifiable: number; needs_app_attachment: number };
    transitions: LegacyTransition[];
  } | null>(null);
  const [normalizeResult, setNormalizeResult] = useState<{
    counters: { total: number; standardized: number; merged_existing: number; overlap_flagged: number; unclassifiable: number };
    decisions: Decision[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parsed = useMemo(() => {
    const rules: Array<Record<string, string>> = [];
    for (const raw of text.split('\n')) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const parts = line.split(',').map((s) => s.trim());
      if (parts.length < 5) continue;
      const [legacy_id, source, destination, ports, action, environment] = parts;
      // Split "TCP 1521-1530" into protocol + ports
      const portsParts = ports.split(/\s+/);
      const protocol = portsParts[0] || 'TCP';
      const portValue = portsParts.slice(1).join(' ') || ports;
      rules.push({
        rule_id: legacy_id,
        source,
        destination,
        protocol,
        port: portValue,
        ports,
        action,
        environment: environment || 'Production',
      });
    }
    return rules;
  }, [text]);

  const run = async () => {
    setRunning(true);
    setError(null);
    setTransitionResult(null);
    setNormalizeResult(null);
    try {
      if (view === 'transition') {
        const r = await api.buildLegacyTransitionsBulk(parsed);
        setTransitionResult(r);
      } else {
        const r = await api.normalizeLegacyRulesBulk(parsed);
        setNormalizeResult(r);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-3 border border-purple-200 bg-purple-50/40 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-purple-900">Migration Studio — Legacy → NGDC</h3>
          <p className="text-xs text-gray-700 max-w-3xl">
            For each imported legacy rule the engine parses the atoms (IP / CIDR / group / FQDN), classifies them
            against App Management and the group registry, and proposes the canonical NGDC equivalent: target groups,
            VRF (<code>&lt;NH&gt;-&lt;SZ&gt;</code>), DC, plus the App Management presence updates and group change
            requests needed to land the rule cleanly.
            <br />
            <span className="text-purple-800">
              Multi-DC and cross-DC (Heritage ↔ NGDC) flows are deferred — they keep their original shape until the
              cross-DC strategy is finalised.
            </span>
          </p>
        </div>
        <div className="flex flex-col gap-2 items-end">
          <div className="flex rounded-md border border-purple-300 bg-white overflow-hidden text-[11px]">
            <button
              onClick={() => setView('transition')}
              className={`px-2.5 py-1 ${view === 'transition' ? 'bg-purple-600 text-white' : 'text-purple-700 hover:bg-purple-50'}`}
            >Transition view</button>
            <button
              onClick={() => setView('standardize')}
              className={`px-2.5 py-1 border-l border-purple-300 ${view === 'standardize' ? 'bg-purple-600 text-white' : 'text-purple-700 hover:bg-purple-50'}`}
            >Standardizer (dedup only)</button>
          </div>
          <button onClick={() => void run()} disabled={running || parsed.length === 0}
            className="text-xs px-3 py-1.5 rounded bg-purple-600 text-white hover:bg-purple-700 disabled:bg-gray-300 whitespace-nowrap">
            {running ? 'Running…' : view === 'transition' ? `Compute ${parsed.length} transition${parsed.length === 1 ? '' : 's'}` : `Standardize ${parsed.length}`}
          </button>
        </div>
      </div>

      <div>
        <label className="text-[11px] text-gray-600">
          Legacy rules (one per line — <code>legacy_id, source, destination, ports, action, environment</code>)
        </label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
          className="w-full border rounded px-2 py-1 font-mono text-[11px]" />
      </div>

      {error && <div className="rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">{error}</div>}

      {view === 'transition' && transitionResult && (
        <TransitionResults result={transitionResult} />
      )}
      {view === 'standardize' && normalizeResult && (
        <NormalizeResults result={normalizeResult} />
      )}
    </div>
  );
}

// ============================================================
// Transition view (default)
// ============================================================

function TransitionResults({ result }: { result: { counters: { total: number; new: number; merge: number; conflict: number; overlap: number; unclassifiable: number; needs_app_attachment: number }; transitions: LegacyTransition[] } }) {
  const c = result.counters;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[11px] flex-wrap">
        <Pill label={`Total: ${c.total}`} />
        <Pill label={`New NGDC: ${c.new}`} tone="emerald" />
        <Pill label={`Merge w/ existing: ${c.merge}`} tone="amber" />
        <Pill label={`Conflict: ${c.conflict}`} tone="rose" />
        <Pill label={`Overlap: ${c.overlap}`} tone="amber" />
        <Pill label={`Unclassifiable: ${c.unclassifiable}`} tone="gray" />
        <Pill label={`Needs app attachment: ${c.needs_app_attachment}`} tone="indigo" />
      </div>
      <div className="space-y-3">
        {result.transitions.map((t, i) => (
          <TransitionCard key={t.origin_legacy_rule_id || i} t={t} />
        ))}
      </div>
    </div>
  );
}

function TransitionCard({ t }: { t: LegacyTransition }) {
  return (
    <div className="border border-purple-200 rounded-lg overflow-hidden bg-white">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 border-b border-purple-200 text-[11px]">
        <strong className="font-mono text-purple-900">{t.origin_legacy_rule_id}</strong>
        <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase font-semibold ${VERDICT_STYLE[t.verdict] || ''}`}>{t.verdict}</span>
        <span className="text-gray-500">·</span>
        <span className="text-gray-600">{t.original.environment}</span>
        <span className="text-gray-500">·</span>
        <span className="font-mono text-gray-700">{t.original.protocol} {t.original.ports}</span>
        <span className="ml-auto text-[10px] text-gray-500">{t.original.action}</span>
      </div>

      <div className="grid grid-cols-3 gap-0 text-[11px]">
        {/* Original (legacy) */}
        <div className="p-3 border-r border-gray-100 space-y-1.5">
          <div className="text-[10px] uppercase text-gray-500 font-semibold">Original (legacy)</div>
          <div className="font-mono text-rose-700 text-[11px] break-all">{t.original.source}</div>
          <div className="text-gray-400 text-[10px] text-center">↓</div>
          <div className="font-mono text-rose-700 text-[11px] break-all">{t.original.destination}</div>
        </div>

        {/* Classified */}
        <div className="p-3 border-r border-gray-100 space-y-1.5 bg-amber-50/40">
          <div className="text-[10px] uppercase text-amber-700 font-semibold">Classified</div>
          <ClassifiedSide side={t.classified.source} />
          <div className="text-gray-400 text-[10px] text-center">↓</div>
          <ClassifiedSide side={t.classified.destination} />
        </div>

        {/* Proposed NGDC */}
        <div className="p-3 space-y-1.5 bg-emerald-50/40">
          <div className="text-[10px] uppercase text-emerald-700 font-semibold">Proposed NGDC</div>
          <ProposedSide
            group={t.proposed.src_group}
            vrf={t.proposed.src_vrf}
            dc={t.proposed.src_dc}
          />
          <div className="text-gray-400 text-[10px] text-center">↓</div>
          <ProposedSide
            group={t.proposed.dst_group}
            vrf={t.proposed.dst_vrf}
            dc={t.proposed.dst_dc}
          />
          <div className="pt-1 mt-1 border-t border-emerald-200 font-mono text-[10px] text-emerald-800">
            {t.proposed.ports} · {t.proposed.action}
          </div>
        </div>
      </div>

      {(t.proposed.app_management_changes.length > 0 || t.proposed.group_changes.length > 0 || t.warnings.length > 0) && (
        <div className="px-3 py-2 border-t border-gray-100 space-y-1 bg-gray-50">
          {t.proposed.app_management_changes.length > 0 && (
            <div className="text-[10px]">
              <span className="font-semibold text-indigo-700">App Mgmt updates ({t.proposed.app_management_changes.length}):</span>
              <ul className="ml-4 list-disc text-gray-700">
                {t.proposed.app_management_changes.map((c, i) => (
                  <li key={i} className="font-mono">{JSON.stringify(c)}</li>
                ))}
              </ul>
            </div>
          )}
          {t.proposed.group_changes.length > 0 && (
            <div className="text-[10px]">
              <span className="font-semibold text-emerald-700">Group changes ({t.proposed.group_changes.length}):</span>
              <ul className="ml-4 list-disc text-gray-700">
                {t.proposed.group_changes.map((c, i) => (
                  <li key={i} className="font-mono">
                    {String(c.action)}: <strong>{String(c.name || '')}</strong>
                    {c.dc ? <> @ {String(c.dc)}/{String(c.nh)}/{String(c.sz)}</> : null}
                    {Array.isArray(c.members_to_add) && (c.members_to_add as unknown[]).length > 0 ? (
                      <> · members+: {(c.members_to_add as string[]).join(', ')}</>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {t.warnings.length > 0 && (
            <div className="text-[10px] text-amber-800">
              <span className="font-semibold">Warnings:</span>
              <ul className="ml-4 list-disc">
                {t.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
          {t.dedup_match && (
            <div className="text-[10px] text-rose-700">
              <span className="font-semibold">Dedup match:</span> {String((t.dedup_match as Record<string, string>).rule_id || '')} ({String((t.dedup_match as Record<string, string>).lifecycle_status || '')})
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ClassifiedSide({ side }: { side: LegacyClassifiedSide }) {
  return (
    <div className="space-y-0.5">
      <div className="font-mono text-amber-900 break-all">{side.value}</div>
      <div className="text-[10px] text-amber-700">
        kind: <strong>{side.kind}</strong>
        {side.matched ? <span className="ml-1.5 text-emerald-700">✓ matched</span> : <span className="ml-1.5 text-rose-700">✗ unresolved</span>}
      </div>
      {(side.dc || side.nh || side.sz) && (
        <div className="text-[10px] text-gray-700 font-mono">
          {side.dc || '—'} · {side.nh || '—'} · {side.sz || '—'}
        </div>
      )}
      {(side.app_distributed_id || side.service_id) && (
        <div className="text-[10px] text-indigo-700">
          {side.app_distributed_id ? `app: ${side.app_distributed_id}` : `svc: ${side.service_id}`} · {side.presence_kind}
        </div>
      )}
      {!side.matched && side.reason && (
        <div className="text-[10px] text-rose-600 italic">{side.reason}</div>
      )}
    </div>
  );
}

function ProposedSide({ group, vrf, dc }: { group: string; vrf: string; dc: string }) {
  if (!group) {
    return (
      <div className="font-mono text-rose-700 text-[11px]">— unable to derive NGDC group —</div>
    );
  }
  return (
    <div className="space-y-0.5">
      <div className="font-mono text-emerald-800 break-all">{group}</div>
      <div className="text-[10px] text-emerald-700">
        VRF: <span className="font-mono">{vrf || '—'}</span>
        {dc && <> · DC: <span className="font-mono">{dc}</span></>}
      </div>
    </div>
  );
}

function Pill({ label, tone }: { label: string; tone?: 'emerald' | 'rose' | 'amber' | 'gray' | 'indigo' }) {
  const toneClass: Record<string, string> = {
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    rose: 'bg-rose-50 border-rose-200 text-rose-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    gray: 'bg-gray-100 border-gray-200 text-gray-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  };
  return <span className={`px-2 py-0.5 rounded border ${tone ? toneClass[tone] : 'bg-white'}`}>{label}</span>;
}

// ============================================================
// Standardizer (dedup-only) view — preserved for backward compat
// ============================================================

function NormalizeResults({ result }: { result: { counters: { total: number; standardized: number; merged_existing: number; overlap_flagged: number; unclassifiable: number }; decisions: Decision[] } }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-[11px] flex-wrap">
        <Pill label={`Total: ${result.counters.total}`} />
        <Pill label={`Standardized: ${result.counters.standardized}`} tone="emerald" />
        <Pill label={`Merged into existing: ${result.counters.merged_existing}`} tone="rose" />
        <Pill label={`Overlap flagged: ${result.counters.overlap_flagged}`} tone="amber" />
        <Pill label={`Unclassifiable: ${result.counters.unclassifiable}`} tone="gray" />
      </div>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-[11px]">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left p-2">Legacy ID</th>
              <th className="text-left p-2">Verdict</th>
              <th className="text-left p-2">Standardized rule</th>
              <th className="text-left p-2">Dedup match</th>
              <th className="text-left p-2">Warnings</th>
            </tr>
          </thead>
          <tbody>
            {result.decisions.map((d, i) => (
              <tr key={i} className="border-t border-gray-100 align-top">
                <td className="p-2 font-mono">{d.origin_legacy_rule_id}</td>
                <td className="p-2">
                  <span className={`px-1.5 py-0.5 rounded border text-[10px] uppercase font-semibold ${VERDICT_STYLE[d.verdict] || ''}`}>{d.verdict}</span>
                  {d.block && <span className="ml-1 text-[10px] text-rose-700 font-semibold">BLOCK</span>}
                </td>
                <td className="p-2 font-mono text-[10px]">
                  {d.physical_rule ? <PhysicalRulePreview rule={d.physical_rule} /> : <span className="text-gray-400">—</span>}
                </td>
                <td className="p-2 font-mono text-[10px]">
                  {d.dedup_match ? <DedupMatchPreview match={d.dedup_match} /> : <span className="text-gray-400">—</span>}
                </td>
                <td className="p-2 text-[10px] text-amber-800">
                  {d.warnings.length > 0 ? d.warnings.join('; ') : <span className="text-gray-400">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PhysicalRulePreview({ rule }: { rule: Record<string, unknown> }) {
  const r = rule as Record<string, string | undefined>;
  return (
    <div>
      <div>
        <span className="text-emerald-700">{r.src_dc}</span> · {r.src_group_ref || r.src_group} → <span className="text-emerald-700">{r.dst_dc}</span> · {r.dst_group_ref || r.dst_group}
      </div>
      <div className="text-gray-600">{r.ports} {r.action}</div>
    </div>
  );
}

function DedupMatchPreview({ match }: { match: Record<string, unknown> }) {
  const m = match as Record<string, string | undefined>;
  const memberMatch = m.match_kind === 'member';
  return (
    <div>
      <div className="text-rose-700"><strong>{m.rule_id}</strong> · {m.lifecycle_status}</div>
      <div>{m.src_group} → {m.dst_group}</div>
      <div className="text-gray-600">{m.existing_ports} {m.existing_action}</div>
      {memberMatch && (
        <div
          className="mt-1 inline-block px-1.5 py-0.5 rounded border border-purple-200 bg-purple-50 text-purple-800 text-[10px] font-mono"
          title={`src ${m.src_relation || 'subset'} · dst ${m.dst_relation || 'subset'}`}
        >
          via members of {m.via_src_group}
          {m.via_dst_group && m.via_dst_group !== m.via_src_group ? ` / ${m.via_dst_group}` : ''}
        </div>
      )}
    </div>
  );
}
