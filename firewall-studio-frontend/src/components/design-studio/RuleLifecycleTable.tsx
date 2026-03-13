import { Search, Shield, Trash2, List, Grid, CheckCircle, AlertTriangle } from 'lucide-react';
import { StatusBadge } from '@/components/ui/status-badge';
import type { FirewallRule } from '@/types';

interface RuleLifecycleTableProps {
  rules: FirewallRule[];
  onModify: (rule: FirewallRule) => void;
  onCertify: (ruleId: string) => void;
  onDelete: (ruleId: string) => void;
  onSubmit: (ruleId: string) => void;
  onViewHistory: (ruleId: string) => void;
}

export function RuleLifecycleTable({ rules, onModify, onCertify, onDelete, onSubmit }: RuleLifecycleTableProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h3 className="text-base font-bold text-slate-800">Rule Lifecycle Management</h3>
        <div className="flex items-center gap-2">
          <button className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700 transition-colors">
            Modify
          </button>
          <button
            onClick={() => {
              const draftRule = rules.find(r => r.status === 'Draft');
              if (draftRule) onSubmit(draftRule.rule_id);
            }}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            Submit Rule
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
            Save Draft
          </button>
          <button className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
            Delete
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-2">
        <div className="flex items-center gap-1.5 rounded-md border border-slate-200 px-2 py-1">
          <span className="text-xs font-medium text-slate-600">Rule</span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">All</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-md border border-slate-200 px-2 py-1">
          <span className="text-xs font-medium text-slate-600">Filter</span>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          <span>1-1-{rules.length} of 1-{rules.length}</span>
          <button className="p-1 hover:bg-slate-100 rounded"><Grid className="h-3.5 w-3.5" /></button>
          <button className="p-1 hover:bg-slate-100 rounded"><List className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Rule</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Source</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Destination</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Compliance</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Expiry</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Owner</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className="border-b border-slate-50 hover:bg-blue-50/30 transition-colors">
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <List className="h-3.5 w-3.5 text-slate-400" />
                    <span className="text-sm font-semibold text-slate-700">{rule.rule_id}</span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className="rounded bg-orange-100 px-1 py-0.5 text-xs text-orange-700 font-medium">
                      {rule.source.group_name || rule.source.source_type}
                    </span>
                    <span className="text-xs text-slate-600">
                      {rule.source.ip_address || rule.source.cidr || ''}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className="rounded bg-teal-100 px-1 py-0.5 text-xs text-teal-700 font-medium">
                      {rule.destination.security_zone}
                    </span>
                    <span className="text-xs text-slate-600">{rule.destination.name}</span>
                    <span className="text-xs text-slate-400">{rule.destination.ports}</span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1">
                    {rule.compliance?.naming_valid && rule.compliance?.group_to_group ? (
                      <span className="flex items-center gap-0.5 rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">
                        <CheckCircle className="h-3 w-3" /> Compliant
                      </span>
                    ) : rule.compliance?.requires_exception ? (
                      <span className="flex items-center gap-0.5 rounded-full bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-700">
                        <AlertTriangle className="h-3 w-3" /> Exception
                      </span>
                    ) : (
                      <span className="flex items-center gap-0.5 rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
                        <AlertTriangle className="h-3 w-3" /> Non-Compliant
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={rule.status} />
                </td>
                <td className="px-4 py-2.5 text-xs text-slate-600">{rule.expiry || '—'}</td>
                <td className="px-4 py-2.5 text-xs text-slate-600">{rule.owner}</td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onModify(rule)}
                      className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      <Search className="inline h-3 w-3 mr-0.5" />
                      Modify
                    </button>
                    <button
                      onClick={() => onCertify(rule.rule_id)}
                      className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      <Shield className="inline h-3 w-3 mr-0.5" />
                      Certify
                    </button>
                    <button
                      onClick={() => onDelete(rule.rule_id)}
                      className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="inline h-3 w-3 mr-0.5" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
