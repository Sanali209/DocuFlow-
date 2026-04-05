from pathlib import Path

from docuflow.domain.entities.production import MaterialType
from docuflow.features.folder_scanner.parsers.gnc import GncParser

# Path to the sample data as defined in the project structure
SAMPLE_GNC_DIR = Path("data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025")


def test_extract_sku_revised_logic():
    """
    Verifies the corrected SKU extraction logic:
    '3433-11-004-G-1' -> SKU='3433-11-004', Version='G', ignore '1'
    """
    # 1. Standard Case
    sku, ver = GncParser.extract_sku("3433-11-004-G-1")
    assert sku == "3433-11-004"
    assert ver == "G"

    # 2. Case without digit suffix
    sku, ver = GncParser.extract_sku("3455-20-001-B")
    assert sku == "3455-20-001"
    assert ver == "B"

    # 3. Path and extension
    sku, ver = GncParser.extract_sku(r"C:\parts\3433-11-004-G-1.dft")
    assert sku == "3433-11-004"
    assert ver == "G"


def test_parse_real_gnc_file():
    """
    Parses a real file from the data_sample directory.
    Uses a specific file to ensure consistent expectations.
    """
    gnc_file = SAMPLE_GNC_DIR / "11-01-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC"
    parser = GncParser()
    sheet = parser.parse(gnc_file)

    # Check Sheet Params (from (*SHEET 2500.0 1250.0 3.0 7 1...))
    assert sheet.sheet_x == 2500.0
    assert sheet.sheet_y == 1250.0
    assert sheet.thickness == 3.0
    assert sheet.sheet_qty == 7

    # Check Material (from (Material:AA 5052-H32))
    assert sheet.mat_code == "AA 5052-H32"

    # Check Date (from (DATE JUL 10 2025))
    assert sheet.gnc_date is not None
    assert sheet.gnc_date.year == 2025
    assert sheet.gnc_date.month == 7

    # Check Parts
    # (PART NAME:3455-20-001-B-1 ) -> SKU=3455-20-001, Version=B
    assert len(sheet.parts) >= 1
    assert any(p.sku == "3455-20-001" and p.version == "B" for p in sheet.parts)


def test_estimate_time_logic():
    """
    Verifies that time estimation returns a reasonable value.
    """
    mat = MaterialType(
        code="AA 5052-H32",
        cut_speed_mm_per_min=3000.0,
        pierce_time_sec=3.0,
        idle_speed_mm_per_min=10000.0,
        time_tolerance_pct=15.0,
    )

    gnc_file = next(SAMPLE_GNC_DIR.glob("*.GNC"))
    parser = GncParser()
    sheet = parser.parse(gnc_file)

    # We should have some path lengths extracted
    assert sheet.cut_length_mm > 0
    assert sheet.idle_length_mm > 0

    minutes = parser.estimate_time(sheet, mat)
    assert minutes > 0
    assert isinstance(minutes, int)


def test_graceful_fallback(tmp_path):
    """
    Bad files should not crash the scanner.
    """
    bad_file = tmp_path / "corrupt.GNC"
    bad_file.write_text("NOT A GNC FILE\n(GARBAGE)")

    parser = GncParser()
    sheet = parser.parse(bad_file)

    assert sheet is not None
    assert sheet.parts == []
    assert sheet.sheet_x is None
