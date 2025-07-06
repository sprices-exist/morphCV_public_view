import { apiRequest } from './apiClient';

interface GoogleLoginRequest {
  token: string;
  user_info: {
    email: string;
    name: string;
    picture?: string;
    sub: string;
  }
}

interface AuthResponse {
  message: string;
  user: UserProfile;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface TokenResponse {
  message: string;
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  profile_pic?: string;
  user_tier: string;
  generations_left: number;
  subscription_status?: string;
  subscription_current_period_end?: string;
  created_at: string;
  last_login: string;
}

const authService = {
  /**
   * Login with Google OAuth token
   */
  googleLogin: async (googleData: GoogleLoginRequest): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>({
      method: 'POST',
      url: '/auth/google',
      data: googleData
    });
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    return apiRequest<TokenResponse>({
      method: 'POST',
      url: '/auth/refresh',
      data: { refresh_token: refreshToken }
    });
  },

  /**
   * Logout user
   */
  logout: async (refreshToken?: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>({
      method: 'POST',
      url: '/auth/logout',
      data: refreshToken ? { refresh_token: refreshToken } : {}
    });
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async (): Promise<{ user: UserProfile }> => {
    return apiRequest<{ user: UserProfile }>({
      method: 'GET',
      url: '/auth/me'
    });
  },

  /**
   * Verify if token is valid
   */
  verifyToken: async (): Promise<{ message: string; user_id: number; email: string; expires_at: string }> => {
    return apiRequest<{ message: string; user_id: number; email: string; expires_at: string }>({
      method: 'POST',
      url: '/auth/verify'
    });
  },

  /**
   * Revoke all tokens (logout from all devices)
   */
  revokeAllTokens: async (): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>({
      method: 'POST',
      url: '/auth/revoke-all'
    });
  }
};

export default authService;