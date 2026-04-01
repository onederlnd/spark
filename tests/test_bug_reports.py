# tests/test_bug_reports.py
from app.models import get_db


def test_submit_bug_report_get_as_teacher(teacher_client):
    res = teacher_client.get("/bug-reports/submit")
    assert res.status_code == 200


def test_submit_bug_report_post_valid(teacher_client):
    res = teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "Something broke",
            "description": "It broke when I clicked the button",
            "severity": "medium",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Bug report submitted" in res.data


def test_submit_bug_report_missing_title(teacher_client):
    res = teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "",
            "description": "No title given",
            "severity": "low",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"required" in res.data


def test_submit_bug_report_missing_description(teacher_client):
    res = teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "Valid title",
            "description": "",
            "severity": "low",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"required" in res.data


def test_submit_bug_report_invalid_severity_defaults_to_low(teacher_client, app):
    teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "Bad severity",
            "description": "Testing severity fallback",
            "severity": "critical",
        },
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM bug_reports WHERE title = 'Bad severity'")
            .fetchone()
        )
    assert row is not None
    assert row["severity"] == "low"


def test_submit_bug_report_blocked_for_student(student_client, app):
    student_client.post(
        "/bug-reports/submit",
        data={
            "title": "Student bug",
            "description": "Should not work",
            "severity": "low",
        },
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM bug_reports WHERE title = 'Student bug'")
            .fetchone()
        )
    assert row is None


def test_submit_bug_report_blocked_for_anonymous(client, app):
    client.post(
        "/bug-reports/submit",
        data={
            "title": "Anon bug",
            "description": "No session",
            "severity": "low",
        },
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM bug_reports WHERE title = 'Anon bug'")
            .fetchone()
        )
    assert row is None


def test_my_reports_empty(teacher_client):
    res = teacher_client.get("/bug-reports/my-reports")
    assert res.status_code == 200


def test_my_reports_shows_own_report(teacher_client):
    teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "My report",
            "description": "Check it shows up",
            "severity": "high",
        },
        follow_redirects=True,
    )
    res = teacher_client.get("/bug-reports/my-reports")
    assert res.status_code == 200
    assert b"My report" in res.data


def test_my_reports_does_not_show_other_teachers_reports(teacher_client, app):
    teacher_client.post(
        "/bug-reports/submit",
        data={
            "title": "Teacher1 exclusive report",
            "description": "Belongs to teacher1",
            "severity": "low",
        },
        follow_redirects=True,
    )

    # register + login second teacher
    teacher2 = app.test_client()
    teacher2.post(
        "/auth/register",
        data={
            "username": "teacher2",
            "password": "pass123",
            "bio": "second teacher",
            "role": "teacher",
            "dob": "2000-01-01",
        },
    )
    teacher2.post("/auth/login", data={"username": "teacher2", "password": "pass123"})

    res = teacher2.get("/bug-reports/my-reports")
    assert b"Teacher1 exclusive report" not in res.data


def test_my_reports_blocked_for_student(student_client):
    res = student_client.get("/bug-reports/my-reports", follow_redirects=True)
    assert res.status_code in (403, 200)
    assert b"My report" not in res.data


def get_bug_reports_by_user(user_id):
    db = get_db()
    return db.execute(
        """
        SELECT br.*, u.username
        FROM bug_reports br JOIN users u ON br.reported_by = u.id
        WHERE br.reported_by = ?
        ORDER BY br.created_at DESC
        """,
        (user_id,),
    ).fetchall()
