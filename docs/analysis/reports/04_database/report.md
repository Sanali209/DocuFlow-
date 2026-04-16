# 04. База данных (Database)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 4.1 Database Schema (SQLModel)

### Entity Count: 27 таблиц

| # | Entity | Файл | Описание |
|---|--------|------|----------|
| 1 | Project | production.py | Проекты |
| 2 | WorkItem | production.py | Заказы/папки |
| 3 | TaskItem | production.py | GNC задачи |
| 4 | TaskPart | production.py | Части задач |
| 5 | PartLibrary | production.py | Библиотека деталей |
| 6 | PartTemplate | production.py | Шаблоны деталей |
| 7 | MaterialType | production.py | Типы материалов |
| 8 | MaterialStock | production.py | Склад материалов |
| 9 | Reservation | production.py | Резервирования |
| 10 | MaterialAudit | production.py | Аудит материалов |
| 11 | Consumable | production.py | Расходники |
| 12 | ConsumableLog | production.py | Логи расходников |
| 13 | StorageLocation | production.py | Места хранения |
| 14 | ProductionUnit | production.py | Производственные единицы |
| 15 | WorkerBucketEntry | production.py | Записи рабочих корзин |
| 16 | WorkLog | production.py | Рабочие логи |
| 17 | IncidentLog | production.py | Логи инцидентов |
| 18 | ChatMessage | production.py | Сообщения чата |
| 19 | Tag | production.py | Теги |
| 20 | ReportTemplate | production.py | Шаблоны отчётов |
| 21 | ViewPreset | production.py | Пресеты видов |
| 22 | NotificationTemplate | production.py | Шаблоны уведомлений |
| 23 | Workplace | identity.py | Рабочие места |
| 24 | Role | identity.py | Роли |
| 25 | User | identity.py | Пользователи |
| 26 | NodeSetting | identity.py | Настройки узлов |

---

## 4.2 Base Entity

### BaseEntity (base.py)
```python
class BaseEntity(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
```

### Плюсы
- Единая база для всех сущностей
- Автоматические timestamps для LWW conflict resolution

### ⚠️ Потенциальные проблемы
- `datetime.datetime.now` не timezone-aware
- No soft deletes
- No versioning

---

## 4.3 Indexes

### Indexed Fields: 27

| Entity | Indexed Fields |
|--------|---------------|
| Project | name (unique) |
| WorkItem | project_id, folder_name (unique) |
| TaskItem | work_item_id, mat_type_id |
| TaskPart | task_item_id, part_sku |
| PartLibrary | sku, version |
| PartTemplate | part_sku |
| MaterialType | code (unique) |
| MaterialStock | mat_type_id |
| Reservation | stock_item_id |
| MaterialAudit | - |
| Consumable | name (unique) |
| ConsumableLog | consumable_id |
| StorageLocation | code (unique) |
| ProductionUnit | label_id (unique), node_id |
| WorkerBucketEntry | node_id, task_item_id |
| WorkLog | work_item_id, task_item_id |
| IncidentLog | - |
| ChatMessage | - |
| Tag | - |
| ReportTemplate | - |
| ViewPreset | key (unique) |
| NotificationTemplate | - |
| Workplace | node_id (unique) |
| Role | name (unique) |
| User | username (unique) |
| NodeSetting | node_id, module, key |

### ⚠️ Missing Indexes
- `ChatMessage.created_at` — часто фильтруется
- `IncidentLog.created_at`
- `MaterialAudit.*` — часто запросы

---

## 4.4 Foreign Keys

### ✅ Конфигурация
```python
# di.py:112
cursor.execute("PRAGMA foreign_keys=ON")
```

### Foreign Key References
| From | To | Required |
|------|-----|---------|
| User.role_id | Role.id | ✅ Yes |
| WorkItem.project_id | Project.id | ✅ Yes |
| TaskItem.work_item_id | WorkItem.id | ✅ Yes |
| TaskItem.mat_type_id | MaterialType.id | ❌ No (nullable) |
| TaskPart.task_item_id | TaskItem.id | ✅ Yes |
| PartTemplate.part_sku | PartLibrary.sku | ✅ Yes |
| MaterialStock.mat_type_id | MaterialType.id | ✅ Yes |
| Reservation.stock_item_id | MaterialStock.id | ✅ Yes |
| ConsumableLog.consumable_id | Consumable.id | ✅ Yes |
| WorkerBucketEntry.task_item_id | TaskItem.id | ✅ Yes |

