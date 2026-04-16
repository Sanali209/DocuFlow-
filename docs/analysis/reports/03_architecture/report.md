# 03. Архитектура (Architecture)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 3.1 Макроархитектура

### Architectural Pattern
| Паттерн | Реализация |
|---------|------------|
| **Vertical Slices** | ✅ 17 features, каждый с `system.py` + `view.py` |
| **Hexagonal Architecture** | ✅ Domain / Infrastructure / Application |
| **Dependency Injection** | ✅ Dishka |
| **P2P / Decentralized** | ✅ FileBus + SQLite per-node |

### Структура слоёв

```
src/docuflow/
├── application/          # Application Layer
│   ├── bus/             # P2P Orchestrator, Dispatcher
│   └── base.py          # BaseSystem
├── domain/              # Domain Layer
│   ├── entities/        # SQLModel entities
│   └── messages.py      # P2P message schemas
├── features/            # Vertical Slices (17 штук)
│   ├── system.py        # Business logic
│   └── view.py          # UI (NiceGUI)
├── infrastructure/       # Adapters Layer
│   ├── bus.py           # FileBus
│   ├── coordination.py  # Leader election
│   ├── security.py      # HMAC
│   └── sync.py          # DataSync
└── lib/                 # Shared UI components
    └── widgets/         # Reusable widgets
```

---

## 3.2 Dependency Injection (Dishka)

### Scope Usage

| Scope | Providers | Назначение |
|-------|-----------|------------|
| **Scope.APP** | 15 | Синглтоны: Config, Engine, Orchestrator, Bus, etc. |
| **Scope.REQUEST** | 14 | Per-request: Session, Feature Systems |

### APP-scoped providers
```python
# Infrastructure
- Config
- Engine (SQLite with WAL)
- HMACSigner
- CoordinationSystem
- FileBusSystem
- DataSyncSystem
- HousekeepingSystem
- AdminSyncSystem
- SecureDispatcher
- P2POrchestrator
- SDK (singleton guard)
- FolderScannerSystem
- NSMirrorService
- FolderScannerSettings
- ReportRegistry
```

### REQUEST-scoped providers
```python
# Feature Systems
- SearchSystem
- ProjectSystem
- PartLibrarySystem
- ConsumableSystem
- ProductionSystem
- AuthSystem
- WorkItemSystem
- ViewPresetSystem
- InventorySystem
- AdminSystem
- NotificationService
- TaskBoardSystem
- ChatSystem
- IncidentSystem
- ReportSystem
```

### DI Configuration Issues

#### ⚠️ Потенциальные проблемы
1. **SDK singleton guard** (`di.py:183-184`):
   ```python
   if hasattr(self, "_sdk") and self._sdk is not None:
       return self._sdk
   ```
   - Ручной singleton поверх Dishka scope
   - Может создавать проблемы при multiple containers

2. **TYPE_CHECKING imports** (`di.py:11-36`):
   - Не все импорты обёрнуты в TYPE_CHECKING
   - Некоторые импортируются напрямую

---

## 3.3 Vertical Slices Analysis

### Features (17 активных)

| # | Feature | system.py | view.py | Status |
|---|---------|----------|---------|--------|
| 1 | admin | ✅ | ✅ |  |
| 2 | analytics | ❓ | ❓ | Need check |
| 3 | auth | ✅ | ✅ |  |
| 4 | chat | ✅ | ✅ |  |
| 5 | consumables | ✅ | ❓ | Need check |
| 6 | core | ✅ (search.py) | ❓ | Partial |
| 7 | dashboard | ❓ | ❓ | Need check |
| 8 | docs | ✅ | ✅ |  |
| 9 | folder_scanner | ✅ | ❓ | Partial |
| 10 | inventory | ✅ | ❓ | Need check |
| 11 | notifications | ✅ | ❓ | Need check |
| 12 | parts | ✅ | ✅ |  |
| 13 | production | ✅ | ❓ | Need check |
| 14 | projects | ✅ | ❓ | Need check |
| 15 | reports | ✅ | ✅ |  |
| 16 | task_board | ✅ | ✅ |  |
| 17 | view_presets | ✅ | ❓ | Need check |
| 18 | work_items | ✅ | ✅ |  |

