/**
 * Sales Quotation Detail Page
 * SAP S/4HANA Object Page Pattern
 */
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSAPDialog } from '../hooks/useSAPDialog';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPDialog from '../components/SAPDialog';
import SAPToast from '../components/SAPToast';
import '../styles/sap-theme.css';

interface QuotationItem {
  id: string;
  material: string;
  description: string;
  quantity: number;
  unit: string;
  price: number;
  total: number;
}

const SalesQuotation: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('general');
  const [isEditing, setIsEditing] = useState(false);
  const { dialogState, showAlert, showConfirm, handleClose: closeDialog } = useSAPDialog();
  const { toastState, showSuccess, handleClose: closeToast } = useSAPToast();

  const [quotation, setQuotation] = useState({
    id: id || '20000018',
    soldToParty: 'Magic Company (20000064)',
    shipToParty: 'Magic Company (20000064)',
    overallStatus: 'Open',
    approvalStatus: 'Not Relevant',
    netSalesVolume: '0.00 USD',
    netValue: '6,394,096.45 USD',
    validFrom: '03/07/2025',
    validTo: '05/30/2025',
    documentDate: '02/03/2025',
    requestedDeliveryDate: '06/02/2025',
    orderReason: 'Standard (01)',
    shippingConditions: 'Standard (01)',
    incoterms: 'Ex Works (EXW)',
    paymentTerms: 'Pay Immediately Wo Deduction (0001)',
    documentCurrency: 'US Dollar (USD)',
    salesOffice: '',
    salesGroup: '',
    salesDistrict: '',
    productDivision: '00 (00)',
    directSales: '10',
    distributionChannel: '',
    shipToAddress: 'Lindenstraße 10, 74934 Schöntal, Germany',
    createdOn: '01/01/2025, 16:32:40',
    changedOn: '06/02/2025, 09:52:19',
    lastChangedBy: 'Example InternalSalesRep (CUR9000001022)',
    createdBy: 'Example InternalSalesRep (CUR9000001022)'
  });

  const [items, setItems] = useState<QuotationItem[]>([
    {
      id: '1',
      material: 'MAT-001',
      description: 'Steel Plate 10mm',
      quantity: 1000,
      unit: 'KG',
      price: 125.50,
      total: 125500
    }
  ]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = () => {
    setIsEditing(false);
    showSuccess('Quotation saved successfully!');
  };

  const handleCreateSubsequentOrder = () => {
    showAlert('Create Subsequent Order', 'Creating subsequent order...');
  };

  const handleUpdatePrices = () => {
    showAlert('Update Prices', 'Updating prices...');
  };

  const handleRejectAllItems = async () => {
    const confirmed = await showConfirm('Reject All Items', 'Are you sure you want to reject all items?');
    if (confirmed) {
      showSuccess('All items rejected');
    }
  };

  const handleDisplayChangeLog = () => {
    showAlert('Change Log', 'Displaying change log...');
  };

  const tabs = [
    { id: 'general', label: 'General Information' },
    { id: 'items', label: 'Items' },
    { id: 'partners', label: 'Partners' },
    { id: 'prices', label: 'Prices' },
    { id: 'texts', label: 'Texts' },
    { id: 'status', label: 'Status and Blocks' },
    { id: 'output', label: 'Output Items' }
  ];

  return (
    <div style={{ backgroundColor: '#f7f7f7', minHeight: '100vh' }}>
      {/* Header Bar */}
      <div style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #d9d9d9',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px'
      }}>
        <button 
          className="sap-toolbar-button"
          onClick={() => navigate(-1)}
          style={{ padding: '6px 12px' }}
        >
          ← Back
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '12px', color: '#6a6d70' }}>Quotation (V01)</div>
          <div style={{ fontSize: '20px', fontWeight: 400 }}>{quotation.id}</div>
        </div>
        <button className="sap-toolbar-button" onClick={handleEdit}>
          {isEditing ? '📝 Editing' : 'Edit'}
        </button>
        <button className="sap-toolbar-button" onClick={handleCreateSubsequentOrder}>
          Create Subsequent Order
        </button>
        <button className="sap-toolbar-button" onClick={handleUpdatePrices}>
          Update Prices
        </button>
        <button className="sap-toolbar-button" onClick={handleRejectAllItems}>
          Reject All Items
        </button>
        <button className="sap-toolbar-button" onClick={handleDisplayChangeLog}>
          Display Change Log
        </button>
        <button className="sap-toolbar-button">
          Attachments (0)
        </button>
        <button className="sap-toolbar-button primary">
          ⭐ Summarize
        </button>
        <button className="sap-toolbar-button">
          Related Apps ▼
        </button>
        <button className="sap-toolbar-button">
          ⋮
        </button>
      </div>

      {/* Object Header */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderBottom: '1px solid #d9d9d9'
      }}>
        <div style={{ display: 'flex', gap: '24px', marginBottom: '20px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            backgroundColor: '#0070f2',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '24px',
            fontWeight: 600
          }}>
            📄
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', gap: '16px', marginBottom: '8px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#6a6d70' }}>Partners</div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>
                  Sold-to Party: {quotation.soldToParty}
                </div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>
                  Ship-to Party: {quotation.shipToParty}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#6a6d70' }}>Status</div>
                <div style={{ fontSize: '14px' }}>
                  Overall Status: <span className="sap-status info">{quotation.overallStatus}</span>
                </div>
                <div style={{ fontSize: '14px' }}>
                  Approval Status: <span className="sap-status success">{quotation.approvalStatus}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Figures */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#6a6d70', marginBottom: '4px' }}>Net Sales Volume (YTD)</div>
            <div style={{ fontSize: '20px', fontWeight: 600 }}>{quotation.netSalesVolume}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6a6d70', marginBottom: '4px' }}>Net Value</div>
            <div style={{ fontSize: '20px', fontWeight: 600 }}>{quotation.netValue}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6a6d70', marginBottom: '4px' }}>Valid From</div>
            <div style={{ fontSize: '20px', fontWeight: 600 }}>{quotation.validFrom}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6a6d70', marginBottom: '4px' }}>Valid To</div>
            <div style={{ fontSize: '20px', fontWeight: 600 }}>{quotation.validTo}</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        backgroundColor: 'white',
        borderBottom: '2px solid #e5e5e5',
        padding: '0 24px',
        display: 'flex',
        gap: '24px'
      }}>
        {tabs.map((tab) => (
          <div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '16px 0',
              borderBottom: activeTab === tab.id ? '3px solid #0070f2' : '3px solid transparent',
              color: activeTab === tab.id ? '#0070f2' : '#32363a',
              fontWeight: activeTab === tab.id ? 600 : 400,
              cursor: 'pointer',
              marginBottom: '-2px',
              fontSize: '14px'
            }}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ padding: '24px' }}>
        {activeTab === 'general' && (
          <div>
            <div className="sap-fiori-card" style={{ marginBottom: '16px' }}>
              <div className="sap-fiori-card-header">
                <h3 className="sap-fiori-card-title">Basic Data</h3>
              </div>
              <div className="sap-fiori-card-content">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Quotation Data</h4>
                    <div className="sap-object-attributes">
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Ship-to Party</div>
                        <div className="sap-object-attribute-value">{quotation.shipToParty}</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Customer Reference</div>
                        <div className="sap-object-attribute-value">-</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Requested Delivery Date</div>
                        <div className="sap-object-attribute-value">{quotation.requestedDeliveryDate}</div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Ship-to Party Data</h4>
                    <div className="sap-object-attributes">
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Ship-to Party</div>
                        <div className="sap-object-attribute-value">{quotation.shipToParty}</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Address</div>
                        <div className="sap-object-attribute-value">{quotation.shipToAddress}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="sap-fiori-card">
              <div className="sap-fiori-card-header">
                <h3 className="sap-fiori-card-title">Advanced Data</h3>
              </div>
              <div className="sap-fiori-card-content">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Terms and Conditions</h4>
                    <div className="sap-object-attributes">
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Incoterms</div>
                        <div className="sap-object-attribute-value">{quotation.incoterms}</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Payment Method</div>
                        <div className="sap-object-attribute-value">{quotation.paymentTerms}</div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Organizational Data</h4>
                    <div className="sap-object-attributes">
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Sales Office</div>
                        <div className="sap-object-attribute-value">{quotation.salesOffice || '-'}</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Sales Group</div>
                        <div className="sap-object-attribute-value">{quotation.salesGroup || '-'}</div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Administrative Data</h4>
                    <div className="sap-object-attributes">
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Created On</div>
                        <div className="sap-object-attribute-value">{quotation.createdOn}</div>
                      </div>
                      <div className="sap-object-attribute">
                        <div className="sap-object-attribute-label">Changed On</div>
                        <div className="sap-object-attribute-value">{quotation.changedOn}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'items' && (
          <div className="sap-fiori-card">
            <div className="sap-fiori-card-header">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className="sap-fiori-card-title">Items ({items.length})</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input 
                    type="text" 
                    className="sap-form-input" 
                    placeholder="Search..."
                    style={{ width: '200px' }}
                  />
                  <button className="sap-toolbar-button primary">Create</button>
                  <button className="sap-toolbar-button">Delete</button>
                  <button className="sap-toolbar-button">📋</button>
                  <button className="sap-toolbar-button">⚙️</button>
                  <button className="sap-toolbar-button">📊</button>
                  <button className="sap-toolbar-button">⚡</button>
                  <button className="sap-toolbar-button">⤢</button>
                </div>
              </div>
            </div>
            <div className="sap-fiori-card-content" style={{ padding: 0 }}>
              <table className="sap-table">
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}><input type="checkbox" /></th>
                    <th>Item</th>
                    <th>Material</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Price</th>
                    <th>Total</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td><input type="checkbox" /></td>
                      <td style={{ fontWeight: 600, color: '#0070f2' }}>{item.id}</td>
                      <td>{item.material}</td>
                      <td>{item.description}</td>
                      <td style={{ textAlign: 'right' }}>{item.quantity.toLocaleString()}</td>
                      <td>{item.unit}</td>
                      <td style={{ textAlign: 'right' }}>${item.price.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>${item.total.toLocaleString()}</td>
                      <td>
                        <button className="sap-toolbar-button" style={{ padding: '4px 8px', fontSize: '12px' }}>
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      {isEditing && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: 'white',
          borderTop: '1px solid #d9d9d9',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px',
          boxShadow: '0 -2px 8px rgba(0,0,0,0.1)'
        }}>
          <button 
            className="sap-toolbar-button"
            onClick={() => setIsEditing(false)}
          >
            Cancel
          </button>
          <button 
            className="sap-toolbar-button primary"
            onClick={handleSave}
          >
            Save
          </button>
        </div>
      )}

      {/* SAP Dialogs */}
      <SAPDialog
        isOpen={dialogState.isOpen}
        title={dialogState.title}
        message={dialogState.message}
        type={dialogState.type}
        onClose={closeDialog}
        defaultValue={dialogState.defaultValue}
        inputLabel={dialogState.inputLabel}
      />

      <SAPToast
        isOpen={toastState.isOpen}
        message={toastState.message}
        type={toastState.type}
        onClose={closeToast}
      />
    </div>
  );
};

export default SalesQuotation;
