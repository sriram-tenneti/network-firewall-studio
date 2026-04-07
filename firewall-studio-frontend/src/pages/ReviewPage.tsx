import { useState, useEffect, useCallback } from 'react';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Tabs } from '@/components/shared/Tabs';
import { Notification } from '@/components/shared/Notification';
import { ApprovalModal } from '@/components/review/ApprovalModal';
import { useModal } from '@/hooks/useModal';
import { useNotification } from '@/hooks/useNotification';
import { getReviewRequests, approveReview, rejectReview, compileRule, getRuleModifications, approveRuleModification, rejectRuleModification, approvePolicyChange, rejectPolicyChange } from '@/lib/api';
import type { ReviewRequest, RuleModification } from '@/types';
import type { Column } from '@/components/shared/DataTable';

/** Convert a RuleModification into a ReviewRequest shape so both appear in the same table. */
function modToReview(m: RuleModification): ReviewRequest {
  return {
    id: m.id,
    rule_id: m.rule_id,
    rule_name: m.rule_id,
    request_type: 'modify_rule',
    requestor: 'sns_user',
    reviewer: m.reviewer,
    status: m.status as ReviewRequest['status'],
    submitted_at: m.created_at,
    reviewed_at: m.reviewed_at,
    comments: m.comments,
    review_notes: m.review_notes,
    modification_id: m.id,
    delta: m.delta,
    rule_summary: {
      application: m.original?.app_name || m.original?.app_id || 'N/A',
      source: m.original?.rule_source || 'N/A',
      destination: m.original?.rule_destination || 'N/A',
      ports: m.original?.rule_service || 'N/A',
      environment: m.original?.environment || '',
    },
  };
}

// Map route context to backend module values
const CONTEXT_TO_MODULE: Record<string, string> = {
  'firewall-studio': 'design-studio',
  'ngdc-standardization': 'migration-studio',
  'firewall-management': 'firewall-management',
  'design-studio': 'design-studio',
  'migration-studio': 'migration-studio',
  'org-admin': 'org-admin',
};

