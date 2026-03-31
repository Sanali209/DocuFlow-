# Session 867a9481 - Execution Start

[PROGRESS]
- Phase: Implementation
- Step: Updating backend schemas
- Completed: 0/10 steps
- Next: Modify backend/schemas.py
[/PROGRESS]

[DESIGN_DOC]
Context:
- Problem: Implement GNC editor enhancements (multi-sheet, stock, inventory, order integration).
- Constraints: Maintain existing architecture.
- Non-goals: 

Architecture:
- Components:
    - Backend: gnc_projects router, updated schemas.
    - Frontend: GncView (multi-sheet), DocumentForm (Order button).
    - Worker: NestingWorker (svgnest).

Key Decisions:
- [D6] Using `GNCProject` and `GNCProjectSheet` schemas for multi-sheet state.

Interfaces:

Assumptions & TODOs:
- Assumptions:
- Open questions:
- TODOs (with priority):
[/DESIGN_DOC]
