import { useState, useEffect } from 'react';
import { Modal } from '../shared/Modal';
import { compileRule } from '@/lib/api';
import type { CompiledRule } from '@/types';

interface RuleCompilerViewProps {
  isOpen: boolean;
  onClose: () => void;
  ruleId: string | null;
}

export function RuleCompilerView({ isOpen, onClose, ruleId }: RuleCompilerViewProps) {
  const [compiled, setCompiled] = useState<CompiledRule | null>(null);
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
      const result = await compileRule(id, v);
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Rule Compiler: ${ruleId || ''}`} size="xl">
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
          </>
        )}
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
      </div>
    </Modal>
  );
}
