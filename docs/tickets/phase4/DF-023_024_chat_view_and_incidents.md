# DF-023: chat/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-022](./DF-022_chat_system.md) |

---

## Контекст

Чат-интерфейс должен быть контекст-зависимым — открывается из карточки наряда / задачи / проекта. Также есть глобальный входящий ящик для всех сообщений.

---

## Подзадачи

### chat/view.py
- [ ] **ChatPanel** (встраиваемый в карточки WorkItem/TaskItem):
  - Заголовок: "💬 Чат: {context_name}" + счётчик непрочитанных
  - Список сообщений (дерево):
    - Иконка типа (📋 INFO / ⚠️ WARNING / 🚨 URGENT / 📦 ORDER / ⚡ INCIDENT / 🔄 HANDOVER)
    - Имя автора + время
    - Текст сообщения
    - Вложения: кнопки для скачивания файлов
    - Дочерние сообщения — с отступом (tree indent)
    - Кнопка "↩ Ответить"
  - Compose panel:
    - Textarea
    - Тип сообщения (dropdown)
    - Кнопка "📎 Прикрепить файл" → `ui.upload()`
    - Быстрые ответы chips (из NotificationTemplate quiet replies)
    - Кнопка "Отправить"

- [ ] **InboxView** (отдельный экран — все сообщения всех чатов):
  - Фильтр по типу сообщения
  - Фильтр "Только непрочитанные"
  - Группировка по WorkItem
  - Клик на сообщение → открыть карточку WorkItem + прокрутить к сообщению

- [ ] `lib/widgets/chat_thread.py` — компонент дерева сообщений
- [ ] `lib/widgets/chat_compose.py` — панель ввода сообщения

---

## Псевдокод

```python
class ChatPanel:
    """
    Встраиваемый чат-панель для контекста (WorkItem / TaskItem / Project).
    Принимает ref_type и ref_id.
    """
    def __init__(self, system: ChatSystem, ref_type: str, ref_id: int):
        self.system = system
        self.ref_type = ref_type
        self.ref_id = ref_id
    
    def render(self):
        messages = self.system.get_context(self.ref_type, self.ref_id)
        
        with ui.column().classes("chat-panel"):
            for msg in messages:
                if msg.parent_message_id is None:
                    self._render_message(msg, depth=0)
    
    def _render_message(self, msg: ChatMessage, depth: int):
        indent = "ml-" + str(depth * 4)  # Tailwind-style или css margin
        TYPE_ICONS = {
            ChatMessageType.INFO:     "ℹ️",
            ChatMessageType.WARNING:  "⚠️",
            ChatMessageType.URGENT:   "🚨",
            ChatMessageType.ORDER:    "📦",
            ChatMessageType.INCIDENT: "⚡",
            ChatMessageType.HANDOVER: "🔄",
            ChatMessageType.MESSAGE:  "💬",
            ChatMessageType.REPORT:   "📄",
        }
        with ui.row().classes(f"chat-message {indent}"):
            ui.label(TYPE_ICONS.get(msg.message_type, "💬"))
            with ui.column():
                ui.label(f"{msg.author} · {msg.created_at:%H:%M}").classes("text-xs text-gray")
                ui.label(msg.content)
                
                # Вложения
                for att in json.loads(msg.attachments or "[]"):
                    ui.button(f"📎 {att['name']}",
                        on_click=lambda a=att: ui.download(
                            self.system.resolve_attachment(msg.id, a["name"])
                        ))
                
                # Кнопка ответить
                ui.button("↩ Ответить", on_click=lambda m=msg: self._reply_dialog(m))
        
        # Дочерние сообщения
        children = [m for m in self.all_messages if m.parent_message_id == msg.id]
        for child in children:
            self._render_message(child, depth=depth + 1)
```

---

## TDD: Тесты

```python
async def test_chat_panel_renders(mock_sdk, in_memory_db):
    system = ChatSystem(session=in_memory_db)
    system.send("user1", "Привет", ref_work_item_id=1)
    
    panel = ChatPanel(system=system, ref_type="work_item", ref_id=1)
    await panel.render()  # smoke test

def test_type_icons_all_covered():
    """Все типы сообщений имеют иконку."""
    for msg_type in ChatMessageType:
        assert msg_type in ChatPanel.TYPE_ICONS

async def test_inbox_view_renders(mock_sdk):
    view = InboxView(sdk=mock_sdk)
    await view.render()  # smoke test
```

---

## Definition of Done

```
✓ ChatPanel встраивается в WorkItemCard без ошибок
✓ Дерево сообщений с отступами рендерится корректно
✓ Compose panel: тип + вложение + быстрые ответы
✓ ui.upload() вызывает ChatSystem.attach_file()
✓ Вложения: кнопка скачивания работает
✓ InboxView: фильтры по типу и непрочитанным работают
✓ Все типы ChatMessageType имеют иконки
```

---

# DF-024: IncidentSystem + view

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), [DF-022](./DF-022_chat_system.md) |

---

## Контекст

Инциденты — поломки, брак, простои. Регистрируются оператором. Автоматически публикуются в чат. Статистика простоев нужна для аналитики (DF-030).

---

## Подзадачи

