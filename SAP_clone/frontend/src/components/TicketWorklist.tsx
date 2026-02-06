/**
 * Ticket Worklist Component
 * Requirements 8.2, 8.4 - Table with sorting, filtering, status badges
 */
import React, { useState, useEffect } from 'react';
import { ticketsApi } from '../services/api';

interface Ticket {
  ticket_id: string;
  ticket_type: string;
  module: string;
  priority: string;
  status: string;
  title: string;
  sla_deadline: string;
  created_at: string;
  created_by: string;
}

interface CreateTicketForm {
  module: string;
  ticket_type: string;
  priority: string;
  title: string;
  description: string;
}

const statusColors: Record<string, { bg: string; text: string }> = {
  Open: { bg: '#e6f7ff', text: '#1890ff' },
  Assigned: { bg: '#fffbe6', text: '#faad14' },
  In_Progress: { bg: '#fff7e6', text: '#fa8c16' },
  Closed: { bg: '#f6ffed', text: '#52c41a' },
};

const priorityColors: Record<string, string> = {
  P1: '#ff4d4f',
  P2: '#fa8c16',
  P3: '#faad14',
  P4: '#52c41a',
};

const ticketTypes: Record<string, string[]> = {
  PM: ['Incident', 'Maintenance'],
  MM: ['Procurement'],
  FI: ['Finance_Approval'],
};

const TicketWorklist: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ module: '', status: '' });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<CreateTicketForm>({
    module: 'PM',
    ticket_type: 'Incident',
    priority: 'P3',
    title: '',
    description: '',
  });

  useEffect(() => {
    loadTickets();
  }, [filter, page]);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const response = await ticketsApi.list({
        module: filter.module || undefined,
        status: filter.status || undefined,
        page,
        limit: 20,
      });
      setTickets(response.data.tickets);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to load tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await ticketsApi.create({
        module: form.module,
        ticket_type: form.ticket_type,
        priority: form.priority,
        title: form.title,
        description: form.description || undefined,
        created_by: 'current_user', // In real app, get from auth context
      });
      setShowModal(false);
      setForm({ module: 'PM', ticket_type: 'Incident', priority: 'P3', title: '', description: '' });
      loadTickets();
    } catch (error) {
      console.error('Failed to create ticket:', error);
      alert('Failed to create ticket');
    } finally {
      setCreating(false);
    }
  };

  const handleModuleChange = (module: string) => {
    const types = ticketTypes[module] || [];
    setForm({ ...form, module, ticket_type: types[0] || '' });
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
    }}>
      {priority}
    </span>
  );

  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px' }}>
      {/* Header with filters and create button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <select
            value={filter.module}
            onChange={(e) => setFilter({ ...filter, module: e.target.value })}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
          >
            <option value="">All Modules</option>
            <option value="PM">Plant Maintenance</option>
            <option value="MM">Materials Management</option>
            <option value="FI">Finance</option>
          </select>
          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
          >
            <option value="">All Statuses</option>
            <option value="Open">Open</option>
            <option value="Assigned">Assigned</option>
            <option value="In_Progress">In Progress</option>
            <option value="Closed">Closed</option>
          </select>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#1890ff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          + Create Ticket
        </button>
      </div>

      {/* Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#fafafa', borderBottom: '1px solid #e8e8e8' }}>
            <th style={{ padding: '12px', textAlign: 'left' }}>Ticket ID</th>
            <th style={{ padding: '12px', textAlign: 'left' }}>Title</th>
            <th style={{ padding: '12px', textAlign: 'left' }}>Type</th>
            <th style={{ padding: '12px', textAlign: 'left' }}>Module</th>
            <th style={{ padding: '12px', textAlign: 'center' }}>Priority</th>
            <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
            <th style={{ padding: '12px', textAlign: 'left' }}>Created</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={7} style={{ padding: '24px', textAlign: 'center' }}>Loading...</td>
            </tr>
          ) : tickets.length === 0 ? (
            <tr>
              <td colSpan={7} style={{ padding: '24px', textAlign: 'center' }}>No tickets found</td>
            </tr>
          ) : (
            tickets.map((ticket) => (
              <tr key={ticket.ticket_id} style={{ borderBottom: '1px solid #e8e8e8' }}>
                <td style={{ padding: '12px' }}>{ticket.ticket_id}</td>
                <td style={{ padding: '12px' }}>{ticket.title}</td>
                <td style={{ padding: '12px' }}>{ticket.ticket_type}</td>
                <td style={{ padding: '12px' }}>{ticket.module}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <PriorityBadge priority={ticket.priority} />
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <StatusBadge status={ticket.status} />
                </td>
                <td style={{ padding: '12px' }}>
                  {new Date(ticket.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Total: {total} tickets</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={{ padding: '8px 16px', cursor: page === 1 ? 'not-allowed' : 'pointer' }}
          >
            Previous
          </button>
          <span style={{ padding: '8px' }}>Page {page}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={tickets.length < 20}
            style={{ padding: '8px 16px', cursor: tickets.length < 20 ? 'not-allowed' : 'pointer' }}
          >
            Next
          </button>
        </div>
      </div>

      {/* Create Ticket Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            width: '500px',
            maxHeight: '90vh',
            overflow: 'auto',
          }}>
            <h2 style={{ marginTop: 0 }}>Create Ticket</h2>
            <form onSubmit={handleCreateTicket}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Module</label>
                <select
                  value={form.module}
                  onChange={(e) => handleModuleChange(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
                >
                  <option value="PM">Plant Maintenance (PM)</option>
                  <option value="MM">Materials Management (MM)</option>
                  <option value="FI">Finance (FI)</option>
                </select>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Ticket Type</label>
                <select
                  value={form.ticket_type}
                  onChange={(e) => setForm({ ...form, ticket_type: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
                >
                  {(ticketTypes[form.module] || []).map(type => (
                    <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Priority</label>
                <select
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
                >
                  <option value="P1">P1 - Critical</option>
                  <option value="P2">P2 - High</option>
                  <option value="P3">P3 - Medium</option>
                  <option value="P4">P4 - Low</option>
                </select>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Title</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}
                  placeholder="Enter ticket title"
                />
              </div>
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={4}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', boxSizing: 'border-box', resize: 'vertical' }}
                  placeholder="Enter ticket description (optional)"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #d9d9d9', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#1890ff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: creating ? 'not-allowed' : 'pointer',
                  }}
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TicketWorklist;
