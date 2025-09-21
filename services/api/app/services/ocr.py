import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageFilter, ImageOps


def _ocr_image(img: Image.Image, lang: str = "eng+nor") -> str:
    # light denoise and contrast enhancement
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return pytesseract.image_to_string(img, lang=lang, config="--oem 3 --psm 6")
def pdf_bytes_to_text(pdf_bytes: bytes, lang: str = "eng+nor") -> str:
    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            # 1) Native text first (fast, accurate for digital PDFs)
            native = page.get_text("text") or ""
            if native.strip():
                text_parts.append(native)
                continue
            # 2) Rasterize & OCR for image-only pages
            pix = page.get_pixmap(dpi=200, alpha=False)   # dpi 200 is a good trade-off
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            text_parts.append(_ocr_image(img, lang=lang))
    return "\n".join(text_parts).strip()

def image_bytes_to_text(img_bytes: bytes, lang: str = "eng+nor") -> str:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return _ocr_image(img, lang=lang).strip()
