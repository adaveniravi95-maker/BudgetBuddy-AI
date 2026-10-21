import axios from 'axios';

const API_ORIGIN = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

const api = axios.create({
  baseURL: `${API_ORIGIN}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach JWT token
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

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_ORIGIN}/api/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', res.data.access);
          error.config.headers.Authorization = `Bearer ${res.data.access}`;
          return api(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: (data) => api.post('/auth/logout/', data),
  getProfile: () => api.get('/auth/profile/'),
  checkAuth: () => api.get('/auth/check/'),
};

// Expense API
export const expenseAPI = {
  create: (data) => api.post('/expenses/', data),
  list: (params) => api.get('/expenses/', { params }),
  get: (id) => api.get(`/expenses/${id}/`),
  update: (id, data) => api.put(`/expenses/${id}/`, data),
  delete: (id) => api.delete(`/expenses/${id}/`),
};

// Income API
export const incomeAPI = {
  create: (data) => api.post('/incomes/', data),
  list: (params) => api.get('/incomes/', { params }),
  get: (id) => api.get(`/incomes/${id}/`),
  update: (id, data) => api.put(`/incomes/${id}/`, data),
  delete: (id) => api.delete(`/incomes/${id}/`),
};

// Transaction API
export const transactionAPI = {
  summary: () => api.get('/transactions/summary/'),
  list: (params) => api.get('/transactions/', { params }),
};

// Budget API
export const budgetAPI = {
  create: (data) => api.post('/budgets/', data),
  list: (params) => api.get('/budgets/', { params }),
  get: (id) => api.get(`/budgets/${id}/`),
  update: (id, data) => api.put(`/budgets/${id}/`, data),
  delete: (id) => api.delete(`/budgets/${id}/`),
};

// Savings Goal API
export const savingsAPI = {
  create: (data) => api.post('/savings/', data),
  list: () => api.get('/savings/'),
  get: (id) => api.get(`/savings/${id}/`),
  update: (id, data) => api.put(`/savings/${id}/`, data),
  updateProgress: (id, data) => api.put(`/savings/${id}/progress/`, data),
  delete: (id) => api.delete(`/savings/${id}/`),
};

// Notification API
export const notificationAPI = {
  list: () => api.get('/notifications/'),
  unread: () => api.get('/notifications/unread/'),
  markRead: (id) => api.put(`/notifications/${id}/read/`),
  markAllRead: () => api.put('/notifications/read-all/'),
};

// Report API
export const reportAPI = {
  monthly: (params) => api.get('/reports/monthly/', { params }),
  download: (params) =>
    api.get('/reports/monthly/', {
      params,
      responseType: 'blob',
      headers: { Accept: '*/*' },
    }),
};

// Analytics API
export const analyticsAPI = {
  get: (params) => api.get('/analytics/', { params }),
};

export default api;
