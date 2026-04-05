from datetime import date

from docuflow.domain.entities.production import WorkItemType
from docuflow.features.folder_scanner.parsers.folder import FolderNameParser


def test_parse_sidra_standard():
    parser = FolderNameParser()
    meta = parser.parse("SIDRA-353203-SHLAV-2-07.07.2025")
    assert meta.work_item_type == WorkItemType.SIDRA
    assert meta.sidra_number == "353203"
    assert meta.sidra_step == "SHLAV-2"
    assert meta.project_hint == "SHLAV-2"
    assert meta.doc_date == date(2025, 7, 7)


def test_parse_sidra_case_insensitive():
    parser = FolderNameParser()
    meta = parser.parse("sidra-123456-STEP-1-01.01.2026")
    assert meta.work_item_type == WorkItemType.SIDRA
    assert meta.sidra_number == "123456"
    assert meta.doc_date == date(2026, 1, 1)


def test_parse_rework_detection():
    parser = FolderNameParser()
    # Case 1: REWORK at start
    meta1 = parser.parse("REWORK-353203-SHLAV-2")
    assert meta1.work_item_type == WorkItemType.REWORK
    # Case 2: REWORK in middle
    meta2 = parser.parse("Some-REWORK-Folder")
    assert meta2.work_item_type == WorkItemType.REWORK


def test_parse_mihtav_fallback():
    parser = FolderNameParser()
    # Case 1: Random name
    meta1 = parser.parse("Hand-Written-Order-123")
    assert meta1.work_item_type == WorkItemType.MIHTAV
    assert meta1.sidra_number is None
    # Case 2: Empty string
    meta2 = parser.parse("")
    assert meta2.work_item_type == WorkItemType.MIHTAV


def test_parse_sidra_invalid_date_fallback():
    parser = FolderNameParser()
    # Date looks right but is invalid (e.g., Feb 30)
    meta = parser.parse("SIDRA-123456-STEP-30.02.2025")
    # Should fallback to MIHTAV rather than crashing
    assert meta.work_item_type == WorkItemType.MIHTAV
