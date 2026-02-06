import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Breadcrumbs,
  Link
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Assignment as TicketIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  CheckCircle
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const MULESOFT_URL = process.env.REACT_APP_MULESOFT_URL || "http://localhost:4797";

const MyTickets = () => {
  const navigate = useNavigate();
  const { API_URL } = useAuth();
  const [searchParams] = useSearchParams();
  const [tickets, setTickets] = useState([]);
  const [pendingApprovalTickets, setPendingApprovalTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showTicketDialog, setShowTicketDialog] = useState(false);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [selectedApprovalTicket, setSelectedApprovalTicket] = useState(null);
  const [approvalComments, setApprovalComments] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    // Check URL parameter for tab selection
    const tab = searchParams.get('tab');
    if (tab === 'approvals') {
      setTabValue(1);
    } else {
      setTabValue(0);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchTickets();
    fetchPendingApprovalTickets();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchTickets = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching tickets with token:', token ? 'Token exists' : 'No token');

      const response = await fetch(`${API_URL}/tickets/?my_tickets=true`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Tickets response status:', response.status);
      const data = await response.json();
      console.log('Tickets data received:', data);
      setTickets(data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingApprovalTickets = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching pending approval tickets');

      // Fetch all tickets with pending_approval status
      const response = await fetch(`${API_URL}/tickets/?status=pending_approval`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Pending approval tickets response status:', response.status);
      const data = await response.json();
      console.log('Pending approval tickets received:', data);
      setPendingApprovalTickets(data);
    } catch (error) {
      console.error('Error fetching pending approval tickets:', error);
    }
  };

  // Send notification to MuleSoft
  const notifyMuleSoft = async (ticket, action, comments) => {
    try {
      const payload = {
        ticket_id: ticket.id,
        ticket_number: ticket.ticket_number,
        title: ticket.title,
        description: ticket.description,
        status: action, // 'approved' or 'rejected'
        action_taken: action,
        comments: comments,
        action_timestamp: new Date().toISOString(),
        category: ticket.category,
        subcategory: ticket.subcategory,
        priority: ticket.priority,
        requester_name: ticket.requester_name
      };

      console.log('Sending to MuleSoft:', payload);

      const response = await fetch(`${MULESOFT_URL}/api/ticket-approval`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        console.log('MuleSoft notification sent successfully');
      } else {
        console.error('MuleSoft notification failed:', response.status);
      }
    } catch (error) {
      console.error('Error sending to MuleSoft:', error);
      // Don't throw - we don't want to fail the approval if MuleSoft is unreachable
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'draft': 'default',
      'submitted': 'info',
      'pending_approval': 'warning',
      'approved': 'success',
      'rejected': 'error',
      'in_progress': 'primary',
      'resolved': 'success',
      'closed': 'default',
      'cancelled': 'error'
    };
    return colors[status] || 'default';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'low': 'success',
      'medium': 'warning',
      'high': 'error',
      'critical': 'error'
    };
    return colors[priority] || 'default';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleViewTicket = (ticket) => {
    setSelectedTicket(ticket);
    setShowTicketDialog(true);
  };

  const handleApprovalAction = (ticket) => {
    setSelectedApprovalTicket(ticket);
    setApprovalComments('');
    setShowApprovalDialog(true);
  };

  // Direct approve/reject from table (without dialog)
  const handleDirectAction = async (ticket, action) => {
    setActionLoading(ticket.id);
    try {
      const token = localStorage.getItem('token');
      const newStatus = action === 'approve' ? 'approved' : 'rejected';

      // Update ticket status
      const response = await fetch(`${API_URL}/tickets/${ticket.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status: newStatus
        })
      });

      if (response.ok) {
        // Send notification to MuleSoft
        await notifyMuleSoft(ticket, newStatus, '');

        // Refresh data
        fetchPendingApprovalTickets();
        fetchTickets();
        alert(`Ticket ${newStatus} successfully!`);
      } else {
        throw new Error('Failed to update ticket');
      }
    } catch (error) {
      console.error('Error updating ticket:', error);
      alert('Error updating ticket. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  // Submit approval from dialog (with comments)
  const submitApproval = async (action) => {
    try {
      const token = localStorage.getItem('token');
      const newStatus = action === 'approve' ? 'approved' : 'rejected';

      // Update ticket status
      const response = await fetch(`${API_URL}/tickets/${selectedApprovalTicket.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status: newStatus,
          resolution_notes: approvalComments || undefined
        })
      });

      if (response.ok) {
        // Send notification to MuleSoft
        await notifyMuleSoft(selectedApprovalTicket, newStatus, approvalComments);

        setShowApprovalDialog(false);
        fetchPendingApprovalTickets();
        fetchTickets();
        alert(`Ticket ${newStatus} successfully!`);
      } else {
        throw new Error('Failed to update ticket');
      }
    } catch (error) {
      console.error('Error updating ticket:', error);
      alert('Error updating ticket. Please try again.');
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Loading tickets...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      {/* Header */}
      <Box sx={{ p: 3, backgroundColor: 'white', borderBottom: '1px solid #dee2e6' }}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link 
            color="inherit" 
            href="#" 
            onClick={(e) => { e.preventDefault(); navigate('/'); }}
            sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
          >
            Home
          </Link>
          <Typography color="text.primary">Tickets</Typography>
        </Breadcrumbs>
        
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h4" sx={{ color: '#333', fontWeight: 600 }}>
            Tickets & Approvals
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => { fetchTickets(); fetchPendingApprovalTickets(); }}
            sx={{ borderColor: '#FF8C42', color: '#FF8C42' }}
          >
            Refresh
          </Button>
        </Box>
        
        <Typography variant="body1" color="text.secondary">
          Track your submitted tickets and manage approval requests
        </Typography>
      </Box>

      <Box sx={{ p: 3 }}>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <TicketIcon sx={{ fontSize: 40, color: '#FF8C42', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 600, color: '#333' }}>
                  {tickets.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Tickets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <TicketIcon sx={{ fontSize: 40, color: '#8B1538', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 600, color: '#333' }}>
                  {tickets.filter(t => ['submitted', 'pending_approval', 'approved', 'in_progress'].includes(t.status)).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Open Tickets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <ApproveIcon sx={{ fontSize: 40, color: '#4CAF50', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 600, color: '#333' }}>
                  {pendingApprovalTickets.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pending Approvals
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <CheckCircle sx={{ fontSize: 40, color: '#2196F3', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 600, color: '#333' }}>
                  {tickets.filter(t => ['resolved', 'closed'].includes(t.status)).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Resolved Tickets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label={`Tickets (${tickets.length})`} />
            <Tab label={`Approvals (${pendingApprovalTickets.length})`} />
          </Tabs>
        </Paper>

        {/* Tickets Tab */}
        {tabValue === 0 && (
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell><strong>Ticket #</strong></TableCell>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Type</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><strong>Priority</strong></TableCell>
                    <TableCell><strong>Created</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tickets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">
                          No tickets found. Create your first ticket from the homepage.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    tickets.map((ticket) => (
                      <TableRow key={ticket.id} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#8B1538' }}>
                            {ticket.ticket_number}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {ticket.title}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={ticket.ticket_type.replace('_', ' ')} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={ticket.status.replace('_', ' ')} 
                            size="small" 
                            color={getStatusColor(ticket.status)}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={ticket.priority} 
                            size="small" 
                            color={getPriorityColor(ticket.priority)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {formatDate(ticket.created_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton 
                              size="small" 
                              onClick={() => handleViewTicket(ticket)}
                              sx={{ color: '#FF8C42' }}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )}

        {/* Approvals Tab */}
        {tabValue === 1 && (
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell><strong>Ticket #</strong></TableCell>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Category</strong></TableCell>
                    <TableCell><strong>Priority</strong></TableCell>
                    <TableCell><strong>Requester</strong></TableCell>
                    <TableCell><strong>Created</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pendingApprovalTickets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">
                          No pending approval requests found.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    pendingApprovalTickets.map((ticket) => (
                      <TableRow key={ticket.id} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#8B1538' }}>
                            {ticket.ticket_number}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {ticket.title}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {ticket.category || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={ticket.priority}
                            size="small"
                            color={getPriorityColor(ticket.priority)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {ticket.requester_name || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {formatDate(ticket.created_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Approve">
                              <IconButton
                                size="small"
                                onClick={() => handleDirectAction(ticket, 'approve')}
                                disabled={actionLoading === ticket.id}
                                sx={{
                                  color: '#4CAF50',
                                  '&:hover': { backgroundColor: '#E8F5E9' }
                                }}
                              >
                                <ApproveIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reject">
                              <IconButton
                                size="small"
                                onClick={() => handleDirectAction(ticket, 'reject')}
                                disabled={actionLoading === ticket.id}
                                sx={{
                                  color: '#f44336',
                                  '&:hover': { backgroundColor: '#FFEBEE' }
                                }}
                              >
                                <RejectIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="View Details & Add Comments">
                              <IconButton
                                size="small"
                                onClick={() => handleApprovalAction(ticket)}
                                disabled={actionLoading === ticket.id}
                                sx={{ color: '#FF8C42' }}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )}
      </Box>

      {/* Ticket Detail Dialog */}
      <Dialog 
        open={showTicketDialog} 
        onClose={() => setShowTicketDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedTicket && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">
                  Ticket {selectedTicket.ticket_number}
                </Typography>
                <Chip 
                  label={selectedTicket.status.replace('_', ' ')} 
                  color={getStatusColor(selectedTicket.status)}
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Title</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedTicket.title}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Type</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedTicket.ticket_type.replace('_', ' ')}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Priority</Typography>
                  <Chip label={selectedTicket.priority} size="small" color={getPriorityColor(selectedTicket.priority)} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Created</Typography>
                  <Typography variant="body1">{formatDate(selectedTicket.created_at)}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {selectedTicket.description}
                  </Typography>
                </Grid>
                {selectedTicket.resolution_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Resolution Notes</Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedTicket.resolution_notes}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowTicketDialog(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Approval Dialog */}
      <Dialog
        open={showApprovalDialog}
        onClose={() => setShowApprovalDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedApprovalTicket && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">
                  Approval Request - {selectedApprovalTicket.ticket_number}
                </Typography>
                <Chip
                  label="Pending Approval"
                  size="small"
                  color="warning"
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {selectedApprovalTicket.title}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Requester</Typography>
                  <Typography variant="body1">{selectedApprovalTicket.requester_name || '-'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Priority</Typography>
                  <Chip label={selectedApprovalTicket.priority} size="small" color={getPriorityColor(selectedApprovalTicket.priority)} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Category</Typography>
                  <Typography variant="body1">{selectedApprovalTicket.category || '-'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">Created</Typography>
                  <Typography variant="body1">{formatDate(selectedApprovalTicket.created_at)}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', backgroundColor: '#f5f5f5', p: 2, borderRadius: 1 }}>
                    {selectedApprovalTicket.description}
                  </Typography>
                </Grid>
                {selectedApprovalTicket.business_justification && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Business Justification</Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedApprovalTicket.business_justification}
                    </Typography>
                  </Grid>
                )}
                {selectedApprovalTicket.estimated_cost && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Estimated Cost</Typography>
                    <Typography variant="body1">{selectedApprovalTicket.estimated_cost}</Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Comments (optional)"
                    value={approvalComments}
                    onChange={(e) => setApprovalComments(e.target.value)}
                    placeholder="Add any comments for this approval decision..."
                  />
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions sx={{ p: 2, gap: 1 }}>
              <Button
                onClick={() => setShowApprovalDialog(false)}
                color="inherit"
              >
                Cancel
              </Button>
              <Button
                onClick={() => submitApproval('reject')}
                color="error"
                variant="outlined"
                startIcon={<RejectIcon />}
              >
                Reject
              </Button>
              <Button
                onClick={() => submitApproval('approve')}
                color="success"
                startIcon={<ApproveIcon />}
                variant="contained"
              >
                Approve
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default MyTickets;