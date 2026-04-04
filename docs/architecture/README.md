# DocuFlow — Architecture Documentation

> Все документы основаны на **Master Plan v6** и эволюции через версии v3–v6.
> Приоритет: **Текущий код > эти документы > Obsidian канвас.**

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
| v3 | Ключевые решения зафиксированы. GNC парсинг, буквонезависимые пути, SKU extraction |
| v4 | Глобальный план системы. Матрица ролей, 8 этапов цикла, WorkerBucket, ChatMessage |
| v5 | ChatMessage типы, PartTemplate, IncidentLog, Consumable, SVGGenerator подтверждён. human-readable label_id |
| v6 | Псевдокод формат. PENDING_CUTS, NSMirrorService, NS Mirror delays, time params в MaterialType, ReportRegistry, ViewPreset, NotificationTemplate, Explorer на всех узлах |
