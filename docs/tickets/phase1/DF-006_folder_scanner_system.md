# DF-006: FolderScannerSystem (Polling Loop)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md), [DF-002](./DF-002_gnc_parser.md), [DF-003](./DF-003_folder_name_parser.md), [DF-004](./DF-004_task_file_parser.md), [DF-005](./DF-005_svg_generator.md) |
| **Блокирует** | [DF-007](./DF-007_ns_mirror_service.md), [DF-009](./DF-009_folder_scanner_view.md), [DF-010](../phase2/DF-010_work_item_system.md) |
| **Архитектура** | [02_application_architecture.md §4.4](../architecture/02_application_architecture.md) |
| **Data Flow** | [03_data_flow.md §2-3](../architecture/03_data_flow.md) |

---

## Контекст

Сканер — сердце системы приёма нарядев. Работает **только на мастер-узле**. Читает папки с сетевого диска, создаёт/обновляет WorkItem, TaskItem, PartLibrary. При изменении файлов — записывает WorkLog и рассылает broadcast через FileBus.

Особые кейсы:
- Папка без GNC файлов → `PENDING_CUTS` + уведомление
- GNC файл изменился (hash) → `FILE_CHANGED` WorkLog + broadcast оператору

---

## Execution Plan

```
1. Создать FolderScannerSettings (local + global fields)
2. Реализовать FolderScannerSystem.on_startup() — регистрация, start polling
3. Реализовать async polling loop (asyncio.create_task)
4. Реализовать scan_path() — итерация по одному scan_root
5. Реализовать upsert_work_item() — идемпотентное создание/обновление
6. Реализовать upsert_task_item() — с hash detection
7. Реализовать upsert_part_library() — из GncPartData
8. Тесты с mocked filesystem
```

---

## Подзадачи

### Settings
- [x] `FolderScannerSettings(BaseModuleSettings)`:
  - LOCAL: `sidra_scan_path`, `mihtav_scan_path`, `other_scan_path`, `poll_interval_seconds`, `local_ns_path`, `ns_mirror_interval_seconds`, `ns_mirror_copy_timeout_s`
  - GLOBAL: `enabled`, `default_project_name`
- [x] Регистрация в SDK: `registry.register("folder_scanner", FolderScannerSettings)`

### System Core
- [x] `FolderScannerSystem(BaseSystem)`:
  - `on_startup()` → проверить что это мастер → запустить poll loop
  - `on_shutdown()` → остановить poll loop
- [x] Async polling loop:
  - `while self._running: await asyncio.sleep(poll_interval)`
  - Цикл по `[sidra_path, mihtav_path, other_path]`
  - Только если `settings.enabled`

### Scan Logic
- [x] `scan_path(scan_root: Path, work_item_type: WorkItemType)`:
  - Итерация по `scan_root.iterdir()`
  - Для каждой папки: `parse_folder_name()` → `upsert_work_item()`
  - GNC файлы: `[f for f in folder.iterdir() if not is_variant(f) and f.suffix.upper() == ".GNC"]`
  - Если gnc_files == [] → `WorkItem(PENDING_CUTS)` + `emit_notification("scan.empty_folder")`
  - Иначе → `WorkItem(NEW or update)` + for gnc in gnc_files: process_gnc()

- [x] `upsert_work_item(folder: Path, meta: FolderMeta) -> WorkItem`:
  - Ключ идемпотентности: `folder.name` (unique)
  - Если существует → обновить `last_scanned_at`
  - Если нет → создать с `status=NEW` (или `PENDING_CUTS` если нет GNC)
  - `folder_path` = `to_relative_path(folder, scan_root)` (ТОЛЬКО ОТНОСИТЕЛЬНО!)

- [x] `process_gnc(gnc: Path, work_item: WorkItem, scan_root: Path)`:
  - `parse_task_filename(gnc.name)` → step_index, batch_index
  - `new_hash = md5(gnc)`
  - `task = upsert_task_item(...)` (file_path = relative!)
  - Если `task.file_hash != new_hash`: → `FILE_CHANGED` WorkLog + broadcast
  - `sheet = gnc_parser.parse(gnc)`
  - `upsert_mat_type(sheet.mat_code, sheet.*)`
  - `for part in sheet.parts: upsert_part_library(part)` + `upsert_task_part(part, task)`

- [x] `to_relative_path(abs_path: Path, scan_root: Path) -> str`:
  - `return str(abs_path.relative_to(scan_root))`

---

## Псевдокод

