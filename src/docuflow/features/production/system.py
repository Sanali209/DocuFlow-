import datetime
from typing import List, Optional, Any
from loguru import logger
from sqlmodel import Session, select, func
from docuflow.domain.entities.production import ProductionUnit, TaskItem, WorkLog, WorkLogType
from docuflow.application.base import BaseSystem
from docuflow.infrastructure.config import Config

class ProductionSystem(BaseSystem):
    """
    Logistics and finished part management engine.
    
    Principles:
    - Pallet Traceability: Manages the lifecycle of ProductionUnits (Pallets).
    - Code as Documentation: Methods are self-describing and documented with examples.
    """
    
    def __init__(self, config: Config, db_session: Session, sdk: Any = None):
        super().__init__(config)
        self.db_session = db_session
        self.sdk = sdk

    def create_unique_pallet_label(self, sequence_number: Optional[int] = None) -> str:
        """
        Generates a unique human-readable label ID: YY-MM-NodeID-Seq.
        
        Example:
            label = system.create_unique_pallet_label()
            # Output: 26-04-NODE_1-0015
        """
        now = datetime.datetime.now()
        prefix = f"{now.strftime('%y-%m')}-{self.config.node_id}"
        
        if sequence_number is None:
            # Atomic fetch of the next sequence number for this month/node
            count = self.db_session.exec(select(func.count(ProductionUnit.id)).where(
                ProductionUnit.label_id.startswith(f"{now.strftime('%y-%m')}")
            )).one()
            sequence_number = count + 1
                
        return f"{prefix}-{str(sequence_number).zfill(4)}"

    def register_finished_pallet(self, 
                                 task_item_id: int, 
                                 quantity: int, 
                                 author_name: str = "operator", 
                                 storage_id: Optional[int] = None) -> ProductionUnit:
        """
        Registers a new production unit (pallet) containing finished parts from a task.
        
        Example:
            pallet = system.register_finished_pallet(task_item_id=50, quantity=100, storage_id=1)
        """
        db = self.db_session
        unique_label = self.create_unique_pallet_label()
        
        pallet_unit = ProductionUnit(
            label_id=unique_label,
            task_item_id=task_item_id,
            qty_produced=quantity,
            storage_location_id=storage_id,
            created_by=author_name
        )
        db.add(pallet_unit)
        
        # Log the palletization event for traceability
        task_record = db.get(TaskItem, task_item_id)
        if task_record:
            log_entry = WorkLog(
                work_item_id=task_record.work_item_id,
                task_item_id=task_item_id,
                log_type=WorkLogType.INFO.value,
                message=f"Pallet generated: {unique_label} ({quantity} units)",
                author=author_name,
                node_id=self.config.node_id
            )
            db.add(log_entry)
        
        db.flush()
        db.refresh(pallet_unit)
        
        # Broadcast discovery of new physical unit
        if self.sdk and hasattr(self.sdk, "orchestrator") and self.sdk.orchestrator:
            self.sdk.orchestrator.broadcast_command(
                command="SYNC_PALLET",
                data={"label_id": unique_label, "qty": quantity, "task_id": task_item_id}
            )
            
        return pallet_unit

    def get_recent_production_units(self, limit: int = 50) -> List[ProductionUnit]:
        """
        Lists recently registered production units for dashboard monitoring.
        """
        statement = select(ProductionUnit).order_by(ProductionUnit.id.desc()).limit(limit)
        return list(self.db_session.exec(statement).all())

    def split_production_unit(self, original_pallet_id: int, move_quantity: int, author: str) -> ProductionUnit:
        """
        Splits a pallet into two distinct units (e.g., for multi-storage).
        
        Example:
            new_pallet = system.split_production_unit(original_pallet_id=1, move_quantity=50)
        """
        db = self.db_session
        source_pallet = db.get(ProductionUnit, original_pallet_id)
        if not source_pallet:
            raise ValueError(f"Source pallet {original_pallet_id} not found")
        
        if move_quantity >= source_pallet.qty_produced:
            raise ValueError("Split quantity must be strictly less than current total.")
        
        # 1. Deduct from source
        source_pallet.qty_produced -= move_quantity
        db.add(source_pallet)
        
        # 2. Create secondary pallet
        secondary_label = self.create_unique_pallet_label()
        secondary_unit = ProductionUnit(
            label_id=secondary_label,
            task_item_id=source_pallet.task_item_id,
            qty_produced=move_quantity,
            storage_location_id=source_pallet.storage_location_id,
            parent_label_id=source_pallet.label_id,
            created_by=author
        )
        db.add(secondary_unit)
        
        # 3. Log traceability trail
        # Note: Using .task_item to avoid confusion with internal 'task' variables.
        log_entry = WorkLog(
            work_item_id=source_pallet.task_item.work_item_id if source_pallet.task_item else 0,
            task_item_id=source_pallet.task_item_id,
            log_type=WorkLogType.INFO.value,
            message=f"Pallet split: {source_pallet.label_id} -> {secondary_label} ({move_quantity} units moved)",
            author=author,
            node_id=self.config.node_id
        )
        db.add(log_entry)
        
        db.flush()
        db.refresh(secondary_unit)
        return secondary_unit

    def merge_production_units(self, source_pallet_ids: List[int], target_pallet_id: int, author_name: str) -> ProductionUnit:
        """
        Merges multiple pallets into a single target unit (e.g., consolidating inventory).
        
        Example:
            system.merge_production_units(source_pallet_ids=[1, 2], target_pallet_id=3)
        """
        db = self.db_session
        target_pallet = db.get(ProductionUnit, target_pallet_id)
        if not target_pallet:
            raise ValueError(f"Target pallet {target_pallet_id} not found")
        
        cumulative_moved = 0
        merged_labels_list = []
        
        for source_id in source_pallet_ids:
            if source_id == target_pallet_id: continue
            
            source_pallet = db.get(ProductionUnit, source_id)
            if not source_pallet: continue
            
            # Transfer entire quantity
            batch_qty = source_pallet.qty_produced
            target_pallet.qty_produced += batch_qty
            cumulative_moved += batch_qty
            merged_labels_list.append(source_pallet.label_id)
            
            source_pallet.qty_produced = 0 # Depleted
            db.add(source_pallet)
        
        db.add(target_pallet)
        
        # Log consolidation
        # Note: Using .task_item for explicit relationship access.
        log_entry = WorkLog(
            work_item_id=target_pallet.task_item.work_item_id if target_pallet.task_item else 0,
            task_item_id=target_pallet.task_item_id,
            log_type=WorkLogType.INFO.value,
            message=f"Consolidated into {target_pallet.label_id}: {', '.join(merged_labels_list)} (+{cumulative_moved} units)",
            author=author_name,
            node_id=self.config.node_id
        )
        db.add(log_entry)
        
        db.flush()
        db.refresh(target_pallet)
        return target_pallet
