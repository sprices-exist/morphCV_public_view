from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
import uuid
import enum

db = SQLAlchemy()


class UserTier(enum.Enum):
    """User subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CVStatus(enum.Enum):
    """CV generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class User(UserMixin, db.Model):
    """User model with subscription and authentication support."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    name = db.Column(db.String(100), nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True)
    
    # Subscription fields
    user_tier = db.Column(db.Enum(UserTier), default=UserTier.FREE, nullable=False)
    generations_left = db.Column(db.Integer, default=2)
    stripe_customer_id = db.Column(db.String(100), nullable=True, index=True)
    subscription_id = db.Column(db.String(100), nullable=True)
    subscription_status = db.Column(db.String(50), nullable=True)
    subscription_current_period_end = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    cvs = db.relationship('CV', backref='user', lazy=True, cascade='all, delete-orphan')
    tokens = db.relationship('TokenBlacklist', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
            'user_tier': self.user_tier.value,
            'generations_left': self.generations_left,
            'subscription_status': self.subscription_status,
            'subscription_current_period_end': self.subscription_current_period_end.isoformat() if self.subscription_current_period_end else None,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def can_generate_cv(self):
        """Check if user can generate a new CV."""
        if self.user_tier == UserTier.FREE:
            return self.generations_left > 0
        return True  # Pro and Enterprise have unlimited generations
    
    def use_generation(self):
        """Decrement generation count for free users."""
        if self.user_tier == UserTier.FREE and self.generations_left > 0:
            self.generations_left -= 1
            db.session.commit()


class CV(db.Model):
    """CV model with enhanced tracking and file management."""
    __tablename__ = 'cvs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # CV metadata
    title = db.Column(db.String(200), nullable=False, default='Untitled CV')
    template_name = db.Column(db.String(50), nullable=False)
    
    # User input data
    user_data = db.Column(db.Text, nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    
    # Generated content
    latex_code = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    jpg_path = db.Column(db.String(255), nullable=True)
    
    # Processing status
    status = db.Column(db.Enum(CVStatus), default=CVStatus.PENDING, nullable=False)
    task_id = db.Column(db.String(50), nullable=True, index=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # File metadata
    pdf_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    generation_time = db.Column(db.Float, nullable=True)  # Processing time in seconds
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    last_downloaded = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f'<CV {self.uuid}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert CV to dictionary for API responses."""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'title': self.title,
            'template_name': self.template_name,
            'status': self.status.value,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None,
            'has_pdf': bool(self.pdf_path),
            'has_jpg': bool(self.jpg_path),
            'pdf_size': self.pdf_size,
            'generation_time': self.generation_time
        }
        
        if include_sensitive:
            data.update({
                'user_data': self.user_data,
                'job_description': self.job_description,
                'latex_code': self.latex_code
            })
        
        return data


class TokenBlacklist(db.Model):
    """Blacklisted JWT tokens for logout functionality."""
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'access' or 'refresh'
    revoked_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'


class DownloadToken(db.Model):
    """Temporary tokens for secure file downloads."""
    __tablename__ = 'download_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    cv_id = db.Column(db.Integer, db.ForeignKey('cvs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf' or 'jpg'
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    cv = db.relationship('CV', backref='download_tokens')
    user = db.relationship('User', backref='download_tokens')
    
    def __repr__(self):
        return f'<DownloadToken {self.token}>'
    
    def is_valid(self):
        """Check if download token is still valid."""
        now = datetime.now(timezone.utc)
        return not self.used and self.expires_at > now


# Create indexes for better query performance
db.Index('idx_user_email', User.email)
db.Index('idx_user_google_id', User.google_id)
db.Index('idx_user_stripe_customer', User.stripe_customer_id)
db.Index('idx_cv_user_id', CV.user_id)
db.Index('idx_cv_uuid', CV.uuid)
db.Index('idx_cv_status', CV.status)
db.Index('idx_cv_task_id', CV.task_id)
db.Index('idx_token_blacklist_jti', TokenBlacklist.jti)
db.Index('idx_token_blacklist_user', TokenBlacklist.user_id)
db.Index('idx_download_token', DownloadToken.token)
