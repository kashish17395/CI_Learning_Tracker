import time
from collections import defaultdict, deque
from functools import lru_cache
from threading import Lock
import redis
from app.core.config import get_settings
from app.core.errors import AppError

_attempts = defaultdict(deque)
_lock = Lock()


@lru_cache
def redis_client():
    url = get_settings().redis_url
    return redis.Redis.from_url(url, socket_timeout=3) if url else None


def limit(key, maximum=10, window=60):
    client = redis_client()
    if client:
        # Atomic fixed-window counter shared by all workers.
        script = "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"
        try:
            count = client.eval(script, 1, "learning:limit:" + key, window)
        except redis.RedisError:
            raise AppError(503, "AUTH_UNAVAILABLE", "Sign-in temporarily unavailable")
    else:
        with _lock:
            current = time.monotonic()
            entries = _attempts[key]
            while entries and entries[0] <= current - window:
                entries.popleft()
            entries.append(current)
            count = len(entries)
            if len(_attempts) > 10000:
                for old_key in list(_attempts):
                    if (
                        not _attempts[old_key]
                        or _attempts[old_key][-1] < current - window
                    ):
                        del _attempts[old_key]
    if count > maximum:
        raise AppError(429, "RATE_LIMITED", "Too many attempts. Try again shortly.")
