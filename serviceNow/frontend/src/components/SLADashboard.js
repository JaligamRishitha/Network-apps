import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Search as SearchIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const SLADashboard = () => {
  const { API_URL, token } = useAuth();
  const [breaches, setBreaches] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketSLA, setTicketSLA] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const fetchSLAData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      const [breachesRes, warningsRes] = await Promise.all([
        fetch(`${API_URL}/api/sla/check-breaches`, { headers }),
        fetch(`${API_URL}/api/sla/warnings`, { headers }),
      ]);

      if (!breachesRes.ok || !warningsRes.ok) {
        throw new Error('Failed to fetch SLA data');
      }

      const breachesData = await breachesRes.json();
      const warningsData = await warningsRes.json();

      setBreaches(Array.isArray(breachesData) ? breachesData : breachesData.breaches || []);
      setWarnings(Array.isArray(warningsData) ? warningsData : warningsData.warnings || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchSLAData();
  }, [fetchSLAData]);

  const fetchTicketSLA = async (ticketId) => {
    setDetailLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/sla/ticket/${ticketId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch ticket SLA details');
      }

      const data = await response.json();
      setTicketSLA(data);
      setDetailDialogOpen(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleViewDetails = (ticket) => {
    setSelectedTicket(ticket);
    fetchTicketSLA(ticket.ticket_id || ticket.id);
  };

  const handleCloseDialog = () => {
    setDetailDialogOpen(false);
    setSelectedTicket(null);
    setTicketSLA(null);
  };

  const getPriorityColor = (priority) => {
    const colors = {
      critical: '#d32f2f',
      high: '#f57c00',
      medium: '#fbc02d',
      low: '#388e3c',
    };
    return colors[priority?.toLowerCase()] || '#757575';
  };

  const getStatusChip = (status) => {
    const config = {
      breached: { color: 'error', icon: <ErrorIcon fontSize="small" /> },
      warning: { color: 'warning', icon: <WarningIcon fontSize="small" /> },
      on_track: { color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
    };
    const { color, icon } = config[status?.toLowerCase()] || { color: 'default', icon: null };
    return (
      <Chip
        label={status || 'Unknown'}
        color={color}
        size="small"
        icon={icon}
      />
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatTimeRemaining = (minutes) => {
    if (minutes === null || minutes === undefined) return 'N/A';
    if (minutes < 0) return 'Overdue';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const filterData = (data) => {
    if (!searchTerm) return data;
    return data.filter(item =>
      (item.ticket_number || item.id || '').toString().toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.title || item.short_description || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600, color: '#2c3e50' }}>
        SLA Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#ffebee', borderLeft: '4px solid #d32f2f' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    SLA Breaches
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#d32f2f' }}>
                    {breaches.length}
                  </Typography>
                </Box>
                <ErrorIcon sx={{ fontSize: 40, color: '#d32f2f', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fff3e0', borderLeft: '4px solid #f57c00' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    SLA Warnings
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f57c00' }}>
                    {warnings.length}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 40, color: '#f57c00', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e3f2fd', borderLeft: '4px solid #1976d2' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Total At Risk
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    {breaches.length + warnings.length}
                  </Typography>
                </Box>
                <AccessTimeIcon sx={{ fontSize: 40, color: '#1976d2', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e8f5e9', borderLeft: '4px solid #388e3c' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Compliance Rate
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#388e3c' }}>
                    {breaches.length === 0 ? '100%' : 'N/A'}
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, color: '#388e3c', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <TextField
        fullWidth
        placeholder="Search by ticket number or title..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      {/* SLA Breaches Panel */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <ErrorIcon sx={{ color: '#d32f2f', mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              SLA Breaches ({filterData(breaches).length})
            </Typography>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell><strong>Ticket #</strong></TableCell>
                  <TableCell><strong>Title</strong></TableCell>
                  <TableCell><strong>Priority</strong></TableCell>
                  <TableCell><strong>Breach Time</strong></TableCell>
                  <TableCell><strong>Overdue By</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filterData(breaches).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography color="textSecondary">No SLA breaches found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filterData(breaches).map((breach) => (
                    <TableRow key={breach.ticket_id || breach.id} hover>
                      <TableCell>{breach.ticket_number || breach.ticket_id || breach.id}</TableCell>
                      <TableCell>{breach.title || breach.short_description}</TableCell>
                      <TableCell>
                        <Chip
                          label={breach.priority || 'Unknown'}
                          size="small"
                          sx={{ bgcolor: getPriorityColor(breach.priority), color: 'white' }}
                        />
                      </TableCell>
                      <TableCell>{formatDate(breach.breach_time || breach.breached_at)}</TableCell>
                      <TableCell sx={{ color: '#d32f2f', fontWeight: 600 }}>
                        {formatTimeRemaining(breach.overdue_minutes)}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleViewDetails(breach)}
                          disabled={detailLoading}
                        >
                          View SLA
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* SLA Warnings Panel */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WarningIcon sx={{ color: '#f57c00', mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              SLA Warnings ({filterData(warnings).length})
            </Typography>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#fff3e0' }}>
                  <TableCell><strong>Ticket #</strong></TableCell>
                  <TableCell><strong>Title</strong></TableCell>
                  <TableCell><strong>Priority</strong></TableCell>
                  <TableCell><strong>Time Remaining</strong></TableCell>
                  <TableCell><strong>Due Date</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filterData(warnings).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography color="textSecondary">No SLA warnings found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filterData(warnings).map((warning) => (
                    <TableRow key={warning.ticket_id || warning.id} hover>
                      <TableCell>{warning.ticket_number || warning.ticket_id || warning.id}</TableCell>
                      <TableCell>{warning.title || warning.short_description}</TableCell>
                      <TableCell>
                        <Chip
                          label={warning.priority || 'Unknown'}
                          size="small"
                          sx={{ bgcolor: getPriorityColor(warning.priority), color: 'white' }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#f57c00', fontWeight: 600 }}>
                        {formatTimeRemaining(warning.time_remaining_minutes || warning.minutes_remaining)}
                      </TableCell>
                      <TableCell>{formatDate(warning.due_date || warning.sla_due)}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleViewDetails(warning)}
                          disabled={detailLoading}
                        >
                          View SLA
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Ticket SLA Details Dialog */}
      <Dialog open={detailDialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccessTimeIcon sx={{ mr: 1 }} />
            Ticket SLA Details
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : ticketSLA ? (
            <Box>
              <Typography variant="subtitle2" color="textSecondary">Ticket Number</Typography>
              <Typography sx={{ mb: 2 }}>{ticketSLA.ticket_number || selectedTicket?.ticket_number || 'N/A'}</Typography>

              <Typography variant="subtitle2" color="textSecondary">Title</Typography>
              <Typography sx={{ mb: 2 }}>{ticketSLA.title || selectedTicket?.title || 'N/A'}</Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" color="textSecondary">SLA Status</Typography>
              <Box sx={{ mb: 2 }}>{getStatusChip(ticketSLA.sla_status || ticketSLA.status)}</Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Response SLA</Typography>
                  <Typography>{ticketSLA.response_sla || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Resolution SLA</Typography>
                  <Typography>{ticketSLA.resolution_sla || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Response Due</Typography>
                  <Typography>{formatDate(ticketSLA.response_due)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Resolution Due</Typography>
                  <Typography>{formatDate(ticketSLA.resolution_due)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Time Elapsed</Typography>
                  <Typography>{ticketSLA.time_elapsed || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Time Remaining</Typography>
                  <Typography sx={{ color: ticketSLA.time_remaining_minutes < 0 ? '#d32f2f' : 'inherit' }}>
                    {formatTimeRemaining(ticketSLA.time_remaining_minutes)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          ) : (
            <Typography color="textSecondary">No SLA data available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SLADashboard;
