# Deployment Guide

This guide describes how to deploy DocuFlow as a standalone application on a user's workstation or a local server.

## Overview

DocuFlow is distributed as a **"One-Folder" executable**. This means you do not need to install Python, Node.js, or Docker on the target machine. Everything needed to run the application is contained within the `DocuFlow` folder.

## Installation Steps

### 1. Download the Release
1.  Go to the [Releases](https://github.com/Sanali209/DocuFlow-/releases) page.
2.  Download the latest `DocuFlow_vX.X.zip` for your operating system (Windows or Linux).

### 2. Extract Files
1.  Unzip the archive to your desired location (e.g., `C:\Apps\DocuFlow` or `/opt/DocuFlow`).
2.  Ensure the user has **Read/Write** permissions to this folder (needed for the database and uploads).

### 3. Configuration (Optional)
Open the `config.ini` file (if present) or set Environment Variables to configure:
*   `DOC_NAME_REGEX`: Regex pattern for extracting order numbers.
*   `SYNC_FOLDER`: Path to the root folder for "Mihtav" network shares.

### 4. Run the Application
*   **Windows:** Double-click `DocuFlow.exe`.
*   **Linux:** Run `./DocuFlow`.

A terminal window may appear (displaying server logs), and the application should automatically open in your default web browser at `http://localhost:8000`.

## Building from Source

If you want to build the executable yourself:

### Prerequisites
*   Python 3.12+
*   Node.js 22+
*   PyInstaller (`pip install pyinstaller`)

### Build Steps
1.  **Build Frontend:**
    ```bash
    cd frontend
    npm install
    npm run build
    cd ..
    ```

2.  **Package Backend:**
    ```bash
    pyinstaller --name DocuFlow \
                --onedir \
                --clean \
                --add-data "frontend/dist:static" \
                backend/main.py
    ```

3.  **Locate Output:**
    The built application will be in the `dist/DocuFlow` directory.

## Updating the Application

To update to a new version:
1.  Stop the running application.
2.  Backup your `data/` folder (contains your database).
3.  Replace the `DocuFlow` folder with the new version.
4.  Restore your `data/` folder.
5.  Start the application.
