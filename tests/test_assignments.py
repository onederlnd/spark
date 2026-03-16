# tests/test_assignments.py


# --- create assignment
def test_create_assignment(teacher_client, classroom, assignment):
    """Assignment fixture created — teacher can view it."""
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"Test Assignment" in response.data


def test_create_assignment_non_teacher(auth_client, classroom):
    """Student cannot create an assignment."""
    response = auth_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "Sneaky Assignment", "instructions": "Do this.", "due_date": ""},
    )
    assert response.status_code == 403


def test_create_assignment_invalid_classroom(teacher_client):
    response = teacher_client.post(
        "/classrooms/99999/assignments/new",
        data={"title": "Test", "instructions": "Instructions.", "due_date": ""},
    )
    assert response.status_code == 404


def test_create_assignment_missing_title(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "", "instructions": "Do something.", "due_date": ""},
    )
    assert response.status_code == 200
    assert b"required" in response.data.lower()


def test_create_assignment_missing_instructions(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "Empty Instructions", "instructions": "", "due_date": ""},
    )
    assert response.status_code == 200
    assert b"required" in response.data.lower()


def test_create_assignment_unauthenticated(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={"title": "Test", "instructions": "Instructions.", "due_date": ""},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- get assignment
def test_get_assignment(teacher_client, classroom, assignment):
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"Test Assignment" in response.data


def test_get_assignment_not_found(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/99999")
    assert response.status_code == 404


def test_get_assignment_not_in_classroom(teacher_client, classroom, assignment):
    """Assignment ID that exists but belongs to a different classroom returns 404."""
    response = teacher_client.get(f"/classrooms/99999/assignments/{assignment}")
    assert response.status_code == 404


def test_get_assignment_unauthenticated(client, classroom, assignment):
    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- list assignments
def test_get_assignments_for_classroom(teacher_client, classroom, assignment):
    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 200
    assert b"Test Assignment" in response.data


def test_get_assignments_invalid_classroom(teacher_client):
    response = teacher_client.get("/classrooms/99999/")
    assert response.status_code == 404


def test_get_assignments_not_member(auth_client, classroom):
    response = auth_client.get(f"/classrooms/{classroom}/")
    assert response.status_code == 403


# --- submissions
def test_create_submission(app, teacher_client, classroom, assignment):
    """Student who has joined can submit work."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "submitter",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "submitter", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer is 42."},
    )
    assert response.status_code == 302


def test_create_submission_not_student(teacher_client, classroom, assignment):
    """Teacher cannot submit to their own assignment."""
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Teacher sneaking a submission."},
    )
    assert response.status_code == 403


def test_create_submission_assignment_not_found(app, teacher_client, classroom):
    """Submitting to a non-existent assignment returns 404."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "sub2",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "sub2", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.post(
        f"/classrooms/{classroom}/assignments/99999",
        data={"body": "My answer."},
    )
    assert response.status_code == 404


def test_create_submission_empty_body(app, teacher_client, classroom, assignment):
    """Empty submission body is rejected."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "sub3",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "sub3", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": ""},
    )
    assert response.status_code == 200
    assert b"empty" in response.data.lower()


def test_create_submission_duplicate(app, teacher_client, classroom, assignment):
    """Resubmitting updates the existing submission, doesn't create a duplicate."""
    from app.models.classroom import get_classroom, get_submission

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "resub",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "resub", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "First answer."},
    )
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Updated answer."},
    )

    with app.app_context():
        from app.models.user import get_user_by_username

        user = get_user_by_username("resub")
        sub = get_submission(assignment, user["id"])
        assert sub["body"] == "Updated answer."


def test_create_submission_unauthenticated(client, classroom, assignment):
    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "Answer."},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- get submission


def test_get_submission(app, teacher_client, classroom, assignment):
    """Student's submission appears on the assignment page after submitting."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "viewer",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "viewer", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}", data={"body": "My answer."}
    )

    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"My answer." in response.data


def test_get_submission_not_found(app, teacher_client, classroom, assignment):
    """Student who hasn't submitted sees the submit form, not a submission."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "nosub",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "nosub", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"Submit Your Work" in response.data


def test_get_submission_unauthenticated(client, classroom, assignment):
    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- teacher submission list


def test_get_submissions_for_assignment(app, teacher_client, classroom, assignment):
    """Teacher sees submission count badge after a student submits."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "ts1",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "ts1", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}", data={"body": "Done."}
    )

    response = teacher_client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert response.status_code == 200
    assert b"Grade Submissions" in response.data


def test_get_submissions_for_assignment_not_teacher(app, classroom, assignment):
    """Student does not see the Grade Submissions button."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "ts2",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "ts2", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}")
    assert b"Grade Submissions" not in response.data


def test_get_submissions_for_assignment_invalid(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/assignments/99999")
    assert response.status_code == 404


# --- grade grid


def test_get_submission_grid(teacher_client, classroom, assignment):
    response = teacher_client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/grade"
    )
    assert response.status_code == 200


def test_get_submission_grid_not_teacher(app, teacher_client, classroom, assignment):
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "grid1",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "grid1", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})

    response = client.get(f"/classrooms/{classroom}/assignments/{assignment}/grade")
    assert response.status_code == 403


def test_get_submission_grid_invalid_classroom(teacher_client, assignment):
    response = teacher_client.get(f"/classrooms/99999/assignments/{assignment}/grade")
    assert response.status_code == 404


# --- grading


def test_save_grade(app, teacher_client, classroom, assignment):
    """Teacher can save a grade for a submitted assignment."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "gradee",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "gradee", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}", data={"body": "My work."}
    )

    with app.app_context():
        from app.models.user import get_user_by_username

        student = get_user_by_username("gradee")
        student_id = student["id"]

    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A+", "feedback": "Excellent work!"},
    )
    assert response.status_code == 302


def test_save_grade_non_teacher(app, teacher_client, classroom, assignment):
    """Student cannot grade a submission."""
    from app.models.classroom import get_classroom

    with app.app_context():
        row = get_classroom(classroom)
        join_code = row["join_code"]

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "grader2",
            "password": "pass123",
            "role": "student",
            "dob": "2010-05-21",
        },
    )
    client.post("/auth/login", data={"username": "grader2", "password": "pass123"})
    client.post("/classrooms/join", data={"join_code": join_code})
    client.post(
        f"/classrooms/{classroom}/assignments/{assignment}", data={"body": "My work."}
    )

    with app.app_context():
        from app.models.user import get_user_by_username

        student = get_user_by_username("grader2")
        student_id = student["id"]

    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/{student_id}",
        data={"grade": "A", "feedback": ""},
    )
    assert response.status_code == 403


def test_save_grade_invalid_submission(teacher_client, classroom, assignment):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/99999",
        data={"grade": "B", "feedback": ""},
    )
    assert response.status_code == 404


def test_save_grade_unauthenticated(client, classroom, assignment):
    response = client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/1",
        data={"grade": "A", "feedback": ""},
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
