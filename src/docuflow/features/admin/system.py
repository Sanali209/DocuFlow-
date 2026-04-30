import asyncio
import json
import logging
import time
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import Engine, Select, text
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.entities.identity import NodeSetting, Role, User, Workplace
from docuflow.domain.entities.production import (
    NotificationTemplate,
    WorkLog,
)
from docuflow.domain.messages import CommandType
from docuflow.infrastructure import constants
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.security import HMACSigner

if TYPE_CHECKING:
    from docuflow.application.bus.dispatcher import SecureDispatcher

logger = logging.getLogger("docuflow.admin")


class AdminSystem(BaseSystem):
    """
    Main administrative logic for user management, node settings, and workplace registry.

    Refactored to inherit from BaseSystem and support all admin-plane entities.
    """

    def __init__(
        self,
        session: Session,
        orchestrator: P2POrchestrator,
        signer: HMACSigner,
        config: Config,
    ) -> None:
        super().__init__(config, session)
        self._orchestrator = orchestrator
        self._signer = signer
        self._background_tasks: list[asyncio.Task] = []

    def _create_background_task(self, coro: Any, name: str = "") -> asyncio.Task:
        """Create a tracked background task with exception handling.

        Must be called from within an async context (a running event loop must exist).
        Raises RuntimeError if called outside an async context.
        """
        task: asyncio.Task = asyncio.get_running_loop().create_task(
            self._safe_background_task(coro, name)
        )
        self._background_tasks.append(task)
        task.add_done_callback(lambda t: self._background_tasks.remove(t))
        return task

    async def _safe_background_task(self, coro: Any, name: str) -> None:
        """Wrap a coroutine so unhandled exceptions are logged, not lost."""
        try:
            await coro
        except Exception:
            logger.exception(f"Background task '{name}' failed")

    def _is_admin(self, name: str) -> bool:
        """Robust normalization for core identity checks."""
        n: str = name.strip().lower()
        return n == "admin" or n == "админ"

    def get_cluster_nodes(self) -> list[dict[str, Any]]:
        """Aggregating the health status of all nodes in the decentralized cluster."""
        heartbeats_path: Path = (
            Path(self._config.shared_path) / constants.COORDINATOR_HEARTBEATS_DIR
        )
        nodes: list[dict[str, Any]] = []

        if not heartbeats_path.exists():
            return nodes

        hb_file: Path
        for hb_file in heartbeats_path.glob("node_*.json"):
            try:
                data: dict[str, Any] = json.loads(hb_file.read_text())
                is_stale: bool = (
                    time.time() - data.get("timestamp", 0)
                ) > constants.COORDINATOR_STALE_NODE_SECONDS
                data["status"] = "OFFLINE" if is_stale else "ONLINE"
                nodes.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        return sorted(nodes, key=lambda x: x["node_id"])

    def get_workplace_by_node_id(self, node_id: str) -> Workplace | None:
        """Retrieve the workplace configuration for a specific node."""
        return self.find_one(Workplace, node_id=node_id)

    def force_global_step_down(self) -> None:
        """Administrative command to trigger an immediate cluster-wide re-election."""
        self._create_background_task(
            self._orchestrator.broadcast_command(
                command=CommandType.FORCE_STEP_DOWN,
                data={"reason": "Manual administrative reset"},
            ),
            name="force_global_step_down",
        )

    def reset_cluster_data(self) -> dict[str, int]:
        """DEBUG ONLY: Wipes all production data while preserving identity/admin tables."""
        tables_to_clear: list[str] = [
            "taskpart",
            "parttemplate",
            "workerbucketentry",
            "productionunit",
            "materialaudit",
            "reservation",
            "materialstock",
            "consumablelog",
            "taskitem",
            "partlibrary",
            "workitem",
            "consumable",
            "storagelocation",
            "materialtype",
            "project",
            "worklog",
            "incidentlog",
            "chatmessage",
            "tag",
            "reporttemplate",
            "viewpreset",
            "notificationtemplate",
        ]
        results: dict[str, int] = {}
        try:
            # Disable FK checks to allow out-of-order deletion
            self.db_session.execute(text("PRAGMA foreign_keys = OFF"))
            for table in tables_to_clear:
                try:
                    result: Any = self.db_session.execute(
                        text(f"DELETE FROM {table}")  # noqa: S608
                    )
                    results[table] = result.rowcount  # type: ignore[attr-defined]
                except Exception:
                    logger.exception(f"Failed to clear table {table}")
                    results[table] = -1
            # Reset autoincrement sequences (best-effort)
            try:
                for table in tables_to_clear:
                    self.db_session.execute(
                        text(
                            f"DELETE FROM sqlite_sequence WHERE name='{table}'"  # noqa: S608
                        )
                    )
            except Exception:
                logger.debug("sqlite_sequence may not exist")
            self.db_session.commit()
        finally:
            self.db_session.execute(text("PRAGMA foreign_keys = ON"))
            self.db_session.commit()
        logger.warning(f"Cluster reset complete: {results}")
        return results

    # --- Workplace/Node Binding Management ---
    def get_all_workplaces(self) -> list[Workplace]:
        return self.find_all(Workplace)

    def get_workplace_node_ids(self) -> list[str]:
        """Returns list of node_ids for workplaces, or empty list if none."""
        workplaces: list[Workplace] = self.get_all_workplaces()
        return [w.node_id for w in workplaces] if workplaces else []

    def upsert_workplace(self, workplace_data: dict[str, Any]) -> Workplace:
        s: Session = self.db_session
        node_id: str | None = workplace_data.get("node_id")
        statement: Select = select(Workplace).where(Workplace.node_id == node_id)
        workplace: Workplace | None = s.exec(statement).first()

        if not workplace:
            workplace = Workplace(node_id=str(node_id), name=str(workplace_data.get("name")))

        workplace.name = str(workplace_data.get("name", workplace.name))
        workplace.allowed_modules = workplace_data.get("allowed_modules", workplace.allowed_modules)

        s.add(workplace)
        s.flush()
        s.refresh(workplace)

        self._create_background_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_WORKPLACE,
                data={
                    "node_id": workplace.node_id,
                    "name": workplace.name,
                    "allowed_modules": workplace.allowed_modules,
                },
            ),
            name="upsert_workplace",
        )
        return workplace

    def delete_workplace(self, node_id: str) -> None:
        """Delete a workplace binding by node_id."""
        s: Session = self.db_session
        statement: Select = select(Workplace).where(Workplace.node_id == node_id)
        workplace: Workplace | None = s.exec(statement).first()
        if workplace:
            s.delete(workplace)
            s.flush()
            self._create_background_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_WORKPLACE, data={"node_id": node_id}
                ),
                name="delete_workplace",
            )

    # --- User & Identity CRUD ---
    def get_all_users(self) -> list[User]:
        """Eagerly loads User.role to prevent DetachedInstanceError after session close."""
        s: Session = self.db_session
        stmt: Select = select(User).options(selectinload(User.role))  # type: ignore[arg-type]
        users: list[User] = list(s.exec(stmt).all())
        return users

    def get_all_roles(self) -> list[Role]:
        return self.find_all(Role)

    def create_user(self, user_data: dict[str, Any]) -> User:
        s: Session = self.db_session
        role_id_raw: Any = user_data.get("role_id")
        role_id: int = int(role_id_raw) if role_id_raw is not None else 0
        user: User = User(
            username=str(user_data.get("username")),
            password_hash=str(user_data.get("password_hash")),
            role_id=role_id,  # type: ignore[arg-type]
            allowed_workplaces=user_data.get("allowed_workplaces", "[]"),
        )
        s.add(user)
        s.flush()
        s.refresh(user)

        self._create_background_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_USER,
                data={
                    "username": user.username,
                    "role_id": user.role_id,
                    "password_hash": user.password_hash,
                    "allowed_workplaces": user.allowed_workplaces,
                },
            ),
            name="upsert_user",
        )
        return user

    def delete_user(self, username: str) -> None:
        if self._is_admin(username):
            return

        user: User | None = self.find_one(User, username=username)
        if user:
            self.db_session.delete(user)
            self.db_session.flush()
            self._create_background_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_USER, data={"username": username}
                ),
                name="delete_user",
            )

    # --- Role & Permission Matrix Management ---
    def upsert_role(self, role_name: str, permissions_list: list[str]) -> Role:
        s: Session = self.db_session
        if self._is_admin(role_name):
            admin_role: Role | None = s.exec(select(Role).where(Role.name == "admin")).first()
            if admin_role:
                return admin_role
            raise RuntimeError("Admin role not found")

        statement: Select = select(Role).where(Role.name == role_name)
        role: Role | None = s.exec(statement).first()

        if not role:
            role = Role(name=role_name)

        role.permissions = json.dumps(permissions_list, sort_keys=True)
        s.add(role)
        s.flush()
        s.refresh(role)

        self._create_background_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_ROLE,
                data={"name": role.name, "permissions": role.permissions},
            ),
            name="upsert_role",
        )
        return role

    def delete_role(self, role_name: str) -> None:
        if self._is_admin(role_name):
            return

        s: Session = self.db_session
        statement: Select = select(Role).where(Role.name == role_name)
        role: Role | None = s.exec(statement).first()
        if role:
            s.delete(role)
            s.flush()
            self._create_background_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_ROLE, data={"name": role_name}
                ),
                name="delete_role",
            )

    # --- Node-Specific Configuration Matrix ---
    def get_node_settings(self, node_id: str, module: str) -> dict[str, str]:
        results: list[NodeSetting] = self.find_all(NodeSetting, node_id=node_id, module=module)
        return {s.key: s.value for s in results}

    def update_node_setting(self, node_id: str, module: str, key: str, value: str) -> None:
        s: Session = self.db_session
        statement: Select = select(NodeSetting).where(
            NodeSetting.node_id == node_id,
            NodeSetting.module == module,
            NodeSetting.key == key,
        )
        setting: NodeSetting | None = s.exec(statement).first()

        if not setting:
            setting = NodeSetting(node_id=node_id, module=module, key=key)

        setting.value = str(value)
        s.add(setting)
        s.flush()
        s.commit()

        self._create_background_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_SETTING,
                data={
                    "node_id": node_id,
                    "module": module,
                    "key": key,
                    "value": str(value),
                },
            ),
            name="update_node_setting",
        )

    # --- Notification Templates ---
    def get_notification_templates(self) -> list[NotificationTemplate]:
        return self.find_all(NotificationTemplate)

    def update_notification_template(
        self, template_id: int, text: str, enabled: bool
    ) -> NotificationTemplate | None:
        template: NotificationTemplate | None = self.db_session.get(
            NotificationTemplate, template_id
        )
        if template:
            template.text = text
            template.enabled = enabled
            self.save(template)
        return template

    # --- System Audit Log ---
    def get_system_audit_logs(self, limit: int = 100) -> list[WorkLog]:
        from sqlmodel import desc

        statement: Select = select(WorkLog).order_by(desc(WorkLog.created_at)).limit(limit)
        return list(self.db_session.exec(statement).all())

    def seed_default_roles(self) -> None:
        """Populate the database with the core DocuFlow role matrix (Cyrillic)."""
        matrix: dict[str, list[str]] = {
            "Админ": ["*:full"],
            "Оператор": [
                "bucket:full",
                "chat:full",
                "workitems:read",
                "part_stock:create",
                "part_library:read",
            ],
            "Бригадир": [
                "bucket:read",
                "board:full",
                "chat:full",
                "workitems:full",
                "batching:full",
                "mat_stock:read",
                "consumables:read",
                "part_stock:read",
                "part_library:full",
                "scanner:read",
                "reports:read",
            ],
            "Менеджер": [
                "board:full",
                "chat:full",
                "workitems:full",
                "batching:full",
                "mat_stock:full",
                "consumables:full",
                "part_stock:full",
                "part_library:full",
                "scanner:read",
                "reports:full",
            ],
            "Кладовщик": [
                "chat:full",
                "mat_stock:full",
                "consumables:full",
                "part_stock:full",
                "part_library:read",
            ],
        }

        # DEPRECATED: Legacy role name mapping for database migration only.
        # Remove after all production databases have been migrated to Cyrillic names.
        legacy_mapping: dict[str, str] = {
            "Admin": "Админ",
            "Operator": "Оператор",
            "Foreman": "Бригадир",
            "Manager": "Менеджер",
            "Storekeeper": "Кладовщик",
            "Supervisor": "Бригадир",
        }

        s: Session = self.db_session

        # 1. Seed Cyrillic roles first so they are available for reassignment
        new_roles: dict[str, Role] = {}
        for name, perms in matrix.items():
            stmt: Select = select(Role).where(Role.name == name)
            role: Role | None = s.exec(stmt).first()
            if not role:
                role = Role(name=name, permissions=json.dumps(perms, sort_keys=True))
                s.add(role)
            else:
                role.permissions = json.dumps(perms, sort_keys=True)
            new_roles[name] = role
        s.flush()

        # 2. Re-assign users and clean up legacy roles
        for legacy_name, target_name in legacy_mapping.items():
            stmt: Select = select(Role).where(Role.name == legacy_name)
            legacy_role: Role | None = s.exec(stmt).first()

            if legacy_role:
                # Re-assign users to the new role
                target_role: Role = new_roles[target_name]
                user_stmt: Select = select(User).where(User.role_id == legacy_role.id)
                users: Sequence[User] = s.exec(user_stmt).all()
                for user in users:
                    user.role_id = target_role.id  # type: ignore[assignment]
                    s.add(user)

                s.flush()  # ensure updates before deleting old role
                s.delete(legacy_role)
                s.flush()

        logger.info("Cluster roles matrix seeded with Cyrillic names.")


