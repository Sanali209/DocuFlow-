from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
from src.application.services.gnc_service import GncService
from src.application.services.inventory_service import InventoryService
from src.infrastructure.parsers.gnc_parser import GNCSheet
from src.application.services.production_service import ProductionService
from src.api.dependencies import get_gnc_service, get_db, get_inventory_service, get_production_service
from src.domain.models import Part, Task

router = APIRouter(tags=["gnc"])

@router.post("/parse")
async def parse_gnc_file(file: UploadFile = File(...), service: GncService = Depends(get_gnc_service)):
    try:
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        sheet = service.parse_gnc(text_content, file.filename)
        return sheet.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GNC file: {str(e)}")

@router.put("/save")
async def save_gnc_file(
    sheet: GNCSheet = Body(...),
    filename: str = Body(...),
    overwrite: bool = Body(default=True),
    service: GncService = Depends(get_gnc_service)
):
    try:
        return service.save_gnc(sheet, filename, overwrite)
    except FileExistsError:
        raise HTTPException(status_code=409, detail="File already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save GNC file: {str(e)}")

# Scan parts remains here as a gnc/production system feature
@router.post("/scan")
async def scan_parts(request: Request):
    sync_manager = getattr(request.app.state, 'sync_manager', None)
    if sync_manager:
        sync_manager.trigger_sync()
        return {"status": "started"}
    return {"status": "error", "message": "Sync manager not initialized"}

@router.get("/library-parts", response_model=List[Part])
async def list_library_parts(inventory_service: InventoryService = Depends(get_inventory_service)):
    return inventory_service.list_parts(limit=1000)

@router.get("/orders/{order_id}/tasks", response_model=List[Task])
async def get_order_tasks(order_id: int, service: ProductionService = Depends(get_production_service)):
    return service.get_order_tasks(order_id)

@router.post("/save-order-nesting")
async def save_order_nesting(data: dict = Body(...), service: ProductionService = Depends(get_production_service)):
    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id required")
    if service.save_nesting(order_id, data):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Order not found")

@router.get("/orders/{order_id}/project")
async def get_order_nesting_project(order_id: int, service: ProductionService = Depends(get_production_service)):
    project = service.get_nesting_project(order_id)
    if project:
        return project
    raise HTTPException(status_code=404, detail="Project not found")
