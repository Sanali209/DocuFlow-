# AGENTS.md

## Fast orientation
- Product goal: decentralized workshop orchestration over a shared folder (no central DB), with per-node SQLite + file-based sync.
- Ground truth order: code first, then `docs/arhitecture_2/*`, then older docs (`docs/architecture/*`).
- App entrypoint is `src/docuflow/main.py`; startup orchestration is in `src/docuflow/sdk.py` and `src/docuflow/application/bus/orchestrator.py`.

## 📚 Documentation Index

> **Полный индекс документации:** [docs/index.md](./docs/index.md)

### Architecture (arhitecture_2/) — Актуальная документация
| Документ | Описание |
|---|---|
| [01_design_document.md](./docs/arhitecture_2/01_design_document.md) | Назначение системы, контекст цеха, 8-этапный операционный цикл, матрица ролей, ключевые решения |
| [02_application_architecture.md](./docs/arhitecture_2/02_application_architecture.md) | Структура проекта (vertical slices), сущности БД, системные компоненты, UI архитектура |
| [03_data_flow.md](./docs/arhitecture_2/03_data_flow.md) | Потоки данных: GNC → БД, NS Mirror, FileBus sync, MaterialAudit |
| [04_c4_archimate.md](./docs/arhitecture_2/04_c4_archimate.md) | C4 диаграммы (Context/Container/Component), ArchiMate |
| [05_roadmap.md](./docs/arhitecture_2/05_roadmap.md) | Фазы 1-5 разработки, текущий статус, критерии готовности |

### Core Reference
| Документ | Описание |
|---|---|
| [glossary.md](./docs/glossary.md) | Глоссарий терминов: Vertical Slice, SDK, DI (Dishka), FileBus, NSMirror, HMACSigner, Snapshot и др. |
| [constitution.md](./docs/constitution.md) | Архитектурные принципы: Symmetric Truth, TDD-First, Atomic Progress, Polling Stability |
| [knowledge_gaps.md](./docs/knowledge_gaps.md) | Неочевидные реализации и подводные камни: PollingObserver, Multi-Node DBs, HMAC signing, async testing |

### Project Management
| Документ | Описание |
|---|---|
| [TODO.md](./docs/TODO.md) | Active issues, Ideas, Open Questions (Q1-Q4), Refactoring Plan |
| [repo_conventions.md](./docs/repo_conventions.md) | Две конвенции: smoke tests + TDD |

