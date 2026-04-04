import pytest
from pathlib import Path
from docuflow.features.folder_scanner.parsers.task_file import TaskFileParser

def test_is_variant_aut_file():
    parser = TaskFileParser()
    assert parser.is_variant(Path("12-06-SIDRA-353203_AUT.TXT")) is True
    # Even if it has .GNC suffix but contains _AUT
    assert parser.is_variant(Path("11-01-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3_AUT.GNC")) is True

def test_is_variant_dsp_file():
    parser = TaskFileParser()
    assert parser.is_variant(Path("layout.Dsp")) is True
    assert parser.is_variant(Path("SIDRA-353203-SHLAV-2-07.07.2025.Dsp")) is True

def test_is_variant_main_gnc():
    parser = TaskFileParser()
    # Standard GNC should NOT be a variant
    assert parser.is_variant(Path("01-01-SIDRA-353203-SHLAV-2-07.07.2025-ST 37-2-4.GNC")) is False
    assert parser.is_variant(Path("unknown_order.GNC")) is False

def test_is_variant_other_files():
    parser = TaskFileParser()
    assert parser.is_variant(Path("SIDRA-353203.doc")) is True
    assert parser.is_variant(Path("README.md")) is True

def test_parse_step_batch_index():
    parser = TaskFileParser()
    meta = parser.parse_task_filename("12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC")
    assert meta.step_index == 12
    assert meta.batch_index == 6
    assert meta.gnc_name == "12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC"

def test_parse_filename_fallback():
    parser = TaskFileParser()
    meta = parser.parse_task_filename("unknown_file.GNC")
    assert meta.step_index is None
    assert meta.batch_index is None
    assert meta.gnc_name == "unknown_file.GNC"
