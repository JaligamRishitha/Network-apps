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
  Avatar,
  AvatarGroup,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Group as GroupIcon,
  Search as SearchIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  Visibility as VisibilityIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const AssignmentGroups = () => {
  const { API_URL, token } = useAuth();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [workload, setWorkload] = useState(null);
  const [workloadLoading, setWorkloadLoading] = useState(false);
  const [workloadDialogOpen, setWorkloadDialogOpen] = useState(false);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/assignment-groups`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch assignment groups');
      }

      const data = await response.json();
      setGroups(Array.isArray(data) ? data : data.groups || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const fetchWorkload = async (groupId) => {
    setWorkloadLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/assignment-groups/${groupId}/workload`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch workload data');
      }

      const data = await response.json();
      setWorkload(data);
      setWorkloadDialogOpen(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setWorkloadLoading(false);
    }
  };

  const handleViewWorkload = (group) => {
    setSelectedGroup(group);
    fetchWorkload(group.id || group.group_id);
  };

  const handleCloseDialog = () => {
    setWorkloadDialogOpen(false);
    setSelectedGroup(null);
    setWorkload(null);
  };

  const getWorkloadColor = (percentage) => {
    if (percentage >= 90) return '#d32f2f';
    if (percentage >= 70) return '#f57c00';
    if (percentage >= 50) return '#fbc02d';
    return '#388e3c';
  };

  const getStatusColor = (status) => {
    const colors = {
      active: '#388e3c',
      inactive: '#757575',
      overloaded: '#d32f2f',
    };
    return colors[status?.toLowerCase()] || '#757575';
  };

  const filterGroups = (data) => {
    if (!searchTerm) return data;
    return data.filter(group =>
      (group.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (group.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (group.manager || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getTotalMembers = () => groups.reduce((sum, g) => sum + (g.member_count || g.members?.length || 0), 0);
  const getTotalTickets = () => groups.reduce((sum, g) => sum + (g.open_tickets || g.ticket_count || 0), 0);
  const getActiveGroups = () => groups.filter(g => g.status === 'active' || g.is_active).length;

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
        Assignment Groups
      </Typography>

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
                    Total Groups
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    {groups.length}
                  </Typography>
                </Box>
                <GroupIcon sx={{ fontSize: 40, color: '#1976d2', opacity: 0.7 }} />
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
                    Active Groups
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#388e3c' }}>
                    {getActiveGroups()}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: '#388e3c', opacity: 0.7 }} />
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
                    Total Members
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f57c00' }}>
                    {getTotalMembers()}
                  </Typography>
                </Box>
                <PersonIcon sx={{ fontSize: 40, color: '#f57c00', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fce4ec', borderLeft: '4px solid #c2185b' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Open Tickets
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#c2185b' }}>
                    {getTotalTickets()}
                  </Typography>
                </Box>
                <AssignmentIcon sx={{ fontSize: 40, color: '#c2185b', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <TextField
        fullWidth
        placeholder="Search by group name, description, or manager..."
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

      {/* Groups Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <GroupIcon sx={{ color: '#1976d2', mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              All Assignment Groups ({filterGroups(groups).length})
            </Typography>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell><strong>Group Name</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Manager</strong></TableCell>
                  <TableCell align="center"><strong>Members</strong></TableCell>
                  <TableCell align="center"><strong>Open Tickets</strong></TableCell>
                  <TableCell align="center"><strong>Status</strong></TableCell>
                  <TableCell align="center"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filterGroups(groups).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="textSecondary">No assignment groups found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filterGroups(groups).map((group) => (
                    <TableRow key={group.id || group.group_id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ bgcolor: '#1976d2', mr: 1, width: 32, height: 32 }}>
                            <GroupIcon fontSize="small" />
                          </Avatar>
                          <Typography sx={{ fontWeight: 500 }}>{group.name}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography
                          sx={{
                            maxWidth: 250,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {group.description || 'No description'}
                        </Typography>
                      </TableCell>
                      <TableCell>{group.manager || group.manager_name || 'Unassigned'}</TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {group.members && group.members.length > 0 ? (
                            <Tooltip title={group.members.map(m => m.name || m).join(', ')}>
                              <AvatarGroup max={3} sx={{ '& .MuiAvatar-root': { width: 28, height: 28, fontSize: 12 } }}>
                                {group.members.map((member, idx) => (
                                  <Avatar key={idx} sx={{ bgcolor: '#FF8C42' }}>
                                    {(member.name || member || '?').charAt(0).toUpperCase()}
                                  </Avatar>
                                ))}
                              </AvatarGroup>
                            </Tooltip>
                          ) : (
                            <Typography>{group.member_count || 0}</Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={group.open_tickets || group.ticket_count || 0}
                          size="small"
                          color={(group.open_tickets || group.ticket_count || 0) > 10 ? 'error' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={group.status || (group.is_active ? 'Active' : 'Inactive')}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(group.status || (group.is_active ? 'active' : 'inactive')),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Workload">
                          <IconButton
                            size="small"
                            onClick={() => handleViewWorkload(group)}
                            disabled={workloadLoading}
                          >
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

      {/* Workload Dialog */}
      <Dialog open={workloadDialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <GroupIcon sx={{ mr: 1 }} />
            {selectedGroup?.name} - Agent Workload
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {workloadLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : workload ? (
            <Box>
              {/* Group Summary */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">Total Agents</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {workload.total_agents || workload.agents?.length || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">Total Tickets</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {workload.total_tickets || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">Avg per Agent</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {workload.avg_tickets_per_agent?.toFixed(1) || 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Agent Workload Table */}
              {workload.agents && workload.agents.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell><strong>Agent</strong></TableCell>
                        <TableCell align="center"><strong>Assigned Tickets</strong></TableCell>
                        <TableCell><strong>Workload</strong></TableCell>
                        <TableCell align="center"><strong>Status</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {workload.agents.map((agent, idx) => {
                        const workloadPercent = agent.workload_percentage ||
                          (agent.assigned_tickets / (workload.max_capacity || 10)) * 100;
                        return (
                          <TableRow key={agent.id || idx} hover>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Avatar sx={{ bgcolor: '#FF8C42', mr: 1, width: 32, height: 32 }}>
                                  {(agent.name || 'A').charAt(0).toUpperCase()}
                                </Avatar>
                                <Box>
                                  <Typography sx={{ fontWeight: 500 }}>{agent.name || agent.email}</Typography>
                                  <Typography variant="caption" color="textSecondary">
                                    {agent.email || agent.role || ''}
                                  </Typography>
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Typography sx={{ fontWeight: 600 }}>
                                {agent.assigned_tickets || agent.ticket_count || 0}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Box sx={{ flexGrow: 1, mr: 1 }}>
                                  <LinearProgress
                                    variant="determinate"
                                    value={Math.min(workloadPercent, 100)}
                                    sx={{
                                      height: 8,
                                      borderRadius: 4,
                                      bgcolor: '#e0e0e0',
                                      '& .MuiLinearProgress-bar': {
                                        bgcolor: getWorkloadColor(workloadPercent),
                                        borderRadius: 4,
                                      },
                                    }}
                                  />
                                </Box>
                                <Typography variant="body2" sx={{ minWidth: 40 }}>
                                  {workloadPercent.toFixed(0)}%
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={agent.status || (workloadPercent >= 90 ? 'Overloaded' : 'Available')}
                                size="small"
                                sx={{
                                  bgcolor: getWorkloadColor(workloadPercent),
                                  color: 'white',
                                }}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="textSecondary" align="center">
                  No agent workload data available
                </Typography>
              )}
            </Box>
          ) : (
            <Typography color="textSecondary">No workload data available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssignmentGroups;
