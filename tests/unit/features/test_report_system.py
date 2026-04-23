import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import ReportTemplate
from docuflow.features.reports.system import (
    BlockParam,
    ReportDataBlock,
    ReportRegistry,
    ReportSystem,
)
from docuflow.infrastructure.config import Config


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def registry():
    return ReportRegistry()


@pytest.fixture
def report_system(session: Session, registry: ReportRegistry):
    config = Config(node_id="test_node")
    return ReportSystem(config, session=session, registry=registry)


def test_registry_registration(registry: ReportRegistry):
    def dummy_query(s, p):
        return [{"val": 1}]

    registry.register(
        ReportDataBlock(
            name="test_block",
            label="Test Block",
            params=[BlockParam("p1", "P1", "str")],
            query_fn=dummy_query,
        )
    )

    block = registry.get_block("test_block")
    assert block is not None
    assert block.name == "test_block"


def test_generate_html_with_blocks(
    report_system: ReportSystem, registry: ReportRegistry, session: Session
):
    # Register a data block
    registry.register(
        ReportDataBlock(
            name="stats", label="Stats", params=[], query_fn=lambda s, p: [{"count": 42}]
        )
    )

    # Save a template that uses the block
    template = ReportTemplate(
        name="my_report", template_html="Count: {{ blocks.stats()[0].count }}"
    )
    session.add(template)
    session.commit()

    html = report_system.generate_html_preview("my_report", {})
    assert "Count: 42" in html


def test_generate_html_with_params(
    report_system: ReportSystem, registry: ReportRegistry, session: Session
):
    registry.register(
        ReportDataBlock(
            name="echo", label="Echo", params=[], query_fn=lambda s, p: [{"received": p.get("val")}]
        )
    )

    template = ReportTemplate(
        name="echo_report", template_html="Val: {{ blocks.echo(val=params.custom)[0].received }}"
    )
    session.add(template)
    session.commit()

    html = report_system.generate_html_preview("echo_report", {"custom": "hello"})
    assert "Val: hello" in html


@pytest.mark.asyncio
async def test_startup_seeds_templates(report_system: ReportSystem, session: Session):
    await report_system.on_startup()

    templates = session.exec(select(ReportTemplate)).all()
    assert len(templates) >= 1
    names = [t.name for t in templates]
    assert "shift_summary" in names
