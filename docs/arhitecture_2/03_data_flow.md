# DocuFlow — Data Flow Document

> **Версия:** 2.1 (Task Board v2 — на основе Master Plan v7)
> **Спецификация:** [Task Board v2 Design](../superpowers/specs/2026-04-28-task-board-v2-design.md)
> Описывает движение данных между источниками, системами и хранилищами.

---

## 1. Источники данных и их характеристики

| Источник | Тип | Направление | Протокол |
|---|---|---|---|
| Сетевой диск (Samba) | GNC файлы + папки | READ-только | SMB/CIFS через смонтированный диск |
| .env файл | Конфигурация (local) | READ-только | Локальный файл |
| FileBus (сетевой диск) | REQ/RES/BROADCAST JSON | Двунаправленный | Файловый (polling) |
| SQLite БД (локальная) | Все данные | Чтение/Запись | SQLModel / SQLAlchemy |
| NiceGUI Frontend | Действия пользователя | Ввод | HTTP (localhost) |
| NS папка (локальный диск) | GNC копии для станка | Запись (зеркало) | Файловый (copy, atomic) |
| filelock (.docuflow.lock) | Блокировка сканирования | Эксклюзивный доступ | Файловый |

---

## 2. Полный поток данных: от папки до TaskItem

```
[Samba Network Drive]
        │
        │ SMB mount → Z:\sidra\...
        ▼
[FolderScanner — master only]
  filelock(.docuflow.lock, timeout=5s)  ← защита от параллельного сканирования
  Polling loop (every 300s):
    folder.name ──► FolderNameParser
                          │
                    ┌─────┴──────┐
                    │  SIDRA     │  MIHTAV/REWORK (fallback)
                    │  regex OK  │  project="Default"
                    └─────┬──────┘
                          │ FolderMeta{type, sidra_number, sidra_step}
                          ▼
                    WorkItem.upsert()
                    (key: folder_name — идемпотентно)
                          │
                    IF gnc_files == []:
                      → WorkItem(PENDING_CUTS)
                      → notify(template="scan.empty_folder")
                      → ЖДЁМ следующего poll
                    │
                    ELSE:
                    gnc_files = folder/*.GNC (is_variant filter)
                          │
              ┌───────────┼───────────┐
              │           │           │
           gnc_1       gnc_2       gnc_N
              │
              ▼
          GncParser.parse(gnc_file)
            ├─ *SHEET  → sheet_x, sheet_y, thickness, sheet_qty
            ├─ Material → MaterialType.code (upsert)
            ├─ DATE     → gnc_date
            ├─ PART NAME:SKU-VER-SUFFIX → extract_sku()
            │    "3433-11-004-G-1" → sku="3433-11-004-G",
            │                        version_letter="G",
            │                        version_suffix="1"
            └─ CONTOUR / G-code → SVGGenerator.generate_thumbnail()
                                        └─► bbox_x, bbox_y (мм) ← НЕ PART SIZE!
                                            svg_preview.svg

          GncParser.estimate_time(mat_type)
            ├─ pierce = contour_count × pierce_time_sec
            ├─ cut    = cut_length_mm / cut_speed_mm_per_min × 60
            ├─ idle   = idle_length_mm / idle_speed_mm_per_min × 60
            └─ estimate = (pierce+cut+idle) × sheet_qty / 60 × (1 + tolerance%)
                    └─► estimated_minutes

        TaskItem.upsert()   ← идемпотентно по file_path (RELATIVE от scan_root!)
          ├─ file_hash = md5(gnc_file)
          ├─ sheet_x, sheet_y, thickness, sheet_qty
          ├─ estimated_minutes
          ├─ task_group_id = NULL (на момент сканирования)
          └─ IF hash изменился → check_file_changes()

        TaskPart.upsert() per PART NAME
          ├─ part_sku = "3433-11-004-G"   → PartLibrary.upsert()
          ├─ version  = "G"
          └─ version_suffix = "1"  (сохраняется, назначение TBD)

        PartLibrary.upsert():
          ├─ bbox_x = data_w  (из SVGGenerator, НЕ из PART SIZE!)
          ├─ bbox_y = data_h
          ├─ contour_count, hole_count, corner_count
          └─ svg_preview_path

        TaskGroupService.auto_group_by_material(work_item_id)
          ├─ GROUP BY: mat_type_id + thickness
          ├─ CREATE TaskGroup(name="ST37-2 4.0mm", work_item_id=..., grouping_rule='auto_material')
          └─ UPDATE TaskItem.task_group_id = TaskGroup.id

[SQLite DB — локальная на мастере]
  → через FileBus Snapshot → синхронизируется на slave-узлы
```

