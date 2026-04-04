# DF-022: ChatSystem (треды + типы + файлы)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 4 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](../phase1/DF-001_domain_entities.md), [DF-008](../phase1/DF-008_009_notifications_and_view.md) |
| **Блокирует** | [DF-023](./DF-023_chat_view.md), [DF-024](./DF-024_incident_system.md) |
| **Data Flow** | [03_data_flow.md §5](../architecture/03_data_flow.md) |

---

## Контекст

Оперативный чат — это основной канал коммуникации цеха. Дерево сообщений привязано к объектам (Project / WorkItem / TaskItem). Типы сообщений позволяют фильтровать по смыслу (ORDER отдельно от INCIDENT).

Ключевые отличия от "обычного чата":
- **Контекст-привязка**: каждое сообщение знает к чему относится
- **Типы**: ORDER, INCIDENT, HANDOVER, REPORT — не просто "текст"
- **Вложения**: начальник прикладывает PDF задания к сообщению
- **Система авто-пишет**: NSMirror, сканер, расходники — всё через чат

---

## Execution Plan

```
1. Написать тесты для дерева и фильтрации
2. Реализовать ChatSystem с CRUD
3. Реализовать send() — основной метод
4. Реализовать get_thread() — дерево ответов
5. Реализовать get_context() — все сообщения по объекту
6. Реализовать attachment upload/resolve
```

---

## Подзадачи

### Core
- [ ] `send(author, content, message_type=MESSAGE, ref_project_id?, ref_work_item_id?, ref_task_item_id?, parent_message_id?, template_name?, attachments?) -> ChatMessage`:
  - Валидация: хотя бы один ref или parent (иначе → глобальный чат)
  - Если `template_name` задан → render notification template
  - Если attachments → сохранить файлы, сохранить пути в `attachments` JSON
- [ ] `reply(parent_id, author, content, message_type=MESSAGE, **kwargs) -> ChatMessage`:
  - Наследует ref_* от родительского сообщения
- [ ] `get_thread(message_id) -> list[ChatMessage]`:
  - Рекурсивно: message + все children (по parent_message_id)
- [ ] `get_context(ref_type, ref_id, message_types=None, limit=100) -> list[ChatMessage]`:
  - Все сообщения для ref_type="work_item" ref_id=wi.id
  - Опциональный фильтр по типам
- [ ] `mark_read(message_id, user)`:
  - `is_read = True` (упрощённо; без per-user tracking в v1)
- [ ] `get_unread_count(node_id) -> int`

### Attachments
- [ ] `attach_file(message_id, file_bytes, filename) -> str`:
  - Сохранить в `{data_dir}/chat_attachments/{message_id}/{filename}`
  - Обновить `message.attachments` JSON: `[{"path": rel_path, "name": filename}]`
- [ ] `resolve_attachment(message_id, filename) -> Path`:
  - Вернуть абсолютный путь к файлу (для скачивания)

### Быстрые методы
- [ ] `send_order(work_item_id, content, author) -> ChatMessage`:
  - `type=ORDER`, `ref_work_item_id=work_item_id`
- [ ] `send_incident(task_item_id, description, author) -> ChatMessage`:
  - `type=INCIDENT`, `ref_task_item_id=task_item_id`
- [ ] `send_handover(note, author) -> ChatMessage`:
  - `type=HANDOVER`

### Шаблоны быстрых ответов
- [ ] `get_quick_replies(context) -> list[str]`:
  - Предустановленные фразы из NotificationTemplate с ключами `chat.quick.*`
  - Пример: `chat.quick.understood` = "Понял, принял" / `chat.quick.need_material` = "Нужен материал: {mat}"

---

## Псевдокод

