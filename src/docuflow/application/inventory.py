from sqlmodel import Session, select

from docuflow.application.bus.orchestrator import P2POrchestrator
from docuflow.domain.entities.production import MaterialStock
from docuflow.infrastructure.security import HMACSigner


class InventorySystem:
    """Manages the distributed material inventory and P2P stock synchronization.

    This system ensures that changes to physical stock levels are cryptographically
    signed and broadcasted to all nodes in the cluster.
    """

    def __init__(self, session: Session, orchestrator: P2POrchestrator, signer: HMACSigner):
        self._session = session
        self._orchestrator = orchestrator
        self._signer = signer

    def get_all_materials(self) -> list[MaterialStock]:
        """Listing all available material stocks from the local synchronized database."""
        statement = select(MaterialStock)
        return list(self._session.exec(statement).all())

    def update_stock(self, material_id: int, absolute_quantity: float) -> MaterialStock:
        """Adjusting the absolute quantity of a specific material and broadcasting the update.

        This implementation follows the 'absolute-value' sync model to ensure
        cluster-wide consistency in a P2P environment.
        """
        material = self._session.get(MaterialStock, material_id)
        if not material:
            raise ValueError(f"Material with ID {material_id} not found.")

        # 1. Update the local baseline (Source of Truth for this node)
        material.quantity = absolute_quantity
        self._session.add(material)
        self._session.commit()
        self._session.refresh(material)

        # 2. Prepare the P2P broadcast command
        payload = {
            "type": "UPDATE_STOCK",
            "material_id": material.id,
            "quantity": material.quantity,
            "unit": material.unit,
        }

        # 3. Broadcast across the cluster via the HMAC-signed bus
        # Note: In a real system, the Orchestrator would encapsulate the
        # specific command formatting and signature.
        self._orchestrator.broadcast_command(command="UPDATE_STOCK", data=payload)

        return material

    def create_material(self, name: str, quantity: float, unit: str = "pcs") -> MaterialStock:
        """Adding a new material type to the cluster's unified stock registry."""
        new_material = MaterialStock(name=name, quantity=quantity, unit=unit)
        self._session.add(new_material)
        self._session.commit()
        self._session.refresh(new_material)

        # Broadcast the new entity to the cluster
        self._orchestrator.broadcast_command(
            command="CREATE_MATERIAL", data={"name": name, "quantity": quantity, "unit": unit}
        )

        return new_material
