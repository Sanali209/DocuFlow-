from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re

class GNCCommand(BaseModel):
    type: str  # G00, G01, G02, G03
    x: Optional[float] = None
    y: Optional[float] = None
    i: Optional[float] = None
    j: Optional[float] = None
    line_number: Optional[int] = None
    original_text: Optional[str] = None

class GNCContour(BaseModel):
    id: int
    commands: List[GNCCommand] = []
    is_closed: bool = False
    is_hole: bool = False

    # Stats
    corner_count: int = 0
    length: float = 0.0

class GNCPart(BaseModel):
    id: int
    contours: List[GNCContour] = []
    name: Optional[str] = None

    # Stats
    corner_count: int = 0

class GNCSheet(BaseModel):
    parts: List[GNCPart] = []
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

    def parse(self, content: str, filename: str = "") -> GNCSheet:
        """
        Parses GNC content and returns a GNCSheet object with GNCParts and GNCContours.
        """
        # Detect mode
        if content.startswith("%") or "_801" in filename:
            self.office_mode = False # Machine mode
        else:
            self.office_mode = True # Default/Office mode

        sheet = GNCSheet()

        # Regex patterns
        # Updated G-code pattern to avoid false positives like G3015 matching G3
        g_code_pattern = re.compile(r'G(00|01|02|03|0|1|2|3)(?!\d)', re.IGNORECASE)
        coord_pattern = re.compile(r'([XYIJ])([+-]?\d*\.?\d+)', re.IGNORECASE)
        # Handle 4 or more equals signs
        contour_start_pattern = re.compile(r'\(={4,}\s*CONTOUR\s+(\d+)\s+={4,}\)', re.IGNORECASE)
        part_info_pattern = re.compile(r'\(PART NAME:(.*?)\)', re.IGNORECASE)

        current_part = None
        current_contour = None

        lines = content.splitlines()
        part_counter = 1

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check for Part Name (Implicit New Part)
            part_match = part_info_pattern.search(line)
            if part_match:
                p_name = part_match.group(1).strip()
                current_part = GNCPart(id=part_counter, name=p_name)
                part_counter += 1
                sheet.parts.append(current_part)
                # Reset contour when new part starts
                current_contour = None
                continue

            # Check for Contour Separator
            contour_match = contour_start_pattern.search(line)
            if contour_match:
                cid = int(contour_match.group(1))

                # If no part exists yet, create a default one
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                # Add contour to current part
                current_contour = GNCContour(id=cid)
                current_part.contours.append(current_contour)
                continue

            # Check for P-Codes (Metadata)
            if line.startswith('*N'):
                continue

            # Parse G-Code
            g_match = g_code_pattern.search(line)
            if g_match:

                # If G-code is found but no part/contour exists, we need defaults.
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                if current_contour is None:
                    # Create a default contour if none active (e.g. commands outside CONTOUR block)
                    # For Office Mode, this effectively puts everything in one contour if no blocks used
                    # Use a generic ID or counter
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                cmd_type = g_match.group(1).upper()
                # Normalize G0, G1 etc to G00, G01
                if len(cmd_type) == 1:
                    cmd_type = '0' + cmd_type
                if not cmd_type.startswith('G'):
                    cmd_type = 'G' + cmd_type

                cmd = GNCCommand(type=cmd_type, line_number=i+1, original_text=line)

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

                current_contour.commands.append(cmd)

        self._post_process(sheet)
        return sheet

    def _post_process(self, sheet: GNCSheet):
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
