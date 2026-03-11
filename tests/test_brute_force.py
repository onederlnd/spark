# test_brute_force.py

from app.utils.brute_force import (
    record_failure,
    is_locked_out,
    record_success,
    _lockouts,
    _failed_attempts,
    WINDOW_SECONDS,
)


def test_failed_login_does_not_lockout_early():
    """4 failures should not trigger a lockout"""

    for _ in range(4):
        record_failure("testuser", "127.0.0.1")

    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False


def test_lockout_after_max_attempts():
    for _ in range(5):
        record_failure("testuser", "127.0.0.1")

    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is True


def test_record_success_resets_counter():

    for _ in range(4):
        record_failure("testuser", "192.168.1.1")

    record_success("testuser")

    locked, _ = is_locked_out("testuser", "192.168.1.1")
    assert locked is False


def test_lockout_message_shown_on_login(client):
    for _ in range(5):
        record_failure("testuser", "127.0.0.1")

    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpass"}
    )

    assert response.status_code == 200
    assert b"Too many failed attempts in response.data"


def test_ip_lockout_after_threshold():
    for i in range(10):
        record_failure("{i}", "127.0.0.1")
    locked, _ = is_locked_out("anyuser", "127.0.0.1")
    assert locked is True


def test_successful_login_after_lockout_expires():
    import time

    for _ in range(5):
        record_failure("testuser", "127.0.0.1")

    _lockouts["user:testuser"] = time.monotonic() - 1

    locked, _ = is_locked_out("testuser", "10.0.0.1")

    assert locked is False


def test_lockout_does_not_reveal_username_exists(client):
    """Locked out user and non existent user should get the same error message"""
    for _ in range(5):
        client.post(
            "/auth/login", data={"username": "testuser", "password": "wrongpass"}
        )

    for _ in range(5):
        client.post(
            "/auth/login", data={"username": "wronguser", "password": "rightpass"}
        )

    real_response = client.post(
        "/auth/login", data={"username": "testuser", "password": "wrongpass"}
    )
    fake_response = client.post(
        "/auth/login", data={"username": "wronguser", "password": "rightpass"}
    )

    assert b"Too many failed attempts" in real_response.data
    assert b"Too many failed attempts" in fake_response.data
    assert b"testuser" not in real_response.data
    assert b"wronguser" not in fake_response.data


def test_failed_attempts_outside_window_do_not_count():
    """Failed attempts older thn the window should not count toward lockout"""
    for _ in range(4):
        record_failure("testuser", "127.0.0.1")

    _failed_attempts["user:testuser"] = [
        t - WINDOW_SECONDS - 1 for t in _failed_attempts["user:testuser"]
    ]
    _failed_attempts["ip:127.0.0.1"] = [
        t - WINDOW_SECONDS - 1 for t in _failed_attempts["ip:127.0.0.1"]
    ]
    record_failure("testuser", "127.0.0.1")
    # DEBUG
    print(f"user attempts: {len(_failed_attempts['user:testuser'])}")
    print(f"ip attempts: {len(_failed_attempts['ip:127.0.0.1'])}")
    print(f"lockouts: {dict(_lockouts)}")
    # /DEBUG
    locked, _ = is_locked_out("testuser", "127.0.0.1")
    assert locked is False
