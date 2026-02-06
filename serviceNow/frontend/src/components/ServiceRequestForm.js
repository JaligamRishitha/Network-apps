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
  Chip
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Favorite as FavoriteIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const ServiceRequestForm = ({ 
  title, 
  description, 
  formType = 'general',
  onSubmit 
}) => {
  const navigate = useNavigate();
  const { API_URL } = useAuth();

  const [formData, setFormData] = useState({
    category: '',
    subcategory: '',
    application: '',
    shortDescription: '',
    detailedDescription: '',
    contactNumber: '',
    preferredContact: 'email',
    urgency: 'medium',
    attachments: []
  });

  const [errors, setErrors] = useState({});

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.shortDescription.trim()) {
      newErrors.shortDescription = 'Short description is required';
    }
    
    if (!formData.detailedDescription.trim()) {
      newErrors.detailedDescription = 'Please describe your issue';
    }
    
    if (formType === 'problem' && !formData.contactNumber.trim()) {
      newErrors.contactNumber = 'Contact number is required for problem reports';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      if (onSubmit) {
        onSubmit(formData);
      } else {
        // Default submission - create ticket
        createTicket(formData);
      }
    }
  };

  const createTicket = async (data) => {
    try {
      const token = localStorage.getItem('token');
      const ticketData = {
        title: data.shortDescription,
        description: data.detailedDescription,
        ticket_type: getTicketType(),
        category: data.category,
        subcategory: data.subcategory,
        contact_number: data.contactNumber,
        preferred_contact: data.preferredContact,
        urgency: data.urgency,
        priority: data.urgency === 'high' ? 'high' : data.urgency === 'low' ? 'low' : 'medium'
      };

      const response = await fetch(`${API_URL}/tickets/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(ticketData)
      });

      if (response.ok) {
        const ticket = await response.json();
        alert(`Ticket ${ticket.ticket_number} created successfully! You can track its progress in Tickets.`);
        navigate('/');
      } else {
        throw new Error('Failed to create ticket');
      }
    } catch (error) {
      console.error('Error creating ticket:', error);
      alert('Error creating ticket. Please try again.');
    }
  };

  const getTicketType = () => {
    switch (formType) {
      case 'password':
      case 'problem':
        return 'incident';
      case 'business':
        return 'service_request';
      default:
        return 'service_request';
    }
  };

  const getFormConfig = () => {
    switch (formType) {
      case 'password':
        return {
          categories: ['Account Access', 'Password Issues', 'System Access'],
          subcategories: ['Password Reset', 'Account Unlock', 'New Account'],
          showApplication: false,
          requiresContact: true
        };
      case 'problem':
        return {
          categories: ['Hardware', 'Software', 'Network', 'Email', 'Other'],
          subcategories: ['Desktop/Laptop', 'Printer', 'Application Error', 'System Slow'],
          showApplication: true,
          requiresContact: true
        };
      case 'business':
        return {
          categories: ['Application Support', 'Training', 'Access Request'],
          subcategories: ['CRM', 'ERP', 'Finance System', 'HR System'],
          showApplication: true,
          requiresContact: false
        };
      default:
        return {
          categories: ['General', 'IT Support', 'Access Request'],
          subcategories: ['Hardware', 'Software', 'Network'],
          showApplication: false,
          requiresContact: false
        };
    }
  };

  const config = getFormConfig();

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
          <Typography color="text.primary">{title}</Typography>
        </Breadcrumbs>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton 
            onClick={() => navigate('/')}
            sx={{ mr: 2, color: '#666' }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" sx={{ flexGrow: 1, color: '#333', fontWeight: 600 }}>
            {title}
          </Typography>
          <IconButton sx={{ color: '#FF8C42' }}>
            <FavoriteIcon />
          </IconButton>
        </Box>
        
        <Typography variant="body1" color="text.secondary">
          {description}
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ p: 3 }}>
        {/* Main Form */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            {formType === 'problem' && (
              <Alert severity="info" sx={{ mb: 3 }}>
                Thank you for contacting the service desk. Please describe the nature of your problem in the fields below. Upon receipt, the service desk will categorize and prioritize your problem at which time you will receive an automated email with the details of that update.
                <br /><br />
                <strong style={{ color: '#d32f2f' }}>
                  If it is a Major Incident Contact 02036602010 - Option 1.
                </strong>
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                {/* Category */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={formData.category}
                      label="Category"
                      onChange={(e) => handleInputChange('category', e.target.value)}
                    >
                      <MenuItem value="">-- None --</MenuItem>
                      {config.categories.map((cat) => (
                        <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Subcategory */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Subcategory</InputLabel>
                    <Select
                      value={formData.subcategory}
                      label="Subcategory"
                      onChange={(e) => handleInputChange('subcategory', e.target.value)}
                    >
                      <MenuItem value="">-- None --</MenuItem>
                      {config.subcategories.map((subcat) => (
                        <MenuItem key={subcat} value={subcat}>{subcat}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Application (conditional) */}
                {config.showApplication && (
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Application you are having problems with</InputLabel>
                      <Select
                        value={formData.application}
                        label="Application you are having problems with"
                        onChange={(e) => handleInputChange('application', e.target.value)}
                      >
                        <MenuItem value="">-- None --</MenuItem>
                        <MenuItem value="outlook">Microsoft Outlook</MenuItem>
                        <MenuItem value="teams">Microsoft Teams</MenuItem>
                        <MenuItem value="excel">Microsoft Excel</MenuItem>
                        <MenuItem value="chrome">Google Chrome</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                )}

                {/* Short Description */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="Short description"
                    value={formData.shortDescription}
                    onChange={(e) => handleInputChange('shortDescription', e.target.value)}
                    error={!!errors.shortDescription}
                    helperText={errors.shortDescription}
                    placeholder="Brief summary of your request"
                  />
                </Grid>

                {/* Detailed Description */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    multiline
                    rows={4}
                    label="Please describe your issue below"
                    value={formData.detailedDescription}
                    onChange={(e) => handleInputChange('detailedDescription', e.target.value)}
                    error={!!errors.detailedDescription}
                    helperText={errors.detailedDescription}
                    placeholder="Provide detailed information about your request or issue"
                  />
                </Grid>

                {/* Contact Information */}
                {config.requiresContact && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="h6" sx={{ mb: 2, color: '#333' }}>
                        Contact Information
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        required
                        label="Contact telephone number"
                        value={formData.contactNumber}
                        onChange={(e) => handleInputChange('contactNumber', e.target.value)}
                        error={!!errors.contactNumber}
                        helperText={errors.contactNumber}
                        placeholder="Your phone number"
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Please select your preferred means of contact</InputLabel>
                        <Select
                          value={formData.preferredContact}
                          label="Please select your preferred means of contact"
                          onChange={(e) => handleInputChange('preferredContact', e.target.value)}
                        >
                          <MenuItem value="email">Email</MenuItem>
                          <MenuItem value="phone">Phone</MenuItem>
                          <MenuItem value="teams">Microsoft Teams</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </>
                )}

                {/* File Attachments */}
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mb: 2, color: '#333' }}>
                    Attach a file (e.g. screenshot of the error)
                  </Typography>
                  <Box
                    sx={{
                      border: '2px dashed #ddd',
                      borderRadius: 2,
                      p: 4,
                      textAlign: 'center',
                      backgroundColor: '#fafafa',
                      '&:hover': {
                        borderColor: '#FF8C42',
                        backgroundColor: '#fff5f0'
                      }
                    }}
                  >
                    <CloudUploadIcon sx={{ fontSize: 48, color: '#999', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
                      Choose a file or drag it here.
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Copy and paste clipboard files here.
                    </Typography>
                  </Box>
                </Grid>

                {/* Submit Button */}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                    <Button
                      type="submit"
                      variant="contained"
                      size="large"
                      sx={{
                        backgroundColor: '#8B1538',
                        '&:hover': { backgroundColor: '#6B0F2A' },
                        px: 4
                      }}
                    >
                      Submit
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
              Required Information
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="Contact telephone number" size="small" color="error" />
              <Chip label="Please select your preferred means of contact" size="small" color="primary" />
              <Chip label="Please describe your availability" size="small" color="primary" />
              <Chip label="Host Name" size="small" color="primary" />
              <Chip label="Toughpad / Toughbook" size="small" color="primary" />
              <Chip label="Category | Subcategory" size="small" color="primary" />
              <Chip label="Short description" size="small" color="primary" />
              <Chip label="Please describe your issue below" size="small" color="error" />
            </Box>
          </Paper>

          {formType === 'problem' && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#8B1538' }}>
                Emergency Contact
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                For urgent issues outside business hours:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#d32f2f' }}>
                📞 02036602010 - Option 1
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default ServiceRequestForm;