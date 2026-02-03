"""
GNC Editor API Endpoints
Handles parsing and saving GNC files with P-code editing support.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .gnc_parser import GNCParser, GNCSheet
from .gnc_generator import GNCGenerator
import json

router = APIRouter()

# Ensure GNC output directory
os.makedirs("static/gnc_output", exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/parts/scan")
@router.post("/documents/scan")
async def scan_parts_library(db: Session = Depends(get_db)):
    """
    Scan configured network paths for GNC files and import them.
    Returns a streaming response with progress updates.
    """
    from .scanner import scan_library
    
    def generate_progress():
        try:
            for update in scan_library(db):
                yield json.dumps(update) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e), "percent": 0}) + "\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="application/x-ndjson"
    )

@router.post("/parts/parse-gnc")
async def parse_gnc_part(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Parse a GNC file and extract part information.
    """
    try:
        content_bytes = await file.read()
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = content_bytes.decode('latin-1')
        
        parser = GNCParser()
        sheet = parser.parse(content, filename=file.filename)
        return sheet
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GNC: {str(e)}")

@router.post("/gnc/parse")
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

@router.put("/gnc/save")
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
