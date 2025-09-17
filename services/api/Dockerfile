# services/api/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# shared deps at services/requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy only the api code
COPY api/ .



CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000","--reload"]
