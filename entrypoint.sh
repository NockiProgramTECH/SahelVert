ter name="content">#!/bin/bash
set -e

echo "=========================================="
echo "SahelVert Docker Entry Point"
echo "=========================================="

# Navigate to project directory
cd /app

# Wait for database to be ready
echo "Waiting for database to be ready..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if python -c "
import django
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SahelVert.settings')
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - Database not ready, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Database not available after $max_attempts attempts"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if not already done)
if [ ! -d "/app/staticfiles/admin" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

# Create superuser if it doesn't exist and variables are provided
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

echo "=========================================="
echo "Starting Gunicorn..."
echo "=========================================="

exec "$@"
