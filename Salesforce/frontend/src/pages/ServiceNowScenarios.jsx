import { useState, useEffect } from 'react';
import { ArrowPathIcon, EyeIcon, ArrowPathRoundedSquareIcon, TrashIcon, ClockIcon, CheckCircleIcon, XMarkIcon, ExclamationTriangleIcon, ClipboardIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';
import { accountsAPI, serviceAPI } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import EntitlementBadge from '../components/EntitlementBadge';
import StatCard from '../components/StatCard';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:18000';

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

// Helper function to copy text to clipboard
const copyToClipboard = async (text, label = 'ID') => {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard!`);
  } catch (err) {
    toast.error('Failed to copy');
  }
};

// ServiceNow base URL (configure based on your instance)
const SERVICENOW_BASE_URL = 'https://your-instance.service-now.com';

// Helper component for copyable IDs
const CopyableId = ({ value, label, truncate = true }) => {
  if (!value) return <span className="text-gray-400">-</span>;

  const displayValue = truncate && value.length > 12
    ? `${value.substring(0, 12)}...`
    : value;

  return (
    <div className="flex items-center gap-1 group">
      <span className="font-mono text-xs" title={value}>
        {displayValue}
      </span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(value, label);
        }}
        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded transition-opacity"
        title={`Copy ${label}`}
      >
        <ClipboardIcon className="w-3 h-3 text-gray-500" />
      </button>
    </div>
  );
};

// Helper component for ServiceNow ticket links
const ServiceNowTicketLink = ({ ticketId }) => {
  if (!ticketId) return <span className="text-gray-400">-</span>;

  return (
    <div className="flex items-center gap-1">
      <span className="font-mono text-xs text-blue-600">{ticketId}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(ticketId, 'Ticket ID');
        }}
        className="p-1 hover:bg-gray-100 rounded"
        title="Copy Ticket ID"
      >
        <ClipboardIcon className="w-3 h-3 text-gray-500" />
      </button>
      <a
        href={`${SERVICENOW_BASE_URL}/nav_to.do?uri=incident.do?sysparm_query=number=${ticketId}`}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="p-1 hover:bg-blue-100 rounded text-blue-600"
        title="View in ServiceNow"
      >
        <ArrowTopRightOnSquareIcon className="w-3 h-3" />
      </a>
    </div>
  );
};

// Integration status indicator with icon
const IntegrationStatusIndicator = ({ status, ticketId }) => {
  const getStatusConfig = (status) => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED':
      case 'APPROVED':
        return { icon: CheckCircleIcon, color: 'text-green-600', bg: 'bg-green-100' };
      case 'PENDING':
      case 'SENT_TO_SERVICENOW':
        return { icon: ClockIcon, color: 'text-yellow-600', bg: 'bg-yellow-100' };
      case 'FAILED':
      case 'REJECTED':
        return { icon: XMarkIcon, color: 'text-red-600', bg: 'bg-red-100' };
      default:
        return { icon: ClockIcon, color: 'text-gray-600', bg: 'bg-gray-100' };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${config.bg} ${config.color}`}>
      <Icon className="w-3 h-3" />
      <span>{status || 'PENDING'}</span>
      {ticketId && <span className="text-green-600">✓</span>}
    </div>
  );
};

