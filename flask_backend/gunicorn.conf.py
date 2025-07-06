"""
Gunicorn configuration file for MorphCV Flask application.

This configuration optimizes the application for production deployment
with proper worker management, logging, and security settings.
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 60
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this much time has passed
max_worker_lifetime = 12 * 60 * 60  # 12 hours
max_worker_lifetime_jitter = 60 * 60  # 1 hour

# Application
wsgi_module = "run:app"
pythonpath = "."

# Logging
loglevel = os.environ.get('LOG_LEVEL', 'info')
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'morphcv-flask'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if certificates are provided)
keyfile = os.environ.get('SSL_KEYFILE')
certfile = os.environ.get('SSL_CERTFILE')

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = os.environ.get('GUNICORN_USER')
group = os.environ.get('GUNICORN_GROUP')
tmp_upload_dir = '/tmp'

# Application callbacks
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("MorphCV Flask server is ready. Listening at: %s", server.address)

def worker_int(worker):
    """Called just after a worker has been killed by a SIGINT signal."""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker received a SIGABRT signal."""
    worker.log.info("worker received SIGABRT signal")

# Environment-specific configurations
if os.environ.get('FLASK_ENV') == 'development':
    # Development settings
    reload = True
    loglevel = 'debug'
    workers = 1
elif os.environ.get('FLASK_ENV') == 'production':
    # Production settings
    reload = False
    preload_app = True
    
    # Performance optimizations
    worker_tmp_dir = '/dev/shm'  # Use shared memory for better performance
    
    # Security enhancements
    forwarded_allow_ips = '*'
    secure_scheme_headers = {
        'X-FORWARDED-PROTOCOL': 'ssl',
        'X-FORWARDED-PROTO': 'https',
        'X-FORWARDED-SSL': 'on'
    }

# Health check configuration
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting MorphCV Flask server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading MorphCV Flask server...")

# Memory management
def post_request(worker, req, environ, resp):
    """Called just after a worker processes the request."""
    # Optional: Add memory monitoring here
    pass

# Custom error pages
def default_proc_name(name):
    """Return the default process name."""
    return f"morphcv-{name}"
