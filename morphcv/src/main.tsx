import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ErrorBoundary } from './components/ErrorBoundary.tsx';
import './index.css';
import App from './App.tsx';
import { GoogleOAuthProvider } from '@react-oauth/google';

// Your Google Client ID from the .env file
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </GoogleOAuthProvider>
  </StrictMode>
);