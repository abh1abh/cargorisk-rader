from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    type: str
    storage_uri: str
    has_text: bool

class DocumentTextOut(BaseModel):
    id: int
    text: str

class OcrRunOut(BaseModel):
    id: int
    ocr_chars: int
