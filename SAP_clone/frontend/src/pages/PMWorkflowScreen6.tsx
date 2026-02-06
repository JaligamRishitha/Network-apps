/**
 * PM Workflow - Screen 6: Completion & Cost Settlement
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPToast from '../components/SAPToast';
import PMWorkflowNav from '../components/PMWorkflowNav';
import '../styles/sap-theme.css';

const PMWorkflowScreen6: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  const [loading, setLoading] = useState(false);
  const [orderData, setOrderData] = useState<any>(null);

  useEffect(() => {
    if (orderNumber) {
      loadOrderData();
    }
  }, [orderNumber]);

  const loadOrderData = async () => {
    try {
      setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  if (!orderNumber) {
    return (
      <div className="sap-page">
        <PMWorkflowNav currentScreen={6} />
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
      <PMWorkflowNav orderNumber={orderNumber} currentScreen={6} />
      
      <div className="sap-container" style={{ padding: '24px' }}>
        <div className="sap-object-page-header">
          <h1 className="sap-object-page-title">Screen 6: Completion & Cost Settlement</h1>
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

        {/* Completion Checklist */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Completion Checklist</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirement 6.1-6.3: Verify prerequisites before TECO</span>
          </div>
          <div className="sap-panel-content">
            <p>All operations must be confirmed and all goods movements posted before technical completion.</p>
            <button
              className="sap-button sap-button-emphasized"
              style={{ marginTop: '16px' }}
              onClick={() => showSuccess('TECO functionality will be implemented')}
            >
              Technical Completion (TECO)
            </button>
          </div>
        </div>

        {/* Cost Analysis */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Cost Analysis</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirements 6.4-6.6: Cost variance analysis</span>
          </div>
          <div className="sap-panel-content">
            <p>View estimated vs. actual costs with variance analysis by cost element (material, labor, external).</p>
            {orderData?.cost_summary && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#666' }}>Estimated Total</div>
                    <div style={{ fontSize: '18px', fontWeight: 600 }}>
                      ${orderData.cost_summary.estimated_total_cost}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#666' }}>Actual Total</div>
                    <div style={{ fontSize: '18px', fontWeight: 600 }}>
                      ${orderData.cost_summary.actual_total_cost || '0.00'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Document Flow */}
        <div className="sap-panel" style={{ marginBottom: '24px' }}>
          <div className="sap-panel-header">
            <h3>Document Flow</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirement 9.1-9.5: Complete audit trail</span>
          </div>
          <div className="sap-panel-content">
            <p>View chronological sequence of all related documents and transactions.</p>
          </div>
        </div>

        {/* Cost Settlement */}
        <div className="sap-panel">
          <div className="sap-panel-header">
            <h3>Cost Settlement</h3>
            <span style={{ fontSize: '12px', color: '#666' }}>Requirement 6.7: Settle costs to FI</span>
          </div>
          <div className="sap-panel-content">
            <div className="sap-form-group">
              <label className="sap-label">Cost Center</label>
              <input
                type="text"
                className="sap-input"
                placeholder="CC-MAINT-001"
              />
            </div>
            <button
              className="sap-button sap-button-emphasized"
              style={{ marginTop: '16px' }}
              onClick={() => showSuccess('Cost settlement functionality will be implemented')}
            >
              Settle Costs
            </button>
          </div>
        </div>

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
          <button
            className="sap-button"
            onClick={() => navigate(`/pm-workflow/screen5/${orderNumber}`)}
          >
            ← Previous: Work Execution
          </button>
          <button
            className="sap-button"
            onClick={() => navigate('/pm-workflow')}
          >
            Back to Workflow Home
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

export default PMWorkflowScreen6;
