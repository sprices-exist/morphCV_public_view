import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import environment from '../utils/environmentSetup';

// Base API configuration from environment
const BASE_URL = environment.apiUrl;

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Error handler
export const handleApiError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    
    if (axiosError.response) {
      // The request was made and the server responded with an error status
      const status = axiosError.response.status;
      const data = axiosError.response.data as Record<string, unknown>;
      
      // Format the error message
      const message = data.message 
        ? String(data.message) 
        : `API Error: ${status}`;
      
      // Handle specific status codes
      switch (status) {
        case 401:
          throw new Error(`Authentication error: ${message}`);
        case 403:
          throw new Error(`Permission denied: ${message}`);
        case 404:
          throw new Error(`Resource not found: ${message}`);
        case 429:
          throw new Error(`Rate limit exceeded: ${message}`);
        default:
          throw new Error(message);
      }
    } else if (axiosError.request) {
      // The request was made but no response was received
      throw new Error('Network error: No response received from server');
    } else {
      // Something happened in setting up the request
      throw new Error(`Request error: ${axiosError.message}`);
    }
  }
  
  // For non-Axios errors
  throw new Error(`Unexpected error: ${String(error)}`);
};

// Request interceptor to add authentication token
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('access_token');
    
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 errors with token refresh
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      localStorage.getItem('refresh_token')
    ) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });
        
        // Update tokens
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        // Update the original request with the new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // If refresh fails, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirect to login page
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper method for handling API requests
export const apiRequest = async <T>(
  config: AxiosRequestConfig
): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await apiClient(config);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export default apiClient;