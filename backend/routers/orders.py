from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from .. import schemas, models
from ..dependencies import get_db
from ..services.orders import OrderService

router = APIRouter(tags=["documents"])


@router.post("/documents/order", response_model=schemas.Document)
def create_order_endpoint(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        return OrderService.create_order(db, order_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class OrderFromGNC(BaseModel):
    name: str
    sheets: List[Dict[str, Any]]
    original_document_id: int | None = None

@router.post("/documents/save-as-new-order", response_model=schemas.Document)
def save_as_new_order(
    item: OrderFromGNC,
    db: Session = Depends(get_db)
):
    try:
        return OrderService.save_multi_sheet_order(db, item.sheets, item.name, item.original_document_id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
