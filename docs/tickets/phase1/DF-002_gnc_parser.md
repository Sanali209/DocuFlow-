# DF-002: GncParser (адаптация из MVP)

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🔴 CRITICAL |
| **Status** | TODO |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md) |
| **Блокирует** | [DF-006](./DF-006_folder_scanner_system.md) |
| **MVP источник** | `old mvp/backend/src/infrastructure/graphics/gnc_parser.py` |
| **Архитектура** | [02_application_architecture.md §4.4](../architecture/02_application_architecture.md) |
| **Data Flow** | [03_data_flow.md §2](../architecture/03_data_flow.md) |

---

## Контекст

GNC файл — единственный источник данных о нестах. Парсер должен извлечь:
1. **Материал и параметры листа** (из `*SHEET` и `Material:`)
2. **Список деталей** (из `PART NAME:`) → SKU extraction
3. **Метрики контуров** (contour_count, hole_count, corner_count) — для PartLibrary и поиска
4. **Оценку времени** (estimate_time) — используя параметры MaterialType

Из MVP берём и **адаптируем**: добавляем PART NAME парсинг, SKU extraction, estimate_time.

---

## Execution Plan

```
1. Скопировать gnc_parser.py из old MVP в features/folder_scanner/parsers/gnc.py
2. Написать тесты на реальных файлах data_sample/ (TDD сначала)
3. Адаптировать: добавить PART NAME parsing → extract_sku()
4. Добавить idle path parsing (G00 команды → idle_length_mm)
5. Добавить estimate_time(mat_type) метод
6. Интегрировать с SVGGenerator (вызов из DF-005)
7. Убедиться в graceful fallback для каждого поля
```

---

## Подзадачи

- [x] Скопировать MVP GncParser в `src/docuflow/features/folder_scanner/parsers/gnc.py`
- [x] Добавить парсинг `(PART NAME:...)`:
  - [x] Извлечь raw part name строку
  - [x] Вызвать `extract_sku(raw)` → `(sku: str, version: str)`
- [x] Реализовать `extract_sku(raw: str) -> tuple[str, str]`:
  - [x] Strip path+ext: `raw.strip().split("\\")[-1]` → убрать расширение
  - [x] Split by `-`
  - [x] Если последний сегмент — цифра (напр. `1` в `...-G-1`) → ОТРЕЗАТЬ (это лишнее)
  - [x] Предпоследний сегмент (теперь последний) — это ВЕРСИЯ (напр. `G`, `A`, `B`)
  - [x] Остальное — это SKU (напр. `3433-11-004`)
  - [x] Пример: `3433-11-004-G-1` → SKU: `3433-11-004`, Version: `G`
  - [x] Пример: `PART-ABC-1` → SKU: `PART`, Version: `ABC` (или `A` если не вписывается в паттерн — обсудить)
  - [x] version = `A` если нет суффиксов.
- [x] Добавить парсинг `(*SHEET x y thickness cut_count batch_idx ...)`:
  - [x] sheet_x, sheet_y, thickness, sheet_qty (= cut_count)
- [x] Добавить парсинг `(Material:...)` → MaterialType.code
- [x] Добавить парсинг `(DATE ...)` → gnc_date (parse `JUL 07 2025`)
- [x] Сохранять `contour_count`, `hole_count`, `corner_count` (из MVP — уже есть)
- [x] Парсинг G00 команд → `idle_length_mm` (для estimate_time)
- [x] Парсинг G-код путей → `cut_length_mm` (суммарный путь резки)
- [x] Реализовать `estimate_time(mat_type: MaterialType) -> int` (минуты):
  - pierce = contour_count × mat_type.pierce_time_sec
  - cut = cut_length_mm / mat_type.cut_speed_mm_per_min × 60
  - idle = idle_length_mm / mat_type.idle_speed_mm_per_min × 60
  - base = (pierce + cut + idle) × sheet_qty / 60 (в минутах)
  - return int(base × (1 + mat_type.time_tolerance_pct / 100))
- [x] Graceful fallback: все поля Optional → если не распарсилось → None
- [x] Интеграция с SVGGenerator: `GncParser.get_part_data(sku)` → передаётся в DF-005

---

## Псевдокод

