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
