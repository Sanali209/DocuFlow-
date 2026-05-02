import math
import os
from pathlib import Path
from typing import Any

from docuflow.features.folder_scanner.parsers.gnc import GncPartData


def write_placeholder_svg(
    path: Path | str,
    label: str = "",
    width: int = 200,
    height: int = 200,
) -> None:
    """Write a minimal dark-background placeholder SVG to *path*.

    This is the single shared helper used by :class:`SVGGenerator` whenever a
    part has no geometry to render.  Callers that previously duplicated the
    inline SVG string should call this function instead.

    Args:
        path: Destination file path (created with parents as needed).
        label: Text to display in the centre of the SVG (e.g. "No Data").
        width: Canvas width in pixels.
        height: Canvas height in pixels.
    """
    svg_content: str = (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="100%" height="100%" fill="#1e1e1e"/>\n'
        f'  <text x="50%" y="50%" text-anchor="middle" fill="#666" font-size="12">{label}</text>\n'
        f"</svg>"
    )
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg_content, encoding="utf-8")


class SVGGenerator:
    """
    Generates SVG thumbnails from GNC parts.
    Ported from legacy DocuFlow MVP and adapted for SQLModel/Pydantic entities.
    """

    def calculate_bounds(self, part: GncPartData) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box of a GNC part.
        Returns (min_x, min_y, max_x, max_y)
        """
        min_x: float = float("inf")
        min_y: float = float("inf")
        max_x: float = float("-inf")
        max_y: float = float("-inf")

        has_points: bool = False

        contour: Any
        for contour in part.contours:
            current_x: float = 0.0
            current_y: float = 0.0

            cmd: Any
            for cmd in contour.commands:
                # Update current position
                if cmd.x is not None:
                    current_x = cmd.x
                if cmd.y is not None:
                    current_y = cmd.y

                # Track bounds
                if cmd.x is not None or cmd.y is not None:
                    has_points = True
                    if current_x < min_x:
                        min_x = current_x
                    if current_x > max_x:
                        max_x = current_x
                    if current_y < min_y:
                        min_y = current_y
                    if current_y > max_y:
                        max_y = current_y

        if not has_points:
            return (0, 0, 100, 100)

        return (min_x, min_y, max_x, max_y)

    def generate_thumbnail(
        self, part: GncPartData | None, output_path: str, width: int = 200, height: int = 200
    ) -> tuple[float, float]:
        """
        Generate an SVG thumbnail for a GNC part.
        Returns (width, height) of the part in mm.
        """
        if part is None or not part.contours:
            # Create minimal SVG for empty data
            write_placeholder_svg(output_path, label="No Data", width=width, height=height)
            return (0, 0)

        min_x: float
        min_y: float
        max_x: float
        max_y: float
        min_x, min_y, max_x, max_y = self.calculate_bounds(part)

        data_w: float = max_x - min_x
        data_h: float = max_y - min_y

        if data_w == 0 and data_h == 0:
            # Empty part, create minimal SVG
            write_placeholder_svg(output_path, label="Empty", width=width, height=height)
            return (0, 0)

        # Calculate scale to fit within canvas
        padding: int = 10
        avail_w: int = width - padding * 2
        avail_h: int = height - padding * 2

        scale_x: float = avail_w / data_w if data_w > 0 else 1
        scale_y: float = avail_h / data_h if data_h > 0 else 1
        scale: float = min(scale_x, scale_y) * 0.95  # 0.95 safety factor

        # Calculate centering offset
        content_w: float = data_w * scale
        content_h: float = data_h * scale
        offset_x: float = (width - content_w) / 2
        offset_y: float = (height - content_h) / 2

        # Transform functions
        def tx(x: float) -> float:
            return offset_x + (x - min_x) * scale

        def ty(y: float) -> float:
            # Flip Y axis (SVG Y increases downward, GNC Y increases upward)
            return height - (offset_y + (y - min_y) * scale)

        # Generate SVG path data
        path_data: list[str] = []

        contour: Any
        for contour in part.contours:
            current_x: float | None = None
            current_y: float | None = None
            is_first_point: bool = True

            cmd: Any
            for cmd in contour.commands:
                # Store previous position for arc calculations
                prev_x: float | None = current_x
                prev_y: float | None = current_y

                # Update current position
                if cmd.x is not None:
                    current_x = cmd.x
                if cmd.y is not None:
                    current_y = cmd.y

                # Skip if no valid coordinates
                if current_x is None or current_y is None:
                    continue

                # Handle different command types
                if is_first_point:
                    # Always move to the start of the contour
                    path_data.append(f"M {tx(current_x):.2f} {ty(current_y):.2f}")
                    is_first_point = False

                elif cmd.type == "G00":
                    path_data.append(f"M {tx(current_x):.2f} {ty(current_y):.2f}")

                elif cmd.type in ["G01", "MODAL"]:
                    path_data.append(f"L {tx(current_x):.2f} {ty(current_y):.2f}")

                elif cmd.type in ["G02", "G03"]:
                    # Arc
                    if prev_x is not None and prev_y is not None:
                        # I and J are relative to the start point (prev_x, prev_y)
                        i_val: float = cmd.i if cmd.i is not None else 0.0
                        j_val: float = cmd.j if cmd.j is not None else 0.0

                        center_x: float = prev_x + i_val
                        center_y: float = prev_y + j_val

                        radius: float = math.sqrt(i_val**2 + j_val**2)
                        is_clockwise: bool = cmd.type == "G02"

                        # Calculate angles
                        start_angle: float = math.atan2(prev_y - center_y, prev_x - center_x)
                        end_angle: float = math.atan2(current_y - center_y, current_x - center_x)

                        # Normalize angles
                        def normalize_angle(angle: float) -> float:
                            while angle < 0:
                                angle += 2 * math.pi
                            while angle >= 2 * math.pi:
                                angle -= 2 * math.pi
                            return angle

                        start_angle = normalize_angle(start_angle)
                        end_angle = normalize_angle(end_angle)

                        # Calculate arc sweep
                        angle_diff: float
                        if is_clockwise:
                            angle_diff = start_angle - end_angle
                            if angle_diff < 0:
                                angle_diff += 2 * math.pi
                        else:
                            angle_diff = end_angle - start_angle
                            if angle_diff < 0:
                                angle_diff += 2 * math.pi

                        large_arc_flag: int = 1 if angle_diff > math.pi else 0
                        # SVG sweep: 0=counterclockwise (G03), 1=clockwise (G02)
                        # Wait, SVG arc sweep flag: 1 means rotation from start to end
                        # in positive angle direction.
                        # In SVG (Y down), positive angle is clockwise.
                        # So G02 -> 1, G03 -> 0.
                        sweep_flag: int = 1 if is_clockwise else 0

                        scaled_radius: float = radius * scale
                        if scaled_radius > 0:
                            path_data.append(
                                f"A {scaled_radius:.2f} {scaled_radius:.2f} 0 "
                                f"{large_arc_flag} {sweep_flag} "
                                f"{tx(current_x):.2f} {ty(current_y):.2f}"
                            )
                        else:
                            # Fallback to line if radius is zero
                            path_data.append(f"L {tx(current_x):.2f} {ty(current_y):.2f}")

        # Create SVG
        path_str: str = " ".join(path_data)
        # Deep blue strokes for high premium look
        svg_output: str = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" width="100%" height="100%">\n'
            f'  <rect width="100%" height="100%" fill="#0f172a"/>\n'
            f'  <path d="{path_str}" stroke="#38bdf8" stroke-width="2" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>\n'
            f"</svg>"
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_output)

        return (round(data_w, 2), round(data_h, 2))
