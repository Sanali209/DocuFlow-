import math
from typing import Tuple, Optional
from ..parsers.gnc_parser import GNCPart, GNCSheet

class SVGGenerator:
    """
    Generates SVG thumbnails from GNC parts.
    Ported from GncCanvas.svelte rendering logic.
    """
    
    def calculate_bounds(self, part: GNCPart) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding box of a GNC part.
        Returns (min_x, min_y, max_x, max_y)
        """
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        has_points = False
        
        for contour in part.contours:
            current_x = 0.0
            current_y = 0.0
            
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
    
    def generate_thumbnail(self, part: Optional[GNCPart], output_path: str, width: int = 200, height: int = 200) -> Tuple[float, float]:
        """
        Generate an SVG thumbnail for a GNC part.
        Returns (width, height) of the part in mm.
        """
        if part is None:
            # Create minimal SVG for empty data
            svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#1e1e1e"/>
  <text x="50%" y="50%" text-anchor="middle" fill="#666" font-size="12">No Data</text>
</svg>'''
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            return (0, 0)

        min_x, min_y, max_x, max_y = self.calculate_bounds(part)
        
        data_w = max_x - min_x
        data_h = max_y - min_y
        
        if data_w == 0 and data_h == 0:
            # Empty part, create minimal SVG
            svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#1e1e1e"/>
  <text x="50%" y="50%" text-anchor="middle" fill="#666" font-size="12">Empty</text>
</svg>'''
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            return (0, 0)
        
        # Calculate scale to fit within canvas
        padding = 10
        avail_w = width - padding * 2
        avail_h = height - padding * 2
        
        scale_x = avail_w / data_w if data_w > 0 else 1
        scale_y = avail_h / data_h if data_h > 0 else 1
        scale = min(scale_x, scale_y) * 0.95  # 0.95 safety factor
        
        # Calculate centering offset
        content_w = data_w * scale
        content_h = data_h * scale
        offset_x = (width - content_w) / 2
        offset_y = (height - content_h) / 2
        
        # Transform functions
        def tx(x: float) -> float:
            return offset_x + (x - min_x) * scale
        
        def ty(y: float) -> float:
            # Flip Y axis (SVG Y increases downward, GNC Y increases upward)
            return height - (offset_y + (y - min_y) * scale)
        
        # Generate SVG path data
        path_data = []
        
        for contour in part.contours:
            current_x = None
            current_y = None
            is_first_point = True
            
            for cmd in contour.commands:
                # Store previous position for arc calculations
                prev_x = current_x
                prev_y = current_y
                
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
                
                elif cmd.type == "G00" or (cmd.command == "G" and cmd.value == 0):
                    # Move to - treated as line to if not first point? G00 usually implies move without cut.
                    # For visualization, it acts as a move.
                    path_data.append(f"M {tx(current_x):.2f} {ty(current_y):.2f}")
                
                elif (cmd.type == "G01" or (cmd.command == "G" and cmd.value == 1) or
                      cmd.type == "MODAL" or cmd.type == "G41" or cmd.type == "G40"):
                    # Line to
                    path_data.append(f"L {tx(current_x):.2f} {ty(current_y):.2f}")
                
                elif (cmd.type == "G02" or cmd.type == "G03" or
                      (cmd.command == "G" and cmd.value in [2, 3])):
                    # Arc
                    if prev_x is not None and prev_y is not None:
                        # I and J are relative to the start point (prev_x, prev_y)
                        i_val = cmd.i if cmd.i is not None else 0.0
                        j_val = cmd.j if cmd.j is not None else 0.0
                        
                        center_x = prev_x + i_val
                        center_y = prev_y + j_val
                        
                        radius = math.sqrt(i_val**2 + j_val**2)
                        is_clockwise = (cmd.type == "G02" or (cmd.command == "G" and cmd.value == 2))
                        
                        # Calculate angles
                        start_angle = math.atan2(prev_y - center_y, prev_x - center_x)
                        end_angle = math.atan2(current_y - center_y, current_x - center_x)
                        
                        # Normalize angles
                        def normalize_angle(angle):
                            while angle < 0:
                                angle += 2 * math.pi
                            while angle >= 2 * math.pi:
                                angle -= 2 * math.pi
                            return angle
                        
                        start_angle = normalize_angle(start_angle)
                        end_angle = normalize_angle(end_angle)
                        
                        # Calculate arc sweep
                        if is_clockwise:
                            angle_diff = start_angle - end_angle
                            if angle_diff < 0:
                                angle_diff += 2 * math.pi
                        else:
                            angle_diff = end_angle - start_angle
                            if angle_diff < 0:
                                angle_diff += 2 * math.pi
                        
                        large_arc_flag = 1 if angle_diff > math.pi else 0
                        sweep_flag = 0 if is_clockwise else 1  # SVG sweep: 0=counterclockwise, 1=clockwise
                        
                        scaled_radius = radius * scale
                        path_data.append(
                            f"A {scaled_radius:.2f} {scaled_radius:.2f} 0 {large_arc_flag} {sweep_flag} "
                            f"{tx(current_x):.2f} {ty(current_y):.2f}"
                        )
        
        # Create SVG
        path_str = " ".join(path_data)
        # Use viewBox for automatic scaling and remove the black background rect 
        # so CSS can control it. Use a clear blue stroke for the paths.
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <path d="{path_str}" stroke="#60a5fa" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return (data_w, data_h)
