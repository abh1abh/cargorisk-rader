from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain.ports import BlobStore, FreightRepo, MediaAssetRepo, OcrPort
from ..schemas.freight import ShipmentRequestOut


@dataclass(slots=True)
class FreightService:
    ocr: OcrPort
    s3: BlobStore
    freight_repo: FreightRepo
    media_asset_repo: MediaAssetRepo

    
    def extract_freight_from_asset(self, db: Session, asset_id: int) -> ShipmentRequestOut:
        asset = self.media_asset_repo.get(asset_id)

        text = asset.ocr_text or ""

        if not text:
            blob= self.s3.get_uri_bytes(asset.storage_uri)
            mime = asset.type or ""
            if mime.startswith("image/"):
                text = self.ocr.image_bytes_to_text(blob, lang="eng+nor")
            elif mime == "application/pdf":
                text = self.ocr.pdf_bytes_to_text(blob, lang="eng+nor")
            elif mime in {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel.sheet.macroEnabled.12",
            }:
                text = self.ocr.xlsx_bytes_to_text(blob)
            else:
                # fallback 
                try:
                    text = self.ocr.pdf_bytes_to_text(blob)
                except Exception:
                    text = self.ocr.image_bytes_to_text(blob)

            # Save OCR
            asset.ocr_text = text
            db.commit()
        
        sr_in = self._heuristic_extract(asset_id, text)
        return self.create_shipment(db, sr_in)
    

    def _heuristic_extract() -> ShipmentRequestOut:
        pass