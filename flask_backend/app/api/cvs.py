from flask import Blueprint, request, jsonify, send_file, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, CV, CVStatus, DownloadToken
from app.services.cv_service import CVService
from app.tasks.cv_tasks import generate_cv_task, edit_cv_task
from app.utils.decorators import jwt_required, generation_limit_check, validate_json
from app.utils.validators import (
    CVCreateSchema, CVUpdateSchema, CVFilterSchema, 
    format_validation_errors, validate_cv_uuid
)
from marshmallow import ValidationError
from datetime import datetime, timezone, timedelta
import os
import logging

# Create blueprint
cvs_bp = Blueprint('cvs', __name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
cv_service = CVService()

# Validation schemas
cv_create_schema = CVCreateSchema()
cv_update_schema = CVUpdateSchema()
cv_filter_schema = CVFilterSchema()

logger = logging.getLogger(__name__)


@cvs_bp.route('', methods=['GET'])
@jwt_required
def list_cvs():
    """
    List user's CVs with pagination and filtering.
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - status: Filter by status
    - template_name: Filter by template
    - search: Search in title and user data
    - sort_by: Sort field (default: created_at)
    - sort_order: Sort order (default: desc)
    """
    try:
        current_user = request.current_user
        
        # Validate query parameters
        try:
            query_params = cv_filter_schema.load(request.args)
        except ValidationError as e:
            return jsonify(format_validation_errors(e.messages)), 400
        
        # Get CVs with pagination and filtering
        result = cv_service.list_user_cvs(current_user.id, query_params)
        
        return jsonify({
            'cvs': [cv.to_dict() for cv in result['cvs']],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'pages': result['pages'],
                'has_next': result['has_next'],
                'has_prev': result['has_prev']
            }
        }), 200
        
    except Exception as e:
        logger.error(f'List CVs error: {str(e)}')
        return jsonify({
            'error': 'Failed to list CVs',
            'message': 'An error occurred while fetching CVs'
        }), 500


@cvs_bp.route('', methods=['POST'])
@jwt_required
@generation_limit_check
@limiter.limit("10 per hour")
@validate_json
def create_cv():
    """
    Create a new CV.
    
    Expected payload:
    {
        "title": "My CV",
        "template_name": "template_1",
        "user_data": {
            "name": "John Doe",
            "email": "john@example.com",
            "experience": "3 years Python development",
            "skills": ["Python", "Flask", "React"],
            "education": "Computer Science Degree"
        },
        "job_description": "Looking for a Python developer..."
    }
    """
    try:
        current_user = request.current_user
        
        # Validate request data
        try:
            cv_data = cv_create_schema.load(request.get_json())
        except ValidationError as e:
            return jsonify(format_validation_errors(e.messages)), 400
        
        # Create CV record
        cv = CV(
            user_id=current_user.id,
            title=cv_data['title'],
            template_name=cv_data['template_name'],
            user_data=str(cv_data['user_data']),  # Store as JSON string
            job_description=cv_data['job_description'],
            status=CVStatus.PENDING
        )
        
        db.session.add(cv)
        db.session.commit()
        
        # Start async CV generation task
        task = generate_cv_task.delay(
            cv.id,
            cv_data['user_data'],
            cv_data['job_description'],
            cv_data['template_name'],
            current_user.user_tier.value
        )
        
        # Update CV with task ID
        cv.task_id = task.id
        cv.status = CVStatus.PROCESSING
        db.session.commit()
        
        # Use generation for free users
        current_user.use_generation()
        
        logger.info(f'Started CV generation for user {current_user.id}, CV {cv.id}')
        
        return jsonify({
            'message': 'CV generation started',
            'cv': cv.to_dict(),
            'task_id': task.id
        }), 201
        
    except Exception as e:
        logger.error(f'Create CV error: {str(e)}')
        return jsonify({
            'error': 'Failed to create CV',
            'message': 'An error occurred while creating CV'
        }), 500


