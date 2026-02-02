"""
GNC Editor API Endpoints
Handles parsing and saving GNC files with P-code editing support.
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from .gnc_parser import GNCParser, GNCSheet
from .gnc_generator import GNCGenerator

router = APIRouter(prefix="/gnc", tags=["gnc"])

# Ensure GNC output directory
os.makedirs("static/gnc_output", exist_ok=True)

@router.post("/parse")
async def parse_gnc_file(file: UploadFile = File(...)):
    """
    Parse an uploaded GNC file and return the structured sheet data.
    """
    try:
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        parser = GNCParser()
        sheet = parser.parse(text_content, filename=file.filename)
        
        return sheet.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GNC file: {str(e)}")

@router.put("/save")
async def save_gnc_file(
    sheet: GNCSheet = Body(...),
    filename: str = Body(...),
    overwrite: bool = Body(default=True)
):
    """
    Save edited GNC sheet data back to a file.
    Regenerates the GNC file content from the sheet structure.
    """
    try:
        generator = GNCGenerator()
        content = generator.generate(sheet)
        
        # Save to output directory
        output_path = os.path.join("static/gnc_output", filename)
        
        if not overwrite and os.path.exists(output_path):
            raise HTTPException(status_code=409, detail="File already exists")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": output_path,
            "filename": filename,
            "size": len(content)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save GNC file: {str(e)}")
