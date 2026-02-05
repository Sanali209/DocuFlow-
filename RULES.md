# Agent Skill Usage Rules

## Project Context
- **Frontend**: Svelte 5, Vite, Tailwind CSS (via `ui-ux-pro-max`).
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, Pydantic.
- **Database**: SQLite (managed via `sql-pro` and `database-architect`).
- **Infrastructure**: Docker, Docker Compose.

## Skill Usage Guidelines

### 1. Architecture & Planning
*Always start complex tasks with planning.*
- **Complex Features/Refactors**: Use `senior-architect` or `software-architecture` to design the system.
- **Database Changes**: MUST check `database-architect` and `database-design` before modifying schemas.
- **Task Breakdown**: Use `planning-with-files` to structure multi-step workflows. For quick plans use `concise-planning`.

### 2. Implementation
- **Frontend Work**:
  - Primary: `ui-ux-pro-max` (Component design, Svelte logic).
  - Standards: `frontend-dev-guidelines`.
  - General: `frontend-developer`.
- **Backend Work**:
  - Primary: `fastapi-pro`.
  - Core Python: `python-pro` and `python-patterns`.
  - Database Interactions: `sql-pro`.

### 3. Workflow & Quality
- **Git Operations**: Use `git-pushing` for standard commits. Use `git-advanced-workflows` for complex branching/rebasing.
- **Code Quality**: Consult `clean-code` and `debugging-strategies` when refactoring or fixing bugs.
- **Documentation**: Use `writing-skills` and `documentation-templates` for `README.md`, `CONTRIBUTING.md`, etc.

## Forbidden Patterns
- **DO NOT** use React, Vue, or Angular specific skills/patterns unless explicitly requested for migration.
- **DO NOT** use "marketing" or "seo" skills for this internal tool.
- **DO NOT** create new skills without user approval.
