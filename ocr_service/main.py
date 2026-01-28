from fastapi import FastAPI, UploadFile, File, HTTPException
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
import shutil
import os
import tempfile
from pydantic import BaseModel
import logging
import preprocessing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global converter instance to reuse models
_converter_instance = None

def get_converter():
    global _converter_instance
    if _converter_instance is None:
        logger.info("Initializing DocumentConverter with TableFormer and EasyOCR...")
        # Configure pipeline options for enhanced table structure and OCR
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True  # Enable TableFormer
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = EasyOcrOptions() # Use EasyOCR for robust recognition on images

        # Initialize converter with explicit formats and options
        # Note: PdfPipelineOptions is passed via PdfFormatOption for both PDF and Image pipeline config in newer Docling versions
        _converter_instance = DocumentConverter(
            allowed_formats=[InputFormat.IMAGE, InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                InputFormat.IMAGE: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    return _converter_instance

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
        converter = get_converter()

        logger.info(f"Converting file at {tmp_path}...")
        
        # Determine if it's an image
        # Simple check by extension or could check mime
        ext = os.path.splitext(tmp_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            logger.info("Image detected, applying preprocessing...")
            processed_path = preprocessing.preprocess_image(tmp_path)
            # conversion input is now the processed file
            conversion_input = processed_path
        else:
            conversion_input = tmp_path
            
        result = converter.convert(conversion_input)
        
        # Cleanup processed file if different
        if conversion_input != tmp_path and os.path.exists(conversion_input):
            try:
                os.remove(conversion_input)
            except OSError:
                pass

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