---

## 3. Поток: Hash Changed Detection + Atomic Write

```
[FolderScanner — повторный poll]
      │
      ▼
  gnc_file → compute_hash(gnc_file) = hash_new
      │
      ├─ hash_new == task_item.file_hash?
      │       YES → ничего (идемпотентно)
      │
      └─ NO:
           old_hash = task_item.file_hash
           task_item.file_hash = hash_new
           WorkLog(FILE_CHANGED,
                   payload={"old": old_hash, "new": hash_new})
                │
                ▼
           FileBus.broadcast(FILE_CHANGED_ALERT, {
               task_item_id: ...,
               file_name: ...
           })
                │
                ▼
           [Все узлы] → NiceGUI ui.notify() оператора
           [NSMirrorService] → сравнивает local/network
                               → UI диалог: "Обновить NS?"

# Атомарная запись при обновлении любого файла:
def atomic_write(path: str, data: bytes):
    tmp = Path(path + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)   # атомарная замена
```

---

## 4. Поток: NSMirrorService

```
[WorkerBucketEntry добавлена на узле LASER_1]
      │
      ▼
NSMirrorService (background, LASER_1, каждые 60s):
  for entry in bucket[LASER_1]:
    network_file = resolve_path(entry.task_item.file_path, scan_root)
    # file_path — RELATIVE от scan_root, восстанавливаем через local env
    local_file   = C:\NS\cutting\{entry.task_item.file_name}

    CASE: local_file не существует
      copy(network → local, timeout=30s)  ← timeout защищает от зависания
      WorkLog(NS_MIRROR, "Скопирован в NS: {file_name}")

    CASE: md5(network) ≠ md5(local)
      WorkLog(FILE_CHANGED, "Сетевой файл изменился!")
      ui.notify(оператор LASER_1, диалог):
        "Файл {name} обновился. Обновить NS-копию?"
        [Обновить]         → copy(network → local, timeout=30s)
                             WorkLog(NS_MIRROR, "NS обновлён")
        [Оставить старый]  → WorkLog(NS_MIRROR, "Оставлен старый")
        [Напомнить позже]  → пропустить до следующего poll

  CASE: task_item removed from bucket:
    delete(local_file)
    WorkLog(NS_MIRROR, "Удалён из NS: {file_name}")
```

---

## 5. Поток: Регистрация бумажного документа

```
[Бригадир — NiceGUI UI]
  нажимает "Подтвердить получение наряда"
      │
      ▼
WorkItemSystem.register_document(work_item_id, user)
      │
      ├─ IF work_item.status IN [NEW, PENDING_CUTS, FOLDER_NO_DOC]:
      │      work_item.status = REGISTERED
      │      work_item.doc_received_at = now
      │      WorkLog(STATUS_CHANGE, "Документ зарегистрирован бригадиром")
      │
      └─ IF work_item НЕ существует (папки нет на диске):
             WorkItem.create(status=DOC_NO_FOLDER,
                             folder_name=input, doc_received_at=now)
             ChatMessage(type=WARNING,
                         "Бумага получена, папки нет на диске")
             WorkLog(STATUS_CHANGE, "Создан DOC_NO_FOLDER")

[SQLite] → sync → [все узлы через Snapshot]

ИНЦИДЕНТ "нет бумажных чертежей":
  ChatMessage(type=INCIDENT, content="...", attachments=[path/to/photo.jpg])
  IncidentLog(incident_type="other", description="...", reported_by=user)
```

