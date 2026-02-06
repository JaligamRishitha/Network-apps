import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent,
  Paper,
  IconButton
} from '@mui/material';
import {
  Search as SearchIcon,
  ShoppingCart as ShoppingCartIcon,
  ReportProblem as ReportIcon,
  BugReport as BugReportIcon,
  MenuBook as KnowledgeIcon,
  VpnKey as PasswordIcon,
  Business as BusinessIcon,
  Computer as ITIcon,
  Gavel as LegalIcon,
  Business as FacilitiesIcon,
  ShoppingBag as ProcurementIcon,
  Group as GroupIcon,
  Assignment as MenuBook
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Homepage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  const quickActions = [
    {
      title: "Do you want something?",
      description: "Browse the catalog for services and items you need.",
      icon: <ShoppingCartIcon />,
      color: "#FF8C42",
      action: () => navigate('/service-catalog')
    },
    {
      title: "Got a problem?",
      description: "Contact support to report a problem.",
      icon: <ReportIcon />,
      color: "#8B1538",
      action: () => navigate('/problem-report')
    },
    {
      title: "Report a RTU/Interrupt Fault",
      description: "Contact support to report a problem.",
      icon: <BugReportIcon />,
      color: "#FF6B35",
      action: () => navigate('/incidents')
    },
    {
      title: "Knowledge Base",
      description: "Browse and search for articles that could solve your issue.",
      icon: <KnowledgeIcon />,
      color: "#F7931E",
      action: () => navigate('/knowledge-base')
    },
    {
      title: "Need a password reset?",
      description: "Click here to access the password portal. Click here for info on Password Mgr",
      icon: <PasswordIcon />,
      color: "#8B1538",
      action: () => navigate('/password-reset')
    },
    {
      title: "Need help with a business application?",
      description: "Click here to access Business Helpdesk.",
      icon: <BusinessIcon />,
      color: "#FF8C42",
      action: () => navigate('/business-app-help')
    }
  ];

  const serviceCategories = [
    {
      title: "My Activities",
      description: "Manage and consolidate your daily activities.",
      icon: <MenuBook />,
      color: "#FF8C42",
      action: () => navigate('/dashboard')
    },
    {
      title: "IT Services",
      description: "Contact IT for requests, equipment, and issues.",
      icon: <ITIcon />,
      color: "#8B1538",
      action: () => navigate('/it-services')
    },
    {
      title: "Legal Matters",
      description: "Contact Legal Matters for advice and guidance.",
      icon: <LegalIcon />,
      color: "#FF6B35",
      action: () => {}
    },
    {
      title: "Facilities",
      description: "Contact Facilities Team to request services regarding any enquiry.",
      icon: <FacilitiesIcon />,
      color: "#F7931E",
      action: () => {}
    },
    {
      title: "Our Procurement",
      description: "Contact Procurement and Commercial to log an enquiry.",
      icon: <ProcurementIcon />,
      color: "#8B1538",
      action: () => {}
    }
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #FF8C42 0%, #FF6B35 50%, #F7931E 100%)',
          minHeight: '300px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: '-50%',
            right: '-20%',
            width: '600px',
            height: '600px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.1)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: '-30%',
            right: '-10%',
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.05)',
          }
        }}
      >
        <Typography variant="h2" component="h1" sx={{ mb: 2, fontWeight: 300, textAlign: 'center' }}>
          Welcome {user?.full_name || 'User'}
        </Typography>
        <Typography variant="h5" sx={{ mb: 4, fontWeight: 300, textAlign: 'center' }}>
          How can we help you today?
        </Typography>
        <TextField
          variant="outlined"
          placeholder="Search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{
            width: '400px',
            backgroundColor: 'white',
            borderRadius: 1,
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                border: 'none',
              },
            },
          }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton>
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Announcements */}
      <Box sx={{ position: 'absolute', top: 140, right: 20, zIndex: 10 }}>
        <Paper
          elevation={3}
          sx={{
            p: 2,
            backgroundColor: 'white',
            borderRadius: 2,
            minWidth: 200,
            border: '2px solid #8B1538'
          }}
        >
          <Typography variant="h6" sx={{ color: '#8B1538', mb: 1, display: 'flex', alignItems: 'center' }}>
            📢 Announcements
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No information available
          </Typography>
        </Paper>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ p: 4, backgroundColor: '#f5f5f5' }}>
        <Grid container spacing={3}>
          {quickActions.map((action, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                  border: '1px solid #e0e0e0',
                  minHeight: 120,
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onClick={action.action}
              >
                <CardContent sx={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  p: 3,
                  flexGrow: 1,
                  minHeight: 88
                }}>
                  <Box
                    sx={{
                      backgroundColor: action.color,
                      color: 'white',
                      borderRadius: '50%',
                      p: 1.5,
                      mr: 2,
                      minWidth: 48,
                      minHeight: 48,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {action.icon}
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ color: action.color, mb: 1, fontWeight: 600 }}>
                      {action.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {action.description}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Service Categories */}
      <Box sx={{ p: 4, backgroundColor: 'white' }}>
        <Typography variant="h4" sx={{ mb: 1, textAlign: 'center', color: '#333' }}>
          Service Management
        </Typography>
        <Typography variant="body1" sx={{ mb: 4, textAlign: 'center', color: '#666' }}>
          Welcome to ServiceNow Service Management, providing each department its own support area, knowledge base, and user-facing service catalog.
        </Typography>
        
        <Grid container spacing={4} justifyContent="center">
          {serviceCategories.map((category, index) => (
            <Grid item xs={12} sm={6} md={4} lg={2.4} key={index}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                  textAlign: 'center',
                  minHeight: 200,
                  display: 'flex',
                  flexDirection: 'column',
                  border: '1px solid #e0e0e0'
                }}
                onClick={category.action}
              >
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Box
                    sx={{
                      backgroundColor: category.color,
                      color: 'white',
                      borderRadius: '50%',
                      p: 2,
                      mx: 'auto',
                      mb: 2,
                      width: 64,
                      height: 64,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {category.icon}
                  </Box>
                  <Typography variant="h6" sx={{ color: category.color, mb: 1, fontWeight: 600 }}>
                    {category.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {category.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center', borderTop: '1px solid #e0e0e0' }}>
        <Typography variant="body2" color="text.secondary">
          © 2024 ServiceNow. All rights reserved. | Terms of Use | Privacy Policy | Trademarks
        </Typography>
      </Box>
    </Box>
  );
};

export default Homepage;