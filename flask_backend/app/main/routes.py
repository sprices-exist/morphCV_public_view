from flask import render_template, send_from_directory, current_app, jsonify
from app.main import main_bp
import os


@main_bp.route('/')
def index():
    """Serve React frontend index.html in production."""
    try:
        # In production, serve the React build
        static_folder = current_app.static_folder
        if static_folder and os.path.exists(os.path.join(static_folder, 'index.html')):
            return send_from_directory(static_folder, 'index.html')
        else:
            # Development fallback - API status
            return jsonify({
                'service': 'MorphCV API',
                'status': 'running',
                'version': '1.0.0',
                'endpoints': {
                    'auth': '/api/v1/auth',
                    'cvs': '/api/v1/cvs',
                    'subscription': '/api/v1/subscription',
                    'users': '/api/v1/users'
                },
                'documentation': '/api/v1/docs'
            })
    except Exception as e:
        return jsonify({
            'error': 'Service unavailable',
            'message': str(e)
        }), 500


@main_bp.route('/<path:path>')
def serve_static(path):
    """Serve React static files."""
    try:
        static_folder = current_app.static_folder
        if static_folder and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        else:
            # If file doesn't exist, serve index.html for client-side routing
            return send_from_directory(static_folder, 'index.html')
    except Exception:
        return jsonify({
            'error': 'File not found',
            'message': 'The requested resource could not be found'
        }), 404


@main_bp.route('/api/v1/docs')
def api_documentation():
    """Serve API documentation."""
    return jsonify({
        'title': 'MorphCV API Documentation',
        'version': '1.0.0',
        'description': 'AI-powered CV generation and management API',
        'base_url': '/api/v1',
        'authentication': {
            'type': 'Bearer Token (JWT)',
            'header': 'Authorization: Bearer <token>',
            'login_endpoint': '/api/v1/auth/google'
        },
        'endpoints': {
            'authentication': {
                'POST /auth/google': 'Google OAuth login',
                'POST /auth/refresh': 'Refresh access token',
                'POST /auth/logout': 'Logout user',
                'GET /auth/me': 'Get current user profile'
            },
            'cv_management': {
                'GET /cvs': 'List user CVs with pagination',
                'POST /cvs': 'Generate new CV',
                'GET /cvs/{uuid}': 'Get CV details',
                'PUT /cvs/{uuid}': 'Edit CV',
                'DELETE /cvs/{uuid}': 'Delete CV',
                'GET /cvs/{uuid}/status': 'Get generation status',
                'GET /cvs/{uuid}/download': 'Download CV file'
            },
            'subscription': {
                'GET /subscription': 'Get subscription status',
                'POST /subscription/checkout': 'Create payment session',
                'POST /subscription/portal': 'Customer portal',
                'GET /subscription/prices': 'Available prices'
            },
            'user_management': {
                'GET /users/profile': 'Get user profile',
                'PUT /users/profile': 'Update profile',
                'GET /users/statistics': 'User statistics',
                'POST /users/export': 'Export user data'
            }
        },
        'rate_limits': {
            'authentication': '5 requests per minute',
            'cv_generation': '10 requests per hour',
            'api_general': '100 requests per hour'
        },
        'response_format': {
            'success': {'data': '...', 'message': 'Success'},
            'error': {'error': 'Error Type', 'message': 'Description', 'status_code': 400}
        }
    })


@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    try:
        static_folder = current_app.static_folder
        if static_folder:
            return send_from_directory(static_folder, 'favicon.ico')
    except Exception:
        pass
    
    # Return empty response if favicon not found
    return '', 204
