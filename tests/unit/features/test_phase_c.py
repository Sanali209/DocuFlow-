import pytest
from unittest.mock import MagicMock
from sqlmodel import Session, select
from docuflow.features.admin.system import AdminSystem, AdminSyncSystem
from docuflow.features.notifications.system import NotificationService
from docuflow.domain.entities.production import NotificationTemplate, ChatMessage, ChatMessageType
from docuflow.domain.entities.identity import Role, User
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.security import HMACSigner

@pytest.fixture
def test_config():
    return Config(node_id="test_node", shared_path="./test_shared", storage_secret="test_secret")

@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_orchestrator():
    return MagicMock()

@pytest.fixture
def mock_signer():
    return MagicMock(spec=HMACSigner)

class TestPhaseCRefactoring:
    """Verification for Phase C Architectural Refactoring."""

    def test_admin_system_initialization(self, test_config, mock_session, mock_orchestrator, mock_signer):
        """Verify AdminSystem uses injected Session."""
        admin = AdminSystem(mock_session, mock_orchestrator, mock_signer, test_config)
        assert admin.session == mock_session
        
        # Test a simple get_all_roles using mocked session
        mock_session.exec.return_value.all.return_value = [Role(name="Admin")]
        roles = admin.get_all_roles()
        assert len(roles) == 1
        assert roles[0].name == "Admin"
        mock_session.exec.assert_called()

    def test_notification_service_initialization(self, test_config, mock_session):
        """Verify NotificationService uses injected Session."""
        ns = NotificationService(test_config, mock_session)
        assert ns.db_session == mock_session
        
        # Test seeding
        mock_session.exec.return_value.first.return_value = None
        ns.seed_defaults()
        assert mock_session.add.call_count > 0
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_notification_emit(self, test_config, mock_session):
        """Verify NotificationService.emit creates ChatMessage."""
        ns = NotificationService(test_config, mock_session)
        
        # Setup mock for render (which uses session)
        mock_template = NotificationTemplate(key="test", text="Hello {{ name }}", enabled=True)
        # Mock session.exec(stmt).first()
        mock_session.exec.return_value.first.return_value = mock_template
        
        await ns.emit("test", name="World")
        
        # Verify ChatMessage was added
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, ChatMessage)
        assert "Hello World" in added_obj.content
        assert added_obj.author == "System"
        mock_session.flush.assert_called()

    def test_admin_sync_system_uses_engine(self, test_config):
        """Verify AdminSyncSystem uses Engine (APP scope) for background tasks."""
        mock_engine = MagicMock()
        sync = AdminSyncSystem(mock_engine)
        assert sync._engine == mock_engine

@pytest.mark.asyncio
async def test_sdk_request_scope(test_config):
    """Verify SDK provides correct scope for resolution."""
    from docuflow.sdk import SDK
    from dishka import make_async_container, Provider, Scope, provide
    
    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_str(self) -> str:
            return "scoped_string"
            
    container = make_async_container(TestProvider())
    sdk = SDK(container)
    
    async with sdk.request_scope() as req:
        val = await req.get(str)
        assert val == "scoped_string"
    
    await container.close()