---

## 6. Поток: Создание и выполнение TaskGroup

```
[Бригадир — task_board/view.py, таб "Производство"]
      │
      ├─ TaskGroupService.auto_group_by_material(work_item_id) → TaskGroup[]
      │      DEFAULT: GROUP BY: mat_type_id + thickness
      │      grouping_rule = 'auto_material'
      │      UPDATE TaskItem.task_group_id = TaskGroup.id
      │
      ├─ STOCK_ALERT проверка:
      │      FOR each task IN group:
      │        FOR each part IN task.task_parts:
      │          IF ProductionUnit(is_stock=True, part_sku=part.sku) EXISTS:
      │            WorkLog(STOCK_ALERT, "Деталь {sku} есть в запасе!")
      │            ChatMessage(type=WARNING, ref=task_item)
      │            TaskItem.status = BLOCKED, block_reason = "Деталь в запасе"
      │
      ├─ РУЧНАЯ БЛОКИРОВКА:
      │      TaskItem.status = BLOCKED
      │      TaskItem.block_reason = "Ждём новый раскрой" / "Нет материала" / ...
      │
      ├─ Бригадир редактирует группы: разбить, объединить, переместить задачу
      │
      └─ Назначение на узел + резервирование материала:
           InventorySystem.create_reservation(
               stock_item_id=selected_stock_id,
               work_item_id=work_item_id,
               qty=estimated_sheets, is_hard=False
           )

[Оператор — WorkerBucket, таб "Моя корзина"]
  резервирует TaskGroup (lock_taskgroup):
      │
      ├─ FileBus.REQ(lock_taskgroup, {task_group_id, node_id=LASER_1})
      ├─ Мастер:
      │    WorkerBucketEntry.create() per task in group
      │    NSMirrorService → запускает копирование GNC в NS
      └─ TaskItem.status = IN_PROGRESS, started_at = now

[Оператор — обновляет прогресс]
  sheets_done++ → TaskItem.sheets_done (UI: прогресс-бар "5 из 8 листов")
  on_hold: pause_reason (обязательно) → WorkLog(ON_HOLD)
  suspended: причина → WorkLog(ON_HOLD) + TaskItem.status = SUSPENDED
  done:
     ├─ Авто-расчёт: qty_produced = sum(TaskPart.qty) * sheets_done
     ├─ Диалог "Куда кладём?":
     │    Новая паллета: ProductionUnit(label_id=..., task_item_id=task.id, qty=qty_produced)
     │    К существующей: ProductionUnit.qty_produced += qty_produced
     ├─ TaskItem.status = DONE, completed_at = now
     ├─ actual_minutes = (completed_at - started_at) - Σ(on_hold durations)
     ├─ drift_pct = (actual - estimated) / estimated * 100
     ├─ MaterialAudit(write_off, qty=sheets_done, ref=task_item)
     │    Приоритет: reservation → FIFO fallback
     └─ ConsumableLog(use, ref=task_item)  ← если списаны расходники
```

---

## 7. Поток: Создание ProductionUnit (завершение TaskItem)

