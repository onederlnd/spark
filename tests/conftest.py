# tests/conftest.py
import os
import pytest
import tempfile
from app import create_app
from app.utils.rate_limit import _request_counts
from app.utils.brute_force import _lockouts


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset the in-memory rate limit store before each test"""
    _request_counts.clear()
    yield
    _request_counts.clear()


@pytest.fixture(autouse=True)
def reset_brute_force():
    from app.utils.brute_force import _failed_attempts, _clean_attempts

    _failed_attempts.clear()
    _lockouts.clear()
    yield
    _failed_attempts.clear()
    _lockouts.clear()


@pytest.fixture(scope="function")
def app():
    db_fd, db_path = tempfile.mkstemp()

    test_app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": db_path,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-source",
            "BCRYPT_ROUNDS": 4,
        }
    )
    yield test_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def auth_client(app):
    client = app.test_client()
    client.post(
        "/auth/register",
        data={"username": "testuser", "password": "pass123", "bio": "test bio"},
    )
    client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "pass123",
        },
    )
    return client
