import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title = 'Error',
  message,
  onRetry
}) => {
  return (
    <div className="glass-effect p-6 rounded-xl text-center">
      <div className="flex flex-col items-center">
        <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
          <AlertCircle className="w-6 h-6 text-red-400" />
        </div>
        
        <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
        <p className="text-white/80 mb-4">{message}</p>
        
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center space-x-2 bg-white/10 hover:bg-white/20 text-white py-2 px-4 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;