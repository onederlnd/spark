# tests/conftest.py
import os
import pytest
import tempfile
from app import create_app


@pytest.fixture(scope="function")
def app():
    db_fd, db_path = tempfile.mkstemp()

    test_app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": db_path,
            "SECRET_KEY": "test-source",
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
        data={"username": "testuser", "password": "testpass123", "bio": "test bio"},
    )
    client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    return client
