import { apiRequest } from './apiClient';
import { UserProfile } from './authService';

export interface UserStatistics {
  subscription_tier: string;
  monthly_generations: {
    used: number;
    limit: number;
    reset_date: string;
  };
  total_cvs: number;
  account_created: string;
}

export interface UserProfileUpdateRequest {
  display_name?: string;
}

const userService = {
  /**
   * Get user profile
   */
  getProfile: async (): Promise<{ user: UserProfile }> => {
    return apiRequest<{ user: UserProfile }>({
      method: 'GET',
      url: '/users/profile'
    });
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: UserProfileUpdateRequest): Promise<{ user: UserProfile }> => {
    return apiRequest<{ user: UserProfile }>({
      method: 'PUT',
      url: '/users/profile',
      data
    });
  },

  /**
   * Get user statistics
   */
  getStatistics: async (): Promise<UserStatistics> => {
    return apiRequest<UserStatistics>({
      method: 'GET',
      url: '/users/statistics'
    });
  }
};

export default userService;