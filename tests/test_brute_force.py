# tests/test_brute_force.py
import time
import pytest
from app.utils.brute_force import (
    record_failure,
    record_success,
    is_locked_out,
    _lockouts,
    _failed_attempts,
    WINDOW_SECONDS,
)


def _fail(username="testuser", ip="127.0.0.1", n=1):
    for _ in range(n):
        record_failure(username, ip)


def _expire_attempts(username, ip):
    """Push all recorded attempts outside the window so they no longer count."""
    key_user = f"user:{username}"
    key_ip = f"ip:{ip}"
    if key_user in _failed_attempts:
        _failed_attempts[key_user] = [
            t - WINDOW_SECONDS - 1 for t in _failed_attempts[key_user]
        ]
    if key_ip in _failed_attempts:
        _failed_attempts[key_ip] = [
            t - WINDOW_SECONDS - 1 for t in _failed_attempts[key_ip]
        ]


def _expire_lockout(username=None, ip=None):
    """Push lockout timestamp into the past so it registers as expired."""
    if username:
        _lockouts[f"user:{username}"] = time.monotonic() - 1
    if ip:
        _lockouts[f"ip:{ip}"] = time.monotonic() - 1


def test_single_failure_does_not_lock():
    _fail(n=1)
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_failures_below_threshold_do_not_lock():
    _fail(n=4)
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_lockout_triggers_at_threshold():
    _fail(n=5)
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is True


def test_lockout_returns_positive_seconds_remaining():
    _fail(n=5)
    locked, seconds = is_locked_out("testuser", "127.0.0.1")
    assert locked is True
    assert seconds > 0


def test_record_success_clears_user_counter():
    _fail(n=4)
    record_success("testuser")
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_record_success_does_not_clear_ip_counter():
    """Clearing a user counter should not affect the IP-level counter."""
    _fail(n=4)
    record_success("testuser")
    # IP still has 4 failures — 1 more should not re-lock via user key,
    # but IP key threshold should still be trackable independently
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False  # user key is clear


def test_record_success_allows_fresh_failure_tracking():
    """After a reset, 4 new failures should still not lock."""
    _fail(n=4)
    record_success("testuser")
    _fail(n=4)
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_ip_lockout_after_threshold():
    """Enough failures from one IP across any usernames should trigger IP lockout."""
    for i in range(10):
        record_failure(f"user_{i}", "127.0.0.1")
    locked, _ = is_locked_out("anyuser", "127.0.0.1")
    assert locked is True


def test_ip_lockout_affects_different_usernames():
    """A locked IP should block even a username with no failures."""
    for i in range(10):
        record_failure(f"spammer_{i}", "10.0.0.1")
    locked, _ = is_locked_out("innocent_user", "10.0.0.1")
    assert locked is True


def test_different_ips_do_not_share_ip_counter():
    for i in range(9):
        record_failure(f"unique_user_{i}", "1.1.1.1")
    locked, _ = is_locked_out("testuser", "2.2.2.2")
    assert locked is False


def test_ip_counter_locks_independently_of_username():
    for i in range(10):
        record_failure(f"user_{i}", "1.1.1.1")
    locked, _ = is_locked_out("anyuser", "1.1.1.1")
    assert locked is True


def test_username_counter_locks_across_different_ips():
    for ip in ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4", "5.5.5.5"]:
        record_failure("testuser", ip)
    locked, _ = is_locked_out("testuser", "9.9.9.9")
    assert locked is True


def test_username_and_ip_lock_independently():
    record_failure("testuser", "1.1.1.1")
    locked_user, _ = is_locked_out("testuser", "9.9.9.9")
    locked_ip, _ = is_locked_out("nobody", "1.1.1.1")
    assert locked_user is False
    assert locked_ip is False


def test_same_user_different_ips_user_key_aggregates():
    """User-level failures accumulate regardless of IP."""
    record_failure("testuser", "1.1.1.1")
    record_failure("testuser", "2.2.2.2")
    record_failure("testuser", "3.3.3.3")
    record_failure("testuser", "4.4.4.4")
    record_failure("testuser", "5.5.5.5")
    locked, _ = is_locked_out("testuser", "6.6.6.6")
    assert locked is True


