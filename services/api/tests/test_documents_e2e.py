import io, httpx, pytest
from PIL import Image, ImageDraw, ImageFont
import os

BASE = os.getenv("BASE", "http://localhost:8000")

@pytest.mark.e2e
def test_upload_and_ocr_e2e(tesseract_available):
    # create a simple text file
    # Generate an in-memory PNG with the text "Hello"
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 25), "Hello seed content", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    f = {'file': ('hello.png', png_bytes, 'image/png')}
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
