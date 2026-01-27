from fastapi import FastAPI, UploadFile, File, HTTPException
from docling.document_converter import DocumentConverter
import shutil
import os
import tempfile
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class RecognitionResult(BaseModel):
    markdown: str

@app.post("/process", response_model=RecognitionResult)
async def process_document(file: UploadFile = File(...)):
    logger.info(f"Processing file: {file.filename}")

    # Create a temporary file to save the uploaded image
    suffix = os.path.splitext(file.filename)[1]
    if not suffix:
        suffix = ".tmp"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Initialize converter
        # Note: In a production env, you might want to instantiate this once globally
        # if it loads heavy models, but for now we'll do it here or globally.
        # Let's do it globally to avoid reloading models on every request if possible,
        # but docling might handle lazy loading.
        logger.info("Initializing DocumentConverter...")
        converter = DocumentConverter()

        logger.info(f"Converting file at {tmp_path}...")
        result = converter.convert(tmp_path)

        logger.info("Exporting to markdown...")
        markdown = result.document.export_to_markdown()

        return RecognitionResult(markdown=markdown)
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "docling-ocr"}
