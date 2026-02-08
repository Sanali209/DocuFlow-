from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import List, Optional
from src.application.services.inventory_service import InventoryService
from src.application.services.gnc_service import GncService
from src.domain.models import Material, Part, StockItem, Reservation, Consumption
from src.api.dependencies import get_inventory_service, get_gnc_service
import os

router = APIRouter(tags=["inventory"])

# Materials
@router.get("/materials/", response_model=List[Material])
def list_materials(service: InventoryService = Depends(get_inventory_service)):
    return service.list_materials()

@router.post("/materials/", response_model=Material)
def create_material(material: Material, service: InventoryService = Depends(get_inventory_service)):
    return service.create_material(material)

@router.put("/materials/{material_id}", response_model=Material)
def update_material(material_id: int, name: str = Query(...), service: InventoryService = Depends(get_inventory_service)):
    return service.update_material(material_id, name)

@router.delete("/materials/{material_id}")
def delete_material(material_id: int, service: InventoryService = Depends(get_inventory_service)):
    if service.delete_material(material_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Material not found")

# Parts
@router.get("/parts/", response_model=List[Part])
def list_parts(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    material_id: Optional[int] = None,
    min_width: Optional[float] = None,
    max_width: Optional[float] = None,
    min_height: Optional[float] = None,
    max_height: Optional[float] = None,
    service: InventoryService = Depends(get_inventory_service)
):
    filters = {
        "search": search,
        "material_id": material_id,
        "min_width": min_width,
        "max_width": max_width,
        "min_height": min_height,
        "max_height": max_height
    }
    return service.list_parts(skip, limit, filters)

@router.get("/parts/{part_id}", response_model=Part)
def get_part(part_id: int, service: InventoryService = Depends(get_inventory_service)):
    part = service.get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part

@router.post("/parts/", response_model=Part)
def create_part(part: Part, service: InventoryService = Depends(get_inventory_service)):
    return service.create_part(part)

@router.put("/parts/{part_id}", response_model=Part)
def update_part(part_id: int, data: dict, service: InventoryService = Depends(get_inventory_service)):
    # Simple dict update for now
    return service.update_part(part_id, data)

@router.delete("/parts/{part_id}")
def delete_part(part_id: int, service: InventoryService = Depends(get_inventory_service)):
    if service.delete_part(part_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Part not found")

@router.get("/parts/{part_id}/gnc")
def get_part_gnc(
    part_id: int, 
    inventory_service: InventoryService = Depends(get_inventory_service),
    gnc_service: GncService = Depends(get_gnc_service)
):
    part = inventory_service.get_part(part_id)
    if not part or not part.gnc_file_path:
        raise HTTPException(status_code=404, detail="GNC file path not found for this part")
    
    if not os.path.exists(part.gnc_file_path):
        raise HTTPException(status_code=404, detail=f"GNC file not found: {part.gnc_file_path}")
    
    try:
        with open(part.gnc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return gnc_service.parse_gnc(content, os.path.basename(part.gnc_file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing GNC file: {str(e)}")

# Stock
@router.get("/stock/", response_model=List[StockItem])
def list_stock(service: InventoryService = Depends(get_inventory_service)):
    return service.list_stock()

@router.post("/stock/", response_model=StockItem)
def create_stock_item(item: StockItem, service: InventoryService = Depends(get_inventory_service)):
    return service.create_stock_item(item)

@router.delete("/stock/{stock_id}")
def delete_stock_item(stock_id: int, service: InventoryService = Depends(get_inventory_service)):
    if service.delete_stock_item(stock_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Stock item not found")

# Reservations
@router.get("/reservations", response_model=List[Reservation])
def read_reservations(task_id: int | None = Query(None), service: InventoryService = Depends(get_inventory_service)):
    return service.list_reservations(task_id)

@router.post("/reservations", response_model=Reservation)
def create_reservation(reservation: Reservation, service: InventoryService = Depends(get_inventory_service)):
    return service.create_reservation(reservation)

@router.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: int, service: InventoryService = Depends(get_inventory_service)):
    if service.delete_reservation(reservation_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Reservation not found")

# Consumptions
@router.get("/consumptions", response_model=List[Consumption])
def read_consumptions(task_id: int | None = Query(None), service: InventoryService = Depends(get_inventory_service)):
    return service.list_consumptions(task_id)

@router.post("/consumptions", response_model=Consumption)
def create_consumption(consumption: Consumption, service: InventoryService = Depends(get_inventory_service)):
    return service.create_consumption(consumption)

@router.delete("/consumptions/{consumption_id}")
def delete_consumption(consumption_id: int, service: InventoryService = Depends(get_inventory_service)):
    if service.delete_consumption(consumption_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Consumption not found")

@router.post("/inventory/rescan")
def rescan_library(request: Request):
    sync_manager = getattr(request.app.state, 'sync_manager', None)
    if sync_manager:
        sync_manager.trigger_sync()
        return {"status": "started"}
    return {"status": "error", "message": "Sync manager not initialized"}
