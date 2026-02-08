from typing import List, Optional
from src.domain.models import Material, Part, StockItem, Reservation, Consumption
from abc import ABC, abstractmethod

class IMaterialRepository(ABC):
    @abstractmethod
    def list(self) -> List[Material]: pass
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Material]: pass
    @abstractmethod
    def add(self, material: Material) -> Material: pass
    @abstractmethod
    def update(self, id: int, name: str) -> Material: pass
    @abstractmethod
    def delete(self, id: int) -> bool: pass

class IPartRepository(ABC):
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Part]: pass
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Part]: pass
    @abstractmethod
    def add(self, part: Part) -> Part: pass
    @abstractmethod
    def update(self, id: int, data: dict) -> Part: pass
    @abstractmethod
    def delete(self, id: int) -> bool: pass

class IStockRepository(ABC):
    @abstractmethod
    def list(self) -> List[StockItem]: pass
    @abstractmethod
    def add(self, item: StockItem) -> StockItem: pass
    @abstractmethod
    def delete(self, id: int) -> bool: pass
    
    @abstractmethod
    def list_reservations(self, task_id: int = None) -> List[Reservation]: pass
    @abstractmethod
    def add_reservation(self, reservation: Reservation) -> Reservation: pass
    @abstractmethod
    def delete_reservation(self, id: int) -> bool: pass
    
    @abstractmethod
    def list_consumptions(self, task_id: int = None) -> List[Consumption]: pass
    @abstractmethod
    def add_consumption(self, consumption: Consumption) -> Consumption: pass
    @abstractmethod
    def delete_consumption(self, id: int) -> bool: pass
