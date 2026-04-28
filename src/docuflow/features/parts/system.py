import datetime
from typing import Any

from sqlmodel import Session, select

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import (
    PartLibrary,
    PartTemplate,
    ProductionUnit,
    TaskItem,
    TaskPart,
    WorkItem,
)
from docuflow.infrastructure.config import Config


class PartLibrarySystem(BaseSystem):
    """
    Global registry of unique physical parts (SKU + Version).

    Principles:
    - Unique Identification: SKU and Version form the unique part key.
    - Geometrical Search: Supports finding parts via BBox dimensions.
    - Traceability: Tracks every pallet and work item utilizing a specific SKU.
    """

    DEFAULT_GEOMETRIC_TOLERANCE_PCT = 5.0

    def __init__(self, config: Config, db_session: Session, sdk: Any = None):
        super().__init__(config, db_session)
        self.sdk = sdk

    # --- Part Definition Logic ---

    def synchronize_part_definition(self, sku: str, version: str = "A", **kwargs) -> PartLibrary:
        """
        Idempotently creates or updates a part specification in the global library.

        Example:
            part = system.synchronize_part_definition(
                sku="BASE-001", version="B", bbox_x=100.5, bbox_y=200.0
            )
        """
        db = self.db_session
        statement = select(PartLibrary).where(
            PartLibrary.sku == sku, PartLibrary.version == version
        )
        part_record = db.exec(statement).first()

        now = datetime.datetime.now()
        if part_record:
            # Update existing metadata
            for field, value in kwargs.items():
                if value is not None and hasattr(part_record, field):
                    setattr(part_record, field, value)
            part_record.last_seen_at = now
        else:
            # Create new global part entry
            part_record = PartLibrary(
                sku=sku, version=version, first_seen_at=now, last_seen_at=now, **kwargs
            )
            db.add(part_record)

        db.flush()
        db.refresh(part_record)
        return part_record

    def retrieve_part_specification(self, sku: str, version: str = "A") -> PartLibrary | None:
        """
        Retrieves a specific part from the library by its unique SKU/Version identifier.
        """
        statement = select(PartLibrary).where(
            PartLibrary.sku == sku, PartLibrary.version == version
        )
        return self.db_session.exec(statement).first()

    def search_part_library(
        self, sku_filter: str | None = None, mat_type_id: int | None = None, limit: int = 100
    ) -> list[PartLibrary]:
        """
        Filters and lists parts in the global library.
        """
        statement = select(PartLibrary)
        if sku_filter:
            statement = statement.where(PartLibrary.sku.contains(sku_filter))  # type: ignore[attr-defined]
        if mat_type_id:
            statement = statement.where(PartLibrary.mat_type_id == mat_type_id)

        return list(self.db_session.exec(statement.limit(limit)).all())

    # --- Geometrical Intelligence ---

    def find_parts_by_geometric_similarity(
        self,
        x_dimension: float,
        y_dimension: float,
        tolerance_percent: float | None = None,
    ) -> list[PartLibrary]:
        """
        Search: find parts with similar bounding box dimensions using percentage tolerance.

        Example:
            matches = system.find_parts_by_geometric_similarity(100.0, 200.0, 2.0)
        """
        db = self.db_session
        actual_tolerance = (
            tolerance_percent
            if tolerance_percent is not None
            else self.DEFAULT_GEOMETRIC_TOLERANCE_PCT
        )
        tolerance_factor = actual_tolerance / 100.0

        statement = select(PartLibrary).where(
            PartLibrary.bbox_x.between(  # type: ignore[attr-defined]
                x_dimension * (1 - tolerance_factor), x_dimension * (1 + tolerance_factor)
            ),
            PartLibrary.bbox_y.between(  # type: ignore[attr-defined]
                y_dimension * (1 - tolerance_factor), y_dimension * (1 + tolerance_factor)
            ),
        )
        return list(db.exec(statement).all())

    # --- Downstream Traceability ---

    def trace_work_items_for_sku(self, sku: str) -> list[WorkItem]:
        """
        Retrieves all production WorkItems that have utilized this part SKU.
        """
        db = self.db_session
        statement = (
            select(WorkItem)
            .join(TaskItem, WorkItem.id == TaskItem.work_item_id)  # type: ignore[arg-type]
            .join(TaskPart, TaskItem.id == TaskPart.task_item_id)  # type: ignore[arg-type]
            .where(TaskPart.part_sku == sku)
            .distinct()
        )
        return list(db.exec(statement).all())

    def trace_pallets_for_sku(self, sku: str) -> list[ProductionUnit]:
        """
        Locates all finished ProductionUnits (pallets) containing this specific part SKU.
        """
        db = self.db_session
        statement = (
            select(ProductionUnit)
            .join(TaskItem, ProductionUnit.task_item_id == TaskItem.id)  # type: ignore[arg-type]
            .join(TaskPart, TaskItem.id == TaskPart.task_item_id)  # type: ignore[arg-type]
            .where(TaskPart.part_sku == sku)
            .distinct()
        )
        return list(db.exec(statement).all())

    # --- Knowledge Management (Templates) ---

    def create_part_template(
        self, sku: str, note_message: str, severity_level: str = "warning", author: str = "system"
    ) -> PartTemplate:
        """
        Attaches a reusable warning or informational template to a part SKU.

        Example:
            system.create_part_template(
                sku="A1", note_message="Sharp edges", severity_level="caution"
            )
        """
        db = self.db_session
        template = PartTemplate(
            part_sku=sku, message=note_message, severity=severity_level, created_by=author
        )
        db.add(template)
        db.flush()
        return template

    def list_part_templates(self, sku: str) -> list[PartTemplate]:
        """
        Retrieves all linked knowledge/warning templates for a specific part SKU.
        """
        statement = select(PartTemplate).where(PartTemplate.part_sku == sku)
        return list(self.db_session.exec(statement).all())

    def remove_part_template(self, template_id: int):
        """
        Deletes a linked knowledge template from the library.
        """
        template_record = self.db_session.get(PartTemplate, template_id)
        if template_record:
            self.db_session.delete(template_record)
            self.db_session.flush()
