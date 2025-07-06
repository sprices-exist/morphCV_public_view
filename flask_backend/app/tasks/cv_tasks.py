import time
import json
import logging
from celery import current_task
from app import celery
from app.models import CVStatus
from app.services.cv_service import CVService
from app.services.gemini_service import generate_cv_with_gemini, edit_cv_with_gemini
from app.services.latex_service import compile_latex_to_pdf
from sqlalchemy import text


logger = logging.getLogger(__name__)


@celery.task(bind=True, name='generate_cv_task')
def generate_cv_task(self, cv_id, user_data, job_description, template_name, user_tier):
    """
    Celery task for generating CV using Gemini and LaTeX.
    
    Args:
        cv_id (int): CV database ID
        user_data (dict): User information
        job_description (str): Job description to tailor CV for
        template_name (str): LaTeX template to use
        user_tier (str): User subscription tier
    """
    cv_service = CVService()
    start_time = time.time()
    
    try:
        logger.info(f'Starting CV generation for CV {cv_id}')
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Generating CV content with AI', 'progress': 20}
        )
        
        # Step 1: Generate LaTeX code using Gemini
        latex_code = generate_cv_with_gemini(user_data, job_description, template_name)
        
        if not latex_code:
            raise Exception("Failed to generate LaTeX code with Gemini")
        
        logger.info(f'Generated LaTeX code for CV {cv_id}')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Compiling PDF document', 'progress': 60}
        )
        
        # Step 2: Compile LaTeX to PDF
        from app.models import CV
        cv = CV.query.get(cv_id)
        if not cv:
            raise Exception(f"CV {cv_id} not found in database")
        
        pdf_path, jpg_path = compile_latex_to_pdf(cv.uuid, latex_code, user_tier)
        
        logger.info(f'Compiled PDF for CV {cv_id}')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Finalizing CV', 'progress': 90}
        )
        
        # Step 3: Update CV record with results
        generation_time = time.time() - start_time
        
        success = cv_service.update_cv_status(
            cv_id=cv_id,
            status=CVStatus.SUCCESS,
            latex_code=latex_code,
            pdf_path=pdf_path,
            jpg_path=jpg_path,
            generation_time=generation_time
        )
        
        if not success:
            raise Exception("Failed to update CV record in database")
        
        logger.info(f'Successfully generated CV {cv_id} in {generation_time:.2f} seconds')
        
        return {
            'cv_id': cv_id,
            'status': 'success',
            'generation_time': generation_time,
            'has_pdf': bool(pdf_path),
            'has_jpg': bool(jpg_path),
            'message': 'CV generated successfully'
        }
        
    except Exception as e:
        error_message = str(e)
        generation_time = time.time() - start_time
        
        logger.error(f'CV generation failed for CV {cv_id}: {error_message}')
        
        # Update CV record with error
        cv_service.update_cv_status(
            cv_id=cv_id,
            status=CVStatus.FAILED,
            error_message=error_message,
            generation_time=generation_time
        )
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_message,
                'cv_id': cv_id,
                'generation_time': generation_time
            }
        )
        
        raise Exception(error_message)


@celery.task(bind=True, name='edit_cv_task')
def edit_cv_task(self, cv_id, edit_instructions, user_tier):
    """
    Celery task for editing existing CV using Gemini and LaTeX.
    
    Args:
        cv_id (int): CV database ID
        edit_instructions (str): Instructions for editing the CV
        user_tier (str): User subscription tier
    """
    cv_service = CVService()
    start_time = time.time()
    
    try:
        logger.info(f'Starting CV editing for CV {cv_id}')
        
        # Get existing CV
        from app.models import CV
        cv = CV.query.get(cv_id)
        if not cv:
            raise Exception(f"CV {cv_id} not found in database")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Analyzing edit instructions', 'progress': 20}
        )
        
        # Step 1: Edit LaTeX code using Gemini
        if not cv.latex_code:
            raise Exception("No existing LaTeX code found for editing")
        
        # Parse user data back to dict
        try:
            user_data = json.loads(cv.user_data) if isinstance(cv.user_data, str) else cv.user_data
        except json.JSONDecodeError:
            raise Exception("Invalid user data format in CV record")
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Editing CV content with AI', 'progress': 40}
        )
        
        edited_latex_code = edit_cv_with_gemini(
            cv.latex_code, 
            edit_instructions,
            user_data,
            cv.job_description
        )
        
        if not edited_latex_code:
            raise Exception("Failed to edit LaTeX code with Gemini")
        
        logger.info(f'Edited LaTeX code for CV {cv_id}')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Compiling updated PDF', 'progress': 70}
        )
        
        # Step 2: Compile edited LaTeX to PDF
        pdf_path, jpg_path = compile_latex_to_pdf(cv.uuid, edited_latex_code, user_tier)
        
        logger.info(f'Compiled edited PDF for CV {cv_id}')
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Finalizing edited CV', 'progress': 90}
        )
        
        # Step 3: Update CV record with results
        generation_time = time.time() - start_time
        
        success = cv_service.update_cv_status(
            cv_id=cv_id,
            status=CVStatus.SUCCESS,
            latex_code=edited_latex_code,
            pdf_path=pdf_path,
            jpg_path=jpg_path,
            generation_time=generation_time
        )
        
        if not success:
            raise Exception("Failed to update CV record in database")
        
        logger.info(f'Successfully edited CV {cv_id} in {generation_time:.2f} seconds')
        
        return {
            'cv_id': cv_id,
            'status': 'success',
            'generation_time': generation_time,
            'has_pdf': bool(pdf_path),
            'has_jpg': bool(jpg_path),
            'message': 'CV edited successfully'
        }
        
    except Exception as e:
        error_message = str(e)
        generation_time = time.time() - start_time
        
        logger.error(f'CV editing failed for CV {cv_id}: {error_message}')
        
        # Update CV record with error
        cv_service.update_cv_status(
            cv_id=cv_id,
            status=CVStatus.FAILED,
            error_message=error_message,
            generation_time=generation_time
        )
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_message,
                'cv_id': cv_id,
                'generation_time': generation_time
            }
        )
        
        raise Exception(error_message)


