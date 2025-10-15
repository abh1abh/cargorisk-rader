
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core.deps import UploadServiceDependency, get_db

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", summary="Upload a file to MinIO and register media asset")
async def upload(
    upload_service: UploadServiceDependency,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    try:
        # service returns a dict: {"id", "sha256", "uri"}
        return await upload_service.upload(db=db, file=file)
    except ValueError as e:
        msg = str(e)
        if "Empty file" in msg:        
            raise HTTPException(status_code=400, detail=str(e)) from e
        if "too large" in msg:
            raise HTTPException(status_code=413, detail=str(e)) from e
        if "Unsupported" in msg:
            raise HTTPException(status_code=415, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Unexpected value error occurred.") from e

