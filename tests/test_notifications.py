# tests/test_notifications.py


# --- mark as read ---


def test_mark_as_read(auth_client):
    """Notifications can be marked as read."""
    response = auth_client.post("/notifications/read")
    assert response.status_code == 302


# --- follow notification ---


def test_notification_on_follow(auth_client, app):
    """A notification is created when a user is followed."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    auth_client.post("/profile/otheruser/follow")

    other.post("/auth/login", data={"username": "otheruser", "password": "pass123"})
    response = other.get("/notifications/")
    assert b"followed you" in response.data


# --- reply notification ---


def test_notification_on_reply(auth_client, app):
    """A notification is created when a user receives a reply to their post."""
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Original Post",
            "body": "This post will receive a reply",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]

    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    other.post("/auth/login", data={"username": "otheruser", "password": "pass123"})
    other.post(
        f"/posts/{post_id}/reply",
        data={"body": "This is a reply to the original post", "topic_id": ""},
    )

    response = auth_client.get("/notifications/")
    assert b"replied to your post" in response.data


# --- grade notification ---


def test_grade_notification_created(
    app, teacher_client, student_client, classroom, assignment
):
    """A notification is created for the student when a teacher grades their submission."""
    # enroll student in classroom
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()

    # student submits
    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )

    # teacher grades
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A", "feedback": "Great work!"},
    )

    # student checks notifications
    response = student_client.get("/notifications/")
    assert response.status_code == 200
    assert b"graded" in response.data


def test_grade_notification_links_to_assignment(
    app, teacher_client, student_client, classroom, assignment
):
    """The grade notification contains a link back to the assignment."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "B+", "feedback": "Good effort."},
    )

    with app.app_context():
        from app.models.notifications import get_notification

        notifications = get_notification(student_id)
        assert len(notifications) > 0
        grade_notif = next((n for n in notifications if n["type"] == "grade"), None)
        assert grade_notif is not None
        assert (
            f"/classrooms/{classroom}/assignments/{assignment}" in grade_notif["link"]
        )


def test_grade_notification_includes_assignment_title(
    app, teacher_client, student_client, classroom, assignment
):
    """The notification message includes the assignment title."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A-", "feedback": "Well done."},
    )

    with app.app_context():
        from app.models.notifications import get_notification

        notifications = get_notification(student_id)
        grade_notif = next((n for n in notifications if n["type"] == "grade"), None)
        assert grade_notif is not None
        assert "Test Assignment" in grade_notif["message"]


def test_grade_notification_unread_count(
    app, teacher_client, student_client, classroom, assignment
):
    """Grading increments the student's unread notification count."""
    with app.app_context():
        from app.models import get_db
        from app.models.notifications import get_unread_count

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()
        before = get_unread_count(student_id)

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "C", "feedback": "Needs improvement."},
    )

    with app.app_context():
        from app.models.notifications import get_unread_count

        after = get_unread_count(student_id)
        assert after == before + 1


def test_no_grade_notification_for_other_students(
    app, teacher_client, student_client, classroom, assignment
):
    """Only the graded student receives a notification, not others in the classroom."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()

    # register a second student
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "student2",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post("/auth/login", data={"username": "student2", "password": "pass123"})

    with app.app_context():
        from app.models import get_db
        from app.models.notifications import get_unread_count

        db = get_db()
        other_student = db.execute(
            "SELECT id FROM users WHERE username = 'student2'"
        ).fetchone()
        other_id = other_student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, other_id),
        )
        db.commit()

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A", "feedback": "Excellent."},
    )

    with app.app_context():
        from app.models.notifications import get_unread_count

        assert get_unread_count(other_id) == 0


def test_grade_notification_marked_read(
    app, teacher_client, student_client, classroom, assignment
):
    """Student can mark the grade notification as read."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student_id),
        )
        db.commit()

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A", "feedback": "Perfect."},
    )

    student_client.post("/notifications/read")

    with app.app_context():
        from app.models.notifications import get_unread_count

        assert get_unread_count(student_id) == 0
