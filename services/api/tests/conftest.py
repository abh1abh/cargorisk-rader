import io
import os
import shutil
import time

import httpx
import pytest
from PIL import Image, ImageDraw

BASE = os.getenv("BASE", "http://localhost:8000")

@pytest.fixture(scope="session")
def tesseract_available():
    return shutil.which("tesseract") is not None

def pytest_collection_modifyitems(config, items):
    # Skip @e2e unless -k e2e is explicitly requested
    k = config.getoption("-k") or ""
    if "e2e" not in k:
        skip_e2e = pytest.mark.skip(reason="Skipping e2e by default; run with -k e2e")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)


@pytest.fixture(scope="session")
def wait_for_api():
    """Wait for /health up to ~60s; skip e2e if not available."""
    if httpx is None:
        pytest.skip("httpx not installed; skipping e2e")
    url = f"{BASE}/health"
    for _ in range(60):
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    pytest.skip("API not reachable at /health; skipping e2e")

@pytest.fixture(scope="session")
def ensure_seed(wait_for_api):
    # Create & embed a tiny doc so search has something to find.
    # Generate an in-memory PNG with the text "Hello"
    base = Image.new("L", (260, 70), color=255) 
    d = ImageDraw.Draw(base)
    text = "HELLO SEED CONTENT"
    x, y = 8, 20
    for dx, dy in [(0,0),(1,0),(0,1),(1,1),(-1,0),(0,-1)]:  # thicken strokes
        d.text((x+dx, y+dy), text, fill=0)
    # Upscale 4x with NEAREST to avoid blur (improves OCR a lot)
    img = base.resize((base.width*4, base.height*4), resample=Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    f = {'file': ('seed.png', png_bytes, 'image/png')}
    r = httpx.post(f"{BASE}/upload", files=f, timeout=20)
    r.raise_for_status()
    asset_id = r.json()['id']

    httpx.post(f"{BASE}/documents/{asset_id}/ocr", timeout=60).raise_for_status()
    httpx.post(f"{BASE}/documents/{asset_id}/embed", timeout=60).raise_for_status()
    return asset_id