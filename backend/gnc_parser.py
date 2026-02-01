from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re

class GNCCommand(BaseModel):
    type: str  # G00, G01, M30, METADATA, etc.
    command: Optional[str] = None # G, M, T
    value: Optional[float] = None # 0, 1, 30, etc.
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
    metadata: Dict[str, Any] = {}

    # Stats
    corner_count: int = 0
    length: float = 0.0

class GNCPart(BaseModel):
    id: int
    contours: List[GNCContour] = []
    name: Optional[str] = None
    metadata: Dict[str, Any] = {}

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
        g_code_pattern = re.compile(r'G(00|01|02|03|0|1|2|3)(?!\d)', re.IGNORECASE)
        command_pattern = re.compile(r'\b([GMT])(\d+(?:\.\d+)?)\b', re.IGNORECASE)
        coord_pattern = re.compile(r'([XYIJ])([+-]?\d*\.?\d+)', re.IGNORECASE)
        contour_start_pattern = re.compile(r'\(={4,}\s*CONTOUR\s+(\d+)\s+={4,}\)', re.IGNORECASE)
        part_info_pattern = re.compile(r'\(PART NAME:(.*?)\)', re.IGNORECASE)
        p_code_pattern = re.compile(r'P(\d+)=([^\s]+)', re.IGNORECASE)

        current_part = None
        current_contour = None

        lines = content.splitlines()
        part_counter = 1

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Ensure we have defaults if we encounter content
            if current_part is None:
                # If we hit a PART NAME tag later, we might switch, but for now use default
                # Logic: If line is PART NAME, we handle it below.
                pass

            # Check for Part Name (Implicit New Part)
            part_match = part_info_pattern.search(line)
            if part_match:
                p_name = part_match.group(1).strip()
                current_part = GNCPart(id=part_counter, name=p_name)
                part_counter += 1
                sheet.parts.append(current_part)
                current_contour = None

                # Store this line as METADATA command in the new part's first contour?
                # Or maybe Parts should have a list of 'Header Commands'?
                # For now, let's put it in a "Header" contour or the first contour.
                # Actually, strictly hierarchical: Part -> Contours -> Commands.
                # If we just started a part, we might need a dummy contour or "Part Header" contour.
                # Let's create a contour 0 or similar for header info?
                # Or just append to the next contour?
                # User wants "Code command end contain in contur".
                # Let's create a default contour if needed.
                if current_contour is None:
                    current_contour = GNCContour(id=0) # 0 for header/metadata
                    current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Check for Contour Separator
            contour_match = contour_start_pattern.search(line)
            if contour_match:
                cid = int(contour_match.group(1))

                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                current_contour = GNCContour(id=cid)
                current_part.contours.append(current_contour)

                # Store the separator line itself
                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Check for P-Codes (Metadata)
            if line.startswith('*N'):
                # Extract P-codes to metadata
                matches = p_code_pattern.findall(line)
                if matches and current_contour:
                    for key, val in matches:
                        current_contour.metadata[f"P{key}"] = val

                # Store line as METADATA command
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)
                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Parse Commands (G/M/T)
            commands_found = command_pattern.findall(line)

            if commands_found:
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                coords = coord_pattern.findall(line)
                line_coords = {}
                for axis, value in coords:
                    line_coords[axis.lower()] = float(value)

                for prefix, val_str in commands_found:
                    prefix = prefix.upper()
                    value = float(val_str)
                    type_str = f"{prefix}{int(value):02d}" if prefix in ['G', 'M'] else f"{prefix}{value}"

                    cmd = GNCCommand(
                        type=type_str,
                        command=prefix,
                        value=value,
                        line_number=i+1,
                        original_text=line # Note: this duplicates text for every cmd in line
                    )

                    if prefix == 'G':
                        if 'x' in line_coords: cmd.x = line_coords['x']
                        if 'y' in line_coords: cmd.y = line_coords['y']
                        if 'i' in line_coords: cmd.i = line_coords['i']
                        if 'j' in line_coords: cmd.j = line_coords['j']

                    current_contour.commands.append(cmd)

            elif coord_pattern.search(line):
                # Modal Line
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)
                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                coords = coord_pattern.findall(line)
                cmd = GNCCommand(type="MODAL", line_number=i+1, original_text=line)
                for axis, value in coords:
                    val = float(value)
                    if axis.upper() == 'X': cmd.x = val
                    elif axis.upper() == 'Y': cmd.y = val
                    elif axis.upper() == 'I': cmd.i = val
                    elif axis.upper() == 'J': cmd.j = val
                current_contour.commands.append(cmd)

            else:
                # Other lines (comments, empty, etc.) not caught above
                # Store as METADATA/COMMENT to preserve file structure
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)
                if current_contour is None:
                    current_contour = GNCContour(id=0) # Header/Misc contour
                    current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
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
                # Basic stats: Count motion commands (G00, G01, G02, G03)
                motion_cmds = [c for c in contour.commands if c.command == 'G' and c.value in [0, 1, 2, 3]]
                contour.corner_count = len(motion_cmds)
                part_corner_count += contour.corner_count
                sheet.total_contours += 1
            part.corner_count = part_corner_count
