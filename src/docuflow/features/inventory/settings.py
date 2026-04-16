from pydantic import Field

from docuflow.domain.settings import BaseModuleSettings


class InventorySettings(BaseModuleSettings):
    """Configuration for material management and stock alerts."""

    low_stock_threshold: int = Field(
        default=10,
        description="Threshold for low stock warnings (sheets/units)",
        json_schema_extra={"scope": "global"},
    )
