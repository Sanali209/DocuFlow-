# Глоссарий терминов — DocuFlow

Цель: зафиксировать общее понимание терминов, используемых в коде, документации и в ходе аудита.

- Vertical Slice (вертикальный срез)
  - Коротко: модуль, включающий логику домена (system.py) и UI (view.py) для одной функциональной области.
  - Где смотреть: `src/docuflow/features/<module>/`.

- SDK (Software Development Kit / фасад)
  - Коротко: фасад для получения систем/инфраструктуры из DI-контейнера и оркестрации lifecycle.
  - Где: `src/docuflow/sdk.py`.

- DI (Dependency Injection) / Dishka
  - Коротко: контейнер для провайдирования объектов; в проекте используется библиотека `dishka`.
  - Важны scope'ы: `Scope.APP` (singleton на весь процесс) и `Scope.REQUEST` (scope на web-request / ui action).
  - Где: `src/docuflow/infrastructure/di.py`.

- AppProvider
  - Коротко: класс-провайдер для Dishka, описывает, как создаются системы и их scope.
  - Где: `src/docuflow/infrastructure/di.py`.

- FileBus (файловая шина)
  - Коротко: протокол обмена командами/событиями между узлами через сетевую папку (Samba/CIFS).
  - Папки: `BUS/INBOX`, `BUS/OUTBOX`.
  - Файлы: `REQ_{from}_{to}_{id}.json`, `RES_{from}_{to}_{id}.json`, `BROADCAST_{from}_{id}.json`.
  - TEMP_ — префикс временных файлов во время записи.
  - Где: `src/docuflow/infrastructure/bus.py`, `src/docuflow/infrastructure/constants.py`.

- REQ / RES / BROADCAST
  - REQ: запрос от узла-отправителя к конкретному узлу-получателю.
  - RES: ответ на REQ.
  - BROADCAST: сообщение, адресованное всем узлам (широковещание).

- Atomic write / временные файлы
  - Коротко: безопасная запись файла в сетевой папке: записать в TEMP, flush/fsync, затем atomically переименовать в финальное имя (os.replace / os.rename в зависимости от платформы и файловой системы).
  - Почему важно: предотвращает частично записанные/повреждённые сообщения на Samba.
  - Где: `src/docuflow/infrastructure/bus.py` (реализация `_atomic_write`).

- P2POrchestrator
  - Коротко: координатор фоновых задач: polling шины, maintenance (snapshot/GC), координация (leader election).
  - Где: `src/docuflow/application/bus/orchestrator.py`.

- CoordinationSystem (координация / leader election)
  - Коротко: система heartbeats и выбора мастера (leader/master).
  - is_leader: флаг, управляющий тем, какие узлы выполняют master-only задачи (например, FolderScanner).
  - Где: `src/docuflow/infrastructure/coordination.py` (см. di provider).

- Snapshot / Sync
  - Snapshot: экспорт состояния БД мастера в JSON для синхронизации с другими узлами.
  - Sync: механики применения snapshot на slave-узлах.
  - Где: `src/docuflow/infrastructure/sync.py`, `Housekeeping`.

- FolderScanner / FolderScannerSystem
  - Коротко: модуль, который сканирует сетевые папки (SIDRA/MIHTAV/OTHER), создаёт/апдейтит WorkItem/TaskItem.
  - Leader-only: запускается только на мастере.
  - Где: `src/docuflow/features/folder_scanner/`.

- NSMirrorService
  - Коротко: копирует GNC-файлы в локальную NS-папку (для станков), проверяет md5 и уведомляет оператора.
  - Где: `src/docuflow/features/folder_scanner/mirror.py`.

- WorkItem / TaskItem / TaskPart
  - WorkItem: «папка/наряд» — верхнеуровневая единица работы.
  - TaskItem: один GNC-файл (задача) внутри WorkItem.
  - TaskPart: деталь внутри TaskItem (связанная с PartLibrary).
  - Где: `src/docuflow/domain/entities/production.py`.

- PartLibrary / PartTemplate
  - PartLibrary: справочник деталей (sku, bbox, svg_preview).
  - PartTemplate: шаблоны/правила предупреждений для деталей.
  - Где: `src/docuflow/features/parts/` и domain entities.

- Project
  - Коротко: группировка WorkItem'ов (проект клиента или внутренний проект).
  - Где: `src/docuflow/features/projects/*`.

- WorkerBucket / lock_batch
  - Коротко: резерв задач (batch) за узлом; lock_batch — операция резервирования батча через FileBus.

- GNC
  - Коротко: формат файла задания для резки (G-code-like), откуда парсятся sheet, part name, contours и т.д.
  - Где: `src/docuflow/features/folder_scanner/parsers/gnc.py`.

- SVGGenerator / PartPreviewGenerator
  - Коротко: генерация миниатюр SVG из GNC (bbox в мм), используется для PartLibrary.
  - Где: парсеры и генераторы в folder_scanner/parsers.

- Idempotency (идемпотентность)
  - Правило: повторный poll не должен создавать дубликатов — upsert по ключам `WorkItem.folder_name` и `TaskItem.file_path`.
  - Где: `src/docuflow/features/folder_scanner/system.py`.

- ViewPreset
  - Коротко: предустановки отображения (filters, sort, columns) — личные (owner=username) и глобальные (owner="global").
  - Где: `src/docuflow/features/view_presets/`.

- NotificationTemplate
  - Коротко: шаблоны уведомлений (ключ, текст, enabled) — например `scan.empty_folder`.
  - Где: `src/docuflow/features/notifications/system.py` и domain entities.

- HMACSigner / SecureDispatcher
  - HMACSigner: подписывает сообщения HMAC-SHA256; используется для верификации целостности сообщений.
  - SecureDispatcher: валидирует подпись и sequence перед вызовом зарегистрированных handler'ов.
  - Где: `src/docuflow/infrastructure/security.py`, `src/docuflow/application/bus/dispatcher.py`.

- Housekeeping
  - Коротко: задачи по GC и ротации snapshot'ов, удалению старых сообщений.
  - Где: `src/docuflow/infrastructure/housekeeping.py`.

- SQLModel / Engine / Session
  - SQLModel: ORM (на основе SQLAlchemy) для доменных сущностей.
  - Engine: SQLAlchemy engine для node-specific DB (`{node_id}.db`).
  - Session: unit of work для операций с БД.
  - Где: `src/docuflow/infrastructure/di.py` и domain entities.

- PollingObserver
  - Коротко: watchdog PollingObserver, более стабильный для сетевых ресурсов, используется для FileBus наблюдения.

- fsync / os.replace
  - Коротко: рекомендуемая последовательность для атомарной записи файлов: записать в временный файл, flush, fsync, затем os.replace (атомарно заменить существующий файл).

- Smoke test
  - Коротко: быстрый рендер/проход UI для подтверждения, что view не падает при рендере.
  - Где: тесты в `tests/smoke/`.

- TDD (Test-Driven Development)
  - Коротко: практика писать тесты перед реализацией. В проекте это обязательная конвенция (`docs/arhitecture_2/05_roadmap.md`).

---
