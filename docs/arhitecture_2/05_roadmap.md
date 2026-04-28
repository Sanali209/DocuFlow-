# DocuFlow — Development Roadmap

> **Версия:** 3.2 (Task Board v2 — на основе Master Plan v7)
> **Спецификация:** [Task Board v2 Design](../superpowers/specs/2026-04-28-task-board-v2-design.md)
> **Статус:** Фазы 1-3 завершены. Task Board v2 — текущий приоритет.
> **Методология:** TDD — тесты пишутся ДО реализации.
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
| Производственный домен (WorkItem, TaskItem, ...) | ✅ Готово |
| FolderScanner & честный GNC Parser | ✅ Готово |
| Операторская панель / Бригадир / Батчинг | ✅ Готово |
| Сквозной поиск (Omnibar) & Контекстная навигация | ✅ Готово |
| Чат & Инциденты | ⏳ В процессе |
| Task Board v2 (единый производственный центр) | 🔥 ТЕКУЩИЙ ПРИОРИТЕТ |
| Отчёты & Аналитика | ❌ Backlog |

---

## 📊 Общий статус выполнения (Gates)

```
Gate 1 (Домен + Сканер):    ✅ ВЫПОЛНЕНО (Апрель 2025)
Gate 2 (Задачи + Батчинг):  ✅ ВЫПОЛНЕНО (Июнь 2025)
Gate 3 (Склад + Поиск):     ✅ ВЫПОЛНЕНО (Июль 2025)
Gate 4 (Чат + Логистика):   ⏳ В ПРОЦЕССЕ (Январь 2026)
Gate 4.5 (Task Board v2):   🔥 ТЕКУЩИЙ (Апрель 2026)
Gate 5 (Отчёты + v1):       ❌ ПЛАН (Июнь 2026)
```

---

## Фаза 1 — Домен + FolderScanner

> **Цель:** Система видит наряды, читает GNC файлы, строит PartLibrary.
> **Статус:** ✅ ВЫПОЛНЕНО

| Тикет | Название | Описание |
|---|---|---|
| [DF-001](./phase1/DF-001_domain_entities.md) | Доменные сущности | Все SQLModel сущности production.py (22 сущности). |
| [DF-005](./phase1/DF-005_svg_generator.md) | SVGGenerator | Реальный bbox из G-кода. НЕ из PART SIZE! |
| [DF-006](./phase1/DF-006_folder_scanner_system.md) | FolderScannerSystem | Polling, MD5 hash detection, upsert. |

### 🔑 Gate 1 — Пройдено
```
✓ Сканер обнаруживает наряды → WorkItem(NEW)
✓ GncParser вычисляет время и габариты по G-коду
✓ Идемпотентность сканирования проверена
```

---

## Фаза 2 — Оперативная работа

> **Цель:** Бригадир планирует, оператор берёт задачи, ведёт трекинг.
> **Статус:** ✅ ВЫПОЛНЕНО

| Тикет | Название | Описание |
|---|---|---|
| [DF-012](./phase2/DF-011_012_work_items_view_and_batch_engine.md) | BatchEngine | Группировка MAT+THK, STOCK_ALERT, ручной батчинг. |
| [DF-013](./phase2/DF-013_task_board_system.md) | TaskBoardSystem | WorkerBucket, статусы, drift%, handover. |
| [DF-016](./phase2/DF-014_015_016_views_presets_widgets.md) | UX улучшения | Реактивность (@refreshable), Deep Linking, Handover Alerts. |

### 🔑 Gate 2 — Пройдено
```
✓ Оператор: начать → завершить → автоматическое списание материала
✓ Бригадир: планирование через ручной и авто-батчинг
✓ Контекстные переходы Наряд -> Задачи работают
```

---

## Фаза 3 — Склад + Справочники

> **Цель:** Полный учёт материалов, расходников. PartLibrary со сквозным поиском.
> **Статус:** ✅ ВЫПОЛНЕНО

| Тикет | Название | Описание |
|---|---|---|
| [DF-017](./phase3/DF-017_018_material_system.md) | MaterialSystem | Приход/списание/аудит, Очередь подачи (Supply Queue). |
| [DF-019](./phase3/DF-019_020_part_library.md) | Omnibar | Сквозной поиск по всей системе (Наряды, Детали, Паллеты). |

### 🔑 Gate 3 — Пройдено
```
✓ Сквозной поиск находит детали и переключает экраны
✓ Запрос металла от оператора мгновенно виден на складе
✓ pytest tests/integration/test_ux_features.py — пройдено
```

---

## Фаза 4 — Коммуникация + Логистика

> **Цель:** Чат, инциденты, паллеты, складирование.
> **Статус:** ⏳ В ПРОЦЕССЕ

---

## Фаза 4.5 — Task Board v2 (Единый производственный центр)

> **Цель:** Единый Task Board с 2 табами, замена BatchEngine на TaskGroupService, интеграция всех модулей.
> **Спецификация:** [Task Board v2 Design](../superpowers/specs/2026-04-28-task-board-v2-design.md)
> **Статус:** 🔥 ТЕКУЩИЙ ПРИОРИТЕТ

| Тикет | Название | Описание |
|---|---|---|
| TB2-001 | TaskGroup entity + миграция | Замена batch_group_id (UUID) на task_group_id (FK). TaskGroupService. |
| TB2-002 | Единый Task Board view | 2 таба: "Производство" (иерархия) + "Моя корзина" (оператор). |
| TB2-003 | ViewState + ViewPreset | Сохранение раскрытия уровней + комплексные фильтры с пресетами. |
| TB2-004 | Omnisearch v2 | Поиск по всем уровням + ProductionUnit.label_id + Part.sku. |
| TB2-005 | Паллет-трекинг + авто-qty | Связь TaskItem ↔ ProductionUnit. Авто-расчёт qty_produced. |
| TB2-006 | Резервирование материалов | Создание reservation при назначении на узел. Авто-списание при DONE. |
| TB2-007 | Интеграция Part Library | Клик на деталь в TaskItem → модальное окно. Корзина заказа + rework nests. |
| TB2-008 | Интеграция Warehouse | Резервирование из Task Board. Новая вкладка "РЕЗЕРВЫ". |
| TB2-009 | Интеграция Chat/Incidents | HANDOVER тип, deeplink #<task_id>, канал "Производство", фильтр по Project/WI. |
| TB2-010 | Интеграция Analytics/Reports | Метрики TaskGroup, node_utilization, pallet_by_project. Новые data blocks. |
| TB2-011 | Модальные окна + превью | Project, WorkItem, TaskGroup, TaskItem, Pallet модалки. Превью неста SVG. |

### 🔑 Gate 4.5 — Критерии
```
✓ TaskGroup — полноценная DB-сущность, batch_group_id удалён
✓ 2 таба: "Производство" (иерархия) и "Моя корзина" (оператор)
✓ Раскрытие/сворачивание с сохранением в ViewState
✓ Комплексные фильтры с пресетами (ViewPreset)
✓ Omnisearch работает по всем уровням + паллетам + деталям
✓ Авто-расчёт qty_produced, диалог завершения с паллетой
✓ Резервирование материала + авто-списание при DONE
✓ Интеграция Part Library, Warehouse, Production, Chat, Incidents
```

---

## Фаза 5 — Аналитика + Отчёты

> **Цель:** Управленческая видимость. Отчёты по шаблонам.
> **Статус:** ❌ ПЛАН
