import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogIn, Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';
import { useAuth } from '../contexts/AuthContext';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const GoogleLoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname:string } })?.from?.pathname || '/app';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // This is the new way to handle Google Login using the hook
  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        // The new library gives an access token. Use it to get user info.
        const userInfoResponse = await axios.get(
          'https://www.googleapis.com/oauth2/v3/userinfo',
          {
            headers: {
              Authorization: `Bearer ${tokenResponse.access_token}`,
            },
          }
        );

        // We now have the user info and a token. We can proceed with our backend login.
        // NOTE: The `tokenResponse.access_token` is for Google's API.
        // For our backend, we can send this token for server-side validation if needed,
        // or just use the user info as we did before. Your backend expects `id_token`
        // which isn't directly provided here, so we'll send the user info.
        
        const userInfo = {
          email: userInfoResponse.data.email,
          name: userInfoResponse.data.name,
          picture: userInfoResponse.data.picture,
          sub: userInfoResponse.data.sub,
        };

        // Call our app's login function from the AuthContext
        // We'll pass the access_token as the "token" for our backend to potentially verify
        await login(tokenResponse.access_token, userInfo);

        navigate(from, { replace: true });

      } catch (error) {
        console.error('Google login error:', error);
        setErrorMessage('Failed to sign in with Google. Please try again.');
      } finally {
        setIsLoading(false);
      }
    },
    onError: (error) => {
      console.error('Login Failed:', error);
      setErrorMessage('Google login failed. Please check your permissions and try again.');
      setIsLoading(false);
    },
  });

  // This function is now just a simple wrapper
  const triggerGoogleLogin = () => {
    setIsLoading(true);
    // It seems handleGoogleLogin itself sets isLoading to false on error,
    // but to be safe, and for general user experience, ensure it's reset.
    // However, the useGoogleLogin hook handles its own state.
    // We primarily set isLoading true here to disable our button.
    // The hook will eventually call onSuccess or onError.
    // In onSuccess, we navigate. In onError, message is set.
    // So, direct setIsLoading(false) here might be premature if the hook is async.
    // For now, let's assume the hook manages its own loading state internally
    // for the Google interaction part, and our isLoading is for our button's state.
    handleGoogleLogin();
  };

  // Email/password login and input change handlers are removed.

  return (
    <div className="min-h-screen flex items-center justify-center relative">
      <FloatingParticles />
      <div className="max-w-md w-full mx-4 relative z-10">
        <div className="glass-effect p-8 rounded-2xl animate-fade-in">
          {/* ... (rest of your JSX is the same) ... */}
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 gradient-button rounded-full mx-auto mb-4 flex items-center justify-center">
              <LogIn className="w-8 h-8 text-black" />
            </div>
            <h1 className="text-3xl font-bold mb-2">
              Welcome to <span className="gradient-text">MorphCV</span>
            </h1>
            <p className="text-white/80">
              Sign in to your account and start creating amazing CVs
            </p>
          </div>
          
          {errorMessage && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg flex items-start">
              <AlertCircle className="w-5 h-5 text-red-400 mr-3 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-white/90">{errorMessage}</p>
            </div>
          )}

          {/* Google Login Button - now calls triggerGoogleLogin */}
          <button
            onClick={triggerGoogleLogin}
            disabled={isLoading}
            className="w-full bg-white text-gray-900 font-semibold py-4 px-6 rounded-lg mb-6 flex items-center justify-center space-x-3 hover:bg-gray-50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-gray-400 border-t-gray-900 rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            )}
            <span>Continue with Google</span>
          </button>
          
          <div className="mt-8 text-center">
            <p className="text-white/70 text-sm">
              Use your Google account to sign in or create a new account.
            </p>
          </div>

          {/* Removed email/password form and related elements */}
          {/* The "or continue with email" divider is removed. */}
          {/* The form is removed. */}
          {/* The "Don't have an account?" text is simplified above. */}

          <div className="mt-8 text-center"> {/* Increased margin-top for spacing */}
            <Link
              to="/"
              className="text-white/60 hover:text-white/80 transition-colors text-sm flex items-center justify-center space-x-1"
            >
              <span>← Back to home</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoogleLoginPage;