/**
 * PM Workflow - Screen 1: Order Planning & Initiation
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPToast from '../components/SAPToast';
import '../styles/sap-theme.css';

interface Operation {
  operation_number: string;
  work_center: string;
  description: string;
  planned_hours: number;
  technician_id?: string;
}

interface Component {
  material_number?: string;
  description: string;
  quantity_required: number;
  unit_of_measure: string;
  estimated_cost: number;
  has_master_data: boolean;
}

interface CostSummary {
  estimated_material_cost: number;
  estimated_labor_cost: number;
  estimated_external_cost: number;
  estimated_total_cost: number;
}

const PMWorkflowScreen1: React.FC = () => {
  const { user } = useAuth();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  // Order header state
  const [orderType, setOrderType] = useState<'general' | 'breakdown'>('general');
  const [equipmentId, setEquipmentId] = useState('');
  const [functionalLocation, setFunctionalLocation] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high' | 'urgent'>('normal');
  const [plannedStartDate, setPlannedStartDate] = useState('');
  const [plannedEndDate, setPlannedEndDate] = useState('');
  const [breakdownNotificationId, setBreakdownNotificationId] = useState('');

  // Operations state
  const [operations, setOperations] = useState<Operation[]>([]);
  const [newOperation, setNewOperation] = useState<Operation>({
    operation_number: '',
    work_center: '',
    description: '',
    planned_hours: 0,
    technician_id: ''
  });

  // Components state
  const [components, setComponents] = useState<Component[]>([]);
  const [newComponent, setNewComponent] = useState<Component>({
    material_number: '',
    description: '',
    quantity_required: 0,
    unit_of_measure: 'EA',
    estimated_cost: 0,
    has_master_data: true
  });

  // Cost summary state
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(false);

  // Add operation to list
  const handleAddOperation = () => {
    if (!newOperation.operation_number || !newOperation.work_center || !newOperation.description) {
      showError('Please fill in all required operation fields');
      return;
    }
    setOperations([...operations, { ...newOperation }]);
    setNewOperation({
      operation_number: '',
      work_center: '',
      description: '',
      planned_hours: 0,
      technician_id: ''
    });
    showSuccess('Operation added');
  };

  // Remove operation from list
  const handleRemoveOperation = (index: number) => {
    setOperations(operations.filter((_, i) => i !== index));
  };

  // Add component to list
  const handleAddComponent = () => {
    if (!newComponent.description || newComponent.quantity_required <= 0) {
      showError('Please fill in all required component fields');
      return;
    }
    setComponents([...components, { ...newComponent }]);
    setNewComponent({
      material_number: '',
      description: '',
      quantity_required: 0,
      unit_of_measure: 'EA',
      estimated_cost: 0,
      has_master_data: true
    });
    showSuccess('Component added');
  };

  // Remove component from list
  const handleRemoveComponent = (index: number) => {
    setComponents(components.filter((_, i) => i !== index));
  };

  // Calculate cost estimate
  const handleCalculateCosts = () => {
    const materialCost = components.reduce((sum, comp) => sum + comp.estimated_cost, 0);
    const laborCost = operations.reduce((sum, op) => sum + (op.planned_hours * 50), 0); // $50/hour
    const externalCost = 0; // Placeholder
    const totalCost = materialCost + laborCost + externalCost;

    setCostSummary({
      estimated_material_cost: materialCost,
      estimated_labor_cost: laborCost,
      estimated_external_cost: externalCost,
      estimated_total_cost: totalCost
    });
    showSuccess('Cost estimate calculated');
  };

  // Create order
  const handleCreateOrder = async () => {
    // Validation
    if (!equipmentId && !functionalLocation) {
      showError('Either Equipment ID or Functional Location is required');
      return;
    }
    if (operations.length === 0) {
      showError('At least one operation is required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/pm-workflow/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          order_type: orderType,
          equipment_id: equipmentId || null,
          functional_location: functionalLocation || null,
          priority,
          planned_start_date: plannedStartDate ? new Date(plannedStartDate).toISOString() : null,
          planned_end_date: plannedEndDate ? new Date(plannedEndDate).toISOString() : null,
          breakdown_notification_id: breakdownNotificationId || null,
          created_by: user?.username || 'system',
          operations,
          components,
          permits: []
        })
      });

      if (!response.ok) {
        const error = await response.json();
        console.error('API Error Response:', error);
        throw new Error(error.detail || 'Failed to create order');
      }

      const data = await response.json();
      showSuccess(`Order created successfully: ${data.order_number}`);
      
      // Reset form
      resetForm();
    } catch (error: any) {
      console.error('Create order error:', error);
      showError(error.message || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setOrderType('general');
    setEquipmentId('');
    setFunctionalLocation('');
    setPriority('normal');
    setPlannedStartDate('');
    setPlannedEndDate('');
    setBreakdownNotificationId('');
    setOperations([]);
    setComponents([]);
    setCostSummary(null);
  };

  return (
    <div className="sap-container">
      <div className="sap-header">
        <h1 className="sap-title">Screen 1: Order Planning & Initiation</h1>
        <div className="sap-subtitle">Create and plan maintenance orders</div>
      </div>

      <div className="sap-content">
        {/* Order Header Section */}
        <div className="sap-section">
          <div className="sap-section-header">
            <h2 className="sap-section-title">Order Header</h2>
          </div>
          <div className="sap-section-content">
            <div className="sap-form-grid">
              <div className="sap-form-group">
                <label className="sap-label">Order Type *</label>
                <select
                  className="sap-input"
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as 'general' | 'breakdown')}
                >
                  <option value="general">General Maintenance</option>
                  <option value="breakdown">Breakdown Maintenance</option>
                </select>
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Priority *</label>
                <select
                  className="sap-input"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as any)}
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Equipment ID</label>
                <input
                  type="text"
                  className="sap-input"
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  placeholder="e.g., EQ-12345"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Functional Location</label>
                <input
                  type="text"
                  className="sap-input"
                  value={functionalLocation}
                  onChange={(e) => setFunctionalLocation(e.target.value)}
                  placeholder="e.g., PLANT-01-AREA-A"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Planned Start Date</label>
                <input
                  type="datetime-local"
                  className="sap-input"
                  value={plannedStartDate}
                  onChange={(e) => setPlannedStartDate(e.target.value)}
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Planned End Date</label>
                <input
                  type="datetime-local"
                  className="sap-input"
                  value={plannedEndDate}
                  onChange={(e) => setPlannedEndDate(e.target.value)}
                />
              </div>

              {orderType === 'breakdown' && (
                <div className="sap-form-group">
                  <label className="sap-label">Breakdown Notification ID</label>
                  <input
                    type="text"
                    className="sap-input"
                    value={breakdownNotificationId}
                    onChange={(e) => setBreakdownNotificationId(e.target.value)}
                    placeholder="e.g., NOTIF-12345"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Operations Section */}
        <div className="sap-section">
          <div className="sap-section-header">
            <h2 className="sap-section-title">Operations</h2>
          </div>
          <div className="sap-section-content">
            {/* Add Operation Form */}
            <div className="sap-form-grid" style={{ marginBottom: '1rem' }}>
              <div className="sap-form-group">
                <label className="sap-label">Operation Number *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newOperation.operation_number}
                  onChange={(e) => setNewOperation({ ...newOperation, operation_number: e.target.value })}
                  placeholder="e.g., PM01"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Work Center *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newOperation.work_center}
                  onChange={(e) => setNewOperation({ ...newOperation, work_center: e.target.value })}
                  placeholder="e.g., MAINT-01"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Description *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newOperation.description}
                  onChange={(e) => setNewOperation({ ...newOperation, description: e.target.value })}
                  placeholder="Operation description"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Planned Hours *</label>
                <input
                  type="number"
                  className="sap-input"
                  value={newOperation.planned_hours}
                  onChange={(e) => setNewOperation({ ...newOperation, planned_hours: parseFloat(e.target.value) })}
                  min="0"
                  step="0.5"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Technician ID</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newOperation.technician_id}
                  onChange={(e) => setNewOperation({ ...newOperation, technician_id: e.target.value })}
                  placeholder="Optional"
                />
              </div>

              <div className="sap-form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button className="sap-button sap-button-primary" onClick={handleAddOperation}>
                  Add Operation
                </button>
              </div>
            </div>

            {/* Operations Table */}
            {operations.length > 0 && (
              <div className="sap-table-container">
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>Op. No.</th>
                      <th>Work Center</th>
                      <th>Description</th>
                      <th>Planned Hours</th>
                      <th>Technician</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {operations.map((op, index) => (
                      <tr key={index}>
                        <td>{op.operation_number}</td>
                        <td>{op.work_center}</td>
                        <td>{op.description}</td>
                        <td>{op.planned_hours}</td>
                        <td>{op.technician_id || '-'}</td>
                        <td>
                          <button
                            className="sap-button sap-button-secondary"
                            onClick={() => handleRemoveOperation(index)}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Components Section */}
        <div className="sap-section">
          <div className="sap-section-header">
            <h2 className="sap-section-title">Components (Materials)</h2>
          </div>
          <div className="sap-section-content">
            {/* Add Component Form */}
            <div className="sap-form-grid" style={{ marginBottom: '1rem' }}>
              <div className="sap-form-group">
                <label className="sap-label">Material Number</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newComponent.material_number}
                  onChange={(e) => setNewComponent({ ...newComponent, material_number: e.target.value })}
                  placeholder="Optional"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Description *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newComponent.description}
                  onChange={(e) => setNewComponent({ ...newComponent, description: e.target.value })}
                  placeholder="Component description"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Quantity *</label>
                <input
                  type="number"
                  className="sap-input"
                  value={newComponent.quantity_required}
                  onChange={(e) => setNewComponent({ ...newComponent, quantity_required: parseFloat(e.target.value) })}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Unit *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={newComponent.unit_of_measure}
                  onChange={(e) => setNewComponent({ ...newComponent, unit_of_measure: e.target.value })}
                  placeholder="e.g., EA, KG, L"
                />
              </div>

              <div className="sap-form-group">
                <label className="sap-label">Estimated Cost *</label>
                <input
                  type="number"
                  className="sap-input"
                  value={newComponent.estimated_cost}
                  onChange={(e) => setNewComponent({ ...newComponent, estimated_cost: parseFloat(e.target.value) })}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="sap-form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button className="sap-button sap-button-primary" onClick={handleAddComponent}>
                  Add Component
                </button>
              </div>
            </div>

            {/* Components Table */}
            {components.length > 0 && (
              <div className="sap-table-container">
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>Material No.</th>
                      <th>Description</th>
                      <th>Quantity</th>
                      <th>Unit</th>
                      <th>Est. Cost</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {components.map((comp, index) => (
                      <tr key={index}>
                        <td>{comp.material_number || '-'}</td>
                        <td>{comp.description}</td>
                        <td>{comp.quantity_required}</td>
                        <td>{comp.unit_of_measure}</td>
                        <td>${comp.estimated_cost.toFixed(2)}</td>
                        <td>
                          <button
                            className="sap-button sap-button-secondary"
                            onClick={() => handleRemoveComponent(index)}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Cost Summary Section */}
        <div className="sap-section">
          <div className="sap-section-header">
            <h2 className="sap-section-title">Cost Estimate</h2>
          </div>
          <div className="sap-section-content">
            <button
              className="sap-button sap-button-primary"
              onClick={handleCalculateCosts}
              style={{ marginBottom: '1rem' }}
            >
              Calculate Cost Estimate
            </button>

            {costSummary && (
              <div className="sap-info-box">
                <div className="sap-form-grid">
                  <div className="sap-form-group">
                    <label className="sap-label">Material Cost</label>
                    <div className="sap-value">${costSummary.estimated_material_cost.toFixed(2)}</div>
                  </div>
                  <div className="sap-form-group">
                    <label className="sap-label">Labor Cost</label>
                    <div className="sap-value">${costSummary.estimated_labor_cost.toFixed(2)}</div>
                  </div>
                  <div className="sap-form-group">
                    <label className="sap-label">External Cost</label>
                    <div className="sap-value">${costSummary.estimated_external_cost.toFixed(2)}</div>
                  </div>
                  <div className="sap-form-group">
                    <label className="sap-label">Total Cost</label>
                    <div className="sap-value" style={{ fontWeight: 'bold', fontSize: '1.2em' }}>
                      ${costSummary.estimated_total_cost.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="sap-button-bar">
          <button
            className="sap-button sap-button-primary"
            onClick={handleCreateOrder}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Order'}
          </button>
          <button
            className="sap-button sap-button-secondary"
            onClick={resetForm}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </div>

      <SAPToast {...toastState} onClose={closeToast} />
    </div>
  );
};

export default PMWorkflowScreen1;
