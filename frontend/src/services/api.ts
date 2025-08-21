import axios from 'axios';
import { Document, ProcessingStatus } from '@/types';

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Document API functions
export const documentApi = {
  // Upload document
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<Document>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Get all documents
  getAll: async (): Promise<Document[]> => {
    const response = await api.get<Document[]>('/api/documents/');
    return response.data;
  },

  // Get document by ID
  getById: async (id: string): Promise<Document> => {
    const response = await api.get<Document>(`/api/documents/${id}`);
    return response.data;
  },

  // Get document results
  getResults: async (id: string): Promise<Document> => {
    const response = await api.get<Document>(`/api/documents/${id}/results`);
    return response.data;
  },

  // Delete document
  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/documents/${id}`);
  },

  // Cancel processing
  cancelProcessing: async (id: string): Promise<void> => {
    await api.post(`/api/documents/${id}/cancel`);
  },
};

// Processing status API functions
export const processingApi = {
  // Get processing status
  getStatus: async (documentId: string): Promise<ProcessingStatus> => {
    const response = await api.get<ProcessingStatus>(`/api/documents/${documentId}/status`);
    return response.data;
  },

  // Get active processes
  getActiveProcesses: async (): Promise<{ active_processes: Record<string, any>; count: number }> => {
    const response = await api.get('/api/documents/active/processes');
    return response.data;
  },
};

// Health check API functions
export const healthApi = {
  // Health check
  check: async (): Promise<{ status: string; message: string; version: string; timestamp: string }> => {
    const response = await api.get('/health/');
    return response.data;
  },

  // Readiness check
  ready: async (): Promise<{ status: string; timestamp: string; services: Record<string, string> }> => {
    const response = await api.get('/health/ready');
    return response.data;
  },
};

export default api;