export default function ReviewPage(props: { context?: string }) {
  const moduleContext = props.context ? (CONTEXT_TO_MODULE[props.context] || props.context) : '';
  const [reviews, setReviews] = useState<ReviewRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEnv, setSelectedEnv] = useState<string>('');
  const [selectedModule, setSelectedModule] = useState<string>(moduleContext);
  const [activeTab, setActiveTab] = useState('Pending');
  const approvalModal = useModal<ReviewRequest>();
  const { notification, showNotification } = useNotification();

  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const [reviewData, modData] = await Promise.all([
        getReviewRequests(),
        getRuleModifications(),
      ]);
      // Merge rule modifications into reviews as modify_rule entries
      const modReviews = modData.map(modToReview);
      // Avoid duplicates — if a review already references the same modification_id, skip
      const existingModIds = new Set(reviewData.filter(r => r.modification_id).map(r => r.modification_id));
      const uniqueModReviews = modReviews.filter(mr => !existingModIds.has(mr.modification_id));
      setReviews([...reviewData, ...uniqueModReviews]);
    } catch {
      showNotification('Failed to load reviews', 'error');
    }
    setLoading(false);
  }, [showNotification]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  const envFilteredReviews = reviews.filter(r => {
    if (selectedEnv && r.rule_summary?.environment !== selectedEnv) return false;
    // Module-level filtering: each module sees only its own reviews
    if (selectedModule) {
      const mod = r.module || (r as unknown as Record<string, string>).module || '';
      // Strict: if module is set on the review, it must match; if not set, exclude from filtered views
      if (mod !== selectedModule) return false;
    }
    return true;
  });

  const filteredReviews = envFilteredReviews.filter(r => {
    if (activeTab === 'All') return true;
    return r.status === activeTab;
  });

  const counts = {
    All: envFilteredReviews.length,
    Pending: envFilteredReviews.filter(r => r.status === 'Pending').length,
    Approved: envFilteredReviews.filter(r => r.status === 'Approved').length,
    Rejected: envFilteredReviews.filter(r => r.status === 'Rejected').length,
  };

  const handleApprove = async (reviewId: string, notes: string) => {
    try {
      // Check if this is a rule modification (MOD-xxx), a policy change (POL-xxx), or a regular review
      const isModification = reviewId.startsWith('MOD-');
      // Find the review to check if it's a policy change
      const review = reviews.find(r => r.id === reviewId);
      const isPolicyChange = review?.request_type?.startsWith('policy_');
      if (isModification) {
        await approveRuleModification(reviewId, notes);
        showNotification('Rule modification approved successfully', 'success');
      } else if (isPolicyChange && review?.policy_change_id) {
        await approvePolicyChange(String(review.policy_change_id), notes);
        showNotification('Policy change approved and applied', 'success');
      } else {
        await approveReview(reviewId, notes);
        showNotification('Review approved successfully', 'success');
      }
      loadReviews();
    } catch {
      showNotification('Failed to approve', 'error');
    }
  };

  const handleReject = async (reviewId: string, notes: string) => {
    try {
      const isModification = reviewId.startsWith('MOD-');
      const review = reviews.find(r => r.id === reviewId);
      const isPolicyChange = review?.request_type?.startsWith('policy_');
      if (isModification) {
        await rejectRuleModification(reviewId, notes);
        showNotification('Rule modification rejected', 'warning');
      } else if (isPolicyChange && review?.policy_change_id) {
        await rejectPolicyChange(String(review.policy_change_id), notes);
        showNotification('Policy change rejected', 'warning');
      } else {
        await rejectReview(reviewId, notes);
        showNotification('Review rejected', 'warning');
      }
      loadReviews();
    } catch {
      showNotification('Failed to reject', 'error');
    }
  };

  const exportableTypes = new Set(['new_rule', 'modify_rule', 'delete_rule']);

  const handleExportRequest = (review: ReviewRequest) => {
    const headers = ['Request ID', 'Rule ID', 'Request Type', 'Application', 'Source', 'Destination', 'Ports', 'Environment', 'Status', 'Requestor', 'Submitted At', 'Reviewer', 'Comments'];
    const row = [
      review.id, review.rule_id, review.request_type.replace(/_/g, ' '),
      review.rule_summary?.application || '', review.rule_summary?.source || '',
      review.rule_summary?.destination || '', review.rule_summary?.ports || '',
      review.rule_summary?.environment || '', review.status, review.requestor,
      review.submitted_at || '', review.reviewer || '', review.comments || '',
    ];
    if (review.delta) {
      headers.push('Added', 'Removed', 'Changed');
      row.push(
        Object.entries(review.delta.added).map(([k, v]) => `${k.startsWith('group:') ? `Group Members (${k.slice(6)})` : k}: ${v.join(', ')}`).join('; '),
        Object.entries(review.delta.removed).map(([k, v]) => `${k.startsWith('group:') ? `Group Members (${k.slice(6)})` : k}: ${v.join(', ')}`).join('; '),
        Object.entries(review.delta.changed).map(([k, v]) => `${k.startsWith('group:') ? `Group Members (${k.slice(6)})` : k}: ${v.from} -> ${v.to}`).join('; '),
      );
    }
    const csvContent = [headers, row].map(r => r.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `request-${review.request_type}-${review.rule_id}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification('Request exported successfully', 'success');
  };

  const columns: Column<ReviewRequest>[] = [
    { key: 'rule_id', header: 'Rule ID', sortable: true, width: '120px' },
    {
      key: 'request_type', header: 'Type', sortable: true, width: '120px',
      render: (_, row) => (
        <span className={`text-xs capitalize px-1.5 py-0.5 rounded ${
          row.request_type === 'new_rule' ? 'bg-green-50 text-green-700' :
          row.request_type === 'modify_rule' ? 'bg-amber-50 text-amber-700' :
          row.request_type === 'delete_rule' ? 'bg-red-50 text-red-700' :
          row.request_type === 'group_policy_change' ? 'bg-purple-50 text-purple-700' :
          row.request_type === 'policy_add' ? 'bg-teal-50 text-teal-700' :
          row.request_type === 'policy_modify' ? 'bg-indigo-50 text-indigo-700' :
          row.request_type === 'policy_delete' ? 'bg-rose-50 text-rose-700' :
          'bg-gray-50 text-gray-700'
        }`}>{row.request_type.replace(/_/g, ' ')}</span>
      ),
    },
    {
      key: 'rule_summary', header: 'Application', sortable: false, width: '120px',
      render: (_, row) => <span className="text-xs">{row.rule_summary?.application || 'N/A'}</span>,
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
      key: '_actions', header: 'Actions', sortable: false, width: '140px',
      render: (_, row) => (
        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
          <button
            onClick={() => approvalModal.open(row)}
            className={`px-2 py-1 text-xs font-medium rounded ${
              row.status === 'Pending'
                ? 'text-blue-700 bg-blue-50 hover:bg-blue-100'
                : 'text-gray-600 bg-gray-50 hover:bg-gray-100'
            }`}
          >
            {row.status === 'Pending' ? 'Review' : 'View'}
          </button>
          {exportableTypes.has(row.request_type) && (
            <button
              onClick={() => handleExportRequest(row)}
              className="px-2 py-1 text-xs font-medium text-teal-700 bg-teal-50 rounded hover:bg-teal-100"
            >
              Export
            </button>
          )}
        </div>
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

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review & Approval</h1>
          <p className="text-sm text-gray-500 mt-1">Review migration and firewall rule requests. Export new/modify/remove requests from the table below.</p>
        </div>
        <div className="flex items-center gap-3">
          {!moduleContext && (
            <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
              value={selectedModule} onChange={e => setSelectedModule(e.target.value)}>
              <option value="">All Modules</option>
              <option value="firewall-management">Firewall Management</option>
              <option value="design-studio">Design Studio</option>
              <option value="migration-studio">Migration Studio</option>
              <option value="org-admin">Policy Matrix (Org Admin)</option>
            </select>
          )}
          <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 bg-white"
            value={selectedEnv} onChange={e => setSelectedEnv(e.target.value)}>
            <option value="">All Environments</option>
            <option value="Production">Production</option>
            <option value="Non-Production">Non-Production</option>
            <option value="Pre-Production">Pre-Production</option>
          </select>
          <span className="text-xs text-gray-500">Export is available for Add / Modify / Remove requests</span>
        </div>
      </div>

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
              searchPlaceholder="Search by rule ID, app, source, destination, requestor..."
              searchFields={['id', 'rule_id', 'request_type', 'requestor']}
              onRowClick={(row) => approvalModal.open(row)}
              emptyMessage="No review requests found. Select rules for migration in the Migration to NGDC page and submit for review."
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
