import json
from pathlib import Path
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import ChatMessage, ChatMessageType
from docuflow.infrastructure.config import Config


class ChatSystem(BaseSystem):
    """
    Decentralized communication engine for the DocuFlow workshop.

    Vertical Slice: features/chat/system.py
    Principles:
    - Self-explaining code: Named constants and descriptive variables.
    - Code as documentation: Docstrings include usage examples.
    """

    # Storage Directory within the cluster's shared path
    ATTACHMENTS_SUBDIR = "chat_attachments"

    def __init__(self, config: Config, session: Session, sdk: Any = None):
        """
        Initialize the communication engine.

        Args:
            config: System configuration.
            session: SQLModel session for message persistence.
            sdk: Optional SDK facade.
        """
        super().__init__(config, session)
        self.sdk = sdk

        # Initialize root storage for chat files
        self.attachments_root = Path(config.shared_path) / self.ATTACHMENTS_SUBDIR
        self.attachments_root.mkdir(parents=True, exist_ok=True)

    # --- Core Messaging Ecosystem ---

    async def send_message(
        self,
        author: str,
        content: str,
        message_type: ChatMessageType = ChatMessageType.MESSAGE,
        ref_project_id: int | None = None,
        ref_work_item_id: int | None = None,
        ref_task_item_id: int | None = None,
        parent_message_id: int | None = None,
        attachments: list[dict] | None = None,
    ) -> ChatMessage:
        """
        Create and record a new message, then broadcast to peers via FileBus.
        """
        # Perform context inheritance if replying to a thread
        if parent_message_id and not any([ref_project_id, ref_work_item_id, ref_task_item_id]):
            parent_msg = self.session.get(ChatMessage, parent_message_id)
            if parent_msg:
                ref_project_id = parent_msg.ref_project_id
                ref_work_item_id = parent_msg.ref_work_item_id
                ref_task_item_id = parent_msg.ref_task_item_id

        new_message = ChatMessage(
            author=author,
            node_id=self.config.node_id,
            message_type=message_type,
            content=content,
            ref_project_id=ref_project_id,
            ref_work_item_id=ref_work_item_id,
            ref_task_item_id=ref_task_item_id,
            parent_message_id=parent_message_id,
            attachments=json.dumps(attachments or []),
            is_read=False,
        )

        self.session.add(new_message)
        self.session.commit()  # Ensure data is committed
        self.session.refresh(new_message)

        # P2P Notification via FileBus
        if self.sdk:
            try:
                from docuflow.infrastructure.bus import FileBusSystem

                bus = await self.sdk.resolve_system_by_type(FileBusSystem)
                await bus.broadcast_message(
                    {
                        "action": "CHAT_MESSAGE_NEW",
                        "id": new_message.id,
                        "author": author,
                        "type": message_type.value,
                    }
                )
            except Exception as e:
                logger.error(f"Chat: Failed to broadcast P2P notification: {e}")

        logger.info(f"Chat: Message {new_message.id} recorded and broadcasted")
        return new_message

    async def broadcast_order_request(
        self, work_item_id: int, content: str, author: str
    ) -> ChatMessage:
        """Convenience: Broadcast a supply order request to the workshop channel."""
        return await self.send_message(
            author=author,
            content=content,
            message_type=ChatMessageType.ORDER,
            ref_work_item_id=work_item_id,
        )

    async def broadcast_incident_alert(
        self, task_item_id: int, description: str, author: str
    ) -> ChatMessage:
        """Convenience: Broadcast a priority failure alert for a specific task."""
        return await self.send_message(
            author=author,
            content=description,
            message_type=ChatMessageType.INCIDENT,
            ref_task_item_id=task_item_id,
        )

    async def reply(self, parent_id: int, author: str, content: str, **kwargs) -> ChatMessage:
        """
        Threaded reply convenience. Inherits project/task context from parent.

        Example:
            chat.reply(parent_id=1, author="tech", content="Confirmed!")
        """
        return await self.send_message(
            author=author, content=content, parent_message_id=parent_id, **kwargs
        )

    # --- Discussion & Query Logic ---

    def get_context_thread(self, ref_type: str, ref_id: int, limit: int = 100) -> list[ChatMessage]:
        """
        Retrieve all messages linked to a specific workshop entity.

        Args:
            ref_type: One of 'project', 'work_item', 'task_item'.
            ref_id: Database identity of the linked entity.
        """
        FIELD_MAP = {
            "project": ChatMessage.ref_project_id,
            "work_item": ChatMessage.ref_work_item_id,
            "task_item": ChatMessage.ref_task_item_id,
        }

        if ref_type not in FIELD_MAP:
            raise ValueError(f"Unknown reference type mapping: {ref_type}")

        statement = (
            select(ChatMessage)
            .where(FIELD_MAP[ref_type] == ref_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )

        return list(self.session.exec(statement).all())

    def get_recursive_thread(self, root_message_id: int) -> list[ChatMessage]:
        """
        Assembles all children of a message into a single linear discussion list.
        """
        root_msg = self.session.get(ChatMessage, root_message_id)
        if not root_msg:
            return []

        results = [root_msg]

        def _fetch_children(parent_id: int):
            children_statement = (
                select(ChatMessage)
                .where(ChatMessage.parent_message_id == parent_id)
                .order_by(ChatMessage.created_at.asc())
            )

            children = self.session.exec(children_statement).all()
            for child in children:
                results.append(child)
                _fetch_children(child.id)

        _fetch_children(root_message_id)
        return results

    def get_global_messages(self, limit: int = 100) -> list[ChatMessage]:
        """
        Retrieves the most recent broadcast messages that are not linked to a project or task.
        """
        statement = (
            select(ChatMessage)
            .where(ChatMessage.ref_project_id is None)
            .where(ChatMessage.ref_work_item_id is None)
            .where(ChatMessage.ref_task_item_id is None)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        return list(self.session.exec(statement).all())

    # --- File Management Vertical Slice ---

    def attach_file(self, message_id: int, filename: str, content: bytes) -> str:
        """
        Permanently store a physical file attached to a chat message.
        """
        message_storage_path = self._prepare_message_dir(message_id)
        full_file_path = message_storage_path / filename
        full_file_path.write_bytes(content)

        self._link_attachment_to_db(message_id, filename, full_file_path, len(content))
        return str(full_file_path)

    def _prepare_message_dir(self, message_id: int) -> Path:
        """Internal: Ensure unique file directory for the given message."""
        message_dir = self.attachments_root / str(message_id)
        message_dir.mkdir(parents=True, exist_ok=True)
        return message_dir

    def _link_attachment_to_db(
        self, message_id: int, filename: str, full_path: Path, size_bytes: int
    ):
        """Internal: Update ChatMessage metadata with file pointer."""
        chat_msg = self.session.get(ChatMessage, message_id)
        if not chat_msg:
            return

        existing_attachments = json.loads(chat_msg.attachments or "[]")
        # Relative path for cross-node resolution via shared_path
        relative_storage_path = str(full_path.relative_to(self.attachments_root))

        existing_attachments.append(
            {"name": filename, "path": relative_storage_path, "size": size_bytes}
        )

        chat_msg.attachments = json.dumps(existing_attachments)
        self.session.add(chat_msg)
        self.session.flush()

    def get_physical_path(self, relative_attachment_path: str) -> Path:
        """Resolve a metadata path string to a real Local Path for downloading."""
        return self.attachments_root / relative_attachment_path
