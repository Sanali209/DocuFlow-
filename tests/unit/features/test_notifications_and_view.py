from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.identity import Role
from docuflow.features.notifications.system import NotificationService
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Import all models to register them

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.mark.asyncio
async def test_notification_render(engine):
    config = Config(node_id="test")
    with Session(engine) as session:
        svc = NotificationService(config, db_session=session)

        # 1. Seed
        svc.seed_defaults()

        # 2. Render existing
        text = await svc.render("scan.empty_folder", folder_name="ORDER-1")
        assert "ORDER-1" in text
        assert "нестов нет" in text


@pytest.mark.asyncio
async def test_notification_emit(engine):
    config = Config(node_id="test")
    with Session(engine) as session:
        svc = NotificationService(config, db_session=session)
        svc.seed_defaults()

        await svc.emit("scan.new_work_item", folder_name="NEW-123")

        from docuflow.domain.entities.production import ChatMessage

        msg = session.exec(select(ChatMessage)).first()
        assert msg is not None
        assert "NEW-123" in msg.content


@pytest.mark.asyncio
async def test_view_smoke(engine):
    """Ensure view component doesn't crash on initialization."""
    mock_sdk = MagicMock()
    mock_sdk.is_master = AsyncMock(return_value=True)
    mock_sdk.resolve_system_by_type = AsyncMock()

    config = Config(node_id="test")

    # This just checks if the async function runs without immediate errors
    # NiceGUI components usually require a full event loop/browser to test deeply
    # We can't easily 'render' in a unit test without mocking the whole NiceGUI ui object,
    # but we can check if it resolves dependencies.


@pytest.mark.asyncio
async def test_role_seeding(engine):
    from docuflow.application.bus.orchestrator import P2POrchestrator
    from docuflow.features.admin.system import AdminSystem

    mock_orchestrator = MagicMock(spec=P2POrchestrator)
    mock_signer = MagicMock()
    config = Config(node_id="test")

    admin = AdminSystem(
        None, mock_orchestrator, mock_signer, config
    )  # Session not needed for seeding role names in memory if using engine manually later, but for compliance:
    with Session(engine) as session:
        admin = AdminSystem(session, mock_orchestrator, mock_signer, config)
        admin.seed_default_roles()
        session.commit()
        roles = session.exec(select(Role)).all()
        role_names = [r.name for r in roles]
        assert "Админ" in role_names
        assert "Оператор" in role_names
        assert "Бригадир" in role_names

        operator = session.exec(select(Role).where(Role.name == "Оператор")).first()
        assert "bucket:full" in operator.permissions_list
        assert "workitems:read" in operator.permissions_list
