import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.infrastructure.security import HMACSigner
from docuflow.infrastructure import constants
from docuflow.domain.entities.identity import User, Workplace, Role, NodeSetting
from sqlalchemy import Engine

logger = logging.getLogger("docuflow.admin")

class AdminSystem:
    """
    Main administrative logic for user management, node settings, and workplace registry.
    
    Refactored to use constructor-based Session injection (Phase C).
    """

    def __init__(
        self, 
        session: Session, 
        orchestrator: P2POrchestrator,
        signer: HMACSigner,
        config
    ):
        self.session = session
        self._orchestrator = orchestrator
        self._signer = signer
        self._config = config

    def _is_admin(self, name: str) -> bool:
        """Robust normalization for core identity checks."""
        n = name.strip().lower()
        return n == "admin" or n == "админ"

    async def get_cluster_nodes(self) -> List[Dict[str, Any]]:
        """Aggregating the health status of all nodes in the decentralized cluster."""
        heartbeats_path = Path(self._config.shared_path) / constants.COORDINATOR_HEARTBEATS_DIR
        nodes = []
        
        if not heartbeats_path.exists():
            return nodes
            
        for hb_file in heartbeats_path.glob("node_*.json"):
            try:
                data = json.loads(hb_file.read_text())
                is_stale = (time.time() - data.get("timestamp", 0)) > constants.COORDINATOR_STALE_NODE_SECONDS
                data["status"] = "OFFLINE" if is_stale else "ONLINE"
                nodes.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        
        return sorted(nodes, key=lambda x: x["node_id"])

    def force_global_step_down(self):
        """Administrative command to trigger an immediate cluster-wide re-election."""
        self._orchestrator.broadcast_command(
            command="FORCE_STEP_DOWN",
            data={"reason": "Manual administrative reset"}
        )

    # --- Workplace/Node Binding Management ---
    def get_all_workplaces(self) -> List[Workplace]:
        return list(self.session.exec(select(Workplace)).all())

    def upsert_workplace(self, workplace_data: Dict[str, Any]) -> Workplace:
        s = self.session
        node_id = workplace_data.get("node_id")
        statement = select(Workplace).where(Workplace.node_id == node_id)
        workplace = s.exec(statement).first()
        
        if not workplace:
            workplace = Workplace(node_id=node_id, name=workplace_data.get("name"))
        
        workplace.name = workplace_data.get("name", workplace.name)
        workplace.allowed_modules = workplace_data.get("allowed_modules", workplace.allowed_modules)
        
        s.add(workplace)
        s.flush()
        s.refresh(workplace)
            
        self._orchestrator.broadcast_command(
            command="UPSERT_WORKPLACE",
            data={
                "node_id": workplace.node_id,
                "name": workplace.name,
                "allowed_modules": workplace.allowed_modules
            }
        )
        return workplace

    # --- User & Identity CRUD ---
    def get_all_users(self) -> List[User]:
        """Eagerly loads User.role to prevent DetachedInstanceError after session close."""
        s = self.session
        stmt = select(User).options(selectinload(User.role))
        users = list(s.exec(stmt).all())
        return users

    def get_all_roles(self) -> List[Role]:
        return list(self.session.exec(select(Role)).all())

    def create_user(self, user_data: Dict[str, Any]) -> User:
        s = self.session
        user = User(
            username=user_data.get("username"),
            password_hash=user_data.get("password_hash"),
            role_id=user_data.get("role_id"),
            allowed_workplaces=user_data.get("allowed_workplaces", "[]")
        )
        s.add(user)
        s.flush()
        s.refresh(user)
            
        self._orchestrator.broadcast_command(
            command="UPSERT_USER",
            data={
                "username": user.username,
                "role_id": user.role_id,
                "password_hash": user.password_hash,
                "allowed_workplaces": user.allowed_workplaces
            }
        )
        return user

    def delete_user(self, username: str):
        if self._is_admin(username):
            return
            
        s = self.session
        statement = select(User).where(User.username == username)
        user = s.exec(statement).first()
        if user:
            s.delete(user)
            s.flush()
            self._orchestrator.broadcast_command(
                command="DELETE_USER",
                data={"username": username}
            )

    # --- Role & Permission Matrix Management ---
    def upsert_role(self, role_name: str, permissions_list: List[str]) -> Role:
        s = self.session
        if self._is_admin(role_name):
            return s.exec(select(Role).where(Role.name == "admin")).first()
                
        statement = select(Role).where(Role.name == role_name)
        role = s.exec(statement).first()
        
        if not role:
            role = Role(name=role_name)
        
        role.permissions = json.dumps(permissions_list, sort_keys=True)
        s.add(role)
        s.flush()
        s.refresh(role)
        
        self._orchestrator.broadcast_command(
            command="UPSERT_ROLE",
            data={"name": role.name, "permissions": role.permissions}
        )
        return role

    def delete_role(self, role_name: str):
        if self._is_admin(role_name):
            return
            
        s = self.session
        statement = select(Role).where(Role.name == role_name)
        role = s.exec(statement).first()
        if role:
            s.delete(role)
            s.flush()
            self._orchestrator.broadcast_command(
                command="DELETE_ROLE",
                data={"name": role_name}
            )

    # --- Node-Specific Configuration Matrix ---
    def get_node_settings(self, node_id: str, module: str) -> Dict[str, str]:
        statement = select(NodeSetting).where(
            NodeSetting.node_id == node_id,
            NodeSetting.module == module
        )
        results = self.session.exec(statement).all()
        return {s.key: s.value for s in results}

    def update_node_setting(self, node_id: str, module: str, key: str, value: str):
        s = self.session
        statement = select(NodeSetting).where(
            NodeSetting.node_id == node_id,
            NodeSetting.module == module,
            NodeSetting.key == key
        )
        setting = s.exec(statement).first()
        
        if not setting:
            setting = NodeSetting(node_id=node_id, module=module, key=key)
        
        setting.value = str(value)
        s.add(setting)
        s.flush()
        
        self._orchestrator.broadcast_command(
            command="UPSERT_SETTING",
            data={
                "node_id": node_id,
                "module": module,
                "key": key,
                "value": str(value)
            }
        )

    def seed_default_roles(self):
        """Populate the database with the core DocuFlow role matrix (Cyrillic)."""
        matrix = {
            "Админ": ["*:full"],
            "Оператор": [
                "bucket:full", "chat:full", "workitems:read", 
                "part_stock:create", "part_library:read"
            ],
            "Бригадир": [
                "bucket:read", "board:full", "chat:full", "workitems:full", 
                "batching:full", "mat_stock:read", "consumables:read", 
                "part_stock:read", "part_library:full", "scanner:read", "reports:read"
            ],
            "Менеджер": [
                "board:full", "chat:full", "workitems:full", "batching:full", 
                "mat_stock:full", "consumables:full", "part_stock:full", 
                "part_library:full", "scanner:read", "reports:full"
            ],
            "Кладовщик": [
                "chat:full", "mat_stock:full", "consumables:full", 
                "part_stock:full", "part_library:read"
            ]
        }
        
        legacy_mapping = {
            "Admin": "Админ",
            "Operator": "Оператор",
            "Foreman": "Бригадир",
            "Manager": "Менеджер",
            "Storekeeper": "Кладовщик",
            "Supervisor": "Бригадир"
        }
        
        s = self.session
        
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
                    
                s.flush() # ensure updates before deleting old role
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

    def _is_admin(self, name: str) -> bool:
        return name.strip().lower() == "admin"

    def handle_upsert_role(self, data: Dict[str, Any]):
        role_name = data.get("name")
        if self._is_admin(role_name):
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

    def handle_delete_role(self, data: Dict[str, Any]):
        role_name = data.get("name")
        if self._is_admin(role_name):
            return
                
        with Session(self._engine) as session:
            statement = select(Role).where(Role.name == role_name)
            role = session.exec(statement).first()
            if role:
                session.delete(role)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted Role '{role_name}'")

    def handle_upsert_setting(self, data: Dict[str, Any]):
        with Session(self._engine) as session:
            node_id = data.get("node_id")
            module = data.get("module")
            key = data.get("key")
            
            statement = select(NodeSetting).where(
                NodeSetting.node_id == node_id,
                NodeSetting.module == module,
                NodeSetting.key == key
            )
            setting = session.exec(statement).first()
            if not setting:
                setting = NodeSetting(node_id=node_id, module=module, key=key)
            setting.value = str(data.get("value"))
            session.add(setting)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Setting {module}.{key}")

    def handle_upsert_user(self, data: Dict[str, Any]):
        username = data.get("username")
        with Session(self._engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if not user:
                user = User(username=username, password_hash=data.get("password_hash"))
            user.role_id = data.get("role_id")
            user.password_hash = data.get("password_hash", user.password_hash)
            user.allowed_workplaces = data.get("allowed_workplaces", "[]")
            session.add(user)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated UserRegistry '{username}'")

    def handle_delete_user(self, data: Dict[str, Any]):
        username = data.get("username")
        if self._is_admin(username):
            return
                
        with Session(self._engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"Sync [ADMIN]: Deleted User '{username}'")

    def handle_upsert_workplace(self, data: Dict[str, Any]):
        node_id = data.get("node_id")
        with Session(self._engine) as session:
            statement = select(Workplace).where(Workplace.node_id == node_id)
            workplace = session.exec(statement).first()
            if not workplace:
                workplace = Workplace(node_id=node_id, name=data.get("name"))
            workplace.name = data.get("name", workplace.name)
            workplace.allowed_modules = data.get("allowed_modules", workplace.allowed_modules)
            session.add(workplace)
            session.commit()
            logger.info(f"Sync [ADMIN]: Updated Workplace '{node_id}'")
