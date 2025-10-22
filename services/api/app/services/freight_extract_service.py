from dataclasses import dataclass
from ..schemas.freight import ShipmentRequestCreate

@dataclass(slots=True)
class FreightExtractService:

    
    def create_shipment(int: id) -> ShipmentRequestCreate:
        pass        
