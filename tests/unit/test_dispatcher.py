import time
import pytest
from docuflow.application.bus.dispatcher import SecureDispatcher
from docuflow.domain.messages import CommandType, P2PMessage, P2PPayload
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.security import HMACSigner


def make_message(sender: str, seq: int, secret: str = "test") -> P2PMessage:
    signer = HMACSigner(secret)
    msg = P2PMessage(
        sender_id=sender,
        sequence=seq,
        timestamp=time.time(),
        payload=P2PPayload(command=CommandType.UPSERT_USER, data={}),
    )
    msg.signature = signer.sign(msg.to_signable_content())
    return msg


@pytest.fixture
def dispatcher():
    config = Config(node_id="TEST")
    signer = HMACSigner("test")
    return SecureDispatcher(config, signer)


def test_sequence_not_updated_when_handler_raises(dispatcher):
    """If handler raises, sequence must NOT be updated so message can be retried."""
    call_count = 0

    def failing_handler(data):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("handler failed")

    dispatcher.register_handler(CommandType.UPSERT_USER, failing_handler)
    msg = make_message("NODE_B", seq=1)

    with pytest.raises(RuntimeError):
        dispatcher.dispatch(msg)

    # Sequence must NOT have been recorded
    assert dispatcher._last_sequences.get("NODE_B", -1) == -1, (
        "Sequence must not be updated when handler fails"
    )

    # Retry: same seq=1 should be accepted (not rejected as replay)
    msg2 = make_message("NODE_B", seq=1)
    with pytest.raises(RuntimeError):
        dispatcher.dispatch(msg2)
    assert call_count == 2  # handler called twice (not blocked by replay protection)


def test_sequence_updated_after_successful_handler(dispatcher):
    """After successful handler, sequence is recorded."""
    dispatcher.register_handler(CommandType.UPSERT_USER, lambda d: "ok")
    msg = make_message("NODE_B", seq=5)
    dispatcher.dispatch(msg)
    assert dispatcher._last_sequences["NODE_B"] == 5


def test_replay_attack_rejected(dispatcher):
    """A duplicate message with the same sequence is rejected."""
    dispatcher.register_handler(CommandType.UPSERT_USER, lambda d: "ok")
    msg = make_message("NODE_B", seq=1)
    dispatcher.dispatch(msg)

    msg2 = make_message("NODE_B", seq=1)
    with pytest.raises(ValueError, match="Duplicate or out-of-order"):
        dispatcher.dispatch(msg2)
