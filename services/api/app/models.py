from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, JSON as JSON_, Column, DateTime, Integer, String, ForeignKey, Numeric, Date, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


from .core.db import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)  # "pdf" | "image"
    storage_uri = Column(String, nullable=False)
    sha256 = Column(String, nullable=False, unique=True)
    ocr_text = Column(String)
    embedding = Column(Vector(384))  # open up vector search later
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ShipmentRequest(Base):
    __tablename__ = "shipment_requests"
    id = Column(Integer, primary_key=True)
    # legacy column (keep readable, prefer "meta" going forward)
    metadata_json = Column("metadata", JSON, nullable=True)

    # new freight-only plumbing
    source_asset_id = Column(Integer, nullable=True)
    status = Column(String, default="draft")
    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("FreightItem", back_populates="shipment_request", cascade="all, delete-orphan")

class FreightItem(Base):
    __tablename__ = "freight_items"
    id = Column(Integer, primary_key=True)
    shipment_request_id = Column(Integer, ForeignKey("shipment_requests.id", ondelete="CASCADE"))
    origin = Column(String)
    destination = Column(String)
    mode = Column(String)
    carrier = Column(String)
    equipment = Column(String)
    qty = Column(Integer)
    currency = Column(String)
    rate_per_unit = Column(Numeric(12,4))
    total_freight = Column(Numeric(12,2))
    valid_from = Column(Date)
    valid_to = Column(Date)
    confidence = Column(Float)
    raw_cells = Column(JSON_)

    shipment_request = relationship("ShipmentRequest", back_populates="items")
