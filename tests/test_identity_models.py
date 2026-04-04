import json
import pytest
from sqlmodel import Session, create_engine, SQLModel, select
from docuflow.domain.entities.identity import Workplace, Role, User

def test_identity_models_creation():
    """TDD: Verify that all identity models can be persisted and retrieved correctly."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # 1. Create Role
        role = Role(name="Operator", permissions=json.dumps(["can_view_tasks"]))
        session.add(role)
        session.commit()
        session.refresh(role)
        
        # 2. Create Workplace
        wp = Workplace(node_id="LASER_01", name="Laser Cutter Unit", allowed_modules=json.dumps(["tracking"]))
        session.add(wp)
        session.commit()
        session.refresh(wp)
        
        # 3. Create User
        user = User(
            username="alice",
            password_hash="fake_hash",
            role_id=role.id,
            allowed_workplaces=json.dumps([wp.id])
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # 4. Verification
        stmt = select(User).where(User.username == "alice")
        retrieved_user = session.exec(stmt).one()
        
        assert retrieved_user.username == "alice"
        assert retrieved_user.role_id == role.id
        allowed_wp_ids = json.loads(retrieved_user.allowed_workplaces)
        assert wp.id in allowed_wp_ids

def test_role_default_values():
    """TDD: Ensure roles have basic fields."""
    role = Role(name="Admin", permissions="[]")
    assert role.name == "Admin"

def test_workplace_index():
    """TDD: Workplace node_id should be searchable."""
    wp = Workplace(node_id="LATHE_01", name="CNC Lathe", allowed_modules="[]")
    assert wp.node_id == "LATHE_01"
