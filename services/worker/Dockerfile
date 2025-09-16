FROM python:3.11-slim
WORKDIR /app
COPY services/api/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY services/worker /app
CMD ["celery", "-A", "worker.app", "worker", "-l", "INFO"]
