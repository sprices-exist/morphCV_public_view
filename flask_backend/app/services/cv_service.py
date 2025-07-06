import os
import json
import logging
from datetime import datetime, timezone
from flask import current_app
from sqlalchemy import desc, asc, or_
from app.models import db, CV, CVStatus, User
from app import celery
import shutil

logger = logging.getLogger(__name__)


class CVService:
    """Service for CV management and operations."""
    
    def list_user_cvs(self, user_id, query_params):
        """
        List user's CVs with pagination and filtering.
        
        Args:
            user_id (int): User ID
            query_params (dict): Query parameters from request
            
        Returns:
            dict: Paginated CV results
        """
        try:
            # Base query
            query = CV.query.filter_by(user_id=user_id)
            
            # Apply filters
            if query_params.get('status'):
                try:
                    status = CVStatus(query_params['status'])
                    query = query.filter_by(status=status)
                except ValueError:
                    pass  # Invalid status, ignore filter
            
            if query_params.get('template_name'):
                query = query.filter_by(template_name=query_params['template_name'])
            
            if query_params.get('search'):
                search_term = f"%{query_params['search']}%"
                query = query.filter(
                    or_(
                        CV.title.ilike(search_term),
                        CV.user_data.ilike(search_term),
                        CV.job_description.ilike(search_term)
                    )
                )
            
            # Apply sorting
            sort_by = query_params.get('sort_by', 'created_at')
            sort_order = query_params.get('sort_order', 'desc')
            
            if hasattr(CV, sort_by):
                sort_column = getattr(CV, sort_by)
                if sort_order == 'asc':
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
            
            # Apply pagination
            page = query_params.get('page', 1)
            per_page = query_params.get('per_page', 10)
            
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'cvs': pagination.items,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
        except Exception as e:
            logger.error(f'List user CVs error: {str(e)}')
            raise e
    
    def get_cv_by_uuid(self, cv_uuid, user_id=None):
        """
        Get CV by UUID with optional user verification.
        
        Args:
            cv_uuid (str): CV UUID
            user_id (int, optional): User ID for ownership verification
            
        Returns:
            CV: CV object or None if not found
        """
        try:
            query = CV.query.filter_by(uuid=cv_uuid)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            return query.first()
            
        except Exception as e:
            logger.error(f'Get CV by UUID error: {str(e)}')
            return None
    
    def delete_cv_files(self, cv):
        """
        Delete CV-related files from filesystem.
        
        Args:
            cv (CV): CV object
        """
        try:
            files_to_delete = []
            
            if cv.pdf_path and os.path.exists(cv.pdf_path):
                files_to_delete.append(cv.pdf_path)
            
            if cv.jpg_path and os.path.exists(cv.jpg_path):
                files_to_delete.append(cv.jpg_path)
            
            # Delete the entire CV directory if it exists
            cv_dir = os.path.dirname(cv.pdf_path) if cv.pdf_path else None
            if cv_dir and os.path.exists(cv_dir):
                try:
                    shutil.rmtree(cv_dir)
                    logger.info(f'Deleted CV directory: {cv_dir}')
                except Exception as e:
                    logger.warning(f'Failed to delete CV directory {cv_dir}: {str(e)}')
                    # Fall back to individual file deletion
                    for file_path in files_to_delete:
                        try:
                            os.remove(file_path)
                            logger.info(f'Deleted file: {file_path}')
                        except Exception as fe:
                            logger.warning(f'Failed to delete file {file_path}: {str(fe)}')
            
        except Exception as e:
            logger.error(f'Delete CV files error: {str(e)}')
    
    def get_task_status(self, task_id):
        """
        Get Celery task status.
        
        Args:
            task_id (str): Celery task ID
            
        Returns:
            dict: Task status information
        """
        try:
            if not task_id:
                return None
            
            # Get task result from Celery
            task_result = celery.AsyncResult(task_id)
            
            status_info = {
                'task_id': task_id,
                'state': task_result.state,
                'ready': task_result.ready(),
                'successful': task_result.successful(),
                'failed': task_result.failed()
            }
            
            # Add additional info based on state
            if task_result.state == 'PENDING':
                status_info['message'] = 'Task is waiting to be processed'
            elif task_result.state == 'PROGRESS':
                # Get progress info if available
                if hasattr(task_result, 'info') and task_result.info:
                    status_info.update(task_result.info)
            elif task_result.state == 'SUCCESS':
                status_info['result'] = task_result.result
            elif task_result.state == 'FAILURE':
                status_info['error'] = str(task_result.info)
            
            return status_info
            
        except Exception as e:
            logger.error(f'Get task status error: {str(e)}')
            return {
                'task_id': task_id,
                'state': 'UNKNOWN',
                'error': str(e)
            }
    
    def update_cv_status(self, cv_id, status, error_message=None, 
                        latex_code=None, pdf_path=None, jpg_path=None,
                        generation_time=None):
        """
        Update CV status and related fields.
        
        Args:
            cv_id (int): CV ID
            status (CVStatus): New status
            error_message (str, optional): Error message if failed
            latex_code (str, optional): Generated LaTeX code
            pdf_path (str, optional): Path to generated PDF
            jpg_path (str, optional): Path to generated JPG
            generation_time (float, optional): Generation time in seconds
        """
        try:
            cv = CV.query.get(cv_id)
            if not cv:
                logger.error(f'CV not found: {cv_id}')
                return False
            
            # Update status
            cv.status = status
            cv.updated_at = datetime.now(timezone.utc)
            
            # Update optional fields
            if error_message is not None:
                cv.error_message = error_message
            
            if latex_code is not None:
                cv.latex_code = latex_code
            
            if pdf_path is not None:
                cv.pdf_path = pdf_path
                # Get file size if file exists
                if os.path.exists(pdf_path):
                    cv.pdf_size = os.path.getsize(pdf_path)
            
            if jpg_path is not None:
                cv.jpg_path = jpg_path
            
            if generation_time is not None:
                cv.generation_time = generation_time
            
            db.session.commit()
            
            logger.info(f'Updated CV {cv_id} status to {status.value}')
            return True
            
        except Exception as e:
            logger.error(f'Update CV status error: {str(e)}')
            db.session.rollback()
            return False
    
    def get_user_cv_statistics(self, user_id):
        """
        Get CV statistics for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: CV statistics
        """
        try:
            total_cvs = CV.query.filter_by(user_id=user_id).count()
            
            successful_cvs = CV.query.filter_by(
                user_id=user_id, 
                status=CVStatus.SUCCESS
            ).count()
            
            failed_cvs = CV.query.filter_by(
                user_id=user_id, 
                status=CVStatus.FAILED
            ).count()
            
            processing_cvs = CV.query.filter(
                CV.user_id == user_id,
                CV.status.in_([CVStatus.PENDING, CVStatus.PROCESSING])
            ).count()
            
            # Get most used template
            from sqlalchemy import func
            template_stats = db.session.query(
                CV.template_name,
                func.count(CV.id).label('count')
            ).filter_by(user_id=user_id).group_by(CV.template_name).all()
            
            most_used_template = None
            if template_stats:
                most_used_template = max(template_stats, key=lambda x: x.count).template_name
            
            # Get average generation time
            avg_generation_time = db.session.query(
                func.avg(CV.generation_time)
            ).filter(
                CV.user_id == user_id,
                CV.generation_time.isnot(None)
            ).scalar()
            
            return {
                'total_cvs': total_cvs,
                'successful_cvs': successful_cvs,
                'failed_cvs': failed_cvs,
                'processing_cvs': processing_cvs,
                'success_rate': (successful_cvs / total_cvs * 100) if total_cvs > 0 else 0,
                'most_used_template': most_used_template,
                'average_generation_time': float(avg_generation_time) if avg_generation_time else None,
                'template_usage': {stat.template_name: stat.count for stat in template_stats}
            }
            
        except Exception as e:
            logger.error(f'Get user CV statistics error: {str(e)}')
            return {
                'total_cvs': 0,
                'successful_cvs': 0,
                'failed_cvs': 0,
                'processing_cvs': 0,
                'success_rate': 0,
                'most_used_template': None,
                'average_generation_time': None,
                'template_usage': {}
            }
    
    def search_cvs(self, user_id, search_query, filters=None, limit=10):
        """
        Search CVs with advanced filtering.
        
        Args:
            user_id (int): User ID
            search_query (str): Search query
            filters (dict, optional): Additional filters
            limit (int): Maximum results to return
            
        Returns:
            list: List of matching CVs
        """
        try:
            query = CV.query.filter_by(user_id=user_id)
            
            # Apply search query
            if search_query:
                search_term = f"%{search_query}%"
                query = query.filter(
                    or_(
                        CV.title.ilike(search_term),
                        CV.user_data.ilike(search_term),
                        CV.job_description.ilike(search_term),
                        CV.latex_code.ilike(search_term)
                    )
                )
            
            # Apply additional filters
            if filters:
                if 'status' in filters:
                    try:
                        status = CVStatus(filters['status'])
                        query = query.filter_by(status=status)
                    except ValueError:
                        pass
                
                if 'template_name' in filters:
                    query = query.filter_by(template_name=filters['template_name'])
                
                if 'date_from' in filters:
                    query = query.filter(CV.created_at >= filters['date_from'])
                
                if 'date_to' in filters:
                    query = query.filter(CV.created_at <= filters['date_to'])
            
            # Order by relevance (newest first for now)
            query = query.order_by(desc(CV.created_at))
            
            # Apply limit
            results = query.limit(limit).all()
            
            return [cv.to_dict() for cv in results]
            
        except Exception as e:
            logger.error(f'Search CVs error: {str(e)}')
            return []
    
    def bulk_delete_cvs(self, user_id, cv_ids):
        """
        Delete multiple CVs in bulk.
        
        Args:
            user_id (int): User ID
            cv_ids (list): List of CV IDs to delete
            
        Returns:
            dict: Result with deleted count and any errors
        """
        try:
            deleted_count = 0
            errors = []
            
            for cv_id in cv_ids:
                try:
                    cv = CV.query.filter_by(id=cv_id, user_id=user_id).first()
                    
                    if cv:
                        # Delete files
                        self.delete_cv_files(cv)
                        
                        # Delete record
                        db.session.delete(cv)
                        deleted_count += 1
                    else:
                        errors.append(f'CV {cv_id} not found or access denied')
                        
                except Exception as e:
                    errors.append(f'Failed to delete CV {cv_id}: {str(e)}')
            
            db.session.commit()
            
            logger.info(f'Bulk deleted {deleted_count} CVs for user {user_id}')
            
            return {
                'deleted_count': deleted_count,
                'errors': errors,
                'success': deleted_count > 0
            }
            
        except Exception as e:
            logger.error(f'Bulk delete CVs error: {str(e)}')
            db.session.rollback()
            return {
                'deleted_count': 0,
                'errors': [str(e)],
                'success': False
            }
    
    def cleanup_orphaned_files(self):
        """
        Clean up orphaned files that don't have corresponding CV records.
        This should be run periodically as a maintenance task.
        """
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'user_data')
            
            if not os.path.exists(upload_folder):
                return {'cleaned_count': 0, 'message': 'Upload folder does not exist'}
            
            cleaned_count = 0
            
            # Get all CV directories
            for item in os.listdir(upload_folder):
                item_path = os.path.join(upload_folder, item)
                
                if os.path.isdir(item_path) and item.startswith('cv_'):
                    # Extract UUID from directory name
                    try:
                        cv_uuid = item.replace('cv_', '')
                        
                        # Check if CV exists in database
                        cv = CV.query.filter_by(uuid=cv_uuid).first()
                        
                        if not cv:
                            # Orphaned directory, remove it
                            shutil.rmtree(item_path)
                            cleaned_count += 1
                            logger.info(f'Cleaned up orphaned directory: {item_path}')
                            
                    except Exception as e:
                        logger.warning(f'Error processing directory {item_path}: {str(e)}')
            
            return {
                'cleaned_count': cleaned_count,
                'message': f'Cleaned up {cleaned_count} orphaned files/directories'
            }
            
        except Exception as e:
            logger.error(f'Cleanup orphaned files error: {str(e)}')
            return {
                'cleaned_count': 0,
                'error': str(e)
            }
