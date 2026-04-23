from typing import Any

from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    ChatMessage,
    ChatMessageType,
    Consumable,
    ConsumableLog,
)
from docuflow.infrastructure.config import Config


class ConsumableSystem(BaseSystem):
    """
    Supplies and consumables management (nozzles, lenses, etc.).

    Principles:
    - Code as Documentation: Google-style docstrings with usage examples.
    - Self-Explaining: Descriptive identifiers (db_session, consumable_name).
    """

    def __init__(self, config: Config, session: Session, sdk: Any = None):
        """
        Initialize the consumables management system.

        Args:
            config: System configuration.
            session: SQLModel session for supply tracking.
            sdk: Optional SDK facade.
        """
        super().__init__(config, session)
        self.sdk = sdk

    # --- Core CRUD ---
    def create_consumable(
        self, name: str, category: str = "nozzle", unit: str = "pcs", min_quantity: float = 0.0
    ) -> Consumable:
        """
        Create a new workshop supply catalog entry.

        Example:
            item = supplies.create_consumable(name="Nozzle 1.5mm", category="Laser")
        """
        consumable = Consumable(name=name, category=category, unit=unit, min_quantity=min_quantity)
        self.db_session.add(consumable)
        self.db_session.flush()
        self.db_session.commit()
        self.db_session.refresh(consumable)
        return consumable

    def list_consumables(self, with_critical: bool = False) -> list[Consumable]:
        """
        List all consumables, optionally filtering for low-stock items.

        Example:
            low_stock = supplies.list_consumables(with_critical=True)
        """
        statement = select(Consumable)
        if with_critical:
            statement = statement.where(Consumable.quantity <= Consumable.min_quantity)
        return list(self.db_session.exec(statement).all())

    def get_consumable_by_name(self, name: str) -> Consumable | None:
        """
        Retrieve a consumable entry by its exact name.
        """
        statement = select(Consumable).where(Consumable.name == name)
        return self.db_session.exec(statement).first()

    # --- Operations ---
    def restock(
        self,
        consumable_id: int,
        quantity_delta: float,
        user: str = "system",
        note: str | None = None,
    ) -> Consumable:
        """
        Increment consumable stock and record an audit log.

        Example:
            supplies.restock(consumable_id=1, quantity_delta=100)
        """
        consumable = self.db_session.get(Consumable, consumable_id)
        if not consumable:
            raise ValueError(f"Consumable ID {consumable_id} not found in cluster registry.")

        consumable.quantity += quantity_delta
        self.db_session.add(consumable)

        log_entry = ConsumableLog(
            consumable_id=consumable_id,
            operation="restock",
            qty_delta=quantity_delta,
            author=user,
            note=note,
        )
        self.db_session.add(log_entry)
        self.db_session.flush()
        self.db_session.commit()
        self.db_session.refresh(consumable)
        return consumable

    def use(
        self,
        consumable_id: int,
        quantity_used: float,
        ref_task_item_id: int | None = None,
        user: str = "system",
        note: str | None = None,
    ) -> Consumable:
        """
        Decrement consumable stock and log usage. Triggers a cluster alert if minimum quantity reached.

        Example:
            supplies.use(consumable_id=2, quantity_used=1, user="operator-5")
        """
        consumable = self.db_session.get(Consumable, consumable_id)
        if not consumable:
            raise ValueError(f"Consumable ID {consumable_id} not found in cluster registry.")

        consumable.quantity -= quantity_used
        self.db_session.add(consumable)

        usage_log = ConsumableLog(
            consumable_id=consumable_id,
            operation="use",
            qty_delta=-quantity_used,
            ref_task_item_id=ref_task_item_id,
            author=user,
            note=note,
        )
        self.db_session.add(usage_log)

        if consumable.quantity <= consumable.min_quantity:
            self._broadcast_critical_alert(consumable)

        self.db_session.flush()
        self.db_session.commit()
        self.db_session.refresh(consumable)
        return consumable

    def use_consumable(self, *args, **kwargs):
        """Legacy alias for use()."""
        return self.use(*args, **kwargs)

    def perform_write_off(
        self, consumable_id: int, quantity_lost: float, reason: str, author: str = "system"
    ) -> Consumable:
        """
        Manually decrement stock for non-production reasons (damage, loss).
        """
        consumable = self.db_session.get(Consumable, consumable_id)
        if not consumable:
            raise ValueError(f"Consumable ID {consumable_id} not found.")

        consumable.quantity -= quantity_lost
        self.db_session.add(consumable)

        write_off_log = ConsumableLog(
            consumable_id=consumable_id,
            operation="write_off",
            qty_delta=-quantity_lost,
            author=author,
            note=reason,
        )
        self.db_session.add(write_off_log)
        self.db_session.flush()
        self.db_session.commit()
        self.db_session.refresh(consumable)
        return consumable

    def get_log(self, consumable_id: int, limit: int = 50) -> list[ConsumableLog]:
        """
        Retrieve chronological movement history for a specific consumable item.
        """
        statement = (
            select(ConsumableLog)
            .where(ConsumableLog.consumable_id == consumable_id)
            .order_by(ConsumableLog.id.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self.db_session.exec(statement).all())

    def get_movement_history(self, *args, **kwargs):
        """Legacy alias for get_log()."""
        return self.get_log(*args, **kwargs)

    def _broadcast_critical_alert(self, consumable: Consumable) -> None:
        """
        Internal: Dispatch a critical low-stock warning message to the workshop chat.
        """
        alert_entry = ChatMessage(
            author="System",
            node_id=self.config.node_id,
            message_type=ChatMessageType.WARNING,
            content=f"⚠️ КРИТИЧЕСКИЙ ОСТАТОК: {consumable.name} = {consumable.quantity:.0f} {consumable.unit} (Мин: {consumable.min_quantity:.0f})",
        )
        self.db_session.add(alert_entry)
        logger.warning(f"Consumable Alert: {consumable.name} is low ({consumable.quantity})")