@cvs_bp.route('/<cv_uuid>', methods=['GET'])
@jwt_required
def get_cv(cv_uuid):
    """Get CV details by UUID."""
    try:
        current_user = request.current_user
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to access it'
            }), 404
        
        # Include sensitive data for owner
        cv_data = cv.to_dict(include_sensitive=True)
        
        # Add download URLs if files exist
        if cv.pdf_path:
            cv_data['download_urls'] = {
                'pdf': f'/api/v1/cvs/{cv_uuid}/download?type=pdf'
            }
            if cv.jpg_path:
                cv_data['download_urls']['jpg'] = f'/api/v1/cvs/{cv_uuid}/download?type=jpg'
        
        return jsonify({'cv': cv_data}), 200
        
    except Exception as e:
        logger.error(f'Get CV error: {str(e)}')
        return jsonify({
            'error': 'Failed to get CV',
            'message': 'An error occurred while fetching CV'
        }), 500


@cvs_bp.route('/<cv_uuid>', methods=['PUT'])
@jwt_required
@limiter.limit("20 per hour")
@validate_json
def update_cv(cv_uuid):
    """
    Update/edit CV.
    
    Expected payload:
    {
        "title": "Updated CV Title",
        "user_data": {...},
        "job_description": "Updated job description",
        "edit_instructions": "Make the experience section more detailed"
    }
    """
    try:
        current_user = request.current_user
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Validate request data
        try:
            update_data = cv_update_schema.load(request.get_json())
        except ValidationError as e:
            return jsonify(format_validation_errors(e.messages)), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to edit it'
            }), 404
        
        # Check if CV is in a state that can be edited
        if cv.status in [CVStatus.PROCESSING]:
            return jsonify({
                'error': 'CV is being processed',
                'message': 'Cannot edit CV while it is being processed'
            }), 409
        
        # Update basic fields
        if 'title' in update_data:
            cv.title = update_data['title']
        
        # If this is a regeneration (has edit_instructions or new job_description)
        needs_regeneration = 'edit_instructions' in update_data or 'job_description' in update_data
        
        if needs_regeneration:
            # Update data and start regeneration task
            if 'user_data' in update_data:
                cv.user_data = str(update_data['user_data'])
            if 'job_description' in update_data:
                cv.job_description = update_data['job_description']
            
            # Start editing task
            cv.status = CVStatus.PROCESSING
            
            task = edit_cv_task.delay(
                cv.id,
                update_data.get('edit_instructions', 'Please update the CV based on the new information'),
                current_user.user_tier.value
            )
            
            cv.task_id = task.id
            
            message = 'CV editing started'
            logger.info(f'Started CV editing for user {current_user.id}, CV {cv.id}')
        else:
            # Just update metadata without regeneration
            message = 'CV updated successfully'
            logger.info(f'Updated CV metadata for user {current_user.id}, CV {cv.id}')
        
        cv.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': message,
            'cv': cv.to_dict(),
            'task_id': cv.task_id if needs_regeneration else None
        }), 200
        
    except Exception as e:
        logger.error(f'Update CV error: {str(e)}')
        return jsonify({
            'error': 'Failed to update CV',
            'message': 'An error occurred while updating CV'
        }), 500


