// Document types
export interface Document {
  id: string;
  filename: string;
  total_pages: number;
  upload_date: string;
  status: 'processing' | 'completed' | 'failed' | 'completed_with_errors' | 'cancelled';
  results?: BrandDetection[];
}

export interface DocumentCreate {
  filename: string;
  total_pages: number;
}

// Brand detection types
export interface BrandDetection {
  page_number: number;
  brands_detected: string[];
  processing_time: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  brands_review_status: Record<string, boolean>;
}

export interface BrandDetectionCreate {
  page_number: number;
  brands_detected: string[];
}

export interface BrandReviewUpdate {
  document_id: string;
  page_number: number;
  brand_name: string;
  is_reviewed: boolean;
}

// Processing status types
export interface ProcessingStatus {
  document_id: string;
  status: string;
  total_pages: number;
  processed_pages: number;
  failed_pages: number;
  progress_percentage: number;
  page_status: Record<number, string>;
  estimated_time_remaining?: number;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  document: Document;
  message: string;
}

// UI state types
export interface UploadState {
  isUploading: boolean;
  progress: number;
  error?: string;
}

export interface DocumentListState {
  documents: Document[];
  loading: boolean;
  error?: string;
  filters: {
    search: string;
    status: string;
  };
}
