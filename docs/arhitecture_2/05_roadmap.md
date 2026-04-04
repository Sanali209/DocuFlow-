# DocuFlow — Development Roadmap

> **Версия:** 3.0 (на основе Master Plan v7)
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

> **Цель:** Система видит наряды, читает GNC файлы, строит PartLibrary.
> **Пользователи:** Бригадир + Начальник (read-only обзор)
> **TDD:** `pytest tests/unit/phase1/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-001](./phase1/DF-001_domain_entities.md) | Доменные сущности | Все SQLModel сущности production.py (22 сущности). version_suffix в TaskPart. time params в MaterialType |
| [DF-002](./phase1/DF-002_gnc_parser.md) | GncParser | Адаптация из MVP: PART NAME → extract_sku (version_letter + version_suffix), estimate_time(mat_type) |
| [DF-003](./phase1/DF-003_folder_name_parser.md) | FolderNameParser | SIDRA_REGEX + graceful fallback → Default project |
| [DF-004](./phase1/DF-004_task_file_parser.md) | TaskFileParser | is_variant dedup, step_index/batch_index из имени |
| [DF-005](./phase1/DF-005_svg_generator.md) | SVGGenerator | generate_thumbnail() → (data_w, data_h) = реальный bbox из G-кода. НЕ из PART SIZE! |
| [DF-006](./phase1/DF-006_folder_scanner_system.md) | FolderScannerSystem | Polling loop + filelock, PENDING_CUTS, hash detection, идемпотентный upsert по file_path |
| [DF-007](./phase1/DF-007_ns_mirror_service.md) | NSMirrorService | MD5 мониторинг, copy с timeout=30s, диалог (Обновить/Оставить/Напомнить), on_bucket_remove |
| [DF-008+009](./phase1/DF-008_009_notifications_and_view.md) | Notifications + View | NotificationTemplate CRUD (key/text/enabled), scanner status UI, scan_log_panel |

### 🔑 Gate 1 (после DF-009)
```
✓ Сканер обнаруживает наряды → WorkItem(NEW) / WorkItem(PENDING_CUTS)
✓ При появлении GNC в PENDING_CUTS → авто-переход в NEW
✓ GncParser: реальный data_sample/ файл → правильные значения
  - extract_sku("3433-11-004-G-1") → ("3433-11-004-G", "G", "1")
  - PART SIZE не используется для bbox (только SVGGenerator!)
  - estimate_time(mat_type) возвращает разумное число минут
