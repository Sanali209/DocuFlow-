from typing import Optional
from src.infrastructure.parsers.gnc_parser import GNCParser, GNCSheet
from src.infrastructure.graphics.gnc_generator import GNCGenerator
import os

class GncService:
    def __init__(self, output_dir: str = "static/gnc_output"):
        self.parser = GNCParser()
        self.generator = GNCGenerator()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_gnc(self, content: str, filename: str) -> GNCSheet:
        return self.parser.parse(content, filename=filename)

    def save_gnc(self, sheet: GNCSheet, filename: str, overwrite: bool = True) -> dict:
        content = self.generator.generate(sheet)
        output_path = os.path.join(self.output_dir, filename)
        
        if not overwrite and os.path.exists(output_path):
            raise FileExistsError("File already exists")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": output_path,
            "filename": filename,
            "size": len(content)
        }
