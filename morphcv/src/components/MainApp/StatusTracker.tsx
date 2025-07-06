import React, { useEffect, useState } from 'react';
import { Check, AlertCircle, Loader } from 'lucide-react';
import { cvService } from '../../lib/api';

interface StatusTrackerProps {
  cvUuid: string;
  onComplete: () => void;
}

const StatusTracker: React.FC<StatusTrackerProps> = ({ cvUuid, onComplete }) => {
  const [status, setStatus] = useState<string>('processing');
  const [progress, setProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('Starting CV generation...');
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    let interval: number | undefined;
    
    const checkStatus = async () => {
      try {
        const response = await cvService.checkCVStatus(cvUuid);
        
        setStatus(response.status); // Set overall status (pending, processing, success, failed)

        if (response.task_status) {
          // Update progress if available
          if (typeof response.task_status.progress === 'number') {
            setProgress(response.task_status.progress);
          }

          // Update status message if a step message is available
          if (typeof response.task_status.step === 'string' && response.task_status.step.trim() !== '') {
            setStatusMessage(response.task_status.step);
          } else if (response.status === 'processing') {
            // If step is empty/null but overall status is 'processing', show a generic message
            // This check helps if task_status is present but 'step' is not informative yet
            if (statusMessage === 'Starting CV generation...') { // Only update if it's still the initial message
                 setStatusMessage('Processing, please wait...');
            }
          }
        } else if (response.status === 'processing') {
          // If task_status is null, but overall status is 'processing'
          // This means the backend acknowledges processing but hasn't provided details yet
          // Or the details are no longer provided because it's about to switch to success/failure
          if (statusMessage === 'Starting CV generation...') { // Only update if it's still the initial message
             setStatusMessage('Processing, please wait...');
          }
          // Optionally, you could set a small progress here if progress is 0, e.g., setProgress(prev => prev === 0 ? 5 : prev);
        }

        // Handle terminal states
        if (response.status === 'success') {
          clearInterval(interval);
          // Ensure final state is set before calling onComplete
          setProgress(100);
          setStatusMessage('Generation complete!');
          // Add a small delay before calling onComplete to allow React to render this final state
          setTimeout(() => {
            onComplete();
          }, 100); // 100ms delay, adjust if needed
        } else if (response.status === 'failed') {
          clearInterval(interval);
          // The error message for the span will be taken from the 'error' state variable
          // which is set in the catch block or if response.status is 'failed'.
          // We can set a specific message from response if available.
          setError(response.error_message || 'CV generation failed. Please try again.');
        }
      } catch (err) {
        console.error('Error checking CV status:', err);
        // Set a generic error message for the status display
        setError('Error checking generation status');
        if (interval) { // Ensure interval is cleared on error
            clearInterval(interval);
        }
      }
    };
    
    // Check status immediately and then every 3 seconds
    checkStatus();
    interval = window.setInterval(checkStatus, 3000);
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [cvUuid, onComplete]);
  
  const getStatusDisplay = () => {
    switch (status) {
      case 'success':
        return (
          <div className="flex items-center text-green-400">
            <Check className="w-5 h-5 mr-2" />
            <span>Generation complete!</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center text-red-400">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{error || 'Generation failed'}</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center text-blue-400">
            <Loader className="w-5 h-5 mr-2 animate-spin" />
            <span>{statusMessage}</span>
          </div>
        );
    }
  };
  
  return (
    <div className="w-full glass-effect p-6 rounded-xl">
      <div className="mb-3">
        {getStatusDisplay()}
      </div>
      
      <div className="w-full bg-white/10 rounded-full h-2.5">
        <div 
          className="bg-gradient-to-r from-cyan-400 to-green-400 h-2.5 rounded-full" 
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="mt-2 text-sm text-white/70">
        {progress}% Complete
      </div>
    </div>
  );
};

export default StatusTracker;