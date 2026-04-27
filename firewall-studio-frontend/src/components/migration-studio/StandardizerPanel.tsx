import { useMemo, useState } from 'react';
import * as api from '@/lib/api';

/**
 * Migration Standardizer Panel
 *
 * Lets ops paste / type a small batch of legacy rule rows and run them
 * through the same standardization + dedup engine that pre-submit
 * validation uses. Surfaces a verdict per rule and the matching existing
 * standardized rule (if any) so SNS can bulk-merge legacy → NGDC without
 * recreating duplicates.
 *
 * Input format (one rule per line, comma-separated):
 *   legacy_id, source_ip_or_group, destination_ip_or_group, protocol_ports, action[, env]
 * Example:
 *   LEG-001, 10.10.0.0/22, g-ORACLE-NH02-CCS, TCP 1521-1530, ALLOW, Production
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
  identical: 'bg-rose-50 text-rose-700 border-rose-200',
  subset: 'bg-rose-50 text-rose-700 border-rose-200',
  conflict: 'bg-rose-50 text-rose-700 border-rose-200',
  overlap: 'bg-amber-50 text-amber-800 border-amber-200',
  unclassifiable: 'bg-gray-100 text-gray-700 border-gray-200',
};

export default function StandardizerPanel() {
  const [text, setText] = useState<string>(
    'LEG-001, 10.10.0.0/22, g-ORACLE-NH02-CCS, TCP 1521-1530, ALLOW, Production',
  );
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{
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
      rules.push({
        legacy_id,
        source,
        destination,
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
    setResult(null);
    try {
      const r = await api.normalizeLegacyRulesBulk(parsed);
      setResult(r);
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
          <h3 className="text-sm font-semibold text-purple-900">Migration Standardizer</h3>
          <p className="text-xs text-gray-700 max-w-2xl">
            Run legacy rules through the standardization + dedup engine. Each rule is normalized to NGDC group naming
            (<code className="font-mono">g-</code> → <code className="font-mono">grp-</code>; per-zone <code>naming_mode</code> applied) and checked against existing
            Approved/Deployed rules. Zone-scoped SZs (<strong>STD/GEN/Shared/UGen/USTD</strong>) collapse per-app legacy groups into a single shared
            cluster group, so legacy → NGDC migrations dedup heavily.
          </p>
        </div>
        <button onClick={() => void run()} disabled={running || parsed.length === 0}
          className="text-xs px-3 py-1.5 rounded bg-purple-600 text-white hover:bg-purple-700 disabled:bg-gray-300 whitespace-nowrap">
          {running ? 'Standardizing…' : `Standardize ${parsed.length} rule${parsed.length === 1 ? '' : 's'}`}
        </button>
      </div>

      <div>
        <label className="text-[11px] text-gray-600">
          Legacy rules (one per line — <code>legacy_id, source, destination, ports, action, environment</code>)
        </label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
          className="w-full border rounded px-2 py-1 font-mono text-[11px]" />
      </div>

      {error && <div className="rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">{error}</div>}

      {result && (
        <div className="space-y-2">
          <div className="flex items-center gap-3 text-[11px] flex-wrap">
            <span className="px-2 py-0.5 rounded border bg-white">Total: {result.counters.total}</span>
            <span className="px-2 py-0.5 rounded border bg-emerald-50 border-emerald-200 text-emerald-700">Standardized: {result.counters.standardized}</span>
            <span className="px-2 py-0.5 rounded border bg-rose-50 border-rose-200 text-rose-700">Merged into existing: {result.counters.merged_existing}</span>
            <span className="px-2 py-0.5 rounded border bg-amber-50 border-amber-200 text-amber-700">Overlap flagged: {result.counters.overlap_flagged}</span>
            <span className="px-2 py-0.5 rounded border bg-gray-100 border-gray-200 text-gray-700">Unclassifiable: {result.counters.unclassifiable}</span>
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
                      <span className={`px-1.5 py-0.5 rounded border text-[10px] uppercase font-semibold ${VERDICT_STYLE[d.verdict] || ''}`}>
                        {d.verdict}
                      </span>
                      {d.block && <span className="ml-1 text-[10px] text-rose-700 font-semibold">BLOCK</span>}
                    </td>
                    <td className="p-2 font-mono text-[10px]">
                      {d.physical_rule ? (
                        <PhysicalRulePreview rule={d.physical_rule} />
                      ) : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="p-2 font-mono text-[10px]">
                      {d.dedup_match ? (
                        <DedupMatchPreview match={d.dedup_match} />
                      ) : <span className="text-gray-400">—</span>}
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
      )}
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
