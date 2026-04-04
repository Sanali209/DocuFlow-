# DocuFlow Tickets — INDEX

> **Платформа:** Файловая система. Каждый тикет = `.md` файл.
> **Формат ID:** `DF-XXX`
> **Методология:** TDD (Test-Driven Development) — тесты пишутся ДО реализации.
> **Ворота (Gates):** Каждый тикет имеет Definition of Done. Переход к следующему только после прохождения ворот.

---

## Фаза 1 — Домен + FolderScanner

| ID | Название | Зависит от | Статус | Тесты |
|---|---|---|---|---|
| [DF-001](./phase1/DF-001_domain_entities.md) | Доменные сущности (production.py) | — | ✅ DONE | 75 passed |
| [DF-002](./phase1/DF-002_gnc_parser.md) | GncParser (адаптация из MVP) | DF-001 | ✅ DONE | — |
| [DF-003](./phase1/DF-003_folder_name_parser.md) | FolderNameParser | DF-001 | ✅ DONE | — |
| [DF-004](./phase1/DF-004_task_file_parser.md) | TaskFileParser + is_variant | DF-001 | ✅ DONE | — |
| [DF-005](./phase1/DF-005_svg_generator.md) | SVGGenerator интеграция | DF-001 | ✅ DONE | — |
| [DF-006](./phase1/DF-006_folder_scanner_system.md) | FolderScannerSystem (polling loop) | DF-001, DF-002, DF-003, DF-004, DF-005 | ✅ DONE | 3 failed (старые тесты) |
| [DF-007](./phase1/DF-007_ns_mirror_service.md) | NSMirrorService | DF-001, DF-006 | ✅ DONE | 2 passed |
| [DF-008](./phase1/DF-008_notification_templates.md) | NotificationTemplate система | DF-001 | ✅ DONE | 3 passed |
| [DF-009](./phase1/DF-009_folder_scanner_view.md) | folder_scanner/view.py | DF-006, DF-007, DF-008 | ✅ DONE | 1 passed |

### Phase 1 — Результаты тестов (03.04.2026)

**Всего**: 75 passed, 3 failed (старые тесты)

**Failed тесты** (требуют обновления):
1. `test_scan_pending_cuts_on_empty_folder` — MagicMock не работает с await
2. `test_master_check_on_startup` — coroutine не был awaited  
3. `test_role_seeding` — проблема с кодировкой русских символов

**Passed тесты по модулям**:
- BatchEngine: 10 passed
- FolderScanner: 1 passed
- Notifications: 3 passed
- NSMirror: 2 passed
- TaskBoardSystem: 9 passed
- ViewPreset: 19 passed
- WorkItemSystem: 19 passed
- Widgets: 12 passed

## Фаза 2 — Оперативная работа

