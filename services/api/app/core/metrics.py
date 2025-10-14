import time

from .logging import get_logger

log = get_logger("metrics")
def timed(label: str):
    start = time.perf_counter()
    def finish(extra: dict | None = None):
        ms = (time.perf_counter() - start) * 1000
        payload = {"ms": round(ms, 2), **(extra or {})}
        # flattened, log-friendly
        log.info("metric:%s %s", label, " ".join(f"{k}={v}" for k,v in payload.items()))
        return ms
    return finish
