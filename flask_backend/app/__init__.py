from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import os
import logging
from datetime import datetime, timezone

# Import extensions
from app.models import db, User
from app.config import get_config

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Initialize Celery
celery = Celery('morphcv')


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    limiter.init_app(app)
    
    # Configure Celery
    configure_celery(app, celery)
    
    # Configure logging
    configure_logging(app)
    
    # Configure login manager
    login_manager.login_view = 'api.auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            response.headers[header] = value
        return response
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': db_status,
            'version': '1.0.0'
        })
    
    return app


def configure_celery(app, celery):
    """Configure Celery with Flask app context."""
    
    # Update configuration
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer=app.config.get('CELERY_TASK_SERIALIZER', 'json'),
        result_serializer=app.config.get('CELERY_RESULT_SERIALIZER', 'json'),
        accept_content=app.config.get('CELERY_ACCEPT_CONTENT', ['json']),
        timezone=app.config.get('CELERY_TIMEZONE', 'UTC'),
        enable_utc=app.config.get('CELERY_ENABLE_UTC', True),
        task_track_started=True,
        task_send_sent_event=True,
        worker_send_task_events=True,
        result_expires=3600,  # 1 hour
    )
    
    # Create task base class with app context
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask


def register_blueprints(app):
    """Register all application blueprints."""
    
    # API v1 blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Main routes (for serving React frontend in production)
    from app.main import main_bp
    app.register_blueprint(main_bp)


def register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server.',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource.',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource.',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource could not be found.',
            'status_code': 404
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429,
            'retry_after': error.retry_after
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred.',
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        
        if app.debug:
            # In debug mode, return the actual error
            return jsonify({
                'error': 'Exception',
                'message': str(error),
                'type': type(error).__name__,
                'status_code': 500
            }), 500
        else:
            # In production, return generic error
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }), 500


def configure_logging(app):
    """Configure application logging."""
    
    if not app.debug and not app.testing:
        # Production logging configuration
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/morphcv.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('MorphCV startup')


# Make celery available for imports
__all__ = ['create_app', 'celery']
