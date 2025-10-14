import os

import httpx
import pytest

BASE = os.getenv("BASE", "http://localhost:8000")

@pytest.mark.e2e
def test_upload_and_ocr_e2e(tesseract_available):
    # create a simple text file
    f = {'file': ('hello.txt', b'Hello Incoterms CFA', 'text/plain')}
    r = httpx.post(f"{BASE}/upload", files=f, timeout=30)
    r.raise_for_status()
    asset_id = r.json()['id']

    if not tesseract_available:
        pytest.skip("tesseract not available in PATH")

    r = httpx.post(f"{BASE}/documents/{asset_id}/ocr", timeout=120)
    r.raise_for_status()

    r = httpx.get(f"{BASE}/documents/{asset_id}/text", timeout=30)
    r.raise_for_status()
    assert "Hello" in r.json()['text']
