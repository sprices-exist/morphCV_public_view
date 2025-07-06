from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, User, TokenBlacklist
from app.services.auth_service import AuthService
from app.utils.decorators import jwt_required, validate_json
from app.utils.validators import LoginSchema, TokenRefreshSchema
from datetime import datetime, timezone
import logging

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
auth_service = AuthService()

# Validation schemas
login_schema = LoginSchema()
token_refresh_schema = TokenRefreshSchema()

logger = logging.getLogger(__name__)


@auth_bp.route('/google', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json
def google_login():
    """
    Google OAuth login endpoint.
    
    Expected payload:
    {
        "token": "google_oauth_token",
        "user_info": {
            "email": "user@example.com",
            "name": "User Name",
            "picture": "profile_pic_url",
            "sub": "google_user_id"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('token') or not data.get('user_info'):
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Both token and user_info are required'
            }), 400
        
        user_info = data['user_info']
        required_fields = ['email', 'name', 'sub']
        missing_fields = [field for field in required_fields if not user_info.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing user info fields',
                'message': f'Missing fields: {", ".join(missing_fields)}'
            }), 400
        
        # Verify token with Google (simplified for now)
        # In production, you should verify the token with Google's API
        
        # Find or create user
        user = User.query.filter_by(google_id=user_info['sub']).first()
        
        if not user:
            # Check if user exists with same email
            existing_user = User.query.filter_by(email=user_info['email']).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = user_info['sub']
                existing_user.name = user_info.get('name', existing_user.name)
                existing_user.profile_pic = user_info.get('picture', existing_user.profile_pic)
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=user_info['email'],
                    google_id=user_info['sub'],
                    name=user_info.get('name'),
                    profile_pic=user_info.get('picture')
                )
                db.session.add(user)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate JWT tokens
        access_token, refresh_token = auth_service.generate_tokens(user)
        
        logger.info(f'User {user.email} logged in successfully via Google OAuth')
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }), 200
        
    except Exception as e:
        logger.error(f'Google login error: {str(e)}')
        return jsonify({
            'error': 'Login failed',
            'message': 'An error occurred during login'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json
def refresh_token():
    """
    Refresh JWT access token using refresh token.
    
    Expected payload:
    {
        "refresh_token": "jwt_refresh_token"
    }
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'error': 'Missing refresh token',
                'message': 'Refresh token is required'
            }), 400
        
        # Validate and process refresh token
        result = auth_service.refresh_access_token(refresh_token)
        
        if result['success']:
            return jsonify({
                'message': 'Token refreshed successfully',
                'access_token': result['access_token'],
                'token_type': 'Bearer'
            }), 200
        else:
            return jsonify({
                'error': 'Token refresh failed',
                'message': result['message']
            }), 401
            
    except Exception as e:
        logger.error(f'Token refresh error: {str(e)}')
        return jsonify({
            'error': 'Token refresh failed',
            'message': 'An error occurred during token refresh'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    Logout user and blacklist tokens.
    
    Expected payload:
    {
        "refresh_token": "jwt_refresh_token"  # optional
    }
    """
    try:
        current_user = request.current_user
        token_jti = request.token_claims.get('jti')
        
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        
        # Blacklist current access token
        if token_jti:
            blacklist_entry = TokenBlacklist(
                jti=token_jti,
                user_id=current_user.id,
                token_type='access',
                expires_at=datetime.fromtimestamp(request.token_claims.get('exp'), timezone.utc)
            )
            db.session.add(blacklist_entry)
        
        # Blacklist refresh token if provided
        if refresh_token:
            result = auth_service.blacklist_refresh_token(refresh_token, current_user.id)
            if not result['success']:
                logger.warning(f'Failed to blacklist refresh token for user {current_user.id}')
        
        db.session.commit()
        
        logger.info(f'User {current_user.email} logged out successfully')
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return jsonify({
            'error': 'Logout failed',
            'message': 'An error occurred during logout'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Get current user profile information."""
    try:
        current_user = request.current_user
        
        return jsonify({
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'Get current user error: {str(e)}')
        return jsonify({
            'error': 'Failed to get user info',
            'message': 'An error occurred while fetching user information'
        }), 500


@auth_bp.route('/verify', methods=['POST'])
@jwt_required
def verify_token():
    """Verify if current access token is valid."""
    try:
        current_user = request.current_user
        
        return jsonify({
            'message': 'Token is valid',
            'user_id': current_user.id,
            'email': current_user.email,
            'expires_at': datetime.fromtimestamp(
                request.token_claims.get('exp'), timezone.utc
            ).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Token verification error: {str(e)}')
        return jsonify({
            'error': 'Token verification failed',
            'message': 'An error occurred during token verification'
        }), 500


@auth_bp.route('/revoke-all', methods=['POST'])
@jwt_required
def revoke_all_tokens():
    """Revoke all tokens for the current user (force logout from all devices)."""
    try:
        current_user = request.current_user
        
        # Get all non-expired tokens for the user
        result = auth_service.revoke_all_user_tokens(current_user.id)
        
        if result['success']:
            return jsonify({
                'message': f"Revoked {result['revoked_count']} tokens successfully"
            }), 200
        else:
            return jsonify({
                'error': 'Token revocation failed',
                'message': result['message']
            }), 500
            
    except Exception as e:
        logger.error(f'Revoke all tokens error: {str(e)}')
        return jsonify({
            'error': 'Token revocation failed',
            'message': 'An error occurred during token revocation'
        }), 500


# Error handlers specific to auth routes
@auth_bp.errorhandler(429)
def auth_rate_limit_exceeded(error):
    """Handle rate limit exceeded for auth routes."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many authentication attempts. Please try again later.',
        'retry_after': error.retry_after
    }), 429
