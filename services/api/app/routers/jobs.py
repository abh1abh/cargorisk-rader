from fastapi import APIRouter, Request
from celery import Celery
import os

router = APIRouter(prefix="/jobs", tags=["jobs"])
celery = Celery(broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

@router.post("/extract/{asset_id}")
def trigger_extract(asset_id: int, request: Request):
    req_id = request.headers.get("x-request-id")
    task = celery.send_task(
        "extract_metadata",
        args=[asset_id],
        headers={"request_id": req_id} if req_id else None,
    )
    return {"task_id": task.id}


@router.get("/{task_id}")
def job_status(task_id: str):
    res = celery.AsyncResult(task_id)
    return {"task_id": task_id, "state": res.state, "result": res.result if res.ready() else None}
