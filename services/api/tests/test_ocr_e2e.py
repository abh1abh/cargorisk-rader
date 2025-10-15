# services/api/tests/test_ocr_e2e.py
import io
import os

import fitz  # PyMuPDF
import httpx
import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.getenv("BASE", "http://localhost:8000")


def _ocr_friendly_png_bytes(text="HELLO OCR TEST"):
    # Use larger base resolution
    base = Image.new("L", (800, 200), color=255)
    d = ImageDraw.Draw(base)

    # Use a clean, bold font (fallback to default if not available)
    try:
        font = ImageFont.truetype("arialbd.ttf", 120)  # Bold Arial
    except Exception:
        font = ImageFont.load_default()

    # Draw text centered
    bbox = d.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (base.width - text_width) // 2
    y = (base.height - text_height) // 2

    d.text((x, y), text, fill=0, font=font)


    # Optional: slight blur improves OCR detection on some engines
    img = base.filter(ImageFilter.GaussianBlur(radius=0.3))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _native_pdf_bytes(text="HELLO OCR NATIVE"):
    # Create a PDF that contains actual text (no images), so pdf_bytes_to_text()
    # picks it up via page.get_text("text") deterministically.
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4-ish
    page.insert_text((72, 120), text, fontsize=24)  # 1-inch margin at 72pt
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.e2e
@pytest.mark.ocr
def test_ocr_pdf_native_text(wait_for_api):
    # Deterministic: no OCR, pure text extraction
    pdf = _native_pdf_bytes("HELLO OCR NATIVE")
    files = {'file': ('native.pdf', pdf, 'application/pdf')}

    r = httpx.post(f"{BASE}/upload", files=files, timeout=30)
    r.raise_for_status()
    asset_id = r.json()['id']

    httpx.post(f"{BASE}/document/{asset_id}/ocr?lang=eng", timeout=60).raise_for_status()
    text = httpx.get(f"{BASE}/document/{asset_id}/text", timeout=30).json().get("text","")

    assert "hello" in text.lower(), f"Expected native text, got: {text!r}"


@pytest.mark.e2e
@pytest.mark.ocr
def test_ocr_image_and_pdf(tesseract_available, wait_for_api):
    if not tesseract_available:
        pytest.skip("tesseract not available in PATH")

    # IMAGE OCR (assert non-empty only to avoid flakiness)
    png_bytes = _ocr_friendly_png_bytes("HELLO SEED CONTENT")
    r = httpx.post(f"{BASE}/upload",
                   files={'file': ('ocr.png', png_bytes, 'image/png')},
                   timeout=30)
    r.raise_for_status()
    img_id = r.json()['id']

    httpx.post(f"{BASE}/document/{img_id}/ocr?lang=eng", timeout=120).raise_for_status()
    img_text = httpx.get(f"{BASE}/document/{img_id}/text", timeout=30).json().get("text","")
    assert img_text.strip(), "Image OCR returned empty text"

    # IMAGE-ONLY PDF OCR (assert non-empty)
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    pdf_buf = io.BytesIO()
    img.save(pdf_buf, format="PDF")
    pdf_bytes = pdf_buf.getvalue()

    r = httpx.post(f"{BASE}/upload",
                   files={'file': ('ocr.pdf', pdf_bytes, 'application/pdf')},
                   timeout=30)
    r.raise_for_status()
    pdf_id = r.json()['id']

    httpx.post(f"{BASE}/document/{pdf_id}/ocr?lang=eng", timeout=120).raise_for_status()
    pdf_text = httpx.get(f"{BASE}/document/{pdf_id}/text", timeout=30).json().get("text","")
    assert pdf_text.strip(), "Image-only PDF OCR returned empty text"
