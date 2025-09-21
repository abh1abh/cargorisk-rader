import time

from fastapi import Request

from .logging import get_logger, new_request_id, request_id_ctx

log = get_logger("api.http")

async def http_logging_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    token = request_id_ctx.set(rid)
    t0 = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000.0
        # Log the error path with a best-effort status (usually handled by error middleware)
        log.exception(
            "http_request_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": 500,  # conservative default; actual may differ
                "ms": round(dt, 2),
                "error": e.__class__.__name__,
            },
        )
        raise
    finally:
        # Only log the normal request line if we actually got a response
        if response is not None:
            dt = (time.perf_counter() - t0) * 1000.0
            log.info(
                "http_request",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status": getattr(response, "status_code", 0),
                    "ms": round(dt, 2),
                },
            )
        request_id_ctx.reset(token)
