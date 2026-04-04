from dishka import make_async_container
from docuflow.infrastructure.di import AppProvider
from docuflow.sdk import SDK
from docuflow.infrastructure.config import Config

async def create_test_sdk(config: Config) -> SDK:
    """Helper to initialize a fully-isolated SDK instance for testing.
    
    This factory ensures that each node gets its own DI container and
    properly integrated configuration, enabling E2E verification of 
    multiple nodes in a single process.
    
    Args:
        config: Custom configuration for the node instance.
        
    Returns:
        An initialized SDK instance.
        
    Example:
        >>> config = Config(node_id="NODE_A")
        >>> sdk = await create_test_sdk(config)
        >>> await sdk.on_startup()
    """
    provider = AppProvider(config)
    container = make_async_container(provider)
    sdk = SDK(container)
    await sdk.on_startup()
    return sdk
