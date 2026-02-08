import { useState, useEffect } from 'react';
import { DocumentTextIcon, UserGroupIcon, BuildingOfficeIcon, CalendarDaysIcon, WrenchScrewdriverIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/solid';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import ObjectListPage from '../components/ObjectListPage';
import ImportModal from '../components/ImportModal';
import AssignLabelModal from '../components/AssignLabelModal';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import { casesAPI, contactsAPI, accountsAPI, serviceAPI } from '../services/api';
import toast from 'react-hot-toast';

const subNavItems = [
  { key: 'cases', label: 'Cases' },
  { key: 'appointments', label: 'Appointments' },
  // { key: 'workorders', label: 'Work Orders' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'accounts', label: 'Accounts' },
  { key: 'quicktext', label: 'Quick Text' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'knowledge', label: 'Knowledge' },
];

const caseColumns = [
  { key: 'case_number', label: 'Case Number' },
  { key: 'subject', label: 'Subject' },
  {
    key: 'priority',
    label: 'Priority',
    render: (item) => (
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        item.priority === 'Critical' ? 'bg-red-100 text-red-800' :
        item.priority === 'High' ? 'bg-orange-100 text-orange-800' :
        item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
        'bg-green-100 text-green-800'
      }`}>
        {item.priority}
      </span>
    ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (item) => (
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        item.status === 'Escalated' ? 'bg-red-100 text-red-800' :
        item.status === 'Closed' ? 'bg-gray-100 text-gray-800' :
        item.status === 'Working' ? 'bg-blue-100 text-blue-800' :
        'bg-green-100 text-green-800'
      }`}>
        {item.status}
      </span>
    ),
  },
  {
    key: 'created_at',
    label: 'Date/Time Opened',
    render: (item) => new Date(item.created_at).toLocaleString(),
  },
  { key: 'owner_alias', label: 'Case Owner Alias' },
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

