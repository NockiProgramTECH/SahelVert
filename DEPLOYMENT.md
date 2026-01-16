ter name="content"># SahelVert Docker Deployment Guide

## Overview

This document provides complete instructions for deploying the SahelVert Django e-commerce application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- At least 2GB of available RAM
- At least 5GB of disk space

## Architecture

```
                        NGINX (Reverse Proxy)
                    Ports: 80 (HTTP), 443 (HTTPS)
                                │
                                ▼
                    Gunicorn (Django App)
                       Port: 8000
                   Container: sahelvert_web
                                │
                                ▼
                    PostgreSQL Database
                       Port: 5432
                   Container: sahelvert_db
```

## Project Structure

```
ProjetSahelVert/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-container orchestration
├── nginx.conf             # Nginx reverse proxy config
├── entrypoint.sh          # Container startup script
├── .env.production        # Environment variables template
├── .dockerignore          # Files to exclude from Docker build
├── SahelVert/             # Django project
├── static/                # Static files (CSS, JS)
├── media/                 # Uploaded files
└── templates/             # Django templates
```

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ProjetSahelVert
```

### 2. Create Environment File

```bash
# Copy the template
cp .env.production .env

# Edit with your settings
nano .env
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access the Application

- Application: http://localhost:80
- Admin Panel: http://localhost:80/admin

## Production Deployment

### 1. SSL/HTTPS Setup

```bash
# Create SSL directory
mkdir -p ssl

# Option A: Let's Encrypt (free)
# Install certbot and generate certificates
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Option B: Use your own certificates
cp your-certificate.crt ssl/cert.pem
cp your-private-key.key ssl/key.pem

# Set correct permissions
chmod 600 ssl/key.pem
```

### 2. Production Environment Variables

Edit .env with production values:

```env
SECRET_KEY=your-very-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_NAME=sahelvert
DB_USER=sahelvert_user
DB_PASSWORD=very-secure-password

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Deploy with Docker

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Useful Commands

### Container Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Restart a service
docker-compose restart web

# Rebuild after requirements change
docker-compose up -d --build
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec db psql -U sahelvert_user -d sahelvert

# Backup database
docker-compose exec db pg_dump -U sahelvert_user sahelvert > backup.sql

# Restore database
docker-compose exec -T db psql -U sahelvert_user -d sahelvert < backup.sql
```

### Django Management

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check system
docker-compose exec web python manage.py check

# Open Django shell
docker-compose exec web python manage.py shell
```

### Static Files

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic

# Find unused static files
docker-compose exec web python manage.py findstatic --noinput
```

## Troubleshooting

### Container wont start

```bash
# Check logs
docker-compose logs web

# Verify environment
docker-compose exec web env
```

### Database connection failed

```bash
# Check database health
docker-compose exec db pg_isready -U sahelvert_user

# Check connection from web container
docker-compose exec web python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SahelVert.settings')
import django
django.setup()
from django.db import connection
print('Database connected!' if connection.cursor() else 'Failed')
"
```

### Port already in use

```bash
# Find process using port
sudo lsof -i :80

# Kill the process or change port in docker-compose.yml
```

### Clear everything and restart

```bash
docker-compose down -v
docker-compose up -d --build
```

## Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Set DEBUG=False in production
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Keep dependencies updated
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## Updating the Application

```bash
# 1. Pull latest code
git fetch origin
git pull origin main

# 2. Rebuild images
docker-compose build

# 3. Run migrations
docker-compose run --rm web python manage.py migrate

# 4. Collect static files
docker-compose run --rm web python manage.py collectstatic --noinput

# 5. Restart services
docker-compose up -d

# 6. Verify
docker-compose logs -f
