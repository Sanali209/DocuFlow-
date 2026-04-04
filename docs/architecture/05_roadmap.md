# DocuFlow — Development Roadmap

> **Версия:** 2.0 (с ссылками на тикеты)
> **Методология:** TDD — тесты пишутся ДО реализации.
> **Тикеты:** [docs/tickets/INDEX.md](../tickets/INDEX.md)
> **Гейты:** Каждая фаза = рабочая система + deployable на реальные машины.
> **Принцип:** Откат невозможен — только вперёд.

---

## Текущее состояние (Baseline)

| Компонент | Статус |
|---|---|
| P2P FileBus + Координация | ✅ Готово |
| Heartbeat + Master Election | ✅ Готово |
| Snapshot / Sync кластера | ✅ Готово |
| RBAC авторизация (User/Role/Workplace) | ✅ Готово |
| Admin Panel (мониторинг кластера, пользователи) | ✅ Готово |
| NiceGUI Portal + Vertical Slice навигация | ✅ Готово |
| Производственный домен (WorkItem, TaskItem, ...) | ❌ [DF-001](./phase1/DF-001_domain_entities.md) |
| FolderScanner | ❌ [DF-006](./phase1/DF-006_folder_scanner_system.md) |
| Операторская панель / Бригадир | ❌ [DF-013](./phase2/DF-013_task_board_system.md) |
| Чат, Инциденты, Отчёты | ❌ [DF-022](./phase4/DF-022_chat_system.md), [DF-028](./phase5/DF-028_report_system.md) |

---

## Фаза 1 — Домен + FolderScanner

