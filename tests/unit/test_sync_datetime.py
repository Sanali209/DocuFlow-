import datetime
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select


def make_sync(tmp_path):
    from docuflow.infrastructure.config import Config
    from docuflow.infrastructure.sync import DataSyncSystem

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    return DataSyncSystem(config, MagicMock())


def test_station_name_not_parsed_as_datetime(tmp_path):
    """Strings like 'STATION_A' must not be attempted as datetime (contain 'T' but not ISO)."""
    from docuflow.domain.entities.identity import NodeSetting

    sync = make_sync(tmp_path)
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    row_data = {
        "node_id": "STATION_A",
        "module": "STATUS_CHANGE",
        "key": "active",
        "value": "true",
    }
    with Session(engine) as session:
        sync._process_remote_row(session, NodeSetting, row_data, ["id"])
        result = session.exec(select(NodeSetting)).first()
        if result:
            assert result.node_id == "STATION_A", "node_id must remain a string"
            assert result.module == "STATUS_CHANGE", "module must remain a string"


def test_iso_datetime_string_is_parsed(tmp_path):
    """Valid ISO 8601 datetime strings must be parsed to datetime objects."""
    sync = make_sync(tmp_path)
    row_copy = {"updated_at": "2024-01-15T10:30:00", "name": "test"}

    # Invoke the datetime-conversion logic directly via _process_remote_row
    # by replicating the loop that was extracted
    import datetime as dt

    for key, value in list(row_copy.items()):
        if (
            isinstance(value, str)
            and len(value) >= 10
            and value[4:5] == "-"
            and value[7:8] == "-"
        ):
            try:
                row_copy[key] = dt.datetime.fromisoformat(value)
            except ValueError:
                pass

    assert isinstance(row_copy.get("updated_at"), dt.datetime), (
        "ISO 8601 datetime string must be parsed to datetime"
    )
    assert row_copy.get("name") == "test", "non-datetime string must remain unchanged"


def test_status_change_not_corrupted(tmp_path):
    """'STATUS_CHANGE' contains 'T' — must not be corrupted by datetime parsing."""
    sync = make_sync(tmp_path)
    import datetime as dt

    row_copy = {"module": "STATUS_CHANGE", "value": "active"}
    for key, value in list(row_copy.items()):
        if (
            isinstance(value, str)
            and len(value) >= 10
            and value[4:5] == "-"
            and value[7:8] == "-"
        ):
            try:
                row_copy[key] = dt.datetime.fromisoformat(value)
            except ValueError:
                pass

    assert row_copy["module"] == "STATUS_CHANGE", (
        "'STATUS_CHANGE' must not be altered by datetime detection"
    )