```
[Оператор — task_board/view.py, TaskItem Modal]
  TaskItem.done → диалог "Завершить задачу"
      │
      ├─ Авто-расчёт qty_produced:
      │    qty_produced = sum(TaskPart.qty for part in task.parts) * sheets_done
      │    fallback: если parts пустой → qty_produced = sheets_done
      │
      ├─ Новая паллета:
      │      label_id = generate_human_id():
      │        year     = str(now.year)[-2:]   # "26"
      │        month    = f"{now.month:02d}"   # "04"
      │        node     = workplace.code        # "LASER_1"
      │        seq      = next_seq(node, month) # "0015"
      │        → "26-04-LASER_1-0015"
      │      ProductionUnit.create(
      │          label_id, task_item_id=task.id,
      │          qty_produced=auto_calculated, is_stock=False
      │      )
      │      Оператор выбирает / создаёт StorageLocation
      │
      └─ К существующей паллете (live search ≥2 символа):
             UI: "LASER_1-001" → ["26-04-LASER_1-0015", ...]
             existing_pallet.qty_produced += auto_calculated_qty
             WorkLog: "Added to pallet X: +N units from task Y"

ДО-СИСТЕМНЫЕ ПАЛЛЕТЫ:
  Кладовщик/Бригадир → ProductionUnit.create(
      label_id=manual_input,
      task_item_id=NULL,    ← без TaskItem
      is_pre_system=True
  )

SPLIT паллеты:
  split(unit, qty_to_stock=10):
    unit_stock  = ProductionUnit(qty=10, is_stock=True, parent_label_id=old.label_id)
    unit_active = ProductionUnit(qty=remaining, is_stock=False, parent_label_id=old.label_id)
    old: archived

MERGE паллет:
  merge(unit_a, unit_b):
    new_unit = ProductionUnit(qty=a.qty+b.qty, label_id=generate_human_id())
    unit_a: archived; unit_b: archived

ПОИСК паллеты:
  по label_id (partial, live search)  → ProductionUnit
  по SKU детали → TaskPart → TaskItem → ProductionUnit[]
  по task_item_id (прямая связь) → ProductionUnit[]
  по work_item  → TaskItem[] → ProductionUnit[]
  по project    → WorkItem[] → TaskItem[] → ProductionUnit[]
  по материалу  → MaterialType → TaskItem[] → ProductionUnit[]
  по location   → StorageLocation → ProductionUnit[]
  ОБРАТНЫЙ: label_id → ProductionUnit → TaskItem (через FK)
```

---

## 8. Поток: Аудит материалов

```
[Событие: поступление материала]
  Кладовщик → MaterialStock.create(mat_type, qty, batch_code, location)
  MaterialAudit(income, qty_delta=+N, author, node_id)

[Событие: резервирование под наряд]
  Бригадир → Reservation.create(stock_item, work_item, type=soft)
  MaterialStock.status = RESERVED

[Событие: списание при завершении TaskItem]
  TaskItem(DONE) →
    MaterialAudit(write_off, qty_delta=-sheets_done,
                  ref_task_item_id, author="system", node_id)
  IF reservation exists: Reservation.remove()
  MaterialStock.quantity -= sheets_done

[Событие: дозаказ]
  Бригадир → ChatMessage(type=ORDER, "Нужен AA 5052-H32 3mm")
  MaterialAudit(reorder, note="ref:ChatMessage #{id}")

[Событие: брак/коррекция]
  MaterialAudit(defect/correction, qty_delta, reason)

[Расходники]
  ConsumableLog(use, qty_delta=-N, ref_task_item_id)
  IF consumable.quantity <= consumable.min_quantity:
    ChatMessage(type=WARNING, "Расходник '{name}' заканчивается!")
```

---

## 9. Поток: Синхронизация между узлами

```
[MASTER node]
  SQLite (master) ──► Snapshot JSON ──► Samba FileBus folder
                                               │
                                               ▼
                                    [SLAVE nodes — polling]
                                    При обнаружении нового snapshot:
                                      apply_delta(snapshot)
                                      SQLite (slave) обновлена

[REQ/RES команды (FileBus)]
  SLAVE: REQ_{slave}_{master}_{id}.json
  MASTER: обрабатывает → RES_{master}_{slave}_{id}.json
  Команды: lock_batch, unlock_batch, file_changed, ns_mirror_alert

[BROADCAST]
  BROADCAST_{from}_{id}.json
  Все узлы читают + удаляют после обработки
```

---

## 10. Поток: Поиск деталей (прямой и обратный)

