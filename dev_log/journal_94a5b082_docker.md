# Session 94a5b082 (Continued)

[PROGRESS]
- Phase: Implementation
- Step: Create Docker Compose
- Completed: 4/4 steps
- Next: Done
[/PROGRESS]

[DESIGN_DOC]
Context:
- Problem: User requested `docker-compose.yml` for simplified orchestration.
- Constraints: Persistent DB and models cache.

Architecture:
- Services: `app` (Main) and `ocr-service`.
- Networks: Bridge network `docuflow-network`.
- Volumes: 
    - `docuflow_data` -> `/app/data` (Application DB)
    - `ocr_models` -> `/home/user/.cache` (Docling Models)

Key Decisions:
- [D6] Modified `backend/database.py` to check `DATABASE_URL` env var, allowing volume mapping without code hacks.
- [D7] Mapped OCR service cache to volume to prevent re-downloading models on restart.

Interfaces:
- N/A

Assumptions & TODOs:
- Assumptions: Port 8000 and 7860 are free.
[/DESIGN_DOC]

[EVAL]
- What was achieved: Created robust docker-compose setup.
- Known limitations: None.
[/EVAL]
