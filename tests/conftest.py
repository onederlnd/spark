# tests/conftest.py
import os
import re
import pytest
import tempfile
from app import create_app
from app.utils.rate_limit import _request_counts
from app.utils.brute_force import _lockouts
from app.models.post import create_post


# ---------------------------------------------------------------------------
# shared helper functions (not fixtures — import or call directly in tests)
# ---------------------------------------------------------------------------


def _make_classroom(teacher_client, name="Test Classroom"):
    """Create a classroom via the teacher client. Returns (join_code, classroom_id)."""
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": name},
        follow_redirects=True,
    )
    html = response.data.decode()
    match = re.search(r"/classrooms/(\d+)", html)
    if not match:
        raise ValueError("Classroom ID not found in response HTML")
    classroom_id = int(match.group(1))
    with teacher_client.application.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT join_code FROM classrooms WHERE id = ?", (classroom_id,))
            .fetchone()
        )
        return row["join_code"], classroom_id


def _join_classroom(client, join_code):
    """Join a classroom via join code."""
    return client.post(
        "/classrooms/join",
        data={"join_code": join_code},
        follow_redirects=True,
    )


def _post_announcement(client, classroom_id, *, title="Announcement", body="Test body"):
    """Create an announcement directly in the DB (no HTTP route for post_type yet)."""
    with client.application.app_context():
        from app.models import get_db

        db = get_db()
        # get the teacher's user_id from session cookie isn't available here,
        # so look up by the known teacher username
        user = db.execute("SELECT id FROM users WHERE username = 'teacher1'").fetchone()
        db.execute(
            """INSERT INTO posts (user_id, title, body, classroom_id, post_type, is_hidden, parent_id)
               VALUES (?, ?, ?, ?, 'announcement', 0, NULL)""",
            (user["id"], title, body, classroom_id),
        )
        db.commit()


def _register_student(
    client,
    join_code,
    *,
    first="Alice",
    last="Smith",
    password="pass123",
    dob="2005-06-01",
    email="",
):
    """POST to /auth/register/student and return the response."""
    return client.post(
        "/auth/register/student",
        data={
            "first_name": first,
            "last_name": last,
            "password": password,
            "dob": dob,
            "join_code": join_code,
            "email": email,
        },
    )


def _register_teacher(
    client,
    *,
    first="Bob",
    last="Jones",
    password="pass123",
    dob="1985-03-15",
    email="bob@school.edu",
):
    """POST to /auth/register/teacher and return the response."""
    return client.post(
        "/auth/register/teacher",
        data={
            "first_name": first,
            "last_name": last,
            "password": password,
            "dob": dob,
            "email": email,
        },
    )


def _get_user(app, username_prefix):
    """Fetch the first user whose username starts with username_prefix."""
    with app.app_context():
        from app.models import get_db

        return (
            get_db()
            .execute(
                "SELECT * FROM users WHERE username LIKE ?", (f"{username_prefix}%",)
            )
            .fetchone()
        )


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def classroom(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": "Test Classroom"},
        follow_redirects=True,
    )
    html = response.data.decode()
    match = re.search(r"/classrooms/(\d+)", html)
    if not match:
        raise ValueError("Classroom ID not found in response HTML")
    return int(match.group(1))


@pytest.fixture
def post(classroom):
    """Create a post by student in a classroom."""
    return create_post(
        user_id=2, title="Test Post", body="test body", classroom_id=classroom
    )


@pytest.fixture()
def assignment(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={
            "title": "Test Assignment",
            "instructions": "Solve 1-10",
            "due_date": "2030-01-01",
        },
    )
    location = response.headers["Location"]
    parts = location.rstrip("/").split("/")
    return int(parts[-2])


@pytest.fixture(autouse=True)
def reset_brute_force():
    from app.utils.brute_force import _failed_attempts

    _failed_attempts.clear()
    _lockouts.clear()
    yield
    _failed_attempts.clear()
    _lockouts.clear()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    _request_counts.clear()
    yield
    _request_counts.clear()


@pytest.fixture(scope="function")
def app():
    db_fd, db_path = tempfile.mkstemp()
    test_app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": db_path,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
            "BCRYPT_ROUNDS": 4,
            "SESSION_TIMEOUT_MINUTES": 10,
            "PROPAGATE_EXCEPTIONS": True,
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
        data={
            "username": "testuser",
            "password": "pass123",
            "bio": "test bio",
            "dob": "2000-01-01",
        },
    )
    client.post("/auth/login", data={"username": "testuser", "password": "pass123"})
    return client


@pytest.fixture(scope="function")
def teacher_client(app):
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "teacher1",
            "password": "pass123",
            "bio": "test teacher",
            "role": "teacher",
            "dob": "2000-01-01",
        },
    )
    client.post("/auth/login", data={"username": "teacher1", "password": "pass123"})
    return client


@pytest.fixture(scope="function")
def student_client(app, teacher_client):
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "student1",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    client.post("/auth/login", data={"username": "student1", "password": "pass123"})
    return client


@pytest.fixture(autouse=True)
def mock_emails(monkeypatch):
    import app.utils.email as email_module
    import app.routes.auth as auth_module
    import app.routes.admin as admin_module

    monkeypatch.setattr(auth_module, "send_welcome_email", lambda *a, **kw: None)
    monkeypatch.setattr(
        email_module, "send_coteacher_invite_email_by_email", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        email_module, "send_coteacher_invite_email", lambda *a, **kw: None
    )
    monkeypatch.setattr(admin_module, "send_acceptance_email", lambda *a, **kw: None)
    monkeypatch.setattr(
        email_module, "send_waitlist_admin_notification", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        email_module, "send_waitlist_confirmation", lambda *a, **kw: None
    )


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        from app.models import get_db

        yield get_db()
