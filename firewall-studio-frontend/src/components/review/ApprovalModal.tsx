import { useState } from 'react';
import { Modal } from '../shared/Modal';
import { StatusBadge } from '../shared/StatusBadge';
import type { ReviewRequest } from '@/types';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  review: ReviewRequest | null;
  onApprove: (reviewId: string, notes: string) => void;
  onReject: (reviewId: string, notes: string) => void;
}

export function ApprovalModal({ isOpen, onClose, review, onApprove, onReject }: ApprovalModalProps) {
  const [notes, setNotes] = useState('');
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);

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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Review: ${review.rule_id}`} size="lg">
      <div className="divide-y divide-gray-100 mb-4">
        {rows.map(([label, value]) => (
          <div key={label} className="flex py-2.5 px-1">
            <div className="w-36 text-sm font-medium text-gray-500 flex-shrink-0">{label}</div>
            <div className="text-sm text-gray-900 flex-1">{value}</div>
          </div>
        ))}
      </div>

      {review.comments && (
        <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg mb-4">
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
        <div className="flex justify-end gap-3 mt-4 pt-4 border-t">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Close</button>
        </div>
      )}
    </Modal>
  );
}
