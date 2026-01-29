# DocuFlow - Smart Document Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-5.0+-orange.svg)](https://svelte.dev/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**DocuFlow** is a powerful, modern document management system that combines robust tracking capabilities with AI-powered OCR technology. Built with FastAPI and Svelte 5, it offers a seamless experience for registering, organizing, and searching through documents with intelligent text extraction powered by IBM Docling.

## 🚀 Key Features at a Glance

- **Smart Document Management** - Complete CRUD operations with rich metadata
- **AI-Powered OCR** - Extract text and tables from images/PDFs using IBM Docling
- **Advanced Filtering** - Multi-criteria search with saved filter presets
- **Task Management** - Embedded task lists with status tracking and assignee management
- **Journal & Notes** - Document-linked notes and activity logs
- **File Attachments** - Upload and preview images/PDFs with gallery view
- **Tag System** - Smart categorization with autocomplete
- **Mobile Optimized** - Responsive design with touch-friendly interface
- **Markdown Support** - Rich text viewing with formatted tables and headers

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Features](#features)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 📦 Prerequisites

Before getting started, ensure you have the following installed:

* **Python 3.12+** - Backend runtime
* **Node.js 22+** - Frontend build and development
* **Docker** (Optional) - For containerized deployment and OCR service
* **Git** - Version control

## 🏗️ Architecture Overview

DocuFlow follows a modern microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Svelte 5)               │
│              Responsive UI with Vite                │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│              Backend (FastAPI)                      │
│     SQLAlchemy ORM │ Pydantic Schemas              │
│              SQLite Database                        │
└────────────────────┬────────────────────────────────┘
                     │ HTTP Requests
┌────────────────────▼────────────────────────────────┐
│        OCR Service (FastAPI + Docling)             │
│     IBM Docling │ EasyOCR │ Tesseract             │
│          Dockerized Microservice                    │
└─────────────────────────────────────────────────────┘
```

**Components:**
- **Frontend**: Modern Svelte 5 with Runes API, built with Vite
- **Backend**: FastAPI with SQLAlchemy ORM and SQLite database
- **OCR Service**: Separate microservice with IBM Docling for document processing
- **Static Assets**: Served by FastAPI in production mode

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-
```

### 2. Backend Setup

Install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

The backend uses SQLite by default, so no additional database setup is required.

### 3. Frontend Setup

Install Node.js dependencies:

```bash
cd frontend
npm install
cd ..
```

### 4. OCR Service Setup (Optional)

The OCR service is optional but required for document scanning features. It's designed to run in a separate container:

```bash
cd ocr_service
docker build -t docling-ocr .
docker run -p 7860:7860 docling-ocr
```

**Alternative**: Deploy the OCR service to Hugging Face Spaces (recommended for production) and configure the URL in the application settings.

## 🚀 Running the Application

### Option 1: Using Docker Compose (Recommended)

The easiest way to run the entire stack:

```bash
docker-compose up --build
```

