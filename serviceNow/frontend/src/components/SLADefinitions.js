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
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  AccessTime as AccessTimeIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const SLADefinitions = () => {
  const { API_URL, token } = useAuth();
  const [definitions, setDefinitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDefinition, setSelectedDefinition] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const fetchDefinitions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/sla/definitions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch SLA definitions');
      }

      const data = await response.json();
      setDefinitions(Array.isArray(data) ? data : data.definitions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchDefinitions();
  }, [fetchDefinitions]);

  const handleViewDetails = (definition) => {
    setSelectedDefinition(definition);
    setDetailDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDetailDialogOpen(false);
    setSelectedDefinition(null);
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

  const getStatusColor = (status) => {
    const colors = {
      active: '#388e3c',
      inactive: '#757575',
      draft: '#1976d2',
    };
    return colors[status?.toLowerCase()] || '#757575';
  };

  const formatDuration = (minutes) => {
    if (!minutes && minutes !== 0) return 'N/A';
    if (minutes < 60) return `${minutes} minutes`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours < 24) return mins > 0 ? `${hours}h ${mins}m` : `${hours} hours`;
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days} days`;
  };

  const filterDefinitions = (data) => {
    if (!searchTerm) return data;
    return data.filter(def =>
      (def.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (def.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (def.priority || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (def.category || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getActiveCount = () => definitions.filter(d => d.status === 'active' || d.is_active).length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: '#2c3e50' }}>
          SLA Definitions
        </Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={fetchDefinitions} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
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
                    Total Definitions
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    {definitions.length}
                  </Typography>
                </Box>
                <ScheduleIcon sx={{ fontSize: 40, color: '#1976d2', opacity: 0.7 }} />
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
                    Active Definitions
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#388e3c' }}>
                    {getActiveCount()}
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, color: '#388e3c', opacity: 0.7 }} />
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
                    Response SLAs
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f57c00' }}>
                    {definitions.filter(d => d.response_time || d.response_target).length}
                  </Typography>
                </Box>
                <AccessTimeIcon sx={{ fontSize: 40, color: '#f57c00', opacity: 0.7 }} />
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
                    Resolution SLAs
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#7b1fa2' }}>
                    {definitions.filter(d => d.resolution_time || d.resolution_target).length}
                  </Typography>
                </Box>
                <AssignmentIcon sx={{ fontSize: 40, color: '#7b1fa2', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <TextField
        fullWidth
        placeholder="Search by name, description, priority, or category..."
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

      {/* SLA Definitions Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <ScheduleIcon sx={{ color: '#1976d2', mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              SLA Rules ({filterDefinitions(definitions).length})
            </Typography>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell><strong>Name</strong></TableCell>
                  <TableCell><strong>Category</strong></TableCell>
                  <TableCell><strong>Priority</strong></TableCell>
                  <TableCell><strong>Response Time</strong></TableCell>
                  <TableCell><strong>Resolution Time</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell align="center"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filterDefinitions(definitions).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="textSecondary">No SLA definitions found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filterDefinitions(definitions).map((definition) => (
                    <TableRow key={definition.id || definition.sla_id} hover>
                      <TableCell>
                        <Typography sx={{ fontWeight: 500 }}>{definition.name}</Typography>
                        {definition.description && (
                          <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                            {definition.description.length > 50
                              ? `${definition.description.substring(0, 50)}...`
                              : definition.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={definition.category || definition.ticket_type || 'General'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {definition.priority ? (
                          <Chip
                            label={definition.priority}
                            size="small"
                            sx={{
                              bgcolor: getPriorityColor(definition.priority),
                              color: 'white',
                            }}
                          />
                        ) : (
                          <Typography variant="body2" color="textSecondary">All</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDuration(definition.response_time || definition.response_target_minutes)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDuration(definition.resolution_time || definition.resolution_target_minutes)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={definition.status || (definition.is_active ? 'Active' : 'Inactive')}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(definition.status || (definition.is_active ? 'active' : 'inactive')),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton size="small" onClick={() => handleViewDetails(definition)}>
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ScheduleIcon sx={{ mr: 1 }} />
            SLA Definition Details
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedDefinition && (
            <Box>
              <Typography variant="subtitle2" color="textSecondary">Name</Typography>
              <Typography sx={{ mb: 2, fontWeight: 500 }}>{selectedDefinition.name}</Typography>

              <Typography variant="subtitle2" color="textSecondary">Description</Typography>
              <Typography sx={{ mb: 2 }}>{selectedDefinition.description || 'No description'}</Typography>

              <Divider sx={{ my: 2 }} />

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Category</Typography>
                  <Chip
                    label={selectedDefinition.category || selectedDefinition.ticket_type || 'General'}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 0.5 }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Priority</Typography>
                  {selectedDefinition.priority ? (
                    <Chip
                      label={selectedDefinition.priority}
                      size="small"
                      sx={{
                        mt: 0.5,
                        bgcolor: getPriorityColor(selectedDefinition.priority),
                        color: 'white',
                      }}
                    />
                  ) : (
                    <Typography sx={{ mt: 0.5 }}>All priorities</Typography>
                  )}
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>SLA Targets</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card variant="outlined" sx={{ p: 2, textAlign: 'center', bgcolor: '#fff3e0' }}>
                    <AccessTimeIcon sx={{ color: '#f57c00', mb: 1 }} />
                    <Typography variant="body2" color="textSecondary">Response Time</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#f57c00' }}>
                      {formatDuration(selectedDefinition.response_time || selectedDefinition.response_target_minutes)}
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined" sx={{ p: 2, textAlign: 'center', bgcolor: '#f3e5f5' }}>
                    <AssignmentIcon sx={{ color: '#7b1fa2', mb: 1 }} />
                    <Typography variant="body2" color="textSecondary">Resolution Time</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#7b1fa2' }}>
                      {formatDuration(selectedDefinition.resolution_time || selectedDefinition.resolution_target_minutes)}
                    </Typography>
                  </Card>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Status</Typography>
                  <Chip
                    label={selectedDefinition.status || (selectedDefinition.is_active ? 'Active' : 'Inactive')}
                    size="small"
                    sx={{
                      mt: 0.5,
                      bgcolor: getStatusColor(selectedDefinition.status || (selectedDefinition.is_active ? 'active' : 'inactive')),
                      color: 'white',
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Warning Threshold</Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    {selectedDefinition.warning_threshold
                      ? `${selectedDefinition.warning_threshold}%`
                      : selectedDefinition.warning_minutes
                        ? formatDuration(selectedDefinition.warning_minutes)
                        : '75% of target'}
                  </Typography>
                </Grid>
              </Grid>

              {(selectedDefinition.conditions || selectedDefinition.applies_to) && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="textSecondary">Applies To</Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    {selectedDefinition.applies_to || selectedDefinition.conditions || 'All matching tickets'}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SLADefinitions;
