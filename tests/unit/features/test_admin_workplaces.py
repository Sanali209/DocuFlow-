from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.identity import Workplace
from docuflow.features.admin.system import AdminSystem
from docuflow.infrastructure.config import Config


@pytest.mark.asyncio
async def test_get_all_workplaces():
    # Setup in-memory DB
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        w1 = Workplace(node_id="LASER_1", name="Laser 1")
        w2 = Workplace(node_id="LASER_2", name="Laser 2")
        session.add(w1)
        session.add(w2)
        session.commit()

        # Mock dependencies
        orchestrator = MagicMock()
        signer = MagicMock()
        config = Config()

        # Initialize System
        admin_sys = AdminSystem(
            session=session, orchestrator=orchestrator, signer=signer, config=config
        )

        # Execute
        workplaces = admin_sys.get_all_workplaces()

        # Verify
        assert len(workplaces) >= 2
        node_ids = [w.node_id for w in workplaces]
        assert "LASER_1" in node_ids
        assert "LASER_2" in node_ids
