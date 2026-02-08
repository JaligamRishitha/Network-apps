import React, { useEffect, useState } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { accountsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function AccountRequestsStatus() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);

  // Helper to deduplicate arrays by ID
  const deduplicateById = (items) => {
    const seen = new Set();
    return items.filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  };

  const loadRequests = async () => {
    setLoading(true);
    try {
      const response = await accountsAPI.listRequests({ page_size: 50 });
      setItems(deduplicateById(response.data.items || []));
    } catch (error) {
      console.error('Failed to load requests:', error);
      toast.error('Failed to load requests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200';
      case 'APPROVED':
        return 'bg-green-50 text-green-800 border-green-200';
      case 'COMPLETED':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'REJECTED':
        return 'bg-red-50 text-red-800 border-red-200';
      case 'FAILED':
        return 'bg-red-50 text-red-800 border-red-200';
      default:
        return 'bg-gray-50 text-gray-800 border-gray-200';
    }
  };

  const getIntegrationStatusColor = (status) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'VALIDATED':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Account Creation Requests</h1>
          <p className="text-sm text-gray-500">Track account creation requests sent through MuleSoft</p>
        </div>
        <button type="button" onClick={loadRequests} className="btn-outline flex items-center gap-2">
          <ArrowPathIcon className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-6 text-sm text-gray-500">Loading requests...</div>
        ) : items.length === 0 ? (
          <div className="p-6 text-center text-sm text-gray-500">
            <p className="text-lg font-medium mb-2">No requests found</p>
            <p>Create a new account to see it appear here with tracking information.</p>
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Request Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Integration Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MuleSoft ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => {
                  const isExpanded = expandedRow === item.id;
                  return (
                    <React.Fragment key={`request-${item.id}`}>
                      <tr
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setExpandedRow(isExpanded ? null : item.id)}
                      >
                        <td className="px-4 py-3 text-sm text-gray-700">
                          <div className="flex items-center gap-2">
                            <svg
                              className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                            {item.id}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-blue-600">{item.name}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium border ${getStatusColor(item.status)}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${getIntegrationStatusColor(item.integration_status)}`}>
                            {item.integration_status || 'PENDING'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 font-mono text-xs">
                          {item.mulesoft_transaction_id ? (
                            <span title={item.mulesoft_transaction_id}>
                              {item.mulesoft_transaction_id.substring(0, 20)}...
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan="6" className="px-4 py-4 bg-gray-50">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="font-medium text-gray-700">Correlation ID:</span>
                                <div className="mt-1 font-mono text-xs text-gray-600 break-all">
                                  {item.correlation_id || '-'}
                                </div>
                              </div>
                              <div>
                                <span className="font-medium text-gray-700">Full MuleSoft Transaction ID:</span>
                                <div className="mt-1 font-mono text-xs text-gray-600 break-all">
                                  {item.mulesoft_transaction_id || '-'}
                                </div>
                              </div>
                              {item.error_message && (
                                <div className="col-span-2">
                                  <span className="font-medium text-red-700">Error Message:</span>
                                  <div className="mt-1 text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
                                    {item.error_message}
                                  </div>
                                </div>
                              )}
                              <div>
                                <span className="font-medium text-gray-700">Requested By ID:</span>
                                <div className="mt-1 text-gray-600">{item.requested_by_id || '-'}</div>
                              </div>
                              <div>
                                <span className="font-medium text-gray-700">Approved By ID:</span>
                                <div className="mt-1 text-gray-600">{item.approved_by_id || 'Not yet approved'}</div>
                              </div>
                              <div>
                                <span className="font-medium text-gray-700">Auto Approved:</span>
                                <div className="mt-1 text-gray-600">{item.auto_approved ? 'Yes' : 'No'}</div>
                              </div>
                              {item.created_account_id && (
                                <div className="col-span-2">
                                  <span className="font-medium text-green-700">Account Created - ID:</span>
                                  <div className="mt-1 text-green-600 font-medium">{item.created_account_id}</div>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
