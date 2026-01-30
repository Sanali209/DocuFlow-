# User Guide

Complete guide to using all features of DocuFlow.

## Table of Contents

1. [Document Management](#document-management)
2. [GNC Visualization](#gnc-visualization)
3. [Local Network Integration](#local-network-integration)
4. [Task Management](#task-management)
5. [Search and Filtering](#search-and-filtering)
6. [Settings](#settings)

---

## Document Management

### Viewing Documents
Documents are displayed as cards showing status, author, and tags.
- **Card View:** Click a card to see details.
- **Filters:** Use the filter panel (funnel icon) to find documents by Type, Status, or Tags.

### Creating Documents
1. Click **➕ New Document**.
2. Fill in metadata (Name, Type, Status).
3. **Attachments:** Upload files directly or rely on the [Local Network Integration](#local-network-integration) to auto-populate files.

## GNC Visualization

DocuFlow includes a specialized viewer for CNC programs (.GNC files).

### Opening a GNC File
1. Open a Document that has a linked `.GNC` file.
2. Click the **View Geometry** button next to the attachment.
3. The **GNC Viewer** will open.

### Using the Viewer
- **Pan:** Click and drag to move the view.
- **Zoom:** Use the mouse wheel to zoom in/out.
- **Inspect:** Click on any line or arc to see its properties (Coordinates, P-Codes).
- **Edit:** (Coming Soon) Change P-codes in the right-hand panel.

## Local Network Integration

DocuFlow automatically syncs with your manufacturing network folders.

### How it Works
- The system watches the configured **Sync Folder**.
- **Mihtav (Orders):** When you drop a folder named `Mihtav_12345` into the sync root, DocuFlow automatically creates an Order Document #12345.
- **GNC Files:** Any `.gnc` files inside that folder are automatically attached to the document.
- **Metadata:** Material type and thickness are extracted from the GNC header and saved to the document description.

### Manual Sync
If files don't appear immediately, go to **Settings** and click **Force Sync**.

## Task Management

- **Add Task:** In a document card, click `+ Add Task`.
- **Assign:** Select a user/machine from the dropdown.
- **Status:** Toggle between Planned (Gray) -> Pending (Yellow) -> Done (Green).

## Search and Filtering

- **Quick Search:** Type in the top bar to find Documents by Name or Order Number.
- **Advanced:** Click the Filter icon to search by:
    - **Tag:** e.g., "Urgent"
    - **Status:** e.g., "In Progress"
    - **Date:** Registration range.

## Settings

### Configuration
- **Doc Name Regex:** Pattern to extract order numbers from filenames.
- **Sync Folder:** Path to your local "Mihtav" root directory.

---

[← Back to Home](Home.md)
