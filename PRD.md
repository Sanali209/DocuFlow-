# Product Requirements Document (PRD)
**Product:** DocuFlow & GNC Editor
**Version:** 1.0

## 1. Product Overview
DocuFlow is a web-based platform that combines an Intelligent Document Management System (IDMS) with a specialized Manufacturing Execution visualizer for laser cutting programs. It bridges the gap between administrative paperwork (Orders) and technical execution (GNC files).

## 2. User Personas
*   **The Archivist:** Scans physical documents. Needs fast upload and reliable auto-naming.
*   **The Technologist:** Reviews G-code files. Needs to see the shape, check cut layers (P-codes), and make quick edits without opening a text editor.
*   **The Shop Floor Operator:** Looks for the "Mihtav" (Order) number to find the right program and verify the part count.

## 3. Key Features

### 3.1 Document Core
*   **Card-Based Interface:** Visual representation of documents with status badges.
*   **Intelligent Search:** Full-text search across tags and metadata.
*   **Filter Presets:** Save complex filter combinations (e.g., "My Pending Urgent Tasks") for quick access.

### 3.2 GNC Visualizer & Editor
*   **Canvas Rendering:** Visualize `.GNC` geometry (Lines, Arcs G02/G03) on an HTML5 canvas.
*   **Layer/Parameter Editing:** Click a contour to edit its P-codes (P660, P150) directly in a side panel.
*   **Machine Coordinate Transform:** Automatically flip coordinates (Y-Up to Y-Down) for correct screen display.
*   **Validation:** Warn if contours exceed the defined Sheet dimensions.

### 3.3 File System Integration
*   **Auto-Import:** Watch "Mihtav" (Order) and "Sidra" (Series) folders on the local network.
*   **Metadata Extraction:** Parse GNC headers to find Material type, Part names, and timestamps.
*   **Sync:** Update system records when physical files are modified.

### 3.4 User Management
*   **Workspaces:** Assign users to specific physical machines/stations.
*   **Shift Logs:** Shift Handover notes and operator session tracking.
*   **Roles:** Differentiate between View-Only users (Operators) and Editors (Technologists).

### 3.5 Material & Nesting
*   **Warehouse:** Track sheets (Material, Thickness, Size) and Reservations.
*   **Nesting:** Auto-pack parts onto sheets to calculate required material.
*   **Reverse Engineering:** Custom parser to decode `_801` files and recover metadata/geometry modifications made on the machine.

## 4. User Experience (UX)
*   **Mobile-First:** The UI must be usable on tablets used by machine operators.
*   **Dark/Light Mode:** Support for different shop floor lighting conditions (High contrast required).
*   **Feedback:** Toast notifications for all async actions (Upload, Save, OCR).

## 5. Constraints
*   **Network:** Must operate reliably on the local Intranet.
*   **Browser:** Support for modern Chrome/Edge browsers (Canvas API support required).
