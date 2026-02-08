/**
 * API Service Layer
 * Requirement 8.1 - API client with JWT interceptor
 *
 * REFACTORED: Removed unused API methods to reduce bundle size and network calls
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import logger from '../utils/logger';
import { trackApiCall } from '../utils/performance';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://207.180.217.117:4798/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// JWT token storage
let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

export const getAuthToken = (): string | null => {
  if (!authToken) {
    authToken = localStorage.getItem('auth_token');
  }
  return authToken;
};

// Request interceptor - add JWT token and logging
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log API call
    logger.apiCall(
      config.method?.toUpperCase() || 'UNKNOWN',
      config.url || 'unknown',
      config.data,
      'API'
    );

    return config;
  },
  (error) => {
    logger.error('API request interceptor error', error, 'API');
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors and logging
api.interceptors.response.use(
  (response) => {
    // Log successful API response
    logger.apiSuccess(
      response.config.method?.toUpperCase() || 'UNKNOWN',
      response.config.url || 'unknown',
      {
        status: response.status,
        statusText: response.statusText,
        dataSize: JSON.stringify(response.data).length,
      },
      'API'
    );
    return response;
  },
  (error: AxiosError) => {
    // Log API error
    logger.apiError(
      error.config?.method?.toUpperCase() || 'UNKNOWN',
      error.config?.url || 'unknown',
      error,
      'API'
    );

    if (error.response?.status === 401) {
      logger.warn('Authentication failed, redirecting to login', { status: 401 }, 'AUTH');
      setAuthToken(null);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Enhanced API call wrapper with performance tracking
const apiCall = async <T>(call: () => Promise<T>, method: string, url: string): Promise<T> => {
  return trackApiCall(method, url, call);
};

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    apiCall(() => api.post('/auth/login', { username, password }), 'POST', '/auth/login'),
};

// Tickets API - Only methods actually used in components
export const ticketsApi = {
  list: (params?: { module?: string; status?: string; page?: number; limit?: number }) =>
    apiCall(() => api.get('/tickets', { params }), 'GET', '/tickets'),
  create: (data: { module: string; ticket_type: string; priority: string; title: string; description?: string; created_by: string }) =>
    apiCall(() => api.post('/tickets', data), 'POST', '/tickets'),
  updateStatus: (ticketId: string, newStatus: string, changedBy: string, comment?: string) =>
    apiCall(() => api.patch(`/tickets/${ticketId}/status`, { new_status: newStatus, changed_by: changedBy, comment }), 'PATCH', `/tickets/${ticketId}/status`),
};

// PM API - Only methods actually used in PM.tsx
export const pmApi = {
  createAsset: (data: any) => api.post('/pm/assets', data),
  listAssets: (params?: any) => api.get('/pm/assets', { params }),
  listMaintenanceOrders: (params?: any) => api.get('/pm/maintenance-orders', { params }),
};

// MM API - Only methods actually used in MM.tsx
export const mmApi = {
  createMaterial: (data: any) => api.post('/mm/materials', data),
  listMaterials: (params?: any) => api.get('/mm/materials', { params }),
  listRequisitions: (params?: any) => api.get('/mm/purchase-requisitions', { params }),
};

// FI API - Only methods actually used in FI.tsx
export const fiApi = {
  createCostCenter: (data: any) => api.post('/fi/cost-centers', data),
  listCostCenters: (params?: any) => api.get('/fi/cost-centers', { params }),
  listApprovals: (params?: any) => api.get('/fi/approval-requests', { params }),
  approveRequest: (approvalId: string, decidedBy: string, comment?: string) =>
    api.post(`/fi/approval-requests/${approvalId}/approve`, { decided_by: decidedBy, comment }),
  rejectRequest: (approvalId: string, decidedBy: string, comment?: string) =>
    api.post(`/fi/approval-requests/${approvalId}/reject`, { decided_by: decidedBy, comment }),
};

// Users API - Only methods actually used in UserManagement.tsx
export const usersApi = {
  list: () =>
    apiCall(() => api.get('/users'), 'GET', '/users'),
  create: (data: { username: string; password: string; roles: string[] }) =>
    apiCall(() => api.post('/users', data), 'POST', '/users'),
  changePassword: (username: string, newPassword: string) =>
    apiCall(() => api.patch(`/users/${username}/password`, { username, new_password: newPassword }), 'PATCH', `/users/${username}/password`),
  delete: (username: string) =>
    apiCall(() => api.delete(`/users/${username}`), 'DELETE', `/users/${username}`),
};

// Work Order Flow API (PM → MM → FI) - Only methods actually used
export const workOrderFlowApi = {
  create: (data: any) => api.post('/work-order-flow/work-orders', data),
  list: (params?: any) => api.get('/work-order-flow/work-orders', { params }),
  checkMaterials: (workOrderId: string, performedBy: string) =>
    api.post(`/work-order-flow/work-orders/${workOrderId}/check-materials`, { performed_by: performedBy }),
  requestPurchase: (workOrderId: string, performedBy: string, justification?: string) =>
    api.post(`/work-order-flow/work-orders/${workOrderId}/request-purchase`, { performed_by: performedBy, justification }),
  approvePurchase: (workOrderId: string, approved: boolean, decidedBy: string, comment?: string) =>
    api.post(`/work-order-flow/work-orders/${workOrderId}/approve-purchase`, { approved, decided_by: decidedBy, comment }),
  getPendingPurchase: () => api.get('/work-order-flow/work-orders/pending-purchase'),
  getPendingApproval: () => api.get('/work-order-flow/work-orders/pending-approval'),
};

// Password Reset Tickets API (ServiceNow Integration)
export const passwordResetApi = {
  // GET /api/integration/password-reset-tickets - List pending password reset tickets
  listTickets: () => {
    const baseUrl = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://207.180.217.117:4798';
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return apiCall(
      () => axios.get(`${baseUrl}/api/integration/password-reset-tickets`, { headers }),
      'GET',
      '/api/integration/password-reset-tickets'
    );
  },
  // GET /api/integration/password-reset-tickets/{ticket_id} - Get specific ticket
  getTicket: (ticketId: string) => {
    const baseUrl = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://207.180.217.117:4798';
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return apiCall(
      () => axios.get(`${baseUrl}/api/integration/password-reset-tickets/${ticketId}`, { headers }),
      'GET',
      `/api/integration/password-reset-tickets/${ticketId}`
    );
  },
  // PATCH /api/integration/password-reset-tickets/{ticket_id}/status - Update status
  updateStatus: (ticketId: string, status: string, changedBy: string = 'admin') => {
    const baseUrl = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://207.180.217.117:4798';
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return apiCall(
      () => axios.patch(`${baseUrl}/api/integration/password-reset-tickets/${ticketId}/status`, 
        { status, changed_by: changedBy }, 
        { headers }
      ),
      'PATCH',
      `/api/integration/password-reset-tickets/${ticketId}/status`
    );
  },
  // POST /api/integration/password-reset-tickets/{id}/reset-password - Execute password reset
  resetPassword: (ticketId: string, changedBy: string = 'admin') => {
    const baseUrl = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://207.180.217.117:4798';
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return apiCall(
      () => axios.post(`${baseUrl}/api/integration/password-reset-tickets/${ticketId}/reset-password?changed_by=${changedBy}`, {}, { headers }),
      'POST',
      `/api/integration/password-reset-tickets/${ticketId}/reset-password`
    );
  },
};

export default api;
