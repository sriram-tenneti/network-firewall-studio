import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { ApprovalModal } from '@/components/review/ApprovalModal';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import { getReviewRequests, approveReview, rejectReview, compileRule } from '@/lib/api';
import type { ReviewRequest } from '@/types';
import type { Column } from '@/components/shared/DataTable';

export default function ReviewPage() {
  const [reviews, setReviews] = useState<ReviewRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Pending');
  const approvalModal = useModal<ReviewRequest>();
  const { notification, showNotification } = useNotification();

  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getReviewRequests();
      setReviews(data);
    } catch {
      showNotification('Failed to load reviews', 'error');
    }
    setLoading(false);
  }, [showNotification]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  const filteredReviews = reviews.filter(r => {
    if (activeTab === 'All') return true;
    return r.status === activeTab;
  });

  const counts = {
    All: reviews.length,
    Pending: reviews.filter(r => r.status === 'Pending').length,
    Approved: reviews.filter(r => r.status === 'Approved').length,
    Rejected: reviews.filter(r => r.status === 'Rejected').length,
  };

  const handleApprove = async (reviewId: string, notes: string) => {
    try {
      await approveReview(reviewId, notes);
      showNotification('Review approved successfully', 'success');
      loadReviews();
    } catch {
      showNotification('Failed to approve review', 'error');
    }
  };

  const handleReject = async (reviewId: string, notes: string) => {
    try {
      await rejectReview(reviewId, notes);
      showNotification('Review rejected', 'warning');
      loadReviews();
    } catch {
      showNotification('Failed to reject review', 'error');
    }
  };

  const columns: Column<ReviewRequest>[] = [
    { key: 'rule_id', header: 'Rule ID', sortable: true, width: '120px' },
    {
      key: 'request_type', header: 'Type', sortable: true, width: '120px',
      render: (_, row) => (
        <span className="text-xs capitalize">{row.request_type.replace(/_/g, ' ')}</span>
      ),
    },
    {
      key: 'rule_summary.application', header: 'Application', sortable: true, width: '120px',
    },
    {
      key: 'rule_summary.source', header: 'Source', sortable: false, width: '150px',
      render: (_, row) => <span className="font-mono text-xs">{row.rule_summary?.source || 'N/A'}</span>,
    },
    {
      key: 'rule_summary.destination', header: 'Destination', sortable: false, width: '150px',
      render: (_, row) => <span className="font-mono text-xs">{row.rule_summary?.destination || 'N/A'}</span>,
    },
    {
      key: 'status', header: 'Status', sortable: true, width: '110px',
      render: (_, row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'submitted_at', header: 'Submitted', sortable: true, width: '150px',
      render: (_, row) => row.submitted_at ? new Date(row.submitted_at).toLocaleString() : 'N/A',
    },
    {
      key: 'reviewer', header: 'Reviewer', sortable: true, width: '100px',
      render: (_, row) => row.reviewer || 'Unassigned',
    },
    {
      key: '_actions', header: 'Actions', sortable: false, width: '100px',
      render: (_, row) => (
        <button
          onClick={(e) => { e.stopPropagation(); approvalModal.open(row); }}
          className={`px-2 py-1 text-xs font-medium rounded ${
            row.status === 'Pending'
              ? 'text-blue-700 bg-blue-50 hover:bg-blue-100'
              : 'text-gray-600 bg-gray-50 hover:bg-gray-100'
          }`}
        >
          {row.status === 'Pending' ? 'Review' : 'View'}
        </button>
      ),
    },
  ];

  const tabs = [
    { id: 'All', label: 'All', count: counts.All },
    { id: 'Pending', label: 'Pending', count: counts.Pending },
    { id: 'Approved', label: 'Approved', count: counts.Approved },
    { id: 'Rejected', label: 'Rejected', count: counts.Rejected },
  ];

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      {notification && <Notification message={notification.message} type={notification.type} />}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Review & Approval</h1>
        <p className="text-sm text-gray-500 mt-1">Manage firewall rule review requests and approvals for SNS users</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Reviews', value: counts.All, color: 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800' },
          { label: 'Pending', value: counts.Pending, color: 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-800' },
          { label: 'Approved', value: counts.Approved, color: 'bg-gradient-to-br from-green-100 to-green-200 text-green-800' },
          { label: 'Rejected', value: counts.Rejected, color: 'bg-gradient-to-br from-red-100 to-red-200 text-red-800' },
        ].map(card => (
          <div key={card.label} className={`p-4 rounded-lg ${card.color}`}>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="text-sm font-medium mt-1">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white border rounded-lg shadow-sm">
        <div className="px-4 pt-4">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </div>

        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <DataTable
              data={filteredReviews}
              columns={columns}
              keyField="id"
              searchFields={['id', 'rule_id', 'rule_summary.application', 'requestor']}
              onRowClick={(row) => approvalModal.open(row)}
              emptyMessage="No review requests found"
              defaultPageSize={25}
            />
          )}
        </div>
      </div>

      <ApprovalModal
        isOpen={approvalModal.isOpen}
        onClose={approvalModal.close}
        review={approvalModal.data}
        onApprove={handleApprove}
        onReject={handleReject}
        onCompileRule={compileRule}
      />
    </div>
  );
}
