# --- email invite ---


def test_invite_coteacher_by_email(app, teacher_client, classroom):
    """Owner can send an email invite to a new co-teacher."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "newteacher@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invite sent" in response.data


def test_invite_coteacher_by_email_creates_invite(app, teacher_client, classroom):
    """Email invite creates a pending record in the database."""
    teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "pending@example.com"},
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT * FROM classroom_invites WHERE email = ?",
            ("pending@example.com",),
        ).fetchone()
        assert invite is not None
        assert invite["classroom_id"] == classroom
        assert invite["accepted"] == 0


def test_invite_coteacher_invalid_email(teacher_client, classroom):
    """Submitting a malformed email shows an error."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "notanemail"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid email" in response.data


def test_invite_coteacher_no_input(teacher_client, classroom):
    """Submitting neither username nor email shows an error."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"username": "", "email": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"username or email" in response.data


def test_accept_invite_on_register(app, teacher_client, classroom):
    """Registering with a valid invite token adds the user as co-teacher."""
    # create the invite
    teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "invited@example.com"},
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT token FROM classroom_invites WHERE email = ?",
            ("invited@example.com",),
        ).fetchone()
        token = invite["token"]

    # register using the invite link
    new_teacher = app.test_client(use_cookies=True)
    new_teacher.post(
        f"/auth/register?invite={token}",
        data={
            "username": "invitedteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "1990-01-01",
            "email": "invited@example.com",
            "invite": token,
        },
    )

    with app.app_context():
        from app.models.classroom import get_member_role
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = 'invitedteacher'"
        ).fetchone()
        assert user is not None
        role = get_member_role(classroom, user["id"])
        assert role == "teacher"


def test_accept_invite_marks_accepted(app, teacher_client, classroom):
    """After registering via invite, the invite is marked as accepted."""
    teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "accepted@example.com"},
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT token FROM classroom_invites WHERE email = ?",
            ("accepted@example.com",),
        ).fetchone()
        token = invite["token"]

    new_teacher = app.test_client(use_cookies=True)
    new_teacher.post(
        f"/auth/register?invite={token}",
        data={
            "username": "acceptedteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "1990-01-01",
            "email": "accepted@example.com",
            "invite": token,
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT accepted FROM classroom_invites WHERE token = ?", (token,)
        ).fetchone()
        assert invite["accepted"] == 1


def test_invite_token_only_works_once(app, teacher_client, classroom):
    """A used invite token cannot be used again."""
    teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "onceonly@example.com"},
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT token FROM classroom_invites WHERE email = ?",
            ("onceonly@example.com",),
        ).fetchone()
        token = invite["token"]

    # use it once
    new_teacher = app.test_client(use_cookies=True)
    new_teacher.post(
        f"/auth/register?invite={token}",
        data={
            "username": "onceteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "1990-01-01",
            "email": "onceonly@example.com",
            "invite": token,
        },
    )

    # try to use it again
    with app.app_context():
        from app.models.classroom import get_invite_by_token

        result = get_invite_by_token(token)
        assert result is None


def test_accept_invite_on_login(app, teacher_client, classroom):
    """Logging in with a valid invite token adds the user as co-teacher."""
    # create a teacher account first
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "existingteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "1990-01-01",
            "email": "existing@example.com",
        },
    )

    # create invite for their email
    teacher_client.post(
        f"/classrooms/{classroom}/coteachers/invite",
        data={"email": "existing@example.com"},
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        invite = db.execute(
            "SELECT token FROM classroom_invites WHERE email = ?",
            ("existing@example.com",),
        ).fetchone()
        token = invite["token"]

    # log in with invite token
    other.post(
        f"/auth/login?invite={token}",
        data={
            "username": "existingteacher",
            "password": "pass123",
        },
    )

    with app.app_context():
        from app.models.classroom import get_member_role
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = 'existingteacher'"
        ).fetchone()
        role = get_member_role(classroom, user["id"])
        assert role == "teacher"