```python
# features/folder_scanner/parsers/gnc.py

class GncPartData:
    """Данные об одной детали из GNC файла."""
    sku: str            # "3433-11-004-G"
    version: str        # "1" (digit suffix, не используется для идентификации)
    qty: int            # кол-во в нестe
    contours: List      # сырые данные контуров для SVGGenerator

class GncSheet:
    """Результат парсинга одного GNC файла."""
    # Параметры листа
    sheet_x: Optional[float]     # из *SHEET
    sheet_y: Optional[float]
    thickness: Optional[float]
    sheet_qty: Optional[int]
    gnc_date: Optional[date]
    mat_code: Optional[str]      # "AA 5052-H32"
    
    # Метрики для estimate_time
    cut_length_mm: float = 0.0   # суммарный путь G01/G02/G03
    idle_length_mm: float = 0.0  # суммарный путь G00
    
    # Детали
    parts: List[GncPartData]     # один или несколько PART NAME

class GncParser:
    def parse(self, file_path: Path) -> GncSheet:
        """
        Парсит GNC файл. Возвращает GncSheet.
        При ошибке любого поля → graceful fallback (None, не raise).
        """
        ...
    
    @staticmethod
    def extract_sku(raw: str) -> tuple[str, str]:
        """
        "3433-11-004-G-1 " → ("3433-11-004", "G")
        "3455-20-001-B-2"  → ("3455-20-001", "B")
        "PART-ABC-1"       → ("PART", "ABC")  # Или предусмотреть дефолт
        """
        name = raw.strip().split("\\")[-1]          # убрать путь
        name = re.sub(r'\.\w+$', '', name).strip()   # убрать расширение
        parts = name.split("-")
        
        # 1. Отрезаем не значащую цифру в конце, если она есть
        if len(parts) > 1 and parts[-1].isdigit():
            parts.pop()
            
        # 2. Последний оставшийся сегмент - это версия
        if len(parts) > 1:
            version = parts.pop()
            sku = "-".join(parts)
            return sku, version
            
        return name, "A"
    
    def estimate_time(self, mat_type: MaterialType) -> int:
        """
        Оценка времени резки (минуты) с допуском.
        Использует параметры mat_type (cut_speed, pierce_time, ...).
        """
        pierce = self.sheet.total_contours * mat_type.pierce_time_sec
        cut    = (self.sheet.cut_length_mm / mat_type.cut_speed_mm_per_min) * 60
        idle   = (self.sheet.idle_length_mm / mat_type.idle_speed_mm_per_min) * 60
        base   = (pierce + cut + idle) * (self.sheet.sheet_qty or 1) / 60
        return int(base * (1 + mat_type.time_tolerance_pct / 100))
```

---

## Тестовые данные

Файл: `data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025/12-06-...-AA 5052-H32-3.GNC`

```
Ожидаемый результат парсинга:
  sheet_x   = 3250.0
  sheet_y   = 1250.0
  thickness  = 3.0
  sheet_qty  = 7
  mat_code   = "AA 5052-H32"
  gnc_date   = date(2025, 7, 7)
  parts[0].sku     = "3433-11-004"
  parts[0].version = "G"
```

---

## TDD: Тесты написать ПЕРВЫМИ

Файл: `tests/unit/domain/test_gnc_parser.py`

```python
import pytest
from pathlib import Path
from docuflow.features.folder_scanner.parsers.gnc import GncParser

SAMPLE_GNC = Path("data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025")

def test_extract_sku_with_version_and_meaningless_digit():
    sku, ver = GncParser.extract_sku("3433-11-004-G-1 ")
    assert sku == "3433-11-004"
    assert ver == "G"

def test_extract_sku_no_meaningless_digit():
    sku, ver = GncParser.extract_sku("3433-11-004-A")
    assert sku == "3433-11-004"
    assert ver == "A"

def test_extract_sku_with_path():
    sku, ver = GncParser.extract_sku("\\\\server\\parts\\3433-11-004-G-1.dft")
    assert sku == "3433-11-004"
    assert ver == "G"

def test_parse_sheet_params():
    gnc_file = next(SAMPLE_GNC.glob("*.GNC"))
    parser = GncParser()
    sheet = parser.parse(gnc_file)
    assert sheet.sheet_x == 3250.0
    assert sheet.sheet_y == 1250.0
    assert sheet.thickness == 3.0
    assert sheet.sheet_qty == 7

def test_parse_material_code():
    gnc_file = next(SAMPLE_GNC.glob("*.GNC"))
    sheet = GncParser().parse(gnc_file)
    assert sheet.mat_code == "AA 5052-H32"

def test_parse_part_sku():
    gnc_file = next(SAMPLE_GNC.glob("*.GNC"))
    sheet = GncParser().parse(gnc_file)
    assert len(sheet.parts) >= 1
    assert sheet.parts[0].sku == "3433-11-004"
    assert sheet.parts[0].version == "G"

def test_estimate_time_returns_positive():
    from docuflow.domain.entities.production import MaterialType
    mat = MaterialType(code="TEST", cut_speed_mm_per_min=3000.0,
                       pierce_time_sec=3.0, idle_speed_mm_per_min=10000.0,
                       time_tolerance_pct=15.0)
    gnc_file = next(SAMPLE_GNC.glob("*.GNC"))
    sheet = GncParser().parse(gnc_file)
    minutes = GncParser().estimate_time(mat)
    assert minutes > 0

def test_graceful_fallback_on_bad_file(tmp_path):
    """Плохой файл не должен вызывать исключение."""
    bad_file = tmp_path / "bad.GNC"
    bad_file.write_text("(GARBAGE DATA)")
    sheet = GncParser().parse(bad_file)
    assert sheet is not None
    assert sheet.sheet_x is None   # graceful
    assert sheet.parts == []
```

---

## Definition of Done (Gate)

```
✓ Все тесты в test_gnc_parser.py проходят (pytest)
✓ parse() реального файла из data_sample/ даёт правильные значения
✓ extract_sku() корректно обрабатывает path+ext+version+ignore_digit
✓ estimate_time() возвращает > 0 для реального файла
✓ Плохой файл → graceful fallback (нет raise, нет краша)
✓ mat_code нормализован (strip, lowercase?) — согласован с MaterialType.code
```
