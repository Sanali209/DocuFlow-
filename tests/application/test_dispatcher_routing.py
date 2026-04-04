import pytest
import time
from unittest.mock import MagicMock
from docuflow.application.bus.dispatcher import SecureDispatcher
from docuflow.domain.messages import P2PMessage, P2PPayload, CommandType
from docuflow.infrastructure.security import HMACSigner
from docuflow.infrastructure.config import Config

@pytest.fixture
def signer():
    return HMACSigner("test_secret")

@pytest.fixture
def config():
    return Config(node_id="NODE_B", storage_secret="test_secret")

def test_dispatcher_accepts_valid_signed_message(signer, config):
    """TDD: Verify that SecureDispatcher accepts and routes a valid, signed message."""
    dispatcher = SecureDispatcher(config, signer)
    
    # 1. Create message
    msg = P2PMessage(
        sender_id="NODE_A",
        sequence=1,
        timestamp=time.time(),
        payload=P2PPayload(command=CommandType.UPSERT_USER, data={"user": "alice"})
    )
    
    # 2. Sign message
    msg.signature = signer.sign(msg.to_signable_content())
    
    # 3. Create mock handler
    handler = MagicMock()
    dispatcher.register_handler(CommandType.UPSERT_USER, handler)
    
    # 4. Dispatch
    dispatcher.dispatch(msg)
    
    # 5. Verification
    handler.assert_called_once_with(msg.payload.data)

def test_dispatcher_rejects_invalidly_signed_message(signer, config):
    """TDD: Verify that SecureDispatcher rejects messages with mismatched HMAC signatures."""
    dispatcher = SecureDispatcher(config, signer)
    
    msg = P2PMessage(
        sender_id="NODE_A",
        sequence=1,
        timestamp=time.time(),
        payload=P2PPayload(command=CommandType.UPSERT_USER, data={})
    )
    msg.signature = "invalid_signature"
    
    handler = MagicMock()
    dispatcher.register_handler(CommandType.UPSERT_USER, handler)
    
    # Should log warning/error and return False/raise
    with pytest.raises(ValueError, match="Invalid message signature"):
        dispatcher.dispatch(msg)
    
    handler.assert_not_called()

def test_dispatcher_detects_replay_attack(signer, config):
    """TDD: Verify that SecureDispatcher prevents re-processing of old sequence IDs."""
    dispatcher = SecureDispatcher(config, signer)
    
    def create_msg(seq):
        m = P2PMessage(
            sender_id="NODE_A",
            sequence=seq,
            timestamp=time.time(),
            payload=P2PPayload(command=CommandType.SYNC_WORKPLACE, data={})
        )
        m.signature = signer.sign(m.to_signable_content())
        return m

    dispatcher.register_handler(CommandType.SYNC_WORKPLACE, MagicMock())
    
    # 1. First process seq=10
    dispatcher.dispatch(create_msg(10))
    
    # 2. Replaying seq=10 (or lower) should fail
    with pytest.raises(ValueError, match="Duplicate or out-of-order sequence"):
        dispatcher.dispatch(create_msg(10))
    
    with pytest.raises(ValueError, match="Duplicate or out-of-order sequence"):
        dispatcher.dispatch(create_msg(5))