**Access the application:**
- Main Application: [http://localhost:8000](http://localhost:8000)
- OCR Service API: [http://localhost:7860](http://localhost:7860)
- Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Manual Setup (Development)

For development with hot-reload capabilities:

#### Start the Backend

From the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

**Available endpoints:**
- API: [http://localhost:8000](http://localhost:8000)
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Start the Frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173) with hot module replacement enabled.

## ✨ Features

### Document Management
* **Complete CRUD Operations**: Create, read, update, and delete documents
* **Rich Metadata**: Track Author, Description, Registration Date, Done Date, Type, and Status
* **Modern Card View**: Attractive card-based layout with status indicators and visual tags
* **Full-Text Search**: Search across document names, descriptions, and OCR-extracted content
* **Smart Categorization**: Flexible type system (Plan, Mail, Order, Report, etc.)

### Task Management
* **Embedded Tasks**: Create and manage tasks directly within documents
* **Status Tracking**: Track tasks as Planned, Pending, or Done
* **Assignee Management**: Assign tasks to specific team members
* **Task Filtering**: Filter documents by task status and assignee
* **Inline Display**: Tasks appear directly in document cards for quick access

### Notes & Journal
* **Document-Linked Notes**: Create journal entries tied to specific documents
* **Inline Display**: Notes appear within document cards
* **Timestamped Entries**: Automatic timestamp tracking for all notes
* **Activity Logging**: Keep track of document-related activities

### File Attachments
* **Multi-File Support**: Attach multiple images and PDFs to documents
* **Auto-Save on Scan**: Scanned files are automatically saved as attachments
* **Gallery View**: Quick preview modal with image thumbnails
* **Download Support**: Direct download of attached files

### Advanced Filtering & Search
* **Multi-Criteria Filtering**: Combine search text, type, status, tags, dates, and assignees
* **Date Range Filters**: Filter by registration date or completion date
* **Tag-Based Search**: Quick filtering by document tags
* **Task Type Filters**: Show documents containing specific task types
* **Assignee Filters**: Filter tasks by assigned team member
* **Filter Presets**: Save and quickly load commonly-used filter configurations

### OCR & Document Scanning
* **AI-Powered OCR**: Extract text and tables using IBM Docling
* **Multi-Page Support**: Scan multiple files in one operation
* **Table Recognition**: Preserve table structures in markdown format
* **Auto-Extraction**: Automatically extract document names using configurable regex
* **Sequential Processing**: Scan multiple files with content appending
* **Format Support**: Process both images (JPEG, PNG) and PDF documents

### User Experience
* **Mobile-First Design**: Fully responsive interface optimized for mobile devices
* **Icon-Only Sidebar**: Compact navigation on mobile screens
* **Touch-Friendly**: Optimized touch targets and spacing
* **Markdown Rendering**: View formatted content with tables and headers
* **Dark Mode Ready**: Clean, modern interface design
* **Fast Navigation**: Quick access to all features from the sidebar

## ⚙️ Configuration

### Environment Variables

DocuFlow can be configured using environment variables or through the application settings UI.

**Backend Environment Variables:**

```bash
# OCR Service Configuration
OCR_SERVICE_URL=http://localhost:7860  # Default OCR service endpoint

# Document Name Extraction
DOC_NAME_REGEX="(?si)Order:\s*(.*?)\s*Date:"  # Regex pattern for auto-extraction

# Database
DATABASE_URL=sqlite:///./documents.db  # SQLite database path (default)
```

### Application Settings

Settings can also be configured through the UI:

1. Click the **Settings** icon in the sidebar
2. Configure:
   - **OCR Service URL**: Point to your deployed OCR service
   - **Document Name Regex**: Customize pattern for auto-extracting document names

Settings are persisted in the database and take precedence over environment variables.

## 🌐 Deployment

### Production Deployment with Docker

Build and run the production container:

```bash
# Build the image
docker build -t docuflow .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data docuflow
```

The application will be available at `http://localhost:8000`.

### Platform-Specific Deployment Guides

#### Deploy to Railway

See [RAILWAY.md](RAILWAY.md) for detailed Railway deployment instructions.

#### Deploy to Koyeb with Docker

See [DOCKER_KOYEB.md](DOCKER_KOYEB.md) for Koyeb deployment instructions.

#### Deploy OCR Service to Hugging Face Spaces

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Choose "Docker" as the SDK
3. Upload the contents of `ocr_service/` directory
4. The Space will automatically build and deploy
5. Update the OCR Service URL in DocuFlow settings

### Reverse Proxy Configuration

For production deployments, use a reverse proxy like Nginx:

```nginx
server {
    listen 80;
    server_name docuflow.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Increase upload size for file attachments
    client_max_body_size 50M;
}
```

## 👨‍💻 Development

### Project Structure

```
DocuFlow-/
├── backend/              # FastAPI backend application
│   ├── main.py          # Main application entry point
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   ├── database.py      # Database configuration
│   └── requirements.txt # Python dependencies
├── frontend/            # Svelte 5 frontend application
│   ├── src/            # Source files
│   │   ├── App.svelte  # Root component
│   │   └── components/ # UI components
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
├── ocr_service/        # Docling OCR microservice
│   ├── main.py         # OCR service API
│   ├── Dockerfile      # OCR service container
│   └── requirements.txt
├── docs/               # Documentation
├── docker-compose.yml  # Multi-container setup
├── Dockerfile          # Main application container
└── README.md           # This file
```

### Running Tests

**Backend Tests:**

```bash
cd backend
pytest test_main.py
pytest test_features.py
pytest test_settings.py
pytest test_attachment_update.py
```

**Frontend Development:**

```bash
cd frontend
npm run dev      # Development server with HMR
npm run build    # Production build
npm run preview  # Preview production build
```

### Code Style

- **Backend**: Follow PEP 8 guidelines for Python code
- **Frontend**: Use Prettier for consistent formatting
- **Commits**: Use conventional commit messages

### Database Migrations

The application automatically handles schema migrations on startup. New columns are added via ALTER TABLE statements in `main.py`.

## 🐛 Troubleshooting

### Common Issues

**Issue: OCR Service Connection Error**
```
Solution: Ensure the OCR service is running and the URL is correctly configured in Settings.
Check: docker ps | grep docling-ocr
```

**Issue: Port Already in Use**
```
Solution: Change the port in docker-compose.yml or stop the conflicting service.
Check: lsof -i :8000
```

**Issue: Frontend Build Fails**
```
Solution: Clear node_modules and reinstall dependencies
Commands:
  rm -rf frontend/node_modules
  cd frontend && npm install
```

**Issue: Database Locked**
```
Solution: Close any other connections to the SQLite database
Note: SQLite doesn't support multiple simultaneous writers
```

**Issue: File Upload Too Large**
```
Solution: Check client_max_body_size in your reverse proxy configuration
Increase FastAPI's file size limit if needed
```

### Debug Mode

Enable debug logging:

```bash
# Backend
uvicorn backend.main:app --reload --log-level debug

# Frontend (development mode has built-in debugging)
cd frontend && npm run dev
```

### Performance Optimization

- **Large Databases**: Consider migrating to PostgreSQL for production
- **OCR Processing**: Use GPU-enabled instances for faster processing
- **Static Assets**: Use CDN for serving frontend assets in production
- **Database Indexing**: Indexes are automatically created on document names

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the code style guidelines
4. **Test your changes**: Run the test suite
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes clearly

### Development Guidelines

- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation for API changes
- Follow existing code style and patterns
- Keep pull requests focused and atomic

### Reporting Issues

Found a bug? Have a feature request?

1. Check if the issue already exists
2. Create a new issue with a clear title and description
3. Include steps to reproduce for bugs
4. Add relevant labels

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **Svelte** - Cybernetically enhanced web apps
- **IBM Docling** - Advanced document understanding AI
- **SQLAlchemy** - SQL toolkit and ORM
- **Vite** - Next generation frontend tooling

## 📞 Support

- 📧 Email: [Your Email]
- 🐛 Issues: [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
- 📖 Documentation: [Wiki](https://github.com/Sanali209/DocuFlow-/wiki)

## 🗺️ Roadmap

- [ ] PostgreSQL support
- [ ] Multi-user authentication and authorization
- [ ] Document version control
- [ ] Export functionality (PDF, Excel)
- [ ] Advanced analytics and reporting
- [ ] Document templates
- [ ] Email notifications
- [ ] API webhooks
- [ ] Mobile apps (iOS/Android)

---

**Made with ❤️ by the DocuFlow Team**
