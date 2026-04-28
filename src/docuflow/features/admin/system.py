import asyncio
import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import Engine, text
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.entities.identity import NodeSetting, Role, User, Workplace
from docuflow.domain.entities.production import (
    NotificationTemplate,
    ViewPreset,
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
    ):
        super().__init__(config, session)
        self._orchestrator = orchestrator
        self._signer = signer

    def _is_admin(self, name: str) -> bool:
        """Robust normalization for core identity checks."""
        n = name.strip().lower()
        return n == "admin" or n == "админ"

    def get_cluster_nodes(self) -> list[dict[str, Any]]:
        """Aggregating the health status of all nodes in the decentralized cluster."""
        heartbeats_path = Path(self._config.shared_path) / constants.COORDINATOR_HEARTBEATS_DIR
        nodes = []

        if not heartbeats_path.exists():
            return nodes

        for hb_file in heartbeats_path.glob("node_*.json"):
            try:
                data = json.loads(hb_file.read_text())
                is_stale = (
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

    def force_global_step_down(self):
        """Administrative command to trigger an immediate cluster-wide re-election."""
        asyncio.get_event_loop().create_task(
            self._orchestrator.broadcast_command(
                command=CommandType.FORCE_STEP_DOWN,
                data={"reason": "Manual administrative reset"},
            )
        )

    def reset_cluster_data(self) -> dict[str, int]:
        """DEBUG ONLY: Wipes all production data while preserving identity/admin tables."""
        tables_to_clear = [
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
                    result = self.db_session.execute(
                        text(f"DELETE FROM {table}")  # noqa: S608
                    )
                    results[table] = result.rowcount  # type: ignore[union-attr]
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
        workplaces = self.get_all_workplaces()
        return [w.node_id for w in workplaces] if workplaces else []

    def upsert_workplace(self, workplace_data: dict[str, Any]) -> Workplace:
        s = self.db_session
        node_id = workplace_data.get("node_id")
        statement = select(Workplace).where(Workplace.node_id == node_id)
        workplace = s.exec(statement).first()

        if not workplace:
            workplace = Workplace(node_id=str(node_id), name=str(workplace_data.get("name")))

        workplace.name = str(workplace_data.get("name", workplace.name))
        workplace.allowed_modules = workplace_data.get("allowed_modules", workplace.allowed_modules)

        s.add(workplace)
        s.flush()
        s.refresh(workplace)

        asyncio.get_event_loop().create_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_WORKPLACE,
                data={
                    "node_id": workplace.node_id,
                    "name": workplace.name,
                    "allowed_modules": workplace.allowed_modules,
                },
            )
        )
        return workplace

    def delete_workplace(self, node_id: str) -> None:
        """Delete a workplace binding by node_id."""
        s = self.db_session
        statement = select(Workplace).where(Workplace.node_id == node_id)
        workplace = s.exec(statement).first()
        if workplace:
            s.delete(workplace)
            s.flush()
            asyncio.get_event_loop().create_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_WORKPLACE, data={"node_id": node_id}
                )
            )

    # --- User & Identity CRUD ---
    def get_all_users(self) -> list[User]:
        """Eagerly loads User.role to prevent DetachedInstanceError after session close."""
        s = self.db_session
        stmt = select(User).options(selectinload(User.role))  # type: ignore[arg-type]
        users = list(s.exec(stmt).all())
        return users

    def get_all_roles(self) -> list[Role]:
        return self.find_all(Role)

    def create_user(self, user_data: dict[str, Any]) -> User:
        s = self.db_session
        role_id_raw = user_data.get("role_id")
        role_id = int(role_id_raw) if role_id_raw is not None else 0
        user = User(
            username=str(user_data.get("username")),
            password_hash=str(user_data.get("password_hash")),
            role_id=role_id,  # type: ignore[arg-type]
            allowed_workplaces=user_data.get("allowed_workplaces", "[]"),
        )
        s.add(user)
        s.flush()
        s.refresh(user)

        asyncio.get_event_loop().create_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_USER,
                data={
                    "username": user.username,
                    "role_id": user.role_id,
                    "password_hash": user.password_hash,
                    "allowed_workplaces": user.allowed_workplaces,
                },
            )
        )
        return user

    def delete_user(self, username: str):
        if self._is_admin(username):
            return

        user = self.find_one(User, username=username)
        if user:
            self.db_session.delete(user)
            self.db_session.flush()
            asyncio.get_event_loop().create_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_USER, data={"username": username}
                )
            )

    # --- Role & Permission Matrix Management ---
    def upsert_role(self, role_name: str, permissions_list: list[str]) -> Role:
        s = self.db_session
        if self._is_admin(role_name):
            admin_role = s.exec(select(Role).where(Role.name == "admin")).first()
            if admin_role:
                return admin_role
            raise RuntimeError("Admin role not found")

        statement = select(Role).where(Role.name == role_name)
        role = s.exec(statement).first()

        if not role:
            role = Role(name=role_name)

        role.permissions = json.dumps(permissions_list, sort_keys=True)
        s.add(role)
        s.flush()
        s.refresh(role)

        asyncio.get_event_loop().create_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_ROLE,
                data={"name": role.name, "permissions": role.permissions},
            )
        )
        return role

    def delete_role(self, role_name: str):
        if self._is_admin(role_name):
            return

        s = self.db_session
        statement = select(Role).where(Role.name == role_name)
        role = s.exec(statement).first()
        if role:
            s.delete(role)
            s.flush()
            asyncio.get_event_loop().create_task(
                self._orchestrator.broadcast_command(
                    command=CommandType.DELETE_ROLE, data={"name": role_name}
                )
            )

    # --- Node-Specific Configuration Matrix ---
    def get_node_settings(self, node_id: str, module: str) -> dict[str, str]:
        results = self.find_all(NodeSetting, node_id=node_id, module=module)
        return {s.key: s.value for s in results}

    def update_node_setting(self, node_id: str, module: str, key: str, value: str):
        s = self.db_session
        statement = select(NodeSetting).where(
            NodeSetting.node_id == node_id, NodeSetting.module == module, NodeSetting.key == key
        )
        setting = s.exec(statement).first()

        if not setting:
            setting = NodeSetting(node_id=node_id, module=module, key=key)

        setting.value = str(value)
        s.add(setting)
        s.flush()
        s.commit()

        asyncio.get_event_loop().create_task(
            self._orchestrator.broadcast_command(
                command=CommandType.UPSERT_SETTING,
                data={"node_id": node_id, "module": module, "key": key, "value": str(value)},
            )
        )

    # --- Notification Templates ---
    def get_notification_templates(self) -> list[NotificationTemplate]:
        return self.find_all(NotificationTemplate)

    def update_notification_template(
        self, template_id: int, text: str, enabled: bool
    ) -> NotificationTemplate | None:
        template = self.db_session.get(NotificationTemplate, template_id)
        if template:
            template.text = text
            template.enabled = enabled
            self.save(template)
        return template

    # --- View Presets ---
    def get_view_presets(self, user_id: str = "global") -> list[ViewPreset]:
        return self.find_all(ViewPreset, user_id=user_id)

    def create_view_preset(
        self, view_name: str, name: str, filters_json: str, user_id: str = "global"
    ) -> ViewPreset:
        preset = ViewPreset(
            view_name=view_name, name=name, filters_json=filters_json, user_id=user_id
        )
        return self.save(preset)

    def delete_view_preset(self, preset_id: int):
        preset = self.db_session.get(ViewPreset, preset_id)
        if preset:
            self.delete(preset)

    # --- System Audit Log ---
    def get_system_audit_logs(self, limit: int = 100) -> list[WorkLog]:
        from sqlmodel import desc

        statement = select(WorkLog).order_by(desc(WorkLog.created_at)).limit(limit)
        return list(self.db_session.exec(statement).all())

    def seed_default_roles(self):
        """Populate the database with the core DocuFlow role matrix (Cyrillic)."""
        matrix = {
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
        legacy_mapping = {
            "Admin": "Админ",
            "Operator": "Оператор",
            "Foreman": "Бригадир",
            "Manager": "Менеджер",
            "Storekeeper": "Кладовщик",
            "Supervisor": "Бригадир",
        }

        s = self.db_session

        # 1. Seed Cyrillic roles first so they are available for reassignment
        new_roles = {}
        for name, perms in matrix.items():
            stmt = select(Role).where(Role.name == name)
            role = s.exec(stmt).first()
            if not role:
                role = Role(name=name, permissions=json.dumps(perms, sort_keys=True))
                s.add(role)
            else:
                role.permissions = json.dumps(perms, sort_keys=True)
            new_roles[name] = role
        s.flush()

        # 2. Re-assign users and clean up legacy roles
        for legacy_name, target_name in legacy_mapping.items():
            stmt = select(Role).where(Role.name == legacy_name)
            legacy_role = s.exec(stmt).first()

            if legacy_role:
                # Re-assign users to the new role
                target_role = new_roles[target_name]
                user_stmt = select(User).where(User.role_id == legacy_role.id)
                users = s.exec(user_stmt).all()
                for user in users:
                    user.role_id = target_role.id
                    s.add(user)

                s.flush()  # ensure updates before deleting old role
                s.delete(legacy_role)
                s.flush()

        logger.info("Cluster roles matrix seeded with Cyrillic names.")


class AdminSyncSystem:
    """Consumes administrative P2P commands to ensure decentralized consistency.

    Uses isolated sessions per call via the Engine as it runs in background scope.
    """

    def __init__(self, engine: Engine):
        self._engine = engine

    def register_handlers(self, dispatcher: "SecureDispatcher"):
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

    def handle_force_step_down(self, data: dict[str, Any]):
        # This is a special command handled by orchestrator logic,
        # but registered here for consistency.
        logger.warning("Sync [ADMIN]: Received FORCE_STEP_DOWN command")

    def handle_upsert_role(self, data: dict[str, Any]):
        role_name = data.get("name")
        if not role_name or self._is_admin(str(role_name)):
            return

        with Session(self._engine) as session:
            statement = select(Role).where(Role.name == role_name)
            role = session.exec(statement).first()
            if not role:
                role = Role(name=role_name)
            role.permissions = data.get("permissions", "[]")
            session.add(role)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Role '{role_name}'")

    def handle_delete_role(self, data: dict[str, Any]):
        role_name = data.get("name")
        if not role_name or self._is_admin(str(role_name)):
            return

        with Session(self._engine) as session:
            statement = select(Role).where(Role.name == role_name)
            role = session.exec(statement).first()
            if role:
                session.delete(role)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted Role '{role_name}'")

    def handle_upsert_setting(self, data: dict[str, Any]):
        with Session(self._engine) as session:
            node_id = str(data.get("node_id"))
            module = str(data.get("module"))
            key = str(data.get("key"))

            statement = select(NodeSetting).where(
                NodeSetting.node_id == node_id, NodeSetting.module == module, NodeSetting.key == key
            )
            setting = session.exec(statement).first()
            if not setting:
                setting = NodeSetting(node_id=node_id, module=module, key=key)
            setting.value = str(data.get("value"))
            session.add(setting)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Setting {module}.{key}")

    def handle_upsert_user(self, data: dict[str, Any]):
        username = data.get("username")
        if not username:
            return
        username = str(username)
        with Session(self._engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if not user:
                user = User(
                    username=username, password_hash=str(data.get("password_hash")), role_id=0
                )
            role_id_raw = data.get("role_id")
            user.role_id = int(role_id_raw) if role_id_raw is not None else 0  # type: ignore[assignment]
            user.password_hash = str(data.get("password_hash", user.password_hash))
            user.allowed_workplaces = data.get("allowed_workplaces", "[]")
            session.add(user)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated UserRegistry '{username}'")

    def handle_delete_user(self, data: dict[str, Any]):
        username = data.get("username")
        if not username or self._is_admin(str(username)):
            return

        with Session(self._engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted User '{username}'")

    def handle_upsert_workplace(self, data: dict[str, Any]):
        node_id = data.get("node_id")
        if not node_id:
            return
        node_id = str(node_id)
        with Session(self._engine) as session:
            statement = select(Workplace).where(Workplace.node_id == node_id)
            workplace = session.exec(statement).first()
            if not workplace:
                workplace = Workplace(node_id=node_id, name=str(data.get("name")))
            workplace.name = str(data.get("name", workplace.name))
            workplace.allowed_modules = data.get("allowed_modules", workplace.allowed_modules)
            session.add(workplace)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Workplace '{node_id}'")
