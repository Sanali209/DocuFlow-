# DocuFlow — System Master Plan v7

> **Формат:** Псевдокод. Детали реализации уточняются по мере разработки.
> **Приоритет:** Текущий код > этот план > документация Obsidian.
> **История:** v3 → v4 → v5 → v6 → **v7 (финальный, полный)**
> **Актуализация:** См. [Task Board v2 Design](../superpowers/specs/2026-04-28-task-board-v2-design.md) — единый производственный центр с TaskGroup (замена batch_group_id).

---

## A. Контекст цеха (зафиксировано)

- **2 смены**, рабочие места = лазеры + ПК начальника
- **Оператор = Бригадир** — допустимое совмещение ролей (один человек)
- Оператор режет **с локального диска** (`NS` папка автоматики), не с сетевого
- **Нет QR-сканера** — поиск паллеты по части номера (live search)
- Среда — **Windows** везде
- **Нет бумажных чертежей** = инцидент, регистрируется через чат с фото/номерами

---

## B. Матрица ролей (финальная)

| Модуль | Оператор | Бригадир | Начальник | Кладовщик | **Админ** |
|---|---|---|---|---|---|
| Моя корзина | FULL | READ | — | — | **FULL** |
| Доска задач (все узлы) | — | FULL | FULL | — | **FULL** |
| Чат + файлы | FULL | FULL | FULL | FULL | **FULL** |
| Наряды / WorkItem | READ | FULL | FULL | — | **FULL** |
| Батчинг | — | FULL | FULL | — | **FULL** |
| Склад материалов | — | READ | FULL | FULL | **FULL** |
| Расходники | — | READ | FULL | FULL | **FULL** |
| Склад деталей | Создать | READ | FULL | FULL | **FULL** |
| PartLibrary + Шаблоны | READ | FULL | FULL | READ | **FULL** |
| FolderScanner | — | READ | READ | — | **FULL** |
| Настройки | — | — | — | — | **FULL** |
| Отчёты | — | READ | FULL | — | **FULL** |
| Admin Panel | — | — | — | — | **FULL** |

> **Админ** = разработчик / служба поддержки. Полный доступ ко всему для отладки.
> **Начальник** = все инструменты бригадира + аналитика + отчёты.
> **Роль бригадира и оператора** может быть у одного пользователя одновременно.

---

## C. Операционный цикл (детализированный)

### C1. Получение работы

```
СКАНЕР обнаруживает папку:
  CASE: папка + GNC файлы → WorkItem(NEW) → notify_chat("Новый наряд SIDRA-353203")
  CASE: папка + НЕТ GNC файлов → WorkItem(PENDING_CUTS)
    → notify_all("⚠️ SIDRA-353203: папка пришла, нестов нет! Сходить в раскрой")
    → WorkLog(SCAN_EMPTY_FOLDER)
    → ЖДЁМ: сканер перепроверяет при каждом poll
    → Когда GNC появились → автоматически → WorkItem(NEW) + notify("Несты готовы!")

  Тексты уведомлений — настраиваемые:
    NotificationTemplate (в AdminPanel):
      key: str       # "scan.empty_folder", "scan.new_work_item", "stock.alert" ...
      text: str      # Шаблон с переменными: "⚠️ {folder_name}: нестов нет!"
      enabled: bool
    Отображается везде через: render_template(key, {folder_name=...})

БРИГАДИР регистрирует физический документ:
  нажимает "Подтвердить получение бумажного наряда"
  CASE: папка уже есть → WorkItem(REGISTERED), doc_received_at = now
  CASE: папки нет → WorkItem(DOC_NO_FOLDER)
    → notify("Бумага получена, папки нет на диске")

ИНЦИДЕНТ "нет бумажных чертежей":
  фиксируется через чат (ChatMessage type=INCIDENT)
  прикладывается фото / список номеров деталей
  назначается ответственный
```

### C2. Подготовка к работе

```
БРИГАДИР:
  → проверяет материалы → если нет → дозаказ (ChatMessage type=ORDER)
  → настраивает правила батчинга (BatchRule: материал + толщина + размер)
  → BatchEngine автоматически группирует TaskItem по правилам
  → бригадир редактирует батчи вручную: перетащить таск, разбить батч, объединить
  → расставляет приоритеты, добавляет комментарии (type=INFO/WARNING)
  → РУЧНАЯ БЛОКИРОВКА: lock_reason + reason_text → TaskItem(BLOCKED)
    Причины: "Ждём новый раскрой", "Нет материала", "Срочное письмо вклинено", ...

ПРОВЕРКА ЗАПАСА (автоматически при сканировании):
  FOR each part_sku IN task_parts:
    IF ProductionUnit.is_stock AND part exists:
      WorkLog(STOCK_ALERT, "Деталь 3433-11-004-G есть в запасе!")
      ChatMessage(type=WARNING, ref=task_item, "Деталь есть в запасе — проверить!")
      TaskItem → BLOCKED (до решения бригадира)

УЧЁТ РАСХОДНИКОВ:
  При завершении TaskItem бригадир/оператор может списать расходники:
    ConsumableLog(operation=use, qty_delta, ref_task_item_id)
  При критическом остатке → автоматический алерт в чат
```

### C3. Приём в работу

```
ОПЕРАТОР видит доступные батчи на своём узле:
  фильтр: assigned_to_node = my_node OR global
  может: просматривать детали батча, SVG деталей, предупреждения
  может: редактировать батч (добавить/убрать таски)
  может: комментировать батч (ChatMessage)
  может: зарезервировать батч за собой → WorkerBucket

ВКЛИНИВАНИЕ письма/доработки:
  бригадир/оператор: перетащить WorkItem(MIHTAV/REWORK) в корзину
  → создаётся новый BatchEntry в существующем WorkerBucket
  → WorkLog(HANDOVER, "Вклинили письмо MIHTAV-XXX по причине: срочно")

ПРЕДУПРЕЖДЕНИЯ PartTemplate:
  при открытии карточки TaskItem → показывать все шаблоны деталей из task_parts
  VISIBLE TO: оператор (prominently), бригадир
```

