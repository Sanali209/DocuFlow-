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

### 3.1 As an Operator (Bus Factory Shift Worker)
*   **UR-01:** I want to transfer shift information (notes/problems) to the next operator digitally.
*   **UR-02:** I want the system to recognize the file I edited on the machine (saved with `_801`) and update the central record without losing the original order info.
*   **UR-03:** I want to see a packing plan (Nesting) to know how to arrange parts on the sheet.

### 3.2 As a Technologist (Office)
*   **UR-05:** I receive a drawing from the customer, select standard parts ("Sidra"), and want the system to generate the Work Order and Packing Plan automatically.
*   **UR-06:** I want to reserve specific sheets (e.g., "Steel 1.5mm, 3000x1500") for an order so they aren't used by mistake.
*   **UR-07:** I need to analyze "Action Logs" to see if operators are manually editing P-codes too often (indicating a process problem).

### 3.3 As a Manager
*   **UR-09:** I want to track material consumption and "Remnants" (offcuts) to reduce waste.
*   **UR-10:** I want to see a 24/7 timeline of machine activity based on the Shift Logs.

## 4. Acceptance Criteria
*   Search results must appear within 2 seconds.
*   GNC visualization must load within 3 seconds for files < 1MB.
*   The system must correctly identify 95% of document names from OCR scans.
