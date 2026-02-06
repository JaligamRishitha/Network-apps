import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppShell from './components/AppShell';
import RecordDetail from './components/RecordDetail';
import Login from './pages/Login';
import Home from './pages/Home';
import Contacts from './pages/Contacts';
import Accounts from './pages/Accounts';
import AccountRequests from './pages/AccountRequests';
import Sales from './pages/Sales';
import Service from './pages/Service';
import ServiceManagement from './pages/ServiceManagement';
import Marketing from './pages/Marketing';
import Commerce from './pages/Commerce';
import GenerativeCanvas from './pages/GenerativeCanvas';
import YourAccount from './pages/YourAccount';
import ServiceNowScenarios from './pages/ServiceNowScenarios';
import ServiceNowTracking from './pages/ServiceNowTracking';
import AccountRequestsStatus from './pages/AccountRequestsStatus';
import {
  contactsAPI,
  accountsAPI,
  leadsAPI,
  opportunitiesAPI,
  casesAPI,
} from './services/api';
import './index.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sf-bg">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-sf-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/home" replace />} />
        <Route path="home" element={<Home />} />
        <Route path="contacts" element={<Contacts />} />
        <Route path="contacts/:id" element={<RecordDetail objectType="contact" api={contactsAPI} />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="requests" element={<AccountRequests />} />
        <Route path="accounts/:id" element={<RecordDetail objectType="account" api={accountsAPI} />} />
        <Route path="leads" element={<Sales />} />
        <Route path="leads/:id" element={<RecordDetail objectType="lead" api={leadsAPI} />} />
        <Route path="opportunities" element={<Sales />} />
        <Route path="opportunities/:id" element={<RecordDetail objectType="opportunity" api={opportunitiesAPI} />} />
        <Route path="cases" element={<Service />} />
        <Route path="cases/:id" element={<RecordDetail objectType="case" api={casesAPI} />} />
        <Route path="sales" element={<Sales />} />
        <Route path="service" element={<Service />} />
        <Route path="service-management" element={<ServiceManagement />} />
        <Route path="marketing" element={<Marketing />} />
        <Route path="commerce" element={<Commerce />} />
        <Route path="generative" element={<GenerativeCanvas />} />
        <Route path="account" element={<YourAccount />} />
        <Route path="account-requests-status" element={<AccountRequestsStatus />} />
        <Route path="servicenow" element={<ServiceNowScenarios />} />
        <Route path="servicenow-tracking" element={<ServiceNowTracking />} />
      </Route>
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}
