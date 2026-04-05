import logging

from jinja2 import Template
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import ChatMessage, ChatMessageType, NotificationTemplate
from docuflow.infrastructure.config import Config

logger = logging.getLogger("docuflow.notifications")


class NotificationService(BaseSystem):
    """
    Template-driven notification system for cluster-wide status messages.
    """

    def __init__(self, config: Config, db_session: Session):
        """
        Initialize the notification service.

        Args:
            config: System configuration.
            db_session: SQLModel session for message persistence.
        """
        super().__init__(config)
        self.db_session = db_session

    async def render(self, key: str, **vars) -> str | None:
        """
        Render a notification template using Jinja2.

        Example:
            text = await ns.render("scan.new_work_item", folder_name="Project-A")
        """
        stmt = select(NotificationTemplate).where(NotificationTemplate.key == key)
        tmpl = self.db_session.exec(stmt).first()

        if not tmpl or not tmpl.enabled:
            return None

        try:
            return Template(tmpl.text).render(**vars)
        except Exception as e:
            logger.error(f"Notification: Rendering error for '{key}': {e}")
            return f"[{key}] {vars}"

    async def emit(
        self,
        key: str,
        ref_work_item_id: int | None = None,
        ref_task_item_id: int | None = None,
        **vars,
    ) -> None:
        """
        Broadcasting: Render and persist a cluster-wide notification as a ChatMessage.

        Example:
            await ns.emit("stock.alert", sku="ALU-3")
        """
        content = await self.render(key, **vars)
        if not content:
            return

        msg = ChatMessage(
            author="System",
            node_id=self.config.node_id,
            message_type=ChatMessageType.INFO,
            content=content,
            ref_work_item_id=ref_work_item_id,
            ref_task_item_id=ref_task_item_id,
        )
        self.db_session.add(msg)
        self.db_session.flush()
        logger.info(f"Notification: Emitted '{key}' to cluster.")

    def seed_defaults(self):
        """Standard notification templates for the system."""
        defaults = {
            "scan.empty_folder": "⚠️ {{ folder_name }}: папка пришла, нестов нет! Сходить в раскрой",
            "scan.new_work_item": "📋 Новый наряд: {{ folder_name }}",
            "scan.file_changed": "⚠️ Файл {{ file_name }} изменился на сети! Обновить NS?",
            "stock.alert": "📦 Деталь {{ sku }} есть в запасе — проверить перед резкой",
            "doc.no_folder": "📄 Бумага получена, папки нет на диске: {{ folder_name }}",
            "ns_mirror.sync": "✓ {{ file_name }} синхронизирован на узел {{ node_id }}",
        }

        s = self.db_session
        for key, text in defaults.items():
            stmt = select(NotificationTemplate).where(NotificationTemplate.key == key)
            existing = s.exec(stmt).first()
            if not existing:
                s.add(NotificationTemplate(key=key, text=text, enabled=True))
        s.flush()
        logger.info("Notification templates seeded.")
