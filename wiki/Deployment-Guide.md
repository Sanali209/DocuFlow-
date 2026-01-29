# Deployment Guide

This comprehensive guide covers all deployment options for DocuFlow, from simple Docker deployments to production-ready cloud platforms.

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Platform-Specific Deployments](#platform-specific-deployments)
   - [Railway](#railway-deployment)
   - [Koyeb](#koyeb-deployment)
   - [Render](#render-deployment)
   - [DigitalOcean](#digitalocean-deployment)
   - [Heroku](#heroku-deployment)
4. [OCR Service Deployment](#ocr-service-deployment)
5. [Reverse Proxy Setup](#reverse-proxy-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Environment Variables](#environment-variables)
8. [Production Best Practices](#production-best-practices)
9. [Monitoring and Logging](#monitoring-and-logging)

---

## Docker Deployment

### Building the Docker Image

DocuFlow uses a multi-stage Dockerfile that builds the frontend and bundles it with the backend.

```bash
# Clone the repository
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-

# Build the Docker image
docker build -t docuflow:latest .
```

### Running the Container

```bash
# Run with default settings
docker run -d \
  --name docuflow \
  -p 8000:8000 \
  -v docuflow_data:/app/data \
  docuflow:latest

# Run with custom OCR service URL
docker run -d \
  --name docuflow \
  -p 8000:8000 \
  -e OCR_SERVICE_URL=https://your-ocr-service.hf.space \
  -v docuflow_data:/app/data \
  docuflow:latest
```

### Verifying Deployment

```bash
# Check container status
docker ps | grep docuflow

# View logs
docker logs docuflow

# Test health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Data Persistence

The Docker image stores data in `/app/data`. Always use a volume to persist:

```bash
# Create named volume
docker volume create docuflow_data

# Or bind mount to host directory
docker run -d \
  -p 8000:8000 \
  -v /host/path/data:/app/data \
  docuflow:latest
```

---

## Docker Compose Deployment

Docker Compose is the recommended method for running DocuFlow with the OCR service.

### Full Stack Setup

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: docuflow-app
    ports:
      - "8000:8000"
    environment:
      - OCR_SERVICE_URL=http://ocr-service:7860
      - DATABASE_URL=sqlite:///./data/sql_app.db
    volumes:
      - docuflow_data:/app/data
    depends_on:
      - ocr-service
    networks:
      - docuflow-network
    restart: unless-stopped

  ocr-service:
    build:
      context: ./ocr_service
      dockerfile: Dockerfile
    container_name: docuflow-ocr
    ports:
      - "7860:7860"
    environment:
      - HF_HOME=/home/user/.cache/huggingface
    volumes:
      - ocr_models:/home/user/.cache
    networks:
      - docuflow-network
    restart: unless-stopped

volumes:
  docuflow_data:
  ocr_models:

networks:
  docuflow-network:
    driver: bridge
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Scaling Considerations

For production workloads, consider:

```bash
# Allocate more memory to OCR service
docker-compose up -d --scale ocr-service=1 \
  --memory=4g ocr-service
```

---

## Platform-Specific Deployments

### Railway Deployment

Railway supports deploying DocuFlow as a monorepo with separate services.

#### Backend Service

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add a new service (Backend):
   - **Root Directory**: `/backend`
   - **Build Command**: Auto-detected (pip install)
   - **Start Command**: Defined in `backend/railway.json`

**Environment Variables:**
```env
OCR_SERVICE_URL=https://your-ocr-service-url.com
ALLOWED_ORIGINS=https://your-frontend.railway.app
DATABASE_URL=sqlite:///./data/sql_app.db
```

4. Generate a domain for the backend service

#### Frontend Service

1. Add another service (Frontend):
   - **Root Directory**: `/frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: Defined in `frontend/railway.json`

**Environment Variables:**
```env
VITE_API_URL=https://your-backend.railway.app
```

2. Generate a domain for the frontend service

#### Database Persistence

Railway automatically persists volumes. For production:
- Consider using Railway's PostgreSQL add-on
- Update `DATABASE_URL` to PostgreSQL connection string

---

### Koyeb Deployment

Koyeb supports Docker deployments using the root Dockerfile.

#### Steps

1. Create an account on [Koyeb](https://www.koyeb.com)
2. Create a new app:
   - **Source**: GitHub repository
   - **Builder**: Dockerfile
   - **Dockerfile Location**: `Dockerfile` (root)
3. Configure service:
   - **Port**: 8000
   - **Privileged**: No
   - **Instance Type**: Nano (minimum) or Micro (recommended)

**Environment Variables:**
```env
OCR_SERVICE_URL=https://your-ocr-service.hf.space
ALLOWED_ORIGINS=https://your-app.koyeb.app
PORT=8000
```

4. Deploy and wait for build completion
5. Access your app at the generated Koyeb URL

#### Persistent Storage

Koyeb provides persistent storage via volumes:

```yaml
# Add in Koyeb dashboard
volumes:
  - name: docuflow-data
    mount_path: /app/data
    size: 1GB
```

---

### Render Deployment

Render supports deploying from `render.yaml` blueprint.

#### Blueprint Configuration

```yaml
# render.yaml
services:
  - type: web
    name: docuflow
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: OCR_SERVICE_URL
        value: https://your-ocr-service.hf.space
      - key: ALLOWED_ORIGINS
        value: https://docuflow.onrender.com
    disk:
      name: docuflow-data
      mountPath: /app/data
      sizeGB: 1
```

#### Manual Deployment

1. Create account on [Render](https://render.com)
2. New → Web Service
3. Connect GitHub repository
4. Configure:
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Port**: 8000
5. Add environment variables
6. Add disk for persistence
7. Deploy

---

### DigitalOcean Deployment

Deploy DocuFlow on DigitalOcean using App Platform or Droplets.

#### App Platform (Recommended)

1. Create a new app on [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Connect GitHub repository
3. Configure component:
   - **Type**: Web Service
   - **Source**: Dockerfile
   - **HTTP Port**: 8000

**Environment Variables:**
```env
OCR_SERVICE_URL=https://your-ocr-service.hf.space
ALLOWED_ORIGINS=https://your-app.ondigitalocean.app
```

4. Add volume:
   - **Mount Path**: `/app/data`
   - **Size**: 1GB+

#### Droplet Deployment

For more control, deploy on a Droplet:

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Clone and run
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-
docker-compose up -d
```

---

### Heroku Deployment

Heroku deployment requires additional configuration.

#### Heroku Configuration

1. Install Heroku CLI
2. Create Heroku app:

```bash
heroku create docuflow-app
heroku stack:set container
```

3. Add PostgreSQL (recommended):

```bash
heroku addons:create heroku-postgresql:mini
```

4. Configure environment:

```bash
heroku config:set OCR_SERVICE_URL=https://your-ocr.hf.space
heroku config:set ALLOWED_ORIGINS=https://docuflow-app.herokuapp.com
```

5. Create `heroku.yml`:

```yaml
build:
  docker:
    web: Dockerfile
```

6. Deploy:

```bash
git push heroku main
```

---

## OCR Service Deployment

The OCR service should be deployed separately for optimal performance.

### Hugging Face Spaces (Recommended)

Hugging Face Spaces provides free GPU-accelerated hosting for the OCR service.

#### Steps

1. Create account on [Hugging Face](https://huggingface.co)
2. Create new Space:
   - **Name**: docuflow-ocr
   - **SDK**: Docker
   - **Hardware**: CPU Basic (free) or GPU (faster)
3. Upload OCR service files:

```bash
cd ocr_service
git init
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/docuflow-ocr
git add Dockerfile main.py requirements.txt preprocessing.py
git commit -m "Initial OCR service"
git push space main
```

4. Wait for build completion
5. Test endpoint:

```bash
curl https://YOUR_USERNAME-docuflow-ocr.hf.space/health
```

6. Update DocuFlow settings with Space URL:
   - URL format: `https://YOUR_USERNAME-docuflow-ocr.hf.space`

#### README.md for Space

```markdown
---
title: DocuFlow OCR Service
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# DocuFlow OCR Service

AI-powered OCR service using IBM Docling for document text extraction.
```

### Self-Hosted OCR Service

For private deployments:

```bash
# Build and run locally
docker build -t docuflow-ocr ./ocr_service
docker run -d -p 7860:7860 --name ocr-service docuflow-ocr

# Or with GPU support
docker run -d -p 7860:7860 --gpus all docuflow-ocr
```

---

## Reverse Proxy Setup

For production, use a reverse proxy for security and performance.

### Nginx Configuration

#### Basic Setup

```nginx
# /etc/nginx/sites-available/docuflow
server {
    listen 80;
    server_name docuflow.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name docuflow.example.com;

    # SSL Configuration (see SSL/TLS section)
    ssl_certificate /etc/letsencrypt/live/docuflow.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docuflow.example.com/privkey.pem;

    # Proxy settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Increase upload size for attachments
    client_max_body_size 50M;

    # Static file caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

#### Enable Configuration

```bash
# Enable site
ln -s /etc/nginx/sites-available/docuflow /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

### Apache Configuration

```apache
# /etc/apache2/sites-available/docuflow.conf
<VirtualHost *:80>
    ServerName docuflow.example.com
    Redirect permanent / https://docuflow.example.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName docuflow.example.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/docuflow.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/docuflow.example.com/privkey.pem

    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/

    # Increase timeout for OCR processing
    ProxyTimeout 300

    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
</VirtualHost>
```

---

## SSL/TLS Configuration

### Let's Encrypt (Certbot)

Free SSL certificates using Let's Encrypt:

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (Nginx)
sudo certbot --nginx -d docuflow.example.com

# Obtain certificate (Apache)
sudo certbot --apache -d docuflow.example.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

---

## Environment Variables

### Backend Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OCR_SERVICE_URL` | URL of OCR service | `http://localhost:7860` | No |
| `DOC_NAME_REGEX` | Regex for document name extraction | `(?si)Order:\s*(.*?)\s*Date:` | No |
| `DATABASE_URL` | Database connection string | `sqlite:///./data/sql_app.db` | No |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `*` | No |
| `PORT` | Application port | `8000` | No |

### Frontend Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes (production) |

### OCR Service Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HF_HOME` | Hugging Face cache directory | `/home/user/.cache/huggingface` | No |
| `TORCH_HOME` | PyTorch cache directory | `/home/user/.cache/torch` | No |

### Setting Environment Variables

#### Docker
```bash
docker run -e OCR_SERVICE_URL=https://... docuflow:latest
```

#### Docker Compose
```yaml
environment:
  - OCR_SERVICE_URL=https://...
```

#### System Environment
```bash
export OCR_SERVICE_URL=https://...
uvicorn backend.main:app
```

---

## Production Best Practices

### 1. Database Configuration

**SQLite Limitations:**
- Not recommended for high-traffic production
- No concurrent write support
- File-based, limited scalability

**PostgreSQL Migration (Recommended):**

```python
# Update backend/database.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/docuflow"
)

# Install PostgreSQL driver
pip install psycopg2-binary
```

**Docker Compose with PostgreSQL:**

```yaml
services:
  app:
    environment:
      - DATABASE_URL=postgresql://docuflow:password@db:5432/docuflow
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=docuflow
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=docuflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 2. Security Hardening

```python
# Disable debug mode in production
app = FastAPI(debug=False)

# Restrict CORS origins
ALLOWED_ORIGINS = [
    "https://docuflow.example.com",
    "https://www.docuflow.example.com"
]

# Use secure cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
```

### 3. Performance Optimization

**Enable Gzip Compression:**

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Add Caching Headers:**

```python
@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    response = FileResponse(f"static/{file_path}")
    response.headers["Cache-Control"] = "public, max-age=31536000"
    return response
```

**Connection Pooling:**

```python
# backend/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 4. Resource Limits

**Docker Resource Constraints:**

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 5. Backup Strategy

**Automated Backups:**

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec docuflow-app cp /app/data/sql_app.db /tmp/backup.db
docker cp docuflow-app:/tmp/backup.db $BACKUP_DIR/db_$DATE.db

# Backup uploads
docker cp docuflow-app:/app/static/uploads $BACKUP_DIR/uploads_$DATE

# Retain only last 7 days
find $BACKUP_DIR -name "db_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "uploads_*" -mtime +7 -delete
```

**Cron Schedule:**

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### 6. Health Checks

**Docker Health Check:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Docker Compose:**

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s
```

---

## Monitoring and Logging

### Application Logging

**Structured Logging:**

```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/app.log')
    ]
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    logger.info("Application starting up")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
```

### Docker Logging

**Configure Log Driver:**

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**View Logs:**

```bash
# Follow logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Export logs
docker-compose logs app > app.log
```

### Monitoring with Prometheus

**Add Prometheus Metrics:**

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

**Prometheus Config:**

```yaml
scrape_configs:
  - job_name: 'docuflow'
    static_configs:
      - targets: ['localhost:8000']
```

### Uptime Monitoring

**Health Check Endpoint:**

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

**External Monitoring Services:**
- [UptimeRobot](https://uptimerobot.com) - Free uptime monitoring
- [Pingdom](https://www.pingdom.com) - Comprehensive monitoring
- [Better Uptime](https://betteruptime.com) - Incident management

### Error Tracking

**Sentry Integration:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0
)
```

### Log Aggregation

**Docker logs to external service:**

```yaml
services:
  app:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logs.example.com:514"
```

---

## Deployment Checklist

Before going to production:

- [ ] Database migrated to PostgreSQL
- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Reverse proxy configured
- [ ] CORS origins restricted
- [ ] Backup strategy implemented
- [ ] Health checks configured
- [ ] Monitoring set up
- [ ] Log aggregation enabled
- [ ] Resource limits set
- [ ] Security headers added
- [ ] Error tracking configured
- [ ] Documentation updated
- [ ] Load testing performed
- [ ] Disaster recovery plan documented

---

## Troubleshooting Production Issues

### Container Won't Start

```bash
# Check logs
docker logs docuflow

# Check resource usage
docker stats docuflow

# Inspect container
docker inspect docuflow
```

### Database Connection Issues

```bash
# Test database connection
docker exec docuflow python -c "from backend.database import engine; engine.connect()"

# Check database file permissions
docker exec docuflow ls -la /app/data/
```

### High Memory Usage

```bash
# Monitor memory
docker stats --no-stream docuflow

# Restart with memory limit
docker run --memory="1g" docuflow:latest
```

### Slow OCR Performance

- Use GPU-enabled hosting
- Scale OCR service horizontally
- Add Redis caching for repeated documents
- Optimize image preprocessing

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

[← Back to Wiki Home](Home.md) | [Next: Developer Guide →](Developer-Guide.md)
