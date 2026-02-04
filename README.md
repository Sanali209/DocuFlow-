# DocuFlow

![Project Status](https://img.shields.io/badge/status-production-green)
![Svelte](https://img.shields.io/badge/svelte-%23f1413d.svg?style=for-the-badge&logo=svelte&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

**DocuFlow** is a manufacturing execution system (MES) for laser cutting shops. It digitizes the workflow from the engineering office to the factory floor, replacing physical paper trails with real-time digital tracking, automated material inventory, and G-code visualization.

## 🚀 Key Features

*   **Real-Time Tracking**: Monitor the status of every work order ("Mihtav") and nesting file ("Sidra") instantly.
*   **Zero-Lag Interface**: Local-first architecture (SQLite) ensures sub-100ms response times even when network shares are slow.
*   **G-Code Visualization**: Built-in viewer for Rexroth/Hans Laser `.801` files.
*   **Inventory Control**: Direct integration with material stock levels to prevent production stoppages.
*   **Shift Handovers**: Seamless digital logging for 24/7 operations.

## 📚 Documentation

Detailed technical documentation is available in the `docs/` directory:

*   **[Technical Reference](docs/TECHNICAL_REFERENCE.md)**: Deep dive into architecture, data models, and deployment.
*   **[Deployment Guide](docs/DEPLOYMENT.md)**: Steps to build and install the executable.
*   **[Business Requirements](BRD.md)**: The original project scope and requirements.

## 📦 Getting Started

### Quick Start (Dev)

1.  **Clone**: `git clone https://github.com/Sanali209/DocuFlow-.git`
2.  **Backend**:
    ```bash
    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
    ```
3.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

For full setup details, please see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

Proprietary Software. Internal use only.
