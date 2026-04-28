from typing import Any

from loguru import logger
from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    ChatMessage,
    ChatMessageType,
    MaterialAudit,
    MaterialStock,
    MaterialStockStatus,
    MaterialType,
    Reservation,
    TaskItem,
    WorkLog,
)
from docuflow.features.inventory.settings import InventorySettings
from docuflow.features.reports.system import BlockParam, ReportDataBlock, ReportRegistry
from docuflow.infrastructure.config import Config


class InventorySystem(BaseSystem):
    """
    Decentralized management of material catalog and stock level operations.

    Principles:
    - Code as Documentation: Methods include usage examples.
    - Self-Explaining: Descriptive variable names (db_session, material_type).
    """

    DEFAULT_TIME_TOLERANCE_PCT = 15.0

    def __init__(self, config: Config, session: Session, sdk: Any = None):
        """
        Initialize the inventory management system.

        Args:
            config: System configuration.
            session: SQLModel session for database operations.
            sdk: Optional SDK facade for cross-system interaction.
        """
        super().__init__(config, session)
        self.sdk = sdk

    # --- Material Definition Catalog ---

    def get_material_catalog(self) -> list[MaterialType]:
        """
        List all registered material specifications in the local database.

        Example:
            catalog = inventory.get_material_catalog()
        """
        return self.find_all(MaterialType)

    def update_material_settings(self, mat_id: int, **kwargs) -> MaterialType | None:
        """Updates specific parameters of a material definition."""
        material = self.session.get(MaterialType, mat_id)
        if not material:
            return None

        for key, value in kwargs.items():
            if hasattr(material, key):
                setattr(material, key, value)

        return self.save(material)

    def create_material_definition(self, code: str, thickness: float, **kwargs) -> MaterialType:
        """
        Create or synchronize a material specification in the local catalog.

        Example:
            material = inventory.create_material_definition(code="ALU-3", thickness=3.0)
        """
        material_type = self.find_one(MaterialType, code=code)

        if not material_type:
            material_type = MaterialType(code=code, thickness=thickness, **kwargs)
            self.session.add(material_type)
            self.session.flush()
            self.session.refresh(material_type)
            logger.info(f"Inventory: Registered new material type: {code}")

        return material_type

    # --- Stock & Inventory Management ---

    def get_all_stock(self) -> list[MaterialStock]:
        """Retrieves all current material stock records."""
        return self.find_all(MaterialStock)

    def get_audit_history(self, limit: int = 100) -> list[MaterialAudit]:
        """Retrieves historical material movements."""
        statement = select(MaterialAudit).order_by(MaterialAudit.created_at.desc()).limit(limit)  # type: ignore[attr-defined]
        return list(self.session.exec(statement).all())

    def get_active_supply_requests(self, hours: int = 12) -> list[WorkLog]:
        """Retrieves recent material supply requests from logs."""
        import datetime

        since = datetime.datetime.now() - datetime.timedelta(hours=hours)
        statement = (
            select(WorkLog)
            .where(
                WorkLog.message.contains("[LOGISTICS_REQUEST]"),  # type: ignore[attr-defined]
                WorkLog.created_at >= since,
            )
            .order_by(WorkLog.created_at.desc())  # type: ignore[attr-defined]
        )
        return list(self.session.exec(statement).all())

    def receive_material_batch(
        self,
        mat_type_id: int,
        quantity: float,
        batch_code: str | None = None,
        location: str = "MAIN",
    ) -> MaterialStock:
        """
        Records the arrival of a new material batch into the workshop stock.

        Example:
            batch = inventory.receive_material_batch(mat_type_id=1, quantity=50, batch_code="BATCH-99")
        """
        batch_stock = MaterialStock(
            mat_type_id=mat_type_id,
            quantity=quantity,
            batch_code=batch_code,
            location=location,
            status=MaterialStockStatus.AVAILABLE,
        )
        self.session.add(batch_stock)
        self.session.flush()
        self.session.refresh(batch_stock)

        # Audit trail for inventory tracking
        audit_entry = MaterialAudit(
            stock_item_id=batch_stock.id,
            operation="income",
            qty_delta=quantity,
            author="system",
            node_id=self.config.node_id,
        )
        self.session.add(audit_entry)
        self.session.flush()

        logger.info(f"Inventory: Received {quantity} units of MatID {mat_type_id}")
        return batch_stock

    def record_inventory_correction(
        self, stock_item_id: int, actual_qty: float, reason: str, author: str
    ) -> float:
        """
        Manually adjust stock levels to match physical reality (Audit-logged).

        Example:
            inventory.record_inventory_correction(stock_item_id=10, actual_qty=48.5, reason="Damaged")
        """
        stock_item = self.session.get(MaterialStock, stock_item_id)
        if not stock_item:
            return 0.0

        quantity_difference = actual_qty - stock_item.quantity
        stock_item.quantity = actual_qty
        self.session.add(stock_item)

        audit_entry = MaterialAudit(
            stock_item_id=stock_item_id,
            operation="correction",
            qty_delta=quantity_difference,
            reason=reason,
            author=author,
            node_id=self.config.node_id,
        )
        self.session.add(audit_entry)
        self.session.flush()
        return quantity_difference

    # --- Reservation Logic ---

    def create_reservation(
        self, stock_item_id: int, work_item_id: int, qty: float, is_hard: bool = False
    ) -> Reservation:
        """
        Reserve specific material for an upcoming production order.

        Example:
            reservation = inventory.create_reservation(stock_item_id=1, work_item_id=105, qty=10)
        """
        stock_item = self.session.get(MaterialStock, stock_item_id)

        if is_hard and stock_item:
            stock_item.status = MaterialStockStatus.RESERVED
            self.session.add(stock_item)

        reservation = Reservation(
            stock_item_id=stock_item_id,
            work_item_id=work_item_id,
            qty_reserved=qty,
            reservation_type="hard" if is_hard else "soft",
        )
        self.session.add(reservation)
        self.session.flush()
        self.session.refresh(reservation)
        return reservation

    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancel a reservation and free up the associated stock."""
        reservation = self.session.get(Reservation, reservation_id)
        if not reservation:
            return False

        stock_item = self.session.get(MaterialStock, reservation.stock_item_id)
        if stock_item and stock_item.status == MaterialStockStatus.RESERVED:
            stock_item.status = MaterialStockStatus.AVAILABLE
            self.session.add(stock_item)

        self.session.delete(reservation)
        self.session.flush()
        return True

    # --- Production Write-offs ---

    def perform_write_off(self, task_item: TaskItem, sheets_used: int, author: str) -> None:
        """
        Subtract material from stock upon task completion. Prioritizes existing reservations.

        Example:
            inventory.perform_write_off(task_item_obj, sheets_used=2, author="operator-1")
        """
        if not task_item.mat_type_id:
            return

        # 1. Search for an assigned reservation
        reservation = self.find_one(Reservation, work_item_id=task_item.work_item_id)

        target_stock = None
        if reservation:
            target_stock = self.session.get(MaterialStock, reservation.stock_item_id)
            if target_stock and target_stock.status == MaterialStockStatus.RESERVED:
                target_stock.status = MaterialStockStatus.AVAILABLE
            self.session.delete(reservation)
        else:
            # 2. FIFO fallback: First available batch of matching type
            fifo_query = (
                select(MaterialStock)
                .where(
                    MaterialStock.mat_type_id == task_item.mat_type_id,
                    MaterialStock.status == MaterialStockStatus.AVAILABLE,
                )
                .order_by(MaterialStock.created_at.asc())  # type: ignore[attr-defined]
            )
            target_stock = self.session.exec(fifo_query).first()

        if target_stock:
            # FIX: Prevent negative stock
            if target_stock.quantity < sheets_used:
                raise ValueError(
                    f"Недостаточно материала на складе для партии {target_stock.batch_code or target_stock.id}. "
                    f"Доступно: {target_stock.quantity}, требуется: {sheets_used}"
                )

            target_stock.quantity -= sheets_used
            audit_entry = MaterialAudit(
                stock_item_id=target_stock.id,
                operation="write_off",
                qty_delta=-sheets_used,
                ref_task_item_id=task_item.id,
                author=author,
                node_id=self.config.node_id,
            )
            self.session.add(audit_entry)
            self.session.add(target_stock)
            self.session.flush()

    def request_material_reorder(self, mat_type_id: int, quantity: float, note: str, author: str):
        """
        Creates a formal reorder audit and broadcasts a request to the Workshop Chat.

        Example:
            inventory.request_material_reorder(mat_type_id=1, quantity=100, note="Low stock")
        """
        material_type = self.session.get(MaterialType, mat_type_id)
        mat_label = material_type.code if material_type else f"ID:{mat_type_id}"

        # 1. Permanent Audit
        audit_entry = MaterialAudit(
            stock_item_id=0,
            operation="reorder",
            qty_delta=quantity,
            reason=note,
            author=author,
            node_id=self.config.node_id,
        )
        self.session.add(audit_entry)

        # 2. Alert Broadcast via Chat
        reorder_content = f"📦 ДОЗАКАЗ: {mat_label} — {quantity} {material_type.primary_unit if material_type else 'ед.'}\nПримечание: {note}"
        new_alert = ChatMessage(
            author=author,
            node_id=self.config.node_id,
            message_type=ChatMessageType.ORDER,
            content=reorder_content,
        )
        self.session.add(new_alert)
        self.session.flush()

        logger.info(f"Inventory: Reorder requested for {mat_label} by {author}")

    def resolve_supply_request(self, original_log_id: int, author: str) -> None:
        """Marks a logistics request as fulfilled by creating a resolution log."""
        original_log = self.session.get(WorkLog, original_log_id)
        if not original_log:
            return

        resolution_log = WorkLog(
            work_item_id=original_log.work_item_id,
            task_item_id=original_log.task_item_id,
            log_type=original_log.log_type,
            author=author,
            node_id=self.config.node_id,
            message=f"FULFILLED: {original_log.message.replace('[LOGISTICS_REQUEST]', '').strip()}",
        )
        self.session.add(resolution_log)
        self.session.commit()
        logger.info(f"Inventory: Supply request {original_log_id} marked as fulfilled by {author}")

    # --- Analytics & Reporting Integration ---

    def get_stock_snapshot_query(self, db_session: Session, report_params: dict) -> list[dict]:
        """
        Provides a simplified stock level view for the ReportSystem.
        """
        stock_records = db_session.exec(select(MaterialStock)).all()
        return [
            {
                "id": stock.id,
                "mat_code": stock.material_type.code if stock.material_type else "Unknown",
                "quantity": stock.quantity,
                "location": stock.location,
                "status": stock.status.value
                if hasattr(stock.status, "value")
                else str(stock.status),
            }
            for stock in stock_records
        ]

    def get_usage_audit_log(self, db_session: Session, report_params: dict) -> list[dict]:
        """
        Query method for material usage history blocks.
        """
        row_limit = report_params.get("limit", 50)
        statement = select(MaterialAudit).order_by(MaterialAudit.created_at.desc()).limit(row_limit)  # type: ignore[attr-defined]
        audit_items = db_session.exec(statement).all()
        return [
            {
                "operation": item.operation,
                "delta": item.qty_delta,
                "reason": item.reason,
                "author": item.author,
                "date": item.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for item in audit_items
        ]

    async def on_startup(self):
        """Lifecycle hook to register inventory reporting data blocks and settings."""
        from docuflow.domain.settings import registry as settings_registry

        settings_registry.register("inventory", InventorySettings)

        if not self.sdk:
            return
        registry = await self.sdk.resolve_system_by_type(ReportRegistry)

        registry.register(
            ReportDataBlock(
                name="material_usage_audit",
                label="Material Usage History",
                params=[BlockParam("limit", "Max rows", "int")],
                query_fn=self.get_usage_audit_log,
            )
        )

        registry.register(
            ReportDataBlock(
                name="stock_snapshot",
                label="Current Material Stock",
                params=[],
                query_fn=self.get_stock_snapshot_query,
            )
        )
