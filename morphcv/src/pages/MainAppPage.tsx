import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Download, Edit, Sparkles, User, Briefcase, GraduationCap, Award, AlertCircle } from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';
import { cvService } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import TemplateSelector from '../components/MainApp/TemplateSelector';
import StatusTracker from '../components/MainApp/StatusTracker';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import ErrorDisplay from '../components/shared/ErrorDisplay';

interface CVFormData {
  title: string;
  template_name: string;
  personalInfo: {
    name: string;
    email: string;
    phone: string;
    location: string;
    summary: string;
  };
  jobTitle: string;
  experience: string;
  skills: string;
  education: string;
  jobDescription: string;
}

const MainAppPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Form data
  const [formData, setFormData] = useState<CVFormData>({
    title: 'My Professional CV',
    template_name: 'template_1',
    personalInfo: {
      name: user?.name || '',
      email: user?.email || '',
      phone: '',
      location: '',
      summary: ''
    },
    jobTitle: '',
    experience: '',
    skills: '',
    education: '',
    jobDescription: 'Looking for a professional position that utilizes my skills and experience.'
  });
  
  // CV generation state
  const [generatedCV, setGeneratedCV] = useState<any | null>(null);
  const [generatingCvId, setGeneratingCvId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generationComplete, setGenerationComplete] = useState(false);
  
  // Status display state
  const [showTemplate, setShowTemplate] = useState(false);
  
  // Prefill user data when available
  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        personalInfo: {
          ...prev.personalInfo,
          name: user.name || prev.personalInfo.name,
          email: user.email || prev.personalInfo.email
        }
      }));
    }
  }, [user]);

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('personalInfo.')) {
      const personalField = field.split('.')[1];
      setFormData(prev => ({
        ...prev,
        personalInfo: {
          ...prev.personalInfo,
          [personalField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };
  
  const handleTemplateChange = (template: string) => {
    setFormData(prev => ({
      ...prev,
      template_name: template
    }));
  };
  
  const toggleTemplateSelector = () => {
    setShowTemplate(!showTemplate);
  };

  const generateCV = async () => {
    setIsGenerating(true);
    setError(null);
    
    try {
      // Format the data for the API
      const apiData = {
        title: formData.title,
        template_name: formData.template_name,
        user_data: {
          name: formData.personalInfo.name,
          email: formData.personalInfo.email,
          phone: formData.personalInfo.phone,
          location: formData.personalInfo.location,
          summary: formData.personalInfo.summary,
          job_title: formData.jobTitle,
          experience: formData.experience,
          skills: formData.skills,
          education: formData.education
        },
        job_description: formData.jobDescription
      };
      
      // Call the API to create a CV
      const response = await cvService.createCV(apiData);
      
      // Set the generating CV ID for status tracking
      setGeneratingCvId(response.cv.uuid);
      
    } catch (err) {
      console.error('CV generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to start CV generation');
      setIsGenerating(false);
    }
  };
  
  const handleGenerationComplete = async () => {
    setIsGenerating(false);
    setGenerationComplete(true);
    
    if (generatingCvId) {
      try {
        // Fetch the complete CV data
        const response = await cvService.getCV(generatingCvId);
        setGeneratedCV(response.cv);
      } catch (err) {
        console.error('Error fetching generated CV:', err);
        setError('Generated CV could not be loaded');
      }
    }
  };

  const downloadCV = async () => {
    if (!generatedCV) return;
    
    try {
      // Get direct download URL
      const downloadUrl = cvService.getDownloadUrl(generatedCV.uuid, 'pdf');
      
      // Open in new tab for download
      window.open(downloadUrl, '_blank');
      
    } catch (err) {
      console.error('Download error:', err);
      setError('Failed to download CV');
    }
  };
  
  const navigateToEdit = () => {
    if (generatedCV) {
      navigate(`/edit/${generatedCV.uuid}`);
    }
  };

  return (
    <div className="min-h-screen pt-20 pb-12 relative">
      <FloatingParticles />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Create Your Perfect <span className="gradient-text">CV</span>
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Fill in your information and let our AI create a professional resume tailored for success
          </p>
        </div>

        {error && (
          <div className="mb-8">
            <ErrorDisplay 
              title="CV Generation Error" 
              message={error} 
              onRetry={() => setError(null)} 
            />
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <div className="glass-effect p-8 rounded-2xl animate-slide-in">
            {showTemplate ? (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold">Select Template</h2>
                  <button 
                    onClick={toggleTemplateSelector}
                    className="text-white/70 hover:text-white px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                  >
                    Back to Form
                  </button>
                </div>
                
                <TemplateSelector 
                  selectedTemplate={formData.template_name} 
                  onChange={handleTemplateChange} 
                />
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold flex items-center">
                    <User className="w-6 h-6 mr-3 text-blue-400" />
                    Your Information
                  </h2>
                  
                  <button 
                    onClick={toggleTemplateSelector}
                    className="text-white/70 hover:text-white px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                  >
                    Change Template
                  </button>
                </div>
                
                <div className="space-y-6">
                  {/* CV Title */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">CV Title</label>
                    <input
                      type="text"
                      className="form-input w-full"
                      placeholder="My Professional CV"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                    />
                  </div>
                
                  {/* Personal Information */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Full Name</label>
                    <input
                      type="text"
                      className="form-input w-full"
                      placeholder="John Doe"
                      value={formData.personalInfo.name}
                      onChange={(e) => handleInputChange('personalInfo.name', e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-white/80">Email</label>
                      <input
                        type="email"
                        className="form-input w-full"
                        placeholder="john@example.com"
                        value={formData.personalInfo.email}
                        onChange={(e) => handleInputChange('personalInfo.email', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-white/80">Phone</label>
                      <input
                        type="tel"
                        className="form-input w-full"
                        placeholder="+1 (555) 123-4567"
                        value={formData.personalInfo.phone}
                        onChange={(e) => handleInputChange('personalInfo.phone', e.target.value)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Location</label>
                    <input
                      type="text"
                      className="form-input w-full"
                      placeholder="New York, NY"
                      value={formData.personalInfo.location}
                      onChange={(e) => handleInputChange('personalInfo.location', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <Briefcase className="w-4 h-4 mr-2" />
                      Job Title
                    </label>
                    <input
                      type="text"
                      className="form-input w-full"
                      placeholder="Software Engineer"
                      value={formData.jobTitle}
                      onChange={(e) => handleInputChange('jobTitle', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Professional Summary</label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      placeholder="Brief summary of your professional background..."
                      value={formData.personalInfo.summary}
                      onChange={(e) => handleInputChange('personalInfo.summary', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Experience</label>
                    <textarea
                      className="form-input w-full h-32 resize-none"
                      placeholder="Describe your work experience, achievements, and responsibilities..."
                      value={formData.experience}
                      onChange={(e) => handleInputChange('experience', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <Award className="w-4 h-4 mr-2" />
                      Skills
                    </label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      placeholder="List your relevant skills separated by commas..."
                      value={formData.skills}
                      onChange={(e) => handleInputChange('skills', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80 flex items-center">
                      <GraduationCap className="w-4 h-4 mr-2" />
                      Education
                    </label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      placeholder="Your educational background..."
                      value={formData.education}
                      onChange={(e) => handleInputChange('education', e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2 text-white/80">Job Description (Target Role)</label>
                    <textarea
                      className="form-input w-full h-24 resize-none"
                      placeholder="Paste a job description or describe the role you're targeting..."
                      value={formData.jobDescription}
                      onChange={(e) => handleInputChange('jobDescription', e.target.value)}
                    />
                    <p className="text-xs text-white/60 mt-1">
                      This helps our AI tailor your CV to match the requirements of your target role
                    </p>
                  </div>

                  <button
                    onClick={generateCV}
                    disabled={isGenerating}
                    className="w-full gradient-button text-black font-semibold py-4 rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5" />
                        <span>Generate CV</span>
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Generated CV Preview */}
          <div className="glass-effect p-8 rounded-2xl animate-slide-in">
            <h2 className="text-2xl font-bold mb-6 flex items-center justify-between">
              <span>CV Preview</span>
              {generatedCV && (
                <div className="flex space-x-3">
                  <button 
                    onClick={navigateToEdit}
                    className="glass-effect px-4 py-2 rounded-lg hover:bg-white/10 transition-all flex items-center space-x-2"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={downloadCV}
                    disabled={!generatedCV.has_pdf}
                    className="gradient-button text-black px-4 py-2 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download</span>
                  </button>
                </div>
              )}
            </h2>

            {isGenerating && generatingCvId ? (
              <div className="py-10">
                <StatusTracker 
                  cvUuid={generatingCvId} 
                  onComplete={handleGenerationComplete} 
                />
              </div>
            ) : generatedCV ? (
              <div className="bg-white text-black p-8 rounded-lg shadow-lg">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {generatedCV.user_data?.name || "Your Name"}
                  </h1>
                  <h2 className="text-xl text-blue-600 mb-4">{generatedCV.user_data?.job_title || "Job Title"}</h2>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>{generatedCV.user_data?.email || "email@example.com"} • {generatedCV.user_data?.phone || "Phone"}</p>
                    <p>{generatedCV.user_data?.location || "Location"}</p>
                  </div>
                </div>

                {generatedCV.user_data?.summary && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Professional Summary</h3>
                    <p className="text-gray-700 leading-relaxed">{generatedCV.user_data.summary}</p>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Experience</h3>
                  <div className="text-gray-700 whitespace-pre-line">{generatedCV.user_data?.experience || "Experience details"}</div>
                </div>

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Skills</h3>
                  <p className="text-gray-700">{generatedCV.user_data?.skills || "Skills list"}</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Education</h3>
                  <div className="text-gray-700 whitespace-pre-line">{generatedCV.user_data?.education || "Education details"}</div>
                </div>
                
                {generatedCV.has_pdf && (
                  <div className="mt-6 pt-6 border-t border-gray-200 text-center">
                    <p className="text-blue-600 text-sm">A professionally formatted PDF version is ready for download</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 text-white/60">
                <Sparkles className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Your generated CV will appear here</p>
                <p className="text-sm mt-2">Fill in the form and click "Generate CV" to get started</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainAppPage;
