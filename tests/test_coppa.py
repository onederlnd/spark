from app.models.user import create_user, get_user_by_username
from app.models import get_db


# --- registratoin / COPPA status
def test_register_user_under_13_sets_pending(client):
    """Users under 13 should have coppa_status 'pending'"""

    response = client.post(
        "/auth/register",
        data={
            "username": "child_user",
            "password": "pass123",
            "bio": "",
            "dob": "2015-01-01",
        },
    )
    assert response.status_code == 302
    user = get_user_by_username("child_user")
    assert user["coppa_status"] == "pending"


def test_register_over_13_sets_approved(client):
    """Users 13+ should be marked coppa_status = 'approved'"""
    response = client.post(
        "/auth/register",
        data={
            "username": "teen_user",
            "password": "pass123",
            "bio": "",
            "dob": "2005-01-01",
        },
    )
    assert response.status_code == 302
    user = get_user_by_username("teen_user")
    assert user["coppa_status"] == "approved"


def test_register_invalid_dob(client):
    """Invalid DOB format should return error."""
    response = client.post(
        "/auth/register",
        data={
            "username": "bad_dob",
            "password": "pass123",
            "bio": "",
            "dob": "01-01-2010",
        },
    )
    assert b"Invalid date format" in response.data


# --- login / access restrictions
def test_under_13_cannot_login(client):
    """Under 13 cannot login"""
    create_user("child_user", "pass123", dob="2015-01-01")
    response = client.post(
        "/auth/login",
        data={"username": "child_user", "password": "pass123"},
        follow_redirects=True,
    )
    assert (
        b"restricted" in response.data or b"Account pending approval." in response.data
    )


def test_over_13_can_login(client):
    """Over-13 users can login and access protected routes"""
    create_user("teen_user", "pass123", dob="2005-01-01")
    response = client.post(
        "/auth/login",
        data={"username": "teen_user", "password": "pass123"},
        follow_redirects=True,
    )
    assert b"feed" in response.data or b"Welcome" in response.data
    with client.session_transaction() as sess:
        assert "user_id" in sess


# --- route restrictions
def test_under_13_cannot_create_post(client):
    """Under 13 users are blocked from creating posts"""
    create_user("child_post", "pass123", dob="2015-01-01")

    with client.session_transaction() as sess:
        user = get_user_by_username("child_post")
        sess["user_id"] = user["id"]
        sess["coppa_status"] = user["coppa_status"]

    response = client.post("/posts/new", data={"body": "You shouldn't see this."})
    assert response.status_code == 302
    assert "/auth/coppa/notice" in response.headers["Location"]


def test_over_13_can_create_post(client):
    """Over 13 users can create posts"""
    create_user("teen_post", "pass123", dob="2005-01-01")

    with client.session_transaction() as sess:
        user = get_user_by_username("teen_post")
        sess["user_id"] = user["id"]
        sess["coppa_status"] = user["coppa_status"]

    response = client.post("/posts/new", data={"body": "You shouldn't see this."})
    assert response.status_code == 200


def test_under_13_cannot_access_feed(client):
    """Under 13 users are redirected to COPPA notice"""
    create_user("child_user", "pass123", dob="2015-01-01")
    response = client.post(
        "/auth/login",
        data={"username": "child_user", "password": "pass123"},
        follow_redirects=True,
    )
    assert b"Account Pending Approval" in response.data
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_approved_student_can_access_feed(client):
    """Over-13 or approved users can login and access feed"""
    create_user("student_user", "pass123", dob="2012-05-10")
    response = client.post(
        "/auth/login",
        data={"username": "student_user", "password": "pass123"},
        follow_redirects=True,
    )
    assert b"Feed" in response.data


# --- teacher approval test
def test_teacher_can_approve_coppa(client):
    create_user("pending_student", "pass123", dob="2015-01-01")
    create_user("teacher", "pass123", dob="2000-01-01", role="teacher")

    user = get_user_by_username("pending_student")

    with client.session_transaction() as sess:
        teacher = get_user_by_username("teacher")
        sess["user_id"] = teacher["id"]

    response = client.post(f"/auth/coppa/approve/{user['id']}", follow_redirects=True)
    assert response.status_code == 200


def test_student_sees_coppa_message(client):
    """Pending COPPA student sees notice when logging in"""
    create_user("child_user", "pass123", dob="2015-01-01")
    response = client.post(
        "/auth/login",
        data={"username": "child_user", "password": "pass123"},
        follow_redirects=True,
    )
    assert b"Account Pending Approval" in response.data
    assert b"child_user" in response.data


def test_teacher_receives_coppa_pending_notification(client):
    """Teacher receives COPPA notification when a student signs up"""
    create_user("teacher1", "pass123", dob="2000-01-01", role="teacher")
    create_user("student1", "pass123", dob="2015-01-01")

    teacher = get_user_by_username("teacher1")
    with client.session_transaction() as sess:
        sess["user_id"] = teacher["id"]

    response = client.get("/notifications", follow_redirects=True)

    assert b"student1 has pending COPPA approval" in response.data


def test_teacher_can_approve_pending_coppa(client):
    """Teacher and approve student with pending COPPA status"""
    create_user("teacher", "pass123", dob="2000-01-01", role="teacher")
    create_user("student", "pass123", dob="2015-01-01")

    teacher = get_user_by_username("teacher")
    student = get_user_by_username("student")

    with client.session_transaction() as sess:
        sess["user_id"] = teacher["id"]

    response = client.post(
        f"/auth/coppa/approve/{student['id']}", follow_redirects=True
    )
    assert response.status_code == 200

    student = get_user_by_username("student")
    assert student["coppa_status"] == "approved"


def test_student_can_login_after_coppa_approval(client):
    """Student login after approval serves them with feed"""
    create_user("student", "pass123", dob="2015-01-01")
    student = get_user_by_username("student")

    db = get_db()
    db.execute("UPDATE users SET coppa_status='approved' WHERE id=?", (student["id"],))
    db.commit()

    response = client.post(
        "/auth/login",
        data={"username": "student", "password": "pass123"},
        follow_redirects=True,
    )

    assert b"Feed" in response.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") == student["id"]
        assert sess.get("coppa_status") == "approved"


def test_teacher_can_deny_pendng(client):
    pass
