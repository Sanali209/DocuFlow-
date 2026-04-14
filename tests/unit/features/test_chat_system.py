import os
import shutil

import pytest
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import ChatMessageType, Project
from docuflow.features.chat.system import ChatSystem
from docuflow.infrastructure.config import Config


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
def chat_system(session: Session):
    # Setup tmp shared path
    path = "./tmp_test_chat"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    config = Config(node_id="test_node", shared_path=path)
    system = ChatSystem(config, session=session)
    yield system

    # Cleanup
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.mark.asyncio
async def test_send_global_message(chat_system: ChatSystem, session: Session):
    msg = await chat_system.send_message(author="user1", content="Hello world")
    assert msg.id is not None
    assert msg.content == "Hello world"
    assert msg.author == "user1"
    assert msg.message_type == ChatMessageType.MESSAGE


@pytest.mark.asyncio
async def test_send_with_context(chat_system: ChatSystem, session: Session):
    # Context
    p = Project(name="P-01")
    session.add(p)
    session.commit()

    msg = await chat_system.send_message(
        author="admin", content="Start project", ref_project_id=p.id
    )
    assert msg.ref_project_id == p.id
    assert msg.content == "Start project"


@pytest.mark.asyncio
async def test_reply_inheritance(chat_system: ChatSystem, session: Session):
    parent = await chat_system.send_message(
        author="boss", content="Urgent task", ref_work_item_id=123
    )

    # Reply without explicit context should inherit from parent
    child = await chat_system.reply(parent.id, author="worker", content="Understood")
    assert child.parent_message_id == parent.id
    assert child.ref_work_item_id == 123


@pytest.mark.asyncio
async def test_get_thread_recursive(chat_system: ChatSystem, session: Session):
    root = await chat_system.send_message("u1", "Root")
    c1 = await chat_system.reply(root.id, "u2", "C1")
    c2 = await chat_system.reply(c1.id, "u3", "C2")

    thread = chat_system.get_recursive_thread(root.id)
    assert len(thread) == 3
    assert thread[0].content == "Root"
    assert thread[1].content == "C1"
    assert thread[2].content == "C2"


@pytest.mark.asyncio
async def test_attach_file_persistence(chat_system: ChatSystem, session: Session):
    msg = await chat_system.send_message("u1", "See attachment")
    file_bytes = b"FAKE PDF DATA"
    filename = "spec.pdf"

    # attach_file is synchronous
    file_path = chat_system.attach_file(msg.id, filename, file_bytes)
    assert os.path.exists(file_path)
    assert file_path.endswith("spec.pdf")

    # Check DB linkage
    session.refresh(msg)
    import json

    atts = json.loads(msg.attachments)
    assert len(atts) == 1
    assert atts[0]["name"] == "spec.pdf"


@pytest.mark.asyncio
async def test_send_convenience_methods(chat_system: ChatSystem, session: Session):
    order = await chat_system.broadcast_order_request(
        work_item_id=55, content="Need nozzle", author="tech"
    )
    assert order.message_type == ChatMessageType.ORDER
    assert order.ref_work_item_id == 55

    alert = await chat_system.broadcast_incident_alert(
        task_item_id=99, description="Fire!", author="safe"
    )
    assert alert.message_type == ChatMessageType.INCIDENT
    assert alert.ref_task_item_id == 99
