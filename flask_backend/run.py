#!/usr/bin/env python3
"""
MorphCV Flask Application Entry Point

This file serves as the main entry point for the MorphCV Flask application.
It can be used for both development and production environments.
"""

import os
import sys
from app import create_app, celery

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Create Flask app instance
app = create_app()

def make_celery(app):
    """Create Celery instance with Flask app context."""
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Configure Celery with Flask app
celery = make_celery(app)

@app.shell_context_processor
def make_shell_context():
    """Provide shell context for flask shell command."""
    from app.models import db, User, CV, TokenBlacklist, DownloadToken
    from app.services.auth_service import AuthService
    from app.services.cv_service import CVService
    from app.services.payment_service import PaymentService
    
    return {
        'db': db,
        'User': User,
        'CV': CV,
        'TokenBlacklist': TokenBlacklist,
        'DownloadToken': DownloadToken,
        'AuthService': AuthService,
        'CVService': CVService,
        'PaymentService': PaymentService,
        'app': app,
        'celery': celery
    }

@app.cli.command()
def init_db():
    """Initialize the database."""
    from app.models import db
    db.create_all()
    print("Database initialized successfully.")

@app.cli.command()
def create_admin():
    """Create an admin user."""
    from app.models import db, User, UserTier
    
    email = input("Enter admin email: ")
    name = input("Enter admin name: ")
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"User with email {email} already exists.")
        return
    
    # Create admin user
    admin_user = User(
        email=email,
        name=name,
        user_tier=UserTier.ENTERPRISE,
        generations_left=999
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Admin user created successfully: {email}")

@app.cli.command()
def cleanup():
    """Run cleanup tasks."""
    from app.services.auth_service import AuthService
    from app.services.cv_service import CVService
    
    auth_service = AuthService()
    cv_service = CVService()
    
    # Cleanup expired tokens
    token_result = auth_service.cleanup_expired_tokens()
    print(f"Cleaned up {token_result.get('cleaned_count', 0)} expired tokens")
    
    # Cleanup orphaned files
    file_result = cv_service.cleanup_orphaned_files()
    print(f"Cleaned up {file_result.get('cleaned_count', 0)} orphaned files")

@app.cli.command()
def test_services():
    """Test all services for basic functionality."""
    print("Testing services...")
    
    try:
        # Test database connection
        from app.models import db
        db.session.execute('SELECT 1')
        print("✓ Database connection successful")
        
        # Test Redis connection (via Celery)
        from app.tasks.cv_tasks import health_check_task
        result = health_check_task.delay()
        health_status = result.get(timeout=10)
        if health_status['status'] == 'healthy':
            print("✓ Celery/Redis connection successful")
        else:
            print("✗ Celery/Redis connection failed")
        
        # Test Gemini API
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            print("✓ Gemini API key configured")
        else:
            print("⚠ Gemini API key not configured")
        
        # Test Stripe API
        stripe_key = os.environ.get('STRIPE_SECRET_KEY')
        if stripe_key:
            print("✓ Stripe API key configured")
        else:
            print("⚠ Stripe API key not configured")
        
        print("Service testing completed.")
        
    except Exception as e:
        print(f"✗ Service test failed: {str(e)}")

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting MorphCV Flask application on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
