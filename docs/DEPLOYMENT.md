# Deployment Guide

This guide describes how to build and deploy DocuFlow as a standalone executable.

## Build Process

We usage a unified build script `build_dist.py` that automates:
1.  Building the compiled Svelte frontend (`frontend/dist`).
2.  Packaging the Python backend and embedding the frontend assets using **PyInstaller**.

### Prerequisites for Building

*   Node.js installed.
*   Python environment active with `requirements.txt` installed.
*   `pyinstaller` installed (`pip install pyinstaller`).

### Running the Build

Run the build script from the repository root:

```bash
python build_dist.py
```

### Output

The build artifacts will be located in:
```
/dist/DocuFlow/
```

## Installation on Client Machines

DocuFlow is a "portable" application (One-Folder Distributable).

1.  **Copy**: Copy the entire `dist/DocuFlow` folder to the target machine (e.g., `C:\Program Files\DocuFlow` or `Z:\Apps\DocuFlow`).
2.  **Shortcut**: Create a shortcut to `DocuFlow.exe` (or `main.exe` depending on the build name) on the user's desktop.
3.  **First Run**:
    *   Ensure the machine has access to the network share `Z:`.
    *   Launch the executable.
    *   (Optional) If no database is found, the app may prompt for configuration (see Architecture).

## Updates

To update the application:
1.  Build a new version.
2.  Replace the `DocuFlow` folder on the target machine (ensure the app is closed first).
3.  **Note**: The database file `data.db` is stored EXTERNALLY (on the Z drive or separate data folder), so updating the executable folder will NOT overwrite user data.

## Troubleshooting

*   **"Failed to execute script main"**: Check `logs/client.log` (if configured) or run from a terminal to see stderr output.
*   **Missing Assets**: Verify `_internal/static` exists in the dist folder.
