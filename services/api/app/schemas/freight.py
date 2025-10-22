from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Any

class FreightItemIn(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    mode: Optional[str] = "sea"
    carrier: Optional[str] = None
    equipment: Optional[str] = None
    qty: Optional[int] = 1
    currency: Optional[str] = None
    rate_per_unit: Optional[float] = None
    total_freight: Optional[float] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    confidence: float = 0.0
    raw_cells: Optional[Any] = None

class FreightItem(FreightItemIn):
    id: int

class ShipmentRequestCreate(BaseModel):
    source_asset_id: int
    items: List[FreightItemIn] = Field(default_factory=list)
    meta: Optional[Any] = None

class ShipmentRequestOut(BaseModel):
    id: int
    source_asset_id: int | None = None
    status: str
    meta: Optional[Any] = None
    items: List[FreightItem]
