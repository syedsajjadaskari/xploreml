# XploreML Dockerfile
# Learn, Experiment, and Discover Machine Learning without Code
FROM python:3.9-slim

# Set labels for XploreML
LABEL maintainer="XploreML Team"
LABEL description="XploreML - Learn, Experiment, and Discover Machine Learning without Code"
LABEL version="2.0.0"
LABEL app="xploreml"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories for XploreML
RUN mkdir -p models logs data .streamlit

# Set environment variables for XploreML
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV APP_NAME="XploreML"
ENV APP_VERSION="2.0.0"

# Create non-root user for security
RUN groupadd -r xploreml && useradd -r -g xploreml xploreml
RUN chown -R xploreml:xploreml /app
USER xploreml

# Expose port
EXPOSE 8501

# Health check for XploreML
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run XploreML application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]