```
ПРЯМОЙ: "Есть ли деталь 3433-11-004-G в наряде SIDRA-353203?"
  PartLibrary.sku → TaskPart → TaskItem → WorkItem (WHERE folder_name=...)
  Результат: TaskItem.status, sheets_done, qty_produced

ОБРАТНЫЙ: "Где ещё встречается деталь 3433-11-004-G?"
  PartLibrary.sku → TaskPart[] → TaskItem[] → WorkItem[] → Project[]
  + ProductionUnit[] → StorageLocation[]
  Результат: все наряды и паллеты с этой деталью

ПОИСК по геометрии (когда SKU неизвестен):
  PartLibrarySystem.find_by_bbox(
      x=100.0, y=200.0,
      tolerance_pct=5.0,   # ±5%
      mat_type_id=None,
      hole_count=None,
      corner_count_min=None
  ) → PartLibrary[]

ПОИСК паллеты (без QR):
  live search ≥2 символа по label_id (partial match)
  "07-А" → ["25-07-А-001", "25-07-А-002", ...]
```

---

## 11. Поток: ViewState и ViewPreset

```
[Пользователь — task_board/view.py, таб "Производство"]
  Клик на ▼/▶ раскрытия уровня:
      │
      ▼
  ViewStateSystem.save_expansion_state(
      user_id=current_user.id,
      view_name='task_board_production',
      states={
          ('project', 'SHLAV-2'): True,
          ('workitem', '3455-11-144'): True,
          ('taskgroup', 'ST37-2 4.0mm'): True,
      }
  )
  → SQLite (viewstate table)

  При возвращении на вкладку:
  ViewStateSystem.load_expansion_state(user_id, 'task_board_production')
  → восстанавливает раскрытие иерархии

[Пользователь — FilterPanel]
  Применяет фильтры → [Сохранить пресет]
      │
      ▼
  ViewPresetSystem.save_preset(
      user_id=current_user.id,
      name="Мои срочные",
      view_name="task_board_production",
      filters={status: ['IN_PROGRESS'], urgent: True, node: 'LASER_1'}
  )
  → SQLite (viewpreset table)

  Быстрый выбор пресета из dropdown → применяет фильтры
```

---

## 12. Поток: Генерация отчёта

```
[Начальник — reports/view.py]
  1. Выбирает ReportTemplate (встроенный или пользовательский)
  2. Вводит параметры: date_from, date_to, node_id, ...
  3. Нажимает "Создать отчёт"
      │
      ▼
ReportSystem.generate(template, params):
  context = {
    blocks: BlockProxy(ReportRegistry, params),
    params
  }
  html = jinja2_env.render(template.template_html, context)
      │
  При рендере Jinja2 (примеры блоков):
    {{ blocks.work_items_summary(date_from=..., date_to=...) }}
      → WorkItemSystem.report_work_items_summary(params)
        → SELECT ... FROM workitem WHERE ...

    {{ blocks.task_group_summary(date_from=..., date_to=...) }}
      → TaskBoardSystem.report_task_group_summary(params)
        → SELECT ... FROM taskgroup JOIN taskitem ...

    {{ blocks.shift_completion(node_id=...) }}
      → TaskBoardSystem.report_shift_completion(params)

    {{ blocks.material_reservation_status() }}
      → InventorySystem.report_reservation_status(params)

    {{ blocks.pallet_by_project() }}
      → ProductionSystem.report_pallets_by_project(params)

    {{ blocks.downtime_summary(date_from=...) }}
      → IncidentSystem.report_downtime_summary(params)

  pdf = weasyprint.HTML(string=html).write_pdf()
  ui.download(pdf, filename=f"report_{params.date_from}.pdf")

Встроенные шаблоны:
  "Отчёт по смене"     → shift_completion + incident_log
  "Ход наряда"         → work_item_detail + tasks_by_node + task_group_summary
  "Движение материала" → material_usage + stock_snapshot + material_reservation_status
  "Инциденты"          → incident_log + downtime_summary
  "План vs Факт"       → shift_completion + estimated vs actual drift
  "Паллеты по проектам"→ pallet_by_project
```
