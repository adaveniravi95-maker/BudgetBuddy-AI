import axios from 'axios';

// Base API instance
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Attach JWT Bearer token to protected requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Global error handler for 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 and refresh token exists, try refreshing once
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        originalRequest._retry = true;
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const newAccessToken = res.data.access;
          localStorage.setItem('access_token', newAccessToken);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshErr) {
          // Refresh failed - clear tokens and force logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_info');
          window.dispatchEvent(new Event('auth:logout'));
        }
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        window.dispatchEvent(new Event('auth:logout'));
      }
    }
    return Promise.reject(error);
  }
);

// Auth API services
export const authAPI = {
  register: (userData) => api.post('/auth/register/', userData),
  login: (credentials) => api.post('/auth/login/', credentials),
  getProfile: () => api.get('/auth/me/'),
  refreshToken: (refresh) => api.post('/auth/token/refresh/', { refresh }),
};

// Core Resource API services
export const expensesAPI = {
  getExpenses: () => api.get('/expenses/'),
  getExpense: (id) => api.get(`/expenses/${id}/`),
  createExpense: (data) => api.post('/expenses/', data),
  updateExpense: (id, data) => api.put(`/expenses/${id}/`, data),
  patchExpense: (id, data) => api.patch(`/expenses/${id}/`, data),
  deleteExpense: (id) => api.delete(`/expenses/${id}/`),
};


export const incomesAPI = {
  getIncomes: () => api.get('/incomes/'),
  getIncome: (id) => api.get(`/incomes/${id}/`),
  createIncome: (data) => api.post('/incomes/', data),
  updateIncome: (id, data) => api.put(`/incomes/${id}/`, data),
  patchIncome: (id, data) => api.patch(`/incomes/${id}/`, data),
  deleteIncome: (id) => api.delete(`/incomes/${id}/`),
};

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary/'),
};

export const transactionsAPI = {
  importCsv: (file, preview = false, decisions = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (decisions) formData.append('decisions', JSON.stringify(decisions));
    return api.post('/transactions/import/', formData, {
      params: preview ? { preview: 'true' } : undefined,
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const budgetsAPI = {
  getBudgets: (params) => api.get('/budgets/', { params }),
  getBudget: (id) => api.get(`/budgets/${id}/`),
  createBudget: (data) => api.post('/budgets/', data),
  updateBudget: (id, data) => api.put(`/budgets/${id}/`, data),
  patchBudget: (id, data) => api.patch(`/budgets/${id}/`, data),
  deleteBudget: (id) => api.delete(`/budgets/${id}/`),
  getBudgetSummary: (params) => api.get('/budgets/summary/', { params }),
};

export const savingsGoalsAPI = {
  getGoals: () => api.get('/savings-goals/'),
  getGoal: (id) => api.get(`/savings-goals/${id}/`),
  createGoal: (data) => api.post('/savings-goals/', data),
  updateGoal: (id, data) => api.put(`/savings-goals/${id}/`, data),
  patchGoal: (id, data) => api.patch(`/savings-goals/${id}/`, data),
  deleteGoal: (id) => api.delete(`/savings-goals/${id}/`),
};

export const notificationsAPI = {
  getNotifications: (unreadOnly = false) =>
    api.get('/notifications/', { params: unreadOnly ? { unread: 'true' } : {} }),
  getUnreadCount: () => api.get('/notifications/unread-count/'),
  getNotification: (id) => api.get(`/notifications/${id}/`),
  markAsRead: (id) => api.patch(`/notifications/${id}/read/`),
  markAllAsRead: () => api.post('/notifications/mark-all-read/'),
  deleteNotification: (id) => api.delete(`/notifications/${id}/`),
};

export const analyticsAPI = {
  getOverview: (params) => api.get('/analytics/overview/', { params }),
  getTrends: (params) => api.get('/analytics/trends/', { params }),
};

export const reportsAPI = {
  getReports: () => api.get('/reports/'),
  getReport: (id) => api.get(`/reports/${id}/`),
  generateReport: (data) => api.post('/reports/generate/', data),
  deleteReport: (id) => api.delete(`/reports/${id}/`),
  exportReport: (id, format = 'csv') =>
    api.get(`/reports/${id}/export/`, {
      params: { format },
      responseType: format === 'json' ? 'json' : 'blob',
    }),
};

export default api;
