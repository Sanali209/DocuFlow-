import pytest
import json
from pathlib import Path
from docuflow.infrastructure import constants
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config

@pytest.fixture
def bus_config(tmp_path):
    """Fixture for file bus testing with a temporary directory."""
    shared_path = tmp_path / "shared"
    shared_path.mkdir()
    (shared_path / "BUS").mkdir()
    (shared_path / "BUS" / "INBOX").mkdir()
    (shared_path / "BUS" / "OUTBOX").mkdir()
    
    return Config(
        node_id="TEST_NODE",
        shared_path=str(shared_path)
    )

@pytest.mark.anyio
async def test_file_bus_send_request(bus_config):
    """Test that send_request creates a correctly named file atomically."""
    bus = FileBusSystem(config=bus_config)
    
    req_id = await bus.send_request(
        target_id="COORD",
        command="PING",
        data={"hello": "world"}
    )
    
    # Check that the file exists in INBOX
    inbox_path = Path(bus_config.shared_path) / "BUS" / "INBOX"
    expected_filename = f"REQ_TEST_NODE_COORD_{req_id}.json"
    file_path = inbox_path / expected_filename
    
    assert file_path.exists()
    
    # Verify content
    with open(file_path, "r") as f:
        msg = json.load(f)
        assert msg["header"]["from"] == "TEST_NODE"
        assert msg["header"]["to"] == "COORD"
        assert msg["header"]["cmd"] == "PING"
        assert msg["body"]["hello"] == "world"

@pytest.mark.anyio
async def test_file_bus_poll_inbox(bus_config):
    """Test that poll_messages identifies requests for the current node."""
    bus = FileBusSystem(config=bus_config)
    inbox_path = Path(bus_config.shared_path) / "BUS" / "INBOX"
    
    # Create a request file for TEST_NODE
    req_filename = "REQ_OTHER_TEST_NODE_12345.json"
    req_path = inbox_path / req_filename
    payload = {
        "header": {"from": "OTHER", "to": "TEST_NODE", "id": "12345", "cmd": "TEST"},
        "body": {}
    }
    with open(req_path, "w") as f:
        json.dump(payload, f)
        
    # Create a request file for another node (should be ignored)
    other_req_path = inbox_path / "REQ_OTHER_WRONG_12346.json"
    with open(other_req_path, "w") as f:
        json.dump({"header": {"to": "WRONG"}}, f)

    messages = await bus.poll_messages(folder="INBOX")
    
    assert len(messages) == 1
    assert messages[0]["header"]["id"] == "12345"
    assert messages[0]["_filename"] == req_filename

@pytest.mark.anyio
async def test_file_bus_write_message_for_broadcast(bus_config):
    """Critical path: orchestrator broadcast must be persisted via FileBus.write_message."""
    bus = FileBusSystem(config=bus_config)
    payload = {
        "sender_id": "TEST_NODE",
        "sequence": 1,
        "timestamp": 123.0,
        "payload": {"command": "PING", "data": {"ok": True}},
        "signature": "sig",
    }

    await bus.write_message(payload)

    inbox_path = Path(bus_config.shared_path) / "BUS" / "INBOX"
    files = sorted(inbox_path.glob("*.json"))
    assert len(files) == 1
    assert files[0].name.startswith(constants.BUS_PREFIX_BROADCAST)

    with open(files[0], "r", encoding="utf-8") as f:
        stored = json.load(f)
    assert stored["sender_id"] == "TEST_NODE"
    assert stored["payload"]["command"] == "PING"

    messages = await bus.poll_messages(folder="INBOX")
    assert len(messages) == 1
    assert messages[0]["payload"]["command"] == "PING"
