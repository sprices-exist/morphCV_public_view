from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, User
from app.services.cv_service import CVService
from app.utils.decorators import jwt_required, validate_json
from app.utils.validators import UserUpdateSchema, format_validation_errors
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

# Create blueprint
users_bp = Blueprint('users', __name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
cv_service = CVService()

# Validation schemas
user_update_schema = UserUpdateSchema()

logger = logging.getLogger(__name__)


@users_bp.route('/profile', methods=['GET'])
@jwt_required
def get_user_profile():
    """Get current user's complete profile information."""
    try:
        current_user = request.current_user
        
        # Get CV statistics
        cv_stats = cv_service.get_user_cv_statistics(current_user.id)
        
        profile_data = current_user.to_dict()
        profile_data['cv_statistics'] = cv_stats
        
        return jsonify({
            'user': profile_data
        }), 200
        
    except Exception as e:
        logger.error(f'Get user profile error: {str(e)}')
        return jsonify({
            'error': 'Failed to get profile',
            'message': 'An error occurred while fetching user profile'
        }), 500


@users_bp.route('/profile', methods=['PUT'])
@jwt_required
@limiter.limit("10 per hour")
@validate_json
def update_user_profile():
    """
    Update user profile information.
    
    Expected payload:
    {
        "name": "Updated Name",
        "email": "newemail@example.com"
    }
    """
    try:
        current_user = request.current_user
        
        # Validate request data
        try:
            update_data = user_update_schema.load(request.get_json())
        except ValidationError as e:
            return jsonify(format_validation_errors(e.messages)), 400
        
        # Check if email is being changed and if it's already taken
        if 'email' in update_data and update_data['email'] != current_user.email:
            existing_user = User.query.filter_by(email=update_data['email']).first()
            if existing_user:
                return jsonify({
                    'error': 'Email already taken',
                    'message': 'This email address is already registered'
                }), 409
        
        # Update user fields
        if 'name' in update_data:
            current_user.name = update_data['name']
        
        if 'email' in update_data:
            current_user.email = update_data['email']
        
        current_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f'Updated profile for user {current_user.id}')
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'Update user profile error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update profile',
            'message': 'An error occurred while updating profile'
        }), 500


@users_bp.route('/statistics', methods=['GET'])
@jwt_required
def get_user_statistics():
    """Get detailed user statistics and analytics."""
    try:
        current_user = request.current_user
        
        # Get CV statistics
        cv_stats = cv_service.get_user_cv_statistics(current_user.id)
        
        # Get recent CVs
        recent_cvs_query = cv_service.list_user_cvs(
            current_user.id, 
            {'page': 1, 'per_page': 5, 'sort_by': 'created_at', 'sort_order': 'desc'}
        )
        
        # Calculate account age
        account_age_days = (datetime.now(timezone.utc) - current_user.created_at).days
        
        statistics = {
            'account_info': {
                'user_tier': current_user.user_tier.value,
                'account_age_days': account_age_days,
                'created_at': current_user.created_at.isoformat(),
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
                'generations_left': current_user.generations_left
            },
            'cv_statistics': cv_stats,
            'recent_cvs': [cv.to_dict() for cv in recent_cvs_query['cvs']],
            'subscription_info': {
                'status': current_user.subscription_status,
                'current_period_end': current_user.subscription_current_period_end.isoformat() if current_user.subscription_current_period_end else None,
                'has_active_subscription': bool(current_user.subscription_id and current_user.subscription_status == 'active')
            }
        }
        
        return jsonify(statistics), 200
        
    except Exception as e:
        logger.error(f'Get user statistics error: {str(e)}')
        return jsonify({
            'error': 'Failed to get statistics',
            'message': 'An error occurred while fetching user statistics'
        }), 500


@users_bp.route('/preferences', methods=['GET'])
@jwt_required
def get_user_preferences():
    """Get user preferences and settings."""
    try:
        current_user = request.current_user
        
        # For now, return default preferences
        # In the future, you could add a UserPreferences model
        preferences = {
            'default_template': 'template_1',
            'email_notifications': True,
            'auto_save_drafts': True,
            'preferred_language': 'en',
            'timezone': 'UTC'
        }
        
        return jsonify({
            'preferences': preferences
        }), 200
        
    except Exception as e:
        logger.error(f'Get user preferences error: {str(e)}')
        return jsonify({
            'error': 'Failed to get preferences',
            'message': 'An error occurred while fetching user preferences'
        }), 500