**Консистентность**: 14 из 17 имеют `system.py`, но не все имеют `view.py`

### Vertical Slice Pattern
```python
# features/<name>/system.py
class XxxSystem(BaseSystem):
    def __init__(self, config, session, ...):
        super().__init__(config, session)
        # Dependencies
        
    async def on_startup(self): ...
    async def on_shutdown(self): ...
    # Business methods

# features/<name>/view.py
class XxxView:
    def __init__(self, system: XxxSystem):
        self.system = system
    
    def render(self):
        # NiceGUI UI
```

---

## 3.4 Domain-Driven Design

### Entities (src/docuflow/domain/entities/)

```
domain/entities/
├── __init__.py
├── admin.py
├── chat.py
├── incidents.py
├── inventory.py
├── notifications.py
├── parts.py
├── production.py
├── projects.py
├── reports.py
├── scanner.py
├── settings.py
├── task_board.py
├── users.py
├── work_items.py
└── warehouse.py
```

### Domain Events
- Используются в `features/notifications/system.py`
- Формат: через P2P messages

### Repositories
- Не выделены явно
- Прямые SQLModel операции через `session`

---

## 3.5 P2P Architecture

### Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **P2POrchestrator** | `orchestrator.py` | Lifecycle management |
| **CoordinationSystem** | `coordination.py` | Leader election |
| **FileBusSystem** | `bus.py` | File-based messaging |
| **SecureDispatcher** | `dispatcher.py` | HMAC verification |
| **DataSyncSystem** | `sync.py` | DB synchronization |

### Leader Election
- Координация через файловую систему (shared network)
- Heartbeat mechanism
- 60s failover

---

## 3.6 Base System

### BaseSystem (`application/base.py`)
```python
class BaseSystem:
    def __init__(self, config: Config, session: Session | None = None)
    @property config -> Config
    @property db_session -> Session  # Raises RuntimeError if None
    async def on_startup()
    async def on_shutdown()
```

### Проблемы
1. **RuntimeError** на `db_session` — может быть неожиданным
2. **Mutable session** — сеттер позволяет менять session

---

## 3.7 Выводы

### ✅ Сильные стороны
- Чёткая Vertical Slice структура
- Единый BaseSystem для всех систем
- Dishka для DI с правильными scopes
- P2P архитектура для децентрализации
- Разделение Infrastructure / Application / Domain

### ⚠️ Требует внимания
1. **Missing view.py** — не все features имеют UI
2. **SDK singleton guard** — нестандартный паттерн
3. **Session management** — RuntimeError может быть проблемой
4. **No explicit repositories** — запросы разбросаны по системам
5. **IncidentSystem** — импортируется как `chat.incidents`

---

## 3.8 Рекомендации

1. **Standardize vertical slices**:
   - Все features должны иметь system.py + view.py
   - Или документировать exceptions

2. **Remove SDK singleton guard** — позволить Dishka управлять

3. **Consider Repository pattern**:
   ```python
   # Вместо прямых session.query()
   class WorkItemRepository:
       def __init__(self, session: Session)
       def get_by_id(id) -> WorkItem
   ```

4. **Унифицировать naming**:
   - `chat.incidents` → отдельный feature или часть chat

5. **Добавить Domain Events**:
   ```python
   from dataclasses import dataclass
   
   @dataclass
   class DomainEvent:
       occurred_at: datetime
       aggregate_id: str
   ```

---

## 3.9 TODO

- [ ] Проверить все features на наличие view.py
- [ ] Рефакторить SDK singleton
- [ ] Рассмотреть Repository pattern
- [ ] Унифицировать chat/incidents

---

*Секция: 03_architecture*
