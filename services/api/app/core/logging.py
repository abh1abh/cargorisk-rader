import contextvars
import logging
import time
import uuid

# Context for correlation id
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

def setup_logging(level: str = "INFO") -> None:

    root = logging.getLogger()
    # Run once
    if getattr(root, "_cargorisk_configured", False):
        return
    
    orig_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = orig_factory(*args, **kwargs)
        try:
            record.request_id = request_id_ctx.get()
        except Exception:
            record.request_id = "-"
        return record
    logging.setLogRecordFactory(record_factory)

    fmt = "%(levelname)s:     %(asctime)s - Domain: %(name)s - Message: %(message)s - request_id=%(request_id)s"
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt, force=True)

    # Prevent Uvicorn's own loggers from double-printing through root
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).propagate = False

    root._cargorisk_configured = True

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def now_ms() -> float:
    return time.perf_counter() * 1000.0

def new_request_id() -> str:
    return str(uuid.uuid4())
