import { useState, useEffect } from 'react';
import { BuildingOfficeIcon, ChevronDownIcon, UserPlusIcon, XMarkIcon, ArrowPathIcon, CheckCircleIcon, ClockIcon, XCircleIcon } from '@heroicons/react/24/solid';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import AssignLabelModal from '../components/AssignLabelModal';
import AccountRequestsStatus from './AccountRequestsStatus';
import { accountsAPI, clientUsersAPI } from '../services/api';
import toast from 'react-hot-toast';

const statusStyles = {
  COMPLETED: 'bg-green-100 text-green-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  FAILED: 'bg-red-100 text-red-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
};

const statusLabels = {
  COMPLETED: 'Approved',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  FAILED: 'Failed',
  PENDING: 'Pending',
};

const columns = [
  { key: 'name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'industry', label: 'Industry' },
  {
    key: 'request_status',
    label: 'Status',
    render: (item) => {
      const status = item.request_status || 'COMPLETED';
      return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
          {statusLabels[status] || status}
        </span>
      );
    },
  },
  {
    key: 'actions',
    label: 'Actions',
    render: (item, extraProps) => {
      const status = item.request_status || 'COMPLETED';
      if (status !== 'COMPLETED' && status !== 'APPROVED') return null;
      return (
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (extraProps?.onCreateUser) extraProps.onCreateUser(item);
          }}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
        >
          <UserPlusIcon className="w-3.5 h-3.5" />
          Create User
        </button>
      );
    },
  },
];

function CreateUserModal({ isOpen, onClose, account }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen || !account) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) {
      toast.error('All fields are required');
      return;
    }
    setLoading(true);
    try {
      const res = await clientUsersAPI.create({
        account_id: account.id,
        name: name.trim(),
        email: email.trim(),
        password: password.trim(),
      });
      const sn = res.data.servicenow_ticket_id;
      toast.success(`User created! ServiceNow ticket: ${sn || 'pending'}`);
      setName('');
      setEmail('');
      setPassword('');
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create user';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Create Client User — {account.name}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Full Name"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="user@example.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Initial password"
              required
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ClientUsersPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterAccount, setFilterAccount] = useState('');

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await clientUsersAPI.list();
      setUsers(res.data || []);
    } catch (err) {
      console.error('Failed to load client users:', err);
      toast.error('Failed to load client users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const filteredUsers = filterAccount
    ? users.filter((u) => (u.account_name || '').toLowerCase().includes(filterAccount.toLowerCase()))
    : users;

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Client Portal Users</h2>
          <p className="text-sm text-gray-500">Users created under accounts for client portal access</p>
        </div>
        <button type="button" onClick={loadUsers} className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
          <ArrowPathIcon className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by account name..."
          value={filterAccount}
          onChange={(e) => setFilterAccount(e.target.value)}
          className="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 text-sm text-gray-500">Loading client users...</div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-6 text-center text-sm text-gray-500">
            <p className="text-lg font-medium mb-2">No client users found</p>
            <p>Create a user from the Accounts tab using the "Create User" button.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ServiceNow Ticket</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                  <td className="px-4 py-3 text-sm text-indigo-600 font-medium">{user.account_name || `Account #${user.account_id}`}</td>
                  <td className="px-4 py-3 text-sm">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircleIcon className="w-3.5 h-3.5" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        <ClockIcon className="w-3.5 h-3.5" />
                        Pending Activation
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 font-mono text-xs">
                    {user.servicenow_ticket_id || <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {user.created_at ? new Date(user.created_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Summary */}
      {!loading && filteredUsers.length > 0 && (
        <div className="mt-4 flex gap-6 text-sm text-gray-600">
          <span>Total: <strong>{filteredUsers.length}</strong></span>
          <span className="text-green-700">Active: <strong>{filteredUsers.filter((u) => u.is_active).length}</strong></span>
          <span className="text-yellow-700">Pending: <strong>{filteredUsers.filter((u) => !u.is_active).length}</strong></span>
        </div>
      )}
    </div>
  );
}

export default function Accounts() {
  const [showImportModal, setShowImportModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [activeTab, setActiveTab] = useState('accounts');
  const [createUserAccount, setCreateUserAccount] = useState(null);

  const handleImport = () => {
    setShowImportModal(true);
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one account');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleImportSuccess = () => {
    window.location.reload();
  };

  const actions = [
    {
      label: 'Import',
      onClick: handleImport,
    },
    {
      label: 'Assign Label',
      onClick: handleAssignLabel,
      requiresSelection: true,
    },
  ];

  return (
    <>
      <div className="p-6">
        {/* Page Header */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
          <div className="mt-2 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                type="button"
                onClick={() => setActiveTab('accounts')}
                className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'accounts'
                    ? 'border-sf-blue-500 text-sf-blue-500'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Accounts
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('requests')}
                className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'requests'
                    ? 'border-sf-blue-500 text-sf-blue-500'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Requests
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('client-users')}
                className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'client-users'
                    ? 'border-sf-blue-500 text-sf-blue-500'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Client Users
              </button>
            </nav>
          </div>
        </div>
      </div>

      {activeTab === 'accounts' && (
        <>
          <ObjectListPage
            objectType="account"
            objectLabel="Account"
            columns={columns}
            api={accountsAPI}
            actions={actions}
            icon={<BuildingOfficeIcon className="w-5 h-5 text-white" />}
            iconColor="bg-indigo-500"
            emptyTitle="Accounts show where your contacts work"
            emptyDescription="Improve your reporting and deal tracking with accounts."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
            rowExtraProps={{ onCreateUser: (account) => setCreateUserAccount(account) }}
          />

          <ImportModal
            isOpen={showImportModal}
            onClose={() => setShowImportModal(false)}
            objectType="account"
            api={accountsAPI}
            onSuccess={handleImportSuccess}
          />

          <AssignLabelModal
            isOpen={showLabelModal}
            onClose={() => setShowLabelModal(false)}
            selectedCount={selectedRecords.length}
            onAssign={(labels) => {
              console.log('Assigned labels:', labels);
            }}
          />

          <CreateUserModal
            isOpen={!!createUserAccount}
            onClose={() => setCreateUserAccount(null)}
            account={createUserAccount}
          />
        </>
      )}

      {activeTab === 'requests' && <AccountRequestsStatus />}

      {activeTab === 'client-users' && <ClientUsersPanel />}
    </>
  );
}
