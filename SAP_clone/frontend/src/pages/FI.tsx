/**
 * Financial Accounting (FI) Page - SAP GUI Style
 * Requirements 8.1, 8.2, 8.3 - Cost centers, approvals inbox, GL accounts
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { fiApi, ticketsApi, workOrderFlowApi } from '../services/api';
import { useSAPDialog } from '../hooks/useSAPDialog';
import { useSAPToast } from '../hooks/useSAPToast';
import SAPDialog from '../components/SAPDialog';
import SAPToast from '../components/SAPToast';
import SAPFormDialog from '../components/SAPFormDialog';
import '../styles/sap-theme.css';

const FI: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('approvals');
  const [approvals, setApprovals] = useState<any[]>([]);
  const [workOrderApprovals, setWorkOrderApprovals] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [costCenters, setCostCenters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateCostCenterModal, setShowCreateCostCenterModal] = useState(false);
  const { dialogState, showAlert, showPrompt, showConfirm, handleClose: closeDialog } = useSAPDialog();
  const { toastState, showSuccess, showError, handleClose: closeToast } = useSAPToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const results = await Promise.allSettled([
        fiApi.listApprovals({ decision: 'pending' }),
        fiApi.listCostCenters(),
        ticketsApi.list({ module: 'FI', limit: 100 }),
        workOrderFlowApi.getPendingApproval()
      ]);

      // Handle approvals (index 0)
      if (results[0].status === 'fulfilled') {
        setApprovals(results[0].value.data || []);
      } else {
        console.error('Failed to load approvals:', results[0].reason);
        setApprovals([]);
      }

      // Handle cost centers (index 1)
      if (results[1].status === 'fulfilled') {
        setCostCenters(results[1].value.data.cost_centers || []);
      } else {
        console.error('Failed to load cost centers:', results[1].reason);
        setCostCenters([]);
      }

      // Handle tickets (index 2)
      if (results[2].status === 'fulfilled') {
        const allTickets = results[2].value.data.tickets || [];
        const uniqueTickets = allTickets.filter((ticket: any, index: number, self: any[]) =>
          index === self.findIndex((t: any) => t.ticket_id === ticket.ticket_id)
        );
        setTickets(uniqueTickets);
      } else {
        console.error('Failed to load tickets:', results[2].reason);
        setTickets([]);
      }

      // Handle work order approvals (index 3)
      if (results[3].status === 'fulfilled') {
        setWorkOrderApprovals(results[3].value.data.work_orders || []);
      } else {
        console.error('Failed to load work order approvals:', results[3].reason);
        setWorkOrderApprovals([]);
      }
    } catch (error) {
      console.error('Failed to load FI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveWorkOrder = async (workOrderId: string, title: string, customer: string, estimatedCost: number) => {
    const confirmed = await showConfirm(
      'Approve Work Order Purchase',
      `Work Order: ${workOrderId}\nTitle: ${title}\nCustomer: ${customer}\nEstimated Cost: $${estimatedCost.toLocaleString()}\n\nApprover: ${user?.username || 'system'}\n\nAre you sure you want to approve this work order purchase?`
    );
    if (!confirmed) return;

    try {
      await workOrderFlowApi.approvePurchase(workOrderId, true, user?.username || 'system');
      await loadData();
      showSuccess(`Work Order ${workOrderId} approved successfully by ${user?.username || 'system'}!`);
    } catch (error) {
      showError('Failed to approve work order');
    }
  };

  const handleRejectWorkOrder = async (workOrderId: string, title: string, customer: string, estimatedCost: number) => {
    const reason = await showPrompt(
      'Reject Work Order Purchase',
      `Work Order: ${workOrderId}\nTitle: ${title}\nCustomer: ${customer}\nEstimated Cost: $${estimatedCost.toLocaleString()}\n\nApprover: ${user?.username || 'system'}\n\nEnter rejection reason:`,
      '',
      'Reason'
    );
    if (!reason) return;

    try {
      await workOrderFlowApi.approvePurchase(workOrderId, false, user?.username || 'system', reason);
      await loadData();
      showSuccess(`Work Order ${workOrderId} rejected by ${user?.username || 'system'}`);
    } catch (error) {
      showError('Failed to reject work order');
    }
  };

  const handleApprove = async (approvalId: string, requestedBy: string, justification: string, amount: number) => {
    const confirmed = await showConfirm(
      'Approve Request', 
      `Requester: ${requestedBy}\nJustification: ${justification}\nAmount: $${amount.toLocaleString()}\n\nApprover: ${user?.username || 'system'}\n\nAre you sure you want to approve this request?`
    );
    if (!confirmed) return;

    try {
      await fiApi.approveRequest(approvalId, user?.username || 'system', `Approved by ${user?.username || 'system'} via UI`);
      await loadData();
      showSuccess(`Request ${approvalId} approved successfully by ${user?.username || 'system'}!`);
    } catch (error) {
      showError('Failed to approve request');
    }
  };

  const handleReject = async (approvalId: string, requestedBy: string, justification: string, amount: number) => {
    const reason = await showPrompt(
      'Reject Request', 
      `Requester: ${requestedBy}\nJustification: ${justification}\nAmount: $${amount.toLocaleString()}\n\nApprover: ${user?.username || 'system'}\n\nEnter rejection reason:`, 
      '', 
      'Reason'
    );
    if (!reason) return;
    
    try {
      await fiApi.rejectRequest(approvalId, user?.username || 'system', `Rejected by ${user?.username || 'system'}: ${reason}`);
      await loadData();
      showSuccess(`Request ${approvalId} rejected by ${user?.username || 'system'}`);
    } catch (error) {
      showError('Failed to reject request');
    }
  };

  const handlePostDocument = async () => {
    showAlert('Post Document', 'Feature coming soon');
  };

  const handleDisplay = () => {
    showAlert('Display', 'Feature coming soon');
  };

  const handleChange = () => {
    showAlert('Change', 'Feature coming soon');
  };

  const handleReports = () => {
    showAlert('Reports', 'Opening report generator...');
  };

  const handleAnalysis = () => {
    showAlert('Analysis', 'Opening analytics dashboard...');
  };

  const handlePrint = () => {
    showAlert('Print', 'Generating printable report...');
  };

  const handleCreateCostCenter = async (data: any) => {
    try {
      await fiApi.createCostCenter({
        name: data.name,
        budget_amount: parseFloat(data.budgetAmount),
        fiscal_year: parseInt(data.fiscalYear),
        responsible_manager: data.manager
      });
      await loadData();
      setShowCreateCostCenterModal(false);
      showSuccess('Cost center created successfully!');
    } catch (error) {
      showError('Failed to create cost center');
    }
  };

  const handleSearchAccount = () => {
    showAlert('Search Account', 'Feature coming soon');
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
      await ticketsApi.updateStatus(ticketId, newStatus, user?.username || 'system', 'Status updated from FI module');
      await loadData();
      showSuccess(`Ticket ${ticketId} status updated to ${newStatus}`);
    } catch (error) {
      showError('Failed to update ticket status');
    }
  };

  const handleApproveTicket = async (ticketId: string, title: string, createdBy: string) => {
    const confirmed = await showConfirm(
      'Approve Ticket',
      `Ticket: ${ticketId}\nTitle: ${title}\nRequester: ${createdBy}\n\nApprover: ${user?.username || 'system'}\n\nAre you sure you want to approve this ticket?`
    );
    if (!confirmed) return;

    try {
      // Follow the state machine: Open → Assigned → In_Progress → Closed
      const ticket = tickets.find(t => t.ticket_id === ticketId);
      if (!ticket) {
        showError('Ticket not found');
        return;
      }

      // Transition through states based on current status
      if (ticket.status === 'Open') {
        await ticketsApi.updateStatus(ticketId, 'Assigned', user?.username || 'system', `Assigned for approval by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'In_Progress', user?.username || 'system', `Processing approval by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Approved by ${user?.username || 'system'}`);
      } else if (ticket.status === 'Assigned') {
        await ticketsApi.updateStatus(ticketId, 'In_Progress', user?.username || 'system', `Processing approval by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Approved by ${user?.username || 'system'}`);
      } else if (ticket.status === 'In_Progress') {
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Approved by ${user?.username || 'system'}`);
      }

      await loadData();
      showSuccess(`Ticket ${ticketId} approved by ${user?.username || 'system'}!`);
    } catch (error) {
      showError('Failed to approve ticket');
    }
  };

  const handleRejectTicket = async (ticketId: string, title: string, createdBy: string) => {
    const reason = await showPrompt(
      'Reject Ticket',
      `Ticket: ${ticketId}\nTitle: ${title}\nRequester: ${createdBy}\n\nApprover: ${user?.username || 'system'}\n\nEnter rejection reason:`,
      '',
      'Reason'
    );
    if (!reason) return;

    try {
      // Follow the state machine: Open → Assigned → In_Progress → Closed
      const ticket = tickets.find(t => t.ticket_id === ticketId);
      if (!ticket) {
        showError('Ticket not found');
        return;
      }

      // Transition through states based on current status
      if (ticket.status === 'Open') {
        await ticketsApi.updateStatus(ticketId, 'Assigned', user?.username || 'system', `Assigned for review by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'In_Progress', user?.username || 'system', `Processing rejection by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Rejected by ${user?.username || 'system'}: ${reason}`);
      } else if (ticket.status === 'Assigned') {
        await ticketsApi.updateStatus(ticketId, 'In_Progress', user?.username || 'system', `Processing rejection by ${user?.username || 'system'}`);
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Rejected by ${user?.username || 'system'}: ${reason}`);
      } else if (ticket.status === 'In_Progress') {
        await ticketsApi.updateStatus(ticketId, 'Closed', user?.username || 'system', `Rejected by ${user?.username || 'system'}: ${reason}`);
      }

      await loadData();
      showSuccess(`Ticket ${ticketId} rejected by ${user?.username || 'system'}`);
    } catch (error) {
      showError('Failed to reject ticket');
    }
  };

  const [glAccounts, setGlAccounts] = useState<any[]>([]);

  return (
    <div>
      {/* SAP GUI Container */}
      <div className="sap-gui-container">
        <div className="sap-gui-section">
          Financial Accounting - FI Module
        </div>

        {/* Tabs */}
        <div className="sap-gui-tabs">
          <div 
            className={`sap-gui-tab ${activeTab === 'approvals' ? 'active' : ''}`}
            onClick={() => setActiveTab('approvals')}
          >
            Approvals Inbox
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'costcenters' ? 'active' : ''}`}
            onClick={() => setActiveTab('costcenters')}
          >
            Cost Centers
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'gl' ? 'active' : ''}`}
            onClick={() => setActiveTab('gl')}
          >
            General Ledger
          </div>
          <div 
            className={`sap-gui-tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            Financial Reports
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'approvals' && (
          <div className="sap-gui-panel">
            <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#fff9e6', border: '1px solid #ffd966', borderRadius: '4px' }}>
              <strong>⚠️ Pending Approvals & Tickets</strong>
              <div style={{ fontSize: '13px', marginTop: '4px' }}>
                You have {approvals.length} approval requests, {workOrderApprovals.length} work order approvals, and {tickets.length} FI tickets
              </div>
            </div>

            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                Loading data...
              </div>
            ) : approvals.length === 0 && workOrderApprovals.length === 0 && tickets.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                No pending approvals or tickets
              </div>
            ) : (
              <>
                {/* Work Order Purchase Approvals Section */}
                {workOrderApprovals.length > 0 && (
                  <div style={{ marginBottom: '24px' }}>
                    <h4 style={{ margin: '0 0 12px 0', color: '#0a6ed1' }}>Work Order Purchase Approvals</h4>
                    <table className="sap-table">
                      <thead>
                        <tr>
                          <th>Work Order ID</th>
                          <th>Title</th>
                          <th>Customer</th>
                          <th>Estimated Cost</th>
                          <th>Priority</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {workOrderApprovals.map((wo) => (
                          <tr key={`workorder-${wo.work_order_id}`} style={{ backgroundColor: '#f0f8ff' }}>
                            <td style={{ fontWeight: 600, color: '#0a6ed1', fontFamily: 'monospace' }}>{wo.work_order_id}</td>
                            <td>{wo.title}</td>
                            <td>{wo.customer_name}</td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>${wo.estimated_material_cost?.toLocaleString()}</td>
                            <td>
                              <span className={`sap-status ${
                                wo.priority === 'critical' ? 'error' :
                                wo.priority === 'high' ? 'warning' : 'info'
                              }`}>
                                {wo.priority}
                              </span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <button
                                  className="sap-toolbar-button"
                                  style={{ padding: '4px 12px', fontSize: '12px', backgroundColor: '#107e3e', color: 'white', border: 'none' }}
                                  onClick={() => handleApproveWorkOrder(wo.work_order_id, wo.title, wo.customer_name, wo.estimated_material_cost)}
                                >
                                  ✓ Approve
                                </button>
                                <button
                                  className="sap-toolbar-button"
                                  style={{ padding: '4px 12px', fontSize: '12px', backgroundColor: '#bb0000', color: 'white', border: 'none' }}
                                  onClick={() => handleRejectWorkOrder(wo.work_order_id, wo.title, wo.customer_name, wo.estimated_material_cost)}
                                >
                                  ✗ Reject
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Regular Approvals and Tickets */}
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title / Justification</th>
                      <th>Amount / Priority</th>
                      <th>Requester</th>
                      <th>Date</th>
                      <th>SLA Deadline</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                  {/* Approval Requests */}
                  {approvals.map((app) => (
                    <tr key={`approval-${app.approval_id}`} style={{ backgroundColor: '#fffef0' }}>
                      <td style={{ fontWeight: 600, color: '#0a6ed1' }}>{app.approval_id}</td>
                      <td>{app.justification}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>${app.amount?.toLocaleString()}</td>
                      <td>{app.requested_by}</td>
                      <td>{new Date(app.requested_at).toLocaleDateString()}</td>
                      <td>-</td>
                      <td>
                        <span className="sap-status warning">
                          {app.decision || 'Pending'}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button 
                            className="sap-toolbar-button" 
                            style={{ padding: '4px 12px', fontSize: '12px', backgroundColor: '#107e3e', color: 'white', border: 'none' }}
                            onClick={() => handleApprove(app.approval_id, app.requested_by, app.justification, app.amount)}
                          >
                            ✓ Approve
                          </button>
                          <button 
                            className="sap-toolbar-button" 
                            style={{ padding: '4px 12px', fontSize: '12px', backgroundColor: '#bb0000', color: 'white', border: 'none' }}
                            onClick={() => handleReject(app.approval_id, app.requested_by, app.justification, app.amount)}
                          >
                            ✗ Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  
                  {/* FI Tickets */}
                  {tickets.map((ticket) => {
                    // Extract customer ID and estimated cost from description
                    const customerMatch = ticket.description?.match(/Customer:\s*(CUST-[A-Z0-9-]+)/i);
                    const costMatch = ticket.description?.match(/Estimated Cost:\s*₹?([\d,]+(?:\.\d+)?)/i);
                    const customerName = customerMatch ? customerMatch[1] : ticket.created_by;
                    const estimatedCost = costMatch ? costMatch[1].replace(/,/g, '') : null;
                    
                    return (
                      <tr key={`ticket-${ticket.ticket_id}`}>
                        <td style={{ fontWeight: 600, color: '#0a6ed1', fontFamily: 'monospace' }}>
                          {ticket.ticket_id}
                        </td>
                        <td>{ticket.title}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>
                          {estimatedCost ? `₹${parseInt(estimatedCost).toLocaleString()}` : (
                            <span className={`sap-status ${
                              ticket.priority === 'P1' ? 'error' :
                              ticket.priority === 'P2' ? 'warning' : 'info'
                            }`}>
                              {ticket.priority}
                            </span>
                          )}
                        </td>
                        <td>{customerName}</td>
                        <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                        <td>{new Date(ticket.sla_deadline).toLocaleDateString()}</td>
                        <td>
                          <span className={`sap-status ${
                            ticket.status === 'Closed' ? 'success' :
                            ticket.status === 'In_Progress' ? 'warning' : 'info'
                          }`}>
                            {ticket.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button
                              className="sap-toolbar-button"
                              style={{ padding: '4px 8px', fontSize: '12px' }}
                              onClick={() => handleViewTicketDetails(ticket)}
                            >
                              View
                            </button>
                            <button
                              className="sap-toolbar-button"
                              style={{ padding: '4px 8px', fontSize: '12px', backgroundColor: '#107e3e', color: 'white', border: 'none' }}
                              onClick={() => handleApproveTicket(ticket.ticket_id, ticket.title, customerName)}
                            >
                              ✓ Approve
                            </button>
                            <button
                              className="sap-toolbar-button"
                              style={{ padding: '4px 8px', fontSize: '12px', backgroundColor: '#bb0000', color: 'white', border: 'none' }}
                              onClick={() => handleRejectTicket(ticket.ticket_id, ticket.title, customerName)}
                            >
                              ✗ Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              </>
            )}
          </div>
        )}

        {activeTab === 'costcenters' && (
          <div className="sap-gui-panel">
            <div className="sap-flex-between" style={{ marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>Cost Center Overview</h3>
              <button className="sap-toolbar-button primary" onClick={() => setShowCreateCostCenterModal(true)}>
                + Create Cost Center
              </button>
            </div>

            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                Loading cost centers...
              </div>
            ) : costCenters.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                No cost centers found. Click "Create Cost Center" to add one.
              </div>
            ) : (
              <>
                <table className="sap-table">
                  <thead>
                    <tr>
                      <th>Cost Center</th>
                      <th>Name</th>
                      <th>Budget (USD)</th>
                      <th>Fiscal Year</th>
                      <th>Manager</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costCenters.map((cc) => (
                      <tr key={cc.cost_center_id}>
                        <td style={{ fontWeight: 600, color: '#0a6ed1' }}>{cc.cost_center_id}</td>
                        <td>{cc.name}</td>
                        <td style={{ textAlign: 'right' }}>${cc.budget_amount?.toLocaleString()}</td>
                        <td>{cc.fiscal_year}</td>
                        <td>{cc.responsible_manager}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <h4 style={{ margin: '0 0 12px 0' }}>Budget Summary</h4>
                  <div className="sap-grid sap-grid-3">
                    <div>
                      <div style={{ fontSize: '12px', color: '#6a6d70' }}>Total Budget</div>
                      <div style={{ fontSize: '20px', fontWeight: 600, color: '#0a6ed1' }}>
                        ${costCenters.reduce((sum, cc) => sum + (cc.budget_amount || 0), 0).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#6a6d70' }}>Cost Centers</div>
                      <div style={{ fontSize: '20px', fontWeight: 600, color: '#0a6ed1' }}>
                        {costCenters.length}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#6a6d70' }}>Fiscal Year</div>
                      <div style={{ fontSize: '20px', fontWeight: 600, color: '#0a6ed1' }}>
                        {costCenters[0]?.fiscal_year || new Date().getFullYear()}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'gl' && (
          <div className="sap-gui-panel">
            <div className="sap-flex-between" style={{ marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>General Ledger Accounts</h3>
              <div className="sap-flex" style={{ gap: '8px' }}>
                <input 
                  type="text" 
                  className="sap-form-input" 
                  placeholder="Search account..."
                  style={{ width: '200px' }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button className="sap-toolbar-button" onClick={handleSearchAccount}>Search</button>
              </div>
            </div>

            {glAccounts.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#6a6d70' }}>
                No GL accounts found. Use the search function to find accounts.
              </div>
            ) : (
              <table className="sap-table">
                <thead>
                  <tr>
                    <th>Account Number</th>
                    <th>Description</th>
                    <th>Account Type</th>
                    <th>Balance (USD)</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {glAccounts.map((acc) => (
                    <tr key={acc.account}>
                      <td style={{ fontWeight: 600, color: '#0a6ed1', fontFamily: 'monospace' }}>{acc.account}</td>
                      <td>{acc.description}</td>
                      <td>
                        <span style={{ 
                          padding: '2px 8px', 
                          backgroundColor: '#e5f3ff',
                          borderRadius: '2px',
                          fontSize: '12px',
                          fontWeight: 500
                        }}>
                          {acc.type}
                        </span>
                      </td>
                      <td style={{ 
                        textAlign: 'right', 
                        fontWeight: 600,
                        color: acc.balance < 0 ? '#bb0000' : '#107e3e'
                      }}>
                        ${Math.abs(acc.balance).toLocaleString()}
                        {acc.balance < 0 ? ' CR' : ' DR'}
                      </td>
                      <td>
                        <button className="sap-toolbar-button" style={{ padding: '4px 8px', fontSize: '12px' }}>
                          View Entries
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="sap-gui-panel">
            <h3 style={{ margin: '0 0 16px 0' }}>Financial Reports</h3>
            
            <div className="sap-grid sap-grid-2" style={{ gap: '12px' }}>
              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>📊 Balance Sheet</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  View assets, liabilities, and equity positions
                </div>
              </div>

              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>📈 Profit & Loss</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  Income statement and profitability analysis
                </div>
              </div>

              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>💰 Cash Flow</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  Cash inflows and outflows analysis
                </div>
              </div>

              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>📋 Trial Balance</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  Debit and credit balances verification
                </div>
              </div>

              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>🎯 Budget vs Actual</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  Compare planned budget with actual spending
                </div>
              </div>

              <div style={{ padding: '16px', border: '1px solid #d9d9d9', borderRadius: '4px', cursor: 'pointer' }}
                   onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                   onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>📅 Aging Report</div>
                <div style={{ fontSize: '13px', color: '#6a6d70' }}>
                  Accounts receivable and payable aging
                </div>
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

      {/* Create Cost Center Modal */}
      <SAPFormDialog
        isOpen={showCreateCostCenterModal}
        title="Create Cost Center"
        fields={[
          { name: 'name', label: 'Cost Center Name', type: 'text', required: true },
          { name: 'budgetAmount', label: 'Budget Amount (USD)', type: 'number', required: true },
          { name: 'fiscalYear', label: 'Fiscal Year', type: 'number', required: true, defaultValue: 2025 },
          { name: 'manager', label: 'Responsible Manager', type: 'text', required: true }
        ]}
        onSubmit={handleCreateCostCenter}
        onCancel={() => setShowCreateCostCenterModal(false)}
        submitLabel="Create"
      />
    </div>
  );
};

export default FI;