@celery.task(name='cleanup_task')
def cleanup_task():
    """
    Periodic cleanup task for maintenance.
    """
    try:
        logger.info('Starting cleanup task')
        
        # Cleanup expired tokens
        from app.services.auth_service import AuthService
        auth_service = AuthService()
        token_cleanup_result = auth_service.cleanup_expired_tokens()
        
        # Cleanup orphaned files
        cv_service = CVService()
        file_cleanup_result = cv_service.cleanup_orphaned_files()
        
        result = {
            'status': 'success',
            'token_cleanup': token_cleanup_result,
            'file_cleanup': file_cleanup_result,
            'timestamp': time.time()
        }
        
        logger.info(f'Cleanup task completed: {result}')
        return result
        
    except Exception as e:
        error_message = str(e)
        logger.error(f'Cleanup task failed: {error_message}')
        
        return {
            'status': 'failed',
            'error': error_message,
            'timestamp': time.time()
        }


@celery.task(name='health_check_task')
def health_check_task():
    """
    Health check task for monitoring Celery workers.
    """
    try:
        # Basic health checks
        from app.models import db, User
        
        # Check database connection
        try:
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        # Check if we can access models
        try:
            user_count = User.query.count()
            model_status = 'healthy'
        except Exception as e:
            model_status = f'unhealthy: {str(e)}'
            user_count = None
        
        result = {
            'status': 'healthy' if db_status == 'healthy' and model_status == 'healthy' else 'unhealthy',
            'database': db_status,
            'models': model_status,
            'user_count': user_count,
            'timestamp': time.time(),
            'worker_id': current_task.request.hostname if current_task else 'unknown'
        }
        
        logger.info(f'Health check completed: {result["status"]}')
        return result
        
    except Exception as e:
        error_message = str(e)
        logger.error(f'Health check failed: {error_message}')
        
        return {
            'status': 'unhealthy',
            'error': error_message,
            'timestamp': time.time(),
            'worker_id': current_task.request.hostname if current_task else 'unknown'
        }


@celery.task(name='batch_cv_generation_task')
def batch_cv_generation_task(cv_data_list):
    """
    Task for batch CV generation (enterprise feature).
    
    Args:
        cv_data_list (list): List of CV data dictionaries
    """
    try:
        results = []
        cv_service = CVService()
        
        for i, cv_data in enumerate(cv_data_list):
            try:
                # Update progress
                progress = int((i / len(cv_data_list)) * 100)
                current_task.update_state(
                    state='PROGRESS',
                    meta={'step': f'Processing CV {i+1}/{len(cv_data_list)}', 'progress': progress}
                )
                
                # Generate individual CV
                result = generate_cv_task.delay(
                    cv_data['cv_id'],
                    cv_data['user_data'],
                    cv_data['job_description'],
                    cv_data['template_name'],
                    cv_data['user_tier']
                ).get()  # Wait for completion
                
                results.append({
                    'cv_id': cv_data['cv_id'],
                    'status': 'success',
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'cv_id': cv_data.get('cv_id', 'unknown'),
                    'status': 'failed',
                    'error': str(e)
                })
        
        successful_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len(results) - successful_count
        
        logger.info(f'Batch CV generation completed: {successful_count} successful, {failed_count} failed')
        
        return {
            'status': 'completed',
            'total_cvs': len(cv_data_list),
            'successful_count': successful_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f'Batch CV generation failed: {error_message}')
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': error_message}
        )
        
        raise Exception(error_message)


# Celery beat schedule for periodic tasks
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'cleanup_task',
        'schedule': crontab(minute=0),  # Run every hour
    },
    'health-check-every-5-minutes': {
        'task': 'health_check_task',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
}

celery.conf.timezone = 'UTC'