### C4. Выполнение

```
СТАТУСЫ ВМЕСТО СТАРТ/СТОП:
  Оператор меняет статус TaskItem:
    planned → in_progress (с причиной если нужно)
    in_progress → on_hold (кратковременная, обязательна причина + description)
    in_progress → suspended (длительная приостановка)
    on_hold → in_progress
    suspended → in_progress | done | cancelled
    in_progress → done (+ автоматический qty_produced + sheets_done)

ТРЕКИНГ ЛИСТОВ:
  TaskItem.sheets_done: int  # Сколько листов уже порезано
  TaskItem.sheet_qty: int    # Всего листов
  Оператор обновляет sheets_done при каждом следующем листе
  UI: прогресс-бар "5 из 8 листов"

ОЦЕНКА ВРЕМЕНИ:
  estimated_minutes: int   # из GNC-парсера (кол-во контуров × avg_time) + допуск %
  actual_minutes: int      # вычисляется из (started_at, completed_at) и пауз
  drift: float             # (actual - estimated) / estimated × 100%
  → бригадир видит дрейф оценок, может корректировать коэффициент

NS-ЗЕРКАЛО (критично):
  Оператор режет с локальной папки NS (папка автоматики станка)
  Проблема: сетевой файл обновился, оператор режет со старой версии

  Решение — NS Mirror Service (Background):
    FOR each task_item IN worker_bucket[node]:
      network_path = resolve(task_item.file_path, scan_root)
      local_ns_path = NS_FOLDER / task_item.file_name

      IF local_ns_path не существует:
        copy(network_path → local_ns_path)
        WorkLog(INFO, "Скопирован в NS: {file_name}")

      ELIF md5(network_path) != md5(local_ns_path):
        WorkLog(FILE_CHANGED, "⚠️ Сетевой файл отличается от локального!")
        ChatMessage(type=WARNING, "Файл {name} обновился на сети! Обновить NS?")
        → UI: диалог "Обновить NS / Оставить старый / Пропустить"
        IF operator confirms:
          copy(network_path → local_ns_path)

ИНЦИДЕНТЫ:
  Оператор/бригадир создаёт IncidentLog:
    types: laser_failure | part_defect | material_defect | waiting_crane |
           waiting_forklift | urgent_letter_inserted | other
  Публикуется в чат автоматически (ChatMessage type=INCIDENT)
  С указанием длительности простоя
  Можно указать ссылку (ref_work_item_id / ref_task_item_id)
  Вложения: пути к фото/файлам через JSON список (attachments?: JSON)
```

### C5. Завершение

```
TaskItem → DONE:
  автоматический расчёт qty_produced:
    qty_produced = sum(TaskPart.qty for part in task.parts) * sheets_done
    fallback: если parts пустой → qty_produced = sheets_done
  диалог "Куда кладём?":
    Вариант A: Новая паллета
      → ProductionUnit(
          label_id = generate_human_id(),
          task_item_id = task.id,
          qty_produced = auto_calculated
        )
      → оператор выбирает или создаёт StorageLocation
    Вариант B: К существующей
      → live search по label_id (partial match)
      → пример: ввёл "LASER_1-001" → показывает ["26-04-LASER_1-0015", ...]
      → выбирает → qty добавляется к существующей
    (Нет QR-сканера → только ввод + поиск)

  Списание материала:
    MaterialAudit(write_off, qty=sheets_done, ref=task_item)
    Приоритет: reservation → FIFO fallback

generate_human_id():
  year = now.year[-2:]       # "26"
  month = now.month          # "04"
  node_code = workplace.code # "LASER_1" (код узла)
  seq = next_seq_for(node, month)  # 0015 ...
  return f"{year}-{month:02d}-{node_code}-{seq:04d}"  # "26-04-LASER_1-0015"
```

### C6. Складирование

```
РЕГИСТРАЦИЯ (включая до-системные паллеты):
  кладовщик/бригадир может создать ProductionUnit вручную
  без привязки к TaskItem (для до-системного учёта):
    ProductionUnit(label_id=manual, task_item_id=NULL, is_pre_system=True)

ПОИСК:
  по label_id (partial) → живой поиск по всем паллетам
  по SKU детали → все паллеты где есть эта деталь
  по work_item → все паллеты наряда SIDRA-353203
  по материалу → все паллеты из алюминия 3мм
  по storage_location → что лежит на стеллаже A-02-3

ЧАСТИЧНЫЙ ПЕРЕВОД В ЗАПАС:
  ProductionUnit можно "разбить":
    split(unit, qty_to_stock=10) →
      unit_stock(qty=10, is_stock=True)
      unit_active(qty=remaining)
    оба получают новые label_id, старый архивируется

ОБЪЕДИНЕНИЕ ПАЛЛЕТ:
  merge(unit_a, unit_b) → новый label_id, списывает оба исходных
  (пришло из v5, отсутствовало в v6)

ОТКРЫТЬ В EXPLORER:
  кнопка "📂 Открыть папку" рядом с любым WorkItem/TaskItem
  os.startfile(str(resolved_path.parent))  # Windows: открывает Explorer
```

---

## D. Точный формат GNC (реальный sample)

```gnc
(CK-AN Post V22.1 SP383  run on JUL 07 2025)    ← пост-процессор
(*MODEL HANS_G3015-REXROTH)                       ← модель МАШИНЫ (не проекта!)
(1  PARTS)                                         ← кол-во деталей
(DATE JUL 07 2025)
(*SHEET 3250.0 1250.0 3.0 7 1 0.0 0.0 )           ← КЛЮЧЕВАЯ строка
  │          │      │   │  │
  │     sheet_x  sheet_y │  cut_count (7 листов)
  │              thickness  batch_idx (1)
(Material:AA 5052-H32)                             ← марка материала
(THICKNESS=3.0)                                    ← дублирует *SHEET
(PART SIZE=3201.25  X 1136.361)                    ← bounding box НЕСТA (не детали!)
(SHEET SIZE=3250.0 ,1250.0)                        ← дублирует *SHEET

(*****Part info*****)
(PART NAME:3433-11-004-G-1 )                       ← артикул + версия

(==== CONTOUR 1 ====)
N1005 G00X971Y485.361 ...                          ← G-код
```

