from collections import defaultdict

from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    MaterialType,
    PartLibrary,
    TaskItem,
    TaskItemStatus,
    WorkItem,
    WorkItemStatus,
    WorkItemType,
)


class ReworkGenerator:
    """Generates rework nests from a list of parts."""

    def __init__(self, session: Session, shared_path: str):
        self.session = session
        self.shared_path = shared_path

    def generate(self, sidra_name: str, project_id: int, items: list) -> WorkItem:
        """
        1. Group items by material+thickness
        2. For each group, create a nest GNC file
        3. Save to rework/<sidra_name>/
        4. Register WorkItem + TaskItems
        """
        by_material: dict[tuple[int, float], list] = defaultdict(list)

        for item in items:
            part = self.session.exec(select(PartLibrary).where(PartLibrary.sku == item.sku)).first()
            if part and part.mat_type_id:
                mat = self.session.get(MaterialType, part.mat_type_id)
                if mat is None:
                    continue
                key = (part.mat_type_id, mat.thickness or 0)
                by_material[key].append((part, item.qty))

        work_item = WorkItem(
            project_id=project_id,
            folder_name=sidra_name,
            folder_path=f"rework/{sidra_name}/",
            status=WorkItemStatus.NEW,
            work_item_type=WorkItemType.REWORK,
        )
        self.session.add(work_item)
        self.session.flush()

        assert work_item.id is not None

        for (mat_id, thickness), parts in by_material.items():
            mat = self.session.get(MaterialType, mat_id)
            if mat is None:
                continue
            task = TaskItem(
                work_item_id=work_item.id,
                file_name=f"Sheet_{mat.code}_{thickness}.GNC",
                file_path=f"rework/{sidra_name}/Sheet_{mat.code}_{thickness}.GNC",
                mat_type_id=mat_id,
                thickness=thickness,
                sheet_qty=self._estimate_sheets(parts),
                status=TaskItemStatus.PLANNED,
            )
            self.session.add(task)

        self.session.commit()
        return work_item

    def _estimate_sheets(self, parts: list) -> int:
        """Naive estimation: sum of part areas / sheet area."""
        return 1
