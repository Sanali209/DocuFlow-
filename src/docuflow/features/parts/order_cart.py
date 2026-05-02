from dataclasses import dataclass


@dataclass
class CartItem:
    sku: str
    name: str | None = None
    qty: int = 1


class OrderCart:
    """Session-based order cart for parts."""

    def __init__(self) -> None:
        self.items: dict[str, CartItem] = {}

    def add(self, sku: str, name: str | None = None, qty: int = 1) -> None:
        if sku in self.items:
            self.items[sku].qty += qty
        else:
            self.items[sku] = CartItem(sku=sku, name=name, qty=qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def update_qty(self, sku: str, qty: int) -> None:
        if sku in self.items:
            if qty <= 0:
                self.remove(sku)
            else:
                self.items[sku].qty = qty

    def clear(self) -> None:
        self.items.clear()

    def get_items(self) -> list[CartItem]:
        return list(self.items.values())

    def is_empty(self) -> bool:
        return len(self.items) == 0
