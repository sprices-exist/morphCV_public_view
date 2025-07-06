import { useState, useEffect } from 'react';
import { useLocation, Link, useParams, useNavigate } from 'react-router-dom';
import { Save, Download, ArrowLeft, Edit3, Eye, User, Briefcase, Award, GraduationCap, AlertCircle } from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';
import { cvService } from '../lib/api';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import ErrorDisplay from '../components/shared/ErrorDisplay';

interface CVFormData {
  title: string;
  template_name: string;
  user_data: {
    name: string;
    email: string;
    phone: string;
    location: string;
    summary: string;
    job_title: string;
    experience: string;
    skills: string;
    education: string;
    [key: string]: any;
  };
  job_description: string;
}

const CVEditPage = () => {
  const location = useLocation();
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  
  // State
  const [cvData, setCvData] = useState<CVFormData>({
    title: 'My Professional CV',
    template_name: 'template_1',
    user_data: {
      name: '',
      email: '',
      phone: '',
      location: '',
      summary: '',
      job_title: '',
      experience: '',
      skills: '',
      education: ''
    },
    job_description: ''
  });
  
  const [originalCv, setOriginalCv] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // Load CV data from API or from location state
  useEffect(() => {
    const loadCvData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Check if we have a UUID from URL params
        if (uuid) {
          const response = await cvService.getCV(uuid);
          setOriginalCv(response.cv);
          
          // Format the data for the form
          const userData = response.cv.user_data && typeof response.cv.user_data === 'string'
            ? JSON.parse(response.cv.user_data)
            : response.cv.user_data || {};
            
          setCvData({
            title: response.cv.title || 'My Professional CV',
            template_name: response.cv.template_name || 'template_1',
            user_data: {
              name: userData.name || '',
              email: userData.email || '',
              phone: userData.phone || '',
              location: userData.location || '',
              summary: userData.summary || '',
              job_title: userData.job_title || '',
              experience: userData.experience || '',
              skills: userData.skills || '',
              education: userData.education || ''
            },
            job_description: response.cv.job_description || ''
          });
        } 
        // Check if we have data in location state
        else if (location.state?.cv) {
          setOriginalCv(location.state.cv);
          
          // Format the data for the form
          const userData = location.state.cv.user_data && typeof location.state.cv.user_data === 'string'
            ? JSON.parse(location.state.cv.user_data)
            : location.state.cv.user_data || {};
            
          setCvData({
            title: location.state.cv.title || 'My Professional CV',
            template_name: location.state.cv.template_name || 'template_1',
            user_data: {
              name: userData.name || '',
              email: userData.email || '',
              phone: userData.phone || '',
              location: userData.location || '',
              summary: userData.summary || '',
              job_title: userData.job_title || '',
              experience: userData.experience || '',
              skills: userData.skills || '',
              education: userData.education || ''
            },
            job_description: location.state.cv.job_description || ''
          });
        } else {
          // Redirect to CV list if no data
          navigate('/app');
          return;
        }
      } catch (err) {
        console.error('Error loading CV:', err);
        setError(err instanceof Error ? err.message : 'Failed to load CV data');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadCvData();
  }, [uuid, location.state, navigate]);

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('user_data.')) {
      const userField = field.split('.')[1];
      setCvData(prev => ({
        ...prev,
        user_data: {
          ...prev.user_data,
          [userField]: value
        }
      }));
    } else {
      setCvData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleSave = async () => {
    if (!originalCv || !originalCv.uuid) {
      setError('Cannot save CV: missing CV identifier');
      return;
    }
    
    setIsSaving(true);
    setError(null);
    
    try {
      // Prepare update data
      const updateData = {
        title: cvData.title,
        template_name: cvData.template_name,
        user_data: cvData.user_data,
        job_description: cvData.job_description
      };
      
      // Call API to update CV
      const response = await cvService.updateCV(originalCv.uuid, updateData);
      
      // Update local state with response data
      setOriginalCv(response.cv);
      setIsEditing(false);
    } catch (err) {
      console.error('Error saving CV:', err);
      setError(err instanceof Error ? err.message : 'Failed to save CV');
    } finally {
      setIsSaving(false);
    }
  };

  const downloadCV = async () => {
    if (!originalCv || !originalCv.uuid) {
      setError('Cannot download CV: missing CV identifier');
      return;
    }

    setIsDownloading(true);
    setError(null); // Clear previous errors

    try {
      const blob = await cvService.prepareDownload(originalCv.uuid, 'pdf');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const fileName = originalCv.title
        ? `${originalCv.title.replace(/ /g, '_')}_${originalCv.uuid.substring(0,8)}.pdf`
        : `cv_${originalCv.uuid}.pdf`;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      setError(err instanceof Error ? err.message : 'Failed to download CV');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 pb-12 relative">
      <FloatingParticles />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/app"
                className="glass-effect p-3 rounded-lg hover:bg-white/10 transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold">
                  Edit Your <span className="gradient-text">CV</span>
                </h1>
                <p className="text-white/80 mt-2">
                  Make changes to your CV and see the results in real-time
                </p>
              </div>
            </div>
            
            {!isLoading && !error && originalCv && (
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-all ${
                    isEditing
                      ? 'bg-orange-500 text-white hover:bg-orange-600'
                      : 'glass-effect hover:bg-white/10'
                  }`}
                >
                  {isEditing ? <Eye className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
                  <span>{isEditing ? 'Preview' : 'Edit'}</span>
                </button>
                
                {isEditing && (
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="gradient-button text-black px-4 py-2 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                  >
                    {isSaving ? (
                      <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    <span>Save</span>
                  </button>
                )}
                
                <button
                  onClick={downloadCV}
                  disabled={!originalCv?.has_pdf || isDownloading || isSaving}
                  className="glass-effect px-4 py-2 rounded-lg hover:bg-white/10 transition-all flex items-center space-x-2 disabled:opacity-50"
                >
                  {isDownloading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  <span>{isDownloading ? 'Downloading...' : 'Download'}</span>
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Error display */}
        {error && (
          <div className="mb-8">
            <ErrorDisplay 
              title="Error" 
              message={error} 
              onRetry={() => {
                if (uuid) {
                  navigate(0); // Refresh the page
                } else {
                  navigate('/app');
                }
              }} 
            />
          </div>
        )}
        
        {/* Loading state */}
        {isLoading && (
          <div className="glass-effect p-12 rounded-2xl animate-fade-in flex justify-center">
            <LoadingSpinner size="lg" text="Loading CV data..." />
          </div>
        )}

        {!isLoading && !error && originalCv && (
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Edit Panel */}
            {isEditing && (
              <div className="glass-effect p-8 rounded-2xl animate-slide-in">
                <h2 className="text-2xl font-bold mb-6 flex items-center">
                  <Edit3 className="w-6 h-6 mr-3 text-blue-400" />
                  Edit Information
                </h2>
                
                <div className="space-y-6">
                  {/* CV Title */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">CV Title</label>
                    <input
                      type="text"
                      className="form-input w-full"
                      value={cvData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                    />
                  </div>
                  
                  {/* Personal Information */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center">
                      <User className="w-5 h-5 mr-2 text-green-400" />
                      Personal Information
                    </h3>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2 text-white/80">Full Name</label>
                      <input
                        type="text"
                        className="form-input w-full"
                        value={cvData.user_data.name}
                        onChange={(e) => handleInputChange('user_data.name', e.target.value)}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2 text-white/80">Email</label>
                        <input
                          type="email"
                          className="form-input w-full"
                          value={cvData.user_data.email}
                          onChange={(e) => handleInputChange('user_data.email', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2 text-white/80">Phone</label>
                        <input
                          type="tel"
                          className="form-input w-full"
                          value={cvData.user_data.phone}
                          onChange={(e) => handleInputChange('user_data.phone', e.target.value)}
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-white/80">Location</label>
                      <input
                        type="text"
                        className="form-input w-full"
                        value={cvData.user_data.location}
                        onChange={(e) => handleInputChange('user_data.location', e.target.value)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <Briefcase className="w-4 h-4 mr-2" />
                      Job Title
                    </label>
                    <input
                      type="text"
                      className="form-input w-full"
                      value={cvData.user_data.job_title}
                      onChange={(e) => handleInputChange('user_data.job_title', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Professional Summary</label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      value={cvData.user_data.summary}
                      onChange={(e) => handleInputChange('user_data.summary', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Experience</label>
                    <textarea
                      className="form-input w-full h-32 resize-none"
                      value={cvData.user_data.experience}
                      onChange={(e) => handleInputChange('user_data.experience', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <Award className="w-4 h-4 mr-2" />
                      Skills
                    </label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      value={cvData.user_data.skills}
                      onChange={(e) => handleInputChange('user_data.skills', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <GraduationCap className="w-4 h-4 mr-2" />
                      Education
                    </label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      value={cvData.user_data.education}
                      onChange={(e) => handleInputChange('user_data.education', e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Job Description (Target Role)</label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      value={cvData.job_description}
                      onChange={(e) => handleInputChange('job_description', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* CV Preview */}
            <div className={`glass-effect p-8 rounded-2xl animate-slide-in ${!isEditing ? 'lg:col-span-2' : ''}`}>
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Eye className="w-6 h-6 mr-3 text-purple-400" />
                CV Preview
              </h2>

              <div className="bg-white text-black p-8 rounded-lg shadow-lg max-h-[800px] overflow-y-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {cvData.user_data.name}
                  </h1>
                  <h2 className="text-xl text-blue-600 mb-4">{cvData.user_data.job_title}</h2>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>{cvData.user_data.email} • {cvData.user_data.phone}</p>
                    <p>{cvData.user_data.location}</p>
                  </div>
                </div>

                {cvData.user_data.summary && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Professional Summary</h3>
                    <p className="text-gray-700 leading-relaxed">{cvData.user_data.summary}</p>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Experience</h3>
                  <div className="text-gray-700 whitespace-pre-line">{cvData.user_data.experience}</div>
                </div>

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Skills</h3>
                  <p className="text-gray-700">{cvData.user_data.skills}</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Education</h3>
                  <div className="text-gray-700 whitespace-pre-line">{cvData.user_data.education}</div>
                </div>
                
                {originalCv && originalCv.has_pdf && (
                  <div className="mt-6 pt-6 border-t border-gray-200 text-center">
                    <p className="text-blue-600 text-sm">A professionally formatted PDF version is available for download</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tips */}
        {isEditing && !isLoading && !error && (
          <div className="mt-8 glass-effect p-6 rounded-2xl animate-fade-in">
            <h3 className="text-lg font-semibold mb-4 text-yellow-400">💡 Editing Tips</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-white/80">
              <div>
                <p><strong>Experience:</strong> Use bullet points and action verbs to describe your achievements.</p>
                <p><strong>Skills:</strong> List your most relevant skills first, separated by commas.</p>
              </div>
              <div>
                <p><strong>Summary:</strong> Keep it concise and highlight your unique value proposition.</p>
                <p><strong>Education:</strong> Include relevant coursework, GPA (if 3.5+), and honors.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CVEditPage;
