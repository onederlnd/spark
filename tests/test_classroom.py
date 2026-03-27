# tests/test_classroom.py


# --- join code generation (implicit in classroom creation)


def test_generate_join_code(teacher_client, classroom):
    """Classroom creation generates a visible join code on the classroom page."""
    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 200
    assert b"Join Code" in response.data


def test_generate_join_code_unauthenticated(client, classroom):
    response = client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_generate_join_code_non_teacher(auth_client):
    """Student cannot create a classroom (so no join code generated for them)."""
    response = auth_client.post(
        "/classrooms/new",
        data={"name": "Non Teacher Classroom"},
    )
    assert response.status_code == 403


def test_generate_join_code_invalid_classroom(teacher_client):
    response = teacher_client.get("/classrooms/99999/")
    assert response.status_code == 404


# --- create classroom


def test_create_classroom(teacher_client, classroom):
    """Classroom fixture created successfully — teacher can view it."""
    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 200


def test_create_classroom_missing_name(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": "", "description": "Missing name classroom"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_create_classroom_empty_name(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": "", "description": "Classroom emptyj name"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_create_classroom_invalid_payload(teacher_client):
    """POST with no data at all should show an error, not crash."""
    response = teacher_client.post("/classrooms/new", data={})
    assert response.status_code == 200
    assert b"required" in response.data


# --- get classroom


def test_get_classroom(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}")
    assert response.status_code == 200
    assert b"Join Code" in response.data


def test_get_classroom_not_found(teacher_client):
    response = teacher_client.get("/classrooms/99999/")
    assert response.status_code == 404


def test_get_classroom_invalid_id(teacher_client):
    response = teacher_client.get("/classrooms/abc/")
    assert response.status_code == 404


def test_get_classroom_unauthenticated(client, classroom):
    response = client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- join code lookup


def test_get_classroom_join_code(teacher_client, classroom):
    """Join code is visible to the teacher on their classroom page."""
    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 200
    assert b"Join Code" in response.data


def test_get_classroom_join_code_unauthorized(auth_client, classroom):
    """Student who is not a member cannot see the classroom at all."""
    response = auth_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 403


def test_get_classroom_join_code_invalid_classroom(teacher_client):
    response = teacher_client.get("/classrooms/99999/")
    assert response.status_code == 404


# --- list user classrooms


def test_get_classrooms_for_user(teacher_client, classroom):
    response = teacher_client.get("/classrooms/")
    assert response.status_code == 200
    assert b"Test Classroom" in response.data


def test_get_classrooms_for_user_empty(app):
    """A brand new user with no classrooms sees the empty state."""
    cursor = app.test_client()
    cursor.post(
        "/auth/register",
        data={
            "username": "newteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "2010-05-21",
        },
    )
    cursor.post("/auth/login", data={"username": "newteacher", "password": "pass123"})
    response = cursor.get("/classrooms/")
    assert response.status_code == 200
    assert b"classrooms" in response.data.lower()


def test_get_classrooms_for_user_unauthenticated(client):
    response = client.get("/classrooms/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- members


def test_get_classroom_members(teacher_client, classroom):
    """Teacher is listed as a member of their own classroom."""
    response = teacher_client.get(f"/classrooms/{classroom}")
    assert response.status_code == 200
    assert b"teacher" in response.data.lower()


def test_get_classroom_members_not_member(auth_client, classroom):
    """Student who hasn't joined cannot view the classroom."""
    response = auth_client.get(f"/classrooms/{classroom}")
    assert response.status_code == 403


def test_get_classroom_members_invalid_classroom(teacher_client):
    response = teacher_client.get("/classrooms/99999")
    assert response.status_code == 404


# --- member role


def test_get_member_role(teacher_client, classroom):
    """Teacher's role is shown correctly in their classroom."""
    response = teacher_client.get(f"/classrooms/{classroom}")
    assert response.status_code == 200
    assert b"teacher" in response.data.lower()


def test_get_member_role_not_member(auth_client, classroom):
    response = auth_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 403


def test_get_member_role_invalid_classroom(teacher_client):
    response = teacher_client.get("/classrooms/99999/")
    assert response.status_code == 404


# --- join classroom


def test_join_classroom(app, teacher_client, classroom):
    """Student can join a classroom with a valid join code."""
    # get the join code from the DB directly
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    cursor = app.test_client()
    cursor.post(
        "/auth/register",
        data={
            "username": "joiner",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    cursor.post("/auth/login", data={"username": "joiner", "password": "pass123"})

    response = cursor.post("/classrooms/join", data={"join_code": join_code})
    assert response.status_code == 302
    assert f"/classrooms/{classroom}" in response.headers["Location"]


def test_join_classroom_invalid_code(auth_client):
    response = auth_client.post("/classrooms/join", data={"join_code": "XXXXXX"})
    assert response.status_code == 302
    assert b"Invalid" in auth_client.get("/classrooms/").data


def test_join_classroom_already_member(app, teacher_client, classroom):
    """Joining twice is safe — shows already-member message."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    response = teacher_client.post("/classrooms/join", data={"join_code": join_code})
    assert response.status_code == 302
    assert f"/classrooms/{classroom}" in response.headers["Location"]


def test_join_classroom_missing_code(auth_client):
    response = auth_client.post("/classrooms/join", data={"join_code": ""})
    assert response.status_code == 302
    # should flash an error and redirect to dashboard
    assert "/classrooms/" in response.headers["Location"]


def test_join_classroom_unauthenticated(client, app, teacher_client, classroom):
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    response = client.post("/classrooms/join", data={"join_code": join_code})
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# tests/test_submission_confirmation.py


def _enroll_student(app, classroom_id):
    """Helper — enroll student1 in a classroom and return their user_id."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        student_id = student["id"]
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom_id, student_id),
        )
        db.commit()
    return student_id


# --- happy path ---


def test_submission_confirmation_flash(app, student_client, classroom, assignment):
    """Successful submission shows a confirmation flash message."""
    _enroll_student(app, classroom)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"has been saved" in response.data


def test_submission_confirmation_includes_assignment_title(
    app, student_client, classroom, assignment
):
    """The confirmation message includes the assignment title."""
    _enroll_student(app, classroom)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
        follow_redirects=True,
    )

    assert b"Test Assignment" in response.data


def test_submission_confirmation_no_error_flash(
    app, student_client, classroom, assignment
):
    """A clean submission does not show an error flash."""
    _enroll_student(app, classroom)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
        follow_redirects=True,
    )

    assert b"has been saved" in response.data
    assert b"Something went wrong" not in response.data


