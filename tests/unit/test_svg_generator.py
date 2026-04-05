from pathlib import Path
import pytest

# Skip tests that require large data samples if the data_sample directory is not present
repo_root = Path(__file__).parent.parent.parent
if not (repo_root / "data_sample").exists():
    pytest.skip("data_sample not available; skipping GNC/SVG generator tests", allow_module_level=True)

from docuflow.features.folder_scanner.parsers.gnc import GncParser
from docuflow.features.folder_scanner.parsers.svg_gen import PartPreviewGenerator


def test_gnc_parser_collects_contours():
    """Verify that GncParser now collects contour data."""
    repo_root = Path(__file__).parent.parent.parent
    gnc_file = (
        repo_root
        / "data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025/12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC"
    )

    parser = GncParser()
    sheet = parser.parse(gnc_file)

    assert len(sheet.parts) > 0
    # Check first part
    part = sheet.parts[0]
    assert len(part.contours) > 0
    assert len(part.contours[0].commands) > 0

    # Check if commands have coordinates
    cmd = part.contours[0].commands[0]
    # In GNC, the first command of a contour is usually a move (G00 or G01)
    assert cmd.x is not None or cmd.y is not None


def test_generate_thumbnail_real_file(tmp_path):
    """Verify that PartPreviewGenerator creates a valid SVG and returns bbox."""
    repo_root = Path(__file__).parent.parent.parent
    gnc_file = (
        repo_root
        / "data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025/12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC"
    )

    parser = GncParser()
    sheet = parser.parse(gnc_file)
    part = sheet.parts[0]

    # Setup generator with temp output dir
    previews_dir = tmp_path / "previews"
    gen = PartPreviewGenerator(output_dir=previews_dir)

    bbox_x, bbox_y, rel_path = gen.generate(part, sku="TEST-SKU-1")

    assert bbox_x is not None and bbox_x > 0
    assert bbox_y is not None and bbox_y > 0
    assert rel_path == "TEST-SKU-1.svg"

    full_path = previews_dir / rel_path
    assert full_path.exists()

    # Check SVG content basic structure
    content = full_path.read_text()
    assert "<svg" in content
    assert "<path" in content
    assert 'stroke="#38bdf8"' in content  # Our premium color


def test_generate_graceful_fallback(tmp_path):
    """Verify that bad data doesn't crash the generator."""
    from docuflow.features.folder_scanner.parsers.gnc import GncPartData

    bad_part = GncPartData(sku="BAD", contours=[])
    gen = PartPreviewGenerator(output_dir=tmp_path)

    bbox_x, bbox_y, rel_path = gen.generate(bad_part, sku="BAD-SKU")

    # Should return None for data that generates 0x0 bbox
    assert bbox_x is None
    assert bbox_y is None
    assert rel_path is None
