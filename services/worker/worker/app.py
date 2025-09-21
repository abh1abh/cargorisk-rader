import os, requests
from celery import Celery
CELERY_BROKER = os.getenv("REDIS_URL","redis://redis:6379/0")
app = Celery("cargorisk", broker=CELERY_BROKER, backend=CELERY_BROKER)

# NOTE: bind=True lets us access self.request.headers to read request-id
@app.task(bind=True, name="extract_metadata")
def extract_metadata(self, asset_id: int):
    # placeholder: later do OCR/embeddings

    # req_headers = getattr(self.request, "headers", {}) or {}
    # request_id = req_headers.get("request_id")

    import time, logging
    logging.getLogger().setLevel("INFO")
    time.sleep(2) # placeholder work
    return {"asset_id": asset_id, "status": "done"}

@app.task(bind=True, name="ocr_asset")
def ocr_asset(self, asset_id: int):
    base = os.getenv("API_BASE", "http://api:8000")
    req_id = (getattr(self.request, "headers", {}) or {}).get("request_id")
    headers = {"x-request-id": req_id} if req_id else None
    r = requests.post(f"{base}/documents/{asset_id}/ocr", timeout=120, headers=headers)
    r.raise_for_status()
    return r.json()
