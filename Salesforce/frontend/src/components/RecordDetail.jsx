import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  PencilIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  UserGroupIcon,
  BuildingOfficeIcon,
  ChartBarSquareIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import RecordFormModal from './RecordFormModal';

const objectConfigs = {
  contact: {
    label: 'Contact',
    icon: UserGroupIcon,
    iconColor: 'bg-purple-500',
    displayFields: [
      { key: 'full_name', label: 'Name', primary: true },
      { key: 'title', label: 'Title' },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      { key: 'account_name', label: 'Account' },
      { key: 'owner_name', label: 'Owner' },
      { key: 'created_at', label: 'Created', type: 'datetime' },
    ],
  },
  account: {
    label: 'Account',
    icon: BuildingOfficeIcon,
    iconColor: 'bg-indigo-500',
    displayFields: [
      { key: 'name', label: 'Account Name', primary: true },
      { key: 'phone', label: 'Phone' },
      { key: 'website', label: 'Website' },
      { key: 'industry', label: 'Industry' },
      { key: 'owner_name', label: 'Owner' },
      { key: 'created_at', label: 'Created', type: 'datetime' },
    ],
  },
  lead: {
    label: 'Lead',
    icon: ChartBarSquareIcon,
    iconColor: 'bg-green-500',
    displayFields: [
      { key: 'full_name', label: 'Name', primary: true },
      { key: 'company', label: 'Company' },
      { key: 'title', label: 'Title' },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'owner_name', label: 'Owner' },
      { key: 'created_at', label: 'Created', type: 'datetime' },
    ],
    actions: ['convert'],
  },
  opportunity: {
    label: 'Opportunity',
    icon: ChartBarSquareIcon,
    iconColor: 'bg-yellow-500',
    displayFields: [
      { key: 'name', label: 'Opportunity Name', primary: true },
      { key: 'account_name', label: 'Account' },
      { key: 'amount', label: 'Amount', type: 'currency' },
      { key: 'stage', label: 'Stage', type: 'badge' },
      { key: 'close_date', label: 'Close Date', type: 'date' },
      { key: 'probability', label: 'Probability', type: 'percent' },
      { key: 'owner_name', label: 'Owner' },
      { key: 'created_at', label: 'Created', type: 'datetime' },
    ],
  },
  case: {
    label: 'Case',
    icon: DocumentTextIcon,
    iconColor: 'bg-pink-500',
    displayFields: [
      { key: 'case_number', label: 'Case Number', primary: true },
      { key: 'subject', label: 'Subject' },
      { key: 'description', label: 'Description' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'priority', label: 'Priority', type: 'badge' },
      { key: 'account_name', label: 'Account' },
      { key: 'contact_name', label: 'Contact' },
      { key: 'is_escalated', label: 'Escalated', type: 'boolean' },
      { key: 'owner_name', label: 'Owner' },
      { key: 'created_at', label: 'Created', type: 'datetime' },
    ],
    actions: ['escalate'],
  },
};

export default function RecordDetail({ objectType, api }) {
  const { id } = useParams();
  const navigate = useNavigate();

  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const config = objectConfigs[objectType];
  const Icon = config?.icon;

  useEffect(() => {
    loadRecord();
  }, [id, objectType]);

  const loadRecord = async () => {
    setLoading(true);
    try {
      const response = await api.get(id);
      setRecord(response.data);
    } catch (error) {
      console.error('Failed to load record:', error);
      const errorMsg = error.response?.status === 404
        ? `${config.label} not found. It may have been deleted or not yet approved.`
        : `Failed to load ${config.label.toLowerCase()}`;
      toast.error(errorMsg);

      // Only navigate away after a delay to prevent multiple redirects
      setTimeout(() => {
        navigate(`/${objectType}s`);
      }, 1000);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete this ${config.label}?`)) {
      return;
    }
    try {
      await api.delete(id);
      toast.success(`${config.label} deleted`);
      navigate(`/${objectType}s`);
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleUpdate = async (data) => {
    await api.update(id, data);
    loadRecord();
  };

  const handleConvert = async () => {
    if (!window.confirm('Convert this lead to an Account, Contact, and Opportunity?')) {
      return;
    }
    setActionLoading(true);
    try {
      const response = await api.convert(id, {
        create_account: true,
        create_opportunity: true,
      });
      toast.success('Lead converted successfully');
      navigate(`/contacts/${response.data.contact_id}`);
    } catch (error) {
      toast.error('Failed to convert lead');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!window.confirm('Escalate this case?')) {
      return;
    }
    setActionLoading(true);
    try {
      await api.escalate(id);
      toast.success('Case escalated');
      loadRecord();
    } catch (error) {
      toast.error('Failed to escalate case');
    } finally {
      setActionLoading(false);
    }
  };

  const formatValue = (field, value) => {
    if (value === null || value === undefined) return '-';

    switch (field.type) {
      case 'datetime':
        return new Date(value).toLocaleString();
      case 'date':
        return new Date(value).toLocaleDateString();
      case 'currency':
        return `$${Number(value).toLocaleString()}`;
      case 'percent':
        return `${value}%`;
      case 'boolean':
        return value ? 'Yes' : 'No';
      case 'badge':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {value}
          </span>
        );
      default:
        return String(value);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (!record || !config) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Record not found</p>
      </div>
    );
  }

  const primaryField = config.displayFields.find(f => f.primary);
  const primaryValue = record[primaryField?.key] || record.name || record.subject || `${config.label} ${id}`;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate(`/${objectType}s`)}
          className="flex items-center text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4 mr-1" />
          Back to {config.label}s
        </button>

        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <div className={`w-12 h-12 ${config.iconColor} rounded-lg flex items-center justify-center mr-4`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">{config.label}</p>
              <h1 className="text-2xl font-bold text-gray-900">{primaryValue}</h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {config.actions?.includes('convert') && record.status !== 'Converted' && (
              <button
                type="button"
                onClick={handleConvert}
                disabled={actionLoading}
                className="btn-primary"
              >
                {actionLoading ? 'Converting...' : 'Convert'}
              </button>
            )}
            {config.actions?.includes('escalate') && !record.is_escalated && (
              <button
                type="button"
                onClick={handleEscalate}
                disabled={actionLoading}
                className="btn-secondary"
              >
                {actionLoading ? 'Escalating...' : 'Escalate'}
              </button>
            )}
            <button
              type="button"
              onClick={() => setShowEditModal(true)}
              className="btn-secondary flex items-center"
            >
              <PencilIcon className="w-4 h-4 mr-1" />
              Edit
            </button>
            <button
              type="button"
              onClick={handleDelete}
              className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
            >
              <TrashIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Record Details Card */}
      <div className="card">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{config.label} Details</h2>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            {config.displayFields.map((field) => (
              <div key={field.key} className="border-b border-gray-100 pb-3">
                <dt className="text-sm font-medium text-gray-500">{field.label}</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatValue(field, record[field.key])}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {/* Edit Modal */}
      <RecordFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        objectType={objectType}
        onSave={handleUpdate}
        initialData={record}
      />
    </div>
  );
}
