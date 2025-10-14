import os

import httpx
import pytest

BASE = os.getenv("BASE", "http://localhost:8000")

@pytest.mark.e2e
def test_upload_and_ocr_e2e(tesseract_available):
    # create a simple text file
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
    f = {'file': ('hello.pdf', pdf_bytes, 'application/pdf')}
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