### IncidentSystem
- [ ] `report_incident(task_item_id?, work_item_id?, incident_type, description, reported_by, attachments?) -> IncidentLog`:
  - Создать IncidentLog
  - Автоматически: ChatMessage(type=INCIDENT, content=description, ref_*=context)
- [ ] `resolve_incident(incident_id, resolved_by, resolution_note?)`:
  - `resolved=True`, `resolved_at=now()`, `resolved_by=resolved_by`
  - Вычислить `downtime_minutes = (resolved_at - created_at).total_seconds() / 60`
  - WorkLog(INFO, f"Инцидент закрыт: {resolution_note}")
- [ ] `list_incidents(filters) -> list[IncidentLog]`:
  - Фильтры: resolved, incident_type, node_id, date_from, date_to
- [ ] `get_downtime_stats(date_from, date_to) -> dict`:
  - Общее время простоя по типам инцидентов

### incidents/view.py
- [ ] Список инцидентов (таблица):
  - Колонки: incident_type badge, описание, reported_by, время, resolved badge
  - Красные строки: нерешённые
- [ ] Кнопка "Зарегистрировать инцидент":
  - Диалог: тип, описание + TaskItem ref, вложения (фото?)
- [ ] Карточка инцидента:
  - Описание + вложения
  - Кнопка "✅ Закрыть инцидент" → резолюция

---

## Псевдокод

```python
class IncidentSystem(BaseSystem):
    
    def report_incident(self, task_item_id: Optional[int], work_item_id: Optional[int],
                        incident_type: str, description: str, reported_by: str,
                        attachments: Optional[list] = None) -> IncidentLog:
        incident = IncidentLog(
            task_item_id=task_item_id,
            work_item_id=work_item_id,
            node_id=self.sdk.config.node_id,
            incident_type=incident_type,
            description=description,
            reported_by=reported_by,
            attachments=json.dumps(attachments or []),
            resolved=False
        )
        self.session.add(incident)
        
        # Автопубликация в чат
        self.chat_system.send(
            author=reported_by,
            content=f"⚡ ИНЦИДЕНТ [{incident_type}]: {description}",
            message_type=ChatMessageType.INCIDENT,
            ref_task_item_id=task_item_id,
            ref_work_item_id=work_item_id
        )
        
        self.session.commit()
        return incident
    
    def get_downtime_stats(self, date_from: date, date_to: date) -> dict:
        """Статистика простоев для аналитики (DF-030)."""
        incidents = self.session.exec(
            select(IncidentLog)
            .where(IncidentLog.resolved == True)
            .where(IncidentLog.created_at >= date_from)
            .where(IncidentLog.resolved_at <= date_to)
        ).all()
        
        stats = {}
        for inc in incidents:
            downtime = (inc.resolved_at - inc.created_at).total_seconds() / 60
            stats[inc.incident_type] = \
                stats.get(inc.incident_type, 0) + downtime
        return stats  # {"BREAKDOWN": 120.5, "DEFECT": 45.0, ...}
```

---

## TDD: Тесты

```python
def test_report_creates_incident_and_chat(in_memory_db):
    system = IncidentSystem(session=in_memory_db, chat_system=ChatSystem(...))
    incident = system.report_incident(
        task_item_id=1, work_item_id=1,
        incident_type="BREAKDOWN",
        description="Лазер не режет",
        reported_by="operator1"
    )
    assert incident.id is not None
    msgs = in_memory_db.exec(select(ChatMessage)
                              .where(ChatMessage.message_type == ChatMessageType.INCIDENT)).all()
    assert len(msgs) == 1

def test_resolve_calculates_downtime(in_memory_db):
    system  = IncidentSystem(session=in_memory_db, ...)
    incident = system.report_incident(task_item_id=None, ...,
                                       incident_type="BREAKDOWN",
                                       description="Сопло сгорело",
                                       reported_by="op1")
    # Симулировать 30 минут простоя
    incident.created_at = datetime.now() - timedelta(minutes=30)
    in_memory_db.commit()
    
    system.resolve_incident(incident.id, "foreman1", "Заменили сопло")
    
    updated = in_memory_db.get(IncidentLog, incident.id)
    assert updated.resolved is True
    assert updated.resolved_at is not None
    downtime = (updated.resolved_at - updated.created_at).total_seconds() / 60
    assert 29 < downtime < 31

def test_downtime_stats_grouping(in_memory_db):
    system = IncidentSystem(...)
    # Добавить 2 инцидента разных типов
    ...
    stats = system.get_downtime_stats(
        date_from=date.today() - timedelta(days=1),
        date_to=date.today() + timedelta(days=1)
    )
    assert "BREAKDOWN" in stats
    assert stats["BREAKDOWN"] > 0
```

---

## Definition of Done

```
✓ report_incident() создаёт IncidentLog + ChatMessage(INCIDENT)
✓ resolve_incident() вычисляет downtime правильно
✓ list_incidents() фильтрует по resolved / type / date
✓ get_downtime_stats() группирует по типам
✓ incidents/view.py: нерешённые выделены красным
✓ Закрытие инцидента: диалог с резолюцией работает
✓ Все тесты проходят
```
