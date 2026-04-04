# DF-008: NotificationTemplate система

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md) |
| **Блокирует** | [DF-006](./DF-006_folder_scanner_system.md), [DF-022](../phase4/DF-022_chat_system.md), [DF-027](../phase4/DF-027_admin_improvements.md) |

---

## Контекст

Все тексты системных уведомлений должны быть настраиваемы через Admin Panel (см. review комментарий). Вместо хардкода строк → `render_template(key, vars)`. Шаблоны хранятся в `NotificationTemplate` сущности (DF-001).

---

## Подзадачи

- [ ] `NotificationTemplate` сущность уже в DF-001: `key`, `text` (Jinja2), `enabled`
- [ ] Встроенные шаблоны (`seed_defaults()`):
  ```
  scan.empty_folder   = "⚠️ {folder_name}: папка пришла, нестов нет! Сходить в раскрой"
  scan.new_work_item  = "📋 Новый наряд: {folder_name}"
  scan.file_changed   = "⚠️ Файл {file_name} изменился на сети! Обновить NS?"
  stock.alert         = "📦 Деталь {sku} есть в запасе — проверить перед резкой"
  doc.no_folder       = "📄 Бумага получена, папки нет на диске: {folder_name}"
  ```
- [ ] `NotificationService.render(key: str, **vars) -> Optional[str]`:
  - Если шаблон disabled → return None
  - Если ключ не найден → return fallback string (не raise)
  - Рендер через Jinja2 `Template(text).render(**vars)`
- [ ] Admin Panel: CRUD UI для NotificationTemplate (в DF-027)
- [ ] Метод `emit(key, **vars)` → рендер → `ChatMessage(type=INFO, content=rendered_text)`

---

## Псевдокод

```python
class NotificationService:
    def render(self, key: str, **vars) -> Optional[str]:
        tmpl = self.session.get_by_key(key)
        if not tmpl or not tmpl.enabled:
            return None
        try:
            return Template(tmpl.text).render(**vars)
        except Exception:
            return f"[{key}]"  # fallback
    
    def emit(self, key: str, ref_work_item_id=None, **vars) -> None:
        text = self.render(key, **vars)
        if text:
            msg = ChatMessage(
                author="system", node_id=this_node,
                message_type=ChatMessageType.INFO,
                content=text,
                ref_work_item_id=ref_work_item_id
            )
            self.session.add(msg)
```

---

## TDD: Тесты

```python
def test_render_with_vars():
    svc = NotificationService(templates={"scan.empty_folder": NotificationTemplate(
        key="scan.empty_folder",
        text="⚠️ {folder_name}: нестов нет!",
        enabled=True
    )})
    result = svc.render("scan.empty_folder", folder_name="SIDRA-353203")
    assert result == "⚠️ SIDRA-353203: нестов нет!"

def test_disabled_template_returns_none():
    svc = NotificationService(templates={"key": NotificationTemplate(key="key",
                                          text="text", enabled=False)})
    assert svc.render("key") is None

def test_missing_key_fallback():
    svc = NotificationService(templates={})
    result = svc.render("nonexistent.key", x=1)
    assert result is None or isinstance(result, str)  # не raise
```

---

## Definition of Done

```
✓ Все встроенные ключи имеют дефолтные шаблоны (seed_defaults работает)
✓ render() с корректными vars → правильный текст
✓ render() с disabled шаблоном → None (тихо)
✓ render() с неизвестным ключом → None или fallback (не raise)
✓ emit() создаёт ChatMessage в БД
```

---

# DF-009: folder_scanner/view.py

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-006](./DF-006_folder_scanner_system.md), [DF-007](./DF-007_ns_mirror_service.md), [DF-008](./DF-008_notification_templates.md) |
| **Gate** | **Gate 1** — после этого тикета проходим Gate 1 |

---

## Контекст

UI статуса сканера. Только для бригадира/начальника/админа. Показывает:
- Текущий мастер-узел, статус сканера
- Лог последних событий (WorkLog)
- Кнопка "Scan Now" (немедленное сканирование, только мастер)
- NS Mirror статус (текущие зеркальные файлы)

---

## Подзадачи

- [ ] `folder_scanner/view.py` — NiceGUI Vertical Slice:
  - [ ] Заголовок: "Мастер: {node_id}" + цветной индикатор активности
  - [ ] Карточка настроек: scan paths, poll interval (read-only, редактируется в Admin)
  - [ ] **Live лог**: `ui.log()` или `scan_log_panel` виджет — последние 50 WorkLog записей типа `FILE_CHANGED`, `NS_MIRROR`, `SCAN_ERROR`, `EMPTY_FOLDER`
  - [ ] Кнопка **"Scan Now"**: `await scanner.scan_now()` (только если is_master)
  - [ ] NS Mirror статус: список файлов в NS папке с их статусом (актуально/устарело)
  - [ ] Таблица последних WorkItem: статус + последнее сканирование

- [ ] `lib/widgets/scan_log_panel.py`:
  - Live scroll лог (NiceGUI reactive)
  - Цветовая кодировка: FILE_CHANGED=red, NS_MIRROR=blue, EMPTY_FOLDER=orange

- [ ] `lib/widgets/ns_mirror_status.py`:
  - Индикатор: `✓ Синхронизировано` / `⚠️ {N} файлов устарело`

---

## TDD: Тесты

```python
# Smoke test — компонент рендерится без ошибок
async def test_view_renders(mock_sdk):
    from docuflow.features.folder_scanner.view import FolderScannerView
    view = FolderScannerView(sdk=mock_sdk)
    # Не должно raise при рендере
    await view.render()
```

---

## Definition of Done (Gate 1 ✅)

```
Gate 1 PASSED если:
  ✓ DF-001: Все сущности в БД, тесты проходят
  ✓ DF-002: GncParser парсит реальный data_sample/ файл
  ✓ DF-003: FolderNameParser: SIDRA regex + fallback
  ✓ DF-004: TaskFileParser: is_variant фильтрует правильно
  ✓ DF-005: SVGGenerator возвращает реальный bbox
  ✓ DF-006: Сканер создаёт WorkItem(NEW) и WorkItem(PENDING_CUTS)
  ✓ DF-007: NS Mirror копирует GNC при добавлении в bucket
  ✓ DF-008: Уведомления настраиваемы через Admin
  ✓ DF-009: view.py рендерится, Scan Now работает
```
