import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Download, Edit, Trash2, File, Check, Clock, AlertCircle, 
  Plus, Search, Filter, RefreshCw, ChevronLeft, ChevronRight
} from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';
import { cvService } from '../lib/api';
import type { CVData } from '../lib/api/cvService';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import ErrorDisplay from '../components/shared/ErrorDisplay';

const statusIcons = {
  'pending': <Clock className="w-4 h-4 text-yellow-400" />,
  'processing': <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />,
  'success': <Check className="w-4 h-4 text-green-400" />,
  'failed': <AlertCircle className="w-4 h-4 text-red-400" />
};

const CVListPage = () => {
  const navigate = useNavigate();
  
  // State
  const [cvs, setCvs] = useState<CVData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);
  
  // Load CVs from API
  useEffect(() => {
    loadCVs();
  }, [currentPage, statusFilter]); // Initial load and when filters/page change

  // Effect for polling CV statuses
  useEffect(() => {
    const intervalIds = new Map<string, NodeJS.Timeout>();

    cvs.forEach(cv => {
      if ((cv.status === 'processing' || cv.status === 'pending') && !intervalIds.has(cv.uuid)) {
        const intervalId = setInterval(async () => {
          try {
            console.log(`Polling for CV: ${cv.uuid}, current status: ${cv.status}`);
            const statusResponse = await cvService.checkCVStatus(cv.uuid); // CVStatusResponse from cvService

            if (statusResponse.status === 'success') {
              clearInterval(intervalId);
              intervalIds.delete(cv.uuid);
              console.log(`CV ${cv.uuid} successfully processed. Fetching full details.`);

              const fullCvResponse = await cvService.getCV(cv.uuid); // CVDetailResponse
              setCvs(prevCvs =>
                prevCvs.map(prevCv => {
                  if (prevCv.uuid === cv.uuid) {
                    // Merge full CV data with the latest task_info from statusResponse
                    const taskInfoFromStatus = statusResponse.task_status ? {
                      progress: statusResponse.task_status.progress,
                      status: statusResponse.task_status.step, // Map 'step' to 'status' for task_info
                    } : undefined;

                    return {
                      ...fullCvResponse.cv, // Base with full CV data from getCV
                      // Ensure has_pdf is from the definitive getCV result
                      has_pdf: fullCvResponse.cv.has_pdf,
                      // Overlay the latest task_info from the final status check
                      task_info: taskInfoFromStatus || fullCvResponse.cv.task_info,
                    };
                  }
                  return prevCv;
                })
              );
            } else if (statusResponse.status === 'failed') {
              clearInterval(intervalId);
              intervalIds.delete(cv.uuid);
              console.log(`CV ${cv.uuid} failed processing. Polling stopped. Error: ${statusResponse.error_message}`);
              setCvs(prevCvs =>
                prevCvs.map(prevCv => {
                  if (prevCv.uuid === cv.uuid) {
                    return {
                      ...prevCv,
                      status: statusResponse.status,
                      error_message: statusResponse.error_message,
                      has_pdf: statusResponse.has_files?.pdf || prevCv.has_pdf, // Update has_pdf
                      task_info: statusResponse.task_status ? {
                        progress: statusResponse.task_status.progress,
                        status: statusResponse.task_status.step, // Map 'step' to 'status'
                      } : prevCv.task_info,
                    };
                  }
                  return prevCv;
                })
              );
            } else { // Still 'pending' or 'processing'
              setCvs(prevCvs =>
                prevCvs.map(prevCv => {
                  if (prevCv.uuid === cv.uuid) {
                    return {
                      ...prevCv,
                      status: statusResponse.status, // Update overall status
                      error_message: statusResponse.error_message, // Clear or update error message
                      has_pdf: statusResponse.has_files?.pdf || prevCv.has_pdf, // Update has_pdf
                      task_info: statusResponse.task_status ? {
                        progress: statusResponse.task_status.progress,
                        status: statusResponse.task_status.step, // Map 'step' to 'status'
                      } : prevCv.task_info,
                    };
                  }
                  return prevCv;
                })
              );
            }
          } catch (error) {
            console.error(`Error polling status for CV ${cv.uuid}:`, error);
            // Optionally, decide if to stop polling on error or implement retry limits
            clearInterval(intervalId); // Stop polling on error to prevent spamming
            intervalIds.delete(cv.uuid);
             // Optionally set an error message for this specific CV in the UI
            setCvs(prevCvs =>
              prevCvs.map(prevCv =>
                prevCv.uuid === cv.uuid
                  ? { ...prevCv, status: 'failed', error_message: 'Polling failed' } // Simplified error for display
                  : prevCv
              )
            );
          }
        }, 5000); // Poll every 5 seconds
        intervalIds.set(cv.uuid, intervalId);
      } else if ((cv.status === 'success' || cv.status === 'failed') && intervalIds.has(cv.uuid)) {
        // Clean up if status changed by other means (e.g. manual refresh or initial load already terminal)
        const intervalIdToClear = intervalIds.get(cv.uuid)!;
        clearInterval(intervalIdToClear);
        intervalIds.delete(cv.uuid);
        console.log(`CV ${cv.uuid} is already in a terminal state (${cv.status}). Polling stopped/not started.`);
      }
    });

    return () => { // Cleanup on component unmount or when cvs array itself changes instance
      intervalIds.forEach((id, uuid) => {
        clearInterval(id);
        console.log(`Cleared polling interval for CV ${uuid} on cleanup.`);
      });
      intervalIds.clear();
    };
  }, [cvs]); // Rerun when cvs array changes. setCvs is stable.
  
  const loadCVs = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await cvService.listCVs(
        currentPage,
        10,
        statusFilter || undefined,
        undefined,
        searchQuery || undefined
      );
      
      setCvs(response.cvs);
      setTotalPages(response.pagination.pages);
    } catch (err) {
      console.error('Error loading CVs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load CVs');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadCVs();
  };
  
  const handleFilterChange = (status: string) => {
    setStatusFilter(status);
    setCurrentPage(1);
  };
  
  const handlePageChange = (page: number) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
  };
  
  const handleDeleteCV = async (uuid: string) => {
    setIsDeleting(uuid);
    
    try {
      await cvService.deleteCV(uuid);
      setCvs(cvs.filter(cv => cv.uuid !== uuid));
    } catch (err) {
      console.error('Error deleting CV:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete CV');
    } finally {
      setIsDeleting(null);
    }
  };
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const handleDownloadCV = async (uuid: string, title: string) => {
    setIsDownloading(uuid);
    try {
      const blob = await cvService.prepareDownload(uuid, 'pdf');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${title.replace(/ /g, '_')}_${uuid.substring(0,8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading CV:', err);
      // Display a more user-friendly error, perhaps using a toast notification library
      setError(err instanceof Error ? err.message : 'Failed to download CV');
    } finally {
      setIsDownloading(null);
    }
  };
  
  return (
    <div className="min-h-screen pt-20 pb-12 relative">
      <FloatingParticles />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 animate-fade-in">
          <div>
            <h1 className="text-4xl font-bold mb-2">
              Your <span className="gradient-text">CVs</span>
            </h1>
            <p className="text-white/80">
              Manage, edit and download your generated CVs
            </p>
          </div>
          
          <Link 
            to="/app"
            className="mt-4 md:mt-0 gradient-button text-black font-semibold py-3 px-4 rounded-lg flex items-center justify-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create New CV</span>
          </Link>
        </div>
        
        {error && (
          <div className="mb-8">
            <ErrorDisplay 
              title="Error" 
              message={error} 
              onRetry={() => {
                setError(null);
                loadCVs();
              }} 
            />
          </div>
        )}
        
        <div className="glass-effect p-4 md:p-6 rounded-2xl animate-fade-in mb-6">
          <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
            {/* Search Form */}
            <form 
              onSubmit={handleSearch} 
              className="flex-1 flex items-center glass-effect p-2 rounded-lg"
            >
              <input
                type="text"
                placeholder="Search CVs..."
                className="bg-transparent border-none focus:outline-none text-white w-full px-3 py-1"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                type="submit"
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <Search className="w-5 h-5 text-white/80" />
              </button>
            </form>
            
            {/* Filters */}
            <div className="flex space-x-2">
              <div className="text-white/60 flex items-center px-2">
                <Filter className="w-4 h-4 mr-2" />
                <span>Status:</span>
              </div>
              
              <div className="flex space-x-1">
                <button
                  onClick={() => handleFilterChange('')}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    statusFilter === '' 
                      ? 'bg-white/20 text-white' 
                      : 'text-white/60 hover:bg-white/10'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => handleFilterChange('success')}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    statusFilter === 'success' 
                      ? 'bg-green-500/30 text-green-300' 
                      : 'text-white/60 hover:bg-white/10'
                  }`}
                >
                  Completed
                </button>
                <button
                  onClick={() => handleFilterChange('processing')}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    statusFilter === 'processing' 
                      ? 'bg-yellow-500/30 text-yellow-300' 
                      : 'text-white/60 hover:bg-white/10'
                  }`}
                >
                  Processing
                </button>
              </div>
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={() => loadCVs()}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white/80"
              aria-label="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <div className="glass-effect p-12 rounded-2xl animate-fade-in flex justify-center">
            <LoadingSpinner size="lg" text="Loading your CVs..." />
          </div>
        ) : cvs.length === 0 ? (
          <div className="glass-effect p-12 rounded-2xl animate-fade-in text-center">
            <File className="w-16 h-16 mx-auto mb-4 text-white/40" />
            <h3 className="text-xl font-semibold mb-2">No CVs Found</h3>
            <p className="text-white/70 mb-6">
              {searchQuery || statusFilter
                ? "No CVs match your search criteria."
                : "You haven't created any CVs yet."}
            </p>
            <Link
              to="/app"
              className="gradient-button text-black font-semibold py-2 px-4 rounded-lg inline-flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Create Your First CV</span>
            </Link>
          </div>
        ) : (
          <>
            <div className="grid gap-4">
              {cvs.map((cv) => (
                <div
                  key={cv.uuid}
                  className="glass-effect p-4 rounded-xl animate-fade-in hover:bg-white/5 transition-all"
                >
                  <div className="flex flex-col md:flex-row md:items-center">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        {statusIcons[cv.status as keyof typeof statusIcons] || <Clock className="w-4 h-4" />}
                        <h3 className="text-lg font-semibold ml-2">{cv.title}</h3>
                      </div>
                      
                      <div className="text-sm text-white/70 flex flex-col md:flex-row md:items-center space-y-1 md:space-y-0 md:space-x-3">
                        <span>Created: {formatDate(cv.created_at)}</span>
                        <span className="hidden md:inline">•</span>
                        <span>Template: {cv.template_name.replace('_', ' ')}</span>
                        <span className="hidden md:inline">•</span>
                        <span className="capitalize">Status: {cv.status}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 mt-4 md:mt-0">
                      <Link
                        to={`/edit/${cv.uuid}`}
                        className="p-2 rounded-lg text-white/80 hover:bg-white/10 transition-colors"
                        aria-label="Edit"
                      >
                        <Edit className="w-5 h-5" />
                      </Link>
                      
                      {cv.has_pdf && (
                        <button
                          onClick={() => handleDownloadCV(cv.uuid, cv.title)}
                          disabled={isDownloading === cv.uuid}
                          className="p-2 rounded-lg text-white/80 hover:bg-white/10 transition-colors disabled:opacity-50"
                          aria-label="Download"
                        >
                          {isDownloading === cv.uuid ? (
                            <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
                          ) : (
                            <Download className="w-5 h-5" />
                          )}
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDeleteCV(cv.uuid)}
                        disabled={isDeleting === cv.uuid}
                        className="p-2 rounded-lg text-white/80 hover:bg-red-500/20 hover:text-red-400 transition-colors disabled:opacity-50"
                        aria-label="Delete"
                      >
                        {isDeleting === cv.uuid ? (
                          <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center mt-8">
                <div className="glass-effect rounded-lg flex items-center">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="p-2 text-white/80 hover:bg-white/10 transition-colors rounded-l-lg disabled:opacity-50"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  
                  <div className="px-4 py-2 text-white/90">
                    Page {currentPage} of {totalPages}
                  </div>
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="p-2 text-white/80 hover:bg-white/10 transition-colors rounded-r-lg disabled:opacity-50"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CVListPage;