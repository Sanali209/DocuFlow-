import pytest
pytest.importorskip("dishka")
from dishka import make_async_container
from sqlalchemy import Engine
from sqlmodel import SQLModel

# Ensure SQLModel metadata is fully populated for test schema creation.
import docuflow.domain.entities.identity
import docuflow.domain.entities.production  # noqa: F401
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider
from docuflow.sdk import SDK


async def create_test_sdk(config: Config) -> SDK:
    """Helper to initialize a fully-isolated SDK instance for testing.

    This factory ensures that each node gets its own DI container and
    properly integrated configuration, enabling E2E verification of
    multiple nodes in a single process.

    Args:
        config: Custom configuration for the node instance.

    Returns:
        An initialized SDK instance.
    """
    provider = AppProvider(config)
    container = make_async_container(provider)
    engine = await container.get(Engine)
    SQLModel.metadata.create_all(engine)
    sdk = SDK(container)
    await sdk.on_startup()
    return sdk
