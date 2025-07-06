import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/shared/Navigation';
import LandingPage from './pages/LandingPage';
import MainAppPage from './pages/MainAppPage';
import GoogleLoginPage from './pages/GoogleLoginPage';
import CVEditPage from './pages/CVEditPage';
import CVListPage from './pages/CVListPage';
import SubscriptionPage from './pages/SubscriptionPage';
import ProtectedRoute from './components/shared/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';

// Import environment variable for API URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
console.log('API URL:', API_URL);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen">
          <Navigation />
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<GoogleLoginPage />} />
            
            {/* Protected Routes */}
            <Route 
              path="/app" 
              element={
                <ProtectedRoute>
                  <MainAppPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/edit" 
              element={
                <ProtectedRoute>
                  <CVListPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/edit/:uuid" 
              element={
                <ProtectedRoute>
                  <CVEditPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/subscription" 
              element={
                <ProtectedRoute>
                  <SubscriptionPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
