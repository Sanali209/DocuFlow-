# DF-003: FolderNameParser

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🔴 CRITICAL |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md) |
| **Блокирует** | [DF-006](./DF-006_folder_scanner_system.md) |
| **Data Flow** | [03_data_flow.md §2](../architecture/03_data_flow.md) |

---

## Контекст

Имя папки — единственный источник информации о типе наряда и его атрибутах. Парсер должен корректно работать как для стандартных SIDRA папок, так и для нестандартных (graceful fallback → MIHTAV + Default project).

---

## Execution Plan

```
1. Написать тесты на реальных именах папок (data_sample/) и граничных кейсах
2. Реализовать SIDRA regex
3. Реализовать graceful fallback
4. Проверить на всех примерах из data_sample/
```

---

## Подзадачи

- [x] Реализовать `FolderMeta` dataclass:
  ```
  work_item_type: WorkItemType
  sidra_number: Optional[str]
  sidra_step: Optional[str]
  doc_date: Optional[date]
  project_hint: Optional[str]
  ```
- [x] Реализовать `SIDRA_REGEX`:
  ```
  ^SIDRA-(?P<number>\d+)-(?P<step>.+?)-(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$
  ```
- [x] Реализовать `parse_folder_name(name: str) -> FolderMeta`
- [x] Graceful fallback: не SIDRA → `WorkItemType.MIHTAV`, project_hint=None
- [x] Отдельный кейс: имя содержит "REWORK" → `WorkItemType.REWORK`

---

## Псевдокод

```python
SIDRA_REGEX = re.compile(
    r'^SIDRA-(?P<number>\d+)-(?P<step>.+?)-'
    r'(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$',
    re.IGNORECASE
)

def parse_folder_name(name: str) -> FolderMeta:
    m = SIDRA_REGEX.match(name)
    if m:
        return FolderMeta(
            work_item_type=WorkItemType.SIDRA,
            sidra_number=m.group("number"),   # "353203"
            sidra_step=m.group("step"),       # "SHLAV-2"
            project_hint=m.group("step"),
            doc_date=date(int(m.group("year")),
                         int(m.group("month")),
                         int(m.group("day")))
        )
    # Fallback
    if "REWORK" in name.upper():
        return FolderMeta(work_item_type=WorkItemType.REWORK, ...)
    return FolderMeta(
        work_item_type=WorkItemType.MIHTAV,
        project_hint=None  # → Default project
    )
```

---

## TDD: Тесты

```python
# tests/unit/domain/test_folder_name_parser.py

def test_parse_sidra_standard():
    meta = parse_folder_name("SIDRA-353203-SHLAV-2-07.07.2025")
    assert meta.work_item_type == WorkItemType.SIDRA
    assert meta.sidra_number == "353203"
    assert meta.sidra_step == "SHLAV-2"
    assert meta.doc_date == date(2025, 7, 7)

def test_parse_unknown_folder_fallback():
    meta = parse_folder_name("Some-Random-Folder-Name")
    assert meta.work_item_type == WorkItemType.MIHTAV
    assert meta.sidra_number is None
    assert meta.project_hint is None   # → Default project

def test_parse_rework_folder():
    meta = parse_folder_name("REWORK-2025-07-Apollo-Bumper")
    assert meta.work_item_type == WorkItemType.REWORK

def test_parse_sidra_case_insensitive():
    meta = parse_folder_name("sidra-353203-SHLAV-2-07.07.2025")
    assert meta.work_item_type == WorkItemType.SIDRA
```

---

## Definition of Done

```
✓ Все тесты проходят
✓ Стандартное SIDRA имя парсится полностью
✓ Нестандартное имя → MIHTAV + project_hint=None
✓ REWORK в имени → WorkItemType.REWORK
✓ Нет raise при любом входном имени
```
