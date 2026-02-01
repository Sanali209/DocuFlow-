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

                    # Update P-Codes in Metadata lines
                    if cmd.type == "METADATA" and line_text.strip().startswith("*N"):
                        # Regex: `P(\d+)=([^\s]+)`
                        def replace_pcode(match):
                            key = match.group(1)
                            # current_val = match.group(2)
                            meta_key = f"P{key}"
                            if meta_key in contour.metadata:
                                new_val = str(contour.metadata[meta_key])
                                return f"P{key}={new_val}"
                            return match.group(0)

                        line_text = re.sub(r'P(\d+)=([^\s]+)', replace_pcode, line_text)

                    lines.append(line_text)

        return "\n".join(lines)
