import React, { useState, useEffect } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { accountsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function MuleSoftIntegrationTab() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    loadRequests();
    const interval = setInterval(loadRequests, 5000);
    return () => clearInterval(interval);
  }, []);

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
    try {
      const response = await accountsAPI.listRequests({ page_size: 50 });
      setRequests(deduplicateById(response.data.items || []));
      setLoading(false);
    } catch (error) {
      console.error('Failed to load requests:', error);
      toast.error('Failed to load MuleSoft requests');
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      VALIDATED: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      FAILED: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      PENDING: '⏳',
      VALIDATED: '✔',
      COMPLETED: '✅',
      FAILED: '❌'
    };
    return icons[status] || '•';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-8 text-gray-500">Loading MuleSoft integration data...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">MuleSoft Integration Status</h2>
          <p className="text-sm text-gray-500">Track account creation requests and integration status</p>
        </div>
        <button
          type="button"
          onClick={loadRequests}
          className="btn-outline flex items-center gap-2"
        >
          <ArrowPathIcon className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
          <div className="text-2xl font-bold text-yellow-600">
            {requests.filter(r => r.integration_status === 'PENDING').length}
          </div>
          <div className="text-sm text-yellow-700">Pending</div>
        </div>
        <div className="bg-blue-50 p-4 rounded border border-blue-200">
          <div className="text-2xl font-bold text-blue-600">
            {requests.filter(r => r.integration_status === 'VALIDATED').length}
          </div>
          <div className="text-sm text-blue-700">Validated</div>
        </div>
        <div className="bg-green-50 p-4 rounded border border-green-200">
          <div className="text-2xl font-bold text-green-600">
            {requests.filter(r => r.integration_status === 'COMPLETED').length}
          </div>
          <div className="text-sm text-green-700">Completed</div>
        </div>
        <div className="bg-red-50 p-4 rounded border border-red-200">
          <div className="text-2xl font-bold text-red-600">
            {requests.filter(r => r.integration_status === 'FAILED').length}
          </div>
          <div className="text-sm text-red-700">Failed</div>
        </div>
      </div>

      {/* Requests Table */}
      <div className="card overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Account Name</th>
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Integration</th>
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">MuleSoft ID</th>
              <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
            </tr>
          </thead>
          <tbody>
            {requests.map(req => {
              const isExpanded = expandedRow === req.id;
              return (
                <React.Fragment key={`mulesoft-${req.id}`}>
                  <tr
                    className="border-t hover:bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedRow(isExpanded ? null : req.id)}
                  >
                    <td className="p-3 text-sm">
                      <div className="flex items-center gap-2">
                        <svg
                          className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        {req.id}
                      </div>
                    </td>
                    <td className="p-3 text-sm font-medium text-blue-600">{req.name || '-'}</td>
                    <td className="p-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(req.status)}`}>
                        {getStatusIcon(req.status)} {req.status}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(req.integration_status)}`}>
                        {req.integration_status || 'PENDING'}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs text-gray-600">
                      {req.mulesoft_transaction_id ? req.mulesoft_transaction_id.substring(0, 12) + '...' : '-'}
                    </td>
                    <td className="p-3 text-xs text-gray-500">{new Date(req.created_at).toLocaleString()}</td>
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td colSpan="6" className="px-4 py-4 bg-gray-50">
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-gray-700">Correlation ID:</span>
                            <div className="mt-1 font-mono text-xs text-gray-600 break-all">
                              {req.correlation_id || '-'}
                            </div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Full MuleSoft ID:</span>
                            <div className="mt-1 font-mono text-xs text-gray-600 break-all">
                              {req.mulesoft_transaction_id || '-'}
                            </div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Requested By:</span>
                            <div className="mt-1 text-gray-600">User ID: {req.requested_by_id || '-'}</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Approved By:</span>
                            <div className="mt-1 text-gray-600">
                              {req.approved_by_id ? `User ID: ${req.approved_by_id}` : 'Not yet approved'}
                            </div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Auto Approved:</span>
                            <div className="mt-1 text-gray-600">{req.auto_approved ? 'Yes' : 'No'}</div>
                          </div>
                          {req.error_message && (
                            <div className="col-span-3">
                              <span className="font-medium text-red-700">Error:</span>
                              <div className="mt-1 text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
                                {req.error_message}
                              </div>
                            </div>
                          )}
                          {req.created_account_id && (
                            <div className="col-span-3">
                              <span className="font-medium text-green-700">Created Account ID:</span>
                              <div className="mt-1 text-green-600 font-medium">{req.created_account_id}</div>
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

        {requests.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No MuleSoft requests yet. Create a new account to start tracking.
          </div>
        )}
      </div>
    </div>
  );
}
