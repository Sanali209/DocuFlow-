[DESIGN_DOC]
Context:
- Problem: Missing dependency `python-multipart` for `run_solid.py`.
- Constraints: Windows environment, specific Python path.
- Non-goals: Full refactor of build system.

Architecture:
- Components: FASTAPI backend, Svelte frontend (via `run_solid.py`).
- Data flow: Local execution.
- External dependencies: `python-multipart`, `uvicorn`.

Key Decisions:
- [D1] Use full path to python executable for pip install – Rationale: `pip` command not in PATH, avoid ambiguity.

Interfaces:
- N/A

Assumptions & TODOs:
- Assumptions: User will run `run_solid.py` manually after install.
- Open questions: None.
- TODOs (with priority): None.
[/DESIGN_DOC]
