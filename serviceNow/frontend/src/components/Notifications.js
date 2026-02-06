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
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  Email as EmailIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Notifications = () => {
  const { API_URL, token } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedNotifications, setSelectedNotifications] = useState([]);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [processResult, setProcessResult] = useState(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/notifications/pending`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pending notifications');
      }

      const data = await response.json();
      setNotifications(Array.isArray(data) ? data : data.notifications || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleProcessNotifications = async () => {
    setProcessing(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${API_URL}/api/notifications/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification_ids: selectedNotifications.length > 0 ? selectedNotifications : undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process notifications');
      }

      const result = await response.json();
      setProcessResult(result);
      setSuccess(`Successfully processed ${result.processed || result.sent || 'all'} notifications`);
      setSelectedNotifications([]);
      setConfirmDialogOpen(false);

      // Refresh the list
      fetchNotifications();
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedNotifications(notifications.map(n => n.id || n.notification_id));
    } else {
      setSelectedNotifications([]);
    }
  };

  const handleSelectNotification = (notificationId) => {
    setSelectedNotifications(prev => {
      if (prev.includes(notificationId)) {
        return prev.filter(id => id !== notificationId);
      } else {
        return [...prev, notificationId];
      }
    });
  };

  const getTypeIcon = (type) => {
    const icons = {
      email: <EmailIcon fontSize="small" />,
      warning: <WarningIcon fontSize="small" />,
      info: <InfoIcon fontSize="small" />,
      success: <CheckCircleIcon fontSize="small" />,
      sla: <ScheduleIcon fontSize="small" />,
    };
    return icons[type?.toLowerCase()] || <NotificationsIcon fontSize="small" />;
  };

  const getTypeColor = (type) => {
    const colors = {
      email: '#1976d2',
      warning: '#f57c00',
      info: '#0288d1',
      success: '#388e3c',
      sla: '#7b1fa2',
      error: '#d32f2f',
    };
    return colors[type?.toLowerCase()] || '#757575';
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getGroupedByType = () => {
    const grouped = {};
    notifications.forEach(n => {
      const type = n.type || 'other';
      if (!grouped[type]) grouped[type] = 0;
      grouped[type]++;
    });
    return grouped;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  const groupedByType = getGroupedByType();

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: '#2c3e50' }}>
          Notifications
        </Typography>
        <Box>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchNotifications} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e3f2fd', borderLeft: '4px solid #1976d2' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Pending Notifications
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    {notifications.length}
                  </Typography>
                </Box>
                <NotificationsIcon sx={{ fontSize: 40, color: '#1976d2', opacity: 0.7 }} />
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
                    Email Notifications
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f57c00' }}>
                    {groupedByType.email || 0}
                  </Typography>
                </Box>
                <EmailIcon sx={{ fontSize: 40, color: '#f57c00', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#f3e5f5', borderLeft: '4px solid #7b1fa2' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    SLA Notifications
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#7b1fa2' }}>
                    {groupedByType.sla || 0}
                  </Typography>
                </Box>
                <ScheduleIcon sx={{ fontSize: 40, color: '#7b1fa2', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#ffebee', borderLeft: '4px solid #d32f2f' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Warning Notifications
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#d32f2f' }}>
                    {groupedByType.warning || 0}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 40, color: '#d32f2f', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Process Button */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Send Pending Notifications
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {selectedNotifications.length > 0
                  ? `${selectedNotifications.length} notification(s) selected`
                  : 'Select notifications or process all pending'}
              </Typography>
            </Box>
            <Button
              variant="contained"
              color="primary"
              startIcon={processing ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              onClick={() => setConfirmDialogOpen(true)}
              disabled={processing || notifications.length === 0}
              sx={{ bgcolor: '#FF8C42', '&:hover': { bgcolor: '#FF6B35' } }}
            >
              {processing ? 'Processing...' : 'Process Notifications'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Notifications Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <NotificationsIcon sx={{ color: '#1976d2', mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Pending Notifications ({notifications.length})
            </Typography>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      indeterminate={selectedNotifications.length > 0 && selectedNotifications.length < notifications.length}
                      checked={notifications.length > 0 && selectedNotifications.length === notifications.length}
                      onChange={handleSelectAll}
                    />
                  </TableCell>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Recipient</strong></TableCell>
                  <TableCell><strong>Subject</strong></TableCell>
                  <TableCell><strong>Related To</strong></TableCell>
                  <TableCell><strong>Priority</strong></TableCell>
                  <TableCell><strong>Created</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {notifications.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <CheckCircleIcon sx={{ fontSize: 48, color: '#388e3c', mb: 1 }} />
                        <Typography color="textSecondary">No pending notifications</Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  notifications.map((notification) => (
                    <TableRow key={notification.id || notification.notification_id} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedNotifications.includes(notification.id || notification.notification_id)}
                          onChange={() => handleSelectNotification(notification.id || notification.notification_id)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getTypeIcon(notification.type)}
                          label={notification.type || 'General'}
                          size="small"
                          sx={{
                            bgcolor: getTypeColor(notification.type),
                            color: 'white',
                            '& .MuiChip-icon': { color: 'white' },
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {notification.recipient || notification.recipient_email || notification.to || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          sx={{
                            maxWidth: 300,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {notification.subject || notification.title || notification.message || 'No subject'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {notification.ticket_number || notification.ticket_id || notification.related_to || 'N/A'}
                      </TableCell>
                      <TableCell>
                        {notification.priority && (
                          <Chip
                            label={notification.priority}
                            size="small"
                            sx={{
                              bgcolor: getPriorityColor(notification.priority),
                              color: 'white',
                            }}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {formatDate(notification.created_at || notification.created)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SendIcon sx={{ mr: 1 }} />
            Confirm Send Notifications
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography>
            {selectedNotifications.length > 0
              ? `Are you sure you want to send ${selectedNotifications.length} selected notification(s)?`
              : `Are you sure you want to send all ${notifications.length} pending notification(s)?`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)} disabled={processing}>
            Cancel
          </Button>
          <Button
            onClick={handleProcessNotifications}
            variant="contained"
            disabled={processing}
            sx={{ bgcolor: '#FF8C42', '&:hover': { bgcolor: '#FF6B35' } }}
          >
            {processing ? 'Sending...' : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Notifications;
