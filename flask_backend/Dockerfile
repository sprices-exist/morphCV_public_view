# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # LaTeX for PDF generation
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    # Other utilities
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app user for security
RUN groupadd -r morphcv && useradd -r -g morphcv morphcv

# Set work directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/user_data /app/latex_templates /app/logs && \
    chown -R morphcv:morphcv /app

# Copy application code
COPY --chown=morphcv:morphcv . /app/

# Copy LaTeX templates
COPY --chown=morphcv:morphcv latex_templates/ /app/latex_templates/

# Switch to non-root user
USER morphcv

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]

# Development stage (optional)
FROM production as development

USER root

# Install development dependencies
RUN pip install pytest pytest-flask black flake8 ipython

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

USER morphcv

# Override command for development
CMD ["python", "run.py"]
