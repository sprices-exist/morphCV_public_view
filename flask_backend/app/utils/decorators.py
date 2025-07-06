from functools import wraps
from flask import request, jsonify, current_app
from app.services.auth_service import AuthService
from app.models import User, UserTier
import logging

logger = logging.getLogger(__name__)


def jwt_required(f):
    """
    Decorator to require valid JWT token for route access.
    
    Adds the following to the request object:
    - request.current_user: User object
    - request.token_claims: JWT payload
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Missing Authorization header',
                'message': 'Authorization header is required'
            }), 401
        
        # Extract token from "Bearer <token>" format
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid token type',
                    'message': 'Authorization header must be in format: Bearer <token>'
                }), 401
        except ValueError:
            return jsonify({
                'error': 'Invalid Authorization header format',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401
        
        # Validate token
        auth_service = AuthService()
        user, payload = auth_service.validate_user_token(token, 'access')
        
        if not user or not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'message': 'Please login again'
            }), 401
        
        # Add user and token info to request
        request.current_user = user
        request.token_claims = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def subscription_required(tier=UserTier.PRO):
    """
    Decorator to require specific subscription tier.
    
    Args:
        tier (UserTier): Minimum required subscription tier
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This decorator should be used after jwt_required
            if not hasattr(request, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'This decorator requires jwt_required to be applied first'
                }), 500
            
            user = request.current_user
            
            # Define tier hierarchy
            tier_levels = {
                UserTier.FREE: 0,
                UserTier.PRO: 1,
                UserTier.ENTERPRISE: 2
            }
            
            user_level = tier_levels.get(user.user_tier, 0)
            required_level = tier_levels.get(tier, 1)
            
            if user_level < required_level:
                return jsonify({
                    'error': 'Subscription required',
                    'message': f'This feature requires {tier.value} subscription',
                    'current_tier': user.user_tier.value,
                    'required_tier': tier.value
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json(f):
    """
    Decorator to validate that request contains valid JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type',
                'message': 'Request must contain valid JSON'
            }), 400
        
        try:
            request.get_json()
        except Exception:
            return jsonify({
                'error': 'Invalid JSON',
                'message': 'Request body contains invalid JSON'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def generation_limit_check(f):
    """
    Decorator to check if user can generate CVs based on their tier and remaining generations.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This decorator should be used after jwt_required
        if not hasattr(request, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'This decorator requires jwt_required to be applied first'
            }), 500
        
        user = request.current_user
        
        if not user.can_generate_cv():
            return jsonify({
                'error': 'Generation limit exceeded',
                'message': 'You have reached your CV generation limit',
                'generations_left': user.generations_left,
                'user_tier': user.user_tier.value,
                'upgrade_required': user.user_tier == UserTier.FREE
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges.
    Note: This is a placeholder - you would need to add admin fields to User model.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This decorator should be used after jwt_required
        if not hasattr(request, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'This decorator requires jwt_required to be applied first'
            }), 500
        
        user = request.current_user
        
        # For now, check if user has enterprise tier as admin proxy
        # In production, you'd add an is_admin field to User model
        if user.user_tier != UserTier.ENTERPRISE:
            return jsonify({
                'error': 'Admin access required',
                'message': 'This endpoint requires administrator privileges'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit_handler(f):
    """
    Decorator to handle rate limiting errors with custom responses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if 'rate limit' in str(e).lower():
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': getattr(e, 'retry_after', 60)
                }), 429
            raise e
    
    return decorated_function


def log_request(f):
    """
    Decorator to log API requests for monitoring and debugging.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request info
        user_id = None
        if hasattr(request, 'current_user'):
            user_id = request.current_user.id
        
        logger.info(
            f'API Request: {request.method} {request.path} '
            f'- User: {user_id} - IP: {request.remote_addr}'
        )
        
        try:
            response = f(*args, **kwargs)
            
            # Log response status if it's a tuple
            if isinstance(response, tuple):
                status_code = response[1]
                logger.info(f'API Response: {status_code} for {request.path}')
            
            return response
            
        except Exception as e:
            logger.error(f'API Error: {str(e)} for {request.path}')
            raise e
    
    return decorated_function


def cors_headers(f):
    """
    Decorator to add CORS headers to response.
    Note: This is mainly for development - use Flask-CORS in production.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # If response is a tuple, get the response object
        if isinstance(response, tuple):
            resp_obj, status_code = response
            if hasattr(resp_obj, 'headers'):
                response_obj = resp_obj
            else:
                # Create response object
                from flask import make_response
                response_obj = make_response(resp_obj, status_code)
        else:
            response_obj = response
        
        # Add CORS headers
        if hasattr(response_obj, 'headers'):
            response_obj.headers['Access-Control-Allow-Origin'] = '*'
            response_obj.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response_obj.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response_obj
    
    return decorated_function
