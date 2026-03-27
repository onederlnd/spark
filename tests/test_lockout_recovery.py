# tests/test_lockout_recovery.py

from app.utils.brute_force import (
    record_failure,
    is_locked_out,
    unlock_user,
    _lockouts,
    _failed_attempts,
)


# --- helpers


def _register_and_login(client, username, role="student", dob="2008-01-01"):
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


def _create_classroom(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={
            "name": "Test Class",
            "description": "",
        },
        follow_redirects=False,
    )
    # extract classroom_id from redirect
    location = response.headers["Location"]
    classroom_id = int(location.rstrip("/").split("/")[-1])
    return classroom_id


def _enroll_student(teacher_client, student_client, classroom_id):
    from app.models.classroom import get_classroom

    classroom = get_classroom(classroom_id)
    student_client.post("/classrooms/join", data={"join_code": classroom["join_code"]})


# --- unlock_user unit tests


def test_unlock_clears_lockout():
    record_failure("lockedkid", "1.2.3.4")
    _lockouts["user:lockedkid"] = 9999999999  # force locked
    locked, _ = is_locked_out("lockedkid", "1.2.3.4")
    assert locked is True
    unlock_user("lockedkid")
    locked, _ = is_locked_out("lockedkid", "1.2.3.4")
    assert locked is False


def test_unlock_clears_failed_attempts():
    record_failure("attemptskid", "1.2.3.4")
    unlock_user("attemptskid")
    assert _failed_attempts["user:attemptskid"] == []


def test_unlock_nonexistent_user_does_not_error():
    unlock_user("ghostuser")  # should not raise


def test_unlock_idempotent():
    _lockouts["user:doublekid"] = 9999999999
    unlock_user("doublekid")
    unlock_user("doublekid")  # second call should not raise
    locked, _ = is_locked_out("doublekid", "")
    assert locked is False


# --- unlock route tests


def test_unlock_route_returns_302(app):
    # --- teacher setup
    with app.test_client() as teacher_client:
        _register_and_login(
            teacher_client, "unlockteacher", role="teacher", dob="1990-01-01"
        )
        classroom_id = _create_classroom(teacher_client)

    # --- student setup (separate client)
    with app.test_client() as student_client:
        _register_and_login(student_client, "lockedstudent")
        _enroll_student(teacher_client, student_client, classroom_id)

    from app.models.user import get_user_by_username

    student = get_user_by_username("lockedstudent")
    _lockouts["user:lockedstudent"] = 9999999999

    # --- teacher performs unlock (new clean context)
    with app.test_client() as teacher_client:
        _register_and_login(
            teacher_client, "unlockteacher", role="teacher", dob="1990-01-01"
        )

        response = teacher_client.post(
            f"/classrooms/{classroom_id}/students/{student['id']}/unlock"
        )
        assert response.status_code == 302


def test_unlock_route_clears_lockout(app):
    with app.test_client() as teacher_client:
        _register_and_login(
            teacher_client, "unlockteacher2", role="teacher", dob="1990-01-01"
        )
        classroom_id = _create_classroom(teacher_client)

    with app.test_client() as student_client:
        _register_and_login(student_client, "lockedstudent2")
        _enroll_student(teacher_client, student_client, classroom_id)
        from app.models.user import get_user_by_username

        student = get_user_by_username("lockedstudent2")
        _lockouts["user:lockedstudent2"] = 9999999999
        teacher_client.post(
            f"/classrooms/{classroom_id}/students/{student['id']}/unlock"
        )
        locked, _ = is_locked_out("lockedstudent2", "")
        assert locked is False


def test_unlock_route_requires_login(client):
    response = client.post("/classrooms/1/students/1/unlock")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_student_cannot_unlock(app):
    with app.test_client() as student_client:
        _register_and_login(student_client, "sneakystudent")
        response = student_client.post("/classrooms/1/students/1/unlock")
        assert response.status_code in (302, 403)


def test_unlock_nonmember_student_returns_404(app):
    with app.test_client() as teacher_client:
        _register_and_login(
            teacher_client, "unlockteacher3", role="teacher", dob="1990-01-01"
        )
        classroom_id = _create_classroom(teacher_client)
        response = teacher_client.post(
            f"/classrooms/{classroom_id}/students/99999/unlock"
        )
        assert response.status_code == 404
