import logging, time, uuid, contextvars
from typing import Optional, Dict, Any

# Context for correlation id
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True

def setup_logging(level: str = "INFO") -> None:
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s request_id=%(request_id)s"
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt)
    # add filter to root so all loggers get request_id
    logging.getLogger().addFilter(RequestIdFilter())

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def now_ms() -> float:
    return time.perf_counter() * 1000.0

def new_request_id() -> str:
    return str(uuid.uuid4())
