import { useState } from 'react';
import { ChartBarSquareIcon, UserGroupIcon, BuildingOfficeIcon } from '@heroicons/react/24/solid';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import SendEmailModal from '../components/SendEmailModal';
import AssignLabelModal from '../components/AssignLabelModal';
import { leadsAPI, contactsAPI, accountsAPI, opportunitiesAPI } from '../services/api';
import toast from 'react-hot-toast';

const subNavItems = [
  { key: 'leads', label: 'Leads' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'accounts', label: 'Accounts' },
  { key: 'opportunities', label: 'Opportunities' },
  { key: 'products', label: 'Products' },
  { key: 'pricebooks', label: 'Price Books' },
  { key: 'calendar', label: 'Calendar' },
  { key: 'analytics', label: 'Analytics' },
];

const leadColumns = [
  {
    key: 'full_name',
    label: 'Name',
    render: (item) => item.full_name || `${item.first_name || ''} ${item.last_name}`.trim(),
  },
  { key: 'title', label: 'Title' },
  { key: 'company', label: 'Company' },
  { key: 'phone', label: 'Phone' },
  { key: 'email', label: 'Email' },
  { key: 'status', label: 'Lead Status' },
  { key: 'owner_alias', label: 'Owner Alias' },
];

const contactColumns = [
  {
    key: 'full_name',
    label: 'Name',
    render: (item) => item.full_name || `${item.first_name || ''} ${item.last_name}`.trim(),
  },
  { key: 'account_name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'email', label: 'Email' },
  { key: 'owner_alias', label: 'Contact Owner Alias' },
];

const accountColumns = [
  { key: 'name', label: 'Account Name' },
  { key: 'phone', label: 'Phone' },
  { key: 'industry', label: 'Industry' },
  { key: 'owner_alias', label: 'Account Owner Alias' },
];

const opportunityColumns = [
  { key: 'name', label: 'Opportunity Name' },
  { key: 'account_name', label: 'Account Name' },
  {
    key: 'amount',
    label: 'Amount',
    render: (item) => item.amount ? `$${item.amount.toLocaleString()}` : '-',
  },
  { key: 'stage', label: 'Stage' },
  {
    key: 'close_date',
    label: 'Close Date',
    render: (item) => item.close_date ? new Date(item.close_date).toLocaleDateString() : '-',
  },
  { key: 'owner_alias', label: 'Owner Alias' },
];

export default function Sales() {
  const [activeTab, setActiveTab] = useState('leads');
  const [showImportModal, setShowImportModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [importObjectType, setImportObjectType] = useState('lead');

  const handleImport = (objectType) => {
    setImportObjectType(objectType);
    setShowImportModal(true);
  };

  const handleSendEmail = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    setSelectedRecords(records);
    setShowEmailModal(true);
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleChangeOwner = (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    // In a real app, this would open an owner selection modal
    toast.success(`Change owner for ${selectedIds.length} record(s)`);
  };

  const handleAddToCampaign = (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    toast.success(`Added ${selectedIds.length} record(s) to campaign`);
  };

  const handleImportSuccess = () => {
    window.location.reload();
  };

  const getImportApi = () => {
    switch (importObjectType) {
      case 'lead': return leadsAPI;
      case 'contact': return contactsAPI;
      case 'account': return accountsAPI;
      case 'opportunity': return opportunitiesAPI;
      default: return leadsAPI;
    }
  };

  const leadActions = [
    { label: 'Import', onClick: () => handleImport('lead') },
    { label: 'Add to Campaign', onClick: handleAddToCampaign, requiresSelection: true },
    { label: 'Send Email', onClick: handleSendEmail, requiresSelection: true },
    { label: 'Change Owner', onClick: handleChangeOwner, requiresSelection: true },
  ];

  const contactActions = [
    { label: 'Import', onClick: () => handleImport('contact') },
    { label: 'Send Email', onClick: handleSendEmail, requiresSelection: true },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const accountActions = [
    { label: 'Import', onClick: () => handleImport('account') },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const opportunityActions = [
    { label: 'Import', onClick: () => handleImport('opportunity') },
    { label: 'Change Owner', onClick: handleChangeOwner, requiresSelection: true },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'leads':
        return (
          <ObjectListPage
            objectType="lead"
            objectLabel="Lead"
            columns={leadColumns}
            api={leadsAPI}
            actions={leadActions}
            icon={<ChartBarSquareIcon className="w-5 h-5 text-white" />}
            iconColor="bg-green-500"
            emptyTitle="Focus on the right leads"
            emptyDescription="Leads are potential customers and deals. Track progress and see which ones are most likely to close."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'contacts':
        return (
          <ObjectListPage
            objectType="contact"
            objectLabel="Contact"
            columns={contactColumns}
            api={contactsAPI}
            actions={contactActions}
            icon={<UserGroupIcon className="w-5 h-5 text-white" />}
            iconColor="bg-purple-500"
            emptyTitle="Top sellers add their contacts first"
            emptyDescription="It's the fastest way to win more deals."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'accounts':
        return (
          <ObjectListPage
            objectType="account"
            objectLabel="Account"
            columns={accountColumns}
            api={accountsAPI}
            actions={accountActions}
            icon={<BuildingOfficeIcon className="w-5 h-5 text-white" />}
            iconColor="bg-indigo-500"
            emptyTitle="Accounts show where your contacts work"
            emptyDescription="Improve your reporting and deal tracking with accounts."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'opportunities':
        return (
          <ObjectListPage
            objectType="opportunity"
            objectLabel="Opportunity"
            columns={opportunityColumns}
            api={opportunitiesAPI}
            actions={opportunityActions}
            icon={<ChartBarSquareIcon className="w-5 h-5 text-white" />}
            iconColor="bg-yellow-500"
            emptyTitle="Track your deals"
            emptyDescription="Create opportunities to track potential revenue."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      default:
        return (
          <div className="p-6">
            <div className="card p-12 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-500">This feature is under development.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="px-6 pt-6 pb-0">
        <h1 className="text-2xl font-bold text-gray-900">Sales</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6 overflow-x-auto">
            {subNavItems.map((item) => (
              <button
                type="button"
                key={item.key}
                onClick={() => setActiveTab(item.key)}
                className={`py-2 px-1 text-sm font-medium whitespace-nowrap flex items-center ${
                  activeTab === item.key
                    ? 'border-b-2 border-sf-blue-500 text-sf-blue-500'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {item.label}
                <ChevronDownIcon className="w-3 h-3 ml-1" />
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      {renderContent()}

      {/* Import Modal */}
      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        objectType={importObjectType}
        api={getImportApi()}
        onSuccess={handleImportSuccess}
      />

      {/* Send Email Modal */}
      <SendEmailModal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
        recipients={selectedRecords}
      />

      {/* Assign Label Modal */}
      <AssignLabelModal
        isOpen={showLabelModal}
        onClose={() => setShowLabelModal(false)}
        selectedCount={selectedRecords.length}
        onAssign={(labels) => {
          console.log('Assigned labels:', labels);
        }}
      />
    </div>
  );
}
