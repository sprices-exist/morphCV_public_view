import jwt
import uuid
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.models import db, User, TokenBlacklist
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication, JWT tokens, and user management."""
    
    def generate_tokens(self, user):
        """
        Generate access and refresh JWT tokens for a user.
        
        Args:
            user (User): User object
            
        Returns:
            tuple: (access_token, refresh_token)
        """
        now = datetime.now(timezone.utc)
        
        # Generate unique JTIs
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'user_tier': user.user_tier.value,
            'jti': access_jti,
            'type': 'access',
            'iat': now,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'jti': refresh_jti,
            'type': 'refresh',
            'iat': now,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        }
        
        # Encode tokens
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        logger.info(f'Generated tokens for user {user.id}')
        
        return access_token, refresh_token
    
    def decode_token(self, token):
        """
        Decode and validate JWT token.
        
        Args:
            token (str): JWT token string
            
        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(payload.get('jti')):
                logger.warning("Attempted use of blacklisted token")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info('Token has expired')
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f'Invalid token: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Token decode error: {str(e)}')
            return None
    
    def refresh_access_token(self, refresh_token):
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token (str): Refresh token string
            
        Returns:
            dict: Result with success status and new access token or error message
        """
        try:
            # Decode refresh token
            payload = self.decode_token(refresh_token)
            
            if not payload:
                return {'success': False, 'message': 'Invalid or expired refresh token'}
            
            if payload.get('type') != 'refresh':
                return {'success': False, 'message': 'Invalid token type'}
            
            # Get user
            user = User.query.get(payload.get('user_id'))
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Generate new access token
            now = datetime.now(timezone.utc)
            access_jti = str(uuid.uuid4())
            
            access_payload = {
                'user_id': user.id,
                'email': user.email,
                'user_tier': user.user_tier.value,
                'jti': access_jti,
                'type': 'access',
                'iat': now,
                'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            }
            
            access_token = jwt.encode(
                access_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm=current_app.config['JWT_ALGORITHM']
            )
            
            logger.info(f'Refreshed access token for user {user.id}')
            
            return {'success': True, 'access_token': access_token}
            
        except Exception as e:
            logger.error(f'Token refresh error: {str(e)}')
            return {'success': False, 'message': 'Token refresh failed'}
    
    def blacklist_refresh_token(self, refresh_token, user_id):
        """
        Blacklist a refresh token.
        
        Args:
            refresh_token (str): Refresh token to blacklist
            user_id (int): User ID for verification
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Decode token to get JTI and expiration
            payload = self.decode_token(refresh_token)
            
            if not payload:
                return {'success': False, 'message': 'Invalid token'}
            
            if payload.get('user_id') != user_id:
                return {'success': False, 'message': 'Token user mismatch'}
            
            if payload.get('type') != 'refresh':
                return {'success': False, 'message': 'Invalid token type'}
            
            # Add to blacklist
            blacklist_entry = TokenBlacklist(
                jti=payload.get('jti'),
                user_id=user_id,
                token_type='refresh',
                expires_at=datetime.fromtimestamp(payload.get('exp'), timezone.utc)
            )
            
            db.session.add(blacklist_entry)
            db.session.commit()
            
            logger.info(f'Blacklisted refresh token for user {user_id}')
            
            return {'success': True, 'message': 'Token blacklisted successfully'}
            
        except Exception as e:
            logger.error(f'Token blacklist error: {str(e)}')
            return {'success': False, 'message': 'Failed to blacklist token'}
    
    def is_token_blacklisted(self, jti):
        """
        Check if a token JTI is blacklisted.
        
        Args:
            jti (str): JWT ID to check
            
        Returns:
            bool: True if blacklisted, False otherwise
        """
        if not jti:
            return True
        
        try:
            blacklisted = TokenBlacklist.query.filter_by(jti=jti).first()
            return blacklisted is not None
        except Exception as e:
            logger.error(f'Blacklist check error: {str(e)}')
            return True  # Err on the side of caution
    
    def revoke_all_user_tokens(self, user_id):
        """
        Revoke all tokens for a specific user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Result with success status and revoked count
        """
        try:
            # This is a simplified approach - in production you might want to
            # track all issued tokens or use a different strategy
            
            # For now, we'll mark this timestamp and check it in token validation
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update user's updated_at timestamp
            # This can be used to invalidate tokens issued before this time
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f'Revoked all tokens for user {user_id}')
            
            return {'success': True, 'revoked_count': 'all', 'message': 'All tokens revoked'}
            
        except Exception as e:
            logger.error(f'Token revocation error: {str(e)}')
            return {'success': False, 'message': 'Failed to revoke tokens'}
    
    def validate_user_token(self, token, required_type='access'):
        """
        Validate token and return user if valid.
        
        Args:
            token (str): JWT token string
            required_type (str): Required token type ('access' or 'refresh')
            
        Returns:
            tuple: (user, payload) if valid, (None, None) if invalid
        """
        try:
            # Decode token
            payload = self.decode_token(token)
            
            if not payload:
                return None, None
            
            # Check token type
            if payload.get('type') != required_type:
                logger.warning(f'Invalid token type: expected {required_type}, got {payload.get("type")}')
                return None, None
            
            # Get user
            user = User.query.get(payload.get('user_id'))
            if not user:
                logger.warning(f'User not found for token: {payload.get("user_id")}')
                return None, None
            
            # Additional validation: check if token was issued before user's last update
            # This helps with the "revoke all tokens" functionality
            token_issued_at = datetime.fromtimestamp(payload.get('iat'), timezone.utc)
            if token_issued_at < user.updated_at:
                logger.info(f'Token issued before user update, considering invalid')
                return None, None
            
            return user, payload
            
        except Exception as e:
            logger.error(f'Token validation error: {str(e)}')
            return None, None
    
    def cleanup_expired_tokens(self):
        """
        Clean up expired blacklisted tokens.
        This should be run periodically as a maintenance task.
        """
        try:
            now = datetime.now(timezone.utc)
            expired_tokens = TokenBlacklist.query.filter(
                TokenBlacklist.expires_at < now
            ).all()
            
            count = len(expired_tokens)
            
            for token in expired_tokens:
                db.session.delete(token)
            
            db.session.commit()
            
            logger.info(f'Cleaned up {count} expired blacklisted tokens')
            
            return {'success': True, 'cleaned_count': count}
            
        except Exception as e:
            logger.error(f'Token cleanup error: {str(e)}')
            return {'success': False, 'message': 'Cleanup failed'}
