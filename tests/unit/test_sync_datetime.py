import datetime
from unittest.mock import MagicMock

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
    """ISO 8601 strings in datetime-typed fields must be parsed to datetime objects."""
    from docuflow.domain.entities.identity import NodeSetting

    sync = make_sync(tmp_path)
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    iso_str = "2024-01-15T10:30:00"
    row_data = {
        "node_id": "STATION_A",
        "module": "CONFIG",
        "key": "last_sync",
        "value": "true",
        "updated_at": iso_str,
    }
    with Session(engine) as session:
        sync._process_remote_row(session, NodeSetting, row_data, ["id"])
        result = session.exec(select(NodeSetting)).first()
        assert result is not None
        assert isinstance(result.updated_at, datetime.datetime), (
            "ISO 8601 datetime string must be parsed to datetime"
        )
        assert result.updated_at == datetime.datetime.fromisoformat(iso_str), (
            "parsed datetime must match the original ISO string"
        )


def test_status_change_not_corrupted(tmp_path):
    """'STATUS_CHANGE' contains 'T' — must not be corrupted by datetime parsing."""
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
        assert result is not None
        assert result.module == "STATUS_CHANGE", (
            "'STATUS_CHANGE' must not be altered by datetime detection"
        )
