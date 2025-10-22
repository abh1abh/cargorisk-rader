from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class FreightItemIn(BaseModel):
    origin: str | None = None
    destination: str | None = None
    mode: str | None = "sea"
    carrier: str | None = None
    equipment: str | None = None
    qty: int | None = 1
    currency: str | None = None
    rate_per_unit: float | None = None
    total_freight: float | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    confidence: float = 0.0
    raw_cells: Any | None = None

class FreightItem(FreightItemIn):
    id: int

class ShipmentRequestCreate(BaseModel):
    source_asset_id: int
    items: list[FreightItemIn] = Field(default_factory=list)
    meta: Any | None = None

class ShipmentRequestOut(BaseModel):
    id: int
    source_asset_id: int | None = None
    status: str
    meta: Any | None = None
    items: list[FreightItem]
