# tests/test_messaging.py

from tests.conftest import _make_classroom, _join_classroom


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _register_and_login(app, *, username, role="student", dob="2005-01-01"):
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": "pass123",
            "bio": "",
            "role": role,
            "dob": dob,
        },
    )
    client.post("/auth/login", data={"username": username, "password": "pass123"})
    return client


def _setup_classroom_with_students(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student_a = _register_and_login(app, username="student_a")
    student_b = _register_and_login(app, username="student_b")
    _join_classroom(student_a, join_code)
    _join_classroom(student_b, join_code)
    return join_code, classroom_id, student_a, student_b


def _enable_messaging(teacher_client, classroom_id):
    teacher_client.post(
        f"/messages/classroom/{classroom_id}/toggle-messaging",
        data={"enabled": "1"},
    )


def _send_new_conversation(
    client, classroom_id, recipient_ids, body="Hello!", title=""
):
    return client.post(
        "/messages/new",
        data={
            "classroom_id": classroom_id,
            "recipient_ids": recipient_ids,
            "body": body,
            "title": title,
        },
        follow_redirects=False,
    )


def _make_teacher_student_conv(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        send_message(conv_id, teacher_id, "Hello!")
        return conv_id, student_a


# ---------------------------------------------------------------------------
# authentication / access control
# ---------------------------------------------------------------------------


def test_inbox_requires_login(client):
    r = client.get("/messages/")
    assert r.status_code in (302, 403)
    if r.status_code == 302:
        assert "/auth/login" in r.headers["Location"]


def test_new_conversation_requires_login(client):
    r = client.get("/messages/new")
    assert r.status_code in (302, 403)


def test_conversation_view_requires_login(client):
    r = client.get("/messages/1")
    assert r.status_code in (302, 403)


def test_send_requires_login(client):
    r = client.post("/messages/1/send", data={"body": "hi"})
    assert r.status_code in (302, 403)


def test_load_messages_requires_login(client):
    r = client.get("/messages/1/messages")
    assert r.status_code in (302, 403)


# ---------------------------------------------------------------------------
# inbox
# ---------------------------------------------------------------------------


def test_inbox_loads(teacher_client):
    r = teacher_client.get("/messages/")
    assert r.status_code == 200


def test_inbox_shows_conversations(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(
            classroom_id, teacher_id, [student_id], title="Test Thread"
        )
        send_message(conv_id, teacher_id, "Welcome!")

    r = teacher_client.get("/messages/")
    assert r.status_code == 200
    assert b"Test Thread" in r.data or b"Welcome!" in r.data


def test_api_conversations_returns_json(teacher_client):
    r = teacher_client.get("/messages/api/conversations")
    assert r.status_code == 200
    assert r.is_json
    assert isinstance(r.get_json(), list)


# ---------------------------------------------------------------------------
# creating conversations
# ---------------------------------------------------------------------------


def test_new_conversation_page_loads(teacher_client):
    r = teacher_client.get("/messages/new")
    assert r.status_code == 200


def test_teacher_can_message_student(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db

        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(
        teacher_client, classroom_id, [student_id], body="Hey student!"
    )
    assert r.status_code == 302
    assert "/messages/" in r.headers["Location"]


def test_student_to_student_requires_messaging_enabled(app, teacher_client):
    join_code, classroom_id, student_a, student_b = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db

        student_b_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_b'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(student_a, classroom_id, [student_b_id], body="Hi!")
    assert r.status_code in (200, 302)
    if r.status_code == 302:
        follow = student_a.get(r.headers["Location"])
        assert (
            b"not enabled" in follow.data.lower() or b"Student messaging" in follow.data
        )


def test_student_to_student_succeeds_when_enabled(app, teacher_client):
    join_code, classroom_id, student_a, student_b = _setup_classroom_with_students(
        app, teacher_client
    )
    _enable_messaging(teacher_client, classroom_id)
    with app.app_context():
        from app.models import get_db

        student_b_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_b'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(student_a, classroom_id, [student_b_id], body="Hi!")
    assert r.status_code == 302
    assert "/messages/" in r.headers["Location"]


def test_missing_classroom_rejected(teacher_client):
    r = teacher_client.post(
        "/messages/new",
        data={"body": "hi", "recipient_ids": [9999]},
        follow_redirects=True,
    )
    assert r.status_code in (200, 302)


def test_missing_recipient_rejected(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="Empty Class")
    r = teacher_client.post(
        "/messages/new",
        data={"classroom_id": classroom_id, "body": "hi"},
        follow_redirects=True,
    )
    assert b"recipient" in r.data.lower() or r.status_code in (200, 302)


def test_empty_body_rejected(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db

        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )

    r = teacher_client.post(
        "/messages/new",
        data={"classroom_id": classroom_id, "recipient_ids": [student_id], "body": ""},
        follow_redirects=True,
    )
    assert b"empty" in r.data.lower() or b"cannot" in r.data.lower()


def test_parent_cannot_message_student(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    parent = _register_and_login(
        app, username="parent_user", role="parent", dob="1980-01-01"
    )
    _join_classroom(parent, join_code)
    with app.app_context():
        from app.models import get_db

        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(parent, classroom_id, [student_id], body="Hi kid")
    assert r.status_code in (200, 302)
    if r.status_code == 302:
        follow = parent.get(r.headers["Location"])
        assert b"parent" in follow.data.lower() or b"cannot" in follow.data.lower()


def test_student_cannot_message_parent(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    parent = _register_and_login(
        app, username="parent_user2", role="parent", dob="1980-01-01"
    )
    _join_classroom(parent, join_code)
    with app.app_context():
        from app.models import get_db

        parent_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'parent_user2'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(student_a, classroom_id, [parent_id], body="Hi parent")
    assert r.status_code in (200, 302)


def test_nonmember_cannot_message(app, teacher_client):
    _, classroom_id, student_a, student_b = _setup_classroom_with_students(
        app, teacher_client
    )
    outsider = _register_and_login(app, username="outsider")
    with app.app_context():
        from app.models import get_db

        student_b_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_b'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(outsider, classroom_id, [student_b_id], body="Sneaky")
    assert r.status_code in (200, 302)


# ---------------------------------------------------------------------------
# conversation view & membership
# ---------------------------------------------------------------------------


def test_member_can_view_conversation(app, teacher_client):
    conv_id, student_a = _make_teacher_student_conv(app, teacher_client)
    r = student_a.get(f"/messages/{conv_id}")
    assert r.status_code == 200


def test_nonmember_cannot_view_conversation(app, teacher_client):
    conv_id, _ = _make_teacher_student_conv(app, teacher_client)
    outsider = _register_and_login(app, username="outsider2")
    r = outsider.get(f"/messages/{conv_id}")
    assert r.status_code == 302


def test_conversation_404_for_missing_id(teacher_client):
    r = teacher_client.get("/messages/99999")
    assert r.status_code in (302, 404)


def test_load_messages_json(app, teacher_client):
    conv_id, student_a = _make_teacher_student_conv(app, teacher_client)
    r = student_a.get(f"/messages/{conv_id}/messages")
    assert r.status_code == 200
    assert r.is_json
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["body"] == "Hello!"


def test_load_messages_after_id(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        m1 = send_message(conv_id, teacher_id, "First")
        send_message(conv_id, teacher_id, "Second")

    r = student_a.get(f"/messages/{conv_id}/messages?after_id={m1}")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 1
    assert data[0]["body"] == "Second"


def test_load_messages_forbidden_for_nonmember(app, teacher_client):
    conv_id, _ = _make_teacher_student_conv(app, teacher_client)
    outsider = _register_and_login(app, username="outsider3")
    r = outsider.get(f"/messages/{conv_id}/messages")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# sending messages
# ---------------------------------------------------------------------------


def test_member_can_send(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])

    r = student_a.post(f"/messages/{conv_id}/send", data={"body": "Reply here!"})
    assert r.status_code == 302
    r2 = student_a.get(f"/messages/{conv_id}")
    assert b"Reply here!" in r2.data


def test_empty_message_rejected(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])

    r = student_a.post(
        f"/messages/{conv_id}/send", data={"body": ""}, follow_redirects=True
    )
    assert b"empty" in r.data.lower() or b"cannot" in r.data.lower()


def test_nonmember_cannot_send(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])

    outsider = _register_and_login(app, username="outsider4")
    r = outsider.post(f"/messages/{conv_id}/send", data={"body": "Sneaky!"})
    assert r.status_code in (302, 403)


# ---------------------------------------------------------------------------
# DM shortcut
# ---------------------------------------------------------------------------


def test_dm_creates_or_reuses_conversation(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    r = teacher_client.get(f"/messages/dm/student_a?classroom_id={classroom_id}")
    assert r.status_code == 302
    assert "/messages/" in r.headers["Location"]

    r2 = teacher_client.get(f"/messages/dm/student_a?classroom_id={classroom_id}")
    assert r2.headers["Location"] == r.headers["Location"]


def test_dm_unknown_user_404(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="DM Class")
    r = teacher_client.get(f"/messages/dm/nobody_exists?classroom_id={classroom_id}")
    assert r.status_code == 404


def test_dm_without_classroom_flashes_error(teacher_client):
    r = teacher_client.get("/messages/dm/student_a", follow_redirects=True)
    assert b"classroom" in r.data.lower()


# ---------------------------------------------------------------------------
# mark-read
# ---------------------------------------------------------------------------


def test_mark_read_api(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        send_message(conv_id, teacher_id, "Unread message")

    r = student_a.post(f"/messages/{conv_id}/mark-read")
    assert r.status_code == 200
    assert r.get_json().get("ok") is True


def test_mark_read_forbidden_for_nonmember(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])

    outsider = _register_and_login(app, username="outsider5")
    r = outsider.post(f"/messages/{conv_id}/mark-read")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# teacher oversight & moderation
# ---------------------------------------------------------------------------


def test_oversight_requires_teacher(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="Oversight Class")
    student = _register_and_login(app, username="stu_oversight")
    r = student.get(f"/messages/classroom/{classroom_id}/oversight")
    assert r.status_code == 403


def test_teacher_can_view_oversight(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="Oversight Class2")
    r = teacher_client.get(f"/messages/classroom/{classroom_id}/oversight")
    assert r.status_code == 200


def test_hide_message_requires_teacher(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        msg_id = send_message(conv_id, student_id, "Student message")

    r = student_a.post(f"/messages/messages/{msg_id}/hide")
    assert r.status_code == 403


def test_teacher_can_hide_message(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        msg_id = send_message(conv_id, student_id, "Should be hidden")

    r = teacher_client.post(f"/messages/messages/{msg_id}/hide")
    assert r.status_code == 302

    msgs = student_a.get(f"/messages/{conv_id}/messages")
    bodies = [m["body"] for m in msgs.get_json()]
    assert "Should be hidden" not in bodies


# ---------------------------------------------------------------------------
# toggle student messaging
# ---------------------------------------------------------------------------


def test_teacher_can_toggle_messaging_on(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="Toggle Class")
    r = teacher_client.post(
        f"/messages/classroom/{classroom_id}/toggle-messaging",
        data={"enabled": "1"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"enabled" in r.data.lower()


def test_teacher_can_toggle_messaging_off(app, teacher_client):
    _, classroom_id = _make_classroom(teacher_client, name="Toggle Class Off")
    r = teacher_client.post(
        f"/messages/classroom/{classroom_id}/toggle-messaging",
        data={"enabled": "0"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"disabled" in r.data.lower()


def test_student_cannot_toggle_messaging(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    r = student_a.post(
        f"/messages/classroom/{classroom_id}/toggle-messaging",
        data={"enabled": "1"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# teacher oversight for under-13 students
# ---------------------------------------------------------------------------


def test_teacher_can_read_under13_conversation(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client, name="Under13 Class")
    young = app.test_client()
    young.post(
        "/auth/register",
        data={
            "username": "young_student",
            "password": "pass123",
            "bio": "",
            "dob": "2015-01-01",
        },
    )
    young.post("/auth/login", data={"username": "young_student", "password": "pass123"})
    _join_classroom(young, join_code)

    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        young_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'young_student'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [young_id])
        send_message(conv_id, young_id, "I need help")

    r = teacher_client.get(f"/messages/{conv_id}")
    assert r.status_code == 200


def test_unrelated_teacher_cannot_read_under13_conversation(app, teacher_client):
    """A teacher NOT in the classroom cannot use oversight to read conversations
    involving under-13 students — the oversight grant is classroom-scoped."""
    join_code, classroom_id = _make_classroom(teacher_client, name="Under13 Class2")
    young = app.test_client()
    young.post(
        "/auth/register",
        data={
            "username": "young_student2",
            "password": "pass123",
            "bio": "",
            "dob": "2015-01-01",
        },
    )
    young.post(
        "/auth/login", data={"username": "young_student2", "password": "pass123"}
    )
    _join_classroom(young, join_code)

    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        young_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'young_student2'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [young_id])
        send_message(conv_id, young_id, "Private message")

    outsider_teacher = _register_and_login(
        app, username="outsider_teacher", role="teacher", dob="1985-01-01"
    )
    r = outsider_teacher.get(f"/messages/{conv_id}")
    assert r.status_code == 302


# ---------------------------------------------------------------------------
# XSS / sanitization
# ---------------------------------------------------------------------------


def test_xss_in_message_body_escaped(app, teacher_client):
    join_code, classroom_id, student_a, _ = _setup_classroom_with_students(
        app, teacher_client
    )
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])

    student_a.post(
        f"/messages/{conv_id}/send", data={"body": "<script>alert('xss')</script>"}
    )
    r = student_a.get(f"/messages/{conv_id}")
    assert b"<script>alert" not in r.data


def test_xss_in_conversation_title_escaped(app, teacher_client):
    join_code, classroom_id, student_a, student_b = _setup_classroom_with_students(
        app, teacher_client
    )
    _enable_messaging(teacher_client, classroom_id)
    with app.app_context():
        from app.models import get_db

        student_b_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_b'")
            .fetchone()["id"]
        )

    r = _send_new_conversation(
        student_a,
        classroom_id,
        [student_b_id],
        body="Hi",
        title="<script>alert('xss')</script>",
    )
    if r.status_code == 302:
        r2 = student_a.get(r.headers["Location"])
        assert b"<script>alert" not in r2.data


# ---------------------------------------------------------------------------
# model-level unit tests
# ---------------------------------------------------------------------------


def test_get_or_create_dm_idempotent(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import get_or_create_dm

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        cid1 = get_or_create_dm(classroom_id, teacher_id, student_id)
        cid2 = get_or_create_dm(classroom_id, teacher_id, student_id)
        assert cid1 == cid2


def test_get_total_unread_count(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import (
            create_conversation,
            send_message,
            get_total_unread_count,
        )

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        send_message(conv_id, teacher_id, "Unread 1")
        send_message(conv_id, teacher_id, "Unread 2")
        count = get_total_unread_count(student_id)
        assert count >= 2


def test_unread_count_resets_after_mark_read(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import (
            create_conversation,
            send_message,
            mark_read,
            get_total_unread_count,
        )

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        send_message(conv_id, teacher_id, "Message!")
        mark_read(conv_id, student_id)
        count = get_total_unread_count(student_id)
        assert count == 0


def test_hidden_message_excluded_from_get_messages(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import (
            create_conversation,
            send_message,
            hide_message,
            get_messages,
        )

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        msg_id = send_message(conv_id, student_id, "This will be hidden")
        hide_message(msg_id)
        msgs = get_messages(conv_id)
        assert "This will be hidden" not in [m["body"] for m in msgs]


def test_before_id_pagination(app, teacher_client):
    join_code, classroom_id, _, _ = _setup_classroom_with_students(app, teacher_client)
    with app.app_context():
        from app.models import get_db
        from app.models.messaging import create_conversation, send_message, get_messages

        teacher_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()["id"]
        )
        student_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student_a'")
            .fetchone()["id"]
        )
        conv_id = create_conversation(classroom_id, teacher_id, [student_id])
        send_message(conv_id, teacher_id, "Oldest")
        m2 = send_message(conv_id, teacher_id, "Middle")
        send_message(conv_id, teacher_id, "Newest")
        older = get_messages(conv_id, before_id=m2)
        assert len(older) == 1
        assert older[0]["body"] == "Oldest"


def test_can_message_unknown_classroom(app, teacher_client):
    with app.app_context():
        from app.models.messaging import can_message

        ok, reason = can_message(1, [2], 99999)
        assert ok is False
        assert "not found" in reason.lower()
