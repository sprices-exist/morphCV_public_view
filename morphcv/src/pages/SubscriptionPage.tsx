import React, { useState, useEffect } from 'react';
import { ArrowRight, Check, Zap, Star, Shield, Award, CreditCard, Clock } from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';
import { subscriptionService } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import ErrorDisplay from '../components/shared/ErrorDisplay';

interface PriceCard {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  popular?: boolean;
}

const defaultPrices: PriceCard[] = [
  {
    id: 'price_free',
    name: 'Free',
    price: 0,
    currency: 'USD',
    interval: 'month',
    features: [
      '2 CV generations per month',
      'Basic templates',
      'PDF and JPG export',
      'Standard editing tools'
    ]
  },
  {
    id: 'price_1RbepXRqEUkwwhOpBGL5tWsR',
    name: 'Pro',
    price: 9.99,
    currency: 'USD',
    interval: 'month',
    features: [
      'Unlimited CV generations',
      'All premium templates',
      'PDF and JPG export',
      'Advanced editing tools',
      'Priority support'
    ],
    popular: true
  },
  {
    id: 'price_1RbeqcRqEUkwwhOpXRFUfiMu',
    name: 'Enterprise',
    price: 29.99,
    currency: 'USD',
    interval: 'month',
    features: [
      'Unlimited CV generations',
      'All premium templates',
      'PDF, JPG, and DOCX export',
      'Advanced editing tools',
      'Priority support',
      'Team management',
      'White-label PDFs'
    ]
  }
];

