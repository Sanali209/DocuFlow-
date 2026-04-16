# 18. UI/UX

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 18.1 Widget Library

### Components (lib/widgets/)
```
lib/widgets/
├── __init__.py
├── activity_stream.py
├── batch_card.py
├── bucket_panel.py
├── bucket_panel_dialogs.py
├── button.py
├── card.py
├── explorer_button.py
├── file_changed_alert.py
├── info_row.py
├── input.py
├── kpi_card.py
├── ns_mirror_status.py
├── part_preview.py
├── scan_log_panel.py
├── status_badge.py
├── status_indicator.py
├── surface.py
├── ui_utils.py
├── work_item_card.py
└── base_widget.py
```

### Count: 20+ widgets

---

## 18.2 NiceGUI Usage

### Pattern
```python
from nicegui import ui

class WorkItemCard:
    def __init__(self, work_item):
        self.work_item = work_item
    
    def render(self) -> ui.card:
        with ui.card():
            ui.label(self.work_item.folder_name)
            StatusBadge(self.work_item.status).render()
```

### ✅ Good
- Component-based
- Reusable widgets
- Consistent styling

---

## 18.3 Navigation

### Structure (main.py)
```python
ui.navigate.to('/')
ui.navigate.to('/admin')
ui.navigate.to('/inventory')
ui.navigate.to('/reports')
```

### ⚠️ Issues
- No breadcrumbs
- No sidebar menu
- URL not always updated

---

## 18.4 Styling

### Tailwind CSS
```python
ui.button('Click me').classes('bg-blue-500 text-white')
```

### ⚠️ Issues
- Inline styles scattered
- `.classes("text-slate-500 text-sm")` in views
- No design tokens
- No theme system

---

## 18.5 State Management

### Current
```python
# Server state
session.query(WorkItem).all()

# UI updates
ui.timer(1.0, update_callback)
```

### ⚠️ Issues
- No optimistic updates
- Polling-based UI
- State synced on interval

---

## 18.6 Accessibility

### ❌ NOT CHECKED
- No ARIA labels
- No keyboard navigation
- No screen reader support

---

## 18.7 Layout

### Layout System
```python
# features/core/layout.py
class MainLayout:
    def __init__(self):
        self.header = Header()
        self.content = Content()
        self.sidebar = Sidebar()
```

### ✅ Good
- Layout separation
- Header/content/sidebar

---

## 18.8 Выводы

### ✅ Сильные стороны
- Good widget library
- Component-based
- Tailwind CSS

### ⚠️ Проблемы
1. **Inline styles** — scattered .classes()
2. **No design tokens** — inconsistent
3. **No breadcrumbs** — poor navigation
4. **Polling UI** — inefficient
5. **No accessibility** — not inclusive

---

## 18.9 Рекомендации

1. **Design tokens**:
   ```python
   # lib/theme.py
   COLORS = {
       'primary': 'blue-500',
       'secondary': 'gray-500',
   }
   SIZES = {
       'small': 'text-sm',
       'normal': 'text-base',
   }
   ```

2. **Breadcrumbs**:
   ```python
   from nicegui import ui
   ui.breadcrumbs([
       {'text': 'Home', 'href': '/'},
       {'text': 'Work Items', 'href': '/work-items'},
   ])
   ```

3. **Optimistic updates**:
   ```python
   async def save():
       # Update UI immediately
       ui.notify('Saving...')
       # Then sync with server
       await system.save()
       ui.notify('Saved!', type='positive')
   ```

---

## 18.10 TODO

- [ ] Extract design tokens
- [ ] Add breadcrumbs
- [ ] Improve navigation
- [ ] Consider real-time updates
- [ ] Add accessibility

---

*Секция: 18_ui_ux*
