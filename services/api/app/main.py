from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from fastapi import FastAPI

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.s3_bucket}

print("Running")