> **ВАЖНО:** `*MODEL` = имя машины (HANS_G3015-REXROTH), **НЕ** шаг проекта.
> Шаг берётся из **имени папки** (SHLAV-2 в SIDRA-353203-**SHLAV-2**-07.07.2025).
> `PART SIZE` = bbox **всего нестa**, не отдельной детали. Для точного bbox
> детали нужен парсинг G-кода контуров через SVGGenerator.calculate_bounds().

---

## E. Паттерны парсинга

### E1. FolderNameParser

```python
SIDRA_REGEX = re.compile(
    r'^SIDRA-(?P<number>\d+)-(?P<step>.+?)-(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$',
    re.IGNORECASE
)

def parse_folder_name(name: str) -> FolderMeta:
    m = SIDRA_REGEX.match(name)
    if m:
        return FolderMeta(
            work_item_type=WorkItemType.SIDRA,
            sidra_number=m.group("number"),
            sidra_step=m.group("step"),     # "SHLAV-2" = шаг наряда
            project_hint=m.group("step"),   # используем для поиска Project
            doc_date=date(int(m.group("year")), int(m.group("month")), int(m.group("day")))
        )
    # Fallback: не SIDRA → MIHTAV или нестандартное → Default проект
    return FolderMeta(
        work_item_type=WorkItemType.MIHTAV,
        project_hint=None,
    )
```

### E2. SKU extraction из PART NAME

```python
def extract_sku(part_name_raw: str) -> tuple[str, str, str | None]:
    """
    Input:  "3433-11-004-G-1 " (с возможными пробелами, путями)
    Output: (sku, version_letter, version_suffix)

    Логика: последний БУКВЕННЫЙ сегмент = версия (letter),
            последний ЦИФРОВОЙ сегмент после версии = version_suffix (назначение TBD)

    "3433-11-004-G-1" → sku="3433-11-004-G", version="G", version_suffix="1"
    """
    # Убираем путь (если есть \\server\path\...)
    name = part_name_raw.strip().split("\\")[-1]
    # Убираем расширение (.dft, .DFT)
    name = re.sub(r'\.\w+$', '', name).strip()

    segments = name.split("-")

    # Находим последний буквенный сегмент = буква версии
    version_letter = "A"
    version_idx = -1
    for i, seg in enumerate(reversed(segments)):
        if seg.isalpha():
            version_letter = seg
            version_idx = len(segments) - 1 - i
            break

    if version_idx < 0:
        return name, "A", None

    sku = "-".join(segments[:version_idx + 1])  # "3433-11-004-G"
    suffix_parts = segments[version_idx + 1:]
    version_suffix = "-".join(suffix_parts) if suffix_parts else None  # "1"

    return sku, version_letter, version_suffix

# Итог для PartLibrary.sku = "3433-11-004-G"
# TaskPart.version = "G", TaskPart.version_suffix = "1" (сохраняем, не используем для ID)
```

> **Открытый вопрос (из v4):** Что означает цифра `version_suffix` ("1" в "3433-11-004-G-1")?
> Инкремент версии? Номер экземпляра? Пока: сохраняем, не используем для идентификации.

### E3. Хранение путей (буквонезависимость)

```python
# При сканировании: сохраняем ОТНОСИТЕЛЬНЫЙ путь от scan_root
def to_relative_path(abs_path: str, scan_root: str) -> str:
    return str(Path(abs_path).relative_to(scan_root))

# При доступе к файлу: восстанавливаем через LOCAL env
def resolve_path(relative_path: str, scan_root: str) -> Path:
    return Path(scan_root) / relative_path
```

### E4. Детекция изменения файла

```python
def compute_hash(file_path: Path) -> str:
    return hashlib.md5(file_path.read_bytes()).hexdigest()

def atomic_write(path: str, data: bytes):
    """Атомарная запись: tmp → fsync → os.replace (из v3/v4)"""
    tmp = Path(path + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def check_file_changes(task_item: TaskItem, scan_root: str, session, orchestrator):
    abs_path = resolve_path(task_item.file_path, scan_root)
    new_hash = compute_hash(abs_path)
    if new_hash != task_item.file_hash:
        old_hash = task_item.file_hash
        task_item.file_hash = new_hash
        log = WorkLog(
            task_item_id=task_item.id,
            log_type=WorkLogType.FILE_CHANGED,
            author="system",
            message=f"GNC file changed: {task_item.file_name}",
            payload=json.dumps({"old_hash": old_hash, "new_hash": new_hash})
        )
        session.add(log)
        orchestrator.broadcast_command("FILE_CHANGED_ALERT", {
            "task_item_id": task_item.id,
            "file_name": task_item.file_name,
        })
```

### E5. Идемпотентный импорт (upsert)

```python
# TaskItem идентифицируется по file_path (относительный) — ключ идемпотентности
# Логика при повторном сканировании:

def upsert_task_item(session, folder_path, file_path, new_hash, gnc_data):
    existing = session.exec(
        select(TaskItem).where(TaskItem.file_path == file_path)
    ).first()

    if not existing:
        # Первый импорт
        task = TaskItem(file_path=file_path, file_hash=new_hash, ...)
        session.add(task)
        WorkLog(log_type=INFO, message="Создан TaskItem")
    elif existing.file_hash != new_hash:
        # Файл изменился — обновить + уведомить
        check_file_changes(existing, ...)
    # else: хэш совпадает → skip (идемпотентно)
```

---

## F. Сущности (псевдокод)

### F1. Производственная иерархия

