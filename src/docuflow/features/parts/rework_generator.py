from collections import defaultdict
from pathlib import Path
from typing import Any

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

    def __init__(self, session: Session, shared_path: str) -> None:
        self.session = session
        self.shared_path = shared_path

    def generate(self, sidra_name: str, project_id: int, items: list) -> WorkItem:
        """
        1. Group items by material+thickness
        2. For each group, create a nest GNC file
        3. Save to rework/<sidra_name>/
        4. Register WorkItem + TaskItems
        """
        by_material: dict[tuple[int | None, float], list] = defaultdict(list)

        item: Any
        for item in items:
            part: PartLibrary | None = self.session.exec(
                select(PartLibrary).where(PartLibrary.sku == item.sku)
            ).first()
            if part and part.mat_type_id:
                mat: MaterialType | None = self.session.get(MaterialType, part.mat_type_id)
                if mat is None:
                    continue
                key: tuple[int | None, float] = (part.mat_type_id, mat.thickness or 0)
                by_material[key].append((part, item.qty))

        work_item: WorkItem = WorkItem(
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
            material: MaterialType | None = self.session.get(MaterialType, mat_id)
            if material is None:
                continue
            gnc_content: str = self._generate_gnc_content(material, parts)
            gnc_path: Path = Path(self.shared_path) / (
                f"rework/{sidra_name}/Sheet_{material.code}_{thickness}.GNC"
            )
            gnc_path.parent.mkdir(parents=True, exist_ok=True)
            gnc_path.write_text(gnc_content, encoding="utf-8")
            task: TaskItem = TaskItem(
                work_item_id=work_item.id,
                file_name=f"Sheet_{material.code}_{thickness}.GNC",
                file_path=f"rework/{sidra_name}/Sheet_{material.code}_{thickness}.GNC",
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

    def _get_standard_sheet_size(self, mat_code: str) -> tuple[float, float]:
        """Return standard sheet size for material."""
        return (3000.0, 1500.0)  # Default

    def _generate_gnc_content(self, mat: MaterialType, parts: list) -> str:
        """Generate GNC file content for a sheet with parts."""
        lines: list[str] = []

        # Sheet header
        sheet_x: float
        sheet_y: float
        sheet_x, sheet_y = self._get_standard_sheet_size(mat.code)
        lines.append(f"(*SHEET {sheet_x:.1f} {sheet_y:.1f} {mat.thickness or 0:.1f} 1)")
        lines.append(f"(Material: {mat.code} {mat.thickness or 0:.1f})")
        lines.append("")

        # Place parts in grid
        x_pos: float = 10.0
        y_pos: float = 10.0
        row_height: float = 0.0

        for part, qty in parts:
            for i in range(qty):
                lines.append(f"(PART NAME: {part.sku})")

                # Simple rectangle contour
                pw: float = part.bbox_x or 100
                ph: float = part.bbox_y or 100

                lines.append(f"(==== CONTOUR {i + 1} ====)")
                lines.append(f"G00 X{x_pos:.3f} Y{y_pos:.3f}")
                lines.append(f"G01 X{x_pos + pw:.3f} Y{y_pos:.3f}")
                lines.append(f"G01 X{x_pos + pw:.3f} Y{y_pos + ph:.3f}")
                lines.append(f"G01 X{x_pos:.3f} Y{y_pos + ph:.3f}")
                lines.append(f"G01 X{x_pos:.3f} Y{y_pos:.3f}")
                lines.append("")

                x_pos += pw + 10
                if x_pos + pw > sheet_x - 10:
                    x_pos = 10
                    y_pos += row_height + 10
                    row_height = 0
                row_height = max(row_height, ph)

        return "\n".join(lines)
