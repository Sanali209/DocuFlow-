from docuflow.infrastructure import constants
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config


def make_bus(node_id: str, tmp_path) -> FileBusSystem:
    config = Config(node_id=node_id, shared_path=str(tmp_path))
    return FileBusSystem(config)


def test_node_id_not_false_positive_substring(tmp_path):
    """node_id 'A' must not match a filename addressed to 'STATION_A'."""
    bus = make_bus("A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}SENDER"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}001{constants.BUS_EXTENSION}"
    )
    result = bus._is_relevant_message(filename, constants.BUS_INBOX_DIR)
    assert result is False, "node_id 'A' must not match 'STATION_A'"


def test_node_id_exact_match(tmp_path):
    """Exact node_id match must return True."""
    bus = make_bus("STATION_A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}SENDER"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}001{constants.BUS_EXTENSION}"
    )
    result = bus._is_relevant_message(filename, constants.BUS_INBOX_DIR)
    assert result is True


def test_broadcast_message_always_relevant_in_inbox(tmp_path):
    """Broadcast messages must always be relevant in inbox regardless of node_id."""
    bus = make_bus("ANY_NODE", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_BROADCAST}SENDER"
        f"{constants.BUS_DELIMITER}001{constants.BUS_EXTENSION}"
    )
    result = bus._is_relevant_message(filename, constants.BUS_INBOX_DIR)
    assert result is True


def test_outbox_res_message_exact_match(tmp_path):
    """RES_ messages in OUTBOX must match exact node_id in TO field."""
    bus = make_bus("NODE_B", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_RES}SENDER"
        f"{constants.BUS_DELIMITER}NODE_B"
        f"{constants.BUS_DELIMITER}001{constants.BUS_EXTENSION}"
    )
    result = bus._is_relevant_message(filename, constants.BUS_OUTBOX_DIR)
    assert result is True


def test_outbox_res_message_no_false_positive(tmp_path):
    """RES_ message addressed to 'NODE_BB' must not match node_id 'B'."""
    bus = make_bus("B", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_RES}SENDER"
        f"{constants.BUS_DELIMITER}NODE_BB"
        f"{constants.BUS_DELIMITER}001{constants.BUS_EXTENSION}"
    )
    result = bus._is_relevant_message(filename, constants.BUS_OUTBOX_DIR)
    assert result is False, "node_id 'B' must not match 'NODE_BB'"
