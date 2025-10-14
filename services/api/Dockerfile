# services/api/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# For tesseract 
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-osd \
      tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-nor \
      libtesseract-dev poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# shared deps at services/requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# >>> Pre-warm the SentenceTransformer model so no network is needed at runtime
ENV HF_HOME=/root/.cache/huggingface \
    TRANSFORMERS_CACHE=/root/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/root/.cache/huggingface
RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model cached.")
PY
# <<<

# copy only the api code
COPY . .


CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000","--workers","1"]
