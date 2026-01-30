# DocuFlow - Smart Document & Manufacturing Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-5.0+-orange.svg)](https://svelte.dev/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**DocuFlow** is a comprehensive solution designed to bridge the gap between administrative document management and manufacturing execution. It combines a robust document tracker with a specialized module for visualizing and managing CNC (GNC) programs, designed to run as a **standalone, single-folder executable** on local networks.

## 🚀 Key Features

### 📄 Document Management
- **Smart Tracking:** Complete lifecycle management of Work Orders ("Mihtav") and technical documents.
- **Card-Based UI:** Modern, responsive interface built with Svelte 5.
- **Advanced Search:** Full-text filtering by tags, status, assignees, and dates.
- **Task Management:** Embedded task lists linked directly to documents.

### 🏭 Manufacturing Visualization (GNC)
- **G-Code Viewer:** Visualize Rexroth/Hans Laser 801 (.GNC) files directly in the browser.
- **Geometry Check:** Verify contour shapes, cut layers (P-codes), and sheet dimensions.
- **No CAD Required:** Lightweight canvas-based rendering for quick shop-floor verification.
- **Parts Library:** Manage standard parts ("Sidra") with version control.

### 🔌 Local Network Integration
- **Auto-Import:** Watch "Mihtav" and "Sidra" network folders for new files.
- **Metadata Sync:** Automatically extract material, thickness, and part lists from GNC headers.
- **One-Folder Deployment:** Runs as a portable executable—no Docker or complex installation required.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Configuration](#configuration)
- [Development](#development)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

## 📦 Prerequisites

*   **Operating System:** Windows 10/11 or Linux
*   **Network Access:** Access to local manufacturing shared folders (optional, for sync features)

## 🏗️ Architecture

DocuFlow is built as a **Self-Contained Monolith** designed for simplicity and portability:

```
┌─────────────────────────────────────────────────┐
│              User Workstation                   │
│         (Desktop / Mobile / Tablet)             │
└────────────────┬────────────────────────────────┘
                 │ HTTP (Localhost / LAN)
┌────────────────▼────────────────────────────────┐
│         Distributable App (One-Folder)          │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │         Frontend Assets (Static)         │   │
│  │     (Served by FastAPI StaticFiles)      │   │
│  └───────────────────┬──────────────────────┘   │
│                      │                          │
│  ┌───────────────────▼──────────────────────┐   │
│  │          Backend (FastAPI)               │   │
│  │                                          │   │
│  │   [ API Endpoints ]   [ GNC Processor ]  │   │
│  │   [ File Watcher  ]   [ DB Manager    ]  │   │
│  └───────────────────┬──────────────────────┘   │
│                      │                          │
│  ┌───────────────────▼──────────────────────┐   │
│  │           SQLite Database                │   │
│  │         (local .db file)                 │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## ⚙️ Installation

### Standard User (Pre-built)
1.  Download the latest release zip file.
2.  Extract the `DocuFlow` folder to a convenient location (e.g., `C:\Apps\DocuFlow`).
3.  Run `DocuFlow.exe`.
4.  Open your browser to `http://localhost:8000`.

### Building from Source (Developers)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Sanali209/DocuFlow-.git
    cd DocuFlow-
    ```

2.  **Install Backend Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Install Frontend Dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

4.  **Build Distributable:**
    ```bash
    # Build Frontend
    cd frontend && npm run build && cd ..

    # Package with PyInstaller
    pyinstaller --name DocuFlow --onedir --add-data "frontend/dist:static" backend/main.py
    ```

## 🚀 Running the App (Dev Mode)

To run the application in development mode with hot-reloading:

**1. Backend Terminal:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**2. Frontend Terminal:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` for the frontend dev server.

## 🔧 Configuration

Configuration is managed via the **Settings** page in the application or environment variables.

| Variable | Description | Default |
|----------|-------------|---------|
| `DOC_NAME_REGEX` | Regex to extract Order ID from GNC files | `(?si)Order:\s*(.*?)\s*Date:` |
| `SYNC_FOLDER` | Path to local "Mihtav" root folder | (None) |

## 🗺️ Roadmap

The project is currently evolving through the following stages (see [ROADMAP_GNC.md](ROADMAP_GNC.md) for details):

- [x] **Core Infrastructure:** FastAPI + Svelte setup.
- [ ] **Stage 1:** Standalone GNC Editor & Visualizer.
- [ ] **Stage 2:** Integration with Document Tracker & Task System.
- [ ] **Stage 2.5:** Local Network Folder Sync ("Mihtav"/"Sidra").
- [ ] **Stage 3:** User Management, Workspaces, and RBAC.

## 🤝 Contributing

Contributions are welcome! Please read [wiki/Contributing.md](wiki/Contributing.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by the DocuFlow Team**
