import { useState } from 'react';
import { Search, Shield, Trash2, List, Grid, CheckCircle, AlertTriangle, Edit, Filter } from 'lucide-react';
import { StatusBadge } from '@/components/ui/status-badge';
import type { FirewallRule, Application } from '@/types';

interface RuleLifecycleTableProps {
  rules: FirewallRule[];
  applications: Application[];
  selectedAppFilter: string;
  onAppFilterChange: (appId: string) => void;
  onModify: (rule: FirewallRule) => void;
  onCertify: (ruleId: string) => void;
  onDelete: (ruleId: string) => void;
  onSubmit: (ruleId: string) => void;
  onViewHistory: (ruleId: string) => void;
  onSaveDraft: (ruleId: string) => void;
}

export function RuleLifecycleTable({
  rules,
  applications,
  selectedAppFilter,
  onAppFilterChange,
  onModify,
  onCertify,
  onDelete,
  onSubmit,
  onViewHistory: _onViewHistory,
  onSaveDraft,
}: RuleLifecycleTableProps) {
  void _onViewHistory;
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);

  const selectedRule = rules.find(r => r.rule_id === selectedRuleId) || null;

  const handleRowClick = (rule: FirewallRule) => {
    setSelectedRuleId(prev => prev === rule.rule_id ? null : rule.rule_id);
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h3 className="text-base font-bold text-slate-800">Rule Lifecycle Management</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { if (selectedRule) onModify(selectedRule); }}
            disabled={!selectedRule}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              selectedRule
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Edit className="inline h-3 w-3 mr-0.5" />
            Modify
          </button>
          <button
            onClick={() => { if (selectedRule) onSubmit(selectedRule.rule_id); }}
            disabled={!selectedRule || selectedRule.status !== 'Draft'}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              selectedRule && selectedRule.status === 'Draft'
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            Submit Rule
          </button>
          <button
            onClick={() => { if (selectedRule && selectedRule.status === 'Draft') onSaveDraft(selectedRule.rule_id); }}
            disabled={!selectedRule || selectedRule.status !== 'Draft'}
            className={`rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors ${
              selectedRule && selectedRule.status === 'Draft'
                ? 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                : 'border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            Save Draft
          </button>
          <button
            onClick={() => { if (selectedRule) { onDelete(selectedRule.rule_id); setSelectedRuleId(null); } }}
            disabled={!selectedRule}
            className={`rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors ${
              selectedRule
                ? 'border-red-300 bg-white text-red-600 hover:bg-red-50'
                : 'border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Trash2 className="inline h-3 w-3 mr-0.5" />
            Delete
          </button>
        </div>
      </div>

      {/* App ID Filter + table controls */}
      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-2">
        <div className="flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-2 py-1">
          <Filter className="h-3.5 w-3.5 text-blue-500" />
          <span className="text-xs font-medium text-blue-700">App ID:</span>
          <select
            value={selectedAppFilter}
            onChange={(e) => onAppFilterChange(e.target.value)}
            className="rounded border-0 bg-transparent text-xs font-semibold text-blue-800 focus:ring-0 py-0 pr-6 pl-1"
          >
            <option value="">All Applications</option>
            {applications.map((app) => (
              <option key={app.id} value={app.app_id}>
                {app.app_id} - {app.name}
              </option>
            ))}
          </select>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          {selectedRule && (
            <span className="rounded bg-blue-100 text-blue-700 px-2 py-0.5 font-medium">
              Selected: {selectedRule.rule_id}
            </span>
          )}
          <span>{rules.length} rule{rules.length !== 1 ? 's' : ''}</span>
          <button className="p-1 hover:bg-slate-100 rounded"><Grid className="h-3.5 w-3.5" /></button>
          <button className="p-1 hover:bg-slate-100 rounded"><List className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-slate-100 bg-slate-50/95">
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase w-8"></th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Rule</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">App</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Source</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Destination</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Compliance</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Expiry</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-400">
                  {selectedAppFilter ? `No rules found for application "${selectedAppFilter}"` : 'No rules found'}
                </td>
              </tr>
            )}
            {rules.map((rule) => {
              const isSelected = selectedRuleId === rule.rule_id;
              return (
                <tr
                  key={rule.id || rule.rule_id}
                  onClick={() => handleRowClick(rule)}
                  className={`border-b border-slate-50 cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50 ring-1 ring-inset ring-blue-200' : 'hover:bg-blue-50/30'
                  }`}
                >
                  <td className="px-4 py-2.5">
                    <input
                      type="radio"
                      name="selectedRule"
                      checked={isSelected}
                      onChange={() => setSelectedRuleId(rule.rule_id)}
                      className="h-3.5 w-3.5 border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <List className="h-3.5 w-3.5 text-slate-400" />
                      <span className="text-sm font-semibold text-slate-700">{rule.rule_id}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-bold text-indigo-700">
                      {rule.application || '\u2014'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <span className="rounded bg-orange-100 px-1 py-0.5 text-xs text-orange-700 font-medium truncate max-w-32">
                        {rule.source.group_name || rule.source.source_type}
                      </span>
                      <span className="text-xs text-slate-600 truncate max-w-20">
                        {rule.source.ip_address || rule.source.cidr || ''}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <span className="rounded bg-teal-100 px-1 py-0.5 text-xs text-teal-700 font-medium">
                        {rule.destination.security_zone}
                      </span>
                      <span className="text-xs text-slate-600 truncate max-w-24">{rule.destination.name}</span>
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
                  <td className="px-4 py-2.5 text-xs text-slate-600">{rule.expiry || '\u2014'}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); onModify(rule); }}
                        className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                        title="Edit this rule"
                      >
                        <Search className="inline h-3 w-3 mr-0.5" />
                        Modify
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onCertify(rule.rule_id); }}
                        className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                        title="Certify this rule"
                      >
                        <Shield className="inline h-3 w-3 mr-0.5" />
                        Certify
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onDelete(rule.rule_id); }}
                        className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                        title="Delete this rule"
                      >
                        <Trash2 className="inline h-3 w-3" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
