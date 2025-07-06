import { apiRequest } from './apiClient';

// Define environment to resolve build error, defaulting apiUrl for same-origin relative paths.
// VITE_API_URL should be the full base URL to the backend API if set, e.g., http://localhost:5000/api/v1
const environment = {
  apiUrl: import.meta.env.VITE_API_URL || '/api/v1'
};

export interface CVData {
  id: number;
  uuid: string;
  title: string;
  template_name: string;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  last_downloaded?: string;
  has_pdf: boolean;
  has_jpg: boolean;
  pdf_size?: number;
  generation_time?: number;
  user_data?: any;
  job_description?: string;
  latex_code?: string;
  download_urls?: {
    pdf?: string;
    jpg?: string;
  };
  task_info?: { // For storing progress and status message from polling
    progress?: number;
    status?: string; // Detailed status message from task
  };
}

export interface CVListResponse {
  cvs: CVData[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface CVCreateRequest {
  title: string;
  template_name: string;
  user_data: {
    name: string;
    email: string;
    experience: string;
    skills: string[] | string;
    education: string;
    [key: string]: any;
  };
  job_description: string;
}

export interface CVUpdateRequest {
  title?: string;
  template_name?: string;
  user_data?: {
    name?: string;
    email?: string;
    experience?: string;
    skills?: string[] | string;
    education?: string;
    [key: string]: any;
  };
  job_description?: string;
}

export interface CVCreateResponse {
  message: string;
  cv: CVData;
  task_id: string;
}

export interface CVDetailResponse {
  cv: CVData;
}

// CORRECTED a more accurate response type
export interface CVStatusResponse {
  cv_id: string;
  status: 'pending' | 'processing' | 'success' | 'failed';
  error_message: string | null;
  generation_time?: number | null; // As per user's prompt for CVStatusCheckResponse
  has_files?: { pdf: boolean; jpg: boolean; }; // As per user's prompt for CVStatusCheckResponse
  task_status: CVTaskStatus | null; // Use the more detailed CVTaskStatus
}

export interface CVTaskStatus { // Structure for the 'task_status' field from backend
  state?: string; // Celery state e.g. PENDING, STARTED, SUCCESS, FAILURE
  progress?: number;
  step?: string;    // This will hold the status message
  // Other fields like ready, successful, failed, step from original CVStatusResponse might be part of 'info' or siblings
  // For now, focusing on aligning with user's reference to task_info.progress and task_info.status
  // Assuming 'info' is the key for the object containing progress and status message
  ready?: boolean;
  successful?: boolean;
  failed?: boolean;
}

const cvService = {
  /**
   * List user's CVs with pagination and filtering
   */
  listCVs: async (
    page = 1,
    perPage = 10,
    status?: string,
    template?: string,
    search?: string,
    sortBy = 'created_at',
    sortOrder = 'desc'
  ): Promise<CVListResponse> => {
    return apiRequest<CVListResponse>({
      method: 'GET',
      url: '/cvs',
      params: {
        page,
        per_page: perPage,
        status,
        template_name: template,
        search,
        sort_by: sortBy,
        sort_order: sortOrder
      }
    });
  },

  /**
   * Create a new CV
   */
  createCV: async (cvData: CVCreateRequest): Promise<CVCreateResponse> => {
    return apiRequest<CVCreateResponse>({
      method: 'POST',
      url: '/cvs',
      data: cvData
    });
  },

  /**
   * Get CV details by UUID
   */
  getCV: async (uuid: string): Promise<CVDetailResponse> => {
    return apiRequest<CVDetailResponse>({
      method: 'GET',
      url: `/cvs/${uuid}`
    });
  },

  /**
   * Update CV by UUID
   */
  updateCV: async (uuid: string, cvData: CVUpdateRequest): Promise<{ message: string; cv: CVData }> => {
    return apiRequest<{ message: string; cv: CVData }>({
      method: 'PUT',
      url: `/cvs/${uuid}`,
      data: cvData
    });
  },

  /**
   * Delete CV by UUID
   */
  deleteCV: async (uuid: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>({
      method: 'DELETE',
      url: `/cvs/${uuid}`
    });
  },

  /**
   * Check CV generation status
   */
  checkCVStatus: async (uuid: string): Promise<CVStatusResponse> => {
    return apiRequest<CVStatusResponse>({
      method: 'GET',
      url: `/cvs/${uuid}/status`
    });
  },

  /**
   * CORRECTED: Get direct download URL for CV file
   */
  getDownloadUrl: (uuid: string, type: 'pdf' | 'jpg'): string => {
    // Construct the full URL using the base API URL from environment
    const relativeUrl = `/cvs/${uuid}/download?type=${type}`;
    const accessToken = localStorage.getItem('access_token');
    // NOTE: For direct linking, we can't easily add the auth header.
    // If your download endpoint requires auth, this approach will fail.
    // The `prepareDownload` method is a better alternative for authenticated downloads.
    // For now, let's assume direct linking might work or we can add token in query.
    return `${environment.apiUrl}${relativeUrl}`;
  },

  /**
   * Prepare file download
   */
  prepareDownload: async (uuid: string, type: 'pdf' | 'jpg'): Promise<Blob> => {
    const response = await apiRequest<Blob>({
      method: 'GET',
      url: `/cvs/${uuid}/download`,
      params: { type },
      responseType: 'blob',
    });
    
    return response;
  }
};

export default cvService;