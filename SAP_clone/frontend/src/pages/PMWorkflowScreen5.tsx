/**
 * PM Workflow - Screen 5: Work Execution & Confirmation
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPToast from '../components/SAPToast';
import PMWorkflowNav from '../components/PMWorkflowNav';
import '../styles/sap-theme.css';

interface GoodsIssue {
  material_number: string;
  quantity_issued: number;
  cost_center: string;
}

interface Confirmation {
  operation_id: string;
  confirmation_type: 'internal' | 'external';
  actual_hours: number;
  work_notes: string;
  vendor_id?: string;
}

interface MalfunctionReport {
  cause_code: string;
  description: string;
  root_cause?: string;
  corrective_action?: string;
}

const PMWorkflowScreen5: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  const [loading, setLoading] = useState(false);
  const [orderData, setOrderData] = useState<any>(null);
  
  // Goods Issue state
  const [goodsIssue, setGoodsIssue] = useState<GoodsIssue>({
    material_number: '',
    quantity_issued: 0,
    cost_center: 'CC-MAINT-001'
  });
  const [goodsIssues, setGoodsIssues] = useState<any[]>([]);

  // Confirmation state
  const [confirmation, setConfirmation] = useState<Confirmation>({
    operation_id: '',
    confirmation_type: 'internal',
    actual_hours: 0,
    work_notes: '',
    vendor_id: ''
  });
  const [confirmations, setConfirmations] = useState<any[]>([]);

  // Malfunction Report state
  const [malfunctionReport, setMalfunctionReport] = useState<MalfunctionReport>({
    cause_code: '',
    description: '',
    root_cause: '',
    corrective_action: ''
  });
  const [showMalfunctionForm, setShowMalfunctionForm] = useState(false);

  useEffect(() => {
    if (orderNumber) {
      loadOrderData();
      loadGoodsIssues();
      loadConfirmations();
    }
  }, [orderNumber]);

  const loadOrderData = async () => {
    try {
      const response = await fetch(`/api/pm-workflow/orders/${orderNumber}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOrderData(data);
      }
    } catch (error) {
      console.error('Error loading order:', error);
    }
  };

  const loadGoodsIssues = async () => {
    try {
      const response = await fetch(`/api/pm-workflow/orders/${orderNumber}/goods-issues`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGoodsIssues(data);
      }
    } catch (error) {
      console.error('Error loading goods issues:', error);
    }
  };

  const loadConfirmations = async () => {
    try {
      const response = await fetch(`/api/pm-workflow/orders/${orderNumber}/confirmations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfirmations(data);
      }
    } catch (error) {
      console.error('Error loading confirmations:', error);
    }
  };

  const handlePostGoodsIssue = async () => {
    if (!goodsIssue.material_number || goodsIssue.quantity_issued <= 0) {
      showError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/pm-workflow/goods-issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          order_number: orderNumber,
          material_number: goodsIssue.material_number,
          quantity_issued: goodsIssue.quantity_issued,
          cost_center: goodsIssue.cost_center,
          issued_by: user?.username || 'system'
        })
      });

      if (response.ok) {
        showSuccess('Goods issue posted successfully');
        setGoodsIssue({
          material_number: '',
          quantity_issued: 0,
          cost_center: 'CC-MAINT-001'
        });
        loadGoodsIssues();
        loadOrderData();
      } else {
        const error = await response.json();
        showError(error.detail || 'Failed to post goods issue');
      }
    } catch (error) {
      showError('Error posting goods issue');
    } finally {
      setLoading(false);
    }
  };

  const handlePostConfirmation = async () => {
    if (!confirmation.operation_id || confirmation.actual_hours <= 0) {
      showError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/pm-workflow/confirmations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          order_number: orderNumber,
          operation_id: confirmation.operation_id,
          confirmation_type: confirmation.confirmation_type,
          actual_hours: confirmation.actual_hours,
          work_notes: confirmation.work_notes,
          vendor_id: confirmation.vendor_id || null,
          confirmed_by: user?.username || 'system'
        })
      });

      if (response.ok) {
        showSuccess('Confirmation posted successfully');
        setConfirmation({
          operation_id: '',
          confirmation_type: 'internal',
          actual_hours: 0,
          work_notes: '',
          vendor_id: ''
        });
        loadConfirmations();
        loadOrderData();
      } else {
        const error = await response.json();
        showError(error.detail || 'Failed to post confirmation');
      }
    } catch (error) {
      showError('Error posting confirmation');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitMalfunctionReport = async () => {
    if (!malfunctionReport.cause_code || !malfunctionReport.description) {
      showError('Please fill in cause code and description');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/pm-workflow/orders/${orderNumber}/malfunction-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...malfunctionReport,
          reported_by: user?.username || 'system'
        })
      });

      if (response.ok) {
        showSuccess('Malfunction report submitted successfully');
        setShowMalfunctionForm(false);
        setMalfunctionReport({
          cause_code: '',
          description: '',
          root_cause: '',
          corrective_action: ''
        });
      } else {
        const error = await response.json();
        showError(error.detail || 'Failed to submit malfunction report');
      }
    } catch (error) {
      showError('Error submitting malfunction report');
    } finally {
      setLoading(false);
    }
  };

  if (!orderNumber) {
    return (
      <div className="sap-page">
        <PMWorkflowNav currentScreen={5} />
        <div className="sap-container" style={{ padding: '40px', textAlign: 'center' }}>
          <h2>No Order Selected</h2>
          <p>Please select an order from Screen 1 to continue.</p>
          <button 
            className="sap-button sap-button-emphasized"
            onClick={() => navigate('/pm-workflow/screen1')}
          >
            Go to Screen 1
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="sap-page">
      <PMWorkflowNav orderNumber={orderNumber} currentScreen={5} />
      
      <div className="sap-container" style={{ padding: '24px' }}>
        <div className="sap-object-page-header">
          <h1 className="sap-object-page-title">Screen 5: Work Execution & Confirmation</h1>
          <p className="sap-object-page-subtitle">Order: {orderNumber}</p>
        </div>

        {/* Order Status */}
        {orderData && (
          <div className="sap-panel" style={{ marginBottom: '24px' }}>
            <div className="sap-panel-header">
              <h3>Order Status</h3>
            </div>
            <div className="sap-panel-content">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Status</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{orderData.status}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Type</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{orderData.order_type}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Priority</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{orderData.priority}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Goods Issue Section */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Goods Issue (GI)</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirement 5.1: GI must be posted before confirmation</span>
          </div>
          <div className="sap-panel-content">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '16px', marginBottom: '16px' }}>
              <div className="sap-form-group">
                <label className="sap-label">Material Number *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={goodsIssue.material_number}
                  onChange={(e) => setGoodsIssue({ ...goodsIssue, material_number: e.target.value })}
                  placeholder="MAT-001"
                />
              </div>
              <div className="sap-form-group">
                <label className="sap-label">Quantity *</label>
                <input
                  type="number"
                  className="sap-input"
                  value={goodsIssue.quantity_issued}
                  onChange={(e) => setGoodsIssue({ ...goodsIssue, quantity_issued: parseFloat(e.target.value) })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="sap-form-group">
                <label className="sap-label">Cost Center *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={goodsIssue.cost_center}
                  onChange={(e) => setGoodsIssue({ ...goodsIssue, cost_center: e.target.value })}
                />
              </div>
              <div className="sap-form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button
                  className="sap-button sap-button-emphasized"
                  onClick={handlePostGoodsIssue}
                  disabled={loading}
                >
                  Post GI
                </button>
              </div>
            </div>

            {/* Goods Issues List */}
            {goodsIssues.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Posted Goods Issues</h4>
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>GI Document</th>
                      <th>Material</th>
                      <th>Quantity</th>
                      <th>Cost Center</th>
                      <th>Date</th>
                      <th>Issued By</th>
                    </tr>
                  </thead>
                  <tbody>
                    {goodsIssues.map((gi, index) => (
                      <tr key={index}>
                        <td>{gi.gi_document}</td>
                        <td>{gi.material_number}</td>
                        <td>{gi.quantity_issued}</td>
                        <td>{gi.cost_center}</td>
                        <td>{new Date(gi.issue_date).toLocaleString()}</td>
                        <td>{gi.issued_by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Confirmation Section */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Work Confirmation</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirements 5.3, 5.4: Confirm completed work</span>
          </div>
          <div className="sap-panel-content">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div className="sap-form-group">
                <label className="sap-label">Operation ID *</label>
                <select
                  className="sap-select"
                  value={confirmation.operation_id}
                  onChange={(e) => setConfirmation({ ...confirmation, operation_id: e.target.value })}
                >
                  <option value="">Select Operation</option>
                  {orderData?.operations?.map((op: any) => (
                    <option key={op.operation_id} value={op.operation_id}>
                      {op.operation_number} - {op.description}
                    </option>
                  ))}
                </select>
              </div>
              <div className="sap-form-group">
                <label className="sap-label">Confirmation Type *</label>
                <select
                  className="sap-select"
                  value={confirmation.confirmation_type}
                  onChange={(e) => setConfirmation({ ...confirmation, confirmation_type: e.target.value as 'internal' | 'external' })}
                >
                  <option value="internal">Internal</option>
                  <option value="external">External</option>
                </select>
              </div>
              <div className="sap-form-group">
                <label className="sap-label">Actual Hours *</label>
                <input
                  type="number"
                  className="sap-input"
                  value={confirmation.actual_hours}
                  onChange={(e) => setConfirmation({ ...confirmation, actual_hours: parseFloat(e.target.value) })}
                  min="0"
                  step="0.5"
                />
              </div>
              {confirmation.confirmation_type === 'external' && (
                <div className="sap-form-group">
                  <label className="sap-label">Vendor ID</label>
                  <input
                    type="text"
                    className="sap-input"
                    value={confirmation.vendor_id}
                    onChange={(e) => setConfirmation({ ...confirmation, vendor_id: e.target.value })}
                    placeholder="VENDOR-001"
                  />
                </div>
              )}
            </div>
            <div className="sap-form-group" style={{ marginBottom: '16px' }}>
              <label className="sap-label">Work Notes</label>
              <textarea
                className="sap-textarea"
                value={confirmation.work_notes}
                onChange={(e) => setConfirmation({ ...confirmation, work_notes: e.target.value })}
                rows={3}
                placeholder="Describe work performed..."
              />
            </div>
            <button
              className="sap-button sap-button-emphasized"
              onClick={handlePostConfirmation}
              disabled={loading}
            >
              Post Confirmation
            </button>

            {/* Confirmations List */}
            {confirmations.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Posted Confirmations</h4>
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>Confirmation ID</th>
                      <th>Operation</th>
                      <th>Type</th>
                      <th>Hours</th>
                      <th>Date</th>
                      <th>Confirmed By</th>
                    </tr>
                  </thead>
                  <tbody>
                    {confirmations.map((conf, index) => (
                      <tr key={index}>
                        <td>{conf.confirmation_id}</td>
                        <td>{conf.operation_id}</td>
                        <td>{conf.confirmation_type}</td>
                        <td>{conf.actual_hours}</td>
                        <td>{new Date(conf.confirmation_date).toLocaleString()}</td>
                        <td>{conf.confirmed_by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Malfunction Report Section */}
        <div className="sap-panel">
          <div className="sap-panel-header">
            <h3>Malfunction Report</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirement 5.5: Report malfunctions (mandatory for breakdown orders)</span>
          </div>
          <div className="sap-panel-content">
            {!showMalfunctionForm ? (
              <button
                className="sap-button"
                onClick={() => setShowMalfunctionForm(true)}
              >
                Report Malfunction
              </button>
            ) : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                  <div className="sap-form-group">
                    <label className="sap-label">Cause Code *</label>
                    <input
                      type="text"
                      className="sap-input"
                      value={malfunctionReport.cause_code}
                      onChange={(e) => setMalfunctionReport({ ...malfunctionReport, cause_code: e.target.value })}
                      placeholder="e.g., MECH-FAIL"
                    />
                  </div>
                  <div className="sap-form-group">
                    <label className="sap-label">Description *</label>
                    <input
                      type="text"
                      className="sap-input"
                      value={malfunctionReport.description}
                      onChange={(e) => setMalfunctionReport({ ...malfunctionReport, description: e.target.value })}
                      placeholder="Brief description"
                    />
                  </div>
                </div>
                <div className="sap-form-group" style={{ marginBottom: '16px' }}>
                  <label className="sap-label">Root Cause</label>
                  <textarea
                    className="sap-textarea"
                    value={malfunctionReport.root_cause}
                    onChange={(e) => setMalfunctionReport({ ...malfunctionReport, root_cause: e.target.value })}
                    rows={2}
                    placeholder="Detailed root cause analysis..."
                  />
                </div>
                <div className="sap-form-group" style={{ marginBottom: '16px' }}>
                  <label className="sap-label">Corrective Action</label>
                  <textarea
                    className="sap-textarea"
                    value={malfunctionReport.corrective_action}
                    onChange={(e) => setMalfunctionReport({ ...malfunctionReport, corrective_action: e.target.value })}
                    rows={2}
                    placeholder="Actions taken to correct the issue..."
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="sap-button sap-button-emphasized"
                    onClick={handleSubmitMalfunctionReport}
                    disabled={loading}
                  >
                    Submit Report
                  </button>
                  <button
                    className="sap-button"
                    onClick={() => setShowMalfunctionForm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
          <button
            className="sap-button"
            onClick={() => navigate('/pm-workflow/screen4')}
          >
            ← Previous: Material Receipt
          </button>
          <button
            className="sap-button sap-button-emphasized"
            onClick={() => navigate(`/pm-workflow/screen6/${orderNumber}`)}
          >
            Next: Completion →
          </button>
        </div>
      </div>

      <SAPToast
        message={toastState.message}
        type={toastState.type}
        isOpen={toastState.isOpen}
        onClose={closeToast}
      />
    </div>
  );
};

export default PMWorkflowScreen5;
