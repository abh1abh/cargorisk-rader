import os, requests
from celery import Celery
CELERY_BROKER = os.getenv("REDIS_URL","redis://redis:6379/0")
app = Celery("cargorisk", broker=CELERY_BROKER, backend=CELERY_BROKER)
API_BASE = os.getenv("API_BASE", "http://api:8000")

# Optional: keep embeddings deterministic & avoid thread thrash
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

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

@app.task(bind=True, name="ocr_asset", autoretry_for=(requests.RequestException,), retry_backoff=True, max_retries=5)
def ocr_asset(self, asset_id: int):
    req_id = (getattr(self.request, "headers", {}) or {}).get("request_id")
    headers = {"x-request-id": req_id} if req_id else None
    r = requests.post(f"{API_BASE}/documents/{asset_id}/ocr", timeout=120, headers=headers)
    r.raise_for_status()
    return r.json()


@app.task(bind=True, name="embed_asset", autoretry_for=(requests.RequestException,), retry_backoff=True, max_retries=5)
def embed_asset(self, asset_id: int):
    req_id = (getattr(self.request, "headers", {}) or {}).get("request_id")
    headers = {"x-request-id": req_id} if req_id else None
    r = requests.post(f"{API_BASE}/documents/{asset_id}/embed", timeout=120, headers=headers)
    r.raise_for_status()
    return r.json()