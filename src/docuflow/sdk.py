from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypeVar, Optional, List, Dict, Any

from dishka import AsyncContainer, Scope

if TYPE_CHECKING:
    from docuflow.application.base import BaseSystem
    from docuflow.infrastructure.config import Config

S = TypeVar("S", bound="BaseSystem")


class SDK:
    """Unified API Facade for the DocuFlow ecosystem.

    The SDK acts as a centralized gateway for resolving infrastructure
    and application systems from the underlying dependency injection container.
    It encapsulates the complexity of the Dishka container and provides a 
    stable interface for the application layers (UI, CLI, etc.).

    Key Responsibilities:
    - **Resource Allocation**: Resolving systems and their dependencies.
    - **Lifecycle Management**: Orchestrating the startup and shutdown of the P2P cluster.
    - **System Access**: Providing synchronous shortcuts to core components like Config and Orchestrator.

    Examples:
        >>> sdk = await init_sdk()
        >>> bus = await sdk.resolve_system_by_type(FileBusSystem)
        >>> await bus.send_message("node_2", {"action": "sync"})
    """

    def __init__(self, container: AsyncContainer):
        """Initialize the SDK with a pre-configured Dishka container."""
        self._container = container
        self._config: Optional["Config"] = None
        self._orchestrator: Optional["P2POrchestrator"] = None
        self._active_request_container: Optional[AsyncContainer] = None

    @property
    def config(self) -> "Config":
        """Access the validated system configuration directly from the container."""
        if self._config is None:
             raise RuntimeError("SDK.config is uninitialized. Call on_startup first.")
        return self._config

    @property
    def orchestrator(self) -> "P2POrchestrator":
        """Access the active P2P Orchestrator for cluster coordination.
        
        Note: This is a synchronous shortcut. For safe initialization, 
        ensure on_startup() has been called or use resolve_system_by_type.
        """
        if self._orchestrator is None:
            # Attempt to resolve from container if accessed early (e.g., during UI build)
            from docuflow.application.bus.orchestrator import P2POrchestrator
            # Since properties are sync, we can only safely return if it was already 
            # started or if we assume the caller handles the cold state.
            # To fix the RuntimeError, we return the cached instance if it exists.
            raise RuntimeError("SDK.orchestrator is uninitialized. Ensure on_startup() is called in the app lifespan.")
        return self._orchestrator

    async def resolve_system_by_type(self, system_class: type[S]) -> S:
        """Dynamically resolve a system instance from the DI container.
        
        Attempts to resolve from the active request scope if available, 
        otherwise falls back to the app scope.
        """
        if self._active_request_container:
            return await self._active_request_container.get(system_class)
        return await self._container.get(system_class)

    @asynccontextmanager
    async def request_scope(self):
        """Context manager to create and use a request-scoped DI container."""
        # In dishka, calling the container instance creates a sub-container for the next scope
        async with self._container() as request_container:
            old_container = self._active_request_container
            self._active_request_container = request_container
            try:
                yield request_container
            finally:
                self._active_request_container = old_container

    @property
    def projects(self) -> "ProjectSystem":
        """Access the Project Management System."""
        if not hasattr(self, "_projects"):
            raise RuntimeError("SDK.projects is uninitialized. Call on_startup first.")
        return self._projects

    @property
    def parts(self) -> "PartLibrarySystem":
        """Access the Part Library System."""
        if not hasattr(self, "_parts"):
            raise RuntimeError("SDK.parts is uninitialized. Call on_startup first.")
        return self._parts

    @property
    def consumables(self) -> "ConsumableSystem":
        """Access the Consumable Management System."""
        if not hasattr(self, "_consumables"):
            raise RuntimeError("SDK.consumables is uninitialized. Call on_startup first.")
        return self._consumables

    @property
    def production(self) -> "ProductionSystem":
        """Access the Production and Logistics System."""
        if not hasattr(self, "_production"):
            raise RuntimeError("SDK.production is uninitialized. Call on_startup first.")
        return self._production

    async def on_startup(self) -> None:
        """Initialize SDK internals and validate configuration.
        
        This method is the 'Hot Boot' trigger. It:
        1. Resolves the global configuration.
        2. Bootstraps the P2P Orchestrator.
        3. Starts the background coordination and polling loops.
        """
        from docuflow.infrastructure.config import Config
        from docuflow.application.bus.orchestrator import P2POrchestrator

        # 1. Resolve and store configuration
        self._config = await self._container.get(Config)
        
        # 2. Resolve and start the P2P Orchestrator
        self._orchestrator = await self._container.get(P2POrchestrator)
        await self._orchestrator.on_startup()
        
        # 3. Create a startup request scope to initialize feature systems
        async with self.request_scope() as req:
            # Notifications run on ALL nodes
            from docuflow.features.notifications.system import NotificationService
            from docuflow.features.admin.system import AdminSystem
            from docuflow.features.projects.system import ProjectSystem
            from docuflow.features.parts.system import PartLibrarySystem
            from docuflow.features.consumables.system import ConsumableSystem
            from docuflow.features.production.system import ProductionSystem
            from docuflow.features.folder_scanner.settings import FolderScannerSettings

            self._notifications = await req.get(NotificationService)
            self._notifications.seed_defaults()
            await self._notifications.on_startup()
            
            self._admin = await req.get(AdminSystem)
            self._admin.seed_default_roles()
            
            await req.get(FolderScannerSettings)
            
            self._projects = await req.get(ProjectSystem)
            self._projects.resolve_default_workshop_project()
            await self._projects.on_startup()
            
            self._parts = await req.get(PartLibrarySystem)
            await self._parts.on_startup()
            
            self._consumables = await req.get(ConsumableSystem)
            await self._consumables.on_startup()
            
            self._production = await req.get(ProductionSystem)
            await self._production.on_startup()

        # 4. Start Background Services (App Scope)
        from docuflow.features.folder_scanner.system import FolderScannerSystem
        from docuflow.features.folder_scanner.mirror import NSMirrorService

        self._folder_scanner = await self._container.get(FolderScannerSystem)
        await self._folder_scanner.on_startup()

        self._ns_mirror = await self._container.get(NSMirrorService)
        await self._ns_mirror.on_startup()

    async def on_shutdown(self) -> None:
        """Gracefully terminate SDK operations and clear resources."""
        if hasattr(self, "_folder_scanner"):
            await self._folder_scanner.on_shutdown()
        
        if hasattr(self, "_ns_mirror"):
            await self._ns_mirror.on_shutdown()

        if hasattr(self, "_notifications"):
            await self._notifications.on_shutdown()

        if self._orchestrator:
            try:
                await self._orchestrator.on_shutdown()
            except Exception:
                pass
