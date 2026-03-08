# app/utils/rate_limit.py
import time
from collections import defaultdict
from functools import wraps
from flask import session, abort

# in-memory store rate limiter {user_id: [timestamps]}
_request_counts = defaultdict(list)


def rate_limit(max_requests, window_seconds):
    """
    Decorator to rate limit routes per user
    max_requests: number of allowed requests
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return f(*args, **kwargs)  # not logged in, skip rate limit

            now = time.time()
            key = f"{user_id}:{f.__name__}"

            # remove timestamps outside the window
            _request_counts[key] = [
                t for t in _request_counts[key] if now - t < window_seconds
            ]

            # check if limit exceeeededd
            if len(_request_counts[key]) >= max_requests:
                abort(429)

            # record
            _request_counts[key].append(now)

            return f(*args, **kwargs)

        return decorated

    return decorator
