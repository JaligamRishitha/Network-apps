/**
 * PM Workflow - Screen 3: Order Release & Execution Readiness
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSAPToast } from '../hooks/useSAPToast';
import { useSAPDialog } from '../hooks/useSAPDialog';
import SAPToast from '../components/SAPToast';
import SAPDialog from '../components/SAPDialog';
import '../styles/sap-theme.css';

interface ReadinessChecklist {
  order_number: string;
  order_type: string;
  current_status: string;
  can_release: boolean;
  blocking_reasons: string[];
  checklist: {
    permits: {
      status: string;
      detail: any[];
    };
    materials: {
      status: string;
      detail: any[];
    };
    technician: {
      status: string;
      detail: any[];
    };
  };
}

const PMWorkflowScreen3: React.FC = () => {
  const { user } = useAuth();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();
  const { dialogState, openDialog, closeDialog } = useSAPDialog();

  const [orderNumber, setOrderNumber] = useState('');
  const [checklist, setChecklist] = useState<ReadinessChecklist | null>(null);
  const [loading, setLoading] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverrideDialog, setShowOverrideDialog] = useState(false);

  // Load readiness checklist
  const loadChecklist = async () => {
    if (!orderNumber) {
      showError('Please enter an order number');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/pm-workflow/orders/${orderNumber}/readiness-checklist`,
        {
          headers: {
            'Authorization': `Bearer ${user?.token || ''}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load readiness checklist');
      }

      const data = await response.json();
      setChecklist(data);
      showSuccess('Readiness checklist loaded');
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to load checklist');
      setChecklist(null);
    } finally {
      setLoading(false);
    }
  };

  // Release order
  const handleRelease = async (withOverride: boolean = false) => {
    if (!orderNumber) {
      showError('Please enter an order number');
      return;
    }

    if (withOverride && !overrideReason) {
      showError('Please provide an override reason');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/pm-workflow/orders/${orderNumber}/release`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${user?.token || ''}`,
          },
          body: JSON.stringify({
            released_by: user?.username || 'system',
            override_blocks: withOverride,
            override_reason: withOverride ? overrideReason : null,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to release order');
      }

      const data = await response.json();
      showSuccess(`Order ${data.order_number} released successfully`);
      setShowOverrideDialog(false);
      setOverrideReason('');
      
      // Reload checklist
      await loadChecklist();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to release order');
    } finally {
      setLoading(false);
    }
  };

  // Assign technician to operation
  const handleAssignTechnician = async (operationId: string, technicianId: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/pm-workflow/operations/${operationId}/assign-technician`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${user?.token || ''}`,
          },
          body: JSON.stringify({
            technician_id: technicianId,
            assigned_by: user?.username || 'system',
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to assign technician');
      }

      showSuccess('Technician assigned successfully');
      
      // Reload checklist
      await loadChecklist();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to assign technician');
    } finally {
      setLoading(false);
    }
  };

  // Get status badge color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'approved':
      case 'available':
      case 'assigned':
        return 'bg-green-100 text-green-800';
      case 'pending':
      case 'unavailable':
      case 'not_assigned':
        return 'bg-yellow-100 text-yellow-800';
      case 'not_required':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="sap-page">
      <div className="sap-page-header">
        <h1 className="sap-page-title">Screen 3: Order Release & Execution Readiness</h1>
        <p className="sap-page-subtitle">
          Validate prerequisites and release orders for execution
        </p>
      </div>

      <div className="sap-content">
        {/* Order Selection */}
        <div className="sap-card mb-6">
          <div className="sap-card-header">
            <h2 className="sap-card-title">Order Selection</h2>
          </div>
          <div className="sap-card-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="sap-label">Order Number</label>
                <input
                  type="text"
                  className="sap-input"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  placeholder="Enter order number"
                />
              </div>
              <div className="flex items-end">
                <button
                  className="sap-button-primary w-full"
                  onClick={loadChecklist}
                  disabled={loading || !orderNumber}
                >
                  {loading ? 'Loading...' : 'Load Checklist'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Readiness Checklist */}
        {checklist && (
          <>
            {/* Order Info */}
            <div className="sap-card mb-6">
              <div className="sap-card-header">
                <h2 className="sap-card-title">Order Information</h2>
              </div>
              <div className="sap-card-content">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="sap-label">Order Number</label>
                    <p className="text-sm font-medium">{checklist.order_number}</p>
                  </div>
                  <div>
                    <label className="sap-label">Order Type</label>
                    <p className="text-sm font-medium capitalize">{checklist.order_type}</p>
                  </div>
                  <div>
                    <label className="sap-label">Current Status</label>
                    <p className="text-sm font-medium capitalize">{checklist.current_status.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <label className="sap-label">Can Release</label>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                      checklist.can_release ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {checklist.can_release ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Blocking Reasons */}
            {checklist.blocking_reasons.length > 0 && (
              <div className="sap-card mb-6 border-l-4 border-yellow-500">
                <div className="sap-card-header">
                  <h2 className="sap-card-title text-yellow-800">Blocking Reasons</h2>
                </div>
                <div className="sap-card-content">
                  <ul className="list-disc list-inside space-y-1">
                    {checklist.blocking_reasons.map((reason, index) => (
                      <li key={index} className="text-sm text-yellow-800">{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Permits Checklist */}
            <div className="sap-card mb-6">
              <div className="sap-card-header">
                <h2 className="sap-card-title">Permits</h2>
                <span className={`px-3 py-1 text-xs font-semibold rounded ${getStatusColor(checklist.checklist.permits.status)}`}>
                  {checklist.checklist.permits.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="sap-card-content">
                {checklist.checklist.permits.detail.length > 0 ? (
                  <div className="sap-table-container">
                    <table className="sap-table">
                      <thead>
                        <tr>
                          <th>Permit ID</th>
                          <th>Type</th>
                          <th>Approver</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {checklist.checklist.permits.detail.map((permit, index) => (
                          <tr key={index}>
                            <td>{permit.permit_id}</td>
                            <td className="capitalize">{permit.permit_type}</td>
                            <td>{permit.approver}</td>
                            <td>
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                permit.approved ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {permit.approved ? 'Approved' : 'Pending'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">No permits required</p>
                )}
              </div>
            </div>

            {/* Materials Checklist */}
            <div className="sap-card mb-6">
              <div className="sap-card-header">
                <h2 className="sap-card-title">Materials</h2>
                <span className={`px-3 py-1 text-xs font-semibold rounded ${getStatusColor(checklist.checklist.materials.status)}`}>
                  {checklist.checklist.materials.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="sap-card-content">
                {checklist.checklist.materials.detail.length > 0 ? (
                  <div className="sap-table-container">
                    <table className="sap-table">
                      <thead>
                        <tr>
                          <th>Component ID</th>
                          <th>Material Number</th>
                          <th>Available</th>
                          <th>On Order</th>
                        </tr>
                      </thead>
                      <tbody>
                        {checklist.checklist.materials.detail.map((material, index) => (
                          <tr key={index}>
                            <td>{material.component_id}</td>
                            <td>{material.material_number || 'N/A'}</td>
                            <td>
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                material.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {material.available ? 'Yes' : 'No'}
                              </span>
                            </td>
                            <td>
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                material.on_order ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                              }`}>
                                {material.on_order ? 'Yes' : 'No'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">No critical materials</p>
                )}
              </div>
            </div>

            {/* Technician Assignment */}
            <div className="sap-card mb-6">
              <div className="sap-card-header">
                <h2 className="sap-card-title">Technician Assignment</h2>
                <span className={`px-3 py-1 text-xs font-semibold rounded ${getStatusColor(checklist.checklist.technician.status)}`}>
                  {checklist.checklist.technician.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="sap-card-content">
                <div className="sap-table-container">
                  <table className="sap-table">
                    <thead>
                      <tr>
                        <th>Operation ID</th>
                        <th>Operation Number</th>
                        <th>Technician ID</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checklist.checklist.technician.detail.map((op, index) => (
                        <tr key={index}>
                          <td>{op.operation_id}</td>
                          <td>{op.operation_number}</td>
                          <td>{op.technician_id || 'Not assigned'}</td>
                          <td>
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${
                              op.technician_id ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {op.technician_id ? 'Assigned' : 'Not Assigned'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Release Actions */}
            <div className="sap-card">
              <div className="sap-card-header">
                <h2 className="sap-card-title">Release Actions</h2>
              </div>
              <div className="sap-card-content">
                <div className="flex gap-4">
                  <button
                    className="sap-button-primary"
                    onClick={() => handleRelease(false)}
                    disabled={loading || !checklist.can_release}
                  >
                    Release Order
                  </button>
                  {!checklist.can_release && checklist.order_type === 'general' && (
                    <button
                      className="sap-button-secondary"
                      onClick={() => setShowOverrideDialog(true)}
                      disabled={loading}
                    >
                      Release with Override
                    </button>
                  )}
                  <button
                    className="sap-button-secondary"
                    onClick={loadChecklist}
                    disabled={loading}
                  >
                    Refresh Checklist
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Override Dialog */}
      {showOverrideDialog && (
        <SAPDialog
          isOpen={showOverrideDialog}
          onClose={() => setShowOverrideDialog(false)}
          title="Release with Override"
          type="warning"
        >
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              You are about to override blocking conditions. Please provide a reason for this override.
            </p>
            <div>
              <label className="sap-label">Override Reason</label>
              <textarea
                className="sap-input"
                rows={4}
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Enter reason for override..."
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                className="sap-button-secondary"
                onClick={() => {
                  setShowOverrideDialog(false);
                  setOverrideReason('');
                }}
              >
                Cancel
              </button>
              <button
                className="sap-button-primary"
                onClick={() => handleRelease(true)}
                disabled={loading || !overrideReason}
              >
                Confirm Override
              </button>
            </div>
          </div>
        </SAPDialog>
      )}

      <SAPToast
        message={toastState.message}
        type={toastState.type}
        isOpen={toastState.isOpen}
        onClose={closeToast}
      />
    </div>
  );
};

export default PMWorkflowScreen3;