const SubscriptionPage = () => {
  const { user, refreshUser } = useAuth();
  
  // State
  const [prices, setPrices] = useState<PriceCard[]>(defaultPrices);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Load subscription data
  useEffect(() => {
    loadSubscriptionData();
  }, []);
  
  const loadSubscriptionData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load subscription status
      const status = await subscriptionService.getSubscriptionStatus();
      setSubscriptionStatus(status);
      
      // Load available prices
      const pricesResponse = await subscriptionService.getPrices();
      if (pricesResponse.prices && pricesResponse.prices.length > 0) {
        const formattedPrices = pricesResponse.prices.map(price => ({
          id: price.id,
          name: price.name,
          price: price.unit_amount / 100, // Convert from cents to dollars
          currency: price.currency.toUpperCase(),
          interval: price.recurring.interval,
          features: price.features || [],
          popular: price.metadata?.popular === 'true'
        }));
        setPrices(formattedPrices);
      }
    } catch (err) {
      console.error('Error loading subscription data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load subscription data');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubscribe = async (priceId: string) => {
    setIsProcessing(true);
    setError(null);
    
    try {
      // Create checkout session
      const session = await subscriptionService.createCheckoutSession({
        price_id: priceId,
        success_url: `${window.location.origin}/subscription?success=true`,
        cancel_url: `${window.location.origin}/subscription?canceled=true`
      });
      
      // Redirect to checkout page
      window.location.href = session.checkout_url;
    } catch (err) {
      console.error('Error creating checkout session:', err);
      setError(err instanceof Error ? err.message : 'Failed to start checkout process');
      setIsProcessing(false);
    }
  };
  
  const handleManageSubscription = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      // Create customer portal session
      const session = await subscriptionService.createCustomerPortal({
        return_url: `${window.location.origin}/subscription`
      });
      
      // Redirect to customer portal
      window.location.href = session.portal_url;
    } catch (err) {
      console.error('Error creating portal session:', err);
      setError(err instanceof Error ? err.message : 'Failed to open subscription management portal');
      setIsProcessing(false);
    }
  };
  
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };
  
  const getPriceString = (price: number, currency: string, interval: string) => {
    return price === 0 
      ? 'Free' 
      : `${currency === 'USD' ? '$' : ''}${price}/${interval}`;
  };
  
  return (
    <div className="min-h-screen pt-20 pb-12 relative">
      <FloatingParticles />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Subscription <span className="gradient-text">Plans</span>
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Choose the perfect plan for your CV needs
          </p>
        </div>
        
        {error && (
          <div className="mb-8">
            <ErrorDisplay 
              title="Error" 
              message={error} 
              onRetry={() => {
                setError(null);
                loadSubscriptionData();
              }} 
            />
          </div>
        )}
        
        {isLoading ? (
          <div className="glass-effect p-12 rounded-2xl animate-fade-in flex justify-center">
            <LoadingSpinner size="lg" text="Loading subscription information..." />
          </div>
        ) : (
          <>
            {/* Current Subscription Status */}
            {user && subscriptionStatus && (
              <div className="glass-effect p-6 rounded-2xl mb-12 animate-fade-in">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold mb-1 flex items-center">
                      <CreditCard className="w-5 h-5 mr-2 text-blue-400" />
                      Your Subscription
                    </h2>
                    <div className="space-y-1 text-white/80">
                      <p className="capitalize">
                        <strong>Plan:</strong> {subscriptionStatus.user_tier}
                      </p>
                      <p>
                        <strong>Generations Left:</strong> {
                          subscriptionStatus.user_tier === 'free' 
                            ? `${subscriptionStatus.generations_left} / month` 
                            : 'Unlimited'
                        }
                      </p>
                      {subscriptionStatus.subscription_status && (
                        <>
                          <p className="capitalize">
                            <strong>Status:</strong> {subscriptionStatus.subscription_status}
                          </p>
                          {subscriptionStatus.subscription_current_period_end && (
                            <p className="flex items-center">
                              <Clock className="w-4 h-4 mr-1 text-white/60" />
                              <span>Renews on {formatDate(subscriptionStatus.subscription_current_period_end)}</span>
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  
                  {subscriptionStatus.user_tier !== 'free' && subscriptionStatus.stripe_customer_id && (
                    <button
                      onClick={handleManageSubscription}
                      disabled={isProcessing}
                      className="mt-4 md:mt-0 glass-effect hover:bg-white/10 text-white py-2 px-4 rounded-lg transition-all flex items-center justify-center space-x-2"
                    >
                      {isProcessing ? (
                        <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
                      ) : (
                        <>
                          <span>Manage Subscription</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )}
            
            {/* Subscription Plans */}
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              {prices.map((price) => (
                <div
                  key={price.id}
                  className={`glass-effect rounded-2xl overflow-hidden transition-all duration-300 ${
                    price.popular 
                      ? 'transform md:scale-105 ring-2 ring-cyan-400' 
                      : 'hover:bg-white/5'
                  }`}
                >
                  {price.popular && (
                    <div className="bg-gradient-to-r from-cyan-500 to-green-500 text-black text-center py-1 font-semibold text-sm">
                      MOST POPULAR
                    </div>
                  )}
                  
                  <div className="p-6">
                    <h3 className="text-2xl font-bold mb-2">{price.name}</h3>
                    
                    <div className="mb-4">
                      <span className="text-4xl font-bold">
                        {price.price === 0 ? 'Free' : `$${price.price}`}
                      </span>
                      {price.price > 0 && (
                        <span className="text-white/70">/{price.interval}</span>
                      )}
                    </div>
                    
                    <ul className="space-y-3 mb-6">
                      {price.features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                          <Check className="w-5 h-5 text-green-400 mr-2 flex-shrink-0 mt-0.5" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    
                    <button
                      onClick={() => handleSubscribe(price.id)}
                      disabled={
                        isProcessing || 
                        (subscriptionStatus?.user_tier === price.name.toLowerCase()) ||
                        (price.name.toLowerCase() === 'free')
                      }
                      className={`w-full py-3 rounded-lg flex items-center justify-center space-x-2 font-semibold ${
                        price.popular
                          ? 'gradient-button text-black'
                          : 'glass-effect hover:bg-white/10 text-white'
                      } ${
                        isProcessing || 
                        (subscriptionStatus?.user_tier === price.name.toLowerCase()) ||
                        (price.name.toLowerCase() === 'free')
                          ? 'opacity-50 cursor-not-allowed' 
                          : ''
                      }`}
                    >
                      {isProcessing ? (
                        <div className={`w-5 h-5 border-2 ${
                          price.popular 
                            ? 'border-black/30 border-t-black' 
                            : 'border-white/20 border-t-white'
                        } rounded-full animate-spin`} />
                      ) : subscriptionStatus?.user_tier === price.name.toLowerCase() ? (
                        <span>Current Plan</span>
                      ) : price.name.toLowerCase() === 'free' ? (
                        <span>Default Plan</span>
                      ) : (
                        <>
                          <span>Subscribe</span>
                          <ArrowRight className="w-5 h-5" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Features Comparison */}
            <div className="glass-effect p-8 rounded-2xl animate-fade-in">
              <h2 className="text-2xl font-bold mb-6 text-center">
                Plan Features <span className="gradient-text">Comparison</span>
              </h2>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="py-4 px-2 text-left">Feature</th>
                      <th className="py-4 px-2 text-center">Free</th>
                      <th className="py-4 px-2 text-center">Pro</th>
                      <th className="py-4 px-2 text-center">Enterprise</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-white/10">
                      <td className="py-4 px-2">CV Generations</td>
                      <td className="py-4 px-2 text-center">2 per month</td>
                      <td className="py-4 px-2 text-center">Unlimited</td>
                      <td className="py-4 px-2 text-center">Unlimited</td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="py-4 px-2">Templates</td>
                      <td className="py-4 px-2 text-center">Basic Only</td>
                      <td className="py-4 px-2 text-center">All Templates</td>
                      <td className="py-4 px-2 text-center">All Templates</td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="py-4 px-2">Export Formats</td>
                      <td className="py-4 px-2 text-center">PDF, JPG</td>
                      <td className="py-4 px-2 text-center">PDF, JPG</td>
                      <td className="py-4 px-2 text-center">PDF, JPG, DOCX</td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="py-4 px-2">AI Enhancement</td>
                      <td className="py-4 px-2 text-center">Basic</td>
                      <td className="py-4 px-2 text-center">Advanced</td>
                      <td className="py-4 px-2 text-center">Premium</td>
                    </tr>
                    <tr className="border-b border-white/10">
                      <td className="py-4 px-2">Customer Support</td>
                      <td className="py-4 px-2 text-center">Email Only</td>
                      <td className="py-4 px-2 text-center">Priority Support</td>
                      <td className="py-4 px-2 text-center">Dedicated Support</td>
                    </tr>
                    <tr>
                      <td className="py-4 px-2">White-Label PDFs</td>
                      <td className="py-4 px-2 text-center">❌</td>
                      <td className="py-4 px-2 text-center">❌</td>
                      <td className="py-4 px-2 text-center">✅</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SubscriptionPage;