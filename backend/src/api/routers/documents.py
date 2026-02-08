from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from typing import List
from datetime import date
from src.application.services.document_service import DocumentService
from src.domain.models import Document, Tag
from src.api.dependencies import get_document_service

router = APIRouter(tags=["documents"])

@router.get("/tags", response_model=List[Tag])
def list_tags(service: DocumentService = Depends(get_document_service)):
    return service.list_tags()

@router.post("/", response_model=Document)
def create_document(document: Document, service: DocumentService = Depends(get_document_service)):
    return service.create_document(document)

@router.post("/create-order", response_model=Document)
def create_order(name: str = Body(..., embed=True), items: List[dict] = Body(...), service: DocumentService = Depends(get_document_service)):
    return service.create_order(name, items)

@router.get("/", response_model=List[Document])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    service: DocumentService = Depends(get_document_service)
):
    return service.list_documents(skip=skip, limit=limit)

@router.get("/{document_id}", response_model=Document)
def read_document(document_id: int, service: DocumentService = Depends(get_document_service)):
    db_document = service.get_document(document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.put("/{document_id}", response_model=Document)
def update_document(document_id: int, document: Document, service: DocumentService = Depends(get_document_service)):
    # Ensure ID matches
    document.id = document_id
    db_document = service.update_document(document)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.delete("/{document_id}")
def delete_document(document_id: int, service: DocumentService = Depends(get_document_service)):
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}

@router.post("/save-as-new-order")
async def save_as_new_order(data: dict = Body(...), service: DocumentService = Depends(get_document_service)):
    return service.save_as_new_order(data)

@router.get("/dashboard/stats")
def get_dashboard_stats(service: DocumentService = Depends(get_document_service)):
    return service.get_dashboard_stats()

@router.get("/{document_id}/zip")
def download_document_zip(document_id: int, service: DocumentService = Depends(get_document_service)):
    zip_buffer = service.get_document_zip(document_id)
    if not zip_buffer:
        raise HTTPException(status_code=404, detail="Zip not found or document has no attachments")
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename=document_{document_id}.zip"}
    )

@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, service: DocumentService = Depends(get_document_service)):
    if service.delete_attachment(attachment_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Attachment not found")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    import os
    import shutil
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.name if hasattr(file, 'name') else file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "filename": file.filename,
        "file_path": file_path,
        "media_type": file.content_type
    }
