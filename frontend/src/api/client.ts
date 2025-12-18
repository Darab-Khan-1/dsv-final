import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.error('[API Connection Error]', 'Backend server is not reachable');
      error.isConnectionError = true;
    } else if (error.response) {
      console.error('[API Error]', error.response.status, error.response.data);
      error.isApiError = true;
    } else {
      console.error('[API Error]', error.message);
    }
    return Promise.reject(error);
  }
);
