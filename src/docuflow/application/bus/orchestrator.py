from typing import TYPE_CHECKING, Any

import anyio
from loguru import logger

from docuflow.application.base import BaseSystem
from docuflow.domain.messages import CommandType, P2PMessage, P2PPayload
from docuflow.infrastructure.config import Config

if TYPE_CHECKING:
    from docuflow.application.bus.dispatcher import SecureDispatcher
    from docuflow.features.admin.system import AdminSyncSystem
    from docuflow.infrastructure.bus import FileBusSystem
    from docuflow.infrastructure.coordination import CoordinationSystem
    from docuflow.infrastructure.housekeeping import HousekeepingSystem
    from docuflow.infrastructure.security import HMACSigner
    from docuflow.infrastructure.sync import DataSyncSystem


class P2POrchestrator(BaseSystem):
    """Application-layer coordinator for decentralized background tasks.

    The P2POrchestrator manages the lifecycle of all asynchronous workers
    required for cluster coordination, message polling, and data sync.
    It ensures that background loops are gracefully started during SDK boot
    and terminated during shutdown.

    Attributes:
        is_running: Boolean indicating if the background task group is active.

    Examples:
        >>> orchestrator = P2POrchestrator(config)
        >>> await orchestrator.on_startup()
        >>> print(orchestrator.is_running)
        True
        >>> await orchestrator.on_shutdown()
    """

    def __init__(
        self,
        config: Config,
        coordination: "CoordinationSystem" = None,  # type: ignore[assignment]
        bus: "FileBusSystem" = None,  # type: ignore[assignment]
        sync: "DataSyncSystem" = None,  # type: ignore[assignment]
        housekeeping: "HousekeepingSystem" = None,  # type: ignore[assignment]
        dispatcher: "SecureDispatcher" = None,  # type: ignore[assignment]
        signer: "HMACSigner" = None,  # type: ignore[assignment]
        admin_sync: "AdminSyncSystem" = None,  # type: ignore[assignment]
    ):
        """Initialize the orchestrator with its required infrastructure systems."""
        super().__init__(config)
        self._coordination = coordination
        self._bus = bus
        self._sync = sync
        self._housekeeping = housekeeping
        self._dispatcher = dispatcher
        self._signer = signer
        self._admin_sync = admin_sync

        if self._admin_sync and self._dispatcher:
            self._admin_sync.register_handlers(self._dispatcher)

        self._cancel_scope: anyio.CancelScope | None = None
        self._is_running: bool = False

        # Track sequence for outgoing broadcasts (leader-only)
        self._outbound_sequence: int = 0

    @property
    def is_running(self) -> bool:
        """Check if background orchestration loops are active."""
        return self._is_running

    @property
    def is_leader(self) -> bool:
        """Check if this node is currently the cluster LEADER/MASTER."""
        return self._coordination.is_leader

    async def on_startup(self) -> None:
        """Initialize background task group and start orchestration loops.

        This method triggers the long-running worker loops for P2P synchronization.
        The loops are managed by an internal cancel scope for clean termination.
        """
        if self._is_running:
            return

        self._is_running = True
        self._cancel_scope = anyio.CancelScope()

        # 0. Bootstrapping sub-systems
        if self._coordination and hasattr(self._coordination, "on_startup"):
            await self._coordination.on_startup()
        if self._bus and hasattr(self._bus, "on_startup"):
            await self._bus.on_startup()
        if self._sync and hasattr(self._sync, "on_startup"):
            await self._sync.on_startup()
        if self._housekeeping and hasattr(self._housekeeping, "on_startup"):
            await self._housekeeping.on_startup()

        # 1. Register P2P handlers
        if self._admin_sync and self._dispatcher:
            self._admin_sync.register_handlers(self._dispatcher)

        # Note: In a pure AnyIO environment, background tasks should be
        # spawned into a TaskGroup managed by the top-level lifespan.
        # For Iteration 2, we implement a self-starting background worker
        # that utilizes the underlying event loop to ensure non-blocking startup.

        # This will be properly bound to the SDK's global TaskGroup in Task 3.1.
        # For now, we utilize the fact that we're in an async context.
        # We start the orchestration in the background via a managed coro.
        try:
            import asyncio

            self._orchestration_task = asyncio.create_task(self._run_orchestration_master())
        except ImportError:
            # Fallback for non-asyncio anyio backends (e.g. Trio)
            # In a real production system, we'd have a more robust backend-agnostic starter
            pass

        logger.info(f"[{self.config.node_id}] P2P Orchestrator background loops initialized.")

    async def _run_orchestration_master(self) -> None:
        """Master background task that manages the lifetime of all orchestration sub-tasks."""
        with self._cancel_scope:
            async with anyio.create_task_group() as tg:
                # 1. Coordination Loop (Leader Election / Heartbeats)
                logger.info(f"Orchestrator [{self.config.node_id}]: Spawning Coordination loop...")
                tg.start_soon(self._coordination.run_coordination_loop)

                # 2. Message Polling Loop
                tg.start_soon(self._polling_worker)

                # 3. Maintenance Loop (Sync & GC - Leader only)
                tg.start_soon(self._maintenance_worker)

                # Keep the task group alive until the orchestrator is shut down
                await anyio.sleep_forever()

    async def on_shutdown(self) -> None:
        """Gracefully terminate all background workers and clear the task group."""
        if not self._is_running or not self._cancel_scope:
            return

        self._cancel_scope.cancel()
        self._is_running = False
        logger.info(f"[{self.config.node_id}] P2P Orchestrator shut down.")

    # --- Background Workers ---

    async def _polling_worker(self) -> None:
        """Periodic worker to check for and process inbox/outbox messages."""
        logger.info("Orchestrator: Polling worker started.")
        while self._is_running:
            logger.trace(
                f"Orchestrator [{self.config.node_id}]: Polling bus (interval: {self.config.bus_poll_interval}s)"
            )
            try:
                # In Iteration 3, we route these messages to domain handlers
                messages = await self._bus.poll_messages()
                for msg_data in messages:
                    try:
                        # 1. Parse raw message
                        p2p_msg = P2PMessage.model_validate(msg_data)

                        # 2. Dispatch to domain handlers (includes security check)
                        self._dispatcher.dispatch(p2p_msg)
                    except Exception as msg_error:
                        logger.warning(f"Orchestrator: Failed to process message: {msg_error}")

                await anyio.sleep(self.config.bus_poll_interval)
            except Exception as e:
                logger.error(f"Orchestrator: Polling loop failure: {e}")
                await self._handle_critical_failure(e)

    async def broadcast_command(self, command: CommandType, data: dict[str, Any]) -> None:
        """Leader-only: Signs and broadcasts a command to all nodes in the cluster.

        Args:
            command: The type of operation to perform.
            data: The command-specific payload.
        """
        import time

        self._outbound_sequence += 1

        # 1. Create message envelope
        msg = P2PMessage(
            sender_id=self.config.node_id,
            sequence=self._outbound_sequence,
            timestamp=time.time(),
            payload=P2PPayload(command=command, data=data),
        )

        # 2. Sign message
        msg.signature = self._signer.sign(msg.to_signable_content())

        # 3. Write to bus (OUTBOX)
        logger.info(
            f"[{self.config.node_id}] Orchestrator: Broadcasting {command} (seq: {msg.sequence})"
        )
        await self._bus.write_message(msg.model_dump())

    async def _maintenance_worker(self) -> None:
        """Periodic worker for leader-based synchronization and housekeeping."""
        logger.info("Orchestrator: Maintenance worker started.")
        while self._is_running:
            try:
                if self._coordination.is_leader:
                    logger.trace(
                        f"Orchestrator [{self.config.node_id}]: PEER LEADER - Running maintenance..."
                    )
                    # 1. Database Sync (Master Snapshot)
                    await self._sync.create_master_snapshot()

                    # 2. Housekeeping (GC)
                    await self._housekeeping.purge_stale_messages()
                    await self._housekeeping.rotate_snapshots()

                await anyio.sleep(self.config.sync_check_interval)
            except Exception as e:
                logger.error(f"Orchestrator: Maintenance loop failure: {e}")
                await self._handle_critical_failure(e)

    async def _handle_force_step_down(self, data: dict[str, Any]) -> None:
        """Administrative handler to trigger coordination reset.

        Args:
            data: Payload containing 'cooldown' (optional).
        """
        cooldown = data.get("cooldown", 30.0)
        logger.warning(f"[{self.config.node_id}] Orchestrator: Received FORCE_STEP_DOWN command.")
        await self._coordination.step_down(cooldown=float(cooldown))

    async def _handle_critical_failure(self, error: Exception) -> None:
        """Standardized response to background task crashes: Shut down the SDK."""
        logger.critical(f"P2P CRITICAL FAILURE: {error}. Triggering emergency shutdown.")
        # In a real implementation, this would signal the SDK to stop
        await self.on_shutdown()
