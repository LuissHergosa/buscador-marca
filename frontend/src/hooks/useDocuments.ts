import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentApi, processingApi } from '@/services/api';
import { useDocumentListStore, useProcessingStatusStore } from '@/store';

// Hook for fetching all documents
export const useDocuments = () => {
  const { setDocuments, setLoading, setError } = useDocumentListStore();
  
  const query = useQuery({
    queryKey: ['documents'],
    queryFn: documentApi.getAll,
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  });

  // Update store when data changes
  useEffect(() => {
    if (query.data) {
      setDocuments(query.data);
      setLoading(false);
      setError(undefined);
    }
  }, [query.data, setDocuments, setLoading, setError]);

  useEffect(() => {
    if (query.error) {
      setError((query.error as any)?.response?.data?.detail || 'Failed to fetch documents');
      setLoading(false);
    }
  }, [query.error, setError, setLoading]);

  return query;
};

// Hook for fetching a single document
export const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => documentApi.getById(id),
    enabled: !!id,
    refetchInterval: 3000, // Refetch every 3 seconds for real-time updates
  });
};

// Hook for fetching document results
export const useDocumentResults = (id: string) => {
  return useQuery({
    queryKey: ['document-results', id],
    queryFn: () => documentApi.getResults(id),
    enabled: !!id,
    refetchInterval: 3000,
  });
};

// Hook for uploading a document
export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  const { addDocument } = useDocumentListStore();
  
  return useMutation({
    mutationFn: documentApi.upload,
    onSuccess: (data) => {
      addDocument(data);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

// Hook for deleting a document
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  const { removeDocument } = useDocumentListStore();
  
  return useMutation({
    mutationFn: documentApi.delete,
    onSuccess: (_, id) => {
      removeDocument(id);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

// Hook for canceling document processing
export const useCancelProcessing = () => {
  const queryClient = useQueryClient();
  const { updateDocument } = useDocumentListStore();
  
  return useMutation({
    mutationFn: documentApi.cancelProcessing,
    onSuccess: (_, id) => {
      updateDocument(id, { status: 'cancelled' });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

// Hook for fetching processing status
export const useProcessingStatus = (documentId: string) => {
  const { setStatus } = useProcessingStatusStore();
  
  const query = useQuery({
    queryKey: ['processing-status', documentId],
    queryFn: () => processingApi.getStatus(documentId),
    enabled: !!documentId,
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  // Update store when data changes
  useEffect(() => {
    if (query.data) {
      setStatus(documentId, query.data);
    }
  }, [query.data, documentId, setStatus]);

  return query;
};

// Hook for fetching active processes
export const useActiveProcesses = () => {
  return useQuery({
    queryKey: ['active-processes'],
    queryFn: processingApi.getActiveProcesses,
    refetchInterval: 3000,
  });
};
