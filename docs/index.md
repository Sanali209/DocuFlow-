# DocuFlow — Documentation Index

> **Приоритет источников:** Код > docs/arhitecture_2/* > docs/obsidian/*

---

## Актуальная документация

### Architecture (arhitecture_2/)
| # | Документ | Описание |
|---|---|---|
| 01 | [Design Document](arhitecture_2/01_design_document.md) | Назначение, контекст цеха, 8-этапный цикл, матрица ролей |
| 02 | [Application Architecture](arhitecture_2/02_application_architecture.md) | Структура проекта, сущности БД, компоненты |
| 03 | [Data Flow](arhitecture_2/03_data_flow.md) | Потоки данных: GNC → БД, NS Mirror, FileBus |
| 04 | [C4 & ArchiMate](arhitecture_2/04_c4_archimate.md) | Диаграммы C4, ArchiMate |
| 05 | [Roadmap](arhitecture_2/05_roadmap.md) | Фазы 1-5, статус, критерии |

### Core Reference
| Документ | Описание |
|---|---|
| [glossary.md](glossary.md) | Глоссарий: Vertical Slice, SDK, DI, FileBus, NSMirror |
| [constitution.md](constitution.md) | Архитектурные принципы: Symmetric Truth, TDD-First |
| [knowledge_gaps.md](knowledge_gaps.md) | Подводные камни: PollingObserver, HMAC signing |

### Project Management
| Документ | Описание |
|---|---|
| [TODO.md](TODO.md) | Active issues, Ideas, Open Questions (Q1-Q4) |
| [repo_conventions.md](repo_conventions.md) | Конвенции: smoke tests + TDD |

---

## Reviews & Reports
| Документ | Описание |
|---|---|
| [Review/repository_audit_report.md](Review/repository_audit_report.md) | Аудит репозитория |
| [Review/ux_implementation_report.md](Review/ux_implementation_report.md) | UX реализация |
| [Review/final_v3_1_report.md](Review/final_v3_1_report.md) | Итоги v3.1 |
| [Review/full_workday_simulation.md](Review/full_workday_simulation.md) | Симуляция рабочего дня |
| [Review/phase1_completion_report.md](Review/phase1_completion_report.md) | Завершение Фазы 1 |
| [Review/kiro/2026-04-14_review.md](Review/kiro/2026-04-14_review.md) | Обзор от Kiro |

## Bug Tracking
| Документ | Описание |
|---|---|
| [Bug track/v3_1_bug_report.md](Bug%20track/v3_1_bug_report.md) | Баг-репорт v3.1 |
| [Bug track/bug_hunt_plan.md](Bug%20track/bug_hunt_plan.md) | План охоты на баги |
| [Bug track/quick_reports.md](Bug%20track/quick_reports.md) | Быстрые отчёты |

## Planning & UX
| Документ | Описание |
|---|---|
| [cross_interaction_ux_plan.md](cross_interaction_ux_plan.md) | UX план кросс-взаимодействия |
| [ui_ux_tdd_plan.md](ui_ux_tdd_plan.md) | TDD план для UI/UX |
| [promo_document_ru.md](promo_document_ru.md) | Промо на русском |

---

## Быстрая навигация

### Хочу понять *что* строим
→ [01 Design Document](arhitecture_2/01_design_document.md)

### Хочу понять *как* устроен код
→ [02 Application Architecture](arhitecture_2/02_application_architecture.md)

### Хочу знать *что делать дальше*
→ [05 Roadmap](arhitecture_2/05_roadmap.md)

---

*Updated: 2026-04-14*