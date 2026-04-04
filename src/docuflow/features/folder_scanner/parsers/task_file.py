import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskFileMeta:
    """Metadata extracted from a GNC task filename."""
    gnc_name: str
    step_index: Optional[int] = None
    batch_index: Optional[int] = None

class TaskFileParser:
    """
    Parses filenames within a task folder to categorize and index them.
    Standard pattern: {step_idx:02d}-{batch_idx:02d}-SIDRA-...
    """
    
    # Pattern to match step and batch indices at the beginning of the filename
    TASK_FILE_REGEX = re.compile(
        r'^(?P<step>\d+)-(?P<batch>\d+)-(?P<rest>.+)\.GNC$',
        re.IGNORECASE
    )

    def is_variant(self, file_path: Path) -> bool:
        """
        Returns True if the file is a variant/metadata file and should NOT 
        be imported as a primary TaskItem.
        """
        name = file_path.name.upper()
        suffix = file_path.suffix.upper()
        
        # 1. Non-GNC files are variants or metadata
        if suffix != ".GNC":
            return True
        
        # 2. Files with _AUT in name (usually metadata)
        if "_AUT" in name:
            return True
            
        # 3. .Dsp projects (handled by suffix=True already, but good to be explicit)
        if ".DSP" in name:
            return True
            
        # 4. Filter out other potential variant suffixes in the future
        # (e.g. -offset1.GNC, -cut1.GNC if they appear)
        
        return False

    def parse_task_filename(self, name: str) -> TaskFileMeta:
        """
        Parses the GNC filename to extract step and batch indices.
        Example: "01-02-SIDRA-353203-..." -> step=1, batch=2
        """
        match = self.TASK_FILE_REGEX.match(name)
        if match:
            return TaskFileMeta(
                gnc_name=name,
                step_index=int(match.group("step")),
                batch_index=int(match.group("batch"))
            )
            
        return TaskFileMeta(gnc_name=name, step_index=None, batch_index=None)
