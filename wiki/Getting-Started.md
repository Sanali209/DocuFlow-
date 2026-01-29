# Getting Started with DocuFlow

This guide will help you set up and run DocuFlow on your local machine or server.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required
- **Python 3.12 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 22 or higher** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/)

### Optional
- **Docker** - For containerized deployment and OCR service
- **Docker Compose** - For multi-container setup

## Installation

### Option 1: Quick Start with Docker Compose (Recommended)

This is the easiest way to get DocuFlow up and running with all services.

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sanali209/DocuFlow-.git
   cd DocuFlow-
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Main Application: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - OCR Service: http://localhost:7860

That's it! DocuFlow is now running with all features enabled.

### Option 2: Manual Setup (Development)

For development with hot-reload capabilities:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-
```

#### Step 2: Set Up the Backend

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# The database will be created automatically on first run
```

#### Step 3: Set Up the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

#### Step 4: Set Up OCR Service (Optional)

The OCR service is optional but required for document scanning features.

```bash
# Build the OCR service Docker image
cd ocr_service
docker build -t docling-ocr .

# Run the OCR service
docker run -d -p 7860:7860 --name docuflow-ocr docling-ocr

# Verify it's running
curl http://localhost:7860/health
```

Alternatively, you can use a hosted OCR service (e.g., on Hugging Face Spaces) and configure the URL in settings.

## Running the Application

### Development Mode

#### Terminal 1: Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Terminal 2: Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:5173

#### Terminal 3: OCR Service (if testing scanning)

```bash
docker start docuflow-ocr
# Or if not created yet:
docker run -p 7860:7860 docling-ocr
```

### Production Mode

For production deployment, see the [Deployment Guide](Deployment-Guide.md).

## First Steps

### 1. Access the Application

Open your browser and navigate to:
- **Docker Compose**: http://localhost:8000
- **Development**: http://localhost:5173

### 2. Configure OCR Service (Optional)

If you're using a different OCR service URL:

1. Click the **Settings** icon in the sidebar (⚙️)
2. Enter your OCR Service URL (e.g., `http://localhost:7860` or your hosted URL)
3. Optionally configure the document name extraction regex
4. Click **Save**

### 3. Create Your First Document

1. Click the **New Document** button (+) in the sidebar
2. Fill in the document details:
   - **Name**: Document title
   - **Type**: Select from Plan, Mail, Order, Report, etc.
   - **Status**: In Progress, Done, etc.
   - **Author**: Person responsible
   - **Description**: Brief description
3. (Optional) Scan a document:
   - Click **Select Files to Scan**
   - Choose one or more PDF/image files
   - Click **Scan** to extract text
4. Click **Save**

### 4. Add Tasks to a Document

1. Locate your document in the list
2. In the **Tasks** section, click **Add Task**
3. Enter task details:
   - **Task name**
   - **Status**: Planned, Pending, or Done
   - **Assignee**: Person assigned to the task
4. Click the checkmark to save

### 5. Add Notes

1. Click the **Add Note** button in a document card
2. Enter your note text
3. Click **Add** - the note will be displayed inline with a timestamp

### 6. Attach Files

1. Click **Add Attachment** in a document card
2. Select a file (image or PDF)
3. The file will be uploaded and displayed in the attachments gallery
4. Click on thumbnails to preview

### 7. Use Filters

1. Use the search bar to find documents by name, description, or content
2. Click **Filters** to access advanced filtering:
   - Filter by Type, Status, Tags
   - Filter by Date Range
   - Filter by Task Status or Assignee
3. Save frequently-used filters as **Presets** for quick access

## Verification

### Check Backend Health

```bash
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy"}
```

### Check OCR Service

```bash
curl http://localhost:7860/health

# Expected response:
# {"status":"healthy","models_loaded":true}
```

### Test API

```bash
# List documents
curl http://localhost:8000/documents/

# Expected: JSON array of documents (empty if none created yet)
```

## Next Steps

Now that DocuFlow is running:

1. **Explore Features** - Read the [User Guide](User-Guide.md) for detailed feature walkthroughs
2. **Configure Settings** - Customize OCR and extraction patterns
3. **Import Data** - Start scanning and organizing your documents
4. **Learn the API** - Check out the [API Documentation](API-Documentation.md)
5. **Deploy to Production** - Follow the [Deployment Guide](Deployment-Guide.md)

## Troubleshooting

### Common Issues

#### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies
```bash
pip install -r backend/requirements.txt
```

#### Frontend Build Fails

**Error**: `npm ERR! code ENOENT`

**Solution**: Install dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Port Already in Use

**Error**: `Address already in use`

**Solution**: Change the port or stop the conflicting service
```bash
# Check what's using the port
lsof -i :8000

# Use a different port
uvicorn backend.main:app --reload --port 8001
```

#### OCR Service Connection Error

**Error**: `Failed to connect to OCR service`

**Solution**: 
1. Verify OCR service is running: `docker ps | grep docling-ocr`
2. Check the URL in Settings matches your OCR service
3. Test direct connection: `curl http://localhost:7860/health`

#### Database Locked

**Error**: `database is locked`

**Solution**: SQLite doesn't support multiple simultaneous writers. Ensure only one instance is running, or migrate to PostgreSQL for production.

### Getting Help

If you encounter other issues:
1. Check the [FAQ & Troubleshooting](FAQ-and-Troubleshooting.md) page
2. Search existing [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
3. Create a new issue with:
   - Your environment (OS, Python version, Node version)
   - Steps to reproduce
   - Error messages and logs

## Additional Resources

- [User Guide](User-Guide.md) - Feature documentation
- [Developer Guide](Developer-Guide.md) - Development workflow
- [API Documentation](API-Documentation.md) - REST API reference
- [Deployment Guide](Deployment-Guide.md) - Production deployment

---

[← Back to Wiki Home](Home.md) | [Next: User Guide →](User-Guide.md)
