from typing import List, Optional
from src.domain.models import Material, Part, StockItem, Reservation, Consumption
from src.domain.material_interface import IMaterialRepository, IPartRepository, IStockRepository

class InventoryService:
    def __init__(self, mat_repo: IMaterialRepository, part_repo: IPartRepository, stock_repo: IStockRepository):
        self.mat_repo = mat_repo
        self.part_repo = part_repo
        self.stock_repo = stock_repo

    # Materials
    def list_materials(self) -> List[Material]:
        return self.mat_repo.list()

    def create_material(self, material: Material) -> Material:
        return self.mat_repo.add(material)

    def update_material(self, id: int, name: str) -> Material:
        return self.mat_repo.update(id, name)

    def delete_material(self, id: int) -> bool:
        return self.mat_repo.delete(id)

    # Parts
    def list_parts(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Part]:
        return self.part_repo.list(skip, limit, filters)

    def get_part(self, id: int) -> Optional[Part]:
        return self.part_repo.get_by_id(id)

    def create_part(self, part: Part) -> Part:
        return self.part_repo.add(part)

    def update_part(self, id: int, data: dict) -> Part:
        return self.part_repo.update(id, data)

    def delete_part(self, id: int) -> bool:
        return self.part_repo.delete(id)

    # Stock
    def list_stock(self) -> List[StockItem]:
        return self.stock_repo.list()

    def create_stock_item(self, item: StockItem) -> StockItem:
        return self.stock_repo.add(item)

    def delete_stock_item(self, id: int) -> bool:
        return self.stock_repo.delete(id)

    # Reservations
    def list_reservations(self, task_id: int = None) -> List[Reservation]:
        return self.stock_repo.list_reservations(task_id)

    def create_reservation(self, reservation: Reservation) -> Reservation:
        return self.stock_repo.add_reservation(reservation)

    def delete_reservation(self, id: int) -> bool:
        return self.stock_repo.delete_reservation(id)

    # Consumptions
    def list_consumptions(self, task_id: int = None) -> List[Consumption]:
        return self.stock_repo.list_consumptions(task_id)

    def create_consumption(self, consumption: Consumption) -> Consumption:
        return self.stock_repo.add_consumption(consumption)

    def delete_consumption(self, id: int) -> bool:
        return self.stock_repo.delete_consumption(id)