```python
class ChatSystem(BaseSystem):
    
    def send(self, author: str, content: str,
             message_type: ChatMessageType = ChatMessageType.MESSAGE,
             ref_project_id:  Optional[int] = None,
             ref_work_item_id: Optional[int] = None,
             ref_task_item_id: Optional[int] = None,
             parent_message_id: Optional[int] = None,
             attachments: Optional[list[dict]] = None) -> ChatMessage:
        """
        Основной метод отправки сообщения.
        Автоматически наследует ref_* от родительского если задан parent.
        """
        if parent_message_id and not any([ref_project_id, ref_work_item_id, ref_task_item_id]):
            parent = self.session.get(ChatMessage, parent_message_id)
            ref_project_id  = parent.ref_project_id
            ref_work_item_id = parent.ref_work_item_id
            ref_task_item_id = parent.ref_task_item_id
        
        msg = ChatMessage(
            author=author,
            node_id=self.sdk.config.node_id,
            message_type=message_type,
            content=content,
            ref_project_id=ref_project_id,
            ref_work_item_id=ref_work_item_id,
            ref_task_item_id=ref_task_item_id,
            parent_message_id=parent_message_id,
            attachments=json.dumps(attachments or []),
            is_read=False
        )
        self.session.add(msg)
        self.session.commit()
        return msg
    
    def get_context(self, ref_type: str, ref_id: int,
                    message_types: Optional[list[ChatMessageType]] = None,
                    limit: int = 100) -> list[ChatMessage]:
        """
        Возвращает все сообщения для объекта (project/work_item/task_item).
        Включает вложенные ответы (дерево).
        """
        ref_col_map = {
            "project":   ChatMessage.ref_project_id,
            "work_item": ChatMessage.ref_work_item_id,
            "task_item": ChatMessage.ref_task_item_id,
        }
        col = ref_col_map[ref_type]
        
        q = select(ChatMessage).where(col == ref_id)
        if message_types:
            q = q.where(ChatMessage.message_type.in_(message_types))
        q = q.order_by(ChatMessage.created_at).limit(limit)
        
        return self.session.exec(q).all()
    
    def get_thread(self, message_id: int) -> list[ChatMessage]:
        """Возвращает сообщение + все дочерние рекурсивно."""
        def _collect(msg_id: int) -> list[ChatMessage]:
            children = self.session.exec(
                select(ChatMessage)
                .where(ChatMessage.parent_message_id == msg_id)
                .order_by(ChatMessage.created_at)
            ).all()
            result = []
            for child in children:
                result.append(child)
                result.extend(_collect(child.id))
            return result
        
        root = self.session.get(ChatMessage, message_id)
        return [root] + _collect(message_id)
```

---

## TDD: Тесты

```python
def test_send_message_with_work_item_ref(in_memory_db):
    wi = WorkItem(folder_name="SIDRA-001", ...)
    in_memory_db.add(wi); in_memory_db.commit()
    
    system = ChatSystem(session=in_memory_db)
    msg = system.send(author="user1", content="Начал резать",
                      ref_work_item_id=wi.id)
    
    assert msg.ref_work_item_id == wi.id
    assert msg.message_type == ChatMessageType.MESSAGE

def test_reply_inherits_ref_from_parent(in_memory_db):
    system = ChatSystem(session=in_memory_db)
    parent = system.send(author="user1", content="Нужен ST37",
                         ref_work_item_id=5)
    child = system.reply(parent_id=parent.id, author="user2",
                         content="Понял, принял")
    
    assert child.ref_work_item_id == parent.ref_work_item_id  # унаследовал
    assert child.parent_message_id == parent.id

def test_get_thread_returns_tree(in_memory_db):
    system = ChatSystem(session=in_memory_db)
    root    = system.send(author="u1", content="Вопрос", ref_work_item_id=1)
    child1  = system.reply(root.id, "u2", "Ответ 1")
    child2  = system.reply(root.id, "u3", "Ответ 2")
    child11 = system.reply(child1.id, "u1", "Уточнение")
    
    thread = system.get_thread(root.id)
    assert len(thread) == 4  # root + 3 детей

def test_get_context_filters_by_type(in_memory_db):
    system = ChatSystem(session=in_memory_db)
    system.send(author="u1", content="Сообщение",
                ref_work_item_id=1, message_type=ChatMessageType.MESSAGE)
    system.send(author="sys", content="Нужен материал",
                ref_work_item_id=1, message_type=ChatMessageType.ORDER)
    
    orders = system.get_context("work_item", 1,
                                 message_types=[ChatMessageType.ORDER])
    assert len(orders) == 1
    assert orders[0].message_type == ChatMessageType.ORDER

def test_attach_file_saves_and_resolves(in_memory_db, tmp_path):
    system = ChatSystem(session=in_memory_db, data_dir=tmp_path)
    msg = system.send(author="user1", content="Задание", ref_work_item_id=1)
    
    system.attach_file(msg.id, b"PDF CONTENT", "zadanie.pdf")
    
    resolved = system.resolve_attachment(msg.id, "zadanie.pdf")
    assert resolved.exists()
    assert resolved.read_bytes() == b"PDF CONTENT"

def test_order_message_creates_correct_type(in_memory_db):
    system = ChatSystem(session=in_memory_db)
    msg = system.send_order(work_item_id=1, content="Нужен AA 5052 3mm", author="foreman1")
    assert msg.message_type == ChatMessageType.ORDER
    assert msg.ref_work_item_id == 1
```

---

## Definition of Done

```
✓ send() создаёт ChatMessage с правильными ref_*
✓ reply() наследует ref_* от родителя
✓ get_thread() возвращает полное дерево
✓ get_context() фильтрует по message_types
✓ attach_file() сохраняет файл физически
✓ resolve_attachment() возвращает рабочий Path
✓ send_order() / send_incident() / send_handover() — конвенции работают
✓ Системные сообщения (NotificationService.emit) используют ChatSystem.send
✓ Все тесты проходят
```