```python
class FolderScannerSystem(BaseSystem):
    """
    Сканирует сетевые папки на наличие новых нарядов (GNC файлов).
    Работает ТОЛЬКО на мастер-узле.
    
    Architecture:
      - Async polling loop: asyncio.sleep(poll_interval_seconds)
      - Идемпотентный: повторный scan одной папки не создаёт дубли
      - Все пути в БД — ОТНОСИТЕЛЬНЫЕ (scan_root-агностичные)
    """
    
    async def on_startup(self) -> None:
        if not self.sdk.coordination.is_master():
            return  # Только мастер сканирует!
        self._task = asyncio.create_task(self._poll_loop())
    
    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._scan_all()
            except Exception as e:
                logger.error(f"Scanner error: {e}")
            await asyncio.sleep(self.settings.poll_interval_seconds)
    
    async def _scan_all(self) -> None:
        paths = [
            (self.settings.sidra_scan_path, WorkItemType.SIDRA),
            (self.settings.mihtav_scan_path, WorkItemType.MIHTAV),
            (self.settings.other_scan_path, WorkItemType.REWORK),
        ]
        for path_str, wi_type in paths:
            if path_str:
                await self._scan_path(Path(path_str), wi_type)
    
    async def _scan_path(self, scan_root: Path, wi_type: WorkItemType) -> None:
        for folder in scan_root.iterdir():
            if not folder.is_dir():
                continue
            meta = parse_folder_name(folder.name)
            work_item = self._upsert_work_item(folder, meta, scan_root)
            
            gnc_files = [f for f in folder.iterdir()
                         if f.suffix.upper() == ".GNC" and not is_variant(f)]
            
            if not gnc_files:
                work_item.status = WorkItemStatus.PENDING_CUTS
                self._emit_notification("scan.empty_folder",
                                         folder_name=folder.name)
            else:
                for gnc in gnc_files:
                    self._process_gnc(gnc, work_item, scan_root)
    
    def _upsert_work_item(self, folder, meta, scan_root) -> WorkItem:
        with self.session() as s:
            wi = s.exec(select(WorkItem)
                        .where(WorkItem.folder_name == folder.name)).first()
            if wi:
                wi.last_scanned_at = datetime.now()
            else:
                wi = WorkItem(
                    folder_name=folder.name,
                    folder_path=str(folder.relative_to(scan_root)),
                    work_item_type=meta.work_item_type,
                    sidra_number=meta.sidra_number,
                    sidra_step=meta.sidra_step,
                    project_id=self._find_or_create_project(meta.project_hint),
                )
                s.add(wi)
            s.commit()
            return wi
```

---

## TDD: Тесты

```python
# tests/unit/features/test_folder_scanner.py
# Используем tmp_path + моки FileBus

async def test_scan_creates_work_item(tmp_path, mock_session):
    """Сканирование папки создаёт WorkItem."""
    sidra_folder = tmp_path / "SIDRA-353203-SHLAV-2-07.07.2025"
    sidra_folder.mkdir()
    (sidra_folder / "12-06-...-3.GNC").write_text("(GNC CONTENT)")
    
    scanner = FolderScannerSystem(...)
    await scanner._scan_path(tmp_path, WorkItemType.SIDRA)
    
    wi = mock_session.query(WorkItem).filter_by(folder_name=sidra_folder.name).first()
    assert wi is not None
    assert wi.status == WorkItemStatus.NEW

async def test_scan_pending_cuts_when_no_gnc(tmp_path, mock_session):
    """Папка без GNC → PENDING_CUTS."""
    folder = tmp_path / "SIDRA-999999-STEP-01.01.2025"
    folder.mkdir()
    # Нет GNC файлов!
    
    scanner = FolderScannerSystem(...)
    await scanner._scan_path(tmp_path, WorkItemType.SIDRA)
    
    wi = mock_session.query(WorkItem).first()
    assert wi.status == WorkItemStatus.PENDING_CUTS

async def test_file_changed_detected(tmp_path, mock_session, mock_filebus):
    """Изменение GNC хэша → WorkLog.FILE_CHANGED + broadcast."""
    gnc = tmp_path / "SIDRA-001" / "01-01-...-3.GNC"
    gnc.parent.mkdir()
    gnc.write_text("ORIGINAL CONTENT")
    
    # Первый скан
    await scanner._scan_path(tmp_path, WorkItemType.SIDRA)
    
    # GNC изменился
    gnc.write_text("CHANGED CONTENT")
    await scanner._scan_path(tmp_path, WorkItemType.SIDRA)
    
    logs = mock_session.query(WorkLog).filter_by(log_type=WorkLogType.FILE_CHANGED).all()
    assert len(logs) == 1
    mock_filebus.broadcast.assert_called_with("FILE_CHANGED_ALERT", ...)

def test_relative_path_stored(tmp_path):
    """file_path в TaskItem — ТОЛЬКО относительный, без буквы диска."""
    scan_root = tmp_path
    gnc_abs = tmp_path / "SIDRA-001" / "01-01-...-3.GNC"
    relative = str(gnc_abs.relative_to(scan_root))
    assert not relative.startswith("Z:")
    assert not relative.startswith("C:")
```

---

## Definition of Done (Gate 1 — частично)

```
✓ Polling loop запускается на мастере и НЕ запускается на slave
✓ Новая папка с GNC → WorkItem(NEW) в БД
✓ Папка без GNC → WorkItem(PENDING_CUTS) + emit_notification вызван
✓ Изменение хэша GNC → WorkLog(FILE_CHANGED) + FileBus broadcast
✓ folder_path и file_path — ВСЕГДА относительные (тест проверяет)
✓ Повторный скан НЕ создаёт дубли WorkItem (idempotent)
✓ Все тесты проходят с mocked filesystem
```
