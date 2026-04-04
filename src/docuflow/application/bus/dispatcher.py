import json
from typing import Any, Callable, Dict
from loguru import logger
from docuflow.application.base import BaseSystem
from docuflow.domain.messages import CommandType, P2PMessage
from docuflow.infrastructure.security import HMACSigner
from docuflow.infrastructure.config import Config

# Type alias for command handlers: Callable[[DataDict], Any]
HandlerFunc = Callable[[Dict[str, Any]], Any]

class SecureDispatcher(BaseSystem):
    """Routing engine for cryptographically secured P2P messages.
    
    The SecureDispatcher verifies the HMAC-SHA256 signature and causal ordering
    (sequence) of every message before delegating execution to domain-specific handlers.
    """

    def __init__(self, config: Config, signer: HMACSigner):
        """Initialize the dispatcher with security and coordination requirements.
        
        Args:
            config: Centralized system configuration.
            signer: HMAC security root for signature verification.
        """
        super().__init__(config)
        self._signer = signer
        self._handlers: Dict[CommandType, HandlerFunc] = {}
        
        # Track the last processed sequence per sender to prevent replay attacks
        self._last_sequences: Dict[str, int] = {}

    def register_handler(self, command: CommandType, handler: HandlerFunc) -> None:
        """Associate a domain logic function with a specific command type.
        
        Args:
            command: The enumeration key of the P2P command.
            handler: A callback function that receives the command payload data.
        """
        self._handlers[command] = handler
        logger.debug(f"[{self.config.node_id}] Dispatcher: Registered handler for {command}")

    def dispatch(self, message: P2PMessage) -> Any:
        """Verify, validate, and execute an incoming P2P message.
        
        Args:
            message: The raw message envelope polled from the File Bus.
            
        Returns:
            The result of the command handler execution.
            
        Raises:
            ValueError: If signature verification fails or sequence is out of order.
        """
        # 1. Signature Verification
        if not message.signature:
            raise ValueError(f"Dispatcher: Missing signature in message from {message.sender_id}")

        signable_content = message.to_signable_content()
        if not self._signer.verify(signable_content, message.signature):
            logger.warning(f"[{self.config.node_id}] Dispatcher: Security alert! Invalid signature from {message.sender_id}")
            raise ValueError("Invalid message signature")

        # 2. Sequence Validation (Replay Protection)
        last_seq = self._last_sequences.get(message.sender_id, -1)
        if message.sequence <= last_seq:
            logger.warning(f"[{self.config.node_id}] Dispatcher: Replay detected! Node {message.sender_id} seq {message.sequence} <= {last_seq}")
            raise ValueError(f"Duplicate or out-of-order sequence (prev: {last_seq}, got: {message.sequence})")

        # 3. Routing
        command = message.payload.command
        handler = self._handlers.get(command)

        if not handler:
            logger.warning(f"[{self.config.node_id}] Dispatcher: No handler registered for {command}")
            return None

        # 4. Successful processing: Update sequence tracker
        self._last_sequences[message.sender_id] = message.sequence
        
        logger.info(f"[{self.config.node_id}] Dispatcher: Executing {command} from {message.sender_id} (seq: {message.sequence})")
        return handler(message.payload.data)
