/**
 * PM Workflow - Screen 4: Material Receipt & Service Entry
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPToast from '../components/SAPToast';
import '../styles/sap-theme.css';

interface PurchaseOrder {
  po_number: string;
  order_number: string;
  po_type: string;
  vendor_id: string;
  total_value: number;
  delivery_date: string;
  status: string;
}

interface GoodsReceipt {
  gr_document: string;
  po_number: string;
  order_number: string;
  material_number: string;
  quantity_received: number;
  receipt_date: string;
  storage_location: string;
  received_by: string;
}

interface ServiceEntry {
  flow_id: string;
  document_type: string;
  document_number: string;
  transaction_date: string;
  user_id: string;
  status: string;
  related_document: string | null;
}

const PMWorkflowScreen4: React.FC = () => {
  const { user } = useAuth();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  // State for order selection
  const [orderNumber, setOrderNumber] = useState('');
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [selectedPO, setSelectedPO] = useState<string>('');

  // State for goods receipt
  const [grMaterialNumber, setGrMaterialNumber] = useState('');
  const [grQuantity, setGrQuantity] = useState<number>(0);
  const [grStorageLocation, setGrStorageLocation] = useState('');
  const [grQualityPassed, setGrQualityPassed] = useState(true);
  const [grQualityNotes, setGrQualityNotes] = useState('');

  // State for service entry
  const [seServiceDescription, setSeServiceDescription] = useState('');
  const [seHoursOrUnits, setSeHoursOrUnits] = useState<number>(0);
  const [seAcceptanceDate, setSeAcceptanceDate] = useState('');
  const [seServiceQuality, setSeServiceQuality] = useState<'acceptable' | 'good' | 'excellent'>('acceptable');

  // State for viewing receipts/entries
  const [goodsReceipts, setGoodsReceipts] = useState<GoodsReceipt[]>([]);
  const [serviceEntries, setServiceEntries] = useState<ServiceEntry[]>([]);

  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'gr' | 'se' | 'view'>('gr');

  // Load purchase orders for selected order
  const handleLoadPurchaseOrders = async () => {
    if (!orderNumber) {
      showError('Please enter an order number');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/pm-workflow/orders/${orderNumber}/purchase-orders`);
      
      if (!response.ok) {
        throw new Error('Failed to load purchase orders');
      }

      const data = await response.json();
      setPurchaseOrders(data);
      
      if (data.length === 0) {
        showError('No purchase orders found for this order');
      } else {
        showSuccess(`Loaded ${data.length} purchase order(s)`);
      }
    } catch (error: any) {
      showError(error.message || 'Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  };

  // Create goods receipt
  const handleCreateGoodsReceipt = async () => {
    if (!selectedPO) {
      showError('Please select a purchase order');
      return;
    }
    if (!grMaterialNumber || grQuantity <= 0 || !grStorageLocation) {
      showError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/pm-workflow/goods-receipts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          po_number: selectedPO,
          material_number: grMaterialNumber,
          quantity_received: grQuantity,
          storage_location: grStorageLocation,
          received_by: user?.username || 'system',
          quality_passed: grQualityPassed,
          quality_notes: grQualityNotes || null
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create goods receipt');
      }

      const data = await response.json();
      showSuccess(`Goods receipt created: ${data.gr_document}`);
      
      // Reset form
      resetGRForm();
      
      // Reload purchase orders to update status
      await handleLoadPurchaseOrders();
    } catch (error: any) {
      showError(error.message || 'Failed to create goods receipt');
    } finally {
      setLoading(false);
    }
  };

  // Create service entry
  const handleCreateServiceEntry = async () => {
    if (!selectedPO) {
      showError('Please select a purchase order');
      return;
    }
    if (!seServiceDescription || seHoursOrUnits <= 0 || !seAcceptanceDate) {
      showError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/pm-workflow/service-entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          po_number: selectedPO,
          service_description: seServiceDescription,
          hours_or_units: seHoursOrUnits,
          acceptance_date: seAcceptanceDate,
          acceptor: user?.username || 'system',
          service_quality: seServiceQuality
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create service entry');
      }

      const data = await response.json();
      showSuccess(`Service entry created: ${data.service_entry_document}`);
      
      // Reset form
      resetSEForm();
      
      // Reload purchase orders to update status
      await handleLoadPurchaseOrders();
    } catch (error: any) {
      showError(error.message || 'Failed to create service entry');
    } finally {
      setLoading(false);
    }
  };

  // Load goods receipts and service entries for viewing
  const handleLoadReceiptsAndEntries = async () => {
    if (!orderNumber) {
      showError('Please enter an order number');
      return;
    }

    setLoading(true);
    try {
      // Load goods receipts
      const grResponse = await fetch(`/api/v1/pm-workflow/orders/${orderNumber}/goods-receipts`);
      if (grResponse.ok) {
        const grData = await grResponse.json();
        setGoodsReceipts(grData);
      }

      // Load service entries
      const seResponse = await fetch(`/api/v1/pm-workflow/orders/${orderNumber}/service-entries`);
      if (seResponse.ok) {
        const seData = await seResponse.json();
        setServiceEntries(seData);
      }

      showSuccess('Loaded receipts and entries');
    } catch (error: any) {
      showError(error.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const resetGRForm = () => {
    setGrMaterialNumber('');
    setGrQuantity(0);
    setGrStorageLocation('');
    setGrQualityPassed(true);
    setGrQualityNotes('');
  };

  const resetSEForm = () => {
    setSeServiceDescription('');
    setSeHoursOrUnits(0);
    setSeAcceptanceDate('');
    setSeServiceQuality('acceptable');
  };

  // Auto-load receipts/entries when switching to view tab
  useEffect(() => {
    if (activeTab === 'view' && orderNumber) {
      handleLoadReceiptsAndEntries();
    }
  }, [activeTab]);

  return (
    <div className="sap-container">
      <div className="sap-header">
        <h1 className="sap-title">Screen 4: Material Receipt & Service Entry</h1>
        <div className="sap-subtitle">Record goods receipts and service sheet entries</div>
      </div>

      <div className="sap-content">
        {/* Order Selection Section */}
        <div className="sap-section">
          <div className="sap-section-header">
            <h2 className="sap-section-title">Order Selection</h2>
          </div>
          <div className="sap-section-content">
            <div className="sap-form-grid">
              <div className="sap-form-group">
                <label className="sap-label">Maintenance Order Number *</label>
                <input
                  type="text"
                  className="sap-input"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  placeholder="e.g., PM-20250127..."
                />
              </div>
              <div className="sap-form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button
                  className="sap-button sap-button-primary"
                  onClick={handleLoadPurchaseOrders}
                  disabled={loading}
                >
                  Load Purchase Orders
                </button>
              </div>
            </div>

            {/* Purchase Orders List */}
            {purchaseOrders.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <label className="sap-label">Select Purchase Order *</label>
                <select
                  className="sap-input"
                  value={selectedPO}
                  onChange={(e) => setSelectedPO(e.target.value)}
                >
                  <option value="">-- Select PO --</option>
                  {purchaseOrders.map((po) => (
                    <option key={po.po_number} value={po.po_number}>
                      {po.po_number} - {po.po_type} - {po.vendor_id} - ${po.total_value.toFixed(2)} - {po.status}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="sap-tabs">
          <button
            className={`sap-tab ${activeTab === 'gr' ? 'sap-tab-active' : ''}`}
            onClick={() => setActiveTab('gr')}
          >
            Goods Receipt
          </button>
          <button
            className={`sap-tab ${activeTab === 'se' ? 'sap-tab-active' : ''}`}
            onClick={() => setActiveTab('se')}
          >
            Service Entry
          </button>
          <button
            className={`sap-tab ${activeTab === 'view' ? 'sap-tab-active' : ''}`}
            onClick={() => setActiveTab('view')}
          >
            View Receipts/Entries
          </button>
        </div>

        {/* Goods Receipt Tab */}
        {activeTab === 'gr' && (
          <div className="sap-section">
            <div className="sap-section-header">
              <h2 className="sap-section-title">Create Goods Receipt</h2>
            </div>
            <div className="sap-section-content">
              <div className="sap-form-grid">
                <div className="sap-form-group">
                  <label className="sap-label">Material Number *</label>
                  <input
                    type="text"
                    className="sap-input"
                    value={grMaterialNumber}
                    onChange={(e) => setGrMaterialNumber(e.target.value)}
                    placeholder="e.g., MAT-12345"
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Quantity Received *</label>
                  <input
                    type="number"
                    className="sap-input"
                    value={grQuantity}
                    onChange={(e) => setGrQuantity(parseFloat(e.target.value))}
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Storage Location *</label>
                  <input
                    type="text"
                    className="sap-input"
                    value={grStorageLocation}
                    onChange={(e) => setGrStorageLocation(e.target.value)}
                    placeholder="e.g., WH-01"
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Quality Inspection</label>
                  <select
                    className="sap-input"
                    value={grQualityPassed ? 'passed' : 'failed'}
                    onChange={(e) => setGrQualityPassed(e.target.value === 'passed')}
                  >
                    <option value="passed">Passed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>

                <div className="sap-form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="sap-label">Quality Notes</label>
                  <textarea
                    className="sap-input"
                    value={grQualityNotes}
                    onChange={(e) => setGrQualityNotes(e.target.value)}
                    placeholder="Optional quality inspection notes"
                    rows={3}
                  />
                </div>
              </div>

              <div className="sap-button-bar">
                <button
                  className="sap-button sap-button-primary"
                  onClick={handleCreateGoodsReceipt}
                  disabled={loading || !selectedPO}
                >
                  {loading ? 'Posting...' : 'Post Goods Receipt'}
                </button>
                <button
                  className="sap-button sap-button-secondary"
                  onClick={resetGRForm}
                  disabled={loading}
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Service Entry Tab */}
        {activeTab === 'se' && (
          <div className="sap-section">
            <div className="sap-section-header">
              <h2 className="sap-section-title">Create Service Entry</h2>
            </div>
            <div className="sap-section-content">
              <div className="sap-form-grid">
                <div className="sap-form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="sap-label">Service Description *</label>
                  <textarea
                    className="sap-input"
                    value={seServiceDescription}
                    onChange={(e) => setSeServiceDescription(e.target.value)}
                    placeholder="Describe the service performed"
                    rows={3}
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Hours/Units *</label>
                  <input
                    type="number"
                    className="sap-input"
                    value={seHoursOrUnits}
                    onChange={(e) => setSeHoursOrUnits(parseFloat(e.target.value))}
                    min="0"
                    step="0.5"
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Acceptance Date *</label>
                  <input
                    type="datetime-local"
                    className="sap-input"
                    value={seAcceptanceDate}
                    onChange={(e) => setSeAcceptanceDate(e.target.value)}
                  />
                </div>

                <div className="sap-form-group">
                  <label className="sap-label">Service Quality</label>
                  <select
                    className="sap-input"
                    value={seServiceQuality}
                    onChange={(e) => setSeServiceQuality(e.target.value as any)}
                  >
                    <option value="acceptable">Acceptable</option>
                    <option value="good">Good</option>
                    <option value="excellent">Excellent</option>
                  </select>
                </div>
              </div>

              <div className="sap-button-bar">
                <button
                  className="sap-button sap-button-primary"
                  onClick={handleCreateServiceEntry}
                  disabled={loading || !selectedPO}
                >
                  {loading ? 'Posting...' : 'Post Service Entry'}
                </button>
                <button
                  className="sap-button sap-button-secondary"
                  onClick={resetSEForm}
                  disabled={loading}
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}

        {/* View Receipts/Entries Tab */}
        {activeTab === 'view' && (
          <>
            {/* Goods Receipts */}
            <div className="sap-section">
              <div className="sap-section-header">
                <h2 className="sap-section-title">Goods Receipts</h2>
              </div>
              <div className="sap-section-content">
                {goodsReceipts.length === 0 ? (
                  <div className="sap-info-box">No goods receipts found for this order</div>
                ) : (
                  <div className="sap-table-container">
                    <table className="sap-table">
                      <thead>
                        <tr>
                          <th>GR Document</th>
                          <th>PO Number</th>
                          <th>Material</th>
                          <th>Quantity</th>
                          <th>Storage Location</th>
                          <th>Receipt Date</th>
                          <th>Received By</th>
                        </tr>
                      </thead>
                      <tbody>
                        {goodsReceipts.map((gr) => (
                          <tr key={gr.gr_document}>
                            <td>{gr.gr_document}</td>
                            <td>{gr.po_number}</td>
                            <td>{gr.material_number}</td>
                            <td>{gr.quantity_received}</td>
                            <td>{gr.storage_location}</td>
                            <td>{new Date(gr.receipt_date).toLocaleString()}</td>
                            <td>{gr.received_by}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Service Entries */}
            <div className="sap-section">
              <div className="sap-section-header">
                <h2 className="sap-section-title">Service Entries</h2>
              </div>
              <div className="sap-section-content">
                {serviceEntries.length === 0 ? (
                  <div className="sap-info-box">No service entries found for this order</div>
                ) : (
                  <div className="sap-table-container">
                    <table className="sap-table">
                      <thead>
                        <tr>
                          <th>Document Number</th>
                          <th>Related PO</th>
                          <th>Status</th>
                          <th>Transaction Date</th>
                          <th>User</th>
                        </tr>
                      </thead>
                      <tbody>
                        {serviceEntries.map((se) => (
                          <tr key={se.flow_id}>
                            <td>{se.document_number}</td>
                            <td>{se.related_document || '-'}</td>
                            <td>{se.status}</td>
                            <td>{new Date(se.transaction_date).toLocaleString()}</td>
                            <td>{se.user_id}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      <SAPToast {...toastState} onClose={closeToast} />
    </div>
  );
};

export default PMWorkflowScreen4;
