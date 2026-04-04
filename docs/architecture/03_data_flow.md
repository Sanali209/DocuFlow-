# DocuFlow — Data Flow Document

> **Версия:** 1.0
> Описывает движение данных между источниками, системами и хранилищами.

---

## 1. Источники данных и их характеристики

| Источник | Тип | Направление | Протокол |
|---|---|---|---|
| Сетевой диск (Samba) | GNC файлы + папки | READ-только | SMB/CIFS через смонтированный диск |
| .env файл | Конфигурация | READ-только | Локальный файл |
| FileBus (сетевой диск) | REQ/RES/BROADCAST JSON | Двунаправленный | Файловый (polling) |
| SQLite БД (локальная) | Все данные | Чтение/Запись | SQLModel / SQLAlchemy |
| NiceGUI Frontend | Действия пользователя | Ввод | HTTP (localhost) |
| NS папка (локальный диск) | GNC копии для станка | Запись (зеркало) | Файловый (copy) |

---

## 2. Полный поток данных: от папки до TaskItem

```
[Samba Network Drive]
        │
        │ SMB mount → Z:\sidra\...
        ▼
[FolderScanner — master only]
  Polling loop (every 300s):
    folder.name ──► FolderNameParser
                          │
                    ┌─────┴──────┐
                    │  SIDRA     │  MIHTAV/REWORK
                    │  regex OK  │  fallback
                    └─────┬──────┘
                          │ FolderMeta{type, sidra_number, sidra_step}
                          ▼
                    WorkItem.upsert()
                    (key: folder_name — идемпотентно)
                          │
                          ▼
                    gnc_files = folder/*.GNC (is_variant filter)
                          │
              ┌───────────┼───────────┐
              │           │           │
           gnc_1       gnc_2       gnc_N
              │
              ▼
          GncParser.parse(gnc_file)
            ├─ *SHEET  → sheet_x, sheet_y, thickness, sheet_qty
            ├─ Material → MaterialType.code
            ├─ DATE     → gnc_date
            ├─ PART NAME:SKU-VER → extract_sku()
            │               sku="3433-11-004-G", version="1"
            └─ CONTOUR / G-code → SVGGenerator.calculate_bounds()
                                        └─► bbox_x, bbox_y (мм)
                                            svg_preview.svg

          GncParser.estimate_time(mat_type)
            ├─ pierce_time × contour_count
            ├─ cut_length / mat_type.cut_speed_mm_per_min
            ├─ idle_length / mat_type.idle_speed_mm_per_min
            └─ × (1 + mat_type.time_tolerance_pct / 100)
                    └─► estimated_minutes

        TaskItem.upsert()
          ├─ file_path (RELATIVE от scan_root!)
          ├─ file_hash = md5(gnc_file)
          ├─ sheet_x, sheet_y, thickness, sheet_qty
          ├─ estimated_minutes
          └─ assigned_to_node (если уже был в WorkerBucket)

        TaskPart.upsert() per PART NAME
          └─ part_sku → PartLibrary.upsert()
               ├─ bbox_x, bbox_y (из SVGGenerator)
               ├─ contour_count, hole_count, corner_count
               └─ svg_preview_path

[SQLite DB — локальная на мастере]
  → через FileBus Snapshot → синхронизируется на slave-узлы
```

---

## 3. Поток: Hash Changed Detection

```
[FolderScanner — повторный poll]
      │
      ▼
  gnc_file → md5(gnc_file) = hash_new
      │
      ├─ hash_new == task_item.file_hash?
      │       YES → ничего
      │
      └─ NO:
           task_item.file_hash = hash_new
           WorkLog(FILE_CHANGED,
                   payload={old: hash_old, new: hash_new})
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
```

---

## 4. Поток: NSMirrorService

```
[WorkerBucketEntry добавлена на узле LASER_1]
      │
      ▼
NSMirrorService (background, LASER_1, каждые 60s):
  for entry in bucket[LASER_1]:
    network_file = Z:\sidra\SIDRA-353203-...\12-06-...-3.GNC
    local_file   = C:\NS\cutting\12-06-...-3.GNC

    CASE: local_file не существует
      copy(network → local, timeout=30s)
      WorkLog(NS_MIRROR, "Скопирован в NS")

    CASE: md5(network) ≠ md5(local)
      WorkLog(FILE_CHANGED, "Сетевой файл изменился!")
      ui.notify(оператор LASER_1, "Файл обновился. Обновить?")
      IF operator: Обновить → copy(network → local)
      IF operator: Пропустить → WorkLog(NS_MIRROR, "Пропущено")

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
      ├─ IF work_item.status == PENDING_CUTS:
      │      work_item.status = REGISTERED (уже есть папка и GNC)
      │      work_item.doc_received_at = now
      │
      ├─ IF work_item НЕ существует (папки нет):
      │      WorkItem.create(status=DOC_NO_FOLDER)
      │      ChatMessage(type=WARNING,
      │                  "Бумага получена, папки нет на диске")
      │
      └─ WorkLog(STATUS_CHANGE, "Документ зарегистрирован бригадиром")

[SQLite] → sync → [все узлы через Snapshot]
```

