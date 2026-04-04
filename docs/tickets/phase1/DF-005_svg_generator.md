# DF-005: SVGGenerator интеграция

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | 1 |
| **Priority** | 🟡 HIGH |
| **Зависит от** | [DF-001](./DF-001_domain_entities.md) |
| **Блокирует** | [DF-006](./DF-006_folder_scanner_system.md), [DF-019](../phase3/DF-019_part_library_system.md) |
| **MVP источник** | `old mvp/backend/src/infrastructure/graphics/svg_generator.py` |

---

## Контекст

SVGGenerator из MVP умеет:
- `calculate_bounds(part)` → `(min_x, min_y, max_x, max_y)` — реальный bbox детали из G-кода
- `generate_thumbnail(part, path)` → `(data_w, data_h)` — ширина и высота в мм + SVG файл

Это критично потому что `PART SIZE` в GNC = bbox **всего нестa**, не отдельной детали. Реальный bbox нужен для поиска по размерам в PartLibrary.

---

## Подзадачи

- [x] Скопировать SVGGenerator из MVP: `lib/svg_generator.py` или `features/folder_scanner/parsers/svg_gen.py`
- [x] Создать wrapper/adapter `PartPreviewGenerator`:
  - `generate(part_data: GncPartData, sku: str, output_dir: Path) -> tuple[float, float, str]`
  - Возвращает: `(bbox_x_mm, bbox_y_mm, svg_preview_path)`
- [x] Интеграция с GncParser: при парсинге PART NAME → вызов SVGGenerator для bbox
- [x] Хранение SVG: `{data_dir}/previews/{sku}.svg` (relative path в PartLibrary)
- [x] Graceful fallback: если SVG генерация падает → bbox = None, svg = None
- [x] Тест: проверить что generate_thumbnail возвращает реальные мм (не нулевые)

---

## Псевдокод

```python
# lib/svg_generator.py — перенесён из MVP

class PartPreviewGenerator:
    """
    Wrapper над SVGGenerator из MVP.
    Генерирует SVG превью детали и возвращает реальный bbox из G-кода.
    """
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, part_data: "GncPartData", sku: str
                 ) -> tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Returns: (bbox_x_mm, bbox_y_mm, svg_relative_path)
        При ошибке: (None, None, None)
        """
        try:
            svg_gen = SVGGenerator()
            output_path = self.output_dir / f"{sku}.svg"
            data_w, data_h = svg_gen.generate_thumbnail(
                part=part_data.contours,
                output_path=str(output_path)
            )
            return data_w, data_h, str(output_path)
        except Exception as e:
            logger.warning(f"SVG generation failed for {sku}: {e}")
            return None, None, None
```

---

## TDD: Тесты

```python
def test_generate_thumbnail_real_file(tmp_path):
    """Проверяем что generate_thumbnail возвращает реальные мм."""
    gnc_file = Path("data_sample/sidra/SIDRA-353203-.../12-06-...-3.GNC")
    sheet = GncParser().parse(gnc_file)
    gen = PartPreviewGenerator(output_dir=tmp_path / "previews")
    
    bbox_x, bbox_y, svg_path = gen.generate(sheet.parts[0], sku="3433-11-004-G")
    
    assert bbox_x is not None and bbox_x > 0
    assert bbox_y is not None and bbox_y > 0
    assert svg_path is not None and Path(svg_path).exists()

def test_generate_graceful_fallback_on_empty_part(tmp_path):
    """Пустые данные контуров не должны вызывать crash."""
    from unittest.mock import MagicMock
    bad_part = MagicMock()
    bad_part.contours = []
    gen = PartPreviewGenerator(output_dir=tmp_path)
    bbox_x, bbox_y, svg_path = gen.generate(bad_part, "TEST-SKU")
    # Либо данные, либо все None — не raise
    assert (bbox_x is None) or (bbox_x > 0)
```

---

## Definition of Done

```
✓ SVGGenerator перенесён и работает
✓ generate() на реальном GNC файле возвращает bbox_x > 0, bbox_y > 0
✓ SVG файл создаётся физически
✓ Graceful fallback при ошибке (не raise)
✓ Путь к SVG хранится как relative (не абсолютный)
```