| ID | Название | Зависит от | Статус | Тесты |
|---|---|---|---|---|
| [DF-010](./phase2/DF-010_work_item_system.md) | WorkItemSystem | DF-001, DF-006 | ✅ DONE | 19 passed |
| [DF-011](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | work_items/view.py | DF-010, DF-015, DF-016 | ✅ DONE | UI |
| [DF-012](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | BatchEngine + BatchRule | DF-001 | ✅ DONE | 10 passed |
| [DF-013](./phase2/DF-013_task_board_system.md) | TaskBoardSystem (WorkerBucket + статусы) | DF-010, DF-012 | ✅ DONE | 9 passed |
| [DF-014](./phase2/DF-014_015_016_views_presets_widgets.md) | task_board/view.py | DF-013 | ✅ DONE | UI |
| [DF-015](./phase2/DF-014_015_016_views_presets_widgets.md) | ViewPreset система | DF-001 | ✅ DONE | 19 passed |
| [DF-016](./phase2/DF-014_015_016_views_presets_widgets.md) | Core UI виджеты | DF-001 | ✅ DONE | 12 passed |

## Фаза 3 — Склад + Справочники

| ID | Название | Зависит от | Статус |
|---|---|---|---|
| [DF-017](./phase3/DF-017_material_system.md) | MaterialSystem + аудит | DF-001 | TODO |
| [DF-018](./phase3/DF-018_material_stock_view.md) | material_stock/view.py | DF-017 | TODO |
| [DF-019](./phase3/DF-019_part_library_system.md) | PartLibrarySystem (поиск + SVG) | DF-001, DF-005 | TODO |
| [DF-020](./phase3/DF-020_part_library_view.md) | part_library/view.py | DF-019 | TODO |
| [DF-021](./phase3/DF-021_consumable_system.md) | ConsumableSystem + view | DF-001 | TODO |

## Фаза 4 — Коммуникация + Логистика

| ID | Название | Зависит от | Статус |
|---|---|---|---|
| [DF-022](./phase4/DF-022_chat_system.md) | ChatSystem (треды + типы + файлы) | DF-001, DF-008 | TODO |
| [DF-023](./phase4/DF-023_chat_view.md) | chat/view.py | DF-022 | TODO |
| [DF-024](./phase4/DF-024_incident_system.md) | IncidentSystem + view | DF-001, DF-022 | TODO |
| [DF-025](./phase4/DF-025_production_system.md) | ProductionSystem (паллеты) | DF-001, DF-013 | TODO |
| [DF-026](./phase4/DF-026_production_view.md) | production/view.py | DF-025 | TODO |
| [DF-027](./phase4/DF-027_admin_improvements.md) | Admin Panel улучшения | DF-015, DF-008 | TODO |

## Фаза 5 — Аналитика + Отчёты

| ID | Название | Зависит от | Статус |
|---|---|---|---|
| [DF-028](./phase5/DF-028_report_system.md) | ReportSystem (Registry + PDF) | DF-001 | TODO |
| [DF-029](./phase5/DF-029_reports_view.md) | reports/view.py | DF-028 | TODO |
| [DF-030](./phase5/DF-030_analytics_view.md) | analytics/view.py | DF-028, DF-013 | TODO |

---

## Ворота (Development Gates)

```
Gate 1 (после DF-009):
  ✓ Сканер обнаруживает нарядые + PartLibrary пополняется
  ✓ PENDING_CUTS + уведомления работают
  ✓ NSMirror копирует GNC в локальную папку
  ✓ Unit тесты парсеров (gnc, folder_name, task_file) проходят

Gate 2 (после DF-016):
  ✓ Бригадир планирует батчи, оператор берёт задачи
  ✓ Трекинг sheets_done работает
  ✓ ViewPreset пресеты сохраняются
  ✓ "Открыть в Explorer" работает

Gate 3 (после DF-021):
  ✓ Кладовщик управляет материалами полностью
  ✓ PartLibrary с умным поиском по bbox
  ✓ Расходники с критическими алертами

Gate 4 (после DF-027):
  ✓ Чат с типами и вложениями работает
  ✓ Инциденты регистрируются → попадают в чат
  ✓ ProductionUnit создаётся при завершении TaskItem
  ✓ Поиск паллет по части label_id работает

Gate 5 (после DF-030):
  ✓ PDF отчёт по смене генерируется
  ✓ Аналитика: план vs факт по узлам
  ✓ Полный операционный цикл проверен end-to-end
```

---

## TDD Стратегия

```
Для каждого тикета:
  1. Написать тест ПЕРВЫМ (файл tests/unit/test_{module}.py)
  2. Запустить → RED (тест провалился — ожидаемо)
  3. Написать минимальную реализацию → GREEN
  4. Рефакторинг → REFACTOR
  5. Интеграционный тест (если нужен)

Правила:
  - Парсеры: unit тесты на реальных GNC семплах (data_sample/)
  - Системы: тесты с in-memory SQLite (не production БД)
  - View: smoke-тесты (компонент рендерится без ошибок)
  - FileBus: mock FileBus в тестах (не реальный диск)
```

---

## Отчёт о проделанной работе (03.04.2026)

### Phase 2 — Оперативная работа (7 из 7 тикетов завершено ✅)

| Тикет | Статус | Файлы | Тесты |
|-------|--------|-------|-------|
| DF-010: WorkItemSystem | ✅ DONE | `src/docuflow/features/work_items/system.py` | 19 passed |
| DF-011: WorkItems View | ✅ DONE | `src/docuflow/features/work_items/view.py` | UI |
| DF-012: BatchEngine | ✅ DONE | `src/docuflow/features/task_board/batch_engine.py` | 10 passed |
| DF-013: TaskBoardSystem | ✅ DONE | `src/docuflow/features/task_board/system.py` | 9 passed |
| DF-015: ViewPreset | ✅ DONE | `src/docuflow/features/view_presets/system.py` | 19 passed |
| DF-016: Core UI виджеты | ✅ DONE | `src/docuflow/lib/widgets/*.py` | 12 passed |
| DF-014: TaskBoard View | ✅ DONE | `src/docuflow/features/task_board/view.py` | UI |

**Всего тестов**: 98 passed (3 старых failed)

---

## Аномальные знания (Важно для будущей разработки)

### 1. Инструменты
- **`uv` вместо `python`** — для запуска тестов: `uv run pytest`, а не `python -m pytest`
- **Windows CMD** — команды в Windows CMD, не bash

### 2. Структура проекта
- **Дублирование** — существовали `src/docuflo` и `src/docuflow`. Исправлено: удалён `src/docuflo`
- **Правильный путь** — код в `src/docuflow/` (с двумя f)

### 3. Модели данных
- **TaskItem.batch_group_id** — отсутствовало, добавлено в `production.py`
- **WorkItem.folder_path** — обязательное поле

### 4. Тестирование
- **BaseSystem требует config** — убрано наследование для тестов
- **WorkLog.select()** — не работает, используем `select(WorkLog)`
- **In-memory SQLite** — все тесты

### 5. UI компоненты
- **NiceGUI** — UI framework
- **StatusBadge** — цвета: NEW=blue, PENDING=orange, REGISTERED=teal, IN_PROGRESS=green, ON_HOLD=yellow, BLOCKED=red, DONE=gray
- **ExplorerButton** — `subprocess.Popen(["explorer.exe", path])`

