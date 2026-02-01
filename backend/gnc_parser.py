from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re

class GNCCommand(BaseModel):
    type: str  # G00, G01, M30, T1, etc.
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
        # Updated to capture G, M, T commands.
        # Captures G01, M30, T1 as (Prefix, Value)
        # Matches Start of line or space followed by Letter+Number
        # Be careful not to match coordinates like X10 as commands, though X is usually coordinate.
        # Standard commands: G, M, T, S, F.
        # We focus on G and M for now as structural/control commands.
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

                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                current_contour = GNCContour(id=cid)
                current_part.contours.append(current_contour)
                continue

            # Check for P-Codes
            if line.startswith('*N'):
                matches = p_code_pattern.findall(line)
                if matches and current_contour:
                    for key, val in matches:
                        current_contour.metadata[f"P{key}"] = val
                continue

            # Parse Commands
            # Find all commands in the line (e.g. N10 G01 X10 Y10 M03)
            # We treat N numbers as line numbers/labels, not commands usually.

            # Search for G/M/T codes
            commands_found = command_pattern.findall(line)

            if commands_found:
                if current_part is None:
                    current_part = GNCPart(id=part_counter, name="Main Part")
                    part_counter += 1
                    sheet.parts.append(current_part)

                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                # Extract coordinates once for the line (assuming single motion per line)
                coords = coord_pattern.findall(line)
                line_coords = {}
                for axis, value in coords:
                    line_coords[axis.lower()] = float(value)

                # Create GNCCommand objects for each command found
                for prefix, val_str in commands_found:
                    prefix = prefix.upper()
                    value = float(val_str)

                    # Normalize Type string (e.g. G1 -> G01)
                    type_str = f"{prefix}{int(value):02d}" if prefix in ['G', 'M'] else f"{prefix}{value}"

                    cmd = GNCCommand(
                        type=type_str,
                        command=prefix,
                        value=value,
                        line_number=i+1,
                        original_text=line
                    )

                    # Attach coordinates only if it's a G-code (motion)
                    # Or attach to all? Usually coordinates belong to the motion G-code.
                    if prefix == 'G':
                        if 'x' in line_coords: cmd.x = line_coords['x']
                        if 'y' in line_coords: cmd.y = line_coords['y']
                        if 'i' in line_coords: cmd.i = line_coords['i']
                        if 'j' in line_coords: cmd.j = line_coords['j']

                    current_contour.commands.append(cmd)

            elif coord_pattern.search(line) and not commands_found:
                # Coordinate only line (modal G-code)?
                # E.g. "X10 Y10" implies previous G code (usually G01/G00)
                # For now, we can create a "Implicit" command or assume G01 if uncertain,
                # OR just treat it as a continuation.
                # To be safe and simple, we might skip creating a formal Command if no G/M code is present,
                # BUT this loses geometry.
                # Let's assume it's a G01 if valid coordinates exist but no G code.
                # NOTE: Complex parsers track state (Modal G code).
                # For this MVP, we might miss "X10" lines if we require "G1 X10".
                # Let's add a fallback: if coords exist but no command, create a "Modal" command.

                if current_contour:
                    coords = coord_pattern.findall(line)
                    cmd = GNCCommand(
                        type="MODAL",
                        line_number=i+1,
                        original_text=line
                    )
                    for axis, value in coords:
                        val = float(value)
                        if axis.upper() == 'X': cmd.x = val
                        elif axis.upper() == 'Y': cmd.y = val
                        elif axis.upper() == 'I': cmd.i = val
                        elif axis.upper() == 'J': cmd.j = val

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
