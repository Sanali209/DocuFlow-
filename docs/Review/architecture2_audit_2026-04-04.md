# Аудит соответствия `architecture_2` (2026-04-04)

## Область и критерии
- Источники: `AGENTS.md`, `docs/arhitecture_2/README.md`, `docs/arhitecture_2/02_application_architecture.md`, `docs/arhitecture_2/03_data_flow.md`, `docs/arhitecture_2/05_roadmap.md`.
- Проверенные модули: `src/docuflow/main.py`, `src/docuflow/sdk.py`, `src/docuflow/infrastructure/di.py`, `src/docuflow/infrastructure/bus.py`, `src/docuflow/application/bus/orchestrator.py`, `src/docuflow/features/folder_scanner/*`, `src/docuflow/features/projects/*`, `src/docuflow/features/core/layout.py`.
- Правило приоритета: согласно `docs/arhitecture_2/README.md` и `AGENTS.md` — **код = ground truth**, `architecture_2` = целевая спецификация и инварианты.

## Группы важности (findings)

### Critical
1. **Нерабочий путь broadcast в P2P** — **исправлено**
   - Архитектурное ожидание: поддержка широковещательных сообщений (`BROADCAST_*`) и командный обмен через FileBus.
   - Исходный дефект: `P2POrchestrator.broadcast_command()` вызывал `self._bus.write_message(...)`, но у `FileBusSystem` такого метода не было.
   - Что исправлено:
     - добавлен `FileBusSystem.write_message(...)`;
     - введён явный префикс `BROADCAST_*`;
     - broadcast-файлы пишутся в `BUS/INBOX`;
     - `poll_messages()` теперь принимает `BROADCAST_*` как релевантные входящие сообщения.
   - Доказательства: `src/docuflow/application/bus/orchestrator.py:186`, `src/docuflow/infrastructure/bus.py`, `src/docuflow/infrastructure/constants.py`.
   - Тесты:
     - `tests/test_file_bus.py::test_file_bus_write_message_for_broadcast`
     - `tests/application/test_orchestrator_lifecycle.py::test_orchestrator_broadcast_command_writes_signed_message`
   - Статус: `Resolved / covered by tests`.

### High
1. **Atomic write не соответствует архитектурному контракту**
   - Архитектурное ожидание: `tmp -> flush/fsync -> os.replace`.
   - Факт в коде: `write_text(...)` + `os.rename(...)`, без `fsync`, без `os.replace`.
   - Доказательства: `src/docuflow/infrastructure/bus.py:231-243`, `docs/arhitecture_2/03_data_flow.md:126-132`.
   - Риск: повреждение/потеря сообщений на сетевом хранилище при сбоях.

2. **Feature Projects не доступна в UI-портале**
   - Архитектурное ожидание: вертикальный срез должен быть доступен через навигацию/роутинг.
   - Факт в коде: в `switch_view` отсутствует ветка `projects`; в боковом меню нет `Projects`.
   - Доказательства: `src/docuflow/main.py:99-183`, `src/docuflow/features/core/layout.py:117-143`.
   - Риск: пользователь не может работать с проектами, несмотря на наличие `ProjectSystem` и `ProjectManagementView`.

3. **Несовпадение API между `projects/view.py` и `projects/system.py`**
   - Факт в коде: view вызывает несуществующие методы (`get_all_projects`, `create_project`, `reassign_work_item`), тогда как system предоставляет (`get_all_active_projects`, `register_new_project`, `reassign_production_group`).
   - Доказательства: `src/docuflow/features/projects/view.py:45,71,121`, `src/docuflow/features/projects/system.py:22,28,41`.
   - Риск: даже при подключении в `main.py` feature не заработает без исправления контракта.

### Medium
1. **Дублирование/рассинхрон SDK-инстансов в app lifecycle**
   - Факт в коде: создается глобальный `_sdk = SDK(_container)`, при этом DI тоже провайдит `SDK`; состояние кладется в `app.state.sdk` в разных точках.
   - Доказательства: `src/docuflow/main.py:35,55-57,79`, `src/docuflow/infrastructure/di.py:149-152`.
   - Риск: непредсказуемость состояния (инициализирован/не инициализирован orchestrator в разных путях).

2. **Структурное отклонение по incident slice**
   - Архитектурная карта в `02_application_architecture.md` предполагает отдельный модуль `features/incidents/`.
   - Факт в коде: incidents размещены внутри `features/chat/`.
   - Доказательства: `src/docuflow/main.py:160-164`, `src/docuflow/features/chat/incidents.py`, `src/docuflow/features/chat/incident_view.py`.
   - Риск: документация и код расходятся, сложнее сопровождать границы модулей.

### Low
1. **Default-значения scanner/mirror не совпадают с документом**
   - Факт в коде: `poll_interval_seconds=60`, `ns_mirror_interval_seconds=300`.
   - Ожидание документа: poll=300, ns_mirror=60.
   - Доказательства: `src/docuflow/features/folder_scanner/settings.py:25-40`, `docs/arhitecture_2/02_application_architecture.md:420-425`.
   - Риск: операционное поведение отличается от описанного, но может быть осознанной настройкой.

## Как view-слой реализует возможности (и где не реализует)

### Доступные через портал (`main.py` + sidebar)
- `dashboard` -> `dashboard_view(...)`.
- `work_items` -> `WorkItemsView.render()`.
- `task_board` -> `TaskBoardView.render()`.
- `scanner` -> `folder_scanner_view(...)`.
- `warehouse` -> `warehouse_view(...)`.
- `parts` -> `PartLibraryView.render()`.
- `consumables` -> `ConsumableView.render()`.
- `chat` -> `ChatView.render_portal()`.
- `incidents` -> `IncidentView.render_dashboard()`.
- `reports` -> `ReportsView.render_portal()`.
- `analytics` -> `analytics_view(...)`.
- `production` -> `production_view(...)`.
- `docs`, `admin` -> подключены.

Доказательства: `src/docuflow/main.py:103-183`, `src/docuflow/features/core/layout.py:117-143`.

### Есть в коде, но не выведено в UI
- `ProjectManagementView` и `ProjectSystem` существуют, но:
  1) нет пункта меню;
  2) нет route/switch для `projects`;
  3) API view != API system.

Доказательства: `src/docuflow/features/projects/view.py`, `src/docuflow/features/projects/system.py`, `src/docuflow/main.py:99-183`, `src/docuflow/features/core/layout.py:117-143`.

## Соответствие `repo_conventions.md`
- Требование "smoke test for all features" сейчас не выполняется полноценно для проектов в UI: feature недоступна из портала.
- TDD частично соблюден: есть unit-тесты на `ProjectSystem` (`tests/unit/features/test_project_system.py`), но нет smoke-покрытия рендера `ProjectManagementView` и интеграции в навигацию.

## Рекомендуемый порядок исправлений
1. Починить atomic write в FileBus (`tmp -> flush/fsync -> os.replace`).
2. Подключить feature projects в `main.py` + sidebar.
3. Синхронизировать API `projects/view.py` и `projects/system.py`.
4. Выбрать и зафиксировать позицию по incidents: отдельный slice или часть chat (обновить код/док).
5. Добавить smoke-тест рендера projects и e2e-проверку доступности из навигации.


