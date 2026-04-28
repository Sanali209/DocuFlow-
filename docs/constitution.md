
- **Symmetric Truth**: Every node treats its **local database** as the source of truth. The "Master" node acts as a central synchronizer, managing snapshots on the shared filesystem and coordinating broad state consistency.
- **TDD-First**: Every development phase begins with the creation of failure-inducing tests that define the success criteria for the component.
- **Atomic Progress**: Tasks are broken down into the smallest verifiable units to ensure continuous stability. and contain all info needed for it to be completed.
- **Polling Stability**: We will use a `PollingObserver` for the File Bus to ensure reliable change detection across network (Samba/CIFS) shares.
- **Code as documentation**: Every phase will be documented in the code itself, with examples and explanations. Code folow principe self explain code. no magic numbers, no magic strings, no magic values. shortest posible functions, shortest posible classes, shortest posible methods. descreptive names for variables, functions, classes, methods. coments in code only for complex logic. but good docstrings for all functions, classes, methods.
-  **follow domain design principles.** each system is folow domain logic
- **for each phase** use all types of tests *- unit, integration, e2e
- **if improwe plan be user review** not onli reflect diference in new plan plan need be solid end describe all from start to finish, if plan so long yore do it step by step, starting from raw and detalize after

## Code Quality & Tooling Constitution

### Linting Stack (mandatory)
All code must pass the following static analysis before merge:

1. **Ruff** — primary linter & formatter (replaces flake8, black, isort, pyupgrade, bandit).
   - Line length: 100
   - Target Python: 3.12
   - Enabled rules: E, F, W, I, B, S, UP, RUF, TID, ASYNC, C4, SIM, PERF
   - Ignored: S101, S106 (tests), RUF001-RUF003 (Cyrillic UI strings)

2. **Pyright** — strict type checking.
   - Zero errors policy on `src/`
   - `ignore_missing_imports` for nicegui/sqlmodel only

3. **import-linter** — architecture boundary enforcement.
   - Vertical slices (`features/*`) must not import each other directly
   - `domain/` may not import `features/`, `infrastructure/`, or `application/`
   - `lib/` may not import `features/`

4. **Vulture** — dead code detection.
   - Run before releases: `uv run vulture src/ --min-confidence 80`

### Pre-commit Hook (mandatory)
Every commit triggers:
- `ruff check --fix`
- `ruff format`
- `pyright`
- `lint-imports`

Install once: `uv run pre-commit install`

### Security
- **Semgrep** custom rules for FileBus atomic writes (`TEMP_*` → rename) and HMAC signing (`sort_keys=True`)
- **Bandit** rules already covered by Ruff `S` category
- No `eval`, no `exec`, no dynamic `__import__` outside of plugin loader

### Performance & Complexity
- Cyclomatic complexity check via Ruff `C901` (threshold 15)
- McCabe complexity: fail CI if any function > B grade
- No duplicate code blocks > 10 lines (enforced by `jscpd` in CI)

### Testing Quality
- **Mutation testing** (`mutmut`) on critical paths: `task_board/`, `folder_scanner/`, `inventory/`
- Minimum test coverage: 70% for `features/`, 90% for `domain/`
- All tests must be deterministic (no random data without fixed seed)

### CI/CD Gate
A PR is blocked until:
- `ruff check src/` → 0 errors
- `pyright src/` → 0 errors
- `lint-imports` → 0 contract violations
- `pytest tests/` → all pass
- `vulture src/ --min-confidence 80` → 0 dead code (except intentional noqa)
- No new `E501` line-too-long errors
