import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:18000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
  getCurrentUser: () => api.get('/api/auth/me'),
  getUsers: () => api.get('/api/auth/users'),
};

// Accounts
export const accountsAPI = {
  list: (params) => api.get('/api/accounts', { params }),
  get: (id) => api.get(`/api/accounts/${id}`),
  create: (data) => api.post('/api/accounts', data),
  update: (id, data) => api.put(`/api/accounts/${id}`, data),
  delete: (id) => api.delete(`/api/accounts/${id}`),
  changeOwner: (id, ownerId) => api.put(`/api/accounts/${id}/change-owner?owner_id=${ownerId}`),
  listRequests: (params) => api.get('/api/accounts/requests', { params }),
  approveRequest: (requestId) => api.post(`/api/accounts/requests/${requestId}/approve`),
  mulesoftAccept: (requestId) => api.post(`/api/accounts/requests/${requestId}/mulesoft-accept`),
  deleteRequest: (requestId) => api.delete(`/api/accounts/requests/${requestId}`),
};

// Contacts
export const contactsAPI = {
  list: (params) => api.get('/api/contacts', { params }),
  get: (id) => api.get(`/api/contacts/${id}`),
  create: (data, checkDuplicates = false) =>
    api.post(`/api/contacts?check_duplicates=${checkDuplicates}`, data),
  update: (id, data) => api.put(`/api/contacts/${id}`, data),
  delete: (id) => api.delete(`/api/contacts/${id}`),
  changeOwner: (id, ownerId) => api.put(`/api/contacts/${id}/change-owner?owner_id=${ownerId}`),
  checkDuplicates: (email, phone) =>
    api.post('/api/contacts/check-duplicates', null, { params: { email, phone } }),
};

// Leads
export const leadsAPI = {
  list: (params) => api.get('/api/leads', { params }),
  get: (id) => api.get(`/api/leads/${id}`),
  create: (data, checkDuplicates = false, autoAssign = true) =>
    api.post(`/api/leads?check_duplicates=${checkDuplicates}&auto_assign=${autoAssign}`, data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
  convert: (id, data) => api.post(`/api/leads/${id}/convert`, data),
  changeOwner: (id, ownerId) => api.put(`/api/leads/${id}/change-owner?owner_id=${ownerId}`),
  checkDuplicates: (email, phone) =>
    api.post('/api/leads/check-duplicates', null, { params: { email, phone } }),
};

// Opportunities
export const opportunitiesAPI = {
  list: (params) => api.get('/api/opportunities', { params }),
  get: (id) => api.get(`/api/opportunities/${id}`),
  create: (data) => api.post('/api/opportunities', data),
  update: (id, data) => api.put(`/api/opportunities/${id}`, data),
  delete: (id) => api.delete(`/api/opportunities/${id}`),
  changeOwner: (id, ownerId) => api.put(`/api/opportunities/${id}/change-owner?owner_id=${ownerId}`),
  updateStage: (id, stage) => api.put(`/api/opportunities/${id}/stage?stage=${stage}`),
};

// Cases
export const casesAPI = {
  list: (params) => api.get('/api/cases', { params }),
  get: (id) => api.get(`/api/cases/${id}`),
  create: (data, autoAssign = true) =>
    api.post(`/api/cases?auto_assign=${autoAssign}`, data),
  update: (id, data) => api.put(`/api/cases/${id}`, data),
  delete: (id) => api.delete(`/api/cases/${id}`),
  escalate: (id) => api.post(`/api/cases/${id}/escalate`),
  merge: (caseIds, masterCaseId) =>
    api.post('/api/cases/merge', { case_ids: caseIds, master_case_id: masterCaseId }),
  changeOwner: (id, ownerId) => api.put(`/api/cases/${id}/change-owner?owner_id=${ownerId}`),
  getByPriority: (ownerId) => api.get('/api/cases/by-priority', { params: { owner_id: ownerId } }),
  checkSLA: () => api.post('/api/cases/check-sla'),
};

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getRecentRecords: (limit = 10) => api.get('/api/dashboard/recent-records', { params: { limit } }),
  search: (q, limit = 20) => api.get('/api/dashboard/search', { params: { q, limit } }),
};

// Activities
export const activitiesAPI = {
  list: (recordType, recordId, skip = 0, limit = 50) =>
    api.get(`/api/activities/${recordType}/${recordId}`, { params: { skip, limit } }),
  create: (data) => api.post('/api/activities', data),
};

// Service
export const serviceAPI = {
  // Service Accounts
  listServiceAccounts: (skip = 0, limit = 25) =>
    api.get('/api/service/accounts', { params: { skip, limit } }),
  createServiceAccount: (data) => api.post('/api/service/accounts', data),
  getServiceAccount: (id) => api.get(`/api/service/accounts/${id}`),
  updateServiceAccount: (id, data) => api.put(`/api/service/accounts/${id}`, data),

  // Quotations
  listQuotations: (skip = 0, limit = 25) =>
    api.get('/api/service/quotations', { params: { skip, limit } }),
  createQuotation: (data) => api.post('/api/service/quotations', data),
  getQuotation: (id) => api.get(`/api/service/quotations/${id}`),
  updateQuotation: (id, data) => api.put(`/api/service/quotations/${id}`, data),

  // Invoices
  listInvoices: (skip = 0, limit = 25) =>
    api.get('/api/service/invoices', { params: { skip, limit } }),
  createInvoice: (data) => api.post('/api/service/invoices', data),
  getInvoice: (id) => api.get(`/api/service/invoices/${id}`),
  updateInvoice: (id, data) => api.put(`/api/service/invoices/${id}`, data),

  // Warranty Extensions
  listWarrantyExtensions: (skip = 0, limit = 25) =>
    api.get('/api/service/warranty-extensions', { params: { skip, limit } }),
  createWarrantyExtension: (data) => api.post('/api/service/warranty-extensions', data),

  // SLAs
  listSLAs: (skip = 0, limit = 25) =>
    api.get('/api/service/slas', { params: { skip, limit } }),
  createSLA: (data) => api.post('/api/service/slas', data),

  // Service Appointments (Scenario 2)
  listAppointments: (params) => api.get('/api/service/appointments', { params }),
  createAppointment: (data) => api.post('/api/service/appointments', data),
  getAppointment: (id) => api.get(`/api/service/appointments/${id}`),

  // Scheduling Requests (MuleSoft Scenario 2)
  listSchedulingRequests: (params) => api.get('/api/service/scheduling-requests', { params }),
  approveSchedulingRequest: (requestId, technicianId, technicianName) =>
    api.post(`/api/service/scheduling-requests/${requestId}/approve?technician_id=${technicianId}&technician_name=${encodeURIComponent(technicianName)}`),

  // Work Orders (Scenario 3)
  listWorkOrders: (params) => api.get('/api/service/work-orders', { params }),
  createWorkOrder: (data) => api.post('/api/service/work-orders', data),
  getWorkOrder: (id) => api.get(`/api/service/work-orders/${id}`),
  checkEntitlement: (workOrderId) => api.get(`/api/service/work-orders/${workOrderId}/check-entitlement`),

  // SAP Integration helpers
  checkPartsAvailability: (appointmentId) => api.get(`/api/service/appointments/${appointmentId}/check-parts`),
  retrySAPSync: (recordId, scenarioType) => api.post(`/api/mulesoft/retry/${scenarioType}/${recordId}`),
};

export default api;