class AdminSyncSystem:
    """Consumes administrative P2P commands to ensure decentralized consistency.

    Uses isolated sessions per call via the Engine as it runs in background scope.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def register_handlers(self, dispatcher: "SecureDispatcher") -> None:
        from docuflow.domain.messages import CommandType

        dispatcher.register_handler(CommandType("UPSERT_ROLE"), self.handle_upsert_role)
        dispatcher.register_handler(CommandType("DELETE_ROLE"), self.handle_delete_role)
        dispatcher.register_handler(CommandType("UPSERT_SETTING"), self.handle_upsert_setting)
        dispatcher.register_handler(CommandType("UPSERT_USER"), self.handle_upsert_user)
        dispatcher.register_handler(CommandType("DELETE_USER"), self.handle_delete_user)
        dispatcher.register_handler(CommandType("UPSERT_WORKPLACE"), self.handle_upsert_workplace)
        dispatcher.register_handler(CommandType("FORCE_STEP_DOWN"), self.handle_force_step_down)

    def _is_admin(self, name: str) -> bool:
        return name.strip().lower() == "admin"

    def handle_force_step_down(self, data: dict[str, Any]) -> None:
        # This is a special command handled by orchestrator logic,
        # but registered here for consistency.
        logger.warning("Sync [ADMIN]: Received FORCE_STEP_DOWN command")

    def handle_upsert_role(self, data: dict[str, Any]) -> None:
        role_name: Any = data.get("name")
        if not role_name or self._is_admin(str(role_name)):
            return

        with Session(self._engine) as session:
            statement: Select = select(Role).where(Role.name == role_name)
            role: Role | None = session.exec(statement).first()
            if not role:
                role = Role(name=role_name)
            role.permissions = data.get("permissions", "[]")
            session.add(role)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Role '{role_name}'")

    def handle_delete_role(self, data: dict[str, Any]) -> None:
        role_name: Any = data.get("name")
        if not role_name or self._is_admin(str(role_name)):
            return

        with Session(self._engine) as session:
            statement: Select = select(Role).where(Role.name == role_name)
            role: Role | None = session.exec(statement).first()
            if role:
                session.delete(role)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted Role '{role_name}'")

    def handle_upsert_setting(self, data: dict[str, Any]) -> None:
        with Session(self._engine) as session:
            node_id: str = str(data.get("node_id"))
            module: str = str(data.get("module"))
            key: str = str(data.get("key"))

            statement: Select = select(NodeSetting).where(
                NodeSetting.node_id == node_id,
                NodeSetting.module == module,
                NodeSetting.key == key,
            )
            setting: NodeSetting | None = session.exec(statement).first()
            if not setting:
                setting = NodeSetting(node_id=node_id, module=module, key=key)
            setting.value = str(data.get("value"))
            session.add(setting)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Setting {module}.{key}")

    def handle_upsert_user(self, data: dict[str, Any]) -> None:
        username: str = data.get("username")  # pyright: ignore[reportAssignmentType]
        if not username:
            logger.warning("Sync [ADMIN]: Missing username for UPSERT_USER command")
            return
        username = str(username)
        with Session(self._engine) as session:
            statement: Select = select(User).where(User.username == username)
            user: User | None = session.exec(statement).first()
            if not user:
                user = User(
                    username=username,
                    password_hash=str(data.get("password_hash")),
                    role_id=0,
                )
            role_id_raw: Any = data.get("role_id")
            user.role_id = int(role_id_raw) if role_id_raw is not None else 0  # type: ignore[assignment]
            user.password_hash = str(data.get("password_hash", user.password_hash))
            user.allowed_workplaces = data.get("allowed_workplaces", "[]")
            session.add(user)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated UserRegistry '{username}'")

    def handle_delete_user(self, data: dict[str, Any]) -> None:
        username: Any = data.get("username")
        if not username or self._is_admin(str(username)):
            return

        with Session(self._engine) as session:
            statement: Select = select(User).where(User.username == username)
            user: User | None = session.exec(statement).first()
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted User '{username}'")

    def handle_upsert_workplace(self, data: dict[str, Any]) -> None:
        node_id: str = data.get("node_id")  # pyright: ignore[reportAssignmentType]
        if not node_id:
            logger.warning("Sync [ADMIN]: Missing node_id for UPSERT_WORKPLACE command")
            return
        node_id = str(node_id)
        with Session(self._engine) as session:
            statement: Select = select(Workplace).where(Workplace.node_id == node_id)
            workplace: Workplace | None = session.exec(statement).first()
            if not workplace:
                workplace = Workplace(node_id=node_id, name=str(data.get("name")))
            workplace.name = str(data.get("name", workplace.name))
            workplace.allowed_modules = data.get("allowed_modules", workplace.allowed_modules)
            session.add(workplace)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Workplace '{node_id}'")
