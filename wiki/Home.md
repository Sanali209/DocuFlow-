# Welcome to the DocuFlow Wiki

DocuFlow is a specialized Document Management and Manufacturing Verification system. It is designed to help manufacturing teams organize Work Orders, visualize GNC (CNC) programs, and track production tasks efficiently.

## Core Modules

### 1. Document Management
- **Centralized Tracking:** Manage all your technical documents and Work Orders in one place.
- **Tagging & Filtering:** Quickly find what you need using smart tags and status filters.
- **Journaling:** Keep a history of notes and decisions for every document.

### 2. GNC Visualization (New!)
- **Browser-Based Viewer:** Check geometry of `.GNC` files without needing CAD software.
- **Parameter Inspection:** Verify P-codes and cut layers instantly.
- **Parts Library:** Manage standard parts with version control.

### 3. Local Network Integration
- **Auto-Sync:** The system watches your local network folders ("Mihtav" and "Sidra").
- **Seamless Import:** New files added to the network are automatically registered in DocuFlow.

## Getting Started

- **[Installation Guide](Deployment-Guide)** - How to install and run DocuFlow.
- **[User Guide](User-Guide)** - How to use the features.
- **[Developer Guide](Developer-Guide)** - Contributing to the codebase.
- **[FAQ & Troubleshooting](FAQ-and-Troubleshooting)** - Common solutions.

## Architecture

DocuFlow is a **Self-Contained Monolithic Application**. It bundles a high-performance **FastAPI** backend with a reactive **Svelte 5** frontend into a single portable executable.

[Read more about the Architecture...](https://github.com/Sanali209/DocuFlow-/blob/main/ARCHITECTURE.md)