```
Project
  id, name (unique), description
  is_default: bool        # "Default" всегда существует
  deadline: date?
  status: active|completed|archived
  → work_items[], tags[], comments[]

WorkItem
  id, project_id
  work_item_type: SIDRA|MIHTAV|REWORK

  status:
    NEW              # сканер нашёл папку + GNC
    PENDING_CUTS     # папка есть, GNC нет (ждём раскрой)
    FOLDER_NO_DOC    # несты есть, бумажного наряда нет
    DOC_NO_FOLDER    # бумага есть, папки нет
    REGISTERED       # папка + документ подтверждены
    IN_PROGRESS      # хотя бы один TaskItem in_progress
    ON_HOLD          # всё заморожено
    DONE             # все TaskItem done
    CANCELLED
    ARCHIVED

  folder_name: str (unique, idx)  # ключ идемпотентности
  folder_path: str                 # относительный от scan_root

  # SIDRA-специфика (null если не удалось распарсить)
  sidra_number: str?    # "353203"
  sidra_step: str?      # "SHLAV-2"

  folder_found_at, doc_received_at?, started_at?, completed_at?, last_scanned_at?

  → task_groups[], logs[], reservations[], tags[], comments[]

TaskGroup
  id, work_item_id
  name: str?            # например "ST37-2 4.0mm"
  grouping_rule: str    # 'auto_material' | 'manual'
  created_by?: str
  created_at: timestamp
  → task_items[]

TaskItem
  id, work_item_id, task_group_id?, mat_type_id?

  status: PLANNED|IN_PROGRESS|ON_HOLD|SUSPENDED|DONE|CANCELLED|BLOCKED
  priority: 0-2
  is_urgent: bool

  file_name, file_path (relative!), file_hash (MD5)

  # Из GNC
  sheet_x?, sheet_y?, sheet_qty?, thickness?
  gnc_date?      # DATE строка из GNC

  # Прогресс трекинг
  sheets_done: int = 0       # сколько листов уже порезано
  qty_produced?: int          # финальный факт (авто: sum(TaskPart.qty) * sheets_done)

  # Оценка времени
  estimated_minutes?: int    # из GNC парсера + коэффициент
  actual_minutes?: int       # вычисляется из хронологии + пауз

  step_index?, batch_index?  # из имени файла (nullable)

  assigned_to_node?, scanned_at, started_at?, completed_at?
  block_reason?: str          # Причина блокировки (если BLOCKED)

  → task_parts[], production_units[], logs[], bucket_entries[]

TaskPart
  id, task_item_id, part_sku (→PartLibrary)
  version: str          # буква версии: "G" в "3433-11-004-G"
  version_suffix?: str  # цифровой суффикс: "1" в "3433-11-004-G-1" (назначение TBD)
  qty: int

PartLibrary
  sku (PK), mat_type_id?
  name?, bbox_x?, bbox_y?    # bbox из SVGGenerator.calculate_bounds()
  contour_count, corner_count, hole_count
  weight_per_pcs?, svg_preview_path?
  first_seen_at, last_seen_at
  → task_parts[], templates[]

PartTemplate
  id, part_sku, message, severity: info|warning|critical
  created_by
  # При открытии TaskItem → показывать в карточке оператору!
```

### F2. Материалы

```
MaterialType
  id, code (idx), form_factor: SHEET|TUBE|BAR|OTHER
  thickness?, nominal_x?, nominal_y?
  weight_per_sheet?        # кг (для аудита по весу)
  primary_unit: pcs|kg|m2

  # Параметры для расчёта времени резки (редактируются бригадиром):
  cut_speed_mm_per_min: float     # скорость резки (мм/мин)
  pierce_time_sec: float          # время прокола одного контура (сек)
  idle_speed_mm_per_min: float    # скорость холостых перемещений (мм/мин)
  time_tolerance_pct: float = 15  # допуск % (инциденты, смена материала и т.д.)

  → stock_items[]

MaterialStock
  id, mat_type_id
  status: AVAILABLE|RESERVED|ALLOCATED|CONSUMED|DEFECT
  batch_code?, quantity, quantity_kg?, location?
  → reservations[], audits[]

Reservation
  id, stock_item_id, work_item_id, qty_reserved
  reservation_type: soft|hard

MaterialAudit
  id, stock_item_id
  operation: income|write_off|correction|defect|reorder
  qty_delta, qty_kg_delta?
  reason?, ref_task_item_id?, author?, node_id?

Consumable
  id, name (unique), category: nozzle|lens|tape|gas|other
  unit, quantity, min_quantity
  → logs[]

ConsumableLog
  id, consumable_id
  operation: use|restock|write_off
  qty_delta, ref_task_item_id?, author?, note?
```

### F3. Производственная логистика

```
StorageLocation
  id, code (unique), name?, is_active

ProductionUnit
  id
  label_id: str (unique)       # "25-07-А-042" (человекочитаемый)
  task_item_id?: int           # NULL для до-системных паллет
  storage_location_id?
  qty_produced, is_stock: bool
  is_pre_system: bool = False  # Паллета создана до внедрения системы
  stock_transferred_at?
  parent_label_id?: str        # Если создана split-ом
  created_by?
```

### F4. Корзина и коммуникация

```
WorkerBucketEntry
  id, node_id (idx), assigned_user?
  task_item_id, task_group_id?   # FK на TaskGroup (замена batch_group_id UUID)
  locked_at
  handover_note?, handover_at?, handover_from?

WorkLog
  id, work_item_id?, task_item_id?
  log_type: INFO|WARNING|FILE_CHANGED|STATUS_CHANGE|ON_HOLD|HANDOVER|
            STOCK_ALERT|SCAN_ERROR|BLOCKED|EMPTY_FOLDER|NS_MIRROR
  author?, node_id?, message, payload?: JSON

IncidentLog
  id, task_item_id?, work_item_id?
  node_id?, incident_type, description, reported_by
  resolved: bool, resolved_by?, resolved_at?
  attachments?: JSON  # список relative paths к файлам/фото

ChatMessage
  id, author, node_id
  message_type: MESSAGE|INFO|WARNING|URGENT|ORDER|INCIDENT|HANDOVER|REPORT
  content: str
  ref_project_id?, ref_work_item_id?, ref_task_item_id?
  parent_message_id?    # Дерево ответов
  template_name?
  attachments?: JSON    # Файлы (pdf, изображения, задания от начальника)
  is_read: bool

Tag
  id, name (unique), color?
  ref_project_id?, ref_work_item_id?, ref_task_item_id?

ReportTemplate
  id, name, author
  template_html: str        # Jinja2 шаблон HTML
  description?
  last_used_at?

ViewPreset                  # Notion-подобные пресеты вида
  id, view_name: str        # "task_board_production" | "task_board_bucket" | ...
  owner: str                # username или "global"
  name: str
  filters_json: JSON        # фильтры, сортировка, группировка, колонки
  is_default: bool

ViewState                   # Состояние раскрытия уровней иерархии
  id, user_id: str
  view_name: str            # "task_board_production"
  entity_type: str          # "project" | "workitem" | "taskgroup"
  entity_id: str
  is_expanded: bool = True
```

