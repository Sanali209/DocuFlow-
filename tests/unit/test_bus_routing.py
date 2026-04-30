"""Tests for FileBusSystem._is_relevant_message routing logic.

Note on delimiter ambiguity: BUS_DELIMITER is "_" and real node IDs like
"STATION_A" contain underscores. Routing is based on the TO field being at
the end of the filename stem (after the numeric ID is removed). This is
reliable for all real node IDs as long as no node ID is a trailing-underscore
suffix of another node's ID (e.g. avoid having both "A" and "STATION_A").
"""
from docuflow.infrastructure import constants
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config


def make_bus(node_id: str, tmp_path) -> FileBusSystem:
    config = Config(node_id=node_id, shared_path=str(tmp_path))
    return FileBusSystem(config)


def test_node_id_exact_match_simple_sender(tmp_path):
    """STATION_A correctly receives messages from a simple-named sender."""
    bus = make_bus("STATION_A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}SENDER"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_INBOX_DIR) is True


def test_node_id_exact_match_both_with_underscores(tmp_path):
    """STATION_A correctly receives messages from STATION_B (both have underscores)."""
    bus = make_bus("STATION_A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}STATION_B"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_INBOX_DIR) is True


def test_node_id_does_not_match_different_node(tmp_path):
    """STATION_C does not receive messages addressed to STATION_A."""
    bus = make_bus("STATION_C", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}STATION_B"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_INBOX_DIR) is False


def test_broadcast_message_always_relevant_in_inbox(tmp_path):
    """Broadcast messages are always relevant in inbox regardless of node_id."""
    bus = make_bus("ANY_NODE", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_BROADCAST}SENDER"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_INBOX_DIR) is True


def test_outbox_res_message_exact_match(tmp_path):
    """RES_ messages in OUTBOX match exact node_id in TO field."""
    bus = make_bus("STATION_B", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_RES}STATION_A"
        f"{constants.BUS_DELIMITER}STATION_B"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_OUTBOX_DIR) is True


def test_outbox_res_message_no_match_wrong_node(tmp_path):
    """RES_ message addressed to STATION_B must not match STATION_A."""
    bus = make_bus("STATION_A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_RES}SENDER"
        f"{constants.BUS_DELIMITER}STATION_B"
        f"{constants.BUS_DELIMITER}1746000000001{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_OUTBOX_DIR) is False


def test_non_numeric_id_rejected(tmp_path):
    """Filenames with non-numeric IDs are rejected as malformed."""
    bus = make_bus("STATION_A", tmp_path)
    filename = (
        f"{constants.BUS_PREFIX_REQ}SENDER"
        f"{constants.BUS_DELIMITER}STATION_A"
        f"{constants.BUS_DELIMITER}abc{constants.BUS_EXTENSION}"
    )
    assert bus._is_relevant_message(filename, constants.BUS_INBOX_DIR) is False
