import { create } from 'zustand';
import { Document, ProcessingStatus, UploadState, DocumentListState } from '@/types';

// Upload state store
interface UploadStore extends UploadState {
  setUploading: (isUploading: boolean) => void;
  setProgress: (progress: number | ((prev: number) => number)) => void;
  setError: (error?: string) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadStore>((set) => ({
  isUploading: false,
  progress: 0,
  error: undefined,
  setUploading: (isUploading) => set({ isUploading }),
  setProgress: (progress) => set((state) => ({ 
    progress: typeof progress === 'function' ? progress(state.progress) : progress 
  })),
  setError: (error) => set({ error }),
  reset: () => set({ isUploading: false, progress: 0, error: undefined }),
}));

// Document list store
interface DocumentListStore extends DocumentListState {
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error?: string) => void;
  setFilters: (filters: { search: string; status: string }) => void;
  clearFilters: () => void;
}

export const useDocumentListStore = create<DocumentListStore>((set) => ({
  documents: [],
  loading: false,
  error: undefined,
  filters: {
    search: '',
    status: '',
  },
  setDocuments: (documents) => set({ documents }),
  addDocument: (document) => set((state) => ({ 
    documents: [document, ...state.documents] 
  })),
  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map(doc => 
      doc.id === id ? { ...doc, ...updates } : doc
    )
  })),
  removeDocument: (id) => set((state) => ({
    documents: state.documents.filter(doc => doc.id !== id)
  })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilters: (filters) => set({ filters }),
  clearFilters: () => set({ 
    filters: { search: '', status: '' } 
  }),
}));

// Processing status store
interface ProcessingStatusStore {
  statuses: Record<string, ProcessingStatus>;
  setStatus: (documentId: string, status: ProcessingStatus) => void;
  removeStatus: (documentId: string) => void;
  clearAll: () => void;
}

export const useProcessingStatusStore = create<ProcessingStatusStore>((set) => ({
  statuses: {},
  setStatus: (documentId, status) => set((state) => ({
    statuses: { ...state.statuses, [documentId]: status }
  })),
  removeStatus: (documentId) => set((state) => {
    const newStatuses = { ...state.statuses };
    delete newStatuses[documentId];
    return { statuses: newStatuses };
  }),
  clearAll: () => set({ statuses: {} }),
}));

// UI state store
interface UIStore {
  sidebarOpen: boolean;
  selectedDocumentId: string | null;
  setSidebarOpen: (open: boolean) => void;
  setSelectedDocumentId: (id: string | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: false,
  selectedDocumentId: null,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setSelectedDocumentId: (selectedDocumentId) => set({ selectedDocumentId }),
}));
