import { apiRequest } from './apiClient';

export interface SubscriptionStatus {
  user_tier: string;
  generations_left: number;
  subscription_status?: string;
  subscription_current_period_end?: string;
  stripe_customer_id?: string;
  subscription_details?: any;
}

export interface CheckoutSessionRequest {
  price_id: string;
  success_url?: string;
  cancel_url?: string;
}

export interface CheckoutSessionResponse {
  checkout_session_id: string;
  checkout_url: string;
  session_expires_at: number;
}

export interface CustomerPortalRequest {
  return_url?: string;
}

export interface CustomerPortalResponse {
  portal_url: string;
}

export interface PriceData {
  id: string;
  name: string;
  currency: string;
  unit_amount: number;
  recurring: {
    interval: string;
    interval_count: number;
  };
  features: string[];
  metadata: Record<string, string>;
}

export interface PricesResponse {
  prices: PriceData[];
}

const subscriptionService = {
  /**
   * Get user's subscription status
   */
  getSubscriptionStatus: async (): Promise<SubscriptionStatus> => {
    return apiRequest<SubscriptionStatus>({
      method: 'GET',
      url: '/subscription'
    });
  },

  /**
   * Create Stripe checkout session for subscription
   */
  createCheckoutSession: async (data: CheckoutSessionRequest): Promise<CheckoutSessionResponse> => {
    return apiRequest<CheckoutSessionResponse>({
      method: 'POST',
      url: '/subscription/checkout',
      data
    });
  },

  /**
   * Create Stripe customer portal session
   */
  createCustomerPortal: async (data?: CustomerPortalRequest): Promise<CustomerPortalResponse> => {
    return apiRequest<CustomerPortalResponse>({
      method: 'POST',
      url: '/subscription/portal',
      data: data || {}
    });
  },

  /**
   * Get available subscription prices
   */
  getPrices: async (): Promise<PricesResponse> => {
    return apiRequest<PricesResponse>({
      method: 'GET',
      url: '/subscription/prices'
    });
  }
};

export default subscriptionService;