---

## G. Уточнённые функциональные механизмы

### G1. NS-Зеркало (критично для оператора)

```
NSMirrorService (background task на каждом узле):
  ns_folder      = config.local_ns_path    # из .env: "C:\NS\cutting"
  check_interval = settings.ns_mirror_interval_seconds  # default: 60s
  copy_timeout   = settings.ns_mirror_copy_timeout_s    # default: 30s (защита от зависания)

  loop: sleep(check_interval)
  for entry in WorkerBucket[this_node]:
    network_file = resolve(entry.task_item.file_path, scan_root)
    local_file   = ns_folder / entry.task_item.file_name

    if not local_file.exists():
      copy(network_file → local_file)
      WorkLog(NS_MIRROR, "Скопирован в NS")

    elif md5(network_file) != md5(local_file):
      WorkLog(FILE_CHANGED, f"⚠️ {file_name}: сетевой ≠ локальный!")
      alert_operator(node=this_node, task_item=entry.task_item,
                     message="Файл обновился. Обновить NS-копию?")
      # Оператор выбирает: Обновить / Оставить / Напомнить позже

  on_task_done or removed_from_bucket:
    delete(local_file)   # Убираем из NS после завершения
```

### G2. TaskGroupService (замена BatchEngine)

```
TaskGroup — полноценная DB-сущность (заменяет batch_group_id UUID):
  id, work_item_id, name, grouping_rule, created_by, created_at
  grouping_rule: 'auto_material' | 'manual'

Авто-группировка (DEFAULT):
  GROUP BY: mat_type_id + thickness (+ sheet_x + sheet_y опционально)
  grouping_rule = 'auto_material'
  UPDATE TaskItem.task_group_id = TaskGroup.id

TaskGroupService:
  auto_group_by_material(work_item_id) → TaskGroup[]
  create_manual_group(task_ids, name) → TaskGroup
  move_task_to_group(task_id, group_id)
  split_group(group_id, task_ids) → TaskGroup
  merge_groups(group_ids) → TaskGroup
  get_group_status(group) → TaskGroupStatus  # агрегация из задач
  get_group_progress(group) → float          # средний прогресс

Рекомендации при редактировании группы:
  "Добавить в группу?" → TaskItem из других нарядов с тем же MAT
  "⚠️ Деталь в запасе!" → если is_stock=True для части task_parts
```

### G3. Временные оценки TaskItem

```
# Параметры хранятся в MaterialType (редактируются бригадиром):
GncParser → estimate_time(gnc_sheet, mat_type) → minutes:
  pierce   = contour_count × mat_type.pierce_time_sec
  cut      = cut_length_mm / mat_type.cut_speed_mm_per_min × 60
  idle     = idle_length_mm / mat_type.idle_speed_mm_per_min × 60
  base     = (pierce + cut + idle) × sheet_qty / 60
  estimate = base × (1 + mat_type.time_tolerance_pct / 100)
  return estimate

TaskItem.estimated_minutes = estimated
TaskItem.actual_minutes    = (completed_at - started_at) - Σ(on_hold durations)
drift = (actual - estimated) / estimated × 100%

# Бригадир видит drift → корректирует mat_type.time_tolerance_pct или cut_speed
```

### G4. Поиск деталей (прямой и обратный)

```
# Из v3 — явный раздел поиска, пропавший в v6:

ПРЯМОЙ: "Есть ли деталь 3433-11-004-G в наряде SIDRA-353203?"
  PartLibrary.sku → TaskPart → TaskItem → WorkItem (filter by folder_name)

ОБРАТНЫЙ: "В каких нарядах / проектах встречается деталь 3433-11-004-G?"
  PartLibrary.sku → TaskPart[] → TaskItem[] → WorkItem[] → Project[]

ПОИСК по габаритам (с допуском):
  SELECT * FROM partlibrary
  WHERE bbox_x BETWEEN :x_min AND :x_max
  AND   bbox_y BETWEEN :y_min AND :y_max
  AND   mat_type_id = :type
  [AND  hole_count = :holes]
  [AND  corner_count BETWEEN :min AND :max]

ПОИСК паллеты:
  по label_id (partial) → живой поиск
  по SKU детали → TaskPart → TaskItem → ProductionUnit
  по work_item  → все паллеты наряда
  по storage_location → что лежит на стеллаже A-02-3
```

### G5. Отчёты (Report Generator — модульная архитектура)

```
ReportDataBlock:
  name: str           # "work_items_summary", "material_usage", ...
  description: str
  params: [str]       # ["date_from", "date_to", "node_id"]
  query_fn: callable

ReportRegistry (singleton):
  register(block: ReportDataBlock)
  get_block(name) → ReportDataBlock
  available_blocks() → список

# Модули регистрируют свои блоки при старте:
work_items.report_blocks:  "work_items_summary", "work_item_detail"
task_board.report_blocks:  "tasks_by_node", "shift_completion"
material.report_blocks:    "material_usage", "stock_snapshot"
incidents.report_blocks:   "incident_log", "downtime_summary"
part_lib.report_blocks:    "parts_produced"

# Шаблон HTML (Jinja2):
{{ blocks.material_usage(date_from=params.date_from) }}
{{ blocks.shift_completion(node_id=params.node_id) }}

ReportSystem:
  generate(template, params) → HTML:
    context = { blocks: BlockProxy(registry, params), params }
    return jinja_env.render(template.template_html, context)
  export_pdf(html) → bytes   # weasyprint / pdfkit
  download(pdf)              # NiceGUI ui.download()

Встроенные шаблоны:
  - Отчёт по смене  - Ход наряда  - Движение материала
  - Инциденты       - План vs Факт (estimated vs actual)
```

