from sqlalchemy.orm import Session
from typing import List, Optional
from src.domain.models import Material, Part, StockItem, Reservation, Consumption
from src.domain.material_interface import IMaterialRepository, IPartRepository, IStockRepository
from .models import MaterialDB, PartDB, StockItemDB, ReservationDB, ConsumptionDB

class SQLMaterialRepository(IMaterialRepository):
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> List[Material]:
        return [Material(id=m.id, name=m.name) for m in self.db.query(MaterialDB).all()]

    def get_by_id(self, id: int) -> Optional[Material]:
        m = self.db.query(MaterialDB).filter(MaterialDB.id == id).first()
        return Material(id=m.id, name=m.name) if m else None

    def add(self, material: Material) -> Material:
        db_m = MaterialDB(name=material.name)
        self.db.add(db_m)
        self.db.commit()
        self.db.refresh(db_m)
        return Material(id=db_m.id, name=db_m.name)

    def update(self, id: int, name: str) -> Material:
        db_m = self.db.query(MaterialDB).filter(MaterialDB.id == id).first()
        if not db_m: raise ValueError("Material not found")
        db_m.name = name
        self.db.commit()
        return Material(id=db_m.id, name=db_m.name)

    def delete(self, id: int) -> bool:
        db_m = self.db.query(MaterialDB).filter(MaterialDB.id == id).first()
        if db_m:
            self.db.delete(db_m)
            self.db.commit()
            return True
        return False

class SQLPartRepository(IPartRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_p: PartDB) -> Part:
        return Part(
            id=db_p.id,
            name=db_p.name,
            registration_number=db_p.registration_number,
            version=db_p.version,
            material_id=db_p.material_id,
            gnc_file_path=db_p.gnc_file_path,
            width=db_p.width or 0.0,
            height=db_p.height or 0.0,
            stats=db_p.stats
        )

    def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Part]:
        query = self.db.query(PartDB)
        if filters:
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(PartDB.name.ilike(search) | PartDB.registration_number.ilike(search))
            if filters.get("material_id"):
                query = query.filter(PartDB.material_id == filters["material_id"])
            if filters.get("min_width"):
                query = query.filter(PartDB.width >= float(filters["min_width"]))
            if filters.get("max_width"):
                query = query.filter(PartDB.width <= float(filters["max_width"]))
            if filters.get("min_height"):
                query = query.filter(PartDB.height >= float(filters["min_height"]))
            if filters.get("max_height"):
                query = query.filter(PartDB.height <= float(filters["max_height"]))
        
        db_parts = query.offset(skip).limit(limit).all()
        return [self._to_domain(p) for p in db_parts]

    def get_by_id(self, id: int) -> Optional[Part]:
        db_p = self.db.query(PartDB).filter(PartDB.id == id).first()
        return self._to_domain(db_p) if db_p else None

    def add(self, part: Part) -> Part:
        db_p = PartDB(
            name=part.name,
            registration_number=part.registration_number,
            version=part.version,
            material_id=part.material_id,
            gnc_file_path=part.gnc_file_path,
            width=part.width,
            height=part.height,
            stats=part.stats
        )
        self.db.add(db_p)
        self.db.commit()
        self.db.refresh(db_p)
        return self._to_domain(db_p)

    def update(self, id: int, data: dict) -> Part:
        db_p = self.db.query(PartDB).filter(PartDB.id == id).first()
        if not db_p: raise ValueError("Part not found")
        for key, value in data.items():
            if hasattr(db_p, key):
                setattr(db_p, key, value)
        self.db.commit()
        self.db.refresh(db_p)
        return self._to_domain(db_p)

    def delete(self, id: int) -> bool:
        db_p = self.db.query(PartDB).filter(PartDB.id == id).first()
        if db_p:
            self.db.delete(db_p)
            self.db.commit()
            return True
        return False

