from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.domain.entities.production import ChatMessage, ChatMessageType
from docuflow.features.chat.incidents import IncidentSystem
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
    config = Config(node_id="test_node", shared_path="./tmp_shared")
    return ChatSystem(config, session=session)


@pytest.fixture
def incident_system(session: Session, chat_system: ChatSystem):
    config = Config(node_id="test_node")
    return IncidentSystem(config, session=session, chat_system=chat_system)


@pytest.mark.asyncio
async def test_report_creates_log_and_chat(incident_system: IncidentSystem, session: Session):
    inc = await incident_system.report_incident(
        incident_type="BREAKDOWN", description="Laser head stuck", reported_by="operator1"
    )

    assert inc.id is not None
    assert inc.resolved is False

    # Check chat broadcast
    stmt = select(ChatMessage).where(ChatMessage.message_type == ChatMessageType.INCIDENT)
    msg = session.exec(stmt).first()
    assert msg is not None
    assert "Laser head stuck" in msg.content


@pytest.mark.asyncio
async def test_resolve_calculates_downtime(incident_system: IncidentSystem, session: Session):
    inc = await incident_system.report_incident("DEFECT", "Blurry lens", "operator1")

    # Manually set created_at back by 30 mins
    inc.created_at = datetime.now() - timedelta(minutes=30)
    session.add(inc)
    session.commit()

    await incident_system.resolve_incident(inc.id, "technician", "Cleaned lens")

    session.refresh(inc)
    assert inc.resolved is True
    # Downtime should be approx 30 minutes
    assert 29.0 < inc.downtime_minutes < 31.0
    assert inc.resolution_note == "Cleaned lens"


@pytest.mark.asyncio
async def test_active_filtering(incident_system: IncidentSystem, session: Session):
    await incident_system.report_incident(incident_system.TYPE_BREAKDOWN, "P1", "u1")
    inc2 = await incident_system.report_incident(incident_system.TYPE_BREAKDOWN, "P2", "u1")
    await incident_system.resolve_incident(inc2.id, "u1", "fixed")

    active = incident_system.get_active_failures()
    assert len(active) == 1
    assert active[0].description == "P1"


@pytest.mark.asyncio
async def test_downtime_stats(incident_system: IncidentSystem, session: Session):
    # Inc 1: 10 mins
    inc1 = await incident_system.report_incident(incident_system.TYPE_BREAKDOWN, "B1", "u1")
    inc1.created_at = datetime.now() - timedelta(minutes=10)

    # Inc 2: 20 mins
    inc2 = await incident_system.report_incident(incident_system.TYPE_BREAKDOWN, "B2", "u1")
    inc2.created_at = datetime.now() - timedelta(minutes=20)

    session.add_all([inc1, inc2])
    session.commit()

    await incident_system.resolve_incident(inc1.id, "u1", "ok")
    await incident_system.resolve_incident(inc2.id, "u1", "ok")

    stats = incident_system.get_summary_stats()
    assert stats[incident_system.TYPE_BREAKDOWN] >= 30.0
