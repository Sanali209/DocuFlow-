# User Requirements Document (URD)
**System:** DocuFlow
**Version:** 1.0

## 1. Introduction
This document outlines the requirements from the perspective of the end-users. It defines "User Stories" and specific capabilities each role expects from the system.

## 2. User Roles
*   **Operator:** Works on the machine, executes the programs.
*   **Technologist:** Prepares and fixes programs in the office.
*   **Manager:** Oversees the flow of orders.

## 3. User Requirements

### 3.1 As an Operator
*   **UR-01:** I want to quickly find a document by typing the "Mihtav" (Order) number so I don't waste time searching folders.
*   **UR-02:** I want to see a visual preview of the GNC file to confirm it matches the physical drawing before I start the machine.
*   **UR-03:** I want to see which "Parts" (details) are included in a specific program/task.
*   **UR-04:** I need the interface to be clear and readable on my workstation tablet.

### 3.2 As a Technologist
*   **UR-05:** I want to upload a GNC file and immediately see if the contours are closed and within the sheet limits.
*   **UR-06:** I want to change the "Cutting Layer" (P660) for a specific contour without manually editing the text file coordinates.
*   **UR-07:** I want the system to auto-detect the Material and Thickness from the GNC file header so I don't have to type it.
*   **UR-08:** I want to save a library of standard parts ("Sidra") to easily reuse them in future tasks.

### 3.3 As a Manager
*   **UR-09:** I want to see a dashboard of all active "Mihtav" orders and their status (Pending/Done).
*   **UR-10:** I want to search for documents using multiple tags (e.g., "Urgent" + "Material:Steel") to prioritize work.
*   **UR-11:** I want to assign specific users to Workspaces (machines) to track who is working on what.
*   **UR-12:** I want to restrict "Delete" permissions so that operators cannot accidentally remove approved files.

## 4. Acceptance Criteria
*   Search results must appear within 2 seconds.
*   GNC visualization must load within 3 seconds for files < 1MB.
*   The system must correctly identify 95% of document names from OCR scans.