### G6. Открыть в Explorer (Windows — все узлы)

```python
def open_in_explorer(task_item):
    scan_root = settings.sidra_scan_path   # из local env этого узла
    if not scan_root:
        show_unc_hint(task_item)  # fallback: показать текстовый путь
        return
    abs_path = Path(scan_root) / task_item.file_path
    subprocess.run(["explorer.exe", str(abs_path.parent)])

def show_unc_hint(task_item):
    # Fallback: показать относительный путь в диалоге
    # "Путь: sidra\SIDRA-353203-SHLAV-2\01-01-...-ST37.GNC"
    pass

# Кнопка "📂" — видна на ВСЕХ узлах
# Работает если LOCAL env настроен | иначе — fallback с текстом пути
```

### G7. ViewPreset (Notion-подобные виды)

```
ViewPreset:
  module: "work_items" | "task_board" | "part_library" | ...
  owner: username | "global"  # global = по умолчанию для всех
  preset_json:
    filters:   [{field, op, value}]
    sort:      [{field, dir}]
    group_by:  field | null
    columns:   [field_name]
    view_type: "table" | "kanban" | "list" | "cards"

UI: "Мои виды" = личные пресеты
    "Общие виды" = owner="global"
    Переключатель вкладок вверху таблицы (как в Notion)
```

### G8. SVGGenerator — bbox из реального G-кода

```python
# SVGGenerator.calculate_bounds(part) → (min_x, min_y, max_x, max_y)
# generate_thumbnail(part, path) → возвращает (data_w, data_h) — реальные мм детали

# При сканировании GNC → PartLibrary:
svg_gen = SVGGenerator()
data_w, data_h = svg_gen.generate_thumbnail(
    part=gnc_sheet.parts[0],
    output_path=f"previews/{sku}.svg"
)
part_lib.bbox_x = data_w   # Реальная ширина из G-кода (НЕ из PART SIZE!)
part_lib.bbox_y = data_h
```

### G9. Файловые блокировки (из v3/v4)

```python
# Для конкурентного сканирования — использовать portalocker/filelock:
import filelock

lock_path = Path(settings.sidra_scan_path) / ".docuflow.lock"
with filelock.FileLock(str(lock_path), timeout=5):
    scan_folder(...)
```

### G10. Настройки (LOCAL env — окончательно)

```python
class FolderScannerSettings(BaseModuleSettings):
    # LOCAL — env per node, НИКОГДА не синхронизируются через P2P
    sidra_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    mihtav_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    other_scan_path: str = Field(default="", json_schema_extra={"scope": "local"})
    poll_interval_seconds: int = Field(default=300, json_schema_extra={"scope": "local"})

    # GLOBAL — синхронизируются через P2P
    enabled: bool = Field(default=True, json_schema_extra={"scope": "global"})
    default_project_name: str = Field(default="Default", json_schema_extra={"scope": "global"})

# .env каждого узла:
# DOCUFLOW_FOLDER_SCANNER__SIDRA_SCAN_PATH=Z:\sidra
# DOCUFLOW_FOLDER_SCANNER__MIHTAV_SCAN_PATH=Z:\mihtav
# DOCUFLOW_FOLDER_SCANNER__OTHER_SCAN_PATH=Z:\other
```

---

## H. Структура модулей

```
features/
  folder_scanner/     # ФАЗА 1
    parsers/          #   gnc.py, folder_name.py, task_file.py
    system.py         #   FolderScannerSettings + FolderScannerSystem
    scanner.py        #   Polling loop (master only) + file locks
    ns_mirror.py      #   NSMirrorService (all nodes)
    view.py           #   Статус + лог + Scanner Now

  work_items/         # ФАЗА 2
    system.py         #   WorkItemSystem: CRUD + lifecycle + doc registration
    view.py           #   Список + карточка + WorkLog + PartTemplates alerts

  task_board/         # ФАЗА 2 → Task Board v2
    task_group_service.py  # TaskGroupService: авто/ручная группировка (замена BatchEngine)
    system.py              # TaskBoardSystem: иерархия, фильтры, пресеты, bucket, drift%
    view.py                # Единый Task Board: 2 таба (Производство + Моя корзина)

  part_library/       # ФАЗА 3
    system.py         # PartLibrarySystem: поиск (SKU / bbox±tol / holes) + SVG
    view.py           # Таблица + превью + шаблоны предупреждений + корзина заказа

  parts/              # 🛒 Task Board v2 — корзина заказа деталей
    order_cart.py     # OrderCart (сессионная корзина)
    rework_generator.py  # Генерация nest + WorkItem из корзины

  material_stock/     # ФАЗА 3
    system.py         #   MaterialSystem + аудит + резервирование
    view.py           #   Типы → остатки + движения

  consumables/        # ФАЗА 3
    system.py
    view.py           #   Расходники + критический порог + лог

  production/         # ФАЗА 4
    system.py         #   ProductionUnit: create/split/merge + StorageLocation
    view.py           #   Паллеты + поиск + обратный поиск + Explorer button

  chat/               # ФАЗА 4
    system.py         #   ChatSystem: треды + типы + шаблоны + файлы
    view.py           #   Дерево + compose + фильтр по объекту

  incidents/          # ФАЗА 4
    system.py
    view.py           #   Список инцидентов + статистика простоев

  reports/            # ФАЗА 5
    system.py         #   ReportSystem: шаблоны + PDF генерация
    view.py           #   Список шаблонов + конструктор + скачать

  analytics/          # ФАЗА 5
    view.py           #   Начальник: ход работы vs план + КПД по узлам

  admin/              # СУЩЕСТВУЕТ → доработать
    system.py         #   + Settings Editor (local paths) + ViewPreset mgmt
    view.py           #   User/Role/Matrix + Workplace + Settings + Presets

lib/widgets/
  status_badge.py
  work_item_card.py
  task_item_row.py         # + паллета (DONE), прогресс, быстрые действия
  task_group_row.py        # Агрегированный статус и прогресс группы
  hierarchy_table.py       # Древовидная таблица с раскрытием уровней
  hierarchy_row.py         # Двухстрочная строка иерархии
  material_chip.py
  part_preview.py          # SVGGenerator интеграция
  nest_preview.py          # Превью раскладки деталей на листе
  scan_log_panel.py
  file_changed_alert.py    # Диалог: GNC изменился!
  chat_thread.py           # Дерево сообщений (рекурсивный виджет)
  chat_compose.py          # Composer с типами + шаблоны
  bucket_panel.py          # Корзина оператора (TaskGroup → таски)
  filter_panel.py          # Панель комплексных фильтров с пресетами
  handover_form.py         # Форма передачи смены
  handover_banner.py       # Баннер входящей передачи смены
  report_builder.py        # Конструктор отчётов
  view_preset_switcher.py  # Notion-like вкладки пресетов
  explorer_button.py       # "📂 Открыть в Explorer"
  ns_mirror_status.py      # Индикатор синхронизации NS
  order_cart_panel.py      # Панель корзины Part Library
```

