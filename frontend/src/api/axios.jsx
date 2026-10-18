import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/',
});

// Request Interceptor: Automatically attach token to every request
api.interceptors.request.use(
  (config) => {
    // Check both potential key names
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    
    if (token && token !== 'undefined' && token !== 'null') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 gracefully
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If token is truly expired, clear storage
      console.warn('Session expired or unauthorized token.');
    }
    return Promise.reject(error);
  }
);

export default api;