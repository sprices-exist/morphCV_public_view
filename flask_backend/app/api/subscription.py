from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, User, UserTier
from app.services.payment_service import PaymentService
from app.utils.decorators import jwt_required, validate_json
from app.utils.validators import SubscriptionCreateSchema, format_validation_errors
from marshmallow import ValidationError
import stripe
import logging

# Create blueprint
subscription_bp = Blueprint('subscription', __name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
# payment_service = PaymentService()

# Validation schemas
subscription_create_schema = SubscriptionCreateSchema()

logger = logging.getLogger(__name__)


@subscription_bp.route('', methods=['GET'])
@jwt_required
def get_subscription_status():
    payment_service = PaymentService()

    """Get current user's subscription status."""
    try:
        current_user = request.current_user
        
        # Get subscription details from Stripe if customer exists
        subscription_details = None
        if current_user.stripe_customer_id:
            subscription_details = payment_service.get_customer_subscription(
                current_user.stripe_customer_id
            )
        
        return jsonify({
            'user_tier': current_user.user_tier.value,
            'generations_left': current_user.generations_left,
            'subscription_status': current_user.subscription_status,
            'subscription_current_period_end': current_user.subscription_current_period_end.isoformat() if current_user.subscription_current_period_end else None,
            'stripe_customer_id': current_user.stripe_customer_id,
            'subscription_details': subscription_details
        }), 200
        
    except Exception as e:
        logger.error(f'Get subscription status error: {str(e)}')
        return jsonify({
            'error': 'Failed to get subscription status',
            'message': 'An error occurred while fetching subscription information'
        }), 500


@subscription_bp.route('/checkout', methods=['POST'])
@jwt_required
@limiter.limit("5 per minute")
@validate_json
def create_checkout_session():
    payment_service = PaymentService()

    """
    Create Stripe checkout session for subscription.
    
    Expected payload:
    {
        "price_id": "price_1234567890",
        "success_url": "https://yourapp.com/success",
        "cancel_url": "https://yourapp.com/cancel"
    }
    """
    try:
        current_user = request.current_user
        
        # Validate request data
        try:
            checkout_data = subscription_create_schema.load(request.get_json())
        except ValidationError as e:
            return jsonify(format_validation_errors(e.messages)), 400
        
        # Ensure user has a Stripe customer ID
        if not current_user.stripe_customer_id:
            customer = payment_service.create_customer(
                email=current_user.email,
                name=current_user.name,
                user_id=current_user.id
            )
            
            if not customer:
                return jsonify({
                    'error': 'Failed to create customer',
                    'message': 'Unable to create payment customer'
                }), 500
            
            current_user.stripe_customer_id = customer['id']
            db.session.commit()
        
        # Create checkout session
        session = payment_service.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=checkout_data['price_id'],
            success_url=checkout_data.get('success_url', f"{request.host_url}success"),
            cancel_url=checkout_data.get('cancel_url', f"{request.host_url}cancel"),
            user_id=current_user.id
        )
        
        if not session:
            return jsonify({
                'error': 'Failed to create checkout session',
                'message': 'Unable to create payment session'
            }), 500
        
        logger.info(f'Created checkout session for user {current_user.id}')
        
        return jsonify({
            'checkout_session_id': session['id'],
            'checkout_url': session['url'],
            'session_expires_at': session['expires_at']
        }), 201
        
    except Exception as e:
        logger.error(f'Create checkout session error: {str(e)}')
        return jsonify({
            'error': 'Failed to create checkout session',
            'message': 'An error occurred while creating checkout session'
        }), 500


