from flask import Blueprint

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Import all API routes to register them
from app.api import auth, cvs, subscription, users

# Register sub-blueprints
api_bp.register_blueprint(auth.auth_bp, url_prefix='/auth')
api_bp.register_blueprint(cvs.cvs_bp, url_prefix='/cvs')
api_bp.register_blueprint(subscription.subscription_bp, url_prefix='/subscription')
api_bp.register_blueprint(users.users_bp, url_prefix='/users')
