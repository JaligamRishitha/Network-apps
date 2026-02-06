/**
 * Plant Maintenance (PM) Page - SAP GUI Style (MM Layout)
 * Requirement 8.2 - Equipment list, work orders, maintenance schedules
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { pmApi, ticketsApi, workOrderFlowApi } from '../services/api';
import { useSAPDialog } from '../hooks/useSAPDialog';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPDialog from '../components/SAPDialog';
import SAPToast from '../components/SAPToast';
import SAPFormDialog from '../components/SAPFormDialog';
import SAPWorkOrderCreate from '../components/SAPWorkOrderCreate';
import '../styles/sap-theme.css';

const PM: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('equipment');
  const [equipment, setEquipment] = useState<any[]>([]);
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [crmWorkOrders, setCrmWorkOrders] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [descriptionSearch, setDescriptionSearch] = useState('');
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [showCreateEquipmentModal, setShowCreateEquipmentModal] = useState(false);
  const [showCreateWorkOrderModal, setShowCreateWorkOrderModal] = useState(false);
  const { dialogState, showAlert, showPrompt, handleClose: closeDialog } = useSAPDialog();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const results = await Promise.allSettled([
        pmApi.listAssets(),
        pmApi.listMaintenanceOrders(),
        ticketsApi.list({ module: 'PM', limit: 100 }),
        workOrderFlowApi.list()
      ]);

      // Handle assets (index 0)
      if (results[0].status === 'fulfilled') {
        setEquipment(results[0].value.data.assets || []);
      } else {
        console.error('Failed to load assets:', results[0].reason);
        setEquipment([]);
      }

      // Handle maintenance orders (index 1)
      if (results[1].status === 'fulfilled') {
        setWorkOrders(results[1].value.data.orders || []);
      } else {
        console.error('Failed to load maintenance orders:', results[1].reason);
        setWorkOrders([]);
      }

      // Handle tickets (index 2)
      if (results[2].status === 'fulfilled') {
        setTickets(results[2].value.data.tickets || []);
      } else {
        console.error('Failed to load tickets:', results[2].reason);
        setTickets([]);
      }

      // Handle CRM work orders (index 3)
      if (results[3].status === 'fulfilled') {
        setCrmWorkOrders(results[3].value.data.work_orders || []);
      } else {
        console.error('Failed to load work orders:', results[3].reason);
        setCrmWorkOrders([]);
      }
    } catch (error) {
      console.error('Failed to load PM data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkOrder = async (data: any) => {
    try {
      await workOrderFlowApi.create({
        title: data.description || 'Work Order',
        description: data.description || '',
        customer_name: data.customer || 'Internal',
        site_location: data.location || 'Main Site',
        requested_date: new Date().toISOString(),
        cost_center_id: 'CC-MAINT-001',
        created_by: user?.username || 'system',
        materials: data.materials || [],
        priority: data.priority || 'medium',
        assigned_to: data.assigned_to || user?.username
      });
      await loadData();
      setShowCreateWorkOrderModal(false);
      showSuccess('Work order created successfully!');
    } catch (error) {
      showError('Failed to create work order');
    }
  };

  const handleCheckMaterials = async (workOrderId: string) => {
    try {
      await workOrderFlowApi.checkMaterials(workOrderId, user?.username || 'system');
      await loadData();
      showSuccess('Materials check completed!');
    } catch (error) {
      showError('Failed to check materials');
    }
  };

  const handleCreateEquipment = async (data: any) => {
    try {
      await pmApi.createAsset({
        name: data.name,
        asset_type: data.type,
        location: data.location,
        status: data.status || 'operational'
      });
      await loadData();
      setShowCreateEquipmentModal(false);
      showSuccess('Equipment created successfully!');
    } catch (error) {
      showError('Failed to create equipment');
    }
  };

  const handleSearch = () => {
    if (!searchTerm && !descriptionSearch) {
      loadData();
      return;
    }
    const filtered = equipment.filter(eq => 
      (searchTerm ? eq.asset_id?.toLowerCase().includes(searchTerm.toLowerCase()) : true) &&
      (descriptionSearch ? eq.name?.toLowerCase().includes(descriptionSearch.toLowerCase()) : true)
    );
    setEquipment(filtered);
  };

  const handleDisplayEquipment = () => {
    if (!selectedEquipment) {
      showAlert('Warning', 'Please select an equipment first');
      return;
    }
    const eq = equipment.find(e => e.asset_id === selectedEquipment);
    if (eq) {
      showAlert('Equipment Details', `ID: ${eq.asset_id}\nName: ${eq.name}\nType: ${eq.asset_type}\nLocation: ${eq.location}\nStatus: ${eq.status}`);
    }
  };

  const handleViewTicketDetails = (ticket: any) => {
    showAlert(
      'Ticket Details',
      `Ticket ID: ${ticket.ticket_id}\nType: ${ticket.ticket_type}\nTitle: ${ticket.title}\nDescription: ${ticket.description || 'N/A'}\nPriority: ${ticket.priority}\nStatus: ${ticket.status}\nCreated: ${new Date(ticket.created_at).toLocaleString()}\nSLA Deadline: ${new Date(ticket.sla_deadline).toLocaleString()}`
    );
  };

  const handleUpdateTicketStatus = async (ticketId: string, currentStatus: string) => {
    const statusOptions = ['Open', 'Assigned', 'In_Progress', 'Closed'];
    const newStatus = await showPrompt(
      'Update Ticket Status',
      `Current Status: ${currentStatus}\n\nEnter new status (Open, Assigned, In_Progress, Closed):`,
      '',
      'New Status'
    );
    
    if (!newStatus || !statusOptions.includes(newStatus)) {
      if (newStatus) showError('Invalid status. Must be one of: Open, Assigned, In_Progress, Closed');
      return;
    }

    try {
      await ticketsApi.updateStatus(ticketId, newStatus, user?.username || 'system', 'Status updated from PM module');
      await loadData();
      showSuccess(`Ticket ${ticketId} status updated to ${newStatus}`);
    } catch (error) {
      showError('Failed to update ticket status');
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f7f7f7', minHeight: 'calc(100vh - 88px)' }}>
      {/* Page Header */}
      <div style={{
        backgroundColor: '#d9edf7',
        padding: '12px 16px',
        marginBottom: '16px',
        borderRadius: '4px',
        fontSize: '14px',
        fontWeight: 600,
        color: '#31708f'
      }}>
        Plant Maintenance - Equipment & Work Orders
      </div>

      {/* SAP GUI Container */}
      <div className="sap-gui-container">
        {/* Tabs */}
        <div className="sap-gui-tabs">
          <div 
            className={`sap-gui-tab ${activeTab === 'equipment' ? 'active' : ''}`}
            onClick={() => setActiveTab('equipment')}
          >
            Equipment Master
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'workorders' ? 'active' : ''}`}
            onClick={() => setActiveTab('workorders')}
          >
            Work Orders
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            Maintenance Schedule
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'equipment' && (
          <div className="sap-gui-panel">
            <div style={{ marginBottom: '16px' }}>
              <div className="sap-flex" style={{ gap: '12px', marginBottom: '16px' }}>
                <div className="sap-form-group" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="sap-form-label">Equipment ID</label>
                  <input 
                    type="text" 
                    className="sap-form-input" 
                    placeholder="Enter equipment ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </div>
                <div className="sap-form-group" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="sap-form-label">Equipment Name</label>
                  <input 
                    type="text" 
                    className="sap-form-input" 
                    placeholder="Search name..."
                    value={descriptionSearch}
                    onChange={(e) => setDescriptionSearch(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
                  <button className="sap-toolbar-button" style={{ padding: '8px 20px' }} onClick={handleSearch}>
                    Search
                  </button>
                  <button className="sap-toolbar-button primary" style={{ padding: '8px 20px' }} onClick={() => setShowCreateEquipmentModal(true)}>
                    Create
                  </button>
                  <button className="sap-toolbar-button" style={{ padding: '8px 20px' }} onClick={handleDisplayEquipment}>
                    Display
                  </button>
                </div>
              </div>
            </div>

            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                Loading equipment...
              </div>
            ) : equipment.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                No equipment found. Click "Create" to add new equipment.
              </div>
            ) : (
              <>
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th style={{ width: '40px' }}>
                        <input type="checkbox" />
                      </th>
                      <th>Equipment ID</th>
                      <th>Equipment Name</th>
                      <th>Type</th>
                      <th>Location</th>
                      <th>Installation Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {equipment.map((eq) => (
                      <tr 
                        key={eq.asset_id}
                        className={selectedEquipment === eq.asset_id ? 'selected' : ''}
                        onClick={() => setSelectedEquipment(eq.asset_id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>
                          <input type="checkbox" />
                        </td>
                        <td style={{ fontWeight: 600, color: '#0a6ed1' }}>{eq.asset_id}</td>
                        <td>{eq.name}</td>
                        <td>{eq.asset_type}</td>
                        <td>{eq.location}</td>
                        <td>{eq.installation_date ? new Date(eq.installation_date).toLocaleDateString() : '-'}</td>
                        <td>
                          <span className={`sap-status ${
                            eq.status === 'operational' ? 'success' :
                            eq.status === 'under_maintenance' ? 'warning' : 'error'
                          }`}>
                            {eq.status === 'operational' ? 'Available' : eq.status === 'under_maintenance' ? 'Maintenance' : 'Offline'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div style={{ marginTop: '12px', fontSize: '12px', color: '#6a6d70' }}>
                  {equipment.length} entries found
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'workorders' && (
          <div style={{ padding: 0 }}>
            {/* Embedded SAP Work Order Create Component */}
            <SAPWorkOrderCreate
              onClose={() => setActiveTab('equipment')}
              onSubmit={handleCreateWorkOrder}
              equipmentList={equipment}
              embedded={true}
            />
            
            {/* CRM Work Orders Section */}
            <div className="sap-gui-panel" style={{ marginTop: '16px' }}>
              <div style={{
                backgroundColor: '#d9edf7',
                padding: '8px 12px',
                marginBottom: '16px',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: 600,
                color: '#31708f'
              }}>
                CRM Work Orders
              </div>
              
              {loading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                  Loading CRM work orders...
                </div>
              ) : crmWorkOrders.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                  No CRM work orders found.
                </div>
              ) : (
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>Work Order ID</th>
                      <th>Title</th>
                      <th>Customer</th>
                      <th>Status</th>
                      <th>Materials Check</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {crmWorkOrders.map((wo) => (
                      <tr key={wo.work_order_id}>
                        <td style={{ fontWeight: 600, color: '#0a6ed1' }}>{wo.work_order_id}</td>
                        <td>{wo.title}</td>
                        <td>{wo.customer_name}</td>
                        <td>
                          <span className={`sap-status ${
                            wo.flow_status === 'completed' ? 'success' :
                            wo.flow_status === 'in_progress' ? 'warning' :
                            wo.flow_status === 'materials_shortage' ? 'error' : 'info'
                          }`}>
                            {wo.flow_status?.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          {wo.materials_check_summary ? (
                            <span className={`sap-status ${
                              wo.materials_check_summary.all_available ? 'success' : 'error'
                            }`}>
                              {wo.materials_check_summary.all_available ? 'Available' : `${wo.materials_check_summary.shortage_count} Missing`}
                            </span>
                          ) : (
                            <span className="sap-status info">Not Checked</span>
                          )}
                        </td>
                        <td>
                          <button
                            className="sap-toolbar-button"
                            style={{ padding: '4px 12px', fontSize: '12px' }}
                            onClick={() => handleCheckMaterials(wo.work_order_id)}
                            disabled={wo.flow_status !== 'received'}
                          >
                            Check Materials
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'schedule' && (
          <div className="sap-gui-panel">
            <div style={{ padding: '60px 20px', textAlign: 'center', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📅</div>
              <div style={{ fontSize: '16px', fontWeight: 500, color: '#6a6d70' }}>
                Preventive Maintenance Calendar
              </div>
              <div style={{ fontSize: '14px', marginTop: '8px', color: '#6a6d70' }}>
                Schedule and track preventive maintenance activities
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="sap-gui-panel">
            <div style={{ padding: '60px 20px', textAlign: 'center', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📜</div>
              <div style={{ fontSize: '16px', fontWeight: 500, color: '#6a6d70' }}>
                Historical Maintenance Records
              </div>
              <div style={{ fontSize: '14px', marginTop: '8px', color: '#6a6d70' }}>
                View completed work orders and maintenance activities
              </div>
            </div>
          </div>
        )}
      </div>

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

      {/* Create Equipment Modal */}
      <SAPFormDialog
        isOpen={showCreateEquipmentModal}
        title="Create Equipment"
        fields={[
          { name: 'name', label: 'Equipment Name', type: 'text', required: true },
          { 
            name: 'type', 
            label: 'Equipment Type', 
            type: 'select', 
            required: true,
            options: [
              { value: 'substation', label: 'Substation' },
              { value: 'transformer', label: 'Transformer' },
              { value: 'feeder', label: 'Feeder' },
              { value: 'generator', label: 'Generator' },
              { value: 'switchgear', label: 'Switchgear' }
            ]
          },
          { name: 'location', label: 'Location', type: 'text', required: true },
          { 
            name: 'status', 
            label: 'Status', 
            type: 'select', 
            required: true,
            options: [
              { value: 'operational', label: 'Operational' },
              { value: 'under_maintenance', label: 'Under Maintenance' },
              { value: 'offline', label: 'Offline' }
            ]
          }
        ]}
        onSubmit={handleCreateEquipment}
        onCancel={() => setShowCreateEquipmentModal(false)}
        submitLabel="Create"
      />
    </div>
  );
};

export default PM;
