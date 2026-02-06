import { useEffect, useMemo, useState } from 'react';
import { CheckCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { accountsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

function isManager(user) {
  return user?.role === 'admin' || user?.role === 'manager';
}

export default function AccountRequests() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);

  const canAccept = useMemo(() => isManager(user), [user]);

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

  const handleAccept = async (requestId) => {
    setActingId(requestId);
    try {
      await accountsAPI.mulesoftAccept(requestId);
      toast.success('Request accepted by MuleSoft');
      await loadRequests();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to accept request';
      toast.error(typeof message === 'string' ? message : 'Failed to accept request');
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Account Requests</h1>
          <p className="text-sm text-gray-500">Requests sent to MuleSoft must be accepted before accounts are created.</p>
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
                  {canAccept && (
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  )}
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
                      {canAccept && (
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => handleAccept(item.id)}
                            className="btn-primary inline-flex items-center gap-2"
                            disabled={!pending || actingId === item.id}
                            title={pending ? 'Accept in MuleSoft (simulated)' : 'Only pending requests can be accepted'}
                          >
                            <CheckCircleIcon className="w-4 h-4" />
                            {actingId === item.id ? 'Accepting...' : 'Accept'}
                          </button>
                        </td>
                      )}
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

