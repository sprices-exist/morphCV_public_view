import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'white' | 'black' | 'gradient';
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  color = 'white',
  text
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  };
  
  const colorClasses = {
    white: 'border-white/20 border-t-white',
    black: 'border-black/30 border-t-black',
    gradient: 'border-cyan-200/20 border-t-gradient'
  };
  
  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-spin`} />
      {text && <p className="mt-3 text-white/80">{text}</p>}
    </div>
  );
};

export default LoadingSpinner;