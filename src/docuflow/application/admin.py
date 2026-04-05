import json
import time
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.entities.identity import Role, User, Workplace
from docuflow.infrastructure.security import HMACSigner


class AdminSystem:
    """Provides high-level cluster administration and identity management.

    This system translates UI-driven administrative actions into secure,
    cryptographically signed P2P commands.
    """

    def __init__(self, session: Session, orchestrator: P2POrchestrator, signer: HMACSigner):
        self._session = session
        self._orchestrator = orchestrator
        self._signer = signer

    async def get_cluster_nodes(self) -> list[dict[str, Any]]:
        """Aggregating the health status of all nodes in the decentralized cluster."""
        # Using the absolute path derived from the shared_path config
        from docuflow.infrastructure import constants

        heartbeats_path = Path("BUS") / constants.COORDINATOR_HEARTBEATS_DIR
        nodes = []

        if not heartbeats_path.exists():
            return nodes

        for hb_file in heartbeats_path.glob("node_*.json"):
            try:
                data = json.loads(hb_file.read_text())
                # Add staleness check
                is_stale = (
                    time.time() - data.get("timestamp", 0)
                ) > constants.COORDINATOR_STALE_NODE_SECONDS
                data["status"] = "OFFLINE" if is_stale else "ONLINE"
                nodes.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        return sorted(nodes, key=lambda x: x["node_id"])

    def force_global_step_down(self):
        """Administrative command to trigger an immediate cluster-wide re-election."""
        self._orchestrator.broadcast_command(
            command="FORCE_STEP_DOWN", data={"reason": "Manual administrative reset"}
        )

    def get_all_workplaces(self) -> list[Workplace]:
        """Listing all registered workplaces in the cluster."""
        return list(self._session.exec(select(Workplace)).all())

    def upsert_workplace(self, workplace_data: dict[str, Any]) -> Workplace:
        """Create or update a physical workplace (station) configuration across the cluster."""
        node_id = workplace_data.get("node_id")
        statement = select(Workplace).where(Workplace.node_id == node_id)
        workplace = self._session.exec(statement).first()

        if not workplace:
            workplace = Workplace(node_id=node_id, name=workplace_data.get("name"))

        workplace.name = workplace_data.get("name", workplace.name)
        workplace.allowed_modules = workplace_data.get("allowed_modules", workplace.allowed_modules)

        self._session.add(workplace)
        self._session.commit()
        self._session.refresh(workplace)

        # Broadcast the change
        self._orchestrator.broadcast_command(
            command="UPSERT_WORKPLACE",
            data={
                "node_id": workplace.node_id,
                "name": workplace.name,
                "allowed_modules": workplace.allowed_modules,
            },
        )
        return workplace

    def get_all_users(self) -> list[User]:
        """Listing all users and their associated roles."""
        return list(self._session.exec(select(User)).all())

    def get_all_roles(self) -> list[Role]:
        """Listing all authorization roles."""
        return list(self._session.exec(select(Role)).all())

    def create_user(self, user_data: dict[str, Any]) -> User:
        """Adding a new user to the cluster with specific roles and workplace bindings."""
        user = User(
            username=user_data.get("username"),
            password_hash=user_data.get("password_hash"),
            role_id=user_data.get("role_id"),
            allowed_workplaces=user_data.get("allowed_workplaces", "[]"),
        )
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)

        # Broadcast identity update
        self._orchestrator.broadcast_command(
            command="UPSERT_USER",
            data={
                "username": user.username,
                "role_id": user.role_id,
                "password_hash": user.password_hash,
                "allowed_workplaces": user.allowed_workplaces,
            },
        )
        return user

    def delete_user(self, user_id: int):
        """Administrative removal of a user identity from the P2P cluster."""
        user = self._session.get(User, user_id)
        if user:
            username = user.username
            self._session.delete(user)
            self._session.commit()

            # Broadcast deletion command
            self._orchestrator.broadcast_command(command="DELETE_USER", data={"username": username})

    def upsert_role(self, role_data: dict[str, Any]) -> Role:
        """Creating or modifying an authorization role."""
        name = role_data.get("name")
        role = self._session.exec(select(Role).where(Role.name == name)).first()
        if not role:
            role = Role(name=name)

        role.permissions = role_data.get("permissions", role.permissions)
        self._session.add(role)
        self._session.commit()
        self._session.refresh(role)

        # Broadcast role update
        self._orchestrator.broadcast_command(
            command="UPSERT_ROLE", data={"name": role.name, "permissions": role.permissions}
        )
        return role
