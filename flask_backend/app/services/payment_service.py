import stripe
import logging
from datetime import datetime, timezone
from flask import current_app
from app.models import db, User, UserTier

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling Stripe payments and subscriptions."""
    
    def __init__(self):
        """Initialize Stripe with API key."""
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    def create_customer(self, email, name=None, user_id=None):
        """
        Create a new Stripe customer.
        
        Args:
            email (str): Customer email
            name (str, optional): Customer name
            user_id (int, optional): Internal user ID
            
        Returns:
            dict: Stripe customer object or None if failed
        """
        try:
            customer_data = {
                'email': email,
                'metadata': {}
            }
            
            if name:
                customer_data['name'] = name
            
            if user_id:
                customer_data['metadata']['user_id'] = str(user_id)
            
            customer = stripe.Customer.create(**customer_data)
            
            logger.info(f'Created Stripe customer {customer.id} for email {email}')
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error creating customer: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error creating customer: {str(e)}')
            return None
    
    def get_customer_subscription(self, customer_id):
        """
        Get customer's active subscription.
        
        Args:
            customer_id (str): Stripe customer ID
            
        Returns:
            dict: Subscription details or None if no active subscription
        """
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )
            
            if subscriptions.data:
                subscription = subscriptions.data[0]
                return {
                    'id': subscription.id,
                    'status': subscription.status,
                    'current_period_start': datetime.fromtimestamp(
                        subscription.current_period_start, timezone.utc
                    ).isoformat(),
                    'current_period_end': datetime.fromtimestamp(
                        subscription.current_period_end, timezone.utc
                    ).isoformat(),
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                    'plan_name': subscription.items.data[0].price.nickname,
                    'amount': subscription.items.data[0].price.unit_amount,
                    'currency': subscription.items.data[0].price.currency,
                    'interval': subscription.items.data[0].price.recurring.interval
                }
            
            return None
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error getting subscription: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error getting subscription: {str(e)}')
            return None
    
    def create_checkout_session(self, customer_id, price_id, success_url, cancel_url, user_id=None):
        """
        Create a Stripe checkout session for subscription.
        
        Args:
            customer_id (str): Stripe customer ID
            price_id (str): Stripe price ID
            success_url (str): Success redirect URL
            cancel_url (str): Cancel redirect URL
            user_id (int, optional): Internal user ID
            
        Returns:
            dict: Checkout session object or None if failed
        """
        try:
            session_data = {
                'customer': customer_id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {}
            }
            
            if user_id:
                session_data['metadata']['user_id'] = str(user_id)
            
            session = stripe.checkout.Session.create(**session_data)
            
            logger.info(f'Created checkout session {session.id} for customer {customer_id}')
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error creating checkout session: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error creating checkout session: {str(e)}')
            return None
    
    def create_customer_portal_session(self, customer_id, return_url):
        """
        Create a Stripe customer portal session.
        
        Args:
            customer_id (str): Stripe customer ID
            return_url (str): Return URL after portal session
            
        Returns:
            dict: Portal session object or None if failed
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            logger.info(f'Created customer portal session for customer {customer_id}')
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error creating portal session: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error creating portal session: {str(e)}')
            return None
    
    def get_subscription_prices(self):
        """
        Get available subscription prices from Stripe.
        
        Returns:
            list: List of available prices or None if failed
        """
        try:
            prices = stripe.Price.list(
                active=True,
                type='recurring',
                limit=20
            )
            
            formatted_prices = []
            for price in prices.data:
                # Only include prices with products that have metadata indicating they're for CV generation
                try:
                    product = stripe.Product.retrieve(price.product)
                    if product.metadata.get('service_type') == 'cv_generation':
                        formatted_prices.append({
                            'id': price.id,
                            'product_id': price.product,
                            'product_name': product.name,
                            'product_description': product.description,
                            'amount': price.unit_amount,
                            'currency': price.currency,
                            'interval': price.recurring.interval,
                            'interval_count': price.recurring.interval_count,
                            'nickname': price.nickname,
                            'tier': product.metadata.get('tier', 'unknown')
                        })
                except Exception as e:
                    logger.warning(f'Error processing price {price.id}: {str(e)}')
                    continue
            
            # Sort by amount
            formatted_prices.sort(key=lambda x: x['amount'])
            
            logger.info(f'Retrieved {len(formatted_prices)} subscription prices')
            return formatted_prices
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error getting prices: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error getting prices: {str(e)}')
            return None
    
    def cancel_subscription(self, subscription_id, cancel_at_period_end=True, reason=None):
        """
        Cancel a subscription.
        
        Args:
            subscription_id (str): Stripe subscription ID
            cancel_at_period_end (bool): Whether to cancel at period end
            reason (str, optional): Cancellation reason
            
        Returns:
            dict: Updated subscription object or None if failed
        """
        try:
            if cancel_at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                    metadata={'cancellation_reason': reason} if reason else {}
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f'Cancelled subscription {subscription_id}')
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error cancelling subscription: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error cancelling subscription: {str(e)}')
            return None
    
    def reactivate_subscription(self, subscription_id):
        """
        Reactivate a cancelled subscription.
        
        Args:
            subscription_id (str): Stripe subscription ID
            
        Returns:
            dict: Updated subscription object or None if failed
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f'Reactivated subscription {subscription_id}')
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f'Stripe error reactivating subscription: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error reactivating subscription: {str(e)}')
            return None
    
    def handle_subscription_created(self, subscription_data):
        """
        Handle subscription.created webhook event.
        
        Args:
            subscription_data (dict): Stripe subscription object
        """
        try:
            customer_id = subscription_data['customer']
            subscription_id = subscription_data['id']
            
            # Find user by Stripe customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                logger.error(f'User not found for customer {customer_id}')
                return
            
            # Update user subscription info
            user.subscription_id = subscription_id
            user.subscription_status = subscription_data['status']
            user.subscription_current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], timezone.utc
            )
            
            # Update user tier based on subscription
            tier = self._get_tier_from_subscription(subscription_data)
            if tier:
                user.user_tier = tier
                if tier in [UserTier.PRO, UserTier.ENTERPRISE]:
                    user.generations_left = 999  # Unlimited for paid tiers
            
            db.session.commit()
            
            logger.info(f'Updated user {user.id} with new subscription {subscription_id}')
            
        except Exception as e:
            logger.error(f'Error handling subscription created: {str(e)}')
            db.session.rollback()
    
    def handle_subscription_updated(self, subscription_data):
        """
        Handle subscription.updated webhook event.
        
        Args:
            subscription_data (dict): Stripe subscription object
        """
        try:
            subscription_id = subscription_data['id']
            
            # Find user by subscription ID
            user = User.query.filter_by(subscription_id=subscription_id).first()
            if not user:
                logger.error(f'User not found for subscription {subscription_id}')
                return
            
            # Update subscription info
            user.subscription_status = subscription_data['status']
            user.subscription_current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], timezone.utc
            )
            
            # Update tier if subscription changed
            tier = self._get_tier_from_subscription(subscription_data)
            if tier:
                user.user_tier = tier
                if tier in [UserTier.PRO, UserTier.ENTERPRISE]:
                    user.generations_left = 999  # Unlimited for paid tiers
            
            db.session.commit()
            
            logger.info(f'Updated subscription for user {user.id}')
            
        except Exception as e:
            logger.error(f'Error handling subscription updated: {str(e)}')
            db.session.rollback()
    
    def handle_subscription_cancelled(self, subscription_data):
        """
        Handle subscription.deleted webhook event.
        
        Args:
            subscription_data (dict): Stripe subscription object
        """
        try:
            subscription_id = subscription_data['id']
            
            # Find user by subscription ID
            user = User.query.filter_by(subscription_id=subscription_id).first()
            if not user:
                logger.error(f'User not found for subscription {subscription_id}')
                return
            
            # Downgrade user to free tier
            user.user_tier = UserTier.FREE
            user.subscription_status = 'cancelled'
            user.subscription_id = None
            user.subscription_current_period_end = None
            user.generations_left = 2  # Reset to free tier limit
            
            db.session.commit()
            
            logger.info(f'Downgraded user {user.id} to free tier after subscription cancellation')
            
        except Exception as e:
            logger.error(f'Error handling subscription cancelled: {str(e)}')
            db.session.rollback()
    
    def handle_payment_succeeded(self, invoice_data):
        """
        Handle invoice.payment_succeeded webhook event.
        
        Args:
            invoice_data (dict): Stripe invoice object
        """
        try:
            customer_id = invoice_data['customer']
            subscription_id = invoice_data['subscription']
            
            # Find user by customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                logger.error(f'User not found for customer {customer_id}')
                return
            
            # Reset generation count for paid tiers on successful payment
            if user.user_tier in [UserTier.PRO, UserTier.ENTERPRISE]:
                user.generations_left = 999  # Unlimited
            
            db.session.commit()
            
            logger.info(f'Processed successful payment for user {user.id}')
            
        except Exception as e:
            logger.error(f'Error handling payment succeeded: {str(e)}')
            db.session.rollback()
    
    def handle_payment_failed(self, invoice_data):
        """
        Handle invoice.payment_failed webhook event.
        
        Args:
            invoice_data (dict): Stripe invoice object
        """
        try:
            customer_id = invoice_data['customer']
            
            # Find user by customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                logger.error(f'User not found for customer {customer_id}')
                return
            
            # Log the failed payment for monitoring
            logger.warning(f'Payment failed for user {user.id}, customer {customer_id}')
            
            # Note: Don't immediately downgrade user - Stripe will retry payments
            # and send subscription.updated/deleted events if needed
            
        except Exception as e:
            logger.error(f'Error handling payment failed: {str(e)}')
    
    def handle_customer_created(self, customer_data):
        """
        Handle customer.created webhook event.
        
        Args:
            customer_data (dict): Stripe customer object
        """
        try:
            customer_id = customer_data['id']
            email = customer_data['email']
            
            # Find user by email and update customer ID if not set
            user = User.query.filter_by(email=email).first()
            if user and not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
                db.session.commit()
                logger.info(f'Linked customer {customer_id} to user {user.id}')
            
        except Exception as e:
            logger.error(f'Error handling customer created: {str(e)}')
            db.session.rollback()
    
    def handle_customer_updated(self, customer_data):
        """
        Handle customer.updated webhook event.
        
        Args:
            customer_data (dict): Stripe customer object
        """
        try:
            customer_id = customer_data['id']
            
            # Find user by customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                # Update user info if email changed
                if customer_data.get('email') and customer_data['email'] != user.email:
                    user.email = customer_data['email']
                
                if customer_data.get('name') and customer_data['name'] != user.name:
                    user.name = customer_data['name']
                
                db.session.commit()
                logger.info(f'Updated customer info for user {user.id}')
            
        except Exception as e:
            logger.error(f'Error handling customer updated: {str(e)}')
            db.session.rollback()
    
    def _get_tier_from_subscription(self, subscription_data):
        """
        Determine user tier from subscription data.
        
        Args:
            subscription_data (dict): Stripe subscription object
            
        Returns:
            UserTier: User tier enum value or None
        """
        try:
            # Get the price ID from the subscription
            if subscription_data.get('items') and subscription_data['items']['data']:
                price_id = subscription_data['items']['data'][0]['price']['id']
                
                # Get the product to check metadata
                price = stripe.Price.retrieve(price_id)
                product = stripe.Product.retrieve(price.product)
                
                # Check product metadata for tier information
                tier_mapping = {
                    'pro': UserTier.PRO,
                    'enterprise': UserTier.ENTERPRISE,
                    'premium': UserTier.PRO,
                    'business': UserTier.ENTERPRISE
                }
                
                tier_name = product.metadata.get('tier', '').lower()
                return tier_mapping.get(tier_name, UserTier.PRO)  # Default to PRO for paid
            
            return UserTier.PRO  # Default for any paid subscription
            
        except Exception as e:
            logger.error(f'Error determining tier from subscription: {str(e)}')
            return UserTier.PRO  # Default fallback
