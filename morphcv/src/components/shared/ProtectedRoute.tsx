import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  redirectTo = '/login'
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="glass-effect p-8 rounded-xl">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-16 h-16 border-4 border-white/20 border-t-white/80 rounded-full animate-spin"></div>
            <p className="text-lg text-white/80">Authenticating...</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Redirect if not authenticated
  if (!isAuthenticated) {
    // Save the current location they were trying to go to
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }
  
  // Render children if authenticated
  return <>{children}</>;
};

export default ProtectedRoute;