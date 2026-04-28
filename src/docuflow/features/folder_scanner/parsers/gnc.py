import datetime
import re
from pathlib import Path

from pydantic import BaseModel

from docuflow.domain.entities.production import MaterialType


class ContourCommand(BaseModel):
    """Single G-code command within a contour."""

    type: str = "G01"  # G00, G01, G02, G03, etc.
    x: float | None = None
    y: float | None = None
    i: float | None = None
    j: float | None = None


class Contour(BaseModel):
    """Collection of commands forming a single continuous path."""

    commands: list[ContourCommand] = []


class GncPartData(BaseModel):
    """Data for a single part found within a GNC file."""

    sku: str
    version: str = "A"
    qty: int = 1
    contours: list[Contour] = []


class GncSheet(BaseModel):
    """Result of parsing a GNC nesting file."""

    sheet_x: float | None = None
    sheet_y: float | None = None
    thickness: float | None = None
    sheet_qty: int | None = None
    gnc_date: datetime.datetime | None = None
    mat_code: str | None = None

    # Metrics for duration estimation
    cut_length_mm: float = 0.0
    idle_length_mm: float = 0.0
    total_contours: int = 0

    parts: list[GncPartData] = []


class GncParser:
    """
    Parses GNC (G-code) files to extract production metadata.
    Adapted from legacy DocuFlow MVP with enhanced SKU extraction and time estimation.
    """

    # Regex patterns
    RE_SHEET = re.compile(r"\(\*SHEET\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)", re.IGNORECASE)
    RE_MATERIAL = re.compile(r"\(Material[:=](.*?)\)", re.IGNORECASE)
    RE_PART_NAME = re.compile(r"\(PART NAME:(.*?)\)", re.IGNORECASE)
    RE_DATE = re.compile(r"\(DATE\s+(.*?)\)", re.IGNORECASE)
    RE_CONTOUR = re.compile(r"\(={4,}\s*CONTOUR\s+(\d+)\s+={4,}\)", re.IGNORECASE)

    # G-code patterns
    RE_G00 = re.compile(r"G00|G0\s", re.IGNORECASE)
    RE_G01_3 = re.compile(r"G(0[123]|[123])", re.IGNORECASE)
    RE_COORD = re.compile(r"([XY])([+-]?\d*\.?\d+)", re.IGNORECASE)

    def parse(self, file_path: Path) -> GncSheet:
        """
        Reads and parses a GNC file.
        Returns GncSheet object with extracted data.
        Does not raise on parsing errors (graceful fallback).
        """
        sheet = GncSheet()
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return sheet

        lines = content.splitlines()

        last_x, last_y = 0.0, 0.0
        is_laser_on = False

        current_part: GncPartData | None = None
        current_contour: Contour | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 1. Metadata Parsing
            if not sheet.sheet_x:
                m = self.RE_SHEET.search(line)
                if m:
                    sheet.sheet_x = float(m.group(1))
                    sheet.sheet_y = float(m.group(2))
                    sheet.thickness = float(m.group(3))
                    sheet.sheet_qty = int(m.group(4))

            if not sheet.mat_code:
                m = self.RE_MATERIAL.search(line)
                if m:
                    sheet.mat_code = m.group(1).strip()

            if not sheet.gnc_date:
                m = self.RE_DATE.search(line)
                if m:
                    try:
                        # Attempt standard date parse: "JUL 10 2025"
                        sheet.gnc_date = datetime.datetime.strptime(m.group(1).strip(), "%b %d %Y")
                    except ValueError:
                        pass

            # 2. Part Detection
            m = self.RE_PART_NAME.search(line)
            if m:
                sku, version = self.extract_sku(m.group(1))
                # Check if we already have this SKU-Version in this sheet to increment qty
                found = False
                for p in sheet.parts:
                    if p.sku == sku and p.version == version:
                        p.qty += 1
                        current_part = p
                        found = True
                        break
                if not found:
                    current_part = GncPartData(sku=sku, version=version)
                    sheet.parts.append(current_part)

                # Reset current contour for new part section
                current_contour = None

            # 3. Contour Detection
            if self.RE_CONTOUR.search(line):
                sheet.total_contours += 1
                if current_part is not None:
                    current_contour = Contour()
                    current_part.contours.append(current_contour)

            # 4. G-Code Path Calculation & Command Collection
            # Find coordinates
            coords = self.RE_COORD.findall(line)

            # Identify command type
            cmd_type = "MODAL"
            if self.RE_G00.search(line):
                cmd_type = "G00"
            elif self.RE_G01_3.search(line):
                m_cmd = self.RE_G01_3.search(line)
                if m_cmd:
                    cmd_val = m_cmd.group(1)
                    cmd_type = f"G{int(cmd_val):02d}"

            if coords or cmd_type != "MODAL":
                new_x, new_y = last_x, last_y
                new_i, new_j = None, None

                # Extract I/J if present (for arcs)
                m_i = re.search(r"I([+-]?\d*\.?\d+)", line, re.I)
                m_j = re.search(r"J([+-]?\d*\.?\d+)", line, re.I)
                if m_i:
                    new_i = float(m_i.group(1))
                if m_j:
                    new_j = float(m_j.group(1))

                for axis, val in coords:
                    if axis.upper() == "X":
                        new_x = float(val)
                    if axis.upper() == "Y":
                        new_y = float(val)

                dist = ((new_x - last_x) ** 2 + (new_y - last_y) ** 2) ** 0.5

                # Logic for metrics
                is_idle = cmd_type == "G00"
                is_cut = cmd_type in ["G01", "G02", "G03"]

                if "LASER_ON" in line:
                    is_laser_on = True
                if "LASER_OFF" in line:
                    is_laser_on = False

                if is_idle:
                    sheet.idle_length_mm += dist
                elif is_cut or is_laser_on:
                    sheet.cut_length_mm += dist

                # Store command if we are within a contour
                if current_contour is not None:
                    current_contour.commands.append(
                        ContourCommand(
                            type=cmd_type,
                            x=new_x if "X" in line.upper() else None,
                            y=new_y if "Y" in line.upper() else None,
                            i=new_i,
                            j=new_j,
                        )
                    )

                last_x, last_y = new_x, new_y

        return sheet

    @staticmethod
    def extract_sku(raw: str) -> tuple[str, str]:
        """
        Extracts Base SKU and Version from raw string.
        Logic:
           - "3433-11-004-G-1" -> SKU="3433-11-004", Version="G"
           - "PART-A"          -> SKU="PART", Version="A"
           - "SIMPLE"          -> SKU="SIMPLE", Version="A"
        """
        # Strip path and extension
        name = raw.strip().split("\\")[-1]
        name = re.sub(r"\.\w+$", "", name).strip()

        parts = name.split("-")

        # 1. Pop trailing meaningless digit (nesting ordinal)
        if len(parts) > 1 and parts[-1].isdigit():
            parts.pop()

        # 2. Extract Version (last remaining segment)
        if len(parts) > 1:
            version = parts.pop()
            sku = "-".join(parts)
            return sku, version

        return name, "A"

    def estimate_time(self, sheet: GncSheet, mat_type: MaterialType) -> int:
        """
        Estimates production time in minutes based on material parameters.
        Formula: (pierce + cut + idle) * sheet_qty
        """
        # Seconds calculation
        pierce_sec = sheet.total_contours * mat_type.pierce_time_sec
        cut_sec = (sheet.cut_length_mm / mat_type.cut_speed_mm_per_min) * 60
        idle_sec = (sheet.idle_length_mm / mat_type.idle_speed_mm_per_min) * 60

        total_sec = (pierce_sec + cut_sec + idle_sec) * (sheet.sheet_qty or 1)

        # Apply tolerance and convert to minutes
        total_min = (total_sec / 60) * (1 + mat_type.time_tolerance_pct / 100)

        return max(1, int(total_min))
