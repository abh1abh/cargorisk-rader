import threading

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "auto", embed_dim: int = 384) -> None:
        self.model = model
        self.device = self._resolve_device(device)
        self.embed_dim = embed_dim
        self._model: SentenceTransformer | None = None
        self._model_lock = threading.Lock()
    
    # Internal
    def _resolve_device(self, device: str) -> str:
        """Pick an available device if 'auto' is requested."""
        if device != "auto":
            return device
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu" 
    
    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._model = SentenceTransformer(self.model, device=self.device)
        return self._model
    
    # Public
    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0]*self.embed_dim
        
        snippet = text[:5000]
        model = self._get_model()
        # normalize_embeddings=True already L2-normalizes the output
        vec = model.encode([snippet], normalize_embeddings=True, convert_to_numpy=True)[0]
        if not isinstance(vec, np.ndarray) or vec.shape[0] != self.embed_dim or not np.isfinite(vec).all():
            return [0.0] * self.embed_dim
        return vec.tolist()



