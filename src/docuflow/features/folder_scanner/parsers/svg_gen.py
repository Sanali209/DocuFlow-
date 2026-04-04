import logging
from pathlib import Path
from typing import Optional, Tuple

from docuflow.infrastructure.graphics.svg_generator import SVGGenerator
from docuflow.features.folder_scanner.parsers.gnc import GncPartData

logger = logging.getLogger(__name__)

class PartPreviewGenerator:
    """
    Wrapper around SVGGenerator for higher-level use in FolderScannerSystem.
    Handles file paths and graceful fallbacks.
    """
    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: Absolute path where SVG files will be stored.
        """
        self.output_dir = output_dir
        self.svg_gen = SVGGenerator()
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, part_data: GncPartData, sku: str
                 ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Generates an SVG preview for a part and returns its dimensions and path.
        
        Returns:
            Tuple of (bbox_x_mm, bbox_y_mm, svg_relative_path)
            If generation fails, returns (None, None, None).
        """
        try:
            # Sanitize SKU for filename
            safe_sku = sku.replace("/", "_").replace("\\", "_").replace(":", "_")
            output_file = self.output_dir / f"{safe_sku}.svg"
            
            data_w, data_h = self.svg_gen.generate_thumbnail(
                part=part_data,
                output_path=str(output_file)
            )
            
            if data_w == 0 and data_h == 0:
                logger.warning(f"Generated SVG for {sku} has zero dimensions.")
                return None, None, None
                
            # We return only the filename (or relative path) for DB storage
            return data_w, data_h, output_file.name
            
        except Exception as e:
            logger.error(f"Failed to generate SVG for SKU {sku}: {e}", exc_info=True)
            return None, None, None
