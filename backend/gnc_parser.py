from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re

class Command(BaseModel):
    type: str  # G00, G01, G02, G03
    x: Optional[float] = None
    y: Optional[float] = None
    i: Optional[float] = None
    j: Optional[float] = None
    line_number: Optional[int] = None
    original_text: Optional[str] = None

class Contour(BaseModel):
    id: int
    commands: List[Command] = []
    is_closed: bool = False
    is_hole: bool = False

    # Stats
    corner_count: int = 0
    length: float = 0.0

class Part(BaseModel):
    id: int
    contours: List[Contour] = []
    name: Optional[str] = None

    # Stats
    corner_count: int = 0

class Sheet(BaseModel):
    parts: List[Part] = []
    metadata: Dict[str, Any] = {}

    # Stats
    total_parts: int = 0
    total_contours: int = 0

    # Material info
    material: Optional[str] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

class GNCParser:
    def __init__(self):
        self.office_mode = False

    def parse(self, content: str, filename: str = "") -> Sheet:
        """
        Parses GNC content and returns a Sheet object with Parts and Contours.
        """
        # Detect mode
        if content.startswith("%") or "_801" in filename:
            self.office_mode = False # Machine mode
        else:
            self.office_mode = True # Default/Office mode

        sheet = Sheet()

        # Regex patterns
        g_code_pattern = re.compile(r'(G00|G01|G02|G03|G0|G1|G2|G3)', re.IGNORECASE)
        coord_pattern = re.compile(r'([XYIJ])([+-]?\d*\.?\d+)', re.IGNORECASE)
        contour_start_pattern = re.compile(r'\(===== CONTOUR (\d+) =====\)')

        current_part = None
        current_contour = None

        if self.office_mode:
            # Office Mode: Treat entire file as one Part
            current_part = Part(id=1, name="Main Part")
            sheet.parts.append(current_part)

            # Start first contour
            current_contour = Contour(id=1)
            current_part.contours.append(current_contour)

        lines = content.splitlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check for Contour Separator (Machine Mode)
            contour_match = contour_start_pattern.search(line)
            if contour_match:
                # In Machine Mode, we treat each CONTOUR block as a separate Part for now,
                # or a new Contour in the current Part?
                # User Requirement: "part sheets contain parts parts contain contours"
                # Assumption: The GNC file represents a Sheet. The "CONTOUR" blocks are likely Parts.

                cid = int(contour_match.group(1))

                # Create a new Part for this block
                current_part = Part(id=cid, name=f"Part {cid}")
                sheet.parts.append(current_part)

                # Create a contour for this part
                current_contour = Contour(id=1) # First contour of this part
                current_part.contours.append(current_contour)
                continue

            # Check for P-Codes (Metadata)
            if line.startswith('*N'):
                continue

            # Parse G-Code
            g_match = g_code_pattern.search(line)
            if g_match:
                cmd_type = g_match.group(1).upper()
                if len(cmd_type) == 2:
                    cmd_type = cmd_type[0] + '0' + cmd_type[1]

                cmd = Command(type=cmd_type, line_number=i+1, original_text=line)

                # Extract coordinates
                coords = coord_pattern.findall(line)
                for axis, value in coords:
                    val = float(value)
                    if axis.upper() == 'X':
                        cmd.x = val
                    elif axis.upper() == 'Y':
                        cmd.y = val
                    elif axis.upper() == 'I':
                        cmd.i = val
                    elif axis.upper() == 'J':
                        cmd.j = val

                if current_contour:
                    current_contour.commands.append(cmd)
                elif not self.office_mode:
                    # G-code found outside a contour block in machine mode
                    # Might be header/footer, ignore for now
                    pass

        self._post_process(sheet)
        return sheet

    def _post_process(self, sheet: Sheet):
        """
        Calculate stats.
        """
        sheet.total_parts = len(sheet.parts)
        sheet.total_contours = 0

        for part in sheet.parts:
            part_corner_count = 0
            for contour in part.contours:
                # Basic stats
                contour.corner_count = len(contour.commands)
                part_corner_count += contour.corner_count
                sheet.total_contours += 1
            part.corner_count = part_corner_count