export default function Service() {
  const [activeTab, setActiveTab] = useState('cases');
  const [showImportModal, setShowImportModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [importObjectType, setImportObjectType] = useState('case');

  // Service Appointments state
  const [appointments, setAppointments] = useState([]);
  const [loadingAppointments, setLoadingAppointments] = useState(false);
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [accounts, setAccounts] = useState([]);

  // Work Orders state
  const [workOrders, setWorkOrders] = useState([]);
  const [loadingWorkOrders, setLoadingWorkOrders] = useState(false);
  const [showWorkOrderModal, setShowWorkOrderModal] = useState(false);

  // Load appointments when tab is active
  useEffect(() => {
    if (activeTab === 'appointments') {
      loadAppointments();
      loadAccounts();
    } else if (activeTab === 'workorders') {
      loadWorkOrders();
      loadAccounts();
    }
  }, [activeTab]);

  // Helper to deduplicate arrays by ID
  const deduplicateById = (items) => {
    const seen = new Set();
    return (items || []).filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  };

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.list({ page_size: 100 });
      setAccounts(deduplicateById(response.data.items));
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const loadAppointments = async () => {
    setLoadingAppointments(true);
    try {
      const response = await serviceAPI.listAppointments({ page_size: 50 });
      setAppointments(deduplicateById(response.data?.items || []));
    } catch (error) {
      console.error('Failed to load appointments:', error);
      // Don't show error toast - endpoint might not be available on server
    } finally {
      setLoadingAppointments(false);
    }
  };

  const loadWorkOrders = async () => {
    setLoadingWorkOrders(true);
    try {
      const response = await serviceAPI.listWorkOrders({ page_size: 50 });
      setWorkOrders(deduplicateById(response.data?.items));
    } catch (error) {
      console.error('Failed to load work orders:', error);
      // Don't show error toast - endpoint might not exist yet
    } finally {
      setLoadingWorkOrders(false);
    }
  };

  const handleImport = (objectType) => {
    setImportObjectType(objectType);
    setShowImportModal(true);
  };

  const handleChangeOwner = (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    toast.success(`Change owner for ${selectedIds.length} record(s)`);
  };

  const handleMergeCases = (selectedIds) => {
    if (selectedIds.length < 2) {
      toast.error('Please select at least 2 cases to merge');
      return;
    }
    const confirmMerge = window.confirm(
      `Merge ${selectedIds.length} cases? The first selected case will be the master.`
    );
    if (confirmMerge) {
      casesAPI.merge(selectedIds, selectedIds[0])
        .then(() => {
          toast.success('Cases merged successfully');
          window.location.reload();
        })
        .catch(() => {
          toast.error('Failed to merge cases');
        });
    }
  };

  const handleEscalate = async (selectedIds) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one case');
      return;
    }
    try {
      for (const id of selectedIds) {
        await casesAPI.escalate(id);
      }
      toast.success(`Escalated ${selectedIds.length} case(s)`);
      window.location.reload();
    } catch (error) {
      toast.error('Failed to escalate cases');
    }
  };

  const handleAssignLabel = (selectedIds, records) => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one record');
      return;
    }
    setSelectedRecords(records);
    setShowLabelModal(true);
  };

  const handleImportSuccess = () => {
    window.location.reload();
  };

  const getImportApi = () => {
    switch (importObjectType) {
      case 'case': return casesAPI;
      case 'contact': return contactsAPI;
      case 'account': return accountsAPI;
      default: return casesAPI;
    }
  };

  const caseActions = [
    { label: 'Change Owner', onClick: handleChangeOwner, requiresSelection: true },
    { label: 'Merge Cases', onClick: handleMergeCases, requiresSelection: true },
    { label: 'Escalate', onClick: handleEscalate, requiresSelection: true },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const contactActions = [
    { label: 'Import', onClick: () => handleImport('contact') },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  const accountActions = [
    { label: 'Import', onClick: () => handleImport('account') },
    { label: 'Assign Label', onClick: handleAssignLabel, requiresSelection: true },
  ];

  // Service Appointment Form Component
  const AppointmentModal = () => {
    const [formData, setFormData] = useState({
      account_id: '',
      subject: '',
      description: '',
      appointment_type: 'Field Service',
      scheduled_start: '',
      scheduled_end: '',
      priority: 'Normal',
      location: '',
    });
    const [parts, setParts] = useState([]);
    const [newPartName, setNewPartName] = useState('');
    const [newPartQty, setNewPartQty] = useState('');
    const [newPartUnit, setNewPartUnit] = useState('units');
    const [submitting, setSubmitting] = useState(false);

    const unitOptions = ['units', 'meters', 'pieces', 'kits', 'sets', 'rolls', 'boxes', 'kg', 'liters'];

    const handleAddPart = () => {
      if (!newPartName.trim()) {
        toast.error('Enter part/material name');
        return;
      }
      if (!newPartQty || parseInt(newPartQty) <= 0) {
        toast.error('Enter valid quantity');
        return;
      }
      setParts([...parts, { name: newPartName.trim(), quantity: parseInt(newPartQty), unit: newPartUnit }]);
      setNewPartName('');
      setNewPartQty('');
      setNewPartUnit('units');
    };

    const handleRemovePart = (index) => {
      setParts(parts.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!formData.subject) {
        toast.error('Subject is required');
        return;
      }
      setSubmitting(true);
      try {
        // Format parts as string for API
        const partsWithQuantity = parts
          .map(p => `${p.name} (${p.quantity} ${p.unit})`)
          .join(', ');

        await serviceAPI.createAppointment({
          ...formData,
          account_id: formData.account_id ? parseInt(formData.account_id) : null,
          required_parts: partsWithQuantity,
        });
        toast.success('Service appointment created successfully');
        setShowAppointmentModal(false);
        loadAppointments();
      } catch (error) {
        console.error('Failed to create appointment:', error);
        toast.error('Failed to create appointment');
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">New Service Appointment</h2>
            <button onClick={() => setShowAppointmentModal(false)} className="p-1 hover:bg-gray-100 rounded">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
                <select
                  value={formData.account_id}
                  onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="">Select Account</option>
                  {accounts.map(acc => (
                    <option key={acc.id} value={acc.id}>{acc.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Appointment Type</label>
                <select
                  value={formData.appointment_type}
                  onChange={(e) => setFormData({...formData, appointment_type: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="Field Service">Field Service</option>
                  <option value="Phone">Phone</option>
                  <option value="Remote">Remote</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({...formData, subject: e.target.value})}
                className="w-full border rounded-md px-3 py-2"
                placeholder="Enter appointment subject"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="w-full border rounded-md px-3 py-2"
                rows={3}
                placeholder="Enter description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Start</label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_start}
                  onChange={(e) => setFormData({...formData, scheduled_start: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled End</label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_end}
                  onChange={(e) => setFormData({...formData, scheduled_end: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="Low">Low</option>
                  <option value="Normal">Normal</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                  placeholder="Service location"
                />
              </div>
            </div>

            {/* Required Parts with Quantity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Required Parts / Materials</label>

              {/* Add new part */}
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={newPartName}
                  onChange={(e) => setNewPartName(e.target.value)}
                  className="flex-1 border rounded-md px-3 py-2 text-sm"
                  placeholder="Part/Material name (e.g., XLPE Cable, Transformer)"
                />
                <input
                  type="number"
                  min="1"
                  value={newPartQty}
                  onChange={(e) => setNewPartQty(e.target.value)}
                  className="w-20 border rounded-md px-3 py-2 text-sm"
                  placeholder="Qty"
                />
                <select
                  value={newPartUnit}
                  onChange={(e) => setNewPartUnit(e.target.value)}
                  className="w-24 border rounded-md px-2 py-2 text-sm"
                >
                  {unitOptions.map(unit => (
                    <option key={unit} value={unit}>{unit}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleAddPart}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                >
                  Add
                </button>
              </div>

              {/* Parts list */}
              {parts.length > 0 && (
                <div className="border rounded-md bg-gray-50 divide-y">
                  {parts.map((part, index) => (
                    <div key={index} className="flex items-center justify-between p-2">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-gray-700">{part.name}</span>
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {part.quantity} {part.unit}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemovePart(index)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {parts.length === 0 && (
                <p className="text-sm text-gray-500 italic">No parts added yet. Add parts/materials required for this appointment.</p>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={() => setShowAppointmentModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Creating...' : 'Create Appointment'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Work Order Form Component
  const WorkOrderModal = () => {
    const [formData, setFormData] = useState({
      account_id: '',
      subject: '',
      description: '',
      priority: 'Medium',
      service_type: 'Warranty',
      product: '',
    });
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!formData.subject) {
        toast.error('Subject is required');
        return;
      }
      setSubmitting(true);
      try {
        await serviceAPI.createWorkOrder({
          ...formData,
          account_id: formData.account_id ? parseInt(formData.account_id) : null,
        });
        toast.success('Work order created successfully');
        setShowWorkOrderModal(false);
        loadWorkOrders();
      } catch (error) {
        console.error('Failed to create work order:', error);
        toast.error('Failed to create work order. Backend endpoint may not be available yet.');
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">New Work Order</h2>
            <button onClick={() => setShowWorkOrderModal(false)} className="p-1 hover:bg-gray-100 rounded">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
                <select
                  value={formData.account_id}
                  onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="">Select Account</option>
                  {accounts.map(acc => (
                    <option key={acc.id} value={acc.id}>{acc.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Type</label>
                <select
                  value={formData.service_type}
                  onChange={(e) => setFormData({...formData, service_type: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="Warranty">Warranty</option>
                  <option value="Paid">Paid Service</option>
                  <option value="Contract">Contract</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({...formData, subject: e.target.value})}
                className="w-full border rounded-md px-3 py-2"
                placeholder="Enter work order subject"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="w-full border rounded-md px-3 py-2"
                rows={3}
                placeholder="Describe the work needed"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product/Equipment</label>
                <input
                  type="text"
                  value={formData.product}
                  onChange={(e) => setFormData({...formData, product: e.target.value})}
                  className="w-full border rounded-md px-3 py-2"
                  placeholder="e.g., Transformer T-100"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={() => setShowWorkOrderModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Creating...' : 'Create Work Order'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Service Appointments Content
  const renderAppointments = () => (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500 rounded-md">
            <CalendarDaysIcon className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-lg font-semibold">Service Appointments</h2>
        </div>
        <button
          onClick={() => setShowAppointmentModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="w-4 h-4" />
          New Appointment
        </button>
      </div>

      {loadingAppointments ? (
        <div className="text-center py-8">Loading appointments...</div>
      ) : appointments.length === 0 ? (
        <div className="card p-12 text-center">
          <CalendarDaysIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Service Appointments</h3>
          <p className="text-gray-500 mb-4">Create a service appointment to schedule field service visits.</p>
          <button
            onClick={() => setShowAppointmentModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Appointment
          </button>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Appointment #</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scheduled</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                {/* <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Technician</th> */}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {appointments.map(apt => (
                <tr key={`svc-apt-${apt.id}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-blue-600">{apt.appointment_number}</td>
                  <td className="px-4 py-3 text-sm">{apt.subject}</td>
                  <td className="px-4 py-3 text-sm">{apt.appointment_type}</td>
                  <td className="px-4 py-3 text-sm">
                    {apt.scheduled_start ? new Date(apt.scheduled_start).toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={apt.priority} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={apt.status?.toUpperCase()} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  // Work Orders Content
  const renderWorkOrders = () => (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-500 rounded-md">
            <WrenchScrewdriverIcon className="w-5 h-5 text-white" />
          </div>
          {/* <h2 className="text-lg font-semibold">Work Orders</h2> */}
        </div>
        <button
          onClick={() => setShowWorkOrderModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="w-4 h-4" />
          New Work Order
        </button>
      </div>

      {loadingWorkOrders ? (
        <div className="text-center py-8">Loading work orders...</div>
      ) : workOrders.length === 0 ? (
        <div className="card p-12 text-center">
          <WrenchScrewdriverIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Work Orders</h3>
          <p className="text-gray-500 mb-4">Create a work order to track service requests and SAP integration.</p>
          <button
            onClick={() => setShowWorkOrderModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Work Order
          </button>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Work Order #</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SAP Order ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {workOrders.map(wo => (
                <tr key={`svc-wo-${wo.id}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-blue-600">{wo.work_order_number}</td>
                  <td className="px-4 py-3 text-sm">{wo.subject}</td>
                  <td className="px-4 py-3 text-sm">{wo.account_name || '-'}</td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={wo.priority} />
                  </td>
                  <td className="px-4 py-3 text-sm">{wo.service_type}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={wo.status} />
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-green-600">{wo.sap_order_id || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'cases':
        return (
          <ObjectListPage
            objectType="case"
            objectLabel="Case"
            columns={caseColumns}
            api={casesAPI}
            actions={caseActions}
            icon={<DocumentTextIcon className="w-5 h-5 text-white" />}
            iconColor="bg-pink-500"
            emptyTitle="Track customer support in one place"
            emptyDescription="Cases bring together customer questions, feedback, and issues from any channel."
            onSelectionChange={(ids, records) => setSelectedRecords(records)}
          />
        );
      case 'appointments':
        return renderAppointments();
      case 'workorders':
        return renderWorkOrders();
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
        <h1 className="text-2xl font-bold text-gray-900">Service</h1>
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

      {/* Assign Label Modal */}
      <AssignLabelModal
        isOpen={showLabelModal}
        onClose={() => setShowLabelModal(false)}
        selectedCount={selectedRecords.length}
        onAssign={(labels) => {
          console.log('Assigned labels:', labels);
        }}
      />

      {/* Appointment Modal */}
      {showAppointmentModal && <AppointmentModal />}

      {/* Work Order Modal */}
      {showWorkOrderModal && <WorkOrderModal />}
    </div>
  );
}
