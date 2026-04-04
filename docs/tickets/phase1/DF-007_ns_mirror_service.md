# DF-007: NSMirrorService

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md), [DF-006](./DF-006_folder_scanner_system.md) |
| **Блокирует** | [DF-009](./DF-009_folder_scanner_view.md) |
| **Data Flow** | [03_data_flow.md §4](../architecture/03_data_flow.md) |

---

## Контекст

Оператор режет **с локального диска** (`NS` папка автоматики станка), а не с сетевого диска напрямую. Это ограничение автоматики. Система должна:
1. При добавлении TaskItem в WorkerBucket → скопировать GNC в NS папку
2. Периодически проверять: сетевой файл != локальный → предупредить оператора
3. При удалении из Bucket → удалить из NS

Работает на **всех узлах** (не только мастер).

---

## Подзадачи

- [x] `NSMirrorService(BaseSystem)`:
  - [x] `on_startup()` → запустить background loop
  - [x] `check_interval = settings.ns_mirror_interval_seconds` (default 60s)
  - [x] `copy_timeout = settings.ns_mirror_copy_timeout_s` (default 30s)
- [x] `_mirror_loop()`:
  - [x] Для каждого `WorkerBucketEntry` на `this_node`:
    - [x] Определить `network_file` и `local_file`
    - [x] Если нет локального → copy с timeout
    - [x] Если MD5 отличается → WorkLog(FILE_CHANGED) + alert оператору
- [x] `_copy_with_timeout(src, dst, timeout)` → используем `asyncio.wait_for`
- [x] Хуки на WorkerBucket (через event или observable):
  - [x] `on_bucket_add(entry)` → немедленно скопировать GNC
  - [x] `on_bucket_remove(entry)` → удалить из NS
- [x] Compute scan_root корректно для данного узла (из local settings)
- [x] Alert оператору через NiceGUI `ui.notify()` или диалог (реализовано через WorkLog)

---

## Псевдокод

```python
class NSMirrorService(BaseSystem):
    """
    Зеркалирует GNC файлы из сети в локальную NS папку автоматики.
    Работает на ВСЕХ узлах (не только мастере).
    
    Architecture:
      - check_interval: настраивается (default 60s)
      - Timeout на copy: защита от зависания при медленном диске (default 30s)
      - При изменении файла: НЕ перезаписывает автоматически — спрашивает оператора
    """
    
    async def _mirror_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.settings.ns_mirror_interval_seconds)
            await self._check_all_bucket_entries()
    
    async def _check_all_bucket_entries(self) -> None:
        entries = self._get_bucket_for_this_node()
        for entry in entries:
            await self._mirror_entry(entry)
    
    async def _mirror_entry(self, entry: WorkerBucketEntry) -> None:
        task = entry.task_item
        network_file = self._resolve_network_path(task.file_path)
        local_file   = Path(self.settings.local_ns_path) / task.file_name
        
        if not local_file.exists():
            await self._copy_with_timeout(network_file, local_file)
            self._log(task, WorkLogType.NS_MIRROR,
                      f"Скопирован в NS: {task.file_name}")
        else:
            network_md5 = md5(network_file)
            local_md5   = md5(local_file)
            if network_md5 != local_md5:
                self._log(task, WorkLogType.FILE_CHANGED,
                          f"⚠️ {task.file_name}: сетевой ≠ локальный!")
                await self._alert_operator(task,
                    message="Файл обновился на сети. Обновить NS-копию?",
                    on_confirm=lambda: self._copy_with_timeout(network_file, local_file)
                )
    
    async def _copy_with_timeout(self, src: Path, dst: Path) -> None:
        async def _do_copy():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        
        await asyncio.wait_for(_do_copy(), timeout=self.settings.ns_mirror_copy_timeout_s)
    
    def _resolve_network_path(self, relative_path: str) -> Path:
        """Восстанавливает абсолютный путь из relative + local scan_root."""
        scan_root = self.settings.sidra_scan_path  # local env!
        return Path(scan_root) / relative_path
    
    async def on_bucket_add(self, entry: WorkerBucketEntry) -> None:
        """Немедленно скопировать при добавлении в bucket."""
        await self._mirror_entry(entry)
    
    async def on_bucket_remove(self, entry: WorkerBucketEntry) -> None:
        """Удалить из NS при завершении/удалении из bucket."""
        local_file = Path(self.settings.local_ns_path) / entry.task_item.file_name
        if local_file.exists():
            local_file.unlink()
            self._log(entry.task_item, WorkLogType.NS_MIRROR,
                      f"Удалён из NS: {entry.task_item.file_name}")
```

---

## TDD: Тесты

```python
async def test_copies_on_bucket_add(tmp_path):
    network_dir = tmp_path / "network"
    ns_dir      = tmp_path / "ns"
    network_dir.mkdir(); ns_dir.mkdir()
    gnc = network_dir / "test.GNC"
    gnc.write_text("GNC CONTENT")
    
    service = NSMirrorService(local_ns_path=str(ns_dir), ...)
    entry = make_bucket_entry(file_path="test.GNC", file_name="test.GNC")
    await service.on_bucket_add(entry)
    
    assert (ns_dir / "test.GNC").exists()
    assert (ns_dir / "test.GNC").read_text() == "GNC CONTENT"

async def test_alerts_on_file_changed(tmp_path, mock_alert):
    network_gnc = tmp_path / "network" / "test.GNC"
    ns_gnc      = tmp_path / "ns" / "test.GNC"
    network_gnc.parent.mkdir(); ns_gnc.parent.mkdir()
    network_gnc.write_text("NEW CONTENT")
    ns_gnc.write_text("OLD CONTENT")
    
    service = NSMirrorService(...)
    entry = make_bucket_entry(file_name="test.GNC")
    await service._mirror_entry(entry)
    
    mock_alert.assert_called_once()
    assert "обновился" in mock_alert.call_args.kwargs["message"].lower()

async def test_deletes_on_bucket_remove(tmp_path):
    ns_dir = tmp_path / "ns"
    ns_dir.mkdir()
    ns_gnc = ns_dir / "test.GNC"
    ns_gnc.write_text("CONTENT")
    
    service = NSMirrorService(local_ns_path=str(ns_dir), ...)
    entry = make_bucket_entry(file_name="test.GNC")
    await service.on_bucket_remove(entry)
    
    assert not ns_gnc.exists()

async def test_copy_timeout_protection(tmp_path):
    """Зависший диск не должен блокировать систему навечно."""
    async def slow_copy():
        await asyncio.sleep(1000)  # имитация зависшего диска
    service = NSMirrorService(ns_mirror_copy_timeout_s=0.1, ...)
    # Должен завершиться без зависания (asyncio.TimeoutError → log, не crash)
```

---

## Definition of Done

```
✓ При добавлении в WorkerBucket → GNC файл появляется в NS папке
✓ MD5 мониторинг работает (интервал 60s)
✓ Изменение файла → alert оператору (UI notify)
✓ Удаление из Bucket → GNC удаляется из NS
✓ Copy timeout защищает от зависания
✓ Работает на slave-узлах (не только мастер)
✓ Все тесты проходят
```
