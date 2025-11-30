# Deployment Guide

This guide covers deploying the North London Planning Intelligence Agent to production environments.

## Prerequisites

- Docker and Docker Compose
- Access to a Supabase project (or self-hosted PostgreSQL with pgvector)
- OpenAI API key
- Domain name (for production)
- SSL certificate (Let's Encrypt recommended)

## Environment Setup

### 1. Clone and Configure

```bash
git clone <repository-url>
cd north-london-planning-agent
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your production values:

```bash
# Required
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-32-char-secret>
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Optional but recommended
REDIS_URL=redis://localhost:6379
SENTRY_DSN=https://...@sentry.io/...
SENDGRID_API_KEY=SG....
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 3. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Option 2: Manual Deployment

#### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Start production server
npm start
```

### Option 3: Platform Deployment

#### Vercel (Frontend)

1. Connect your repository to Vercel
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend URL
3. Deploy

#### Railway/Render (Backend)

1. Connect your repository
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
5. Set environment variables

## Database Setup

### Supabase Setup

1. Create a new Supabase project
2. Run the database migrations:

```bash
# Apply migrations
cd database
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_analytics_tables.sql
psql $DATABASE_URL -f migrations/003_pgvector_setup.sql
```

3. Enable Row Level Security (RLS) for public tables
4. Create database functions for vector search

### pgvector Extension

Ensure pgvector is enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Reverse Proxy Configuration

### Nginx Configuration

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## SSL Certificates

### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (usually configured automatically)
sudo certbot renew --dry-run
```

## Monitoring Setup

### Health Checks

The application exposes health check endpoints:

- `/health` - Basic health check
- `/api/v1/health` - Detailed health with dependencies

### Prometheus Metrics

Metrics are exposed at `/metrics` when `ENABLE_METRICS=true`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'planning-agent'
    static_configs:
      - targets: ['localhost:8000']
```

### Logging

Structured JSON logging is enabled in production:

```bash
# View logs
docker-compose logs -f backend | jq .
```

### Sentry Error Tracking

Set `SENTRY_DSN` for automatic error tracking:

```python
SENTRY_DSN=https://key@sentry.io/project
```

## Scaling Considerations

### Horizontal Scaling

- Backend is stateless - scale with multiple instances
- Use Redis for session/cache sharing across instances
- Frontend can be scaled independently

### Database Optimization

- Enable connection pooling (PgBouncer)
- Add database indexes for common queries
- Consider read replicas for analytics queries

### Caching Strategy

```bash
# Redis caching is enabled by default
REDIS_URL=redis://your-redis:6379

# Cache settings
CACHE_TTL=3600  # 1 hour
EMBEDDING_CACHE_TTL=86400  # 24 hours
```

## Backup and Recovery

### Database Backups

```bash
# Create backup
python scripts/backup_database.py backup --compress

# Restore from backup
python scripts/backup_database.py restore ./backups/20231115_120000/

# List available backups
python scripts/backup_database.py list
```

### Automated Backups

Set up a cron job:

```bash
# Daily backup at 2 AM
0 2 * * * cd /app && python scripts/backup_database.py backup --compress
```

## Security Checklist

- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS only
- [ ] Configure CORS properly (specific origins, not *)
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Use service account keys (not anon keys) for backend
- [ ] Enable Row Level Security in Supabase
- [ ] Rotate API keys regularly
- [ ] Monitor for suspicious activity

## Troubleshooting

### Common Issues

**Connection refused to backend**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check Docker logs
docker-compose logs backend
```

**Database connection errors**
```bash
# Verify Supabase credentials
python -c "from app.services.supabase import supabase_service; print('OK')"
```

**OpenAI API errors**
```bash
# Check API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**High memory usage**
- Reduce embedding batch size
- Enable Redis caching
- Check for memory leaks in long-running processes

### Getting Help

- Check logs: `docker-compose logs -f`
- Run health check: `python scripts/health_check.py --verbose`
- Open an issue on GitHub with logs and configuration