---

## 4.5 SQLite Optimizations

### Pragmas (di.py:106-117)
```python
PRAGMA journal_mode=WAL          # ✅ Concurrent reads
PRAGMA synchronous=NORMAL        # ✅ Balance safety/performance
PRAGMA foreign_keys=ON           # ✅ Referential integrity
PRAGMA cache_size=-64000         # ✅ 64MB cache
```

### ⚠️ TODO: Additional Pragmas
```python
PRAGMA temp_store=MEMORY         # ✅ Temp tables in memory
PRAGMA mmap_size=268435456       # ✅ 256MB memory-mapped I/O
```

---

## 4.6 Multi-Node Databases

### Database Files Found
```
*.db files in root:
- node_01.db (266 KB)
- NODE_A.db (253 KB)
- NODE_B.db (253 KB)
- TEST_ORCH.db (253 KB)
- test_node.db (253 KB)
- test_infra_node.db (258 KB)
```

### Naming Convention
- `{node_id}.db` — соответствует `DOCUFLOW_NODE_ID`

### ⚠️ Проблемы
- Runtime DB файлы в репозитории (`*.db`, `*-wal`, `*-shm`)
- Нет `.gitignore` для `*.db*`

---

## 4.7 Migrations

### ❌ Alembic: NOT FOUND
### ❌ Manual Migrations: NOT FOUND

### ⚠️ Критическая проблема
Нет механизма миграций схемы между версиями!

### Рекомендация: Добавить Alembic
```bash
alembic init migrations
alembic revision --autogenerate -m "initial"
```

---

## 4.8 Queries Analysis

### N+1 Потенциал
```python
# Типичный N+1 паттерн
for work_item in work_items:
    print(work_item.project.name)  # N queries для project
    for task in work_item.tasks:
        print(task.material_type)  # N queries для type
```

### Рекомендация: Eager Loading
```python
session.exec(
    select(WorkItem)
    .options(joinedload(WorkItem.project))
    .where(...)
)
```

---

## 4.9 Soft Deletes

### ❌ NOT IMPLEMENTED
Все сущности используют hard delete.

### ⚠️ Риск
- Accidential data loss
- No audit trail for deletions

---

## 4.10 Выводы

### ✅ Сильные стороны
- Хорошее покрытие indexes
- WAL mode настроен
- Foreign keys enabled
- BaseEntity с timestamps

### ⚠️ Критические проблемы
1. **Нет миграций** — невозможно обновить схему
2. **Нет soft deletes** — риск потери данных
3. **Runtime DB в repo** — `*.db` файлы в git
4. **N+1 queries** — возможны в ORM запросах
5. **Missing indexes** — на часто фильтруемых полях

---

## 4.11 Рекомендации

1. **Добавить Alembic migrations**:
   ```bash
   alembic init migrations
   ```

2. **Добавить soft deletes**:
   ```python
   class BaseEntity(SQLModel):
       is_deleted: bool = Field(default=False)
       deleted_at: datetime | None = None
   ```

3. **Убрать DB из репозитория**:
   ```bash
   echo "*.db" >> .gitignore
   echo "*.db-*" >> .gitignore
   ```

4. **Добавить missing indexes**:
   ```python
   created_at: datetime = Field(default_factory=datetime.datetime.now, index=True)
   ```

5. **Использовать eager loading**:
   ```python
   from sqlalchemy.orm import joinedload
   ```

---

## 4.12 TODO

- [ ] Добавить Alembic migrations
- [ ] Убрать *.db из репозитория
- [ ] Добавить soft deletes
- [ ] Проверить N+1 queries
- [ ] Добавить missing indexes

---

*Секция: 04_database*