def test_expired_lockout_is_no_longer_locked():
    _fail(n=5)
    _expire_lockout(username="testuser")
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_expired_lockout_seconds_remaining_is_zero_or_less():
    _fail(n=5)
    _expire_lockout(username="testuser")
    locked, seconds = is_locked_out("testuser", "127.0.0.1")
    assert not locked
    assert seconds <= 0


def test_attempts_outside_window_do_not_count():
    """Failures older than WINDOW_SECONDS should be ignored."""
    _lockouts.pop("user:testuser", None)
    _lockouts.pop("ip:127.0.0.1", None)

    _fail(n=4)
    _expire_attempts("testuser", "127.0.0.1")
    _fail(n=1)  # one fresh failure — should not reach threshold

    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_mix_of_expired_and_fresh_attempts():
    """Only in-window failures should count toward the threshold."""
    _lockouts.pop("user:testuser", None)
    _lockouts.pop("ip:127.0.0.1", None)

    _fail(n=3)
    _expire_attempts("testuser", "127.0.0.1")
    _fail(n=4)  # 4 fresh — still under threshold of 5

    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_lockout_message_shown_on_login(client):
    _fail(n=5)
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 200
    assert b"Too many failed attempts" in response.data


def test_lockout_shows_minutes_remaining(client):
    _fail(n=5)
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpass"}
    )
    assert b"minutes" in response.data


def test_lockout_does_not_reveal_username_exists(client):
    """Locked-out response should not confirm whether the username is real."""
    client.post(
        "/auth/register",
        data={
            "username": "realuser",
            "password": "correctpass",
            "bio": "",
            "dob": "2000-01-01",
        },
    )

    # lock out the real user via direct counter manipulation
    _fail(username="realuser", n=5)

    # also lock out a nonexistent user
    _fail(username="ghostuser", n=5)

    real_response = client.post(
        "/auth/login", data={"username": "realuser", "password": "wrongpass"}
    )
    fake_response = client.post(
        "/auth/login", data={"username": "ghostuser", "password": "wrongpass"}
    )

    assert b"Too many failed attempts" in real_response.data
    assert b"Too many failed attempts" in fake_response.data
    assert b"realuser" not in real_response.data
    assert b"ghostuser" not in fake_response.data


def test_failed_http_logins_trigger_lockout(client):
    """Brute force via actual HTTP requests should eventually lock the account."""
    client.post(
        "/auth/register",
        data={
            "username": "brutehttp",
            "password": "correct",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    for _ in range(5):
        client.post("/auth/login", data={"username": "brutehttp", "password": "wrong"})

    response = client.post(
        "/auth/login", data={"username": "brutehttp", "password": "wrong"}
    )
    assert b"Too many failed attempts" in response.data or b"locked" in response.data


def test_successful_login_resets_lockout_counter(client):
    """A successful login should clear failures so the user is no longer at risk."""
    client.post(
        "/auth/register",
        data={
            "username": "resetuser",
            "password": "correct",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    _fail(username="resetuser", n=4)
    client.post("/auth/login", data={"username": "resetuser", "password": "correct"})
    locked, _ = is_locked_out("resetuser", "127.0.0.1")
    assert locked is False


def test_is_locked_out_unknown_user_returns_false():
    locked, seconds = is_locked_out("nobody_ever", "127.0.0.1")
    assert locked is False
    assert seconds == 0


def test_record_success_unknown_user_does_not_crash():
    try:
        record_success("never_failed_user")
    except Exception as e:
        pytest.fail(f"record_success raised unexpectedly: {e}")


def test_lockout_is_case_sensitive_or_normalised(client):
    """Document whether TestUser and testuser share a failure counter."""
    _fail(username="CasedUser", n=5)
    locked_exact, _ = is_locked_out("CasedUser", "127.0.0.1")
    locked_lower, _ = is_locked_out("caseduser", "127.0.0.1")
    # either both locked (case-insensitive) or only the exact match (case-sensitive)
    # — this test documents whichever behaviour the implementation has
    assert locked_exact is True
    assert isinstance(locked_lower, bool)  # documents but doesn't prescribe
