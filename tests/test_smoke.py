# tests/test_smoke.py
"""
Smoke tests for SparK SIT environment.

Goal: verify that all critical paths return expected status codes,
auth gates redirect unauthenticated users, and no route returns 500.

Fixtures reused from conftest.py:
  client          — unauthenticated test client
  auth_client     — logged-in student
  teacher_client  — logged-in teacher
  classroom       — classroom owned by teacher_client
  assignment      — assignment inside that classroom
"""

"""
import re
import pytest


# ---------------------------------------------------------------------------
# helper
# ---------------------------------------------------------------------------


def _enroll_student(app, classroom_id, username="student1"):
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if student:
            db.execute(
                "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) "
                "VALUES (?, ?, 'student')",
                (classroom_id, student["id"]),
            )
            db.commit()
            return student["id"]
    return None


# ===========================================================================
# AUTH — register / login / logout
# ===========================================================================


def test_login_page_loads(client):
    r = client.get("/auth/login")
    assert r.status_code == 200
    assert b"login" in r.data.lower() or b"sign in" in r.data.lower()


def test_register_page_loads(client):
    r = client.get("/auth/register")
    assert r.status_code in (200, 302)


def test_login_valid_credentials(app):
    c = app.test_client()
    c.post(
        "/auth/register",
        data={"username": "smokeuser", "password": "pass1234", "dob": "2000-01-01"},
    )
    r = c.post("/auth/login", data={"username": "smokeuser", "password": "pass1234"})
    assert r.status_code == 302


def test_login_wrong_password(app):
    c = app.test_client()
    c.post(
        "/auth/register",
        data={"username": "smokeuser2", "password": "pass1234", "dob": "2000-01-01"},
    )
    r = c.post(
        "/auth/login",
        data={"username": "smokeuser2", "password": "wrongpass"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert (
        b"invalid" in r.data.lower()
        or b"incorrect" in r.data.lower()
        or b"wrong" in r.data.lower()
    )


def test_login_nonexistent_user(client):
    r = client.post(
        "/auth/login",
        data={"username": "nobody_xyz", "password": "pass123"},
        follow_redirects=True,
    )
    assert r.status_code == 200


def test_logout_redirects(auth_client):
    r = auth_client.get("/auth/logout")
    assert r.status_code == 302


def test_logout_clears_session(auth_client):
    auth_client.get("/auth/logout")
    r = auth_client.get("/posts/new")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_terms_page_loads(client):
    r = client.get("/auth/terms")
    assert r.status_code == 200


def test_privacy_page_loads(client):
    r = client.get("/auth/privacy")
    assert r.status_code == 200


# ===========================================================================
# FEED & POSTS
# ===========================================================================


def test_feed_unauthenticated_loads_or_redirects(client):
    r = client.get("/")
    assert r.status_code in (200, 302)


def test_feed_authenticated_loads(auth_client):
    r = auth_client.get("/")
    assert r.status_code == 200
    assert b"500" not in r.data


def test_feed_following_tab(auth_client):
    r = auth_client.get("/?feed=following")
    assert r.status_code == 200


def test_new_post_page_requires_auth(client):
    r = client.get("/posts/new")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_new_post_page_loads_for_auth_user(auth_client):
    r = auth_client.get("/posts/new")
    assert r.status_code == 200


def test_create_post(auth_client):
    r = auth_client.post(
        "/posts/new",
        data={"title": "Smoke Test Post", "body": "Hello world from smoke test"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Smoke Test Post" in r.data


def test_create_post_missing_title(auth_client):
    r = auth_client.post(
        "/posts/new",
        data={"title": "", "body": "Body without title"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"500" not in r.data


def test_view_post(auth_client):
    r = auth_client.post(
        "/posts/new",
        data={"title": "View Me", "body": "Some body text"},
    )
    location = r.headers.get("Location", "")
    match = re.search(r"/posts/(\d+)", location)
    if match:
        post_id = match.group(1)
        r2 = auth_client.get(f"/posts/{post_id}")
        assert r2.status_code == 200
        assert b"View Me" in r2.data


def test_view_nonexistent_post(auth_client):
    r = auth_client.get("/posts/99999")
    assert r.status_code == 404


def test_topics_page_loads(auth_client):
    r = auth_client.get("/topics")
    assert r.status_code == 200


# ===========================================================================
# SEARCH
# ===========================================================================


def test_search_page_loads(auth_client):
    r = auth_client.get("/search?type=posts")
    assert r.status_code == 200


def test_search_with_query(auth_client):
    r = auth_client.get("/search?q=test&type=posts")
    assert r.status_code == 200
    assert b"500" not in r.data


def test_search_empty_query(auth_client):
    r = auth_client.get("/search?q=")
    assert r.status_code == 200
    assert b"500" not in r.data


def test_search_unauthenticated(client):
    r = client.get("/search?q=hello")
    assert r.status_code in (200, 302)


# ===========================================================================
# CLASSROOMS
# ===========================================================================


def test_classrooms_list_requires_auth(client):
    r = client.get("/classrooms/")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_classrooms_list_loads(teacher_client, classroom):
    r = teacher_client.get("/classrooms/")
    assert r.status_code == 200
    assert b"Test Classroom" in r.data


def test_classroom_detail_loads(teacher_client, classroom):
    r = teacher_client.get(f"/classrooms/{classroom}/")
    assert r.status_code == 200
    assert b"500" not in r.data


def test_classroom_detail_requires_auth(client, classroom):
    r = client.get(f"/classrooms/{classroom}/")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_classroom_detail_non_member_forbidden(auth_client, classroom):
    r = auth_client.get(f"/classrooms/{classroom}/")
    assert r.status_code == 403


def test_classroom_not_found(teacher_client):
    r = teacher_client.get("/classrooms/99999/")
    assert r.status_code == 404


def test_create_classroom_page_loads(teacher_client):
    r = teacher_client.get("/classrooms/new")
    assert r.status_code == 200


def test_create_classroom_student_forbidden(auth_client):
    r = auth_client.post("/classrooms/new", data={"name": "Nope"})
    assert r.status_code == 403


def test_join_classroom_bad_code(auth_client):
    r = auth_client.post(
        "/classrooms/join",
        data={"join_code": "BADCODE"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"500" not in r.data


# ===========================================================================
# ASSIGNMENTS
# ===========================================================================


def test_assignment_detail_loads_for_teacher(teacher_client, classroom, assignment):
    r = teacher_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert r.status_code == 200


def test_assignment_detail_requires_auth(client, classroom, assignment):
    r = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_assignment_not_found(teacher_client, classroom):
    r = teacher_client.get(f"/classrooms/{classroom}/assignments/99999")
    assert r.status_code == 404


def test_student_can_view_assignment(app, student_client, classroom, assignment):
    _enroll_student(app, classroom)
    r = student_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert r.status_code == 200


def test_student_submit_assignment(app, student_client, classroom, assignment):
    _enroll_student(app, classroom)
    r = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My smoke test answer"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"has been saved" in r.data


def test_teacher_cannot_submit_assignment(teacher_client, classroom, assignment):
    r = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Teacher answer"},
    )
    assert r.status_code == 403


def test_create_assignment_page_loads(teacher_client, classroom):
    r = teacher_client.get(f"/classrooms/{classroom}/assignments/new")
    assert r.status_code == 200


def test_create_assignment_student_forbidden(app, student_client, classroom):
    _enroll_student(app, classroom)
    r = student_client.get(f"/classrooms/{classroom}/assignments/new")
    assert r.status_code == 403


# ===========================================================================
# NOTIFICATIONS
# ===========================================================================


def test_notifications_requires_auth(client):
    r = client.get("/notifications/")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_notifications_loads(auth_client):
    r = auth_client.get("/notifications/")
    assert r.status_code == 200
    assert b"500" not in r.data


# ===========================================================================
# PROFILE & SETTINGS
# ===========================================================================


def test_profile_loads_for_known_user(auth_client):
    r = auth_client.get("/profile/testuser")
    assert r.status_code == 200


def test_profile_not_found(auth_client):
    r = auth_client.get("/profile/nobody_xyz_zzz")
    assert r.status_code == 404


def test_settings_requires_auth(client):
    r = client.get("/profile/settings")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_settings_loads(auth_client):
    r = auth_client.get("/profile/settings")
    assert r.status_code == 200


# ===========================================================================
# GLOBAL — no route should return 500
# ===========================================================================


@pytest.mark.parametrize(
    "path",
    [
        "/auth/login",
        "/auth/terms",
        "/auth/privacy",
    ],
)
def test_public_route_no_500(client, path):
    r = client.get(path)
    assert r.status_code != 500, f"Got 500 on {path}"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/classrooms/",
        "/notifications/",
        "/topics",
        "/search?type=posts",
    ],
)
def test_auth_route_no_500(auth_client, path):
    r = auth_client.get(path)
    assert r.status_code != 500, f"Got 500 on {path}"
"""
