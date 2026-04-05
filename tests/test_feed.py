# tests/test_feed.py
from conftest import _make_classroom, _join_classroom, _post_announcement
from app.models import get_db

# --- feed routes ---


def test_feed_requires_login(client):
    response = client.get("/feed/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_feed_loads(auth_client):
    response = auth_client.get("/feed/")
    assert response.status_code == 200


def test_feed_default_shows_all(auth_client):
    response = auth_client.get("/feed/")
    assert response.status_code == 200
    assert b"For You" in response.data


# tests/test_feed.py  (additions)


def test_announcements_requires_login(client):
    r = client.get("/feed/announcements", follow_redirects=False)
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_announcements_loads_empty(auth_client):
    r = auth_client.get("/feed/announcements")
    assert r.status_code == 200
    assert b"No announcements yet" in r.data


def test_announcement_visible_to_member(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    _post_announcement(teacher_client, classroom_id, title="Exam next week")

    r = student_client.get("/feed/announcements")
    assert r.status_code == 200
    assert b"Exam next week" in r.data


def test_announcement_visible_to_teacher(teacher_client):
    _, classroom_id = _make_classroom(teacher_client)
    _post_announcement(teacher_client, classroom_id, title="Teacher sees own post")

    r = teacher_client.get("/feed/announcements")
    assert r.status_code == 200
    assert b"Teacher sees own post" in r.data


def test_announcement_not_visible_to_non_member(teacher_client, student_client):
    _, classroom_id = _make_classroom(teacher_client)
    _post_announcement(teacher_client, classroom_id, title="Secret announcement")

    r = student_client.get("/feed/announcements")
    assert b"Secret announcement" not in r.data


def test_announcements_not_in_regular_feed(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    _post_announcement(teacher_client, classroom_id, title="Announcements only")

    r = student_client.get("/feed/")
    assert b"Announcements only" not in r.data


def test_announcements_shows_classroom_name(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client, name="Biology 101")
    _join_classroom(student_client, join_code)
    _post_announcement(teacher_client, classroom_id, title="Lab tomorrow")

    r = student_client.get("/feed/announcements")
    assert b"Biology 101" in r.data


def test_announcements_pagination(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    for i in range(22):
        _post_announcement(teacher_client, classroom_id, title=f"Announcement {i}")

    r1 = student_client.get("/feed/announcements?page=1")
    r2 = student_client.get("/feed/announcements?page=2")
    assert b"Next" in r1.data
    assert b"Prev" in r2.data


def test_assignments_requires_login(client):
    r = client.get("/feed/assignments", follow_redirects=False)
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_assignments_loads_empty(auth_client):
    r = auth_client.get("/feed/assignments")
    assert r.status_code == 200
    assert b"No assignments yet" in r.data


def test_assignment_visible_to_member(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={
            "title": "Essay #1",
            "instructions": "Write 500 words",
            "due_date": "2030-06-01",
        },
    )

    r = student_client.get("/feed/assignments")
    assert r.status_code == 200
    assert b"Essay #1" in r.data


def test_assignment_not_visible_to_non_member(teacher_client, student_client):
    _, classroom_id = _make_classroom(teacher_client)
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={
            "title": "Hidden Assignment",
            "instructions": "...",
            "due_date": "2030-06-01",
        },
    )

    r = student_client.get("/feed/assignments")
    assert b"Hidden Assignment" not in r.data


def test_assignment_shows_not_submitted(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={"title": "Pending HW", "instructions": "Do it", "due_date": "2030-01-01"},
    )

    r = student_client.get("/feed/assignments")
    assert b"Not submitted" in r.data


def test_assignment_shows_submitted(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    resp = teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={"title": "Submit Me", "instructions": "Do it", "due_date": "2030-01-01"},
    )
    assignment_id = int(resp.headers["Location"].rstrip("/").split("/")[-2])
    student_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}",
        data={"body": "My answer"},
        follow_redirects=True,
    )

    r = student_client.get("/feed/assignments")
    assert b"Submitted" in r.data


def test_assignment_shows_graded(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    resp = teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={"title": "Grade Me", "instructions": "Do it", "due_date": "2030-01-01"},
    )
    assignment_id = int(resp.headers["Location"].rstrip("/").split("/")[-2])
    student_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}",
        data={"body": "My answer"},
        follow_redirects=True,
    )
    with app.app_context():
        student = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student1'")
            .fetchone()
        )
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}/grade/{student['id']}",
        data={"grade": "A", "feedback": "Good work"},
        follow_redirects=True,
    )

    r = student_client.get("/feed/assignments")
    assert b"Graded" in r.data


