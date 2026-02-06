import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Homepage from './components/Homepage';
import Dashboard from './components/Dashboard';
import Incidents from './components/Incidents';
import ServiceCatalog from './components/ServiceCatalog';
import ITServices from './components/ITServices';
import KnowledgeBase from './components/KnowledgeBase';
import MyTickets from './components/MyTickets';
import PasswordResetForm from './components/PasswordResetForm';
import ProblemReportForm from './components/ProblemReportForm';
import BusinessAppForm from './components/BusinessAppForm';
import SLADashboard from './components/SLADashboard';
import AssignmentGroups from './components/AssignmentGroups';
import Notifications from './components/Notifications';
import SLADefinitions from './components/SLADefinitions';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function AppContent() {
  const { token } = useAuth();

  if (!token) {
    return <Login />;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', minHeight: '100vh' }}>
      <Navbar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: 8,
          width: '100%',
          position: 'relative',
        }}
      >
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/homepage" element={<Homepage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/service-catalog" element={<ServiceCatalog />} />
          <Route path="/it-services" element={<ITServices />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="/knowledge-base/:articleId" element={<KnowledgeBase />} />
          <Route path="/my-tickets" element={<MyTickets />} />
          <Route path="/password-reset" element={<PasswordResetForm />} />
          <Route path="/problem-report" element={<ProblemReportForm />} />
          <Route path="/business-app-help" element={<BusinessAppForm />} />
          <Route path="/sla-dashboard" element={<SLADashboard />} />
          <Route path="/assignment-groups" element={<AssignmentGroups />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/sla-definitions" element={<SLADefinitions />} />
        </Routes>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;