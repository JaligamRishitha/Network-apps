
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Button,
  Box,
  Menu,
  MenuItem,
  Divider,
  Avatar
} from '@mui/material';
import {
  AccountCircle,
  ExitToApp,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [workplaceAnchor, setWorkplaceAnchor] = useState(null);
  const [itAnchor, setItAnchor] = useState(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);

  const handleWorkplaceClick = (event) => {
    setWorkplaceAnchor(event.currentTarget);
  };

  const handleItClick = (event) => {
    setItAnchor(event.currentTarget);
  };

  const handleUserMenuClick = (event) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleClose = () => {
    setWorkplaceAnchor(null);
    setItAnchor(null);
    setUserMenuAnchor(null);
  };

  const handleNavigation = (path) => {
    navigate(path);
    handleClose();
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: '#fff',
        color: '#333',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        borderBottom: '1px solid #e0e0e0'
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: 2 }}>
        {/* Left side - Logo */}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { opacity: 0.8 }
            }}
            onClick={() => navigate('/')}
          >
            {/* ServiceNow Logo Image */}
            <img 
              src="/images/ServiceNow.png" 
              alt="ServiceNow" 
              style={{
                height: '32px',
                width: 'auto',
                objectFit: 'contain'
              }}
            />
          </Box>
        </Box>

        {/* Center - Navigation Links */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Button
            onClick={handleWorkplaceClick}
            endIcon={<ExpandMoreIcon />}
            sx={{
              color: '#FF8C42', // Orange color
              textTransform: 'none',
              mr: 3,
              fontWeight: 500,
              '&:hover': { backgroundColor: 'rgba(255,140,66,0.04)' }
            }}
          >
            Workplace
          </Button>
          <Menu
            anchorEl={workplaceAnchor}
            open={Boolean(workplaceAnchor)}
            onClose={handleClose}
            sx={{ mt: 1 }}
          >
            <MenuItem onClick={() => handleNavigation('/dashboard')}>Dashboard</MenuItem>
            <MenuItem onClick={() => handleNavigation('/')}>Home</MenuItem>
            <MenuItem onClick={() => handleNavigation('/sla-dashboard')}>SLA Dashboard</MenuItem>
            <MenuItem onClick={() => handleNavigation('/notifications')}>Notifications</MenuItem>
            <Divider />
            <MenuItem onClick={() => handleNavigation('/sla-definitions')}>SLA Definitions</MenuItem>
            <MenuItem onClick={() => handleNavigation('/assignment-groups')}>Assignment Groups</MenuItem>
          </Menu>

          <Button
            onClick={handleItClick}
            endIcon={<ExpandMoreIcon />}
            sx={{
              color: '#FF8C42', // Orange color
              textTransform: 'none',
              mr: 3,
              fontWeight: 500,
              '&:hover': { backgroundColor: 'rgba(255,140,66,0.04)' }
            }}
          >
            IT
          </Button>
          <Menu
            anchorEl={itAnchor}
            open={Boolean(itAnchor)}
            onClose={handleClose}
            sx={{ mt: 1 }}
          >
            <MenuItem onClick={() => handleNavigation('/it-services')}>IT Services</MenuItem>
            <MenuItem onClick={() => handleNavigation('/incidents')}>Incidents</MenuItem>
            <MenuItem onClick={() => handleNavigation('/service-catalog')}>Service Catalog</MenuItem>
            <MenuItem onClick={() => handleNavigation('/knowledge-base')}>Knowledge Base</MenuItem>
          </Menu>
        </Box>

        {/* Right side - User menu and actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            onClick={() => navigate('/my-tickets?tab=approvals')}
            sx={{
              color: '#FF8C42',
              textTransform: 'none',
              fontWeight: 500,
              '&:hover': { backgroundColor: 'rgba(255,140,66,0.04)' }
            }}
          >
            Approvals
          </Button>

          <Button
            onClick={() => navigate('/my-tickets')}
            sx={{
              color: '#FF8C42',
              textTransform: 'none',
              fontWeight: 500,
              '&:hover': { backgroundColor: 'rgba(255,140,66,0.04)' }
            }}
          >
            Tickets
          </Button>

          <Button
            onClick={handleUserMenuClick}
            sx={{
              color: '#333',
              textTransform: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              '&:hover': { backgroundColor: 'rgba(0,0,0,0.04)' }
            }}
          >
            <Avatar sx={{ width: 32, height: 32, backgroundColor: '#FF8C42' }}>
              {user?.full_name?.charAt(0) || 'U'}
            </Avatar>
            <Typography variant="body2" sx={{ color: '#333' }}>
              {user?.full_name || 'User'}
            </Typography>
            <ExpandMoreIcon />
          </Button>

          <Menu
            anchorEl={userMenuAnchor}
            open={Boolean(userMenuAnchor)}
            onClose={handleClose}
            sx={{ mt: 1 }}
          >
            <MenuItem onClick={handleClose}>
              <AccountCircle sx={{ mr: 1 }} />
              Profile
            </MenuItem>
            <MenuItem onClick={handleClose}>
              <SettingsIcon sx={{ mr: 1 }} />
              Settings
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { handleClose(); logout(); }}>
              <ExitToApp sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;