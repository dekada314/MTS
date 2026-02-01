# Use official Python image for Python 3.12
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# Create app directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN mkdir -p /app/m/reports /app/staticfiles
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project code and entrypoint
COPY . .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Multi-stage for production build
FROM base AS production

# # Create non-root user for security
# RUN useradd -m appuser && chown -R appuser:appuser $APP_HOME
# USER appuser

# Expose port for Django
EXPOSE 8000

# Entry point script (already executable from base stage)
ENTRYPOINT ["./entrypoint.sh"]