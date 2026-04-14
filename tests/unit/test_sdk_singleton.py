import pytest

pytest.importorskip("dishka")

from dishka import make_async_container

from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider


@pytest.mark.anyio
async def test_sdk_is_app_scoped_singleton():
    cfg = Config()
    provider = AppProvider(cfg)
    container = make_async_container(provider)

    from docuflow.sdk import SDK

    async with container() as request_container:
        sdk1 = await request_container.get(SDK)

    # The test is limited: ensure that provider.get_sdk returns an SDK instance and
    # that repeated app-scoped resolutions yield the same object when resolved
    # from the app scope. We call container.get(SDK) twice via top-level container.
    from docuflow.sdk import SDK

    sdk_a = await container.get(SDK)
    sdk_b = await container.get(SDK)
    assert sdk_a is sdk_b
