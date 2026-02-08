import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Breadcrumbs,
  Link,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Divider,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Favorite as FavoriteIcon,
  LockReset as LockResetIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Assignment as TicketIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

// ServiceNow API URL for ticket creation (NOT MuleSoft)
const SERVICENOW_URL = process.env.REACT_APP_SERVICENOW_URL || 'http://207.180.217.117:4780';

const PasswordResetForm = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    reason: '',
    contactNumber: '',
    preferredContact: 'phone',
    urgency: 'medium'
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showResultDialog, setShowResultDialog] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.reason.trim()) {
      newErrors.reason = 'Please provide a reason for the password reset';
    }

    if (!formData.contactNumber.trim()) {
      newErrors.contactNumber = 'Contact number is required for identity verification';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Create a ticket in ServiceNow -  Admin will reset password manually
      const response = await fetch(`${SERVICENOW_URL}/api/tickets/auto-create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_type: 'password_reset',
          source_system: 'servicenow_self_service',
          title: `Password Reset Request: ${formData.username}`,
          description: `Password Reset Request

Username: ${formData.username}
Requested By: ${user?.full_name || 'Self-service User'}
Email: ${formData.email || 'Not provided'}
Contact Number: ${formData.contactNumber}
Preferred Contact: ${formData.preferredContact}

Reason for Reset:
${formData.reason}`,
          category: 'User Account',
          subcategory: 'Password Reset',
          priority: formData.urgency,
          assignment_group: 'User Management',
          ticket_type: 'incident',
          sla_hours: formData.urgency === 'high' ? 4 : formData.urgency === 'critical' ? 1 : 24,
          affected_user: formData.username,
          requires_approval: false,
          auto_assign: true,
          metadata: {
            sap_username: formData.username,
            requester_email: formData.email,
            contact_number: formData.contactNumber,
            preferred_contact: formData.preferredContact,
            request_type: 'password_reset'
          }
        })
      });

      const data = await response.json();

      if (response.ok) {
        setResult({
          success: true,
          ticket_number: data.ticket_number,
          ticket_id: data.ticket_id,
          assignment_group: data.assignment_group,
          sla_response_due: data.sla_response_due
        });
      } else {
        setResult({
          success: false,
          error: data.detail || 'Failed to create ticket'
        });
      }

      setShowResultDialog(true);
    } catch (error) {
      console.error('Ticket creation error:', error);
      setResult({
        success: false,
        error: 'Failed to connect to ServiceNow. Please try again or call IT Support.'
      });
      setShowResultDialog(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setShowResultDialog(false);
    if (result?.success) {
      navigate('/');
    }
  };

  const flowSteps = [
    'Submit Request',
    'Ticket Created',
    'Validates Details',
    'Password Reset',
    'User Notified'
  ];

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
          <Typography color="text.primary">Password Reset Request</Typography>
        </Breadcrumbs>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/')} sx={{ mr: 2, color: '#666' }}>
            <ArrowBackIcon />
          </IconButton>
          <LockResetIcon sx={{ mr: 2, fontSize: 32, color: '#8B1538' }} />
          <Typography variant="h4" sx={{ flexGrow: 1, color: '#333', fontWeight: 600 }}>
            Password Reset Request
          </Typography>
          <IconButton sx={{ color: '#FF8C42' }}>
            <FavoriteIcon />
          </IconButton>
        </Box>

        <Typography variant="body1" color="text.secondary">
          Submit a request to reset your account password. A ticket will be created and will verify your identity and reset your password.
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ p: 3 }}>
        {/* Main Form */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>How it works:</strong>
              <ol style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                <li>Submit this form with your username and contact details</li>
                <li>A ticket is created</li>
                <li>After verification, your password is generated automatically</li>
                <li>You will receive a temporary password via your email</li>
              </ol>
            </Alert>

            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                {/* Username */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="Username"
                    value={formData.username}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                    error={!!errors.username}
                    helperText={errors.username || 'Enter your username'}
                    placeholder="e.g., jsmith"
                  />
                </Grid>

                {/* Email */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Email Address"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    helperText="Your corporate email for ticket updates"
                    placeholder="your.email@company.com"
                  />
                </Grid>

                {/* Contact Number */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    required
                    label="Contact Telephone Number"
                    value={formData.contactNumber}
                    onChange={(e) => handleInputChange('contactNumber', e.target.value)}
                    error={!!errors.contactNumber}
                    helperText={errors.contactNumber || 'Required for identity verification'}
                    placeholder="Your phone number"
                  />
                </Grid>

                {/* Reason */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    multiline
                    rows={3}
                    label="Reason for Password Reset"
                    value={formData.reason}
                    onChange={(e) => handleInputChange('reason', e.target.value)}
                    error={!!errors.reason}
                    helperText={errors.reason || 'Please explain why you need a password reset'}
                    placeholder="e.g., Forgot password, Account locked..."
                  />
                </Grid>

                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="h6" sx={{ mt: 2, mb: 1, color: '#333' }}>
                    Request Options
                  </Typography>
                </Grid>

                {/* Urgency */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Urgency</InputLabel>
                    <Select
                      value={formData.urgency}
                      label="Urgency"
                      onChange={(e) => handleInputChange('urgency', e.target.value)}
                    >
                      <MenuItem value="low">Low - Can wait 48 hours</MenuItem>
                      <MenuItem value="medium">Medium - Need within 24 hours</MenuItem>
                      <MenuItem value="high">High - Need within 4 hours</MenuItem>
                      <MenuItem value="critical">Critical - Blocking business</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {/* Preferred Contact */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Preferred Contact Method</InputLabel>
                    <Select
                      value={formData.preferredContact}
                      label="Preferred Contact Method"
                      onChange={(e) => handleInputChange('preferredContact', e.target.value)}
                    >
                      <MenuItem value="phone">Email</MenuItem>
                      <MenuItem value="teams">Phone Call</MenuItem>
                      
                    </Select>
                  </FormControl>
                </Grid>

                {/* Submit Button */}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                    <Button
                      type="submit"
                      variant="contained"
                      size="large"
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <TicketIcon />}
                      sx={{
                        backgroundColor: '#8B1538',
                        '&:hover': { backgroundColor: '#6B0F2A' },
                        px: 4
                      }}
                    >
                      {loading ? 'Submitting...' : 'Submit Password Reset Request'}
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      onClick={() => navigate('/')}
                      sx={{ px: 4 }}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Grid>

        {/* Right Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#8B1538' }}>
              Request Flow
            </Typography>
            <Stepper activeStep={0} orientation="vertical">
              {flowSteps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#8B1538' }}>
              SLA Information
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <ScheduleIcon sx={{ mr: 1, color: '#666' }} />
              <Typography variant="body2"><strong>Critical:</strong> 1 hour</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <ScheduleIcon sx={{ mr: 1, color: '#666' }} />
              <Typography variant="body2"><strong>High:</strong> 4 hours</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <ScheduleIcon sx={{ mr: 1, color: '#666' }} />
              <Typography variant="body2"><strong>Medium:</strong> 24 hours</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ScheduleIcon sx={{ mr: 1, color: '#666' }} />
              <Typography variant="body2"><strong>Low:</strong> 48 hours</Typography>
            </Box>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#8B1538' }}>
              Need Urgent Help?
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              For critical issues blocking business:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#d32f2f' }}>
              Call IT Support: 02036602010 - Option 1
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Result Dialog */}
      <Dialog open={showResultDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{
          backgroundColor: result?.success ? '#e8f5e9' : '#ffebee',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          {result?.success ? (
            <CheckCircleIcon sx={{ color: 'green' }} />
          ) : (
            <ErrorIcon sx={{ color: 'red' }} />
          )}
          {result?.success ? 'Request Submitted Successfully' : 'Request Failed'}
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {result?.success ? (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                Your password reset request has been submitted.
              </Alert>

              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Ticket Number:
                </Typography>
                <Chip
                  icon={<TicketIcon />}
                  label={result.ticket_number}
                  color="primary"
                  size="large"
                  sx={{ fontSize: '1.1rem', py: 2 }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Assigned To: {result.assignment_group || 'User Management'}
                </Typography>
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                <strong>What happens next:</strong>
                <ol style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                  <li>Your request will be reviewed</li>
                  <li>Verifies your identity</li>
                  <li>After verification, password will be reset</li>
                  <li>You'll receive the temporary password</li>
                </ol>
              </Alert>

            </Box>
          ) : (
            <Box>
              <Alert severity="error" sx={{ mb: 2 }}>
                {result?.error || 'An error occurred'}
              </Alert>
              <Typography variant="body2">
                Please try again or contact IT Support at 02036602010.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} variant="contained">
            {result?.success ? 'Done' : 'Close'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PasswordResetForm;