---

## 6. Поток: Создание и выполнение батча

```
[Бригадир — task_board/view.py]
      │
      ├─ BatchEngine.compute(tasks[], BatchRule) → batches[]
      │      GROUP BY: mat_type_id + thickness + sheet_x + sheet_y
      │      per batch: batch_group_id = uuid4()
      │
      ├─ Мнение системы:
      │      PartLibrary → check is_stock → STOCK_ALERT если деталь в запасе
      │      → WorkLog(STOCK_ALERT) + ChatMessage(WARNING)
      │
      ├─ Бригадир вручную перетаскивает таски между батчами
      │
      └─ Бригадир блокирует таск: TaskItem.block_reason = "text"
                                  TaskItem.status = BLOCKED

[Оператор — WorkerBucket]
  резервирует батч:
      │
      ├─ FileBus.REQ(lock_batch, {batch_group_id, node_id})
      ├─ Мастер: WorkerBucketEntry.create() per task in batch
      └─ TaskItem.status = IN_PROGRESS
                 TaskItem.started_at = now

[Оператор — обновляет прогресс]
  sheets_done++ → TaskItem.sheets_done
  on_hold: pause_reason → WorkLog(ON_HOLD)
  done:    qty_produced → TaskItem.qty_produced
           TaskItem.status = DONE
           TaskItem.completed_at = now
           MaterialAudit(write_off, qty=sheets_done)
```

---

## 7. Поток: Создание ProductionUnit

```
[Оператор — task_board/view.py]
  TaskItem.done → диалог "Куда кладём?"
      │
      ├─ Новая паллета:
      │      label_id = generate_human_id(node_code, year, month, seq)
      │            → "25-07-А-042"
      │      ProductionUnit.create(label_id, task_item_id, qty)
      │      Оператор выбирает / создаёт StorageLocation
      │
      └─ К существующей паллете:
             UI: live search по label_id (partial match)
             → "07-А" → ["25-07-А-001", "25-07-А-002", ...]
             ProductionUnit.qty_produced += qty_new

[StorageLocation обновлена] → [поиск сразу доступен]

SPLIT паллеты:
  ProductionUnit(old, qty=20)
    split(qty_to_stock=10) →
      unit_stock:  label_id=new_A, qty=10, is_stock=True
      unit_active: label_id=new_B, qty=10, is_stock=False
      old: archived, parent_label_id=old

ПОИСК:
  по label_id    → ProductionUnit
  по SKU         → TaskPart → TaskItem → ProductionUnit
  по work_item   → TaskItem[] → ProductionUnit[]
  по материалу   → MaterialType → TaskItem[] → ProductionUnit[]
  по location    → StorageLocation → ProductionUnit[]
```

---

## 8. Поток: Аудит материалов

```
[Событие: поступление материала]
  Кладовщик → MaterialStock.create(mat_type, qty, batch_code)
  MaterialAudit(income, qty_delta=+N, author)

[Событие: резервирование под наряд]
  Бригадир → Reservation.create(stock_item, work_item, soft)
  MaterialStock.status = RESERVED

[Событие: списание при завершении TaskItem]
  TaskItem(DONE) →
    MaterialAudit(write_off, qty_delta=-sheets_done,
                  ref_task_item_id, author="system")
  IF reservation exists: Reservation.remove()

[Событие: дозаказ]
  Бригадир → ChatMessage(type=ORDER, "Нужен AA 5052-H32 3mm")
  MaterialAudit(reorder, note="ChatMessage #{id}")

[Событие: брак/коррекция]
  MaterialAudit(defect/correction, reason)
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

## 10. Поток: Генерация отчёта

```
[Начальник — reports/view.py]
  1. Выбирает ReportTemplate
  2. Вводит параметры: date_from, date_to, node_id
  3. Нажимает "Создать"
      │
      ▼
ReportSystem.generate(template, params):
  context = {
    blocks: BlockProxy(ReportRegistry, params),
    params
  }
  html = jinja2_env.render(template.template_html, context)
      │
  При рендере Jinja2:
    {{ blocks.work_items_summary(date_from=...) }}
      → WorkItemSystem.report_block_summary(params)
        → SELECT ... FROM workitem WHERE ...
        → returns [{folder_name, status, ...}, ...]

    {{ blocks.material_usage(date_from=...) }}
      → MaterialSystem.report_block_usage(params)
        → ...

  pdf = weasyprint.HTML(string=html).write_pdf()
  ui.download(pdf, filename="report_2025-07.pdf")
```
