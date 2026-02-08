/**
 * Tickets Page
 * Requirement 8.2 - Ticket worklist with ServiceNow integration
 */
import React, { useState, useEffect } from 'react';
import { ticketsApi, passwordResetApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface Ticket {
  ticket_id: string;
  ticket_type: string;
  module: string;
  priority: string;
  status: string;
  title: string;
  description?: string;
  sla_deadline: string;
  created_at: string;
  created_by: string;
  assigned_to?: string;
}

interface PasswordResetTicket {
  sap_ticket_id: string;
  servicenow_ticket_id: string;
  username: string;
  user_email: string;
  requester_name: string;
  reason: string;
  priority: string;
  status: string;
  created_at: string;
  updated_at: string;
  assigned_to: string | null;
  comments: Array<{
    comment: string;
    by: string;
    at: string;
    status_change?: string;
  }>;
}

const statusColors: Record<string, { bg: string; text: string }> = {
  Open: { bg: '#e6f7ff', text: '#1890ff' },
  Assigned: { bg: '#fffbe6', text: '#faad14' },
  In_Progress: { bg: '#fff7e6', text: '#fa8c16' },
  Closed: { bg: '#f6ffed', text: '#52c41a' },
  pending: { bg: '#fffbe6', text: '#faad14' },
  Pending: { bg: '#fffbe6', text: '#faad14' },
  open: { bg: '#e6f7ff', text: '#1890ff' },
  completed: { bg: '#f6ffed', text: '#52c41a' },
  Completed: { bg: '#f6ffed', text: '#52c41a' },
};

const priorityColors: Record<string, string> = {
  P1: '#ff4d4f',
  P2: '#fa8c16',
  P3: '#faad14',
  P4: '#52c41a',
  High: '#ff4d4f',
  Medium: '#fa8c16',
  Low: '#52c41a',
  high: '#ff4d4f',
  medium: '#fa8c16',
  low: '#52c41a',
  critical: '#ff4d4f',
};

const Tickets: React.FC = () => {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [passwordTickets, setPasswordTickets] = useState<PasswordResetTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ module: '', status: '' });
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [viewTicket, setViewTicket] = useState<Ticket | null>(null);
  const [passwordModal, setPasswordModal] = useState<{
    show: boolean;
    username: string;
    password: string;
    ticketNumber: string;
  }>({ show: false, username: '', password: '', ticketNumber: '' });

  useEffect(() => {
    loadAllTickets();
  }, [filter]);

  const loadAllTickets = async () => {
    setLoading(true);
    try {
      console.log('Loading tickets...');

      const results = await Promise.allSettled([
        passwordResetApi.listTickets(),
        filter.module !== 'ServiceNow'
          ? ticketsApi.list({
              module: filter.module || undefined,
              status: filter.status || undefined,
              limit: 50,
            })
          : Promise.resolve({ data: { tickets: [] } })
      ]);

      // Handle ServiceNow password reset tickets (index 0)
      if (results[0].status === 'fulfilled') {
        const passwordData = results[0].value.data.tickets || results[0].value.data || [];
        console.log('Password tickets loaded:', passwordData.length);
        setPasswordTickets(Array.isArray(passwordData) ? passwordData : []);
      } else {
        console.error('Failed to load ServiceNow tickets:', results[0].reason);
        setPasswordTickets([]);
      }

      // Handle regular tickets (index 1)
      if (results[1].status === 'fulfilled') {
        const regularTickets = results[1].value.data.tickets || [];
        console.log('Regular tickets loaded:', regularTickets.length);
        setTickets(regularTickets);
      } else {
        console.error('Failed to load regular tickets:', results[1].reason);
        setTickets([]);
      }
    } catch (error) {
      console.error('Failed to load tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (ticket: PasswordResetTicket) => {
    const ticketDisplayId = ticket.sap_ticket_id || ticket.servicenow_ticket_id;
    const confirmed = window.confirm(
      `Reset password for user "${ticket.username}"?\n\nTicket: ${ticketDisplayId}`
    );
    if (!confirmed) return;

    setProcessingId(ticket.sap_ticket_id);
    try {
      // Call the reset password API - returns the generated password
      const response = await passwordResetApi.resetPassword(ticket.sap_ticket_id, user?.username || 'admin');
      const generatedPassword = response.data?.new_password || response.data?.password || response.data?.generated_password || 'Password generated successfully';

      // Update ticket status to completed
      await passwordResetApi.updateStatus(ticket.sap_ticket_id, 'completed', user?.username || 'admin');

      // Show modal with the generated password
      setPasswordModal({
        show: true,
        username: ticket.username,
        password: generatedPassword,
        ticketNumber: ticketDisplayId,
      });

      // Reload tickets to reflect status change
      loadAllTickets();
    } catch (err: any) {
      alert(`Failed to reset password: ${err.response?.data?.detail || err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Password copied to clipboard!');
    }).catch(() => {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('Password copied to clipboard!');
    });
  };

  const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const colors = statusColors[status] || { bg: '#f0f0f0', text: '#666' };
    return (
      <span style={{
        padding: '4px 8px',
        borderRadius: '4px',
        backgroundColor: colors.bg,
        color: colors.text,
        fontSize: '12px',
        fontWeight: 500,
      }}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => (
    <span style={{
      padding: '2px 6px',
      borderRadius: '4px',
      backgroundColor: priorityColors[priority] || '#666',
      color: 'white',
      fontSize: '11px',
      fontWeight: 600,
      textTransform: 'capitalize',
    }}>
      {priority}
    </span>
  );

  const filteredPasswordTickets = passwordTickets.filter(ticket => {
    if (filter.module && filter.module !== 'ServiceNow') return false;
    if (filter.status && !ticket.status.toLowerCase().includes(filter.status.toLowerCase())) return false;
    return true;
  });

  const filteredRegularTickets = tickets.filter(ticket => {
    if (filter.module && filter.module !== ticket.module) return false;
    return true;
  });

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>All Tickets</h2>
      
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px' }}>
        {/* Filters */}
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          <select
            value={filter.module}
            onChange={(e) => setFilter({ ...filter, module: e.target.value })}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
          >
            <option value="">All Sources</option>
            <option value="PM">Plant Maintenance</option>
            <option value="MM">Materials Management</option>
            <option value="FI">Finance</option>
            <option value="ServiceNow">ServiceNow (Password Reset)</option>
          </select>
          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
          >
            <option value="">All Statuses</option>
            <option value="Open">Open</option>
            <option value="pending">Pending</option>
            <option value="In_Progress">In Progress</option>
            <option value="Closed">Closed</option>
          </select>
          <button
            onClick={loadAllTickets}
            disabled={loading}
            style={{
              padding: '8px 16px',
              backgroundColor: '#1890ff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Combined Table */}
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#fafafa', borderBottom: '1px solid #e8e8e8' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Ticket ID</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Title/Username</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Type/Source</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Priority</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Created</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: '24px', textAlign: 'center' }}>Loading...</td>
              </tr>
            ) : (
              <>
                {/* ServiceNow Password Reset Tickets */}
                {filteredPasswordTickets.map((ticket) => (
                  <tr key={`pw-${ticket.sap_ticket_id}`} style={{ borderBottom: '1px solid #e8e8e8', backgroundColor: '#fffbf0' }}>
                    <td style={{ padding: '12px', fontFamily: 'monospace' }}>
                      {ticket.sap_ticket_id || ticket.servicenow_ticket_id}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ fontWeight: 500 }}>{ticket.username}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>{ticket.user_email}</div>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ color: '#fa8c16', fontWeight: 500 }}>ServiceNow</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>Password Reset</div>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <PriorityBadge priority={ticket.priority || 'medium'} />
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td style={{ padding: '12px' }}>
                      {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {['pending', 'Pending', 'open', 'Open'].includes(ticket.status) && (
                        <button
                          onClick={() => handleResetPassword(ticket)}
                          disabled={processingId === ticket.sap_ticket_id}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: processingId === ticket.sap_ticket_id ? '#d9d9d9' : '#52c41a',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: processingId === ticket.sap_ticket_id ? 'not-allowed' : 'pointer',
                            fontSize: '12px',
                          }}
                        >
                          {processingId === ticket.sap_ticket_id ? 'Processing...' : 'Reset Password'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                
                {/* Regular Tickets */}
                {filteredRegularTickets.map((ticket) => (
                  <tr key={ticket.ticket_id} style={{ borderBottom: '1px solid #e8e8e8' }}>
                    <td style={{ padding: '12px' }}>{ticket.ticket_id}</td>
                    <td style={{ padding: '12px' }}>{ticket.title}</td>
                    <td style={{ padding: '12px' }}>
                      <div>{ticket.module}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>{ticket.ticket_type}</div>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <PriorityBadge priority={ticket.priority} />
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td style={{ padding: '12px' }}>
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <button
                        onClick={() => setViewTicket(ticket)}
                        style={{
                          padding: '6px 12px', backgroundColor: '#1890ff', color: 'white',
                          border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}

                {filteredPasswordTickets.length === 0 && filteredRegularTickets.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ padding: '24px', textAlign: 'center' }}>No tickets found</td>
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>

        {/* Summary */}
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            Total: {filteredRegularTickets.length + filteredPasswordTickets.length} tickets
            ({filteredPasswordTickets.length} ServiceNow, {filteredRegularTickets.length} Internal)
          </span>
        </div>
      </div>

      {/* Ticket View Modal */}
      {viewTicket && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white', borderRadius: '8px', padding: '0',
            width: '580px', maxHeight: '80vh', overflow: 'auto',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
          }}>
            {/* Header */}
            <div style={{
              backgroundColor: '#1890ff', color: 'white', padding: '14px 20px',
              borderRadius: '8px 8px 0 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>Ticket Details - {viewTicket.ticket_id}</span>
              <button onClick={() => setViewTicket(null)} style={{
                background: 'none', border: 'none', color: 'white', fontSize: '20px', cursor: 'pointer'
              }}>×</button>
            </div>
            {/* Body */}
            <div style={{ padding: '20px' }}>
              <table style={{ width: '100%', fontSize: '13px' }}>
                <tbody>
                  <tr><td style={{ padding: '6px 8px', color: '#666', width: '140px', verticalAlign: 'top' }}>Title</td><td style={{ padding: '6px 8px', fontWeight: 500 }}>{viewTicket.title}</td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Module</td><td style={{ padding: '6px 8px' }}>{viewTicket.module}</td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Type</td><td style={{ padding: '6px 8px' }}>{viewTicket.ticket_type}</td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Priority</td><td style={{ padding: '6px 8px' }}><PriorityBadge priority={viewTicket.priority} /></td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Status</td><td style={{ padding: '6px 8px' }}><StatusBadge status={viewTicket.status} /></td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Created By</td><td style={{ padding: '6px 8px' }}>{viewTicket.created_by}</td></tr>
                  {viewTicket.assigned_to && <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Assigned To</td><td style={{ padding: '6px 8px' }}>{viewTicket.assigned_to}</td></tr>}
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>Created</td><td style={{ padding: '6px 8px' }}>{new Date(viewTicket.created_at).toLocaleString()}</td></tr>
                  <tr><td style={{ padding: '6px 8px', color: '#666', verticalAlign: 'top' }}>SLA Deadline</td><td style={{ padding: '6px 8px' }}>{new Date(viewTicket.sla_deadline).toLocaleString()}</td></tr>
                </tbody>
              </table>

              {/* Description */}
              {viewTicket.description && (
                <div style={{ marginTop: '16px' }}>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: '#1890ff', marginBottom: '8px', borderBottom: '1px solid #e8e8e8', paddingBottom: '4px' }}>Description</div>
                  <div style={{ backgroundColor: '#f9f9f9', padding: '12px', borderRadius: '4px', fontSize: '12px', whiteSpace: 'pre-wrap', lineHeight: '1.6', maxHeight: '250px', overflow: 'auto', border: '1px solid #e8e8e8' }}>
                    {viewTicket.description}
                  </div>
                </div>
              )}
            </div>
            {/* Footer */}
            <div style={{ padding: '12px 20px', borderTop: '1px solid #e8e8e8', textAlign: 'right' }}>
              <button onClick={() => setViewTicket(null)} style={{
                padding: '8px 24px', backgroundColor: '#1890ff', color: 'white',
                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', fontWeight: 500
              }}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Password Generated Modal */}
      {passwordModal.show && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            width: '450px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: '#52c41a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '24px' }}>✓</span> Password Reset Successful
              </h3>
            </div>

            <div style={{
              backgroundColor: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: '6px',
              padding: '16px',
              marginBottom: '16px'
            }}>
              <div style={{ marginBottom: '12px' }}>
                <span style={{ color: '#666', fontSize: '13px' }}>Ticket Number:</span>
                <div style={{ fontWeight: 500, fontFamily: 'monospace' }}>{passwordModal.ticketNumber}</div>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <span style={{ color: '#666', fontSize: '13px' }}>Username:</span>
                <div style={{ fontWeight: 500 }}>{passwordModal.username}</div>
              </div>
              <div>
                <span style={{ color: '#666', fontSize: '13px' }}>New Password:</span>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginTop: '4px'
                }}>
                  <code style={{
                    backgroundColor: '#fff',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    fontSize: '16px',
                    fontWeight: 600,
                    letterSpacing: '1px',
                    flex: 1,
                  }}>
                    {passwordModal.password}
                  </code>
                  <button
                    onClick={() => copyToClipboard(passwordModal.password)}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#1890ff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px',
                    }}
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>

            <div style={{
              backgroundColor: '#fffbe6',
              border: '1px solid #ffe58f',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '16px',
              fontSize: '13px',
              color: '#ad6800'
            }}>
              <strong>Note:</strong> Please share this password securely with the user. The ticket status has been updated to <strong>Completed</strong>.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setPasswordModal({ show: false, username: '', password: '', ticketNumber: '' })}
                style={{
                  padding: '10px 24px',
                  backgroundColor: '#52c41a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 500,
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tickets;
