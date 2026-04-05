# tests/test_lesson_builder.py
import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_lesson(teacher_client, classroom):
    """Create a lesson and return assignment_id."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={
            "title": "Test Lesson",
            "instructions": "",
            "due_date": "",
            "auto_grade": "on",
            "attempts_allowed": "1",
        },
    )
    assert response.status_code == 302
    location = response.headers["Location"]
    # redirects to /classrooms/<id>/assignments/<id>/builder
    assignment_id = int(location.rstrip("/").split("/")[-2])
    return assignment_id


def _add_block(teacher_client, classroom, assignment_id, block_type):
    return teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/add",
        data={"type": block_type},
        follow_redirects=True,
    )


def _get_block_id(app, assignment_id, block_type):
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT id FROM lesson_blocks WHERE assignment_id = ? AND type = ?",
                (assignment_id, block_type),
            )
            .fetchone()
        )
        return row["id"] if row else None


def _make_enrolled_student(app, teacher_client, classroom):
    from app.models.classroom import get_classroom

    with app.app_context():
        join_code = get_classroom(classroom)["join_code"]
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "lessonstu",
            "password": "pass123",
            "role": "student",
            "dob": "2010-01-01",
        },
    )
    client.post("/auth/login", data={"username": "lessonstu", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})
    return client


# ---------------------------------------------------------------------------
# lesson creation
# ---------------------------------------------------------------------------


def test_create_lesson_redirects_to_builder(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "My Lesson", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 302
    assert "builder" in response.headers["Location"]


def test_create_lesson_missing_title(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 200
    assert b"required" in response.data.lower()


def test_create_lesson_non_teacher(auth_client, classroom):
    response = auth_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "Sneaky", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 403


def test_create_lesson_unauthenticated(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "Test", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_create_lesson_invalid_classroom(teacher_client):
    response = teacher_client.post(
        "/classrooms/99999/assignments/new",
        data={"title": "Test", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 404


def test_create_lesson_saves_auto_grade(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT auto_grade FROM assignments WHERE id = ?", (assignment_id,)
            )
            .fetchone()
        )
        assert row["auto_grade"] == 1


def test_create_lesson_saves_attempts(app, teacher_client, classroom):
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={
            "title": "Attempts Test",
            "instructions": "",
            "due_date": "",
            "attempts_allowed": "3",
        },
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT attempts_allowed FROM assignments ORDER BY id DESC LIMIT 1"
            )
            .fetchone()
        )
        assert row["attempts_allowed"] == 3


# ---------------------------------------------------------------------------
# lesson builder page
# ---------------------------------------------------------------------------


def test_builder_loads(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.get(
        f"/classrooms/{classroom}/assignments/{assignment_id}/builder"
    )
    assert response.status_code == 200
    assert b"Test Lesson" in response.data


def test_builder_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    client = _make_enrolled_student(app, teacher_client, classroom)
    response = client.get(
        f"/classrooms/{classroom}/assignments/{assignment_id}/builder"
    )
    assert response.status_code == 403


def test_builder_invalid_assignment(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/99999/builder")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# adding blocks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block_type",
    ["text", "multiple_choice", "true_false", "short_answer", "file_upload"],
)
def test_add_block_all_types(app, teacher_client, classroom, block_type):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = _add_block(teacher_client, classroom, assignment_id, block_type)
    assert response.status_code == 200
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT * FROM lesson_blocks WHERE assignment_id = ? AND type = ?",
                (assignment_id, block_type),
            )
            .fetchone()
        )
        assert row is not None


def test_add_block_invalid_type(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/add",
        data={"type": "invalid_type"},
    )
    assert response.status_code == 400


def test_add_block_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    client = _make_enrolled_student(app, teacher_client, classroom)
    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/add",
        data={"type": "text"},
    )
    assert response.status_code == 403


def test_add_true_false_creates_choices(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "true_false")
    with app.app_context():
        from app.models import get_db

        block = (
            get_db()
            .execute(
                "SELECT id FROM lesson_blocks WHERE assignment_id = ? AND type = 'true_false'",
                (assignment_id,),
            )
            .fetchone()
        )
        choices = (
            get_db()
            .execute("SELECT * FROM block_choices WHERE block_id = ?", (block["id"],))
            .fetchall()
        )
        assert len(choices) == 2
        bodies = {c["body"] for c in choices}
        assert bodies == {"True", "False"}


def test_add_multiple_blocks_position_increments(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "text")
    _add_block(teacher_client, classroom, assignment_id, "multiple_choice")
    _add_block(teacher_client, classroom, assignment_id, "short_answer")
    with app.app_context():
        from app.models import get_db

        blocks = (
            get_db()
            .execute(
                "SELECT position FROM lesson_blocks WHERE assignment_id = ? ORDER BY position ASC",
                (assignment_id,),
            )
            .fetchall()
        )
        positions = [b["position"] for b in blocks]
        assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# updating blocks
# ---------------------------------------------------------------------------


def test_update_block_body(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "short_answer")
    block_id = _get_block_id(app, assignment_id, "short_answer")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={"body": "What is a loop?", "points": "3", "required": "on"},
    )
    with app.app_context():
        from app.models import get_db

        block = (
            get_db()
            .execute("SELECT * FROM lesson_blocks WHERE id = ?", (block_id,))
            .fetchone()
        )
        assert block["body"] == "What is a loop?"
        assert block["points"] == 3
        assert block["required"] == 1


def test_update_block_multiple_choice_saves_choices(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "multiple_choice")
    block_id = _get_block_id(app, assignment_id, "multiple_choice")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={
            "body": "What does range(5) return?",
            "points": "1",
            "choices": ["0-4", "1-5", "0-5", "Error"],
            "correct": "0",
        },
    )
    with app.app_context():
        from app.models import get_db

        choices = (
            get_db()
            .execute("SELECT * FROM block_choices WHERE block_id = ?", (block_id,))
            .fetchall()
        )
        assert len(choices) == 4
        correct = [c for c in choices if c["is_correct"]]
        assert len(correct) == 1
        assert correct[0]["body"] == "0-4"


def test_update_block_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "text")
    block_id = _get_block_id(app, assignment_id, "text")
    client = _make_enrolled_student(app, teacher_client, classroom)

    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={"body": "Hacked", "points": "0"},
    )
    assert response.status_code == 403


def test_update_block_not_found(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/99999/update",
        data={"body": "Test", "points": "1"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# deleting blocks
# ---------------------------------------------------------------------------


def test_delete_block(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "text")
    block_id = _get_block_id(app, assignment_id, "text")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/delete",
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT id FROM lesson_blocks WHERE id = ?", (block_id,))
            .fetchone()
        )
        assert row is None


def test_delete_block_removes_choices(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "true_false")
    block_id = _get_block_id(app, assignment_id, "true_false")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/delete",
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        choices = (
            get_db()
            .execute("SELECT * FROM block_choices WHERE block_id = ?", (block_id,))
            .fetchall()
        )
        assert len(choices) == 0


def test_delete_block_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "text")
    block_id = _get_block_id(app, assignment_id, "text")
    client = _make_enrolled_student(app, teacher_client, classroom)

    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/delete",
    )
    assert response.status_code == 403


def test_delete_block_not_found(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/99999/delete",
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# lesson submission
# ---------------------------------------------------------------------------


def test_submit_lesson_multiple_choice(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "multiple_choice")
    block_id = _get_block_id(app, assignment_id, "multiple_choice")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={
            "body": "What is 2+2?",
            "points": "1",
            "choices": ["3", "4", "5"],
            "correct": "1",
        },
    )

    with app.app_context():
        from app.models import get_db

        choice = (
            get_db()
            .execute(
                "SELECT id FROM block_choices WHERE block_id = ? AND is_correct = 1",
                (block_id,),
            )
            .fetchone()
        )
        correct_choice_id = choice["id"]

    client = _make_enrolled_student(app, teacher_client, classroom)
    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/lesson/submit",
        data={f"block_{block_id}": str(correct_choice_id)},
    )
    assert response.status_code == 302


def test_submit_lesson_auto_grades(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "multiple_choice")
    block_id = _get_block_id(app, assignment_id, "multiple_choice")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={
            "body": "What is 2+2?",
            "points": "2",
            "choices": ["3", "4", "5"],
            "correct": "1",
        },
    )

    with app.app_context():
        from app.models import get_db

        choice = (
            get_db()
            .execute(
                "SELECT id FROM block_choices WHERE block_id = ? AND is_correct = 1",
                (block_id,),
            )
            .fetchone()
        )
        correct_choice_id = choice["id"]

    client = _make_enrolled_student(app, teacher_client, classroom)
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/lesson/submit",
        data={f"block_{block_id}": str(correct_choice_id)},
    )

    with app.app_context():
        from app.models import get_db

        response = (
            get_db()
            .execute(
                "SELECT score FROM block_responses WHERE block_id = ?", (block_id,)
            )
            .fetchone()
        )
        assert response["score"] == 2


def test_submit_lesson_wrong_answer_scores_zero(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "multiple_choice")
    block_id = _get_block_id(app, assignment_id, "multiple_choice")

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/{block_id}/update",
        data={
            "body": "What is 2+2?",
            "points": "2",
            "choices": ["3", "4", "5"],
            "correct": "1",
        },
    )

    with app.app_context():
        from app.models import get_db

        wrong_choice = (
            get_db()
            .execute(
                "SELECT id FROM block_choices WHERE block_id = ? AND is_correct = 0 LIMIT 1",
                (block_id,),
            )
            .fetchone()
        )
        wrong_choice_id = wrong_choice["id"]

    client = _make_enrolled_student(app, teacher_client, classroom)
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/lesson/submit",
        data={f"block_{block_id}": str(wrong_choice_id)},
    )

    with app.app_context():
        from app.models import get_db

        response = (
            get_db()
            .execute(
                "SELECT score FROM block_responses WHERE block_id = ?", (block_id,)
            )
            .fetchone()
        )
        assert response["score"] == 0


def test_submit_lesson_short_answer_saves_body(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    _add_block(teacher_client, classroom, assignment_id, "short_answer")
    block_id = _get_block_id(app, assignment_id, "short_answer")

    client = _make_enrolled_student(app, teacher_client, classroom)
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/lesson/submit",
        data={f"block_{block_id}": "A loop repeats code."},
    )

    with app.app_context():
        from app.models import get_db

        response = (
            get_db()
            .execute("SELECT body FROM block_responses WHERE block_id = ?", (block_id,))
            .fetchone()
        )
        assert response["body"] == "A loop repeats code."


def test_submit_lesson_teacher_cannot_submit(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/lesson/submit",
        data={},
    )
    assert response.status_code == 403


def test_submit_lesson_unauthenticated(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/assignments/1/lesson/submit",
        data={},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# publish lesson
# ---------------------------------------------------------------------------


def test_publish_lesson_notifies_students(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)

    # ← add this — student must exist and be enrolled before publishing
    _make_enrolled_student(app, teacher_client, classroom)

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/publish",
        follow_redirects=True,
    )

    with app.app_context():
        from app.models import get_db
        from app.models.user import get_user_by_username

        student = get_user_by_username("lessonstu")
        notif = (
            get_db()
            .execute(
                "SELECT * FROM notifications WHERE user_id = ? AND type = 'assignment'",
                (student["id"],),
            )
            .fetchone()
        )
        assert notif is not None


def test_publish_lesson_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    client = _make_enrolled_student(app, teacher_client, classroom)
    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment_id}/blocks/publish",
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# lesson results
# ---------------------------------------------------------------------------


def test_lesson_results_teacher(teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    response = teacher_client.get(
        f"/classrooms/{classroom}/assignments/{assignment_id}/results"
    )
    assert response.status_code == 200


def test_lesson_results_non_teacher(app, teacher_client, classroom):
    assignment_id = _make_lesson(teacher_client, classroom)
    client = _make_enrolled_student(app, teacher_client, classroom)
    response = client.get(
        f"/classrooms/{classroom}/assignments/{assignment_id}/results"
    )
    assert response.status_code == 403


def test_lesson_results_invalid_assignment(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/99999/results")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# assignment fixture needs updating
# ---------------------------------------------------------------------------


def test_assignment_fixture_still_works(teacher_client, classroom, assignment):
    """Existing assignment fixture still loads correctly after lesson builder changes."""
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"Test Assignment" in response.data