---

## I. Что переиспользуем из Old MVP

| Компонент | Файл MVP | Действие |
|---|---|---|
| `GNCParser` | `parsers/gnc_parser.py` | ✅ Копируем + исправить SKU extract + сохранить corner/hole count |
| `SVGGenerator` | `graphics/svg_generator.py` | ✅ Копируем как есть → `calculate_bounds()` + `generate_thumbnail()` → (data_w, data_h) |
| `is_variant` dedup logic | `sync/scanner.py` | ✅ Переносим в `parsers/task_file.py` |
| `InventoryService` паттерн | `services/inventory_service.py` | ✅ Паттерн, не код |
| FastAPI / SQLAlchemy / Svelte | — | ❌ Заменяется фреймворком DocuFlow |

---

## J. Открытые вопросы (не закрыты с v4)

> **Q1: version_suffix в SKU** (`3433-11-004-G-1` → суффикс "1")
> Что означает цифра после буквы версии? Пока: сохраняем в `TaskPart.version_suffix`, не используем для идентификации.

> **Q2: ChatMessage синхронизация**
> Чат синхронизируется через FileBus broadcast или хранится в БД для истории?
> Рекомендация: хранить в БД (для ретроспективы смены), broadcast только для real-time уведомлений.

> **Q3: WorkerBucket — один или много TaskItem одновременно?**
> Оператор берёт батч целиком (все TaskItem в батче) или по одному?
> Текущее: берёт батч → все его TaskItem попадают в корзину.

> **Q4: Attachments / manifest**
> Вложения (фото, PDF) хранятся в `attachments/<uuid>/` с `manifest.json`.
> Нужен единый механизм для IncidentLog, ChatMessage и WorkItem.

---

## K. Фазированный план

### Фаза 1 — Домен + Scanner (ТЕКУЩИЙ ПРИОРИТЕТ)
```
[ ] Переписать production.py — все сущности (псевдокод → SQLModel)
[ ] GncParser: SKU extract (с version_letter + version_suffix) + SVGGenerator bbox
[ ] FolderNameParser: SIDRA regex + graceful fallback
[ ] TaskFileParser: is_variant dedup + step/batch extraction
[ ] FolderScannerSystem: polling loop (master) + file locks + empty folder detection
[ ] Идемпотентный upsert TaskItem (по file_path)
[ ] NSMirrorService: фоновый сервис копирования в NS папку
[ ] folder_scanner/view.py: статус + лог + Scan Now
```

### Фаза 2 — Оперативная работа
```
[ ] WorkItemSystem + work_items/view.py
    → регистрация физического документа
    → статус PENDING_CUTS + оповещение
[ ] TaskBoardSystem + bucket + TaskGroupService (замена batch_engine)
[ ] task_board/view.py: Единый Task Board — 2 таба (Производство + Моя корзина)
[ ] Трекинг листов (sheets_done / sheet_qty) + прогресс-бар
[ ] Временные оценки (estimated/actual/drift) + параметры MaterialType
[ ] Базовые виджеты: status_badge, bucket_panel, batch_card
```

### Фаза 3 — Склад + Справочники
```
[ ] MaterialSystem + аудит + резерв
[ ] PartLibrarySystem: поиск с допуском по bbox + hole_count + corner_count
[ ] ConsumableSystem + критический остаток + алерт
[ ] PartTemplate: шаблоны предупреждений в карточке TaskItem
[ ] ViewPreset: сохранение пресетов вида
```

### Фаза 4 — Коммуникация + Логистика
```
[ ] ChatSystem: древовидные треды + типы + файлы + шаблоны + attachments
[ ] IncidentSystem: трекинг + публикация в чат + attachments/фото
[ ] ProductionSystem: create/split/merge + label_id генерация
[ ] StorageLocation + live search по части номера
[ ] Обратный поиск: деталь → паллета → стеллаж
[ ] explorer_button.py (subprocess → explorer.exe)
[ ] Регистрация до-системных паллет (is_pre_system)
```

