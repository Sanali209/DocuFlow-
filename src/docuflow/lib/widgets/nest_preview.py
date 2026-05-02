from typing import Any

from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import PartLibrary, TaskItem
from docuflow.lib.base_widget import BaseDocuWidget


class NestPreview(BaseDocuWidget):
    """Renders an SVG nest preview for a TaskItem."""

    def __init__(self, task_item: TaskItem, system_scope: Any) -> None:
        super().__init__(system_scope)
        self.task_item = task_item

    async def render(self) -> None:
        svg: str = await self._generate_svg()
        ui.html(svg).classes("w-full").style("max-height: 400px; overflow: auto;")

    async def _generate_svg(self) -> str:
        sheet_w: float = self.task_item.sheet_x or 3000
        sheet_h: float = self.task_item.sheet_y or 1500

        view_w: int = 800
        scale: float = view_w / sheet_w
        view_h: float = sheet_h * scale

        svg_parts: list[str] = []
        svg_parts.append(
            f'<svg viewBox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg">'
        )
        svg_parts.append(
            f'<rect width="{view_w}" height="{view_h}" fill="#f0f0f0" '
            f'stroke="#333" stroke-width="2"/>'
        )

        x_offset: float = 10
        y_offset: float = 10
        row_height: float = 0

        async with self.scope() as req:
            session: Session = await req.get(Session)

            for tp in self.task_item.parts or []:
                stmt = select(PartLibrary).where(
                    PartLibrary.sku == tp.part_sku,
                    PartLibrary.version == tp.version,
                )
                part: PartLibrary | None = session.exec(stmt).first()
                if not part:
                    continue

                pw: float = (part.bbox_x or 50) * scale
                ph: float = (part.bbox_y or 50) * scale

                if x_offset + pw > view_w - 10:
                    x_offset = 10
                    y_offset += row_height + 5
                    row_height = 0

                svg_parts.append(
                    f'<rect x="{x_offset}" y="{y_offset}" width="{pw}" height="{ph}" '
                    f'fill="#4a90d9" stroke="#2c5aa0" stroke-width="1" rx="2"/>'
                )
                svg_parts.append(
                    f'<text x="{x_offset + 2}" y="{y_offset + 12}" '
                    f'font-size="10" fill="white">{tp.part_sku}</text>'
                )

                x_offset += pw + 5
                row_height = max(row_height, ph)

        svg_parts.append("</svg>")
        return "".join(svg_parts)
