# 19. Интернационализация (i18n)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 19.1 Current State

### ❌ NOT IMPLEMENTED
- No i18n system
- No translation files
- All strings hardcoded

### ⚠️ Impact
- Russian language only
- No language switching
- Hard to localize

---

## 19.2 Hardcoded Strings

### Examples
```python
ui.label("Начать")  # Start
ui.label("Готово")  # Done
ui.label("В работе")  # In progress
```

### ⚠️ Scope
- UI labels
- Button text
- Status messages
- Error messages

---

## 19.3 Language

### Current: Russian
```python
ui.button("Создать документ")
ui.button("Получить документ")
ui.label("Цеховая документация")
```

### ⚠️ Issues
- No English fallback
- Mixed languages possible
- Hard to maintain

---

## 19.4 Output Format

### Dates
```python
datetime.datetime.now()  # Locale-sensitive
```

### ⚠️ Issues
- No format standardization
- Locale-dependent output

---

## 19.5 Выводы

### ✅ Сильные стороны
- Human-readable labels (Russian)
- Consistent terminology

### ⚠️ Критические проблемы
1. **No i18n system** — not ready for localization
2. **Hardcoded strings** — 100+ strings
3. **No language switching** — single language
4. **No translation files** — no workflow
5. **Mixed languages** — some English, some Russian

---

## 19.6 Рекомендации

1. **Add gettext**:
   ```python
   from gettext import gettext as _
   
   ui.button(_("Создать документ"))
   ```

2. **Create translation files**:
   ```bash
   locale/ru/LC_MESSAGES/messages.po
   locale/en/LC_MESSAGES/messages.po
   ```

3. **Language switcher**:
   ```python
   @ui.page('/settings')
   async def settings():
       ui.select(['ru', 'en'], label='Language')
   ```

4. **Extract strings**:
   ```bash
   xgettext -d messages -o locale/messages.pot src/**/*.py
   ```

---

## 19.7 TODO

- [ ] Add i18n framework
- [ ] Extract hardcoded strings
- [ ] Create translation files
- [ ] Add language switcher
- [ ] Translate to English

---

*Секция: 19_i18n*
