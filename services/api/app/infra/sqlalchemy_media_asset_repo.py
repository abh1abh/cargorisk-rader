from sqlalchemy.orm import Session

from ..domain.exceptions import NotFound
from ..domain.ports import MediaAssetRepo
from ..models import MediaAsset
from sqlalchemy import update


class SqlAlchemyMediaAssetRepo(MediaAssetRepo):
    def get(self, db: Session, asset_id: int) -> MediaAsset:
        m = db.get(MediaAsset, asset_id)
        if not m:
            raise NotFound(f"MediaAsset with id {asset_id} not found")
        return m

    def save_text(self, db: Session, asset_id: int, text: str) -> None:
        asset = self.get(db, asset_id)
        asset.text = text

    def save_embedding(self, db: Session, asset_id: int, emb: list[float]) -> None:
        asset = self.get(db, asset_id)
        asset.embedding = emb

    def create(self, db: Session, asset: MediaAsset) -> None: 
        db.add(asset)

    