/**
 * This utility ensures environment variables are properly initialized
 * even if .env files are missing. It provides fallbacks for critical
 * configuration values.
 */

export interface EnvironmentConfig {
  apiUrl: string;
  googleClientId: string;
  isProduction: boolean;
  stripePublicKey?: string;
}

const getEnvironment = (): EnvironmentConfig => {
  // Use environment variables with fallbacks
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const stripePublicKey = import.meta.env.VITE_STRIPE_PUBLIC_KEY || '';
  const isProduction = import.meta.env.MODE === 'production';

  // Log environment status for debugging (removed in production)
  if (!isProduction) {
    console.log('Environment Config:', {
      apiUrl,
      googleClientId: googleClientId ? '[CONFIGURED]' : '[MISSING]',
      stripePublicKey: stripePublicKey ? '[CONFIGURED]' : '[MISSING]',
      mode: import.meta.env.MODE
    });
  }

  // Validate critical config
  if (!apiUrl) {
    console.error('API URL is not configured. Application may not function correctly.');
  }

  if (!googleClientId && isProduction) {
    console.error('Google Client ID is not configured. Authentication will not work correctly.');
  }

  return {
    apiUrl,
    googleClientId,
    stripePublicKey,
    isProduction
  };
};

export const environment = getEnvironment();
export default environment;