from dataclasses import dataclass

from ..domain.ports import BlobStore, FreightRepo, OcrPort
from ..schemas.freight import ShipmentRequestCreate


@dataclass(slots=True)
class FreightService:
    ocr: OcrPort
    s3: BlobStore
    repo: FreightRepo

    
    def extract_freight_from_asset(int: id) -> ShipmentRequestCreate:
        pass        
