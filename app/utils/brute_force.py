# app/utils/brute_force.py

import time
from collections import defaultdict

_failed_attempts = defaultdict(list)
_lockouts = {}
MAX_ATTEMPTS = 5
IP_MAX_ATTEMPTS = 10
WINDOW_SECONDS = 900  # 15 minutes
LOCKOUT_SECONDS = 900  # 15 minutes


def _clean_attempts(key):
    """Remove attempts outside the rolling window"""
    now = time.monotonic()
    _failed_attempts[key] = [
        t for t in _failed_attempts[key] if now - t < WINDOW_SECONDS
    ]


def is_locked_out(username, ip):
    """Return (locked, seconds_remaining) for username or IP"""
    now = time.monotonic()

    for key in (f"user:{username}", f"ip:{ip}"):
        if key in _lockouts:
            remaining = _lockouts[key] - now
            if remaining > 0:
                return True, int(remaining)
            else:
                del _lockouts[key]
    return False, 0


def record_failure(username, ip):
    """Record a failed login attempt. Lock out if threshold reached"""
    now = time.monotonic()

    user_key = f"user:{username}"
    ip_key = f"ip:{ip}"

    _clean_attempts(user_key)
    _clean_attempts(ip_key)

    _failed_attempts[user_key].append(now)
    _failed_attempts[ip_key].append(now)

    if len(_failed_attempts[user_key]) >= MAX_ATTEMPTS:
        _lockouts[user_key] = now + LOCKOUT_SECONDS

    if len(_failed_attempts[ip_key]) >= IP_MAX_ATTEMPTS:
        _lockouts[ip_key] = now + LOCKOUT_SECONDS


def record_success(username):
    """Reset failed attempts on success login"""
    user_key = f"user:{username}"
    _failed_attempts[user_key] = []
    _lockouts.pop(user_key, None)


# est this sia  test
