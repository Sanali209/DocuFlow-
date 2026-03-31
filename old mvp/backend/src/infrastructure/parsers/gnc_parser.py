from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re
import os

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
    x: Optional[float] = 0.0
    y: Optional[float] = 0.0
    metadata: Dict[str, Any] = {}

    # Stats
    corner_count: int = 0

class GNCSheet(BaseModel):
    name: Optional[str] = None
    task_id: Optional[int] = None
    parts: List[GNCPart] = []
    header_commands: List[GNCCommand] = [] # Captured global headers
    metadata: Dict[str, Any] = {}

    # Stats
    total_parts: int = 0
    total_contours: int = 0

    # Material info
    material: Optional[str] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    
    # SHEET metadata (*SHEET line)
    program_width: Optional[float] = None   # Position 1: program width in mm
    program_height: Optional[float] = None  # Position 2: program height in mm
    cut_count: Optional[int] = None         # Position 4: number of times to cut

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

        # Sheet metadata patterns
        sheet_detail_pattern = re.compile(r'\(\*SHEET\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)', re.IGNORECASE)
        model_tag_pattern = re.compile(r'\(\*MODEL\s+(.*)\)', re.IGNORECASE)
        material_tag_pattern = re.compile(r'\(Material[:=](.*?)\)', re.IGNORECASE)
        thickness_tag_pattern = re.compile(r'\(THICKNESS=(.*?)\)', re.IGNORECASE)
        
        # _801 format P-code pattern: *N1145 P660=190,P150=1,P151=1
        p_code_801_pattern = re.compile(r'\*N\d+\s+P660=(\d+),P150=(\d+),P151=(\d+)', re.IGNORECASE)

        current_part = None
        current_contour = None

        lines = content.splitlines()
        part_counter = 1
        
        # Detect starting N-code and step
        n_codes_found = []
        for line in lines[:200]: # Look at first 200 lines for efficiency
            match = re.search(r'^N(\d+)', line.strip())
            if match:
                n_codes_found.append(int(match.group(1)))
                if len(n_codes_found) >= 2:
                    break
        
        if len(n_codes_found) >= 2:
            sheet.metadata['n_code_start'] = n_codes_found[0]
            sheet.metadata['n_code_step'] = n_codes_found[1] - n_codes_found[0]
        elif len(n_codes_found) == 1:
            sheet.metadata['n_code_start'] = n_codes_found[0]

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Parse SHEET metadata line (detailed)
            sheet_detail_match = sheet_detail_pattern.search(line)
            if sheet_detail_match:
                try:
                    sheet.program_width = float(sheet_detail_match.group(1))
                    sheet.program_height = float(sheet_detail_match.group(2))
                    sheet.thickness = float(sheet_detail_match.group(3))
                    sheet.cut_count = int(sheet_detail_match.group(4))
                    sheet.metadata['sheet_param_5'] = sheet_detail_match.group(5)
                    sheet.metadata['sheet_param_6'] = sheet_detail_match.group(6)
                    sheet.metadata['sheet_param_7'] = sheet_detail_match.group(7)
                except (ValueError, IndexError):
                    pass

            model_match = model_tag_pattern.search(line)
            if model_match:
                sheet.metadata['model'] = model_match.group(1).strip()

            material_match = material_tag_pattern.search(line)
            if material_match:
                mat = material_match.group(1).strip()
                sheet.material = mat
                sheet.metadata['material'] = mat

            thickness_match = thickness_tag_pattern.search(line)
            if thickness_match:
                try:
                    thk = float(thickness_match.group(1).strip())
                    if sheet.thickness is None:  # Don't override SHEET line value
                        sheet.thickness = thk
                    sheet.metadata['thickness'] = thk
                except ValueError:
                    pass
            
            # Check for _801 format P-codes
            p_code_801_match = p_code_801_pattern.search(line)
            if p_code_801_match:
                if current_part is None:
                    # Use filename as default part name if not set
                    default_name = os.path.basename(filename).replace('.gnc', '').replace('.GNC', '')
                    current_part = GNCPart(id=part_counter, name=f"{default_name} (Auto)")
                    part_counter += 1
                    sheet.parts.append(current_part)
                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)
                
                current_contour.metadata['P660'] = p_code_801_match.group(1)
                current_contour.metadata['P150'] = p_code_801_match.group(2)
                current_contour.metadata['P151'] = p_code_801_match.group(3)
                
                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Check for Part Name (Implicit New Part)
            part_match = part_info_pattern.search(line)
            if part_match:
                p_name = part_match.group(1).strip()
                current_part = GNCPart(id=part_counter, name=p_name)
                part_counter += 1
                sheet.parts.append(current_part)
                current_contour = GNCContour(id=1)
                current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Check for Contour Separator
            contour_match = contour_start_pattern.search(line)
            if contour_match:
                cid = int(contour_match.group(1))

                if current_part is None:
                    # Use filename as default part name if not set
                    default_name = os.path.basename(filename).replace('.gnc', '').replace('.GNC', '')
                    current_part = GNCPart(id=part_counter, name=f"{default_name} (Auto)")
                    part_counter += 1
                    sheet.parts.append(current_part)

                current_contour = GNCContour(id=cid)
                current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)
                continue

            # Check for P-Codes (Metadata) on *N lines, but don't skip yet recursively
            # because *N lines can also contain G-codes and coordinates!
            if line.startswith('*N'):
                matches = p_code_pattern.findall(line)
                if matches and current_contour:
                    for key, val in matches:
                        current_contour.metadata[f"P{key}"] = val
                
                # If it's JUST metadata, we can continue. But if it has G, X, Y etc, stay.
                is_only_metadata = not (re.search(r'[GX-YIJT]', line, re.I))
                if is_only_metadata and matches:
                    if current_part is None:
                        # Use filename as default part name if not set
                        default_name = os.path.basename(filename).replace('.gnc', '').replace('.GNC', '')
                        current_part = GNCPart(id=part_counter, name=f"{default_name} (Auto)")
                        part_counter += 1
                        sheet.parts.append(current_part)
                    if current_contour is None:
                        current_contour = GNCContour(id=1)
                        current_part.contours.append(current_contour)

                    cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                    current_contour.commands.append(cmd)
                    continue

            # Parse Commands (G/M/T) - this will now also catch *N lines that have G-codes
            commands_found = command_pattern.findall(line)

            if commands_found:
                if current_part is None:
                    # Capture header commands before any part is detected
                    cmd = GNCCommand(type="HEADER", line_number=i+1, original_text=line)
                    sheet.header_commands.append(cmd)
                    continue

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
                        original_text=line # Note: duplicates text
                    )

                    # Always try to assign coordinates if they exist on the line, 
                    # as modal commands or line numbers (N) often accompany them.
                    if 'x' in line_coords: cmd.x = line_coords['x']
                    if 'y' in line_coords: cmd.y = line_coords['y']
                    if 'i' in line_coords: cmd.i = line_coords['i']
                    if 'j' in line_coords: cmd.j = line_coords['j']

                    current_contour.commands.append(cmd)

            elif coord_pattern.search(line):
                # Modal Line
                if current_part is None:
                    # Capture header commands before any part is detected
                    cmd = GNCCommand(type="HEADER", line_number=i+1, original_text=line)
                    sheet.header_commands.append(cmd)
                    continue

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
                # Other lines (comments, metadata)
                # Check metadata tags again here? Already done at start of loop.
                # If it was a metadata tag, we likely want to store it as a command too to preserve it?
                # Yes, unless we want to strip it. To support "faithful regeneration", we should keep it.

                if current_part is None:
                    # Capture header commands before any part is detected
                    cmd = GNCCommand(type="HEADER", line_number=i+1, original_text=line)
                    sheet.header_commands.append(cmd)
                    continue

                if current_contour is None:
                    current_contour = GNCContour(id=1)
                    current_part.contours.append(current_contour)

                cmd = GNCCommand(type="METADATA", line_number=i+1, original_text=line)
                current_contour.commands.append(cmd)

        self._post_process(sheet)
        return sheet

    def _post_process(self, sheet: GNCSheet):
        """
        Calculate stats and clean up redundant parts.
        """
        # Distinguish between "Auto" parts (created from filename) and "Real" parts (found via metadata)
        real_parts = [p for p in sheet.parts if not (p.name and p.name.endswith("(Auto)"))]
        auto_parts = [p for p in sheet.parts if p.name and p.name.endswith("(Auto)")]

        # If it's a sheet (nesting file) OR we found real parts, discard the Auto ones
        is_sheet = sheet.program_width is not None or sheet.thickness is not None
        if (real_parts and auto_parts) or (is_sheet and auto_parts):
            # Preserve commands from Auto parts (like header comments) by moving them to the first real part
            if real_parts:
                for auto_p in auto_parts:
                    # Prepend auto_p contours to the first real part's contours
                    real_parts[0].contours = auto_p.contours + real_parts[0].contours
            sheet.parts = real_parts
        
        sheet.total_parts = len(sheet.parts)
        sheet.total_contours = 0

        for part in sheet.parts:
            part_corner_count = 0
            for contour in part.contours:
                # Basic stats: Count motion commands (G00, G01, G02, G03)
                motion_cmds = [c for c in contour.commands if c.command == 'G' and c.value in [0, 1, 2, 3]]
                # Also count MODAL commands that have coordinates (treated as G01 usually)
                motion_cmds += [c for c in contour.commands if c.type == "MODAL" and (c.x is not None or c.y is not None)]
                
                contour.corner_count = len(motion_cmds)
                part_corner_count += contour.corner_count
                sheet.total_contours += 1
            part.corner_count = part_corner_count