@cvs_bp.route('/<cv_uuid>', methods=['DELETE'])
@jwt_required
def delete_cv(cv_uuid):
    """Delete CV by UUID."""
    try:
        current_user = request.current_user
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to delete it'
            }), 404
        
        # Delete associated files
        cv_service.delete_cv_files(cv)
        
        # Delete CV record
        db.session.delete(cv)
        db.session.commit()
        
        logger.info(f'Deleted CV {cv.id} for user {current_user.id}')
        
        return jsonify({
            'message': 'CV deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f'Delete CV error: {str(e)}')
        return jsonify({
            'error': 'Failed to delete CV',
            'message': 'An error occurred while deleting CV'
        }), 500


@cvs_bp.route('/<cv_uuid>/status', methods=['GET'])
@jwt_required
def get_cv_status(cv_uuid):
    """Get CV generation/processing status."""
    try:
        current_user = request.current_user
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to access it'
            }), 404
        
        # Get task status if task is running
        task_status = None
        if cv.task_id: # MODIFIED line: condition is now less restrictive
            task_status = cv_service.get_task_status(cv.task_id)
        
        return jsonify({
            'cv_id': cv.uuid,
            'status': cv.status.value,
            'error_message': cv.error_message,
            'created_at': cv.created_at.isoformat(),
            'updated_at': cv.updated_at.isoformat(),
            'generation_time': cv.generation_time,
            'task_status': task_status,
            'has_files': {
                'pdf': bool(cv.pdf_path),
                'jpg': bool(cv.jpg_path)
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Get CV status error: {str(e)}')
        return jsonify({
            'error': 'Failed to get CV status',
            'message': 'An error occurred while fetching CV status'
        }), 500


@cvs_bp.route('/<cv_uuid>/download', methods=['GET'])
@jwt_required
def download_cv(cv_uuid):
    """
    Download CV file.
    
    Query parameters:
    - type: File type ('pdf' or 'jpg')
    - token: Download token (optional, for temporary access)
    """
    try:
        current_user = request.current_user
        file_type = request.args.get('type', 'pdf')
        download_token = request.args.get('token')
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Validate file type
        if file_type not in ['pdf', 'jpg']:
            return jsonify({
                'error': 'Invalid file type',
                'message': 'File type must be pdf or jpg'
            }), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to access it'
            }), 404
        
        # Check if CV has the requested file
        file_path = cv.pdf_path if file_type == 'pdf' else cv.jpg_path
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found',
                'message': f'CV {file_type.upper()} file not found'
            }), 404
        
        # Update download timestamp
        cv.last_downloaded = datetime.now(timezone.utc)
        db.session.commit()
        
        # Determine filename
        filename = f"{cv.title.replace(' ', '_')}_{cv.uuid[:8]}.{file_type}"
        
        logger.info(f'User {current_user.id} downloaded CV {cv.id} ({file_type})')
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf' if file_type == 'pdf' else 'image/jpeg'
        )
        
    except Exception as e:
        logger.error(f'Download CV error: {str(e)}')
        return jsonify({
            'error': 'Failed to download CV',
            'message': 'An error occurred while downloading CV'
        }), 500


@cvs_bp.route('/<cv_uuid>/generate-download-token', methods=['POST'])
@jwt_required
def generate_download_token(cv_uuid):
    """
    Generate temporary download token for sharing.
    
    Expected payload:
    {
        "file_type": "pdf",
        "expires_in": 3600  // seconds, default 1 hour
    }
    """
    try:
        current_user = request.current_user
        data = request.get_json() or {}
        
        file_type = data.get('file_type', 'pdf')
        expires_in = data.get('expires_in', 3600)  # 1 hour default
        
        # Validate UUID format
        try:
            validate_cv_uuid(cv_uuid)
        except ValidationError as e:
            return jsonify({'error': 'Invalid CV UUID'}), 400
        
        # Validate file type
        if file_type not in ['pdf', 'jpg']:
            return jsonify({
                'error': 'Invalid file type',
                'message': 'File type must be pdf or jpg'
            }), 400
        
        # Get CV
        cv = CV.query.filter_by(uuid=cv_uuid, user_id=current_user.id).first()
        
        if not cv:
            return jsonify({
                'error': 'CV not found',
                'message': 'CV not found or you do not have permission to access it'
            }), 404
        
        # Create download token
        download_token = DownloadToken(
            cv_id=cv.id,
            user_id=current_user.id,
            file_type=file_type,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        )
        
        db.session.add(download_token)
        db.session.commit()
        
        download_url = f"/api/v1/cvs/{cv_uuid}/download?type={file_type}&token={download_token.token}"
        
        return jsonify({
            'download_token': download_token.token,
            'download_url': download_url,
            'expires_at': download_token.expires_at.isoformat(),
            'file_type': file_type
        }), 201
        
    except Exception as e:
        logger.error(f'Generate download token error: {str(e)}')
        return jsonify({
            'error': 'Failed to generate download token',
            'message': 'An error occurred while generating download token'
        }), 500


# Error handlers specific to CV routes
@cvs_bp.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors."""
    return jsonify({
        'error': 'File Too Large',
        'message': 'The uploaded file is too large. Maximum size is 16MB.',
        'max_size': '16MB'
    }), 413