✓ FolderNameParser: SIDRA_REGEX корректно парсит + fallback работает
✓ is_variant() корректно фильтрует дубли
✓ Идемпотентность: повторный poll не создаёт дублей TaskItem
✓ filelock: параллельный сканер не ломает данные
✓ NSMirror: GNC копируется в NS при добавлении в bucket
✓ NSMirror: диалог (Обновить/Оставить/Напомнить) работает
✓ NSMirror: файл удаляется из NS при выходе из bucket
✓ NSMirror: copy_timeout=30s не вешает процесс
✓ NotificationTemplate настраиваются через Admin
✓ pytest tests/unit/phase1/ — все проходят
```

---

## Фаза 2 — Оперативная работа

> **Цель:** Бригадир планирует, оператор берёт задачи, ведёт трекинг.
> **Пользователи:** Оператор + Бригадир (основной рабочий инструмент)
> **TDD:** `pytest tests/unit/phase2/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-010](./phase2/DF-010_work_item_system.md) | WorkItemSystem | CRUD, lifecycle, register_document, open_in_explorer (+ fallback UNC hint) |
| [DF-011](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | work_items/view.py | Список + карточка + WorkLog лента + PartTemplate alerts + SVG превью |
| [DF-012](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | BatchEngine | DEFAULT_RULE, группировка по MAT+THK+SIZE, STOCK_ALERT, ручная блокировка TaskItem |
| [DF-013](./phase2/DF-013_task_board_system.md) | TaskBoardSystem | WorkerBucket lock, статусы (on_hold требует причину), drift%, handover |
| [DF-014](./phase2/DF-014_015_016_views_presets_widgets.md) | task_board/view.py | Вид оператора + бригадира, drag&drop батчи, прогресс-бар sheets_done |
| [DF-015](./phase2/DF-014_015_016_views_presets_widgets.md) | ViewPreset система | Notion-like вкладки: личные (owner=username) + глобальные (owner=global) |
| [DF-016](./phase2/DF-014_015_016_views_presets_widgets.md) | Core UI виджеты | status_badge, explorer_button (+ fallback), ns_mirror_status, file_changed_alert (Обновить/Оставить/Напомнить) |

### 🔑 Gate 2 (после DF-016)
```
✓ Оператор: взять батч → начать → sheets_done++ → завершить
✓ on_hold: причина обязательна
✓ Бригадир: все узлы + батчи + drift%
✓ Авто-батчинг DEFAULT_RULE предлагает группировку
✓ РУЧНАЯ БЛОКИРОВКА: TaskItem(BLOCKED) + block_reason работает
✓ Handover: смена передаётся с заметкой (handover_note, handover_from)
✓ STOCK_ALERT отображается + TaskItem автоблокируется
✓ open_in_explorer: subprocess explorer.exe + UNC fallback
✓ PartTemplate предупреждения показываются оператору
✓ ViewPreset вкладки переключаются (личные + глобальные)
✓ pytest tests/unit/phase2/ — все проходят
```

---

## Фаза 3 — Склад + Справочники

> **Цель:** Полный учёт материалов, расходников. PartLibrary с поиском.
> **Пользователи:** Кладовщик + Бригадир + Начальник
> **TDD:** `pytest tests/unit/phase3/`

| Тикет | Название | Описание |
|---|---|---|
| [DF-017](./phase3/DF-017_018_material_system.md) | MaterialSystem | Приход/резерв/списание/аудит (qty + qty_kg), дозаказ, инвентаризация |
| [DF-018](./phase3/DF-017_018_material_system.md) | material_stock/view.py | Time params редактирование (cut_speed, pierce_time, idle_speed, tolerance%), аудит-лента |
| [DF-019](./phase3/DF-019_020_part_library.md) | PartLibrarySystem | upsert, find_by_bbox ±tolerance, hole_count, corner_count, прямой + обратный поиск |
| [DF-020](./phase3/DF-019_020_part_library.md) | part_library/view.py | SVG превью, bbox range slider ±%, PartTemplate CRUD, обратный поиск → паллеты |
| [DF-021](./phase3/DF-021_consumable_system.md) | ConsumableSystem + view | Расходники, критический остаток → ChatMessage(WARNING), ConsumableLog |

### 🔑 Gate 3 (после DF-021)
```
✓ MaterialSystem: приход/резерв/списание/аудит работают (qty + qty_kg)
✓ Бригадир корректирует time params → drift улучшается
✓ PartLibrary пополняется из сканера автоматически
✓ find_by_bbox(tolerance_pct=5) находит похожие детали
✓ hole_count и corner_count фильтрация работает
✓ Прямой поиск: деталь X в наряде Y → правильный результат
✓ Обратный поиск: деталь X → WorkItem[] + ProductionUnit[] + StorageLocation
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
| [DF-022](./phase4/DF-022_chat_system.md) | ChatSystem | Дерево тредов (parent_message_id), типы, вложения (attachments JSON paths), send_order/incident/handover |
| [DF-023](./phase4/DF-023_024_chat_view_and_incidents.md) | chat/view.py | ChatPanel + InboxView, compose с вложениями |
| [DF-024](./phase4/DF-023_024_chat_view_and_incidents.md) | IncidentSystem + view | report_incident → IncidentLog + ChatMessage(INCIDENT), resolve → downtime stats, attachments |
| [DF-025](./phase4/DF-025_production_system.md) | ProductionSystem | generate_human_id ("25-07-А-042"), create/split/merge, is_pre_system, live search ≥2 символа |
| [DF-026](./phase4/DF-026_027_production_view_and_admin.md) | production/view.py | Live search, карточка паллеты, split UI, merge UI, до-системные паллеты |
| [DF-027](./phase4/DF-026_027_production_view_and_admin.md) | Admin Panel улучшения | NotificationTemplate CRUD (key/text/enabled), ViewPreset global manager, User/Role matrix |

### 🔑 Gate 4 (после DF-027)
```
✓ Чат: send/reply/thread/attach (JSON paths) — полный цикл
✓ ChatMessage.message_type: ORDER/INCIDENT/HANDOVER/URGENT работают
✓ Инциденты: report → ChatMessage(INCIDENT) → resolve → downtime stats
✓ IncidentLog.attachments сохраняются (relative paths JSON)
✓ ProductionUnit: label_id "25-07-А-042" создаётся при завершении TaskItem
✓ generate_human_id: формат {year}-{month}-{node_code}-{seq:03d}
✓ Live search ≥2 символа работает быстро
✓ Split: два новых unit + старый archived + parent_label_id
✓ Merge: новый unit + оба исходных archived
✓ is_pre_system=True паллеты создаются без TaskItem
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
| [DF-028](./phase5/DF-028_report_system.md) | ReportSystem | ReportRegistry, BlockProxy, Jinja2 рендер, weasyprint PDF |
| [DF-029](./phase5/DF-029_030_reports_and_analytics.md) | reports/view.py | Динамическая форма параметров, Скачать PDF, встроенные шаблоны |
| [DF-030](./phase5/DF-029_030_reports_and_analytics.md) | analytics/view.py | KPI карточки, drift% по узлам, незакрытые наряды, SimpleQL запросы |

### 🔑 Gate 5 — ФИНАЛЬНЫЙ (после DF-030)
```
✓ PDF отчёт по смене: 2 клика → файл скачан
✓ Встроенные шаблоны работают:
  - Отчёт по смене (shift_completion + incident_log)
  - Ход наряда (work_item_detail + tasks_by_node)
  - Движение материала (material_usage + stock_snapshot)
  - Инциденты (incident_log + downtime_summary)
  - План vs Факт (estimated vs actual, drift%)
✓ analytics/view.py: KPI с реальными данными
✓ drift% по узлам отображается правильно
✓ Открытые вопросы Q1–Q4 закрыты или задокументированы

END-TO-END TEST:
  1. FolderScanner обнаруживает папку с GNC
     - Если нет GNC → PENDING_CUTS + алерт
     - Появились GNC → авто-переход в NEW
  2. extract_sku("3433-11-004-G-1") → PartLibrary.sku="3433-11-004-G"
  3. bbox из SVGGenerator, НЕ из PART SIZE
  4. Бригадир создаёт батч (DEFAULT_RULE) + регистрирует документ
  5. STOCK_ALERT проверка пройдена
  6. Оператор берёт батч → filelock → NSMirrorService → sheets_done++
  7. on_hold с причиной → on_hold durations записаны
  8. TaskItem(DONE) → ProductionUnit("25-07-А-042") + StorageLocation
  9. MaterialAudit(write_off) + ConsumableLog(use) созданы
  10. actual_minutes - Σ(pauses) → drift% вычислен
  11. Обратный поиск детали → найдены WorkItem[] + паллеты
  12. Начальник генерирует отчёт → PDF скачан
  13. Analytics показывает правильный drift% по узлам

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
    extract_sku("3433-11-004-G-1") == ("3433-11-004-G", "G", "1")
    parse_folder_name("SIDRA-353203-SHLAV-2-07.07.2025") == SIDRA meta
    parse_folder_name("NONSTANDARD-FOLDER") == MIHTAV fallback
  - Сканер идемпотентность: scan() дважды = те же записи в БД
  - filelock: конкурентный scan() = только один выполняется
  - Системы: in-memory SQLite (не production БД)
  - View: smoke-тесты (render без raise)
  - FileBus: mock FileBus (не реальный диск)
  - NSMirror: mock copy() + assert timeout=30s

Запуск:
  pytest tests/unit/phase1/     # Gate 1
  pytest tests/unit/phase2/     # Gate 2
  pytest tests/                 # Всё (Gate 5)
```

---

## Backlog (за рамками v1)

| Элемент | Примечание |
|---|---|
| Трубы и прутки (MaterialType: TUBE/BAR) | Backlog |
| ERP интеграция с Сидра | Не планируется в v1 |
| Мобильное приложение (read-only) | Backlog |
| Email/Telegram уведомления | Backlog |
| Fuzzy SKU поиск | Backlog |
| Закрыть Q1: version_suffix в SKU | Нужно уточнить у технолога |
| Закрыть Q2: ChatMessage в БД vs broadcast | Рекомендовано: БД + broadcast |
| Закрыть Q3: WorkerBucket one vs many | Рекомендовано: батч целиком |
| Закрыть Q4: Attachments unified mechanism | Нужна реализация |

---

## График (ориентировочный)

```
Gate 1 (DF-001..DF-009):  Апрель 2025
Gate 2 (DF-010..DF-016):  Май–Июнь 2025
Gate 3 (DF-017..DF-021):  Июль 2025
Gate 4 (DF-022..DF-027):  Август–Октябрь 2025
Gate 5 (DF-028..DF-030):  Январь 2026 → v1 релиз
```
