from datetime import date

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_document_service
from src.application.services.document_service import DocumentService
from src.domain.models import Document, Tag

router = APIRouter(tags=["documents"])


@router.get("/tags", response_model=list[Tag])
def list_tags(service: DocumentService = Depends(get_document_service)):
    return service.list_tags()


@router.post("/", response_model=Document)
def create_document(document: Document, service: DocumentService = Depends(get_document_service)):
    return service.create_document(document)


@router.post("/create-order", response_model=Document)
def create_order(
    name: str = Body(..., embed=True),
    items: list[dict] = Body(...),
    service: DocumentService = Depends(get_document_service),
):
    return service.create_order(name, items)


@router.get("/", response_model=list[Document])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    type: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    assignee: str | None = None,
    material_id: int | None = Query(
        None, alias="material"
    ),  # Mapping "material" query param to material_id
    part_search: str | None = None,
    sort_by: str = "registration_date",
    sort_order: str = "desc",
    start_date: date | None = None,
    end_date: date | None = None,
    date_field: str = "registration_date",
    service: DocumentService = Depends(get_document_service),
):
    return service.list_documents(
        skip=skip,
        limit=limit,
        search=search,
        type=type,
        status=status,
        tag=tag,
        assignee=assignee,
        material_id=material_id,
        part_search=part_search,
        sort_by=sort_by,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
    )


@router.get("/{document_id}", response_model=Document)
def read_document(document_id: int, service: DocumentService = Depends(get_document_service)):
    db_document = service.get_document(document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document


@router.put("/{document_id}", response_model=Document)
def update_document(
    document_id: int, document: Document, service: DocumentService = Depends(get_document_service)
):
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
async def save_as_new_order(
    data: dict = Body(...), service: DocumentService = Depends(get_document_service)
):
    print(
        f"Received save_as_new_order request: Name={data.get('name')}, Sheets={len(data.get('sheets', []))}"
    )
    try:
        return service.save_as_new_order(data)
    except Exception as e:
        print(f"Error in save_as_new_order endpoint: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/stats")
def get_dashboard_stats(service: DocumentService = Depends(get_document_service)):
    return service.get_dashboard_stats()


@router.get("/{document_id}/zip")
def download_document_zip(
    document_id: int, service: DocumentService = Depends(get_document_service)
):
    zip_buffer = service.get_document_zip(document_id)
    if not zip_buffer:
        raise HTTPException(status_code=404, detail="Zip not found or document has no attachments")

    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename=document_{document_id}.zip"},
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
    file_path = os.path.join(upload_dir, file.name if hasattr(file, "name") else file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "file_path": file_path, "media_type": file.content_type}


@router.post("/{document_id}/open-folder")
def open_document_folder(
    document_id: int, service: DocumentService = Depends(get_document_service)
):
    import os
    import subprocess
    import sys

    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Logic to find the folder.
    # For orders, it's likely distinct. For others, it might be the Attachments folder.
    # We'll try to find a common directory from attachments or tasks.
    folder_path = None

    # 1. Check for Order-specific path (convention: static/orders/{uid})
    # We might need to store this path in the document or deduce it.
    # If the document has attachments, use the folder of the first attachment.
    if doc.attachments and len(doc.attachments) > 0:
        folder_path = os.path.dirname(doc.attachments[0].file_path)
    elif doc.tasks and len(doc.tasks) > 0:
        for t in doc.tasks:
            if t.gnc_file_path:
                folder_path = os.path.dirname(t.gnc_file_path)
                break

    if not folder_path or not os.path.exists(folder_path):
        raise HTTPException(
            status_code=404, detail="Could not determine a valid folder for this document"
        )

    try:
        if sys.platform == "win32":
            os.startfile(folder_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {e!s}")
