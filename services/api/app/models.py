from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

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
    metadata_json = Column("metadata", JSON, nullable=True)  # python attr != reserved name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