@subscription_bp.route('/portal', methods=['POST'])
@jwt_required
@limiter.limit("5 per minute")
def create_customer_portal():
    payment_service = PaymentService()

    """
    Create Stripe customer portal session for subscription management.
    
    Expected payload:
    {
        "return_url": "https://yourapp.com/dashboard"
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json() or {}
        
        if not current_user.stripe_customer_id:
            return jsonify({
                'error': 'No subscription found',
                'message': 'You need to have an active subscription to access the portal'
            }), 404
        
        # Create customer portal session
        portal_session = payment_service.create_customer_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=data.get('return_url', f"{request.host_url}dashboard")
        )
        
        if not portal_session:
            return jsonify({
                'error': 'Failed to create portal session',
                'message': 'Unable to create customer portal session'
            }), 500
        
        logger.info(f'Created customer portal session for user {current_user.id}')
        
        return jsonify({
            'portal_url': portal_session['url']
        }), 201
        
    except Exception as e:
        logger.error(f'Create customer portal error: {str(e)}')
        return jsonify({
            'error': 'Failed to create customer portal',
            'message': 'An error occurred while creating customer portal'
        }), 500


@subscription_bp.route('/webhook', methods=['POST'])
@limiter.limit("100 per minute")
def stripe_webhook():
    payment_service = PaymentService()

    """
    Handle Stripe webhooks for subscription events.
    """
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            logger.warning('Missing Stripe-Signature header')
            return jsonify({'error': 'Missing signature'}), 400
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
            )
        except ValueError:
            logger.error('Invalid payload in webhook')
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            logger.error('Invalid signature in webhook')
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        event_type = event['type']
        event_data = event['data']['object']
        
        logger.info(f'Received Stripe webhook: {event_type}')
        
        if event_type == 'customer.subscription.created':
            payment_service.handle_subscription_created(event_data)
        elif event_type == 'customer.subscription.updated':
            payment_service.handle_subscription_updated(event_data)
        elif event_type == 'customer.subscription.deleted':
            payment_service.handle_subscription_cancelled(event_data)
        elif event_type == 'invoice.payment_succeeded':
            payment_service.handle_payment_succeeded(event_data)
        elif event_type == 'invoice.payment_failed':
            payment_service.handle_payment_failed(event_data)
        elif event_type == 'customer.created':
            payment_service.handle_customer_created(event_data)
        elif event_type == 'customer.updated':
            payment_service.handle_customer_updated(event_data)
        else:
            logger.info(f'Unhandled webhook event type: {event_type}')
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f'Stripe webhook error: {str(e)}')
        return jsonify({
            'error': 'Webhook processing failed',
            'message': 'An error occurred while processing the webhook'
        }), 500


@subscription_bp.route('/prices', methods=['GET'])
def get_subscription_prices():
    payment_service = PaymentService()

    """Get available subscription prices from Stripe."""
    try:
        prices = payment_service.get_subscription_prices()
        
        if prices is None:
            return jsonify({
                'error': 'Failed to fetch prices',
                'message': 'Unable to retrieve subscription prices'
            }), 500
        
        return jsonify({
            'prices': prices
        }), 200
        
    except Exception as e:
        logger.error(f'Get subscription prices error: {str(e)}')
        return jsonify({
            'error': 'Failed to get prices',
            'message': 'An error occurred while fetching subscription prices'
        }), 500


@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required
@limiter.limit("5 per minute")
def cancel_subscription():
    payment_service = PaymentService()

    """
    Cancel current subscription.
    
    Expected payload:
    {
        "cancel_at_period_end": true,
        "reason": "Not satisfied with service"
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json() or {}
        
        if not current_user.subscription_id:
            return jsonify({
                'error': 'No active subscription',
                'message': 'You do not have an active subscription to cancel'
            }), 404
        
        cancel_at_period_end = data.get('cancel_at_period_end', True)
        reason = data.get('reason', 'Customer requested cancellation')
        
        # Cancel subscription
        result = payment_service.cancel_subscription(
            subscription_id=current_user.subscription_id,
            cancel_at_period_end=cancel_at_period_end,
            reason=reason
        )
        
        if not result:
            return jsonify({
                'error': 'Failed to cancel subscription',
                'message': 'Unable to cancel subscription'
            }), 500
        
        logger.info(f'Cancelled subscription for user {current_user.id}')
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'cancel_at_period_end': cancel_at_period_end,
            'effective_date': result.get('current_period_end')
        }), 200
        
    except Exception as e:
        logger.error(f'Cancel subscription error: {str(e)}')
        return jsonify({
            'error': 'Failed to cancel subscription',
            'message': 'An error occurred while cancelling subscription'
        }), 500


@subscription_bp.route('/reactivate', methods=['POST'])
@jwt_required
@limiter.limit("5 per minute")
def reactivate_subscription():
    payment_service = PaymentService()

    """Reactivate a cancelled subscription (if still in current period)."""
    try:
        current_user = request.current_user
        
        if not current_user.subscription_id:
            return jsonify({
                'error': 'No subscription found',
                'message': 'You do not have a subscription to reactivate'
            }), 404
        
        # Reactivate subscription
        result = payment_service.reactivate_subscription(current_user.subscription_id)
        
        if not result:
            return jsonify({
                'error': 'Failed to reactivate subscription',
                'message': 'Unable to reactivate subscription'
            }), 500
        
        logger.info(f'Reactivated subscription for user {current_user.id}')
        
        return jsonify({
            'message': 'Subscription reactivated successfully',
            'subscription_status': result.get('status'),
            'current_period_end': result.get('current_period_end')
        }), 200
        
    except Exception as e:
        logger.error(f'Reactivate subscription error: {str(e)}')
        return jsonify({
            'error': 'Failed to reactivate subscription',
            'message': 'An error occurred while reactivating subscription'
        }), 500


@subscription_bp.route('/usage', methods=['GET'])
@jwt_required
def get_usage_statistics():
    payment_service = PaymentService()

    """Get current billing period usage statistics."""
    try:
        current_user = request.current_user
        
        # Get CV statistics for current user
        from app.services.cv_service import CVService
        cv_service = CVService()
        cv_stats = cv_service.get_user_cv_statistics(current_user.id)
        
        # Calculate usage based on subscription tier
        usage_stats = {
            'user_tier': current_user.user_tier.value,
            'generations_used': cv_stats['total_cvs'],
            'generations_left': current_user.generations_left,
            'successful_generations': cv_stats['successful_cvs'],
            'failed_generations': cv_stats['failed_cvs'],
            'success_rate': cv_stats['success_rate'],
            'most_used_template': cv_stats['most_used_template'],
            'average_generation_time': cv_stats['average_generation_time']
        }
        
        # Add tier-specific limits
        if current_user.user_tier == UserTier.FREE:
            usage_stats.update({
                'generation_limit': 2,
                'unlimited_generations': False,
                'can_edit_cvs': False,
                'has_priority_support': False
            })
        elif current_user.user_tier == UserTier.PRO:
            usage_stats.update({
                'generation_limit': None,
                'unlimited_generations': True,
                'can_edit_cvs': True,
                'has_priority_support': False
            })
        elif current_user.user_tier == UserTier.ENTERPRISE:
            usage_stats.update({
                'generation_limit': None,
                'unlimited_generations': True,
                'can_edit_cvs': True,
                'has_priority_support': True,
                'has_batch_generation': True
            })
        
        return jsonify(usage_stats), 200
        
    except Exception as e:
        logger.error(f'Get usage statistics error: {str(e)}')
        return jsonify({
            'error': 'Failed to get usage statistics',
            'message': 'An error occurred while fetching usage information'
        }), 500


# Error handlers specific to subscription routes
@subscription_bp.errorhandler(429)
def subscription_rate_limit_exceeded(error):
    payment_service = PaymentService()

    """Handle rate limit exceeded for subscription routes."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many subscription requests. Please try again later.',
        'retry_after': error.retry_after
    }), 429