def test_assignment_shows_grade_value(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    resp = teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={
            "title": "Grade Value Test",
            "instructions": "Do it",
            "due_date": "2030-01-01",
        },
    )
    assignment_id = int(resp.headers["Location"].rstrip("/").split("/")[-2])
    student_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}",
        data={"body": "My answer"},
        follow_redirects=True,
    )
    with app.app_context():
        student = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student1'")
            .fetchone()
        )
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}/grade/{student['id']}",
        data={"grade": "A+", "feedback": "Excellent"},
        follow_redirects=True,
    )

    r = student_client.get("/feed/assignments")
    assert b"A+" in r.data


def test_assignments_pagination(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    for i in range(22):
        teacher_client.post(
            f"/classrooms/{classroom_id}/assignments/new",
            data={
                "title": f"Assignment {i}",
                "instructions": "...",
                "due_date": "2030-01-01",
            },
        )

    r1 = student_client.get("/feed/assignments?page=1")
    r2 = student_client.get("/feed/assignments?page=2")
    assert b"Next" in r1.data
    assert b"Prev" in r2.data


def test_unsubmitted_sorted_before_submitted(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)

    resp = teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={"title": "Submit Me", "instructions": "...", "due_date": "2030-01-01"},
    )
    assignment_id = int(resp.headers["Location"].rstrip("/").split("/")[-2])
    teacher_client.post(
        f"/classrooms/{classroom_id}/assignments/new",
        data={"title": "Pending One", "instructions": "...", "due_date": "2030-06-01"},
    )
    student_client.post(
        f"/classrooms/{classroom_id}/assignments/{assignment_id}",
        data={"body": "done"},
        follow_redirects=True,
    )

    r = student_client.get("/feed/assignments")
    html = r.data.decode()
    assert html.index("Pending One") < html.index("Submit Me")


# --- announcements not in following feed ---


def test_announcements_not_in_following_feed(teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)
    _post_announcement(teacher_client, classroom_id, title="Following Feed Leak")

    r = student_client.get("/feed/following")
    assert b"Following Feed Leak" not in r.data


# --- create_post positional arg bug (topic_id landing in classroom_id slot) ---


def test_regular_post_has_no_classroom(app, auth_client):
    auth_client.post(
        "/posts/new",
        data={"title": "Topic Post", "body": "some content", "topic_id": ""},
    )
    with app.app_context():
        row = (
            get_db()
            .execute(
                "SELECT classroom_id, post_type FROM posts WHERE title = 'Topic Post'"
            )
            .fetchone()
        )
    assert row is not None
    assert row["classroom_id"] is None
    assert row["post_type"] == "post"


def test_regular_post_appears_in_feed(auth_client):
    auth_client.post(
        "/posts/new",
        data={"title": "Should Appear", "body": "visible content"},
    )
    r = auth_client.get("/feed/")
    assert b"Should Appear" in r.data


# --- replies don't surface as feed posts ---


def test_reply_not_in_feed(app, auth_client):
    resp = auth_client.post(
        "/posts/new",
        data={"title": "Parent Post", "body": "parent body"},
    )
    post_id = int(resp.headers["Location"].rstrip("/").split("/")[-1])
    auth_client.post(
        f"/posts/{post_id}/reply",
        data={"body": "this is a reply"},
    )

    r = auth_client.get("/feed/")
    html = r.data.decode()
    assert "this is a reply" not in html


def test_reply_not_in_following_feed(app, teacher_client, student_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _join_classroom(student_client, join_code)

    # student follows teacher
    with app.app_context():
        teacher = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()
        )
        student = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'student1'")
            .fetchone()
        )
        get_db().execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (student["id"], teacher["id"]),
        )
        get_db().commit()

    resp = teacher_client.post(
        "/posts/new",
        data={"title": "Teacher Post", "body": "teacher body"},
    )
    post_id = int(resp.headers["Location"].rstrip("/").split("/")[-1])
    teacher_client.post(
        f"/posts/{post_id}/reply",
        data={"body": "reply should not appear"},
    )

    r = student_client.get("/feed/following")
    assert b"reply should not appear" not in r.data
