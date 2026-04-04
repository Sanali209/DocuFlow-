# DF-004: TaskFileParser + is_variant

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md) |
| **Блокирует** | [DF-006](./DF-006_folder_scanner_system.md) |

---

## Контекст

Не все GNC файлы в папке нужно сканировать. Существуют "variant" файлы (`_AUT.TXT`, `.Dsp`, и производные GNC-файлы с суффиксами). Только основные GNC файлы попадают как TaskItem.

Также из имени файла извлекается `step_index` и `batch_index` для группировки внутри наряда.

---

## Подзадачи

- [x] Реализовать `is_variant(file: Path) -> bool`:
  - [x] Суффикс не `.GNC` (case-insensitive) → True
  - [x] `_AUT.TXT` файлы → True
  - [x] `.Dsp` файлы → True
  - [x] Основной `.GNC` файл (не суффикс, не _AUT) → False
- [x] Реализовать `TaskFileMeta` dataclass: `step_index`, `batch_index`, `gnc_name`
- [x] Реализовать `parse_task_filename(name: str) -> TaskFileMeta`:
  - [x] Паттерн: `{step_idx:02d}-{batch_idx:02d}-SIDRA-...-{MAT}-{THK}.GNC`
  - [x] Graceful fallback: если не парсится → оба None

---

## Псевдокод

```python
def is_variant(file: Path) -> bool:
    """Возвращает True если файл НЕ является основным нестом."""
    name = file.name.upper()
    if file.suffix.upper() != ".GNC":
        return True
    if "_AUT" in name:
        return True
    # Добавить другие правила по мере обнаружения
    return False

# Паттерн имени GNC файла:
# 12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC
# ↑  ↑
# step_index=12, batch_index=06
TASK_FILE_REGEX = re.compile(
    r'^(?P<step>\d{2})-(?P<batch>\d{2})-(?P<rest>.+)\.GNC$',
    re.IGNORECASE
)

def parse_task_filename(name: str) -> TaskFileMeta:
    m = TASK_FILE_REGEX.match(name)
    if m:
        return TaskFileMeta(
            step_index=int(m.group("step")),
            batch_index=int(m.group("batch")),
            gnc_name=name
        )
    return TaskFileMeta(step_index=None, batch_index=None, gnc_name=name)
```

---

## TDD: Тесты

```python
def test_is_variant_aut_file():
    assert is_variant(Path("12-06-SIDRA-353203_AUT.TXT")) is True

def test_is_variant_dsp_file():
    assert is_variant(Path("layout.Dsp")) is True

def test_is_variant_main_gnc():
    assert is_variant(Path("12-06-SIDRA-353203-...-3.GNC")) is False

def test_parse_step_batch_index():
    meta = parse_task_filename("12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC")
    assert meta.step_index == 12
    assert meta.batch_index == 6

def test_parse_filename_fallback():
    meta = parse_task_filename("unknown_file.GNC")
    assert meta.step_index is None
    assert meta.batch_index is None
```

---

## Definition of Done

```
✓ is_variant() правильно фильтрует из data_sample/
✓ Все реальные GNC файлы прошли как non-variant
✓ step_index/batch_index парсятся из именованных файлов
✓ Graceful fallback (None) для нестандартных имён
```
