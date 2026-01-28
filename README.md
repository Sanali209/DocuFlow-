# Document Tracker

A simple application for registering and tracking documents, built with FastAPI and Svelte 5, featuring AI-powered OCR using IBM Docling.

## Prerequisites

* Python 3.12+
* Node.js 22+
* Docker (for OCR service)

## Setup

1.  **Backend**

    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **Frontend**

    ```bash
    cd frontend
    npm install
    cd ..
    ```

3.  **OCR Service** (Optional, but required for scanning)

    The OCR service is a separate FastAPI application that uses Docling. It is designed to be deployed via Docker, ideally on Hugging Face Spaces (CPU or GPU).

    ```bash
    cd ocr_service
    docker build -t docling-ocr .
    docker run -p 7860:7860 docling-ocr
    ```

## Running the Application
### Using Docker Compose (Recommended)
1. **Build and Run**:
   ```bash
   docker-compose up --build
   ```
2. **Access**:
   - Web App: [http://localhost:8000](http://localhost:8000)
   - OCR Service (Direct): [http://localhost:7860](http://localhost:7860)

### Manual Setup


1.  **Start the Backend** (From the project root)

    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```

    The API will be available at http://localhost:8000.
    Swagger UI: http://localhost:8000/docs

    **Environment Variables:**
    * `OCR_SERVICE_URL`: URL of the OCR service (default: `http://localhost:7860`). Can also be configured via UI Settings.
    * `DOC_NAME_REGEX`: Regex to extract document name (default: `(?si)Order:\s*(.*?)\s*Date:`).

2.  **Start the Frontend**

    ```bash
    cd frontend
    npm run dev
    ```

    The application will be available at http://localhost:5173.

## Features

* **Document Management**: Register, list, update, and delete documents.
* **OCR Scanning**:
    * Scan images or PDFs to extract text and tables using Docling.
    * Supports multi-page scanning (select multiple files).
    * Auto-extracts "Order Name" based on configured Regex.
    * Appends recognized content sequentially.
* **Markdown Viewer**: View recognized content with formatted tables and headers.
* **Settings**: Configure the OCR Service URL directly from the application.
* **Filtering & Search**: Filter by type/status and search by name.
