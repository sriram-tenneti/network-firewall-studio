import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import { compileRule } from '@/lib/api';
import type { CompiledRule } from '@/types';

interface GroupProvisioningResult {
  status: string;
  provisioned: { name: string; type: string; members: string[]; device_command: string }[];
  violations: string[];
  total_groups: number;
  provisioned_count: number;
}

interface CompiledRuleWithGroups extends CompiledRule {
  group_provisioning?: GroupProvisioningResult;
}

interface RuleCompilerViewProps {
  isOpen: boolean;
  onClose: () => void;
  ruleId: string | null;
}

export function RuleCompilerView({ isOpen, onClose, ruleId }: RuleCompilerViewProps) {
  const [compiled, setCompiled] = useState<CompiledRuleWithGroups | null>(null);
  const [vendor, setVendor] = useState('generic');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && ruleId) {
      doCompile(ruleId, vendor);
    }
  }, [isOpen, ruleId]);

  const doCompile = async (id: string, v: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await compileRule(id, v) as CompiledRuleWithGroups;
      setCompiled(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compilation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVendorChange = (v: string) => {
    setVendor(v);
    if (ruleId) doCompile(ruleId, v);
  };

  const handleCopy = () => {
    if (compiled?.compiled_text) {
      navigator.clipboard.writeText(compiled.compiled_text);
    }
  };

  const gp = compiled?.group_provisioning;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Compile & Submit: ${ruleId || ''}`} size="xl">
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Target Platform:</label>
          <div className="flex gap-2">
            {[
              { value: 'generic', label: 'Generic YAML' },
              { value: 'palo_alto', label: 'Palo Alto' },
              { value: 'checkpoint', label: 'Check Point' },
              { value: 'cisco_asa', label: 'Cisco ASA' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => handleVendorChange(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                  vendor === opt.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">{error}</div>
        )}

        {compiled && !loading && (
          <>
            {/* Compiled Output */}
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Compiled Output — {compiled.vendor_format}</span>
                <button onClick={handleCopy} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Copy to Clipboard</button>
              </div>
              <pre className="p-4 bg-gray-900 text-green-400 rounded-lg text-sm font-mono overflow-x-auto max-h-96 leading-relaxed whitespace-pre-wrap">
                {compiled.compiled_text}
              </pre>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">Source Objects</h4>
                <ul className="space-y-1">
                  {compiled.source_objects.map((s, i) => (
                    <li key={i} className="text-gray-600 font-mono text-xs">{s}</li>
                  ))}
                </ul>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">Destination Objects</h4>
                <ul className="space-y-1">
                  {compiled.destination_objects.map((d, i) => (
                    <li key={i} className="text-gray-600 font-mono text-xs">{d}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700">Services</span>
                <div className="mt-1 font-mono text-xs text-gray-600">{compiled.services.join(', ')}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700">Action</span>
                <div className="mt-1 text-xs text-gray-600 capitalize">{compiled.action}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-700">Logging</span>
                <div className="mt-1 text-xs text-gray-600">{compiled.logging ? 'Enabled' : 'Disabled'}</div>
              </div>
            </div>

            {/* Group Provisioning to Firewall Device */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
                Group Submission to Firewall Device
              </h3>
              {gp ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-4 text-xs">
                    <span className={`px-2 py-1 rounded-full font-medium ${
                      gp.status === 'success' ? 'bg-green-100 text-green-700' :
                      gp.status === 'partial' ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {gp.status === 'success' ? 'All Groups Submitted' :
                       gp.status === 'partial' ? 'Partial Submission' :
                       'Submission Failed'}
                    </span>
                    <span className="text-gray-500">
                      {gp.provisioned_count} of {gp.total_groups} groups submitted
                    </span>
                  </div>

                  {gp.provisioned.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <h4 className="text-xs font-medium text-gray-600 mb-2">Provisioned Groups</h4>
                      <div className="space-y-2">
                        {gp.provisioned.map((g, i) => (
                          <div key={i} className="bg-white border border-gray-200 rounded p-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-medium text-gray-800">{g.name}</span>
                              <span className="text-xs text-gray-400">{g.type}</span>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              Members: {g.members.length > 0 ? g.members.slice(0, 5).join(', ') : 'None'}
                              {g.members.length > 5 && ` +${g.members.length - 5} more`}
                            </div>
                            <pre className="text-xs text-blue-600 font-mono mt-1 bg-blue-50 rounded px-2 py-1 overflow-x-auto">
                              {g.device_command}
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {gp.violations.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <h4 className="text-xs font-medium text-red-700 mb-1">NGDC Standards Violations</h4>
                      <ul className="space-y-1">
                        {gp.violations.map((v, i) => (
                          <li key={i} className="text-xs text-red-600 flex items-start gap-1">
                            <span className="mt-0.5 text-red-400">&#x2022;</span> {v}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-500 italic">No groups associated with this rule&apos;s application for device submission.</p>
              )}
            </div>
          </>
        )}
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