@users_bp.route('/preferences', methods=['PUT'])
@jwt_required
@limiter.limit("20 per hour")
@validate_json
def update_user_preferences():
    """
    Update user preferences.
    
    Expected payload:
    {
        "default_template": "template_2",
        "email_notifications": false,
        "auto_save_drafts": true,
        "preferred_language": "en",
        "timezone": "UTC"
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json()
        
        # For now, just validate the data structure
        # In the future, you could store this in a UserPreferences model
        
        valid_templates = ['template_1', 'template_2', 'template_3', 'template_4']
        if 'default_template' in data and data['default_template'] not in valid_templates:
            return jsonify({
                'error': 'Invalid template',
                'message': f'Template must be one of: {", ".join(valid_templates)}'
            }), 400
        
        # Log preference update for now
        logger.info(f'Updated preferences for user {current_user.id}: {data}')
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': data
        }), 200
        
    except Exception as e:
        logger.error(f'Update user preferences error: {str(e)}')
        return jsonify({
            'error': 'Failed to update preferences',
            'message': 'An error occurred while updating preferences'
        }), 500


@users_bp.route('/activity', methods=['GET'])
@jwt_required
def get_user_activity():
    """Get user activity log and recent actions."""
    try:
        current_user = request.current_user
        
        # Get recent CVs with more details
        recent_activity_query = cv_service.list_user_cvs(
            current_user.id,
            {'page': 1, 'per_page': 10, 'sort_by': 'updated_at', 'sort_order': 'desc'}
        )
        
        # Format activity data
        activities = []
        for cv in recent_activity_query['cvs']:
            cv_data = cv.to_dict()
            activities.append({
                'id': cv_data['id'],
                'type': 'cv_generation' if cv_data['status'] == 'success' else 'cv_attempt',
                'title': cv_data['title'],
                'status': cv_data['status'],
                'template_used': cv_data['template_name'],
                'created_at': cv_data['created_at'],
                'updated_at': cv_data['updated_at'],
                'generation_time': cv_data['generation_time']
            })
        
        # Add login activity
        if current_user.last_login:
            activities.append({
                'id': f'login_{current_user.id}',
                'type': 'login',
                'title': 'User Login',
                'status': 'success',
                'created_at': current_user.last_login.isoformat(),
                'updated_at': current_user.last_login.isoformat()
            })
        
        # Sort by updated_at
        activities.sort(key=lambda x: x['updated_at'], reverse=True)
        
        activity_summary = {
            'total_activities': len(activities),
            'recent_activities': activities[:10],
            'activity_types': {
                'cv_generations': len([a for a in activities if a['type'] == 'cv_generation']),
                'cv_attempts': len([a for a in activities if a['type'] == 'cv_attempt']),
                'logins': len([a for a in activities if a['type'] == 'login'])
            }
        }
        
        return jsonify(activity_summary), 200
        
    except Exception as e:
        logger.error(f'Get user activity error: {str(e)}')
        return jsonify({
            'error': 'Failed to get activity',
            'message': 'An error occurred while fetching user activity'
        }), 500


@users_bp.route('/export', methods=['POST'])
@jwt_required
@limiter.limit("5 per hour")
def export_user_data():
    """
    Export user data (GDPR compliance).
    
    Expected payload:
    {
        "format": "json",  // or "csv"
        "include_cvs": true,
        "include_activity": true
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json() or {}
        
        export_format = data.get('format', 'json')
        include_cvs = data.get('include_cvs', True)
        include_activity = data.get('include_activity', True)
        
        if export_format not in ['json', 'csv']:
            return jsonify({
                'error': 'Invalid format',
                'message': 'Format must be json or csv'
            }), 400
        
        # Prepare export data
        export_data = {
            'user_profile': current_user.to_dict(),
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'export_format': export_format
        }
        
        if include_cvs:
            all_cvs_query = cv_service.list_user_cvs(
                current_user.id,
                {'page': 1, 'per_page': 1000, 'sort_by': 'created_at', 'sort_order': 'desc'}
            )
            export_data['cvs'] = [cv.to_dict(include_sensitive=True) for cv in all_cvs_query['cvs']]
        
        if include_activity:
            cv_stats = cv_service.get_user_cv_statistics(current_user.id)
            export_data['statistics'] = cv_stats
        
        logger.info(f'Exported data for user {current_user.id} in {export_format} format')
        
        return jsonify({
            'message': 'Data exported successfully',
            'export_data': export_data,
            'data_size': len(str(export_data)),
            'includes': {
                'profile': True,
                'cvs': include_cvs,
                'activity': include_activity
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Export user data error: {str(e)}')
        return jsonify({
            'error': 'Failed to export data',
            'message': 'An error occurred while exporting user data'
        }), 500


@users_bp.route('/delete-account', methods=['DELETE'])
@jwt_required
@limiter.limit("1 per day")
def delete_user_account():
    """
    Delete user account and all associated data.
    This is irreversible and for GDPR compliance.
    
    Expected payload:
    {
        "confirmation": "DELETE_MY_ACCOUNT",
        "reason": "Optional reason for deletion"
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json() or {}
        
        # Require explicit confirmation
        if data.get('confirmation') != 'DELETE_MY_ACCOUNT':
            return jsonify({
                'error': 'Invalid confirmation',
                'message': 'Please provide the exact confirmation text: DELETE_MY_ACCOUNT'
            }), 400
        
        user_id = current_user.id
        user_email = current_user.email
        
        # Delete all user CVs and files
        all_cvs_query = cv_service.list_user_cvs(
            current_user.id,
            {'page': 1, 'per_page': 1000}
        )
        
        deleted_cvs = 0
        for cv in all_cvs_query['cvs']:
            cv_service.delete_cv_files(cv)
            db.session.delete(cv)
            deleted_cvs += 1
        
        # Delete user account
        db.session.delete(current_user)
        db.session.commit()
        
        logger.warning(f'Deleted user account {user_id} ({user_email}) and {deleted_cvs} CVs. Reason: {data.get("reason", "Not provided")}')
        
        return jsonify({
            'message': 'Account deleted successfully',
            'deleted_items': {
                'user_account': 1,
                'cvs': deleted_cvs
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Delete user account error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete account',
            'message': 'An error occurred while deleting account'
        }), 500


# Error handlers specific to user routes
@users_bp.errorhandler(429)
def users_rate_limit_exceeded(error):
    """Handle rate limit exceeded for user routes."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': error.retry_after
    }), 429
