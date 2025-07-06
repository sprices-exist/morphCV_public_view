# MorphCV Flask Backend

Complete Flask backend API for the MorphCV application with authentication, payment processing, async tasks, and production deployment.

## Features

- **Authentication**: Google OAuth + JWT tokens
- **Payment Processing**: Stripe subscription integration
- **Async Tasks**: Celery/Redis for CV generation
- **Rate Limiting**: Flask-Limiter for API protection
- **File Management**: Secure PDF/JPG downloads
- **Production Ready**: Gunicorn + Docker configuration

## Quick Start

1. **Environment Setup**:
```bash
cp .env.example .env
# Configure environment variables
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Database Setup**:
```bash
flask db upgrade
```

4. **Run Development**:
```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - Celery Worker
celery -A app.celery worker --loglevel=info

# Terminal 3 - Flask App
python run.py
```

5. **Production Deployment**:
```bash
docker-compose up -d
```

## API Documentation

Base URL: `http://localhost:5000/api/v1`

### Authentication Endpoints
- `POST /auth/google` - Google OAuth login
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user profile

### CV Management Endpoints
- `GET /cvs` - List user CVs
- `POST /cvs` - Generate new CV
- `GET /cvs/{cv_id}` - Get CV details
- `PUT /cvs/{cv_id}` - Edit CV
- `DELETE /cvs/{cv_id}` - Delete CV
- `GET /cvs/{cv_id}/download` - Download CV file
- `GET /cvs/{cv_id}/status` - Get generation status

### Subscription Endpoints
- `GET /subscription` - Get subscription status
- `POST /subscription/checkout` - Create Stripe checkout session
- `POST /subscription/portal` - Create customer portal session

## Environment Variables

```env
# Flask Configuration
SECRET_KEY=your-secret-key
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost/morphcv

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
```

## Project Structure

```
flask_backend/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Database models
│   ├── config.py            # Configuration
│   ├── api/                 # API blueprints
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── cvs.py          # CV management endpoints
│   │   └── subscription.py # Payment endpoints
│   ├── services/           # Business logic
│   │   ├── auth_service.py
│   │   ├── cv_service.py
│   │   ├── payment_service.py
│   │   ├── gemini_service.py
│   │   └── latex_service.py
│   ├── tasks/              # Celery tasks
│   │   └── cv_tasks.py
│   └── utils/              # Utilities
│       ├── decorators.py
│       ├── validators.py
│       └── helpers.py
├── migrations/             # Database migrations
├── user_data/             # User generated files
├── latex_templates/       # LaTeX templates
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker setup
├── Dockerfile            # Docker image
├── gunicorn.conf.py      # Gunicorn config
└── run.py               # Application entry point
```
