# FAQ and Troubleshooting Guide

This guide addresses common questions and provides solutions to frequently encountered issues with DocuFlow.

## Table of Contents

1. [Frequently Asked Questions](#frequently-asked-questions)
2. [Backend Errors](#backend-errors)
3. [Frontend Errors](#frontend-errors)
4. [OCR Service Issues](#ocr-service-issues)
5. [Database Problems](#database-problems)
6. [Performance Issues](#performance-issues)
7. [Mobile and Browser Compatibility](#mobile-and-browser-compatibility)
8. [Deployment Issues](#deployment-issues)

---

## Frequently Asked Questions

### General Questions

#### What is DocuFlow?

DocuFlow is a modern document management system that combines smart tracking capabilities with AI-powered OCR technology. It helps you organize, search, and manage documents with features like task management, notes, file attachments, and advanced filtering.

#### What technologies does DocuFlow use?

- **Backend**: FastAPI (Python), SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: Svelte 5 with Vite
- **OCR Service**: IBM Docling, FastAPI
- **Deployment**: Docker, Docker Compose

#### Is DocuFlow free to use?

Yes, DocuFlow is open-source software licensed under the MIT License. You can use, modify, and distribute it freely.

#### Can I use DocuFlow without the OCR service?

Yes! The OCR service is optional. You can use all other features (document management, tasks, notes, attachments, filtering) without OCR. Simply don't configure the OCR service URL.

#### What file formats are supported for OCR?

The OCR service supports:
- Images: JPEG, PNG, TIFF, BMP
- Documents: PDF (single and multi-page)

#### How many documents can DocuFlow handle?

With SQLite (default), DocuFlow can handle thousands of documents efficiently. For larger deployments (10,000+ documents), we recommend migrating to PostgreSQL for better performance.

#### Can multiple users use DocuFlow simultaneously?

The current version is designed for single-user or small team use with SQLite. For multi-user production environments with concurrent access, migrate to PostgreSQL.

#### Is there a mobile app?

DocuFlow is a web application with a mobile-responsive design. Access it from any mobile browser. Native iOS/Android apps are on the roadmap.

#### How do I backup my data?

See the [Database Problems](#database-problems) section for backup procedures. For production deployments, automated backups are essential.

#### Can I import existing documents?

Currently, documents must be created individually. Bulk import functionality is planned for a future release. You can use the API to programmatically create documents.

---

## Backend Errors

### Error: `ModuleNotFoundError: No module named 'fastapi'`

**Cause**: Python dependencies not installed.

**Solution**:
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Or with virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

**Prevention**: Always use a virtual environment for Python projects.

---

### Error: `Address already in use` / Port 8000 in use

**Cause**: Another process is using port 8000.

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # On Linux/Mac
netstat -ano | findstr :8000  # On Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn backend.main:app --reload --port 8001
```

---

### Error: `CORS policy` / Cross-origin request blocked

**Cause**: Frontend origin not allowed by backend CORS configuration.

**Solution**:

1. **Check current CORS settings** in `backend/main.py`:
```python
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative port
    "*"  # Allow all (development only!)
]
```

2. **Add your frontend URL**:
```python
origins.append("http://localhost:5174")  # Your custom port
```

3. **For production**, set `ALLOWED_ORIGINS` environment variable:
```bash
export ALLOWED_ORIGINS="https://your-frontend.com,https://www.your-frontend.com"
```

---

### Error: `database is locked`

**Cause**: SQLite doesn't support concurrent writes. Multiple processes or long-running transactions.

**Solution**:

**Immediate fix**:
```bash
# Stop all instances of the backend
pkill -f "uvicorn backend.main:app"

# Delete lock file
rm data/sql_app.db-journal

# Restart backend
uvicorn backend.main:app --reload
```

**Long-term solution**:
- Migrate to PostgreSQL for production
- Ensure only one backend instance is running
- Implement connection pooling

---

### Error: `404 Not Found` for static files

**Cause**: Frontend build not copied to `static/` directory or static files not being served.

**Solution**:

1. **Build frontend**:
```bash
cd frontend
npm run build
```

2. **Copy to static directory**:
```bash
rm -rf static/*
cp -r frontend/dist/* static/
```

3. **Verify static mount** in `backend/main.py`:
```python
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

4. **Check directory structure**:
```bash
ls -la static/
# Should contain index.html, assets/, etc.
```

---

### Error: `SQLAlchemy` migration errors

**Cause**: Database schema mismatch.

**Solution**:

**Option 1 - Fresh start (development only)**:
```bash
# Backup data first!
cp data/sql_app.db data/sql_app.db.backup

# Delete database
rm data/sql_app.db

# Restart backend (will recreate tables)
uvicorn backend.main:app --reload
```

**Option 2 - Manual migration**:
```bash
# Open database
sqlite3 data/sql_app.db

# Check schema
.schema documents

# Add missing column manually
ALTER TABLE documents ADD COLUMN new_field TEXT;

# Exit
.quit
```

---

### Error: `422 Unprocessable Entity`

**Cause**: Request data doesn't match expected schema.

**Solution**:

1. **Check API documentation**: http://localhost:8000/docs

2. **Verify request body matches schema**:
```javascript
// Correct
await fetch('/documents/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: "Test Document",
    type: "Plan",
    status: "In Progress"
  })
});

// Incorrect - missing required fields
await fetch('/documents/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: "Test Document"
    // Missing type and status
  })
});
```

3. **Check console for validation errors**

---

## Frontend Errors

### Error: `npm ERR! code ENOENT`

**Cause**: `node_modules` not installed or corrupted.

**Solution**:
```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install

# Or use npm ci for clean install
npm ci
```

---

### Error: Build fails with memory error

**Cause**: Node.js running out of memory during build.

**Solution**:
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build

# Or in package.json
"scripts": {
  "build": "NODE_OPTIONS='--max-old-space-size=4096' vite build"
}
```

---

### Error: Blank page / White screen

**Cause**: Multiple possible causes.

**Solution**:

1. **Check browser console** for JavaScript errors

2. **Verify API connection**:
```javascript
// In browser console
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

3. **Check API URL configuration**:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

4. **Rebuild frontend**:
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

5. **Check network tab** in DevTools for failed requests

---

### Error: `Cannot read property of undefined`

**Cause**: Accessing property of null/undefined object, often due to async data loading.

**Solution**:

Add null checks:
```svelte
<!-- Bad -->
<div>{document.name}</div>
<div>{document.tasks.length} tasks</div>

<!-- Good -->
{#if document}
  <div>{document.name}</div>
  {#if document.tasks}
    <div>{document.tasks.length} tasks</div>
  {/if}
{/if}
```

Use optional chaining:
```javascript
// Bad
const taskCount = document.tasks.length;

// Good
const taskCount = document?.tasks?.length ?? 0;
```

---

### Error: Changes not reflecting in browser

**Cause**: Browser cache or dev server not detecting changes.

**Solution**:

1. **Hard refresh**:
   - Chrome/Firefox: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

2. **Clear cache**:
   - Open DevTools → Network tab → Check "Disable cache"

3. **Restart dev server**:
```bash
cd frontend
# Stop server (Ctrl+C)
npm run dev
```

4. **Check HMR is working**:
   - Look for "[vite] hot updated" messages in console
   - If not appearing, restart dev server

---

### Error: Styles not applied

**Cause**: CSS not loading or specificity issues.

**Solution**:

1. **Check if styles are scoped**:
```svelte
<style>
  /* Scoped to component */
  .button { }
</style>

<!-- If you need global styles -->
<style global>
  .button { }
</style>
```

2. **Inspect element** in DevTools to see applied styles

3. **Check for typos** in class names

4. **Increase specificity**:
```css
/* Low specificity */
.button { }

/* Higher specificity */
.document-card .button { }
```

---

## OCR Service Issues

### Error: `Failed to connect to OCR service`

**Cause**: OCR service not running or URL misconfigured.

**Solution**:

1. **Check OCR service is running**:
```bash
# Docker
docker ps | grep ocr

# Test endpoint
curl http://localhost:7860/health
```

2. **Start OCR service if not running**:
```bash
# Using Docker Compose
docker-compose up -d ocr-service

# Using Docker directly
docker run -d -p 7860:7860 docling-ocr

# Build if image doesn't exist
docker build -t docling-ocr ./ocr_service
```

3. **Verify OCR URL in settings**:
   - Click Settings in sidebar
   - Check "OCR Service URL" matches your service (e.g., `http://localhost:7860`)
   - Click Save

4. **Check firewall/network**:
```bash
# Test from backend container
docker exec docuflow-app curl http://ocr-service:7860/health
```

---

### Error: OCR processing is very slow

**Cause**: CPU-only processing, large files, or resource constraints.

**Solution**:

1. **Use GPU-enabled hosting**:
   - Deploy OCR service to GPU-enabled platform
   - Use Hugging Face Spaces with GPU

2. **Optimize images before scanning**:
   - Reduce image size/resolution
   - Use compressed PDFs

3. **Increase container resources**:
```yaml
# docker-compose.yml
services:
  ocr-service:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

4. **Process files individually** instead of batch scanning

5. **Use preprocessing** to optimize images:
   - Convert to grayscale
   - Increase contrast
   - Remove noise

---

### Error: OCR extraction is inaccurate

**Cause**: Poor image quality, unsupported language, or complex layout.

**Solution**:

1. **Improve source image quality**:
   - Use high-resolution scans (300 DPI minimum)
   - Ensure good lighting and contrast
   - Avoid skewed or rotated images

2. **Preprocess images**:
   - Adjust brightness/contrast
   - Convert to grayscale
   - Deskew rotated text

3. **Check document type**:
   - Works best with typed text
   - Handwriting recognition is limited
   - Complex layouts may have issues

4. **Test with different images** to isolate the problem

---

### Error: OCR service crashes / Out of memory

**Cause**: Processing large files without sufficient memory.

**Solution**:

1. **Increase memory allocation**:
```bash
docker run -d -p 7860:7860 --memory="4g" docling-ocr
```

2. **Split large PDFs** into smaller chunks

3. **Reduce image resolution** before processing

4. **Monitor resource usage**:
```bash
docker stats docuflow-ocr
```

---

## Database Problems

### Database Backup

**SQLite Backup**:
```bash
# Simple copy (stop backend first)
cp data/sql_app.db data/sql_app.db.backup

# SQLite backup command (can run while backend is running)
sqlite3 data/sql_app.db ".backup data/sql_app.db.backup"

# Export to SQL
sqlite3 data/sql_app.db .dump > backup.sql
```

**PostgreSQL Backup**:
```bash
# Dump database
pg_dump -U username -d docuflow > backup.sql

# With Docker
docker exec postgres pg_dump -U docuflow > backup.sql
```

---

### Database Restore

**SQLite Restore**:
```bash
# Stop backend
# Replace database
cp data/sql_app.db.backup data/sql_app.db

# Or restore from SQL dump
sqlite3 data/sql_app.db < backup.sql

# Restart backend
```

**PostgreSQL Restore**:
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE docuflow;"
psql -U postgres -c "CREATE DATABASE docuflow;"

# Restore
psql -U username -d docuflow < backup.sql
```

---

### Database Corruption

**Symptoms**:
- "database disk image is malformed"
- Random query failures
- Data inconsistencies

**Solution**:

1. **Check integrity**:
```bash
sqlite3 data/sql_app.db "PRAGMA integrity_check;"
```

2. **Attempt recovery**:
```bash
# Dump and restore
sqlite3 data/sql_app.db .dump > dump.sql
mv data/sql_app.db data/sql_app.db.corrupt
sqlite3 data/sql_app.db < dump.sql
```

3. **Restore from backup** if recovery fails

4. **Prevent future corruption**:
   - Use PostgreSQL for production
   - Ensure proper shutdown procedures
   - Regular backups
   - Don't run multiple instances with SQLite

---

### Migration Issues

**Problem**: Database schema out of date after update.

**Solution**:

1. **Let migrations run** on startup (automatic)

2. **If migrations fail**, check logs:
```bash
uvicorn backend.main:app --log-level debug
```

3. **Manual migration**:
```bash
sqlite3 data/sql_app.db

-- Check existing columns
PRAGMA table_info(documents);

-- Add missing columns
ALTER TABLE documents ADD COLUMN priority TEXT DEFAULT 'Medium';

.quit
```

---

## Performance Issues

### Slow Document Loading

**Cause**: Large number of documents, inefficient queries, or network latency.

**Solution**:

1. **Implement pagination** (already supported):
```javascript
fetch('/documents/?skip=0&limit=50')
```

2. **Add database indexes** (already implemented for common queries)

3. **Use filtering** to reduce result set:
```javascript
fetch('/documents/?search=keyword&status=Done')
```

4. **Enable caching** for static assets:
```nginx
location ~* \.(jpg|jpeg|png|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

5. **Optimize database**:
```bash
# SQLite
sqlite3 data/sql_app.db "VACUUM;"

# Analyze query performance
sqlite3 data/sql_app.db "EXPLAIN QUERY PLAN SELECT * FROM documents;"
```

---

### High Memory Usage

**Cause**: Memory leaks, large files, or inefficient code.

**Solution**:

1. **Monitor memory usage**:
```bash
# Docker
docker stats docuflow-app

# System
htop  # or top
```

2. **Restart containers periodically** in production

3. **Limit upload file size**:
```python
# backend/main.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

4. **Use connection pooling**:
```python
# backend/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

5. **Cleanup old files** periodically:
```bash
# Find files older than 90 days
find static/uploads -type f -mtime +90 -delete
```

---

### Slow OCR Processing

See [OCR Service Issues → OCR processing is very slow](#error-ocr-processing-is-very-slow)

---

### Database Growing Too Large

**Cause**: Many documents, attachments, or OCR content.

**Solution**:

1. **Check database size**:
```bash
ls -lh data/sql_app.db
```

2. **Vacuum database** (reclaim space):
```bash
sqlite3 data/sql_app.db "VACUUM;"
```

3. **Archive old documents**:
   - Export to external storage
   - Delete from database

4. **Store attachments externally**:
   - Use object storage (S3, MinIO)
   - Store only references in database

5. **Migrate to PostgreSQL** for better large-dataset performance

---

## Mobile and Browser Compatibility

### Mobile Display Issues

**Problem**: Layout broken on mobile devices.

**Solution**:

1. **Check viewport meta tag** in `index.html`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

2. **Test responsive design**:
   - Chrome DevTools → Device Toolbar (Ctrl+Shift+M)
   - Test on actual devices

3. **Use mobile-first CSS**:
```css
/* Mobile first */
.container {
  width: 100%;
}

/* Tablet and up */
@media (min-width: 768px) {
  .container {
    width: 750px;
  }
}
```

4. **Check touch targets** are large enough (minimum 44x44px)

---

### Browser Compatibility Issues

**Problem**: Features not working in certain browsers.

**Solution**:

1. **Check browser support**:
   - Modern browsers supported: Chrome, Firefox, Safari, Edge
   - IE11 not supported

2. **Update browser** to latest version

3. **Clear browser cache**:
   - Chrome: Settings → Privacy → Clear browsing data
   - Firefox: Options → Privacy → Clear Data

4. **Disable browser extensions** that might interfere

5. **Check console for errors** specific to that browser

---

### Touch Gestures Not Working

**Problem**: Mobile interactions not responding.

**Solution**:

1. **Use touch events**:
```javascript
element.addEventListener('touchstart', handleTouch);
```

2. **Test on actual devices**, not just emulators

3. **Increase touch target size**:
```css
button {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
}
```

4. **Avoid hover-only interactions** on mobile

---

### File Upload Not Working on Mobile

**Problem**: Can't select files on mobile devices.

**Solution**:

1. **Check input accepts mobile file types**:
```html
<input type="file" accept="image/*,application/pdf" />
```

2. **Use capture attribute** for camera:
```html
<input type="file" accept="image/*" capture="camera" />
```

3. **Test on actual devices** (simulators may behave differently)

4. **Check file size limits** on mobile networks

---

## Deployment Issues

### Docker Build Fails

**Cause**: Build errors, network issues, or resource constraints.

**Solution**:

1. **Check Docker logs**:
```bash
docker build -t docuflow . 2>&1 | tee build.log
```

2. **Common fixes**:
```bash
# Clear build cache
docker build --no-cache -t docuflow .

# Increase build resources
# Docker Desktop → Settings → Resources → Increase memory

# Check .dockerignore
cat .dockerignore
```

3. **Fix common errors**:
   - `npm ci` fails → Delete `package-lock.json` and use `npm install`
   - Python package fails → Check `requirements.txt` for version conflicts
   - Out of memory → Increase Docker memory or use multi-stage build optimization

---

### Container Exits Immediately

**Cause**: Application crash, missing dependencies, or configuration error.

**Solution**:

1. **Check container logs**:
```bash
docker logs docuflow-app
```

2. **Run interactively** to debug:
```bash
docker run -it docuflow:latest /bin/bash

# Inside container
python -c "import fastapi; print('FastAPI OK')"
```

3. **Check entrypoint/command**:
```bash
docker inspect docuflow-app | grep -A 5 "Cmd"
```

---

### Environment Variables Not Working

**Cause**: Variables not passed to container or incorrect format.

**Solution**:

1. **Verify variables in container**:
```bash
docker exec docuflow-app env | grep OCR
```

2. **Set correctly in docker-compose.yml**:
```yaml
environment:
  - OCR_SERVICE_URL=http://ocr-service:7860
  # NOT: OCR_SERVICE_URL: "http://ocr-service:7860" (wrong syntax)
```

3. **Use env_file for many variables**:
```yaml
services:
  app:
    env_file:
      - .env
```

---

### Cannot Access Application from Other Devices

**Cause**: Firewall, wrong host binding, or network configuration.

**Solution**:

1. **Bind to 0.0.0.0** instead of localhost:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

2. **Check firewall**:
```bash
# Linux
sudo ufw allow 8000

# Windows
netsh advfirewall firewall add rule name="DocuFlow" dir=in action=allow protocol=TCP localport=8000
```

3. **Use correct IP address**:
```bash
# Find your local IP
ip addr show  # Linux
ipconfig  # Windows
ifconfig  # Mac

# Access from other device
http://192.168.1.x:8000
```

---

### SSL/TLS Certificate Issues

**Cause**: Expired certificate, misconfiguration, or Let's Encrypt rate limits.

**Solution**:

1. **Check certificate expiry**:
```bash
openssl x509 -in /etc/letsencrypt/live/domain/cert.pem -noout -dates
```

2. **Renew certificate**:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

3. **Test certificate**:
```bash
curl -I https://your-domain.com
```

4. **Check Let's Encrypt rate limits**:
   - 50 certificates per domain per week
   - Use staging for testing:
```bash
certbot --staging -d your-domain.com
```

---

## Getting Additional Help

If you've tried the solutions above and still have issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
2. **Search the wiki**: [DocuFlow Wiki](Home.md)
3. **Create a new issue** with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Node version, Docker version)
   - Relevant logs or error messages
   - Screenshots if applicable

4. **Community resources**:
   - GitHub Discussions
   - Stack Overflow (tag: docuflow)

---

## Diagnostic Commands

Useful commands for troubleshooting:

```bash
# System info
uname -a  # OS
python --version
node --version
docker --version

# Service status
docker ps -a
docker logs docuflow-app
systemctl status nginx

# Network
netstat -tulpn | grep 8000
curl -I http://localhost:8000/health

# Database
sqlite3 data/sql_app.db "SELECT COUNT(*) FROM documents;"
sqlite3 data/sql_app.db "PRAGMA integrity_check;"

# Disk space
df -h
du -sh data/

# Logs
tail -f backend.log
journalctl -u nginx -f
```

---

[← Back to Wiki Home](Home.md) | [Next: Contributing →](Contributing.md)