> **Цель:** Система видит нарядые, читает GNC файлы, строит PartLibrary.
> **Пользователи:** Бригадир + Начальник (read-only обзор)
> **TDD:** `pytest tests/unit/phase1/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-001](./phase1/DF-001_domain_entities.md) | Доменные сущности | Все SQLModel сущности production.py (блок A-H) |
| [DF-002](./phase1/DF-002_gnc_parser.md) | GncParser | Адаптация из MVP: PART NAME, extract_sku, estimate_time |
| [DF-003](./phase1/DF-003_folder_name_parser.md) | FolderNameParser | SIDRA regex + graceful fallback |
| [DF-004](./phase1/DF-004_task_file_parser.md) | TaskFileParser | is_variant dedup, step/batch_index |
| [DF-005](./phase1/DF-005_svg_generator.md) | SVGGenerator | bbox_x/y из G-кода → PartLibrary |
| [DF-006](./phase1/DF-006_folder_scanner_system.md) | FolderScannerSystem | Polling loop, PENDING_CUTS, hash detection |
| [DF-007](./phase1/DF-007_ns_mirror_service.md) | NSMirrorService | MD5 мониторинг, copy с timeout, on_bucket_add/remove |
| [DF-008+009](./phase1/DF-008_009_notifications_and_view.md) | Notifications + View | Configurable templates, scanner status UI |

### 🔑 Gate 1 (после DF-009)
```
✓ Сканер обнаруживает нарядые → WorkItem(NEW) / WorkItem(PENDING_CUTS)
✓ GncParser: реальный data_sample/ файл → правильные значения
✓ NSMirror: GNC копируется в NS при добавлении в bucket
✓ Notification templates настраиваются через Admin
✓ pytest tests/unit/phase1/ — все проходят
```

---

## Фаза 2 — Оперативная работа

> **Цель:** Бригадир планирует, оператор берёт задачи, ведёт трекинг.
> **Пользователи:** Оператор + Бригадир (основной рабочий инструмент)
> **TDD:** `pytest tests/unit/phase2/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-010](./phase2/DF-010_work_item_system.md) | WorkItemSystem | CRUD, lifecycle, register_document, open_in_explorer |
| [DF-011](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | work_items/view.py | Список + карточка + WorkLog лента + SVG превью |
| [DF-012](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | BatchEngine | Группировка по материалу, STOCK_ALERT проверка |
| [DF-013](./phase2/DF-013_task_board_system.md) | TaskBoardSystem | WorkerBucket lock, статусы, drift%, handover |
| [DF-014](./phase2/DF-014_015_016_views_presets_widgets.md) | task_board/view.py | Вид оператора + бригадира, drag&drop батчи |
| [DF-015](./phase2/DF-014_015_016_views_presets_widgets.md) | ViewPreset система | Notion-like вкладки: личные + глобальные пресеты |
| [DF-016](./phase2/DF-014_015_016_views_presets_widgets.md) | Core UI виджеты | status_badge, explorer_button, ns_mirror_status и др. |

### 🔑 Gate 2 (после DF-016)
```
✓ Оператор: взять батч → начать → sheets_done++ → завершить
✓ Бригадир: все узлы + батчи + drift%
✓ Авто-батчинг предлагает группировку
✓ Handover: смена передаётся с заметкой
✓ STOCK_ALERT отображается
✓ ViewPreset вкладки переключаются
✓ pytest tests/unit/phase2/ — все проходят
```

---

## Фаза 3 — Склад + Справочники

> **Цель:** Полный учёт материалов, расходников. PartLibrary с поиском.
> **Пользователи:** Кладовщик + Бригадир + Начальник
> **TDD:** `pytest tests/unit/phase3/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-017](./phase3/DF-017_018_material_system.md) | MaterialSystem | Приход/резерв/списание/аудит, дозаказ, инвентаризация |
| [DF-018](./phase3/DF-017_018_material_system.md) | material_stock/view.py | Time params редактирование, приход, аудит-лента |
| [DF-019](./phase3/DF-019_020_part_library.md) | PartLibrarySystem | upsert, find_by_bbox ±tolerance, обратный поиск |
| [DF-020](./phase3/DF-019_020_part_library.md) | part_library/view.py | SVG превью, bbox range slider, PartTemplate |
| [DF-021](./phase3/DF-021_consumable_system.md) | ConsumableSystem + view | Расходники, критический остаток → ChatMessage(WARNING) |

### 🔑 Gate 3 (после DF-021)
```
✓ MaterialSystem: приход/резерв/списание/аудит работают
✓ Бригадир корректирует time params → drift улучшается
✓ PartLibrary пополняется из сканера автоматически
✓ find_by_bbox() с tolerance_pct находит похожие детали
✓ Обратный поиск SKU → WorkItem-ы + ProductionUnit-ы
✓ ConsumableSystem: критический остаток → ChatMessage(WARNING)
✓ pytest tests/unit/phase3/ — все проходят
```

---

## Фаза 4 — Коммуникация + Логистика

> **Цель:** Чат, инциденты, паллеты, складирование. Полный операционный цикл.
> **Пользователи:** Все роли
> **TDD:** `pytest tests/unit/phase4/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-022](./phase4/DF-022_chat_system.md) | ChatSystem | Дерево тредов, типы, вложения, send_order/incident/handover |
| [DF-023](./phase4/DF-023_024_chat_view_and_incidents.md) | chat/view.py | ChatPanel + InboxView, compose с вложениями |
| [DF-024](./phase4/DF-023_024_chat_view_and_incidents.md) | IncidentSystem + view | report_incident → чат + resolve → downtime stats |
| [DF-025](./phase4/DF-025_production_system.md) | ProductionSystem | generate_human_id, create/split/merge, live search |
| [DF-026](./phase4/DF-026_027_production_view_and_admin.md) | production/view.py | Live search ≥2 символа, карточка паллеты, split UI |
| [DF-027](./phase4/DF-026_027_production_view_and_admin.md) | Admin Panel улучшения | NotificationTemplate CRUD, ViewPreset global, User/Role matrix |

### 🔑 Gate 4 (после DF-027)
```
✓ Чат: send/reply/thread/attach — полный цикл
✓ Инциденты: report → ChatMessage(INCIDENT) → resolve → downtime
✓ ProductionUnit: label_id "25-07-А-042" создаётся при завершении TaskItem
✓ Live search по partial label_id работает
✓ NotificationTemplate CRUD через Admin UI
✓ pytest tests/unit/phase4/ — все проходят
```

---

## Фаза 5 — Аналитика + Отчёты

> **Цель:** Управленческая видимость. Отчёты по шаблонам.
> **Пользователи:** Начальник + Бригадир
> **TDD:** `pytest tests/unit/phase5/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-028](./phase5/DF-028_report_system.md) | ReportSystem | ReportRegistry, BlockProxy, Jinja2 → weasyprint PDF |
| [DF-029](./phase5/DF-029_030_reports_and_analytics.md) | reports/view.py | Динамическая форма параметров, Скачать PDF, Конструктор |
| [DF-030](./phase5/DF-029_030_reports_and_analytics.md) | analytics/view.py | KPI карточки, drift% по узлам, незакрытые наряды |

### 🔑 Gate 5 — ФИНАЛЬНЫЙ (после DF-030)
```
✓ PDF отчёт по смене: 2 клика → файл скачан
✓ analytics/view.py: KPI с реальными данными
✓ drift% по узлам отображается правильно

END-TO-END TEST:
  1. FolderScanner обнаруживает папку с GNC
  2. Бригадир создаёт батч + регистрирует документ
  3. Оператор берёт батч → обновляет листы → завершает
  4. ProductionUnit("25-07-А-042") создаётся в БД
  5. Начальник генерирует отчёт → PDF
  6. Analytics показывает правильный drift%

✓ pytest tests/ — ВСЕ проходят
✓ Нет незакрытых критических багов
✓ Все 5 Gates пройдены → v1 релиз
```

---

## TDD Стратегия (для всех тикетов)

```
Порядок для каждого тикета:
  1. Создать tests/unit/{phase}/{module}_test.py
  2. Написать тест (RED: должен провалиться)
  3. Написать минимальную реализацию (GREEN)
  4. Рефакторинг (REFACTOR)
  5. Интеграционный тест если нужен

Правила:
  - Парсеры: тесты на реальных данных из data_sample/
  - Системы: in-memory SQLite (не production БД)
  - View: smoke-тесты (render без raise)
  - FileBus: mock FileBus (не реальный диск)

Запуск:
  pytest tests/unit/phase1/     # Gate 1
  pytest tests/unit/phase2/     # Gate 2
  pytest tests/                 # Всё (Gate 5)
```

---

## Backlog (за рамками v1)

| Элемент | Тикет |
|---|---|
| Трубы и прутки (MaterialType: TUBE/BAR) | — |
| ERP интеграция с Сидра | — |
| Мобильное приложение (read-only) | — |
| Email/Telegram уведомления | — |
| Fuzzy SKU поиск | — |

---

## График (ориентировочный)

```
Gate 1 (DF-001..DF-009):  Апрель 2025
Gate 2 (DF-010..DF-016):  Май–Июнь 2025
Gate 3 (DF-017..DF-021):  Июль 2025
Gate 4 (DF-022..DF-027):  Август–Октябрь 2025
Gate 5 (DF-028..DF-030):  Январь 2026 → v1 релиз
```