class SQLStockRepository(IStockRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, db_s: StockItemDB) -> StockItem:
        return StockItem(
            id=db_s.id,
            material_id=db_s.material_id,
            width=db_s.width or 0.0,
            height=db_s.height or 0.0,
            quantity=db_s.quantity,
            reserved=db_s.reserved,
            location=db_s.location
        )

    def list(self) -> List[StockItem]:
        return [self._to_domain(s) for s in self.db.query(StockItemDB).all()]

    def add(self, item: StockItem) -> StockItem:
        db_s = StockItemDB(
            material_id=item.material_id,
            width=item.width,
            height=item.height,
            quantity=item.quantity,
            reserved=item.reserved,
            location=item.location
        )
        self.db.add(db_s)
        self.db.commit()
        self.db.refresh(db_s)
        return self._to_domain(db_s)

    def delete(self, id: int) -> bool:
        db_s = self.db.query(StockItemDB).filter(StockItemDB.id == id).first()
        if db_s:
            self.db.delete(db_s)
            self.db.commit()
            return True
        return False

    def list_reservations(self, task_id: int = None) -> List[Reservation]:
        query = self.db.query(ReservationDB)
        if task_id:
            query = query.filter(ReservationDB.task_id == task_id)
        return [Reservation(
            id=r.id,
            task_id=r.task_id,
            stock_item_id=r.stock_item_id,
            quantity_reserved=r.quantity_reserved,
            created_at=r.created_at
        ) for r in query.all()]

    def add_reservation(self, reservation: Reservation) -> Reservation:
        db_r = ReservationDB(
            task_id=reservation.task_id,
            stock_item_id=reservation.stock_item_id,
            quantity_reserved=reservation.quantity_reserved
        )
        self.db.add(db_r)
        
        # Update stock reserved count
        stock = self.db.query(StockItemDB).filter(StockItemDB.id == reservation.stock_item_id).first()
        if stock:
            stock.reserved += reservation.quantity_reserved
            
        self.db.commit()
        self.db.refresh(db_r)
        return Reservation(
            id=db_r.id,
            task_id=db_r.task_id,
            stock_item_id=db_r.stock_item_id,
            quantity_reserved=db_r.quantity_reserved,
            created_at=db_r.created_at
        )

    def delete_reservation(self, id: int) -> bool:
        db_r = self.db.query(ReservationDB).filter(ReservationDB.id == id).first()
        if db_r:
            # Revert stock reserved count
            stock = self.db.query(StockItemDB).filter(StockItemDB.id == db_r.stock_item_id).first()
            if stock:
                stock.reserved -= db_r.quantity_reserved
            
            self.db.delete(db_r)
            self.db.commit()
            return True
        return False

    def list_consumptions(self, task_id: int = None) -> List[Consumption]:
        query = self.db.query(ConsumptionDB)
        if task_id:
            query = query.filter(ConsumptionDB.task_id == task_id)
        return [Consumption(
            id=c.id,
            task_id=c.task_id,
            stock_item_id=c.stock_item_id,
            quantity_used=c.quantity_used,
            remnants_created=c.remnants_created,
            created_at=c.created_at
        ) for c in query.all()]

    def add_consumption(self, consumption: Consumption) -> Consumption:
        db_c = ConsumptionDB(
            task_id=consumption.task_id,
            stock_item_id=consumption.stock_item_id,
            quantity_used=consumption.quantity_used,
            remnants_created=consumption.remnants_created
        )
        self.db.add(db_c)
        
        # Update stock actual count
        stock = self.db.query(StockItemDB).filter(StockItemDB.id == consumption.stock_item_id).first()
        if stock:
            stock.quantity -= consumption.quantity_used
            # If there was a reservation, we should ideally reduce it too, 
            # but legacy crud.py logic might vary. 
            # Assuming consumption consumes the reservation if it exists.
            # For simplicity, we just reduce quantity here.
            
        self.db.commit()
        self.db.refresh(db_c)
        return Consumption(
            id=db_c.id,
            task_id=db_c.task_id,
            stock_item_id=db_c.stock_item_id,
            quantity_used=db_c.quantity_used,
            remnants_created=db_c.remnants_created,
            created_at=db_c.created_at
        )

    def delete_consumption(self, id: int) -> bool:
        db_c = self.db.query(ConsumptionDB).filter(ConsumptionDB.id == id).first()
        if db_c:
            # Revert stock actual count
            stock = self.db.query(StockItemDB).filter(StockItemDB.id == db_c.stock_item_id).first()
            if stock:
                stock.quantity += db_c.quantity_used
            
            self.db.delete(db_c)
            self.db.commit()
            return True
        return False
