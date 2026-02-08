import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  ClipboardIcon,
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const SERVICENOW_BASE_URL = 'https://your-instance.service-now.com';

// Helper function to copy text to clipboard
const copyToClipboard = async (text, label = 'ID') => {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied!`);
  } catch (err) {
    toast.error('Failed to copy');
  }
};

// Copyable field component
const CopyableField = ({ label, value, highlight = false }) => {
  if (!value) return null;

  return (
    <div className="mb-4">
      <label className="text-sm font-medium text-gray-600">{label}</label>
      <div className={`flex items-center gap-2 mt-1 p-2 rounded ${highlight ? 'bg-blue-50' : 'bg-gray-50'}`}>
        <span className="font-mono text-sm flex-1 break-all">{value}</span>
        <button
          onClick={() => copyToClipboard(value, label)}
          className="p-1 hover:bg-gray-200 rounded"
          title={`Copy ${label}`}
        >
          <ClipboardIcon className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </div>
  );
};

// Journey step component
const JourneyStep = ({ title, status, timestamp, description, isLast = false }) => {
  const getStepConfig = (status) => {
    switch (status) {
      case 'completed':
        return { icon: CheckCircleIcon, color: 'text-green-600', bgColor: 'bg-green-100', lineColor: 'bg-green-300' };
      case 'pending':
        return { icon: ClockIcon, color: 'text-yellow-600', bgColor: 'bg-yellow-100', lineColor: 'bg-yellow-300' };
      case 'failed':
        return { icon: XCircleIcon, color: 'text-red-600', bgColor: 'bg-red-100', lineColor: 'bg-red-300' };
      default:
        return { icon: ClockIcon, color: 'text-gray-400', bgColor: 'bg-gray-100', lineColor: 'bg-gray-200' };
    }
  };

  const config = getStepConfig(status);
  const Icon = config.icon;

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-10 h-10 rounded-full ${config.bgColor} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        {!isLast && <div className={`w-0.5 h-16 ${config.lineColor}`} />}
      </div>
      <div className="pb-8">
        <h4 className="font-medium text-gray-900">{title}</h4>
        {timestamp && <p className="text-xs text-gray-500 mt-1">{new Date(timestamp).toLocaleString()}</p>}
        {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
      </div>
    </div>
  );
};

export default function ServiceNowTracking() {
  const [correlationId, setCorrelationId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);

  const api = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
  });

  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!correlationId.trim()) {
      toast.error('Please enter a Correlation ID or Ticket Number');
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/api/integration-tracking/${correlationId}`);
      setResult(response.data);

      // Add to search history
      if (!searchHistory.find(h => h.id === correlationId)) {
        setSearchHistory([{ id: correlationId, timestamp: new Date() }, ...searchHistory.slice(0, 9)]);
      }
      toast.success('Tracking data found!');
    } catch (error) {
      setResult(null);
      toast.error('Correlation ID not found. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = (id) => {
    setCorrelationId(id);
    // Trigger search
    setTimeout(() => {
      document.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true }));
    }, 0);
  };

  const getStatusColor = (status) => {
    const colors = {
      SUCCESS: 'bg-green-100 text-green-800 border-green-200',
      COMPLETED: 'bg-green-100 text-green-800 border-green-200',
      APPROVED: 'bg-green-100 text-green-800 border-green-200',
      DUPLICATE_DETECTED: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      SENT_TO_SERVICENOW: 'bg-blue-100 text-blue-800 border-blue-200',
      PARTS_UNAVAILABLE: 'bg-orange-100 text-orange-800 border-orange-200',
      ENTITLEMENT_FAILED: 'bg-red-100 text-red-800 border-red-200',
      REJECTED: 'bg-red-100 text-red-800 border-red-200',
      FAILED: 'bg-red-100 text-red-800 border-red-200',
      ERROR: 'bg-red-100 text-red-800 border-red-200'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getJourneySteps = (result) => {
    const steps = [];

    // Step 1: Request Created
    steps.push({
      title: 'Request Created in Salesforce',
      status: 'completed',
      timestamp: result.created_at,
      description: `Request ID: ${result.id}`
    });

    // Step 2: Sent to ServiceNow
    if (result.servicenow_ticket_id || result.status !== 'PENDING') {
      steps.push({
        title: 'Sent to ServiceNow',
        status: result.servicenow_ticket_id ? 'completed' : 'pending',
        timestamp: result.servicenow_ticket_id ? result.updated_at : null,
        description: result.servicenow_ticket_id ? `Ticket: ${result.servicenow_ticket_id}` : 'Awaiting ticket creation'
      });
    }

    // Step 3: SAP Integration (if applicable)
    if (result.sap_customer_id || result.sap_order_id || result.assigned_technician_id) {
      steps.push({
        title: 'SAP Integration Complete',
        status: 'completed',
        description: result.sap_customer_id
          ? `Customer ID: ${result.sap_customer_id}`
          : result.sap_order_id
            ? `Order ID: ${result.sap_order_id}`
            : `Technician: ${result.technician_name || result.assigned_technician_id}`
      });
    }

    // Step 4: Final Status
    const finalStatus = ['COMPLETED', 'APPROVED', 'SUCCESS'].includes(result.status)
      ? 'completed'
      : ['FAILED', 'REJECTED', 'ERROR'].includes(result.status)
        ? 'failed'
        : 'pending';

    steps.push({
      title: finalStatus === 'completed' ? 'Completed Successfully' : finalStatus === 'failed' ? 'Failed' : 'In Progress',
      status: finalStatus,
      description: result.message || result.error_message || `Current status: ${result.status}`
    });

    return steps;
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ServiceNow Integration Tracking</h1>
        <p className="text-gray-600 mt-1">Track the complete journey of your requests through ServiceNow and SAP</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Enter Correlation ID or ServiceNow Ticket Number (e.g., TKT123456)..."
              value={correlationId}
              onChange={(e) => setCorrelationId(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <MagnifyingGlassIcon className="w-5 h-5" />
                Search
              </>
            )}
          </button>
        </div>
      </form>

      {/* Search History */}
      {searchHistory.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Searches</h3>
          <div className="flex flex-wrap gap-2">
            {searchHistory.map(item => (
              <button
                key={item.id}
                onClick={() => handleHistoryClick(item.id)}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 text-sm flex items-center gap-1"
              >
                <ClockIcon className="w-3 h-3" />
                {item.id.length > 20 ? `${item.id.substring(0, 20)}...` : item.id}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Journey Timeline */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
              <ClockIcon className="w-5 h-5 text-blue-600" />
              Integration Journey
            </h3>
            <div className="mt-4">
              {getJourneySteps(result).map((step, index, arr) => (
                <JourneyStep
                  key={index}
                  {...step}
                  isLast={index === arr.length - 1}
                />
              ))}
            </div>
          </div>

          {/* Middle Column - Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Integration Details</h3>

            <div className="mb-4">
              <label className="text-sm font-medium text-gray-600">Status</label>
              <div className="mt-1">
                <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium border ${getStatusColor(result.status)}`}>
                  {['COMPLETED', 'APPROVED', 'SUCCESS'].includes(result.status) && <CheckCircleIcon className="w-4 h-4" />}
                  {['PENDING', 'SENT_TO_SERVICENOW'].includes(result.status) && <ClockIcon className="w-4 h-4" />}
                  {['FAILED', 'REJECTED', 'ERROR'].includes(result.status) && <XCircleIcon className="w-4 h-4" />}
                  {result.status}
                </span>
              </div>
            </div>

            <CopyableField label="Request ID" value={result.id?.toString()} />
            <CopyableField label="Correlation ID" value={result.correlation_id} highlight />

            {result.servicenow_ticket_id && (
              <div className="mb-4">
                <label className="text-sm font-medium text-gray-600">ServiceNow Ticket</label>
                <div className="flex items-center gap-2 mt-1 p-2 rounded bg-green-50 border border-green-200">
                  <CheckCircleIcon className="w-4 h-4 text-green-600" />
                  <span className="font-mono text-sm flex-1">{result.servicenow_ticket_id}</span>
                  <button
                    onClick={() => copyToClipboard(result.servicenow_ticket_id, 'Ticket ID')}
                    className="p-1 hover:bg-green-100 rounded"
                    title="Copy Ticket ID"
                  >
                    <ClipboardIcon className="w-4 h-4 text-green-600" />
                  </button>
                  <a
                    href={`${SERVICENOW_BASE_URL}/nav_to.do?uri=incident.do?sysparm_query=number=${result.servicenow_ticket_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 hover:bg-green-100 rounded text-green-600"
                    title="View in ServiceNow"
                  >
                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  </a>
                </div>
              </div>
            )}

            <div className="mb-4">
              <label className="text-sm font-medium text-gray-600">Message</label>
              <p className="mt-1 text-sm text-gray-700 p-2 bg-gray-50 rounded">
                {result.message || result.error_message || 'No message available'}
              </p>
            </div>

            <div className="mb-4">
              <label className="text-sm font-medium text-gray-600">Created</label>
              <p className="mt-1 text-sm text-gray-700">
                {result.created_at ? new Date(result.created_at).toLocaleString() : '-'}
              </p>
            </div>

            {result.updated_at && (
              <div className="mb-4">
                <label className="text-sm font-medium text-gray-600">Last Updated</label>
                <p className="mt-1 text-sm text-gray-700">
                  {new Date(result.updated_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {/* Right Column - SAP Integration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">SAP Integration</h3>

            {/* Scenario 1 - Account Creation */}
            {result.sap_customer_id && (
              <CopyableField label="SAP Customer ID" value={result.sap_customer_id} highlight />
            )}

            {/* Scenario 2 - Service Appointments */}
            {result.appointment_id && (
              <>
                <CopyableField label="Appointment ID" value={result.appointment_id?.toString()} />
                {(result.assigned_technician_id || result.technician_name) && (
                  <div className="mb-4">
                    {/* <label className="text-sm font-medium text-gray-600">Assigned Technician</label> */}
                    <p className="mt-1 text-sm text-gray-700 p-2 bg-blue-50 rounded">
                      {result.technician_name || `ID: ${result.assigned_technician_id}`}
                    </p>
                  </div>
                )}
                {result.parts_available !== undefined && (
                  <div className="mb-4">
                    <label className="text-sm font-medium text-gray-600">Parts Availability</label>
                    <div className="mt-1">
                      <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium ${result.parts_available ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>
                        {result.parts_available ? <CheckCircleIcon className="w-4 h-4" /> : <XCircleIcon className="w-4 h-4" />}
                        {result.parts_available ? 'All parts available' : 'Parts unavailable'}
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Scenario 3 - Work Orders */}
            {result.sap_order_id && (
              <>
                <CopyableField label="SAP Order ID" value={result.sap_order_id} highlight />
                {result.sap_notification_id && (
                  <CopyableField label="SAP Notification ID" value={result.sap_notification_id} />
                )}
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-600">Entitlement Verified</label>
                  <div className="mt-1">
                    <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium ${result.entitlement_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {result.entitlement_verified ? <CheckCircleIcon className="w-4 h-4" /> : <XCircleIcon className="w-4 h-4" />}
                      {result.entitlement_verified ? 'Verified' : 'Not Verified'}
                    </span>
                  </div>
                </div>
              </>
            )}

            {/* No SAP data yet */}
            {!result.sap_customer_id && !result.appointment_id && !result.sap_order_id && (
              <div className="text-center py-8 text-gray-500">
                <ClockIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>SAP integration data will appear here once processed</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <MagnifyingGlassIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Track Your Integration</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Enter a Correlation ID or ServiceNow Ticket Number to view the complete integration journey,
            including ServiceNow ticket status and SAP system references.
          </p>
        </div>
      )}
    </div>
  );
}
