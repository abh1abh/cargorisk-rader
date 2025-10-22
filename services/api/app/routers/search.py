from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import SearchServiceDependency, get_db
from ..core.logging import get_logger
from ..domain.exceptions import BadRequest, ProcessingError

log = get_logger("api.search")

router = APIRouter(prefix="/search", tags=["search"])

# EMBED_DIM = 384  # keep in sync with your model



@router.get("")
def search(
    search_service: SearchServiceDependency,
    q: str = Query(...),
    limit: int = 5,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    try:
        return search_service.search(db=db, query=q, limit=limit, offset=offset)
    except BadRequest as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ProcessingError as e:
        # Embedding/dimension mismatch etc. — treat as 500 to surface infra/config problems
        msg = str(e) if "Embedding dimension mismatch" not in str(e) else "Embedding dimension mismatch"
        raise HTTPException(status_code=500, detail=msg) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected server error.") from e