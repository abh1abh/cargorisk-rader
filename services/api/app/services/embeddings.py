from sentence_transformers import SentenceTransformer

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def embed_text(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0]*384
    vec = get_model().encode([text[:5000]], normalize_embeddings=True)[0]
    return vec.tolist()

