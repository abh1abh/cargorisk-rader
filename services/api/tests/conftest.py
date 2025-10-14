import os
import shutil
import time

import httpx
import pytest

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
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj <<>> endobj\n"
        b"2 0 obj << /Type /Catalog /Pages 3 0 R >> endobj\n"
        b"3 0 obj << /Type /Pages /Kids [4 0 R] /Count 1 >> endobj\n"
        b"4 0 obj << /Type /Page /Parent 3 0 R /MediaBox [0 0 200 200] >> endobj\n"
        b"5 0 obj << /Length 44 >> stream\n"
        b"BT /F1 12 Tf 72 120 Td (Hello seed content) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000010 00000 n \n0000000053 00000 n \n0000000101 00000 n \n"
        b"0000000167 00000 n \n0000000290 00000 n \n"
        b"trailer << /Size 6 /Root 2 0 R >>\nstartxref\n360\n%%EOF"
    )

    f = {'file': ('seed.pdf', pdf_bytes, 'application/pdf')}
    r = httpx.post(f"{BASE}/upload", files=f, timeout=20)
    r.raise_for_status()
    asset_id = r.json()['id']
    httpx.post(f"{BASE}/documents/{asset_id}/ocr", timeout=60).raise_for_status()
    httpx.post(f"{BASE}/documents/{asset_id}/embed", timeout=60).raise_for_status()
    return asset_id