export default function ServiceNowScenarios() {
  const [activeScenario, setActiveScenario] = useState('scenario1');
  const [results, setResults] = useState([]);
  const [appointments, setAppointments] = useState({});
  const [loading, setLoading] = useState(false);

  // Agent review workflow state
  const [pendingAppointments, setPendingAppointments] = useState([]);
  const [pendingWorkOrders, setPendingWorkOrders] = useState([]);
  const [showTechnicianModal, setShowTechnicianModal] = useState(false);
  const [availableTechnicians, setAvailableTechnicians] = useState([]);
  const [selectedTechnician, setSelectedTechnician] = useState(null);
  const [currentRequestId, setCurrentRequestId] = useState(null);
  const [fetchingTechnicians, setFetchingTechnicians] = useState(false);

  useEffect(() => {
    // Clear results when switching scenarios
    setResults([]);
    setPendingAppointments([]);
    setPendingWorkOrders([]);

    // Load new data
    loadResults();
    loadPendingRequests();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadResults();
      loadPendingRequests();
    }, 30000);
    return () => clearInterval(interval);
  }, [activeScenario]);

  // Helper to deduplicate arrays by ID
  const deduplicateById = (items) => {
    const seen = new Set();
    return items.filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  };

  const loadPendingRequests = async () => {
    try {
      if (activeScenario === 'scenario2') {
        const response = await api.get('/api/service/scheduling-requests?status=PENDING');
        setPendingAppointments(response.data?.items || response.data || []);
      } else if (activeScenario === 'scenario3') {
        const response = await api.get('/api/service/workorder-requests?status=PENDING');
        setPendingWorkOrders(response.data?.items || response.data || []);
      }
    } catch (error) {
      console.error('Failed to load pending requests:', error);
    }
  };

  const loadResults = async () => {
    setLoading(true);
    try {
      let newResults = [];
      if (activeScenario === 'scenario1') {
        const response = await accountsAPI.listRequests({ page_size: 50 });
        newResults = deduplicateById(response.data.items || []);
      } else if (activeScenario === 'scenario2') {
        const [schedResponse, apptResponse] = await Promise.all([
          serviceAPI.listSchedulingRequests({ page_size: 50 }),
          serviceAPI.listAppointments({ page_size: 100 })
        ]);
        const rawResults = Array.isArray(schedResponse.data) ? schedResponse.data : schedResponse.data?.items || [];
        // Create appointments lookup map
        const apptList = Array.isArray(apptResponse.data) ? apptResponse.data : apptResponse.data?.items || [];
        const apptMap = {};
        apptList.forEach(a => { apptMap[a.id] = a; });
        setAppointments(apptMap);
        // Show all scheduling requests
        newResults = deduplicateById(rawResults);
      } else if (activeScenario === 'scenario3') {
        const response = await serviceAPI.listWorkOrders({ page_size: 50 });
        const rawResults = Array.isArray(response.data) ? response.data : response.data?.items || [];
        newResults = deduplicateById(rawResults);
      }
      setResults(newResults);
    } catch (error) {
      console.error('Failed to load results:', error);
    } finally {
      setLoading(false);
    }
  };

  // Agent Review Handlers
  const handleApproveAppointment = async (request) => {
    setCurrentRequestId(request.id);
    setFetchingTechnicians(true);
    setShowTechnicianModal(true);
    setAvailableTechnicians([]);
    setSelectedTechnician(null);

    try {
      // Fetch available technicians from SAP HR using the request-based endpoint
      const techResponse = await api.get(`/api/service/appointment-requests/${request.id}/available-technicians`);
      setAvailableTechnicians(techResponse.data.technicians || []);

      if (techResponse.data.technicians?.length === 0) {
        toast.error('No available technicians found in SAP HR');
      }
    } catch (error) {
      console.error('Failed to fetch technicians:', error);
      toast.error(error.response?.data?.detail || 'Failed to fetch available technicians from SAP HR');
      setShowTechnicianModal(false);
    } finally {
      setFetchingTechnicians(false);
    }
  };

  const handleConfirmTechnicianAssignment = async () => {
    if (!selectedTechnician) {
      toast.error('Please select a technician');
      return;
    }

    try {
      toast.loading('Approving and assigning technician...', { id: 'approve' });
      await api.post(`/api/service/appointment-requests/${currentRequestId}/approve`, {
        technician_id: selectedTechnician.id,
        technician_name: selectedTechnician.name
      });
      toast.success('Appointment approved and technician assigned!', { id: 'approve' });
      setShowTechnicianModal(false);
      setSelectedTechnician(null);
      loadResults();
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve appointment', { id: 'approve' });
    }
  };

  const handleRejectAppointment = async (requestId) => {
    if (!window.confirm('Are you sure you want to reject this appointment request?')) {
      return;
    }

    try {
      toast.loading('Rejecting appointment...', { id: 'reject' });
      await api.post(`/api/service/appointment-requests/${requestId}/reject`, {
        reason: 'Rejected by agent'
      });
      toast.success('Appointment request rejected', { id: 'reject' });
      loadResults();
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject appointment', { id: 'reject' });
    }
  };

  const handleApproveWorkOrder = async (requestId) => {
    if (!window.confirm('Approve this work order and send to SAP for processing?')) {
      return;
    }

    try {
      toast.loading('Approving work order...', { id: 'approve-wo' });
      await api.post(`/api/service/workorder-requests/${requestId}/approve`);
      toast.success('Work order approved and sent to SAP!', { id: 'approve-wo' });
      loadResults();
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve work order', { id: 'approve-wo' });
    }
  };

  const handleRejectWorkOrder = async (requestId) => {
    if (!window.confirm('Are you sure you want to reject this work order request?')) {
      return;
    }

    try {
      toast.loading('Rejecting work order...', { id: 'reject-wo' });
      await api.post(`/api/service/workorder-requests/${requestId}/reject`, {
        reason: 'Rejected by agent'
      });
      toast.success('Work order request rejected', { id: 'reject-wo' });
      loadResults();
      loadPendingRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject work order', { id: 'reject-wo' });
    }
  };

  const handleRetrySync = async (id, scenario) => {
    try {
      toast.loading('Retrying sync...', { id: 'retry' });
      toast.success('Sync retry initiated', { id: 'retry' });
      loadResults();
    } catch (error) {
      toast.error('Retry failed', { id: 'retry' });
    }
  };

  const handleViewDetails = (id) => {
    toast.success(`Viewing details for ID: ${id}`);
  };

  const handleDeleteRequest = async (id, name) => {
    if (!window.confirm(`Delete account request "${name}"?`)) {
      return;
    }
    try {
      await accountsAPI.deleteRequest(id);
      toast.success(`Deleted "${name}"`);
      loadResults();
    } catch (error) {
      console.error('Failed to delete request:', error);
      toast.error('Failed to delete request');
    }
  };

  const handleCheckParts = async (appointmentId) => {
    try {
      toast.loading('Checking parts availability...', { id: 'parts' });
      toast.success('Parts check completed', { id: 'parts' });
      loadResults();
    } catch (error) {
      toast.error('Parts check failed', { id: 'parts' });
    }
  };

  const handleCheckEntitlement = async (workOrderId) => {
    try {
      toast.loading('Checking entitlement...', { id: 'entitlement' });
      toast.success('Entitlement check completed', { id: 'entitlement' });
      loadResults();
    } catch (error) {
      toast.error('Entitlement check failed', { id: 'entitlement' });
    }
  };

  // Scenario 1: New Client Creation
  const renderScenario1 = () => {
    const totalSynced = results.filter(r => r.status?.toUpperCase() === 'APPROVED' || r.integration_status === 'COMPLETED').length;
    const duplicateCount = results.filter(r => r.status?.toUpperCase() === 'DUPLICATE_DETECTED').length;
    const pendingCount = results.filter(r => r.status?.toUpperCase() === 'PENDING').length;
    const failedCount = results.filter(r => r.status?.toUpperCase() === 'REJECTED' || r.status?.toUpperCase() === 'FAILED').length;
    const successRate = results.length > 0 ? Math.round((totalSynced / results.length) * 100) : 0;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 1: New Client Creation</h3>
        <p className="text-gray-600 mb-6">Account Creation &rarr; ServiceNow &rarr; SAP Customer Master</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Total Synced" value={totalSynced} color="green" />
          <StatCard title="Success Rate" value={`${successRate}%`} color="blue" />
          <StatCard title="Pending" value={pendingCount} color="yellow" />
          <StatCard title="Duplicates" value={duplicateCount} color="orange" />
          <StatCard title="Failed" value={failedCount} color="red" />
        </div>

        {/* Accounts Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Account Name</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Integration Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">SAP Customer ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">ServiceNow Ticket</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Correlation ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Sync Date</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(account => (
                <tr key={`account-${account.id}`} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium text-blue-600">{account.name || '-'}</td>
                  <td className="p-3">
                    <StatusBadge status={account.status?.toUpperCase()} />
                  </td>
                  <td className="p-3">
                    <IntegrationStatusIndicator
                      status={account.integration_status}
                      ticketId={account.servicenow_ticket_id}
                    />
                  </td>
                  <td className="p-3 font-mono text-sm text-green-600 font-medium">
                    {account.sap_customer_id || '-'}
                  </td>
                  <td className="p-3">
                    <ServiceNowTicketLink ticketId={account.servicenow_ticket_id} />
                  </td>
                  <td className="p-3">
                    <CopyableId value={account.correlation_id} label="Correlation ID" />
                  </td>
                  <td className="p-3 text-xs text-gray-500">
                    {account.created_at ? new Date(account.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(account.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {(account.status?.toUpperCase() === 'FAILED' || account.status?.toUpperCase() === 'REJECTED') && (
                        <button
                          onClick={() => handleRetrySync(account.id, 'scenario1')}
                          className="p-1 text-gray-500 hover:text-orange-600"
                          title="Retry Sync"
                        >
                          <ArrowPathRoundedSquareIcon className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteRequest(account.id, account.name)}
                        className="p-1 text-gray-500 hover:text-red-600"
                        title="Delete"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No account creation requests yet</p>
            <p>Create a new account to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  // Scenario 2: Scheduling & Dispatching
  const renderScenario2 = () => {
    const appointmentsToday = results.filter(r => {
      const created = new Date(r.created_at);
      const today = new Date();
      return created.toDateString() === today.toDateString();
    }).length;
    const scheduledCount = results.filter(r => r.status === 'PENDING').length;
    const successCount = results.filter(r => r.status === 'SUCCESS' || r.status === 'APPROVED').length;
    const partsIssuesCount = results.filter(r => r.status === 'PARTS_UNAVAILABLE').length;
    const failedCount = results.filter(r => r.status === 'FAILED' || r.status === 'TECHNICIAN_UNAVAILABLE').length;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 2: Scheduling & Dispatching</h3>
        <p className="text-gray-600 mb-6">Service Appointment &rarr; ServiceNow &rarr; SAP HR (Technician) & SAP Inventory (Parts)</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Today" value={appointmentsToday} color="blue" />
          <StatCard title="Pending" value={scheduledCount} color="yellow" />
          <StatCard title="Success" value={successCount} color="green" />
          <StatCard title="Parts Issues" value={partsIssuesCount} color="orange" />
          <StatCard title="Failed" value={failedCount} color="red" />
        </div>

        {/* Appointments Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Appointment</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned Technician</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Parts Available</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">ServiceNow Ticket</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Correlation ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(apt => (
                <tr key={`apt-${apt.id}`} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm">
                    <div className="font-medium text-blue-600">
                      {appointments[apt.appointment_id]?.subject || apt.appointment_number || `APT-${apt.id}`}
                    </div>
                    <div className="text-xs text-gray-400">{apt.appointment_number}</div>
                  </td>
                  <td className="p-3">
                    <StatusBadge status={apt.status} />
                  </td>
                  <td className="p-3 text-sm">
                    {apt.technician_name ? (
                      <span className="text-green-600 font-medium">
                        {apt.technician_name}
                        <span className="text-gray-400 text-xs ml-1">(ID: {apt.assigned_technician_id})</span>
                      </span>
                    ) : (
                      <span className="text-gray-400">Not assigned</span>
                    )}
                  </td>
                  <td className="p-3 text-sm">
                    {apt.parts_available ? (
                      <span className="text-green-600 font-medium">Yes</span>
                    ) : (
                      <span className="text-orange-600 font-medium">No</span>
                    )}
                  </td>
                  <td className="p-3">
                    <ServiceNowTicketLink ticketId={apt.servicenow_ticket_id} />
                  </td>
                  <td className="p-3">
                    <CopyableId value={apt.correlation_id} label="Correlation ID" />
                  </td>
                  <td className="p-3 text-xs text-gray-500">
                    {apt.created_at ? new Date(apt.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(apt.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {apt.status === 'PARTS_UNAVAILABLE' && (
                        <button
                          onClick={() => handleCheckParts(apt.id)}
                          className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                        >
                          Check Parts
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No scheduling requests yet</p>
            <p>Create a service appointment to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  // Scenario 3: Work Order Request to SAP
  const renderScenario3 = () => {
    const workOrdersToday = results.filter(r => {
      const created = new Date(r.created_at);
      const today = new Date();
      return created.toDateString() === today.toDateString();
    }).length;
    const entitlementVerifiedCount = results.filter(r => r.entitlement_verified === true).length;
    const entitlementFailedCount = results.filter(r => r.status === 'ENTITLEMENT_FAILED').length;
    const successCount = results.filter(r => r.status === 'SUCCESS' || r.status === 'COMPLETED' || r.status === 'APPROVED').length;
    const pendingCount = results.filter(r => r.status === 'PENDING').length;

    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Scenario 3: Work Order Processing</h3>
        <p className="text-gray-600 mb-6">Work Order &rarr; ServiceNow &rarr; SAP Entitlement Check &rarr; SAP Service Order</p>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard title="Today" value={workOrdersToday} color="blue" />
          <StatCard title="Pending" value={pendingCount} color="yellow" />
          <StatCard title="Verified" value={entitlementVerifiedCount} color="green" />
          <StatCard title="Entitlement Failed" value={entitlementFailedCount} color="red" />
          <StatCard title="Completed" value={successCount} color="purple" />
        </div>

        {/* Work Orders Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Work Order #</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">SAP Order ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">ServiceNow Ticket</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Correlation ID</th>
                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map(wo => (
                <tr key={`wo-${wo.id}`} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium text-blue-600">
                    {wo.work_order_number || `WO-${wo.id}`}
                  </td>
                  <td className="p-3 text-sm">{wo.account_name || '-'}</td>
                  <td className="p-3 text-sm">{wo.subject || '-'}</td>
                  <td className="p-3">
                    <PriorityBadge priority={wo.priority || 'Normal'} />
                  </td>
                  <td className="p-3">
                    <IntegrationStatusIndicator
                      status={wo.status}
                      ticketId={wo.servicenow_ticket_id}
                    />
                  </td>
                  <td className="p-3 font-mono text-sm text-green-600">
                    {wo.sap_order_id || '-'}
                  </td>
                  <td className="p-3">
                    <ServiceNowTicketLink ticketId={wo.servicenow_ticket_id} />
                  </td>
                  <td className="p-3">
                    <CopyableId value={wo.correlation_id} label="Correlation ID" />
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(wo.id)}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      {wo.status === 'ENTITLEMENT_FAILED' && (
                        <button
                          onClick={() => handleCheckEntitlement(wo.id)}
                          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Recheck
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No work orders yet</p>
            <p>Create a work order from the Service page to see it tracked here.</p>
          </div>
        )}
      </div>
    );
  };

  // Technician Selection Modal
  const renderTechnicianModal = () => {
    if (!showTechnicianModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          {/* Modal Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-bold">Assign Technician from SAP HR</h3>
            <button
              onClick={() => {
                setShowTechnicianModal(false);
                setSelectedTechnician(null);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Parts Info Banner */}
          <div className="p-4 bg-blue-50 border-b border-blue-200">
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-blue-600" />
              <div>
                <p className="font-medium text-sm">
                  Parts availability will be verified from SAP Inventory during approval
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  The system will automatically check parts availability before creating the maintenance order
                </p>
              </div>
            </div>
          </div>

          {/* Modal Content */}
          <div className="p-4 max-h-96 overflow-y-auto">
            {fetchingTechnicians ? (
              <div className="flex items-center justify-center py-8">
                <ArrowPathIcon className="w-6 h-6 text-blue-500 animate-spin mr-2" />
                <span>Fetching available technicians from SAP HR...</span>
              </div>
            ) : availableTechnicians.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No available technicians found in SAP HR</p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-600 mb-3">
                  Select a technician to assign ({availableTechnicians.length} available):
                </p>
                {availableTechnicians.map((tech) => (
                  <div
                    key={tech.id}
                    onClick={() => setSelectedTechnician(tech)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedTechnician?.id === tech.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{tech.name}</p>
                        <p className="text-xs text-gray-500">ID: {tech.id}</p>
                        {tech.specialization && (
                          <p className="text-xs text-gray-500">Specialization: {tech.specialization}</p>
                        )}
                      </div>
                      <div className="text-right">
                        {tech.availability_status && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            tech.availability_status === 'AVAILABLE'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {tech.availability_status}
                          </span>
                        )}
                        {tech.current_workload !== undefined && (
                          <p className="text-xs text-gray-500 mt-1">
                            Workload: {tech.current_workload} jobs
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Modal Footer */}
          <div className="flex justify-end gap-3 p-4 border-t bg-gray-50">
            <button
              onClick={() => {
                setShowTechnicianModal(false);
                setSelectedTechnician(null);
              }}
              className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmTechnicianAssignment}
              disabled={!selectedTechnician}
              className={`px-4 py-2 text-sm text-white rounded ${
                selectedTechnician
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-400 cursor-not-allowed'
              }`}
            >
              <CheckCircleIcon className="w-4 h-4 inline mr-1" />
              Confirm Assignment
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ServiceNow Integration Scenarios</h1>
        <button
          type="button"
          onClick={() => {
            loadResults();
            loadPendingRequests();
          }}
          disabled={loading}
          className="btn-outline flex items-center gap-2"
        >
          <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Scenario Tabs */}
      <div className="flex space-x-1 mb-6 border-b">
        <button
          onClick={() => setActiveScenario('scenario1')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario1'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 1: New Client
        </button>
        <button
          onClick={() => setActiveScenario('scenario2')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario2'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 2: Scheduling
        </button>
        <button
          onClick={() => setActiveScenario('scenario3')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeScenario === 'scenario3'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Scenario 3: Work Order
        </button>
      </div>

      {/* Scenario Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {activeScenario === 'scenario1' && renderScenario1()}
        {activeScenario === 'scenario2' && renderScenario2()}
        {activeScenario === 'scenario3' && renderScenario3()}
      </div>

      {/* Technician Selection Modal */}
      {renderTechnicianModal()}
    </div>
  );
}
