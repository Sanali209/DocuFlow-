import re
from .gnc_parser import GNCSheet, GNCPart, GNCContour, GNCCommand

class GNCGenerator:
    def __init__(self):
        pass

    def generate(self, sheet: GNCSheet) -> str:
        """
        Reconstructs the GNC file content from the GNCSheet object.
        Applies updates from metadata to the corresponding lines.
        """
        lines = []

        # Flatten structure: Parts -> Contours -> Commands

        for part in sheet.parts:
            # Note: The parser now preserves the `(PART NAME:...)` line as a METADATA command
            # in the part's contour list (usually Contour 0).
            # So we do NOT need to synthesize it here.

            for contour in part.contours:
                for cmd in contour.commands:
                    line_text = cmd.original_text

                    # Update SHEET line if present
                    if "(*SHEET" in line_text or "(*SHEET" in line_text.upper():
                        if sheet.program_width is not None and sheet.program_height is not None:
                            # Reconstruct SHEET line with updated values
                            param_5 = sheet.metadata.get('sheet_param_5', '1')
                            param_6 = sheet.metadata.get('sheet_param_6', '0.0')
                            param_7 = sheet.metadata.get('sheet_param_7', '0.0')
                            
                            # Preserve line number prefix if present (for _801 format)
                            if line_text.strip().startswith('N'):
                                # Extract line number
                                n_match = re.match(r'(N\d+\s+)', line_text.strip())
                                prefix = n_match.group(1) if n_match else ''
                                line_text = f"{prefix}(*SHEET {sheet.program_width} {sheet.program_height} {sheet.thickness or 0} {sheet.cut_count or 1} {param_5} {param_6} {param_7} )"
                            else:
                                line_text = f"(*SHEET {sheet.program_width} {sheet.program_height} {sheet.thickness or 0} {sheet.cut_count or 1} {param_5} {param_6} {param_7} )"

                    # Update P-Codes in Metadata lines
                    if cmd.type == "METADATA":
                        # Office format: *N P-codes (existing)
                        if line_text.strip().startswith("*N") and "P" in line_text:
                            # Check if it's _801 format (P660=X,P150=Y,P151=Z)
                            if "P660=" in line_text:
                                # _801 format P-codes
                                p660 = contour.metadata.get('P660', '1')
                                p150 = contour.metadata.get('P150', '1')
                                p151 = contour.metadata.get('P151', '1')
                                line_text = re.sub(
                                    r'P660=\d+,P150=\d+,P151=\d+',
                                    f'P660={p660},P150={p150},P151={p151}',
                                    line_text
                                )
                            else:
                                # Office format: P###=value
                                def replace_pcode(match):
                                    key = match.group(1)
                                    meta_key = f"P{key}"
                                    if meta_key in contour.metadata:
                                        new_val = str(contour.metadata[meta_key])
                                        return f"P{key}={new_val}"
                                    return match.group(0)

                                line_text = re.sub(r'P(\d+)=([^\s,]+)', replace_pcode, line_text)

                    lines.append(line_text)

        return "\n".join(lines)

    def _apply_offsets(self, line_text: str, offset_x: float, offset_y: float) -> str:
        """
        Apply X and Y offsets to coordinates in the line.
        Assumes absolute positioning (G90).
        """
        if offset_x == 0 and offset_y == 0:
            return line_text

        # Regex to find X and Y values
        # We look for X followed by a number, potentially negative/decimal
        def replace_coord(match):
            axis = match.group(1).upper()
            val_str = match.group(2)
            try:
                val = float(val_str)
                if axis == 'X':
                    return f"X{val + offset_x:.3f}"
                elif axis == 'Y':
                    return f"Y{val + offset_y:.3f}"
            except ValueError:
                pass
            return match.group(0)

        # Replace X
        if offset_x != 0:
            line_text = re.sub(r'([X])([+-]?\d*\.?\d+)', replace_coord, line_text, flags=re.IGNORECASE)
        
        # Replace Y
        if offset_y != 0:
            line_text = re.sub(r'([Y])([+-]?\d*\.?\d+)', replace_coord, line_text, flags=re.IGNORECASE)
            
        return line_text

    def generate(self, sheet: GNCSheet) -> str:
        """
        Reconstructs the GNC file content from the GNCSheet object.
        Applies updates from metadata to the corresponding lines.
        """
        lines = []

        # Flatten structure: Parts -> Contours -> Commands

        for part in sheet.parts:
            # Note: The parser now preserves the `(PART NAME:...)` line as a METADATA command
            # in the part's contour list (usually Contour 0).
            
            # Determine Offsets for this Part
            # We use loose typing access because Pydantic model might not have x/y fields defined
            # if they were added dynamically in frontend/JSON. 
            # But wait, GNCSheet.parts is List[GNCPart]. GNCPart doesn't have x/y.
            # We need to make sure the data passed to generate() includes x/y or logic to extract it.
            # The input `sheet` is a GNCSheet object.
            # If we want to support offsets, we need to know them.
            # The frontend sends JSON which *has* x/y. 
            # But FastAPI/Pydantic validation might strip extra fields if not in model!
            # We must update GNCPart model to include x/y (Defaults to 0).
            
            offset_x = getattr(part, 'x', 0.0) or 0.0
            offset_y = getattr(part, 'y', 0.0) or 0.0

            for contour in part.contours:
                for cmd in contour.commands:
                    line_text = cmd.original_text
                    if not line_text: continue

                    # Update SHEET line if present
                    if "(*SHEET" in line_text or "(*SHEET" in line_text.upper():
                        if sheet.program_width is not None and sheet.program_height is not None:
                            # Reconstruct SHEET line with updated values
                            param_5 = sheet.metadata.get('sheet_param_5', '1')
                            param_6 = sheet.metadata.get('sheet_param_6', '0.0')
                            param_7 = sheet.metadata.get('sheet_param_7', '0.0')
                            
                            # Preserve line number prefix if present (for _801 format)
                            if line_text.strip().startswith('N'):
                                # Extract line number
                                n_match = re.match(r'(N\d+\s+)', line_text.strip())
                                prefix = n_match.group(1) if n_match else ''
                                line_text = f"{prefix}(*SHEET {sheet.program_width} {sheet.program_height} {sheet.thickness or 0} {sheet.cut_count or 1} {param_5} {param_6} {param_7} )"
                            else:
                                line_text = f"(*SHEET {sheet.program_width} {sheet.program_height} {sheet.thickness or 0} {sheet.cut_count or 1} {param_5} {param_6} {param_7} )"

                    # Update P-Codes in Metadata lines
                    if cmd.type == "METADATA":
                        # Office format: *N P-codes (existing)
                        if line_text.strip().startswith("*N") and "P" in line_text:
                            # Check if it's _801 format (P660=X,P150=Y,P151=Z)
                            if "P660=" in line_text:
                                # _801 format P-codes
                                p660 = contour.metadata.get('P660', '1')
                                p150 = contour.metadata.get('P150', '1')
                                p151 = contour.metadata.get('P151', '1')
                                line_text = re.sub(
                                    r'P660=\d+,P150=\d+,P151=\d+',
                                    f'P660={p660},P150={p150},P151={p151}',
                                    line_text
                                )
                            else:
                                # Office format: P###=value
                                def replace_pcode(match):
                                    key = match.group(1)
                                    meta_key = f"P{key}"
                                    if meta_key in contour.metadata:
                                        new_val = str(contour.metadata[meta_key])
                                        return f"P{key}={new_val}"
                                    return match.group(0)

                                line_text = re.sub(r'P(\d+)=([^\s,]+)', replace_pcode, line_text)
                    
                    # Apply Coordinate Offsets (for G-codes)
                    if cmd.type not in ["METADATA", "COMMENT"]:
                         line_text = self._apply_offsets(line_text, offset_x, offset_y)

                    lines.append(line_text)

        return "\n".join(lines)
