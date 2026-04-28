# DocuFlow — Architecture Documentation

> Все документы основаны на **Master Plan v7** и эволюции через версии v3–v7.
> Приоритет: **Текущий код > эти документы > Obsidian канвас.**
> **Актуальная спецификация:** [Task Board v2 Design](../superpowers/specs/2026-04-28-task-board-v2-design.md) — единый производственный центр (Project→WorkItem→TaskGroup→TaskItem).
> **Полный индекс:** смотри [docs/index.md](../index.md)

---

## Документы

| # | Документ | Описание |
|---|---|---|
| 01 | [Design Document](./01_design_document.md) | Назначение системы, контекст цеха, операционный цикл, матрица ролей, ключевые решения |
| 02 | [Application Architecture](./02_application_architecture.md) | Структура проекта, сущности БД, системные компоненты, конфигурация, UI архитектура |
| 03 | [Data Flow](./03_data_flow.md) | Потоки данных: GNC → БД, NS Mirror, FileBus sync, MaterialAudit, ReportSystem |
| 04 | [C4 & ArchiMate Diagrams](./04_c4_archimate.md) | C4 (Context/Container/Component), ArchiMate (мотивация, технологии, sequence) |
| 05 | [Development Roadmap](./05_roadmap.md) | Фазы 1-5, задачи, критерии готовности, backlog, ориентировочный график |

---

## Быстрая навигация

### Хочу понять *что* строим
→ [01 Design Document](./01_design_document.md)

### Хочу понять *как* устроен код
→ [02 Application Architecture](./02_application_architecture.md)

### Хочу понять *как двигаются данные*
→ [03 Data Flow](./03_data_flow.md)

### Хочу увидеть *диаграммы*
→ [04 C4 & ArchiMate](./04_c4_archimate.md)

### Хочу знать *что делать дальше*
→ [05 Roadmap](./05_roadmap.md)

---

## История версий плана

| Версия | Ключевые изменения |
|---|---|
| v3 | Ключевые решения зафиксированы. GNC парсинг, буквонезависимые пути, SKU extraction с примерами. Паттерны: compute_hash, atomic_write, идемпотентный upsert |
| v4 | Глобальный план системы. Матрица ролей, 8 этапов цикла, WorkerBucket, ChatMessage. version_suffix в TaskPart. Открытые вопросы Q1–Q4 |
| v5 | ChatMessage типы, PartTemplate, IncidentLog, Consumable, SVGGenerator подтверждён. human-readable label_id. merge() паллет |
| v6 | Псевдокод формат. PENDING_CUTS, NSMirrorService, NS Mirror, time params в MaterialType, ReportRegistry, ViewPreset, NotificationTemplate, Explorer на всех узлах |
| **v7** | **Финальный.** Восстановлено из v3/v4/v5: формат GNC с sample, SIDRA_REGEX код, SKU extraction (version_letter + version_suffix), compute_hash + atomic_write, идемпотентный upsert, DEFAULT_RULE батчинга, явный раздел поиска деталей (прямой+обратный+bbox), SVGGenerator вызов, файловые блокировки (filelock), merge() паллет, учёт расходников в цикле, открытые вопросы Q1–Q4 |
| **v7.1** | **Task Board v2.** Единый Task Board с 2 табами (Производство + Моя корзина). TaskGroup заменяет batch_group_id. ViewState + ViewPreset. Интеграция Part Library, Warehouse, Production, Chat, Incidents, Analytics, Reports. TaskItemStatus.SUSPENDED. Авто-расчёт qty_produced. Паллет-трекинг и резервирование материалов. |
