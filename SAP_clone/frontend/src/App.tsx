/**
 * Main App Component with Routing
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import TopNavLayout from './components/TopNavLayout';
import Login from './pages/Login';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Tickets from './pages/Tickets';
import PM from './pages/PM';
import MM from './pages/MM';
import FI from './pages/FI';
import AllTickets from './pages/AllTickets';
import UserManagement from './pages/UserManagement';
import ServiceNowTest from './components/ServiceNowTest';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* All pages with top navigation */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <TopNavLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="home" element={<Home />} />
        <Route path="tickets" element={<Tickets />} />
        <Route path="pm" element={<PM />} />
        <Route path="mm" element={<MM />} />
        <Route path="fi" element={<FI />} />
        <Route path="all-tickets" element={<AllTickets />} />
        <Route path="servicenow-test" element={<ServiceNowTest />} />
        <Route path="user-management" element={<UserManagement />} />
        <Route path="analytics" element={<div style={{padding: '20px'}}>Analytics Page</div>} />
        <Route path="billing" element={<div style={{padding: '20px'}}>Billing Page</div>} />
        <Route path="bpm" element={<div style={{padding: '20px'}}>Business Process Management</div>} />
        <Route path="credit" element={<div style={{padding: '20px'}}>Credit Management</div>} />
        <Route path="returns" element={<div style={{padding: '20px'}}>Customer Returns</div>} />
        <Route path="employee" element={<div style={{padding: '20px'}}>Employee Situation Handling</div>} />
        <Route path="sales" element={<div style={{padding: '20px'}}>Internal Sales</div>} />
        <Route path="sales-pro" element={<div style={{padding: '20px'}}>Internal Sales - Professional Services</div>} />
      </Route>
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
