# DF-013: TaskBoardSystem (WorkerBucket + Статусы + Трекинг)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 2 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-010](./DF-010_work_item_system.md), [DF-012](./DF-011_012_work_items_view_and_batch_engine.md) |
| **Блокирует** | [DF-014](./DF-014_task_board_view.md), [DF-025](../phase4/DF-025_production_system.md) |
| **Data Flow** | [03_data_flow.md §6](../architecture/03_data_flow.md) |

---

## Контекст

TaskBoardSystem — это операционное сердце для оператора. Управляет:
1. **WorkerBucket** — корзина активных задач оператора (синхронизируется через FileBus lock_batch)
2. **Статусы TaskItem** — с проверкой допустимых переходов и WorkLog
3. **Трекинг прогресса** — sheets_done, actual_minutes, drift%
4. **Передача смены** — handover с заметками

---

## Подзадачи

### WorkerBucket
- [ ] `lock_batch(batch_group_id, node_id, user)`:
  - FileBus REQ к мастеру: `lock_batch`
  - Мастер: создать WorkerBucketEntry per TaskItem in batch
  - TaskItem.status → PLANNED, assigned_to_node = node_id
  - NSMirrorService hook: `on_bucket_add(entry)`
- [ ] `unlock_batch(batch_group_id, node_id)`:
  - Удалить WorkerBucketEntry
  - TaskItem.status → NEW (если не начат)
  - NSMirrorService hook: `on_bucket_remove(entry)`
- [ ] `get_bucket(node_id) -> list[WorkerBucketEntry]`
- [ ] `handover(node_id, to_user, note)`:
  - Обновить `handover_note`, `handover_from`, `handover_at`
  - ChatMessage(type=HANDOVER, content=note)

### TaskItem Lifecycle
- [ ] `start_task(task_id)`:
  - TaskItem.status → IN_PROGRESS
  - `started_at = now()`
  - WorkLog(STATUS_CHANGE, ...)
- [ ] `pause_task(task_id, reason)`:
  - TaskItem.status → ON_HOLD
  - WorkLog(ON_HOLD, reason=reason)
  - `pause_note = reason`
- [ ] `resume_task(task_id)`:
  - TaskItem.status → IN_PROGRESS
  - Вычесть паузу из actual_minutes
- [ ] `block_task(task_id, reason)`:
  - TaskItem.status → BLOCKED
  - TaskItem.block_reason = reason
- [ ] `complete_task(task_id, sheets_done, qty_produced)`:
  - TaskItem.status → DONE
  - TaskItem.sheets_done = sheets_done
  - TaskItem.qty_produced = qty_produced
  - TaskItem.completed_at = now()
  - `actual_minutes = (completed_at - started_at) - pause_duration`
  - MaterialAudit(write_off, qty=sheets_done) → через MaterialSystem
  - Проверить: all tasks done → WorkItem.status → DONE

### Трекинг
- [ ] `increment_sheets(task_id) -> int`:
  - `sheets_done += 1`; return sheets_done
- [ ] `get_drift(task) -> float`:
  - `(actual_minutes - estimated_minutes) / estimated_minutes * 100`
  - Позитивный drift = потратили больше
- [ ] ALLOWED_TRANSITIONS для TaskItemStatus:
  ```
  PLANNED   → IN_PROGRESS | CANCELLED
  IN_PROGRESS → ON_HOLD | DONE | BLOCKED | CANCELLED
  ON_HOLD   → IN_PROGRESS | CANCELLED
  BLOCKED   → IN_PROGRESS | CANCELLED
  ```

---

## Псевдокод

```python
class TaskBoardSystem(BaseSystem):
    
    async def lock_batch(self, batch_group_id: UUID, node_id: str, user: str) -> list[WorkerBucketEntry]:
        """
        Резервирует батч за оператором через FileBus REQ (slave) / прямо (master).
        """
        tasks = self._get_batch_tasks(batch_group_id)
        entries = []
        for task in tasks:
            entry = WorkerBucketEntry(
                node_id=node_id,
                assigned_user=user,
                task_item_id=task.id,
                batch_group_id=batch_group_id,
                locked_at=datetime.now()
            )
            self.session.add(entry)
            task.assigned_to_node = node_id
            task.status = TaskItemStatus.PLANNED
            entries.append(entry)
        self.session.commit()
        # Уведомить NSMirrorService
        for e in entries:
            await self.ns_mirror.on_bucket_add(e)
        return entries
    
    def complete_task(self, task_id: int, sheets_done: int, qty_produced: int) -> TaskItem:
        task = self.session.get(TaskItem, task_id)
        task.status = TaskItemStatus.DONE
        task.sheets_done = sheets_done
        task.qty_produced = qty_produced
        task.completed_at = datetime.now()
        
        # Вычислить actual_minutes
        if task.started_at:
            total = (task.completed_at - task.started_at).total_seconds() / 60
            # pause_duration вычисляем из WorkLog
            pause_logs = [l for l in task.work_logs if l.log_type == WorkLogType.ON_HOLD]
            pause_min = sum(json.loads(l.payload or "{}").get("duration_min", 0) 
                           for l in pause_logs)
            task.actual_minutes = int(total - pause_min)
        
        # WorkItem автоматически → DONE если все задачи закрыты
        self._check_work_item_completion(task.work_item_id)
        
        # Аудит материала
        self.material_system.write_off(task, sheets_done, author="system")
        
        self.session.commit()
        return task
```

---

## TDD: Тесты

```python
def test_lock_batch_creates_bucket_entries(in_memory_db):
    tasks = [TaskItem(batch_group_id=BATCH_UUID, ...) for _ in range(3)]
    system = TaskBoardSystem(...)
    entries = await system.lock_batch(BATCH_UUID, "LASER_1", "user1")
    
    assert len(entries) == 3
    assert all(e.node_id == "LASER_1" for e in entries)

def test_complete_task_calculates_drift(in_memory_db):
    task = TaskItem(estimated_minutes=60, started_at=now()-timedelta(minutes=90), ...)
    system = TaskBoardSystem(...)
    completed = system.complete_task(task.id, sheets_done=7, qty_produced=100)
    
    assert completed.actual_minutes == approx(90, abs=1)
    drift = system.get_drift(completed)
    assert drift == approx(50.0, abs=1)  # 50% перерасход

def test_invalid_transition_raises():
    task = TaskItem(status=TaskItemStatus.DONE, ...)
    with pytest.raises(ValueError):
        system.start_task(task.id)  # DONE → IN_PROGRESS запрещено

def test_work_item_auto_done_when_all_tasks_done(in_memory_db):
    wi = WorkItem(status=WorkItemStatus.IN_PROGRESS, ...)
    tasks = [TaskItem(work_item_id=wi.id, status=TaskItemStatus.DONE, ...),
             TaskItem(work_item_id=wi.id, status=TaskItemStatus.PLANNED, ...)]
    system = TaskBoardSystem(...)
    system.complete_task(tasks[1].id, sheets_done=5, qty_produced=50)
    
    wi_updated = in_memory_db.get(WorkItem, wi.id)
    assert wi_updated.status == WorkItemStatus.DONE
```

---

## Definition of Done

```
✓ lock_batch() → WorkerBucketEntry создаются + NSMirror вызван
✓ complete_task() → actual_minutes вычислен + MaterialAudit создан
✓ WorkItem → DONE автоматически когда все TaskItem DONE
✓ Все переходы статусов проверяются (недопустимые → ValueError)
✓ handover() создаёт ChatMessage(HANDOVER)
✓ drift% вычисляется правильно
✓ Все тесты проходят
```
