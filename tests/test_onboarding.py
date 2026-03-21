# tests/test_onboarding.py

# tests/test_onboarding.py


def _register_teacher(client, username="newteacher"):
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": "pass123",
            "bio": "test teacher",
            "role": "teacher",
            "dob": "2000-01-01",
        },
    )
    client.post("/auth/login", data={"username": username, "password": "pass123"})
    return client


# --- modal visibility


def test_onboarding_modal_shown_on_first_login(app):
    client = app.test_client()
    _register_teacher(client)
    response = client.get("/classrooms/")
    assert b"Welcome to SparK Classrooms" in response.data


def test_onboarding_modal_not_shown_to_student(student_client):
    response = student_client.get("/classrooms/")
    assert b"Welcome to SparK Classrooms" not in response.data


def test_onboarding_modal_not_shown_after_dismissal(app):
    client = app.test_client()
    _register_teacher(client)

    # dismiss the modal
    client.post("/classrooms/onboarding/complete")

    response = client.get("/classrooms/")
    assert b"Welcome to SparK Classrooms" not in response.data


def test_onboarding_modal_not_shown_to_existing_teacher(teacher_client):
    # teacher_client fixture already went through registration
    # mark them as onboarded first
    teacher_client.post("/classrooms/onboarding/complete")

    response = teacher_client.get("/classrooms/")
    assert b"Welcome to SparK Classrooms" not in response.data


# --- complete onboarding endpoint


def test_complete_onboarding_returns_204(app):
    client = app.test_client()
    _register_teacher(client)
    response = client.post("/classrooms/onboarding/complete")
    assert response.status_code == 204


def test_complete_onboarding_requires_login(client):
    response = client.post("/classrooms/onboarding/complete")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_complete_onboarding_idempotent(app):
    """Calling complete twice should not error"""
    client = app.test_client()
    _register_teacher(client)
    client.post("/classrooms/onboarding/complete")
    response = client.post("/classrooms/onboarding/complete")
    assert response.status_code == 204


# --- db flag


def test_onboarded_flag_set_after_completion(app):
    from app.models.user import get_user_by_username

    client = app.test_client()
    _register_teacher(client, username="flagteacher")

    user = get_user_by_username("flagteacher")
    assert user["onboarded"] == 0

    client.post("/classrooms/onboarding/complete")

    user = get_user_by_username("flagteacher")
    assert user["onboarded"] == 1


def test_onboarded_flag_default_is_zero(app):
    from app.models.user import get_user_by_username

    client = app.test_client()
    _register_teacher(client, username="freshteacher")

    user = get_user_by_username("freshteacher")
    assert user["onboarded"] == 0


def test_student_onboarded_flag_default_is_zero(app):
    from app.models.user import get_user_by_username

    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "freshstudent",
            "password": "pass123",
            "bio": "",
            "dob": "2008-01-01",
        },
    )
    user = get_user_by_username("freshstudent")
    assert user["onboarded"] == 0
