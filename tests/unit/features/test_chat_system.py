import pytest
import os
import shutil
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine, select
from docuflow.features.chat.system import ChatSystem
from docuflow.domain.entities.production import (
    ChatMessage, 
    ChatMessageType,
    Project,
    WorkItem
)
from docuflow.infrastructure.config import Config

@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "chat_data"
    d.mkdir()
    return d

@pytest.fixture
def config(temp_dir):
    return Config(node_id="test_node", shared_path=str(temp_dir))

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def chat_system(config, session: Session):
    return ChatSystem(config, db_session=session)

def test_send_global_message(chat_system: ChatSystem, session: Session):
    msg = chat_system.send_message(author="user1", content="Hello world")
    assert msg.id is not None
    assert msg.author == "user1"
    assert msg.ref_project_id is None
    
    globals = chat_system.get_global_messages()
    assert len(globals) == 1
    assert globals[0].content == "Hello world"

def test_send_with_context(chat_system: ChatSystem, session: Session):
    # Context
    p = Project(name="P-01")
    session.add(p)
    session.flush()
    
    msg = chat_system.send_message(author="admin", content="Start project", ref_project_id=p.id)
    assert msg.ref_project_id == p.id
    
    context_msgs = chat_system.get_context_thread("project", p.id)
    assert len(context_msgs) == 1
    assert context_msgs[0].content == "Start project"

def test_reply_inheritance(chat_system: ChatSystem, session: Session):
    parent = chat_system.send_message(author="boss", content="Urgent task", ref_work_item_id=123)
    
    # Reply without explicit context should inherit from parent
    child = chat_system.reply(parent.id, author="worker", content="Understood")
    
    assert child.parent_message_id == parent.id
    assert child.ref_work_item_id == 123
    assert child.ref_project_id is None

def test_get_thread_recursive(chat_system: ChatSystem, session: Session):
    root = chat_system.send_message("u1", "Root")
    c1 = chat_system.reply(root.id, "u2", "C1")
    c2 = chat_system.reply(root.id, "u3", "C2")
    c11 = chat_system.reply(c1.id, "u1", "C1.1")
    
    thread = chat_system.get_recursive_thread(root.id)
    assert len(thread) == 4
    # Check hierarchy logic indirectly via count
    contents = [m.content for m in thread]
    assert "Root" in contents
    assert "C1.1" in contents

def test_attach_file_persistence(chat_system: ChatSystem, session: Session):
    msg = chat_system.send_message("u1", "See attachment")
    file_bytes = b"FAKE PDF DATA"
    filename = "spec.pdf"
    
    file_path = chat_system.attach_file(msg.id, filename, file_bytes)
    
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == file_bytes
        
    # Check metadata
    session.refresh(msg)
    import json
    attachments = json.loads(msg.attachments)
    assert len(attachments) == 1
    assert attachments[0]["name"] == filename

def test_send_convenience_methods(chat_system: ChatSystem, session: Session):
    order = chat_system.broadcast_order_request(work_item_id=55, content="Need nozzle", author="tech")
    assert order.message_type == ChatMessageType.ORDER
    assert order.ref_work_item_id == 55
    
    incident = chat_system.broadcast_incident_alert(task_item_id=99, description="Drill broke", author="worker")
    assert incident.message_type == ChatMessageType.INCIDENT
    assert incident.ref_task_item_id == 99
