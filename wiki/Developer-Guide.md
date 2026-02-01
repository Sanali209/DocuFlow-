# Developer Guide

Welcome to the DocuFlow Developer Guide. This document provides comprehensive information for developers working on DocuFlow, focusing on the new standalone architecture.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [GNC Module Development](#gnc-module-development)
4. [File System Watcher](#file-system-watcher)
5. [Building the Distributable](#building-the-distributable)
6. [Code Style & Testing](#code-style--testing)

---

## Development Environment Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 22+**
- **Git**
- **IDE/Editor** (VS Code recommended)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/Sanali209/DocuFlow-.git
cd DocuFlow-

# Backend Setup
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend Setup
cd frontend
npm install
cd ..
```

### Running Development Servers

#### Terminal 1: Backend

```bash
# From project root
uvicorn backend.main:app --reload --port 8000
```
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```
- App: http://localhost:5173

### Environment Variables

Create a `.env` file in the project root:

```env
# Optional: Path to local 'Mihtav' root for testing sync
SYNC_FOLDER_PATH=./test_data/mihtav_root
DOC_NAME_REGEX=(?si)Order:\s*(.*?)\s*Date:
```

---

## Project Structure

```
DocuFlow-/
├── backend/
│   ├── gnc_parser/            # [NEW] GNC parsing logic
│   ├── file_watcher/          # [NEW] Local network sync logic
│   ├── main.py                # Entry point
│   ├── models.py              # DB Models
│   └── ...
├── frontend/
│   ├── src/lib/gnc/           # [NEW] GNC Canvas components
│   ├── src/App.svelte         # Root
│   └── ...
└── README.md
```

## GNC Module Development

### Backend Parsing (`backend/gnc_parser/`)
The GNC Parser is responsible for converting `.gnc` text files into JSON.

**Key Class:** `GNCProcessor`
- **Input:** Raw text content of a GNC file.
- **Output:** Pydantic model `GNCFile` containing `Sheet` info and `contours` list.
- **Logic:** Regex parsing of `===== CONTOUR` delimiters and G-codes (`G00`, `G01`, `G02`, `G03`).

### Frontend Visualization (`frontend/src/lib/gnc/`)
The visualizer uses the HTML5 Canvas API.

**Key Component:** `GncCanvas.svelte`
- **Props:** `gncData` (JSON from backend).
- **Coordinate System:** Must flip Y-axis (Machine Y-Up -> Canvas Y-Down).
- **Interactivity:** `click` events on the canvas should hit-test against contours to trigger selection.

## File System Watcher

### Logic
- **Module:** `backend/file_watcher/`
- **Function:** Periodically scans `SYNC_FOLDER_PATH`.
- **Naming Convention:** Folders starting with `Mihtav_` are treated as Orders.
- **Action:**
    1. Check if Document exists for the Order.
    2. If not, create it.
    3. Check for `.gnc` files inside.
    4. Parse headers (Material, Thickness).
    5. Link files as Attachments.

## Building the Distributable

We use **PyInstaller** to create a single-folder executable that requires no dependencies on the target machine.

### 1. Build Frontend
```bash
cd frontend
npm run build
# Creates frontend/dist/
```

### 2. Build Backend & Bundle
```bash
# From project root
pyinstaller --name DocuFlow \
            --onedir \
            --clean \
            --add-data "frontend/dist:static" \
            backend/main.py
```

### 3. Test
Run `dist/DocuFlow/DocuFlow.exe`. The app should launch and serve the frontend at `http://localhost:8000`.

## Code Style & Testing

### Python
- **Formatter:** Black
- **Linter:** Flake8
- **Tests:** `pytest`

### Frontend
- **Formatter:** Prettier
- **Linter:** ESLint

---

[← Back to Wiki Home](Home.md)
