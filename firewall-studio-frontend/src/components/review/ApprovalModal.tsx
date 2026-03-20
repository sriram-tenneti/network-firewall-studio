import { useState } from 'react';
import { Modal } from '../shared/Modal';
import { StatusBadge } from '../shared/StatusBadge';
import type { ReviewRequest, CompiledRule } from '@/types';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  review: ReviewRequest | null;
  onApprove: (reviewId: string, notes: string) => void;
  onReject: (reviewId: string, notes: string) => void;
  onCompileRule?: (ruleId: string, vendor?: string) => Promise<CompiledRule>;
}

export function ApprovalModal({ isOpen, onClose, review, onApprove, onReject, onCompileRule }: ApprovalModalProps) {
  const [notes, setNotes] = useState('');
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);
  const [compiledRule, setCompiledRule] = useState<CompiledRule | null>(null);
  const [compileVendor, setCompileVendor] = useState('generic');
  const [compiling, setCompiling] = useState(false);
  // showPolicy toggle removed - compile section is always visible for approvers

  const handleCompile = async () => {
    if (!review || !onCompileRule) return;
    setCompiling(true);
    try {
      const result = await onCompileRule(review.rule_id, compileVendor);
      setCompiledRule(result);
      setShowPolicy(true);
    } catch {
      setCompiledRule(null);
    }
    setCompiling(false);
  };

  if (!review) return null;

  const handleSubmit = () => {
    if (action === 'approve') {
      onApprove(review.id, notes);
    } else if (action === 'reject') {
      if (!notes.trim()) return;
      onReject(review.id, notes);
    }
    setNotes('');
    setAction(null);
    onClose();
  };

  const rows: [string, string | React.ReactNode][] = [
    ['Review ID', review.id],
    ['Rule ID', review.rule_id],
    ['Request Type', review.request_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())],
    ['Status', <StatusBadge key="s" status={review.status} />],
    ['Requestor', review.requestor],
    ['Submitted', review.submitted_at ? new Date(review.submitted_at).toLocaleString() : 'N/A'],
    ['Application', review.rule_summary?.application || 'N/A'],
    ['Source', review.rule_summary?.source || 'N/A'],
    ['Destination', review.rule_summary?.destination || 'N/A'],
    ['Ports', review.rule_summary?.ports || 'N/A'],
    ['Environment', review.rule_summary?.environment || 'N/A'],
  ];

  const hasDelta = review.delta && (
    Object.keys(review.delta.added).length > 0 ||
    Object.keys(review.delta.removed).length > 0 ||
    Object.keys(review.delta.changed).length > 0
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Review: ${review.rule_id}`} size="xl">
      <div className="max-h-[80vh] overflow-y-auto pr-1 space-y-4">
      {/* Rule Details */}
      <div className="divide-y divide-gray-100">
        {rows.map(([label, value]) => (
          <div key={label} className="flex py-2.5 px-1">
            <div className="w-36 text-sm font-medium text-gray-500 flex-shrink-0">{label}</div>
            <div className="text-sm text-gray-900 flex-1">{value}</div>
          </div>
        ))}
      </div>

      {/* Delta View - Full Change Details for Approvers */}
      {hasDelta && review.delta && (
        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <h3 className="text-sm font-semibold text-blue-800 mb-3">Change Delta (Full Details)</h3>
          <div className="space-y-3">
            {Object.keys(review.delta.added).length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-green-700 mb-1">Added</h4>
                {Object.entries(review.delta.added).map(([field, values]) => (
                  <div key={field} className="ml-2">
                    <span className="text-xs text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
                    {values.map((v, i) => (
                      <div key={i} className="text-xs text-green-700 font-mono ml-2">+ {v}</div>
                    ))}
                  </div>
                ))}
              </div>
            )}
            {Object.keys(review.delta.removed).length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-red-700 mb-1">Removed</h4>
                {Object.entries(review.delta.removed).map(([field, values]) => (
                  <div key={field} className="ml-2">
                    <span className="text-xs text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
                    {values.map((v, i) => (
                      <div key={i} className="text-xs text-red-700 font-mono ml-2">- {v}</div>
                    ))}
                  </div>
                ))}
              </div>
            )}
            {Object.keys(review.delta.changed).length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-blue-700 mb-1">Changed</h4>
                {Object.entries(review.delta.changed).map(([field, change]) => (
                  <div key={field} className="ml-2 text-xs">
                    <span className="text-gray-500">{field.replace(/rule_/g, '').replace(/_/g, ' ')}:</span>
                    <span className="text-red-600 line-through ml-1">{change.from}</span>
                    <span className="mx-1">&rarr;</span>
                    <span className="text-green-600">{change.to}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Compile Rule - Prominent for Approvers */}
      <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-indigo-800">Compile to Device-Deployable Rule</h3>
          {onCompileRule && (
            <div className="flex items-center gap-2">
              <select
                value={compileVendor}
                onChange={e => setCompileVendor(e.target.value)}
                className="px-2 py-1 text-xs border border-indigo-300 rounded-md bg-white"
              >
                <option value="generic">Generic</option>
                <option value="palo_alto">Palo Alto</option>
                <option value="checkpoint">Check Point</option>
                <option value="cisco_asa">Cisco ASA</option>
              </select>
              <button
                onClick={handleCompile}
                disabled={compiling}
                className="px-4 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 shadow-sm"
              >
                {compiling ? 'Compiling...' : 'Compile Rule'}
              </button>
            </div>
          )}
        </div>
        {compiledRule ? (
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400 font-medium">Format: {compiledRule.vendor_format}</span>
              <button
                onClick={() => navigator.clipboard.writeText(compiledRule.compiled_text)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Copy to Clipboard
              </button>
            </div>
            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{compiledRule.compiled_text}</pre>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-gray-500">Source Objects:</span> <span className="text-gray-300">{compiledRule.source_objects?.join(', ') || 'N/A'}</span></div>
              <div><span className="text-gray-500">Dest Objects:</span> <span className="text-gray-300">{compiledRule.destination_objects?.join(', ') || 'N/A'}</span></div>
              <div><span className="text-gray-500">Services:</span> <span className="text-gray-300">{compiledRule.services?.join(', ') || 'N/A'}</span></div>
              <div><span className="text-gray-500">Action:</span> <span className="text-gray-300">{compiledRule.action}</span></div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-indigo-600 italic">Select a vendor format and click &quot;Compile Rule&quot; to generate device-specific deployable output (Palo Alto, Check Point, Cisco ASA, or Generic).</p>
        )}
      </div>

      {review.comments && (
        <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <h4 className="text-xs font-semibold text-blue-700 mb-1">Requestor Comments</h4>
          <p className="text-sm text-blue-800">{review.comments}</p>
        </div>
      )}

      {review.status === 'Pending' && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Review Notes</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-20 resize-none"
              placeholder={action === 'reject' ? 'Rejection reason is required...' : 'Optional notes for approval...'}
              value={notes}
              onChange={e => setNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={() => { setAction('reject'); }}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                action === 'reject' ? 'bg-red-600 text-white' : 'text-red-700 bg-red-50 border border-red-200 hover:bg-red-100'
              }`}
            >
              Reject
            </button>
            <button
              onClick={() => { setAction('approve'); }}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                action === 'approve' ? 'bg-green-600 text-white' : 'text-green-700 bg-green-50 border border-green-200 hover:bg-green-100'
              }`}
            >
              Approve
            </button>
          </div>

          {action && (
            <div className="flex justify-end gap-3 pt-2 border-t">
              <button onClick={() => { setAction(null); setNotes(''); }} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
              <button
                onClick={handleSubmit}
                disabled={action === 'reject' && !notes.trim()}
                className={`px-4 py-2 text-sm font-medium text-white rounded-md ${
                  action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                Confirm {action === 'approve' ? 'Approval' : 'Rejection'}
              </button>
            </div>
          )}
        </div>
      )}

      {review.status !== 'Pending' && (
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
        </div>
      )}
      </div>
    </Modal>
  );
}
