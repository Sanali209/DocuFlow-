import builtins
from abc import ABC, abstractmethod

from src.domain.models import Consumption, Material, Part, Reservation, StockItem


class IMaterialRepository(ABC):
    @abstractmethod
    def list(self) -> list[Material]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Material | None:
        pass

    @abstractmethod
    def add(self, material: Material) -> Material:
        pass

    @abstractmethod
    def update(self, id: int, name: str) -> Material:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class IPartRepository(ABC):
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> list[Part]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Part | None:
        pass

    @abstractmethod
    def add(self, part: Part) -> Part:
        pass

    @abstractmethod
    def update(self, id: int, data: dict) -> Part:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class IStockRepository(ABC):
    @abstractmethod
    def list(self) -> list[StockItem]:
        pass

    @abstractmethod
    def add(self, item: StockItem) -> StockItem:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass

    @abstractmethod
    def list_reservations(self, task_id: int = None) -> builtins.list[Reservation]:
        pass

    @abstractmethod
    def add_reservation(self, reservation: Reservation) -> Reservation:
        pass

    @abstractmethod
    def delete_reservation(self, id: int) -> bool:
        pass

    @abstractmethod
    def list_consumptions(self, task_id: int = None) -> builtins.list[Consumption]:
        pass

    @abstractmethod
    def add_consumption(self, consumption: Consumption) -> Consumption:
        pass

    @abstractmethod
    def delete_consumption(self, id: int) -> bool:
        pass