### Legacy / Obsolete
| Документ | Описание |
|---|---|
| [obsidian/docuFlow/доку десиджн/v4.md](./docs/obsidian/docuFlow/доку%20десиджн/v4.md) | Master Plan v4 (утратил актуальность) |
| [obsidian/docuFlow/доку десиджн/v5.md](./docs/obsidian/docuFlow/доку%20десиджн/v5.md) | Master Plan v5 (утратил актуальность) |
| [obsidian/docuFlow/доку десиджн/v 6.md](./docs/obsidian/docuFlow/доку%20десиджн/v%206.md) | Master Plan v6 (утратил актуальность) |
| [arhitecture_2/docuflow_v7.md](./docs/arhitecture_2/docuflow_v7.md) | Consolidated v7 (дублирует arhitecture_2/*) |

### Reviews & Reports
| Документ | Описание |
|---|---|
| [Review/repository_audit_report.md](./docs/Review/repository_audit_report.md) | Аудит репозитория: критические проблемы, безопасность, качество кода |
| [Review/ux_implementation_report.md](./docs/Review/ux_implementation_report.md) | Отчёт о реализации UX: F1, Omnibar, навигация |
| [Review/final_v3_1_report.md](./docs/Review/final_v3_1_report.md) | Итоговый отчёт v3.1: стабилизация, багфиксы |
| [Review/full_workday_simulation.md](./docs/Review/full_workday_simulation.md) | Симуляция полного рабочего дня: тестирование сценариев |
| [Review/gap_analysis_and_bughunt_v3_1.md](./docs/Review/gap_analysis_and_bughunt_v3_1.md) | Анализ разрывов и охота на баги v3.1 |
| [Review/phase1_completion_report.md](./docs/Review/phase1_completion_report.md) | Отчёт о завершении Фазы 1: домен + сканер |
| [Review/fix_plan_tdd_phases.md](./docs/Review/fix_plan_tdd_phases.md) | План исправлений через TDD фазы |
| [Review/kiro/2026-04-14_review.md](./docs/Review/kiro/2026-04-14_review.md) | Обзор от Kiro: состояние системы |

### Bug Tracking
| Документ | Описание |
|---|---|
| [Bug track/v3_1_bug_report.md](./docs/Bug%20track/v3_1_bug_report.md) | Баг-репорт v3.1: известные проблемы |
| [Bug track/bug_hunt_plan.md](./docs/Bug%20track/bug_hunt_plan.md) | План охоты на баги |
| [Bug track/quick_reports.md](./docs/Bug%20track/quick_reports.md) | Быстрые отчёты о проблемах |

### Promotional & Planning
| Документ | Описание |
|---|---|
| [promo_document_ru.md](./docs/promo_document_ru.md) | Промо-документ на русском языке |
| [cross_interaction_ux_plan.md](./docs/cross_interaction_ux_plan.md) | UX план кросс-взаимодействия |
| [ui_ux_tdd_plan.md](./docs/ui_ux_tdd_plan.md) | TDD план для UI/UX |

---

## Architecture map (work where responsibility already lives)
- Use vertical slices in `src/docuflow/features/*`: each feature keeps logic in `system.py` and UI in `view.py`.
- Wire new systems through Dishka in `src/docuflow/infrastructure/di.py` (scope is important: `Scope.APP` vs `Scope.REQUEST`).
- Keep domain entities in `src/docuflow/domain/entities/*`; cross-feature orchestration belongs in SDK/orchestrator layers, not views.
- `main.py` routes NiceGUI pages and resolves feature systems from DI per request scope.

## P2P and file-bus rules you must preserve
- FileBus protocol is filename-driven (`REQ_...json`, `RES_...json`) in `src/docuflow/infrastructure/bus.py`.
- Writes must stay atomic: write to `TEMP_*` then rename (`FileBusSystem._atomic_write`).
- Cluster work loops are background tasks in `P2POrchestrator`: coordination, polling, maintenance.
- Security path: messages are signed/verified via HMAC (`HMACSigner`, `SecureDispatcher`).

## Scanner/sync behavior (common regression zone)
- Folder scanning is leader-only (`FolderScannerSystem._discovery_loop` checks `sdk.orchestrator.is_leader`).
- Scanner idempotency is by DB upsert keys: `WorkItem.folder_name`, `TaskItem.file_path` (relative path from scan root).
- Empty production folders should transition to `PENDING_CUTS` and emit `scan.empty_folder` notification.
- NS mirror runs separately (`src/docuflow/features/folder_scanner/mirror.py`) and compares/copies network vs local NS files.

## Config and environment conventions
- Runtime config is `Config` in `src/docuflow/infrastructure/config.py` with env prefix `DOCUFLOW_`.
- Node DB file is derived from node id in DI (`{node_id}.db`), not fixed `local.db`.
- Shared bus/snapshots paths are derived from `shared_path`; avoid hardcoding absolute machine paths in code.

## Developer workflows that match this repo
- Install deps: `uv sync`
- Run app node: `uv run python -m docuflow.main`
- Run tests (project convention): `uv run pytest`
- Quality checks from `pyproject.toml`: `uv run ruff check .` and `uv run mypy src`
- Useful local diagnostics/scripts: `scripts/diagnose_scanner.py`, `scripts/check_settings.py`, `scripts/reset_cluster.py`, `scripts/seed_test_data.py`

## Project-specific coding expectations
- Keep constants named (tests enforce no magic values patterns; see `tests/test_code_quality.py`).
- Public/provider methods are expected to have docstrings (also enforced in quality tests).
- Prefer small, explicit methods and preserve existing status transitions/enums in domain models.
- For new feature work, add tests under `tests/unit` or relevant integration area before implementation.
