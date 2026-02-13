import { useEffect, useState } from 'react';
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { accountsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function AccountRequests() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const response = await accountsAPI.listRequests({ page_size: 50 });
      setItems(response.data.items || []);
    } catch (error) {
      console.error('Failed to load account requests:', error);
      toast.error('Failed to load requests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleApprove = async (requestId) => {
    setActingId(requestId);
    try {
      await accountsAPI.approveRequest(requestId);
      toast.success('Request approved — account created');
      await loadRequests();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to approve request';
      toast.error(typeof message === 'string' ? message : 'Failed to approve request');
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (requestId) => {
    setActingId(requestId);
    try {
      await accountsAPI.rejectRequest(requestId);
      toast.success('Request rejected');
      await loadRequests();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to reject request';
      toast.error(typeof message === 'string' ? message : 'Failed to reject request');
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Account Requests</h1>
          <p className="text-sm text-gray-500">Review account creation requests — approve to create the account or reject to decline.</p>
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
          <div className="p-6 text-sm text-gray-500">No requests found.</div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Integration</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ServiceNow</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requested By</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => {
                  const pending = item.status === 'PENDING';
                  return (
                    <tr key={`acct-req-${item.id}`} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-700">{item.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-sf-blue-600">{item.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{item.status}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{item.integration_status || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{item.servicenow_ticket_id || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{item.requested_by_id}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {pending ? (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => handleApprove(item.id)}
                              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                              disabled={actingId === item.id}
                            >
                              <CheckCircleIcon className="w-4 h-4" />
                              {actingId === item.id ? 'Processing...' : 'Approve'}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleReject(item.id)}
                              className="inline-flex items-center gap-1 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                              disabled={actingId === item.id}
                            >
                              <XCircleIcon className="w-4 h-4" />
                              {actingId === item.id ? 'Processing...' : 'Reject'}
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">{item.status}</span>
                        )}
                      </td>
                    </tr>
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
