from functools import lru_cache

from celery import Celery

from .config import get_settings

_celery = None

@lru_cache(maxsize=1)
def get_celery() -> Celery:
    s = get_settings()
    app = Celery(broker=s.redis_url, backend=s.redis_url)
    return app