# --- redirect behaviour ---


def test_submission_redirects_back_to_assignment(
    app, student_client, classroom, assignment
):
    """After submitting, the student is redirected back to the assignment page."""
    _enroll_student(app, classroom)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )

    assert response.status_code == 302
    assert (
        f"/classrooms/{classroom}/assignments/{assignment}"
        in response.headers["Location"]
    )


# --- empty submission ---


def test_empty_submission_shows_error(app, student_client, classroom, assignment):
    """Submitting an empty body does not show a confirmation and returns an error."""
    _enroll_student(app, classroom)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": ""},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"has been saved" not in response.data
    assert b"empty" in response.data or b"required" in response.data.lower()


# --- teacher cannot submit ---


def test_teacher_cannot_submit(teacher_client, classroom, assignment):
    """Teachers posting to the submission endpoint are forbidden."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Teacher trying to submit"},
    )

    assert response.status_code == 403


# --- submission is persisted ---


def test_submission_saved_to_db(app, student_client, classroom, assignment):
    """After a confirmed submission, the record exists in the database."""
    student_id = _enroll_student(app, classroom)

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Persisted answer"},
    )

    with app.app_context():
        from app.models.classroom import get_submission

        submission = get_submission(assignment, student_id)
        assert submission is not None
        assert "Persisted answer" in submission["body"]
