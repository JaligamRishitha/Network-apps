import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Breadcrumbs,
  Link,
  Chip
} from '@mui/material';
import {
  Computer as ComputerIcon,
  PhoneAndroid as PhoneIcon,
  Security as SecurityIcon,
  Cloud as CloudIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Print as PrintIcon,
  Support as SupportIcon,
  Build as BuildIcon,
  VpnKey as AccessIcon,
  Email as EmailIcon,
  Backup as BackupIcon
} from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const ITServices = () => {
  const [services, setServices] = useState([]);
  const { API_URL } = useAuth();

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API_URL}/service-catalog/`);
      setServices(response.data);
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  const itServiceCategories = [
    {
      title: "Hardware Requests",
      description: "Request new computers, laptops, monitors, and other hardware equipment.",
      icon: <ComputerIcon />,
      color: "#17A2B8",
      items: ["New Laptop Request", "Desktop Computer", "Monitor Request", "Printer Request", "Mobile Device"]
    },
    {
      title: "Software & Applications",
      description: "Install software, request licenses, and get application support.",
      icon: <BuildIcon />,
      color: "#28A745",
      items: ["Software Installation", "License Request", "Application Support", "Software Update"]
    },
    {
      title: "Access & Security",
      description: "Request system access, password resets, and security-related services.",
      icon: <AccessIcon />,
      color: "#DC3545",
      items: ["Access Request", "Password Reset", "VPN Access", "Security Token", "Account Unlock"]
    },
    {
      title: "Network & Connectivity",
      description: "Network issues, WiFi problems, and connectivity requests.",
      icon: <NetworkIcon />,
      color: "#FFC107",
      items: ["Network Issue", "WiFi Access", "Internet Problem", "VPN Setup", "Network Drive Access"]
    },
    {
      title: "Email & Communication",
      description: "Email setup, distribution lists, and communication tools.",
      icon: <EmailIcon />,
      color: "#6F42C1",
      items: ["Email Setup", "Distribution List", "Teams Setup", "Phone Configuration"]
    },
    {
      title: "Cloud Services",
      description: "Cloud storage, backup services, and cloud application access.",
      icon: <CloudIcon />,
      color: "#20C997",
      items: ["Cloud Storage", "Backup Request", "OneDrive Setup", "SharePoint Access"]
    },
    {
      title: "Technical Support",
      description: "General IT support, troubleshooting, and technical assistance.",
      icon: <SupportIcon />,
      color: "#FD7E14",
      items: ["General Support", "Troubleshooting", "Remote Assistance", "Training Request"]
    },
    {
      title: "Printing Services",
      description: "Printer setup, print queue issues, and printing support.",
      icon: <PrintIcon />,
      color: "#6C757D",
      items: ["Printer Setup", "Print Queue Issue", "Scanner Setup", "Copier Request"]
    }
  ];

  const handleServiceRequest = (categoryTitle, serviceItem) => {
    // In a real application, this would open a service request form
    alert(`Requesting: ${serviceItem} from ${categoryTitle}`);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ p: 3, backgroundColor: '#f8f9fa', borderBottom: '1px solid #dee2e6' }}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link color="inherit" href="/" onClick={(e) => { e.preventDefault(); }}>
            Home
          </Link>
          <Typography color="text.primary">IT Services</Typography>
        </Breadcrumbs>
        
        <Typography variant="h4" sx={{ mb: 1, color: '#17A2B8', fontWeight: 600 }}>
          IT Services
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Contact IT for requests, equipment, and issues. Browse our comprehensive catalog of IT services and submit requests for hardware, software, access, and technical support.
        </Typography>
      </Box>

      {/* Service Categories */}
      <Box sx={{ p: 4, backgroundColor: 'white' }}>
        <Grid container spacing={4}>
          {itServiceCategories.map((category, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                  border: '1px solid #e0e0e0',
                  borderTop: `4px solid ${category.color}`
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        backgroundColor: category.color,
                        color: 'white',
                        borderRadius: '8px',
                        p: 1.5,
                        mr: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {category.icon}
                    </Box>
                    <Typography variant="h6" sx={{ color: category.color, fontWeight: 600 }}>
                      {category.title}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    {category.description}
                  </Typography>

                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: '#333' }}>
                      Available Services:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {category.items.map((item, itemIndex) => (
                        <Chip
                          key={itemIndex}
                          label={item}
                          size="small"
                          clickable
                          onClick={() => handleServiceRequest(category.title, item)}
                          sx={{
                            backgroundColor: `${category.color}15`,
                            color: category.color,
                            border: `1px solid ${category.color}30`,
                            '&:hover': {
                              backgroundColor: `${category.color}25`,
                            }
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Popular Services */}
      <Box sx={{ p: 4, backgroundColor: '#f8f9fa' }}>
        <Typography variant="h5" sx={{ mb: 3, color: '#333', fontWeight: 600 }}>
          Most Requested Services
        </Typography>
        <Grid container spacing={2}>
          {[
            { name: "New Laptop Request", category: "Hardware", color: "#17A2B8" },
            { name: "Software Installation", category: "Software", color: "#28A745" },
            { name: "Access Request", category: "Security", color: "#DC3545" },
            { name: "Password Reset", category: "Security", color: "#DC3545" },
            { name: "Email Setup", category: "Communication", color: "#6F42C1" },
            { name: "VPN Access", category: "Network", color: "#FFC107" }
          ].map((service, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  },
                  border: '1px solid #e0e0e0'
                }}
                onClick={() => handleServiceRequest(service.category, service.name)}
              >
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, color: service.color }}>
                    {service.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {service.category}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Contact Information */}
      <Box sx={{ p: 4, backgroundColor: 'white', borderTop: '1px solid #dee2e6' }}>
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" sx={{ mb: 2, color: '#17A2B8', fontWeight: 600 }}>
              Need Help?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              If you can't find what you're looking for, contact our IT support team:
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              📧 Email: it-support@company.com
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              📞 Phone: +1 (555) 123-4567
            </Typography>
            <Typography variant="body2">
              🕒 Hours: Monday - Friday, 8:00 AM - 6:00 PM
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" sx={{ mb: 2, color: '#17A2B8', fontWeight: 600 }}>
              Emergency Support
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              For critical IT issues outside business hours:
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              📞 Emergency Line: +1 (555) 999-9999
            </Typography>
            <Typography variant="body2">
              Available 24/7 for critical system outages
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default ITServices;