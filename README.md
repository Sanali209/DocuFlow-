# Document Tracker

A simple application for registering and tracking documents, built with FastAPI and Svelte 5.

## Prerequisites

* Python 3.12+
* Node.js 22+

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

## Running the Application

1.  **Start the Backend** (From the project root)

    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```

    The API will be available at http://localhost:8000.
    Swagger UI: http://localhost:8000/docs

2.  **Start the Frontend**

    ```bash
    cd frontend
    npm run dev
    ```

    The application will be available at http://localhost:5173.

## Features

* Register new documents (Name, Type, Status, Date).
* List documents.
* Search documents by name.
* Filter documents by type and status.
* Update document status.
* Delete documents.
