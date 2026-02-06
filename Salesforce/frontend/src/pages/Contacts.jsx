import { useState, useRef } from 'react';
import { UserGroupIcon } from '@heroicons/react/24/solid';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import SendEmailModal from '../components/SendEmailModal';
import AssignLabelModal from '../components/AssignLabelModal';
import { contactsAPI } from '../services/api';
import toast from 'react-hot-toast';

const columns = [
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

export default function Contacts() {
  const [showImportModal, setShowImportModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const listRef = useRef(null);

  const handleImport = () => {
    setShowImportModal(true);
  };

  const handleAddToCampaign = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one contact');
      return;
    }
    // In a real app, this would open a campaign selection modal
    toast.success(`Added ${selectedIds.length} contact(s) to campaign`);
  };

  const handleSendEmail = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one contact');
      return;
    }
    setSelectedRecords(records);
    setShowEmailModal(true);
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one contact');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleImportSuccess = () => {
    // Refresh the list by triggering a reload
    // This will be handled by the ObjectListPage when it remounts
    window.location.reload();
  };

  const actions = [
    {
      label: 'Import',
      onClick: handleImport,
    },
    {
      label: 'Add to Campaign',
      onClick: handleAddToCampaign,
      requiresSelection: true,
    },
    {
      label: 'Send Email',
      onClick: handleSendEmail,
      requiresSelection: true,
    },
    {
      label: 'Assign Label',
      onClick: handleAssignLabel,
      requiresSelection: true,
    },
  ];

  return (
    <>
      <ObjectListPage
        ref={listRef}
        objectType="contact"
        objectLabel="Contact"
        columns={columns}
        api={contactsAPI}
        actions={actions}
        icon={<UserGroupIcon className="w-5 h-5 text-white" />}
        iconColor="bg-purple-500"
        emptyTitle="Top sellers add their contacts first"
        emptyDescription="It's the fastest way to win more deals."
        onSelectionChange={(ids, records) => setSelectedRecords(records)}
      />

      {/* Import Modal */}
      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        objectType="contact"
        api={contactsAPI}
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
          // In a real app, this would save the labels to the contacts
          console.log('Assigned labels:', labels);
        }}
      />
    </>
  );
}
