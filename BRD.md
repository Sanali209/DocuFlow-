# Business Requirements Document (BRD)
**Project Name:** DocuFlow (incl. GNC Module)
**Date:** 2024-01-29
**Version:** 1.0

## 1. Executive Summary
The goal of the DocuFlow project is to digitize and streamline the document management and manufacturing verification processes within the organization. Currently, workflows rely on physical paper documents and manual file handling, leading to inefficiencies, tracking errors, and lack of visibility. This system will serve as a centralized digital hub for document tracking, intelligent OCR extraction, and direct visualization/editing of manufacturing programs (GNC).

## 2. Business Objectives
*   **Digitization:** Eliminate manual data entry by using AI-powered OCR to extract data from scanned paper documents.
*   **Efficiency:** Reduce the time spent searching for files and verifying manufacturing program geometry by 40%.
*   **Accuracy:** Minimize human error in checking CNC program parameters (P-codes) and geometry.
*   **Traceability:** Provide full visibility into the status of every Work Order ("Mihtav") and manufacturing Part.
*   **Integration:** Seamlessly synchronize with existing local network file structures ("Mihtav", "Sidra") to avoid disrupting current shop-floor habits.

## 3. Scope
### In Scope
*   **Document Management System (DMS):** Storage, tagging, filtering, and searching of digital documents.
*   **OCR Integration:** Automatic text and table extraction from PDFs/Images.
*   **Task Tracking:** Assigning and monitoring tasks linked to specific documents.
*   **GNC Module:** Visualization and parameter editing of Rexroth/Hans Laser 801 G-code files.
*   **Network Sync:** Automatic importing of files from local network folders.

### Out of Scope
*   Direct machine control (DNC) or sending files to machines via serial protocols (files are saved to network only).
*   ERP system replacement (integrates with, does not replace core financial systems).

## 4. Key Stakeholders
*   **Production Managers:** Need visibility into order status and potential bottlenecks.
*   **Technologists:** Responsible for verifying GNC programs and editing P-codes.
*   **Operators:** Need quick access to visual confirmations of parts before cutting.
*   **IT/Admin:** Responsible for system maintenance and network configuration.

## 5. Success Metrics
*   **Adoption Rate:** 100% of new Work Orders tracked in the system within 3 months.
*   **Processing Time:** Average time to verify a GNC file reduced from 15 mins to 5 mins.
*   **Error Rate:** Reduction in scrapped parts due to incorrect P-codes.
