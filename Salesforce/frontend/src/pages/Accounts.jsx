import { useState } from 'react';
import { BuildingOfficeIcon, ChevronDownIcon } from '@heroicons/react/24/solid';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import AssignLabelModal from '../components/AssignLabelModal';
import AccountRequestsStatus from './AccountRequestsStatus';
import { accountsAPI } from '../services/api';
import toast from 'react-hot-toast';

const columns = [
  { key: 'name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'industry', label: 'Industry' },
  { key: 'website', label: 'Website' },
  { key: 'owner_alias', label: 'Owner' },
];

export default function Accounts() {
  const [showImportModal, setShowImportModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [activeTab, setActiveTab] = useState('accounts');

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
        </>
      )}

      {activeTab === 'requests' && <AccountRequestsStatus />}
    </>
  );
}
