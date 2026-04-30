import asyncio
import datetime
from typing import Any

from sqlmodel import Session, func, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import ProductionUnit, TaskItem, WorkLog, WorkLogType
from docuflow.infrastructure.config import Config


class ProductionSystem(BaseSystem):
    """
    Logistics and finished part management engine.

    Principles:
    - Pallet Traceability: Manages the lifecycle of ProductionUnits (Pallets).
    - Code as Documentation: Methods are self-describing and documented with examples.
    """

    DEFAULT_RECENT_LIMIT = 50

    def __init__(self, config: Config, session: Session, sdk: Any = None) -> None:
        super().__init__(config, session)
        self.sdk = sdk

    def create_unique_pallet_label(self, sequence_number: int | None = None) -> str:
        """
        Generates a unique human-readable label ID: YY-MM-NodeID-Seq.

        Example:
            label = system.create_unique_pallet_label()
            # Output: 26-04-NODE_1-0015
        """
        session: Session = self.db_session
        now: datetime.datetime = datetime.datetime.now()
        prefix: str = f"{now.strftime('%y-%m')}-{self.config.node_id}"

        if sequence_number is None:
            # Atomic fetch of the next sequence number for this month/node
            count: int = session.exec(
                select(func.count())
                .select_from(ProductionUnit)
                .where(ProductionUnit.label_id.startswith(f"{now.strftime('%y-%m')}"))
            ).one()
            sequence_number = count + 1

        return f"{prefix}-{str(sequence_number).zfill(4)}"

    def register_finished_pallet(
        self,
        task_item_id: int,
        quantity: int,
        author_name: str = "operator",
        storage_id: int | None = None,
    ) -> ProductionUnit:
        """
        Registers a new production unit (pallet) containing finished parts from a task.

        Example:
            pallet = system.register_finished_pallet(task_item_id=50, quantity=100, storage_id=1)
        """
        db: Session = self.db_session
        unique_label: str = self.create_unique_pallet_label()

        pallet_unit: ProductionUnit = ProductionUnit(
            label_id=unique_label,
            task_item_id=task_item_id,
            qty_produced=quantity,
            storage_location_id=storage_id,
            created_by=author_name,
        )
        db.add(pallet_unit)

        # Log the palletization event for traceability
        task_record: TaskItem | None = db.get(TaskItem, task_item_id)
        if task_record:
            log_entry: WorkLog = WorkLog(
                work_item_id=task_record.work_item_id,
                task_item_id=task_item_id,
                log_type=WorkLogType.INFO,
                message=f"Pallet generated: {unique_label} ({quantity} units)",
                author=author_name,
                node_id=self.config.node_id,
            )
            db.add(log_entry)

        db.flush()
        db.refresh(pallet_unit)

        # Broadcast discovery of new physical unit — best-effort, skipped outside async context
        if self.sdk and hasattr(self.sdk, "orchestrator") and self.sdk.orchestrator:
            try:
                asyncio.get_running_loop().create_task(
                    self.sdk.orchestrator.broadcast_command(
                        command="SYNC_PALLET",
                        data={"label_id": unique_label, "qty": quantity, "task_id": task_item_id},
                    )
                )
            except RuntimeError:
                pass  # No running event loop (e.g. CLI/test context); broadcast skipped

        return pallet_unit

    def mark_as_shipped(self, pallet_id: int, author: str) -> ProductionUnit:
        """Marks a pallet as shipped/dispatched from the workshop."""
        db: Session = self.db_session
        pallet: ProductionUnit | None = db.get(ProductionUnit, pallet_id)
        if not pallet:
            raise ValueError(f"Pallet {pallet_id} not found")

        pallet.is_stock = False
        pallet.stock_transferred_at = datetime.datetime.now()
        db.add(pallet)

        # Log shipment
        log_entry: WorkLog = WorkLog(
            work_item_id=pallet.task_item.work_item_id if pallet.task_item else 0,
            task_item_id=pallet.task_item_id,
            log_type=WorkLogType.INFO,
            message=f"Pallet SHIPPED: {pallet.label_id}",
            author=author,
            node_id=self.config.node_id,
        )
        db.add(log_entry)
        db.flush()
        return pallet

    def get_recent_production_units(self, limit: int | None = None) -> list[ProductionUnit]:
        """
        Lists recently registered production units for dashboard monitoring.
        """
        session: Session = self.db_session
        actual_limit: int = limit if limit is not None else self.DEFAULT_RECENT_LIMIT
        statement: Any = (
            select(ProductionUnit)
            .order_by(ProductionUnit.id.desc())  # type: ignore[union-attr]
            .limit(actual_limit)
        )
        return list(session.exec(statement).all())

    def split_production_unit(
        self, original_pallet_id: int, move_quantity: int, author: str
    ) -> ProductionUnit:
        """
        Splits a pallet into two distinct units (e.g., for multi-storage).

        Example:
            new_pallet = system.split_production_unit(original_pallet_id=1, move_quantity=50)
        """
        db: Session = self.db_session
        source_pallet: ProductionUnit | None = db.get(ProductionUnit, original_pallet_id)
        if not source_pallet:
            raise ValueError(f"Source pallet {original_pallet_id} not found")

        if move_quantity >= source_pallet.qty_produced:
            raise ValueError("Split quantity must be strictly less than current total.")

        # 1. Deduct from source
        source_pallet.qty_produced -= move_quantity
        db.add(source_pallet)

        # 2. Create secondary pallet
        secondary_label: str = self.create_unique_pallet_label()
        secondary_unit: ProductionUnit = ProductionUnit(
            label_id=secondary_label,
            task_item_id=source_pallet.task_item_id,
            qty_produced=move_quantity,
            storage_location_id=source_pallet.storage_location_id,
            parent_label_id=source_pallet.label_id,
            created_by=author,
        )
        db.add(secondary_unit)

        # 3. Log traceability trail
        log_entry: WorkLog = WorkLog(
            work_item_id=source_pallet.task_item.work_item_id if source_pallet.task_item else 0,
            task_item_id=source_pallet.task_item_id,
            log_type=WorkLogType.INFO,
            message=(
                f"Pallet split: {source_pallet.label_id} -> {secondary_label} "
                f"({move_quantity} units moved)"
            ),
            author=author,
            node_id=self.config.node_id,
        )
        db.add(log_entry)

        db.flush()
        db.refresh(secondary_unit)
        return secondary_unit

    def merge_production_units(
        self, source_pallet_ids: list[int], target_pallet_id: int, author_name: str
    ) -> ProductionUnit:
        """
        Merges multiple pallets into a single target unit (e.g., consolidating inventory).

        Example:
            system.merge_production_units(source_pallet_ids=[1, 2], target_pallet_id=3)
        """
        db: Session = self.db_session
        target_pallet: ProductionUnit | None = db.get(ProductionUnit, target_pallet_id)
        if not target_pallet:
            raise ValueError(f"Target pallet {target_pallet_id} not found")

        cumulative_moved: int = 0
        merged_labels_list: list[str] = []

        source_id: int
        for source_id in source_pallet_ids:
            if source_id == target_pallet_id:
                continue

            source_pallet: ProductionUnit | None = db.get(ProductionUnit, source_id)
            if not source_pallet:
                continue

            # Transfer entire quantity
            batch_qty: int = source_pallet.qty_produced
            target_pallet.qty_produced += batch_qty
            cumulative_moved += batch_qty
            merged_labels_list.append(source_pallet.label_id)

            source_pallet.qty_produced = 0  # Depleted
            db.add(source_pallet)

        db.add(target_pallet)

        # Log consolidation
        log_entry: WorkLog = WorkLog(
            work_item_id=target_pallet.task_item.work_item_id if target_pallet.task_item else 0,
            task_item_id=target_pallet.task_item_id,
            log_type=WorkLogType.INFO,
            message=(
                f"Consolidated into {target_pallet.label_id}: "
                f"{', '.join(merged_labels_list)} (+{cumulative_moved} units)"
            ),
            author=author_name,
            node_id=self.config.node_id,
        )
        db.add(log_entry)

        db.flush()
        db.refresh(target_pallet)
        return target_pallet