### Фаза 4.5 — Task Board v2 (Единый производственный центр)
```
[ ] TaskGroup entity + миграция batch_group_id → task_group_id
[ ] TaskGroupService: авто/ручная группировка, split/merge
[ ] Единый Task Board view: 2 таба (Производство + Моя корзина)
[ ] HierarchyTable + HierarchyRow (двухстрочные строки)
[ ] ViewState: сохранение раскрытия уровней в БД
[ ] ViewPreset: комплексные фильтры с пресетами
[ ] Omnisearch v2: поиск по всем уровням + паллеты + детали
[ ] Авто-расчёт qty_produced = sum(TaskPart.qty) * sheets_done
[ ] Диалог завершения: "Создать новую паллету" / "Добавить к существующей"
[ ] Связь TaskItem ↔ ProductionUnit с обратным поиском
[ ] Резервирование материала при назначении на узел
[ ] Авто-списание материала при DONE (reservation → FIFO)
[ ] Интеграция Part Library: клик на деталь → модальное окно
[ ] Интеграция Warehouse: резервирование из Task Board, вкладка РЕЗЕРВЫ
[ ] Интеграция Chat: HANDOVER тип, deeplink #<task_id>, канал Производство
[ ] Интеграция Incidents: deeplink на TaskItem, фильтр по Project/WorkItem
[ ] Интеграция Analytics: метрики TaskGroup, node_utilization, pallet_by_project
[ ] Интеграция Reports: task_group_summary, material_reservation, pallet_by_project
[ ] Модальные окна: Project, WorkItem, TaskGroup, TaskItem, Pallet
[ ] Превью неста: SVG раскладка деталей на листе
[ ] Part Library: корзина заказа + генерация rework nests
```

### Фаза 5 — Аналитика + Отчёты
```
[ ] ReportSystem: Jinja2 шаблоны + PDF (weasyprint)
[ ] Встроенные шаблоны: смена / наряд / материалы / инциденты / план vs факт
[ ] analytics/view.py: ход работы vs план + КПД узлов
[ ] Доработка admin/view.py: ViewPreset manager + Settings Editor
```

---

## L. Сводка изменений относительно v6 (что восстановлено)

| # | Что восстановлено / добавлено | Источник |
|---|---|---|
| 1 | Раздел D: Точный формат GNC с реальным sample + пояснения по `*MODEL` и `PART SIZE` | v3 |
| 2 | Раздел E1: FolderNameParser с полным SIDRA_REGEX + fallback | v3 |
| 3 | Раздел E2: SKU extraction — полная логика с version_letter + version_suffix, примеры | v3/v4 |
| 4 | Раздел E3: Хранение путей — функции `to_relative_path` / `resolve_path` | v3 |
| 5 | Раздел E4: `compute_hash`, `atomic_write` (tmp→fsync→replace), `check_file_changes` | v3/v4 |
| 6 | Раздел E5: Идемпотентный upsert (логика при повторном сканировании) | v3/v4 |
| 7 | G2: `DEFAULT_RULE` для BatchEngine (конкретный пример стандартного правила) | v3/v4 |
| 8 | G4: Явный раздел поиска деталей (прямой + обратный + по bbox + по hole_count) | v3 |
| 9 | G8: SVGGenerator — явный код вызова + пояснение что это реальный bbox из G-кода | v5 |
| 10 | G9: Файловые блокировки (portalocker/filelock) при конкурентном сканировании | v3/v4 |
| 11 | C6: `merge(unit_a, unit_b)` для ProductionUnit (было в v5, пропало в v6) | v5 |
| 12 | C2: Явный учёт расходников в операционном цикле | v5 |
| 13 | F1: `TaskPart.version_suffix` (для хранения цифрового суффикса) | v4 |
| 14 | F2: Параметры времени резки в `MaterialType` (cut_speed, pierce_time, idle_speed, tolerance) | v6 — перенесено в DDL |
| 15 | J: Открытые вопросы (Q1–Q4) — не закрыты с v4, нужна фиксация решения | v4 |
| 16 | I: Таблица переиспользования из MVP (явная, с `is_variant` dedup) | v3/v4 |

---

## M. Сводка изменений Task Board v2 (v7.1)

| # | Что изменено | Примечание |
|---|---|---|
| 1 | TaskGroup entity | Заменяет batch_group_id (UUID). FK task_group_id в TaskItem и WorkerBucketEntry. |
| 2 | TaskGroupService | Заменяет BatchEngine. Авто/ручная группировка, split/merge, агрегация статуса. |
| 3 | Единый Task Board | 2 таба: "Производство" (иерархия) + "Моя корзина" (оператор). |
| 4 | ViewState | Сохранение раскрытия уровней Project/WorkItem/TaskGroup в БД. |
| 5 | ViewPreset | Комплексные фильтры + пресеты для таба "Производство". |
| 6 | TaskItemStatus.SUSPENDED | Длительная приостановка (бригадир/оператор). |
| 7 | Авто-qty_produced | qty_produced = sum(TaskPart.qty) * sheets_done. Оператор НЕ вводит вручную. |
| 8 | Связь TaskItem ↔ ProductionUnit | Прямой FK task_item_id. Обратный поиск по label_id. |
| 9 | Резервирование материалов | InventorySystem.create_reservation при назначении TaskGroup на узел. |
| 10 | Авто-списание при DONE | MaterialAudit(write_off) с приоритетом: reservation → FIFO. |
| 11 | Omnisearch v2 | + ProductionUnit.label_id + Part.sku + MaterialType.code. |
| 12 | Интеграция Part Library | Клик на деталь в TaskItem → модальное окно. Корзина + rework nests. |
| 13 | Интеграция Warehouse | Резервирование из Task Board. Новая вкладка "РЕЗЕРВЫ" в Warehouse. |
| 14 | Интеграция Chat | Тип HANDOVER, deeplink #<task_id>, канал "Производство". |
| 15 | Интеграция Incidents | Deeplink на TaskItem, фильтр по Project/WorkItem. |
| 16 | Интеграция Analytics | Метрики TaskGroup, node_utilization, pallet_by_project. |
| 17 | Интеграция Reports | Новые data blocks: task_group_summary, material_reservation, pallet_by_project. |
| 18 | Модальные окна | Project, WorkItem, TaskGroup, TaskItem, Pallet с полным просмотром/редактированием. |
| 19 | Превью неста | SVG-рендеринг раскладки деталей на листе в TaskItem Modal. |
| 20 | Новые виджеты | hierarchy_table, hierarchy_row, filter_panel, handover_form, handover_banner, nest_preview, order_cart_panel. |
