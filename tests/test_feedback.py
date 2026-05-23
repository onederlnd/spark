# tests/test_feedback.py

import pytest
from app.models.feedback import submit_feedback, get_all_feedback, get_feedback_summary


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "classroom_experience": 5,
    "student_engagement": 4,
    "ease_of_use": 3,
    "assignment_workflow": 4,
    "safety_moderation": 5,
    "open_suggestions": "Great platform!",
    "page_url": "/feed",
    "page_context": "Home Feed",
}

REQUIRED_FIELDS = [
    "classroom_experience",
    "student_engagement",
    "ease_of_use",
    "assignment_workflow",
    "safety_moderation",
]


def post_feedback(client, payload):
    return client.post(
        "/feedback/submit",
        json=payload,
        content_type="application/json",
    )


def _make_user(app):
    """Insert a minimal user and return their id."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("modeluser", "hash", "teacher"),
        )
        db.commit()
        return db.execute(
            "SELECT id FROM users WHERE username = 'modeluser'"
        ).fetchone()["id"]


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------


def test_feedback_unauthenticated_blocked(client):
    res = post_feedback(client, VALID_PAYLOAD)
    assert res.status_code in (401, 403, 302)


def test_feedback_student_blocked(student_client):
    res = post_feedback(student_client, VALID_PAYLOAD)
    assert res.status_code == 403


def test_feedback_teacher_allowed(teacher_client):
    res = post_feedback(teacher_client, VALID_PAYLOAD)
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_feedback_returns_ok(teacher_client):
    res = post_feedback(teacher_client, VALID_PAYLOAD)
    assert res.status_code == 200
    assert res.get_json() == {"ok": True}


def test_feedback_persisted_to_db(app, teacher_client):
    post_feedback(teacher_client, VALID_PAYLOAD)
    with app.app_context():
        rows = get_all_feedback()
    assert len(rows) == 1
    row = rows[0]
    assert row["classroom_experience"] == 5
    assert row["student_engagement"] == 4
    assert row["ease_of_use"] == 3
    assert row["assignment_workflow"] == 4
    assert row["safety_moderation"] == 5
    assert row["open_suggestions"] == "Great platform!"


def test_feedback_optional_fields_default_gracefully(teacher_client):
    payload = {**VALID_PAYLOAD}
    payload.pop("open_suggestions", None)
    payload.pop("page_url", None)
    payload.pop("page_context", None)
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 200


def test_feedback_summary_averages_correct(app, teacher_client):
    post_feedback(teacher_client, VALID_PAYLOAD)
    with app.app_context():
        summary = get_feedback_summary()
    assert summary["total"] == 1
    assert summary["avg_classroom"] == 5.0
    assert summary["avg_engagement"] == 4.0


# ---------------------------------------------------------------------------
# missing fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_field", REQUIRED_FIELDS)
def test_feedback_missing_required_field(teacher_client, missing_field):
    payload = {**VALID_PAYLOAD}
    del payload[missing_field]
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert missing_field in data["error"]


def test_feedback_no_body_returns_400(teacher_client):
    res = teacher_client.post(
        "/feedback/submit",
        content_type="application/json",
        data="",
    )
    assert res.status_code == 400


def test_feedback_empty_json_returns_400(teacher_client):
    res = post_feedback(teacher_client, {})
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# invalid ratings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [0, 6, -1, 100])
def test_feedback_out_of_range_rejected(teacher_client, bad_value):
    payload = {**VALID_PAYLOAD, "classroom_experience": bad_value}
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 400
    assert "error" in res.get_json()


@pytest.mark.parametrize("bad_value", ["five", None, "", [], {}])
def test_feedback_non_integer_rejected(teacher_client, bad_value):
    payload = {**VALID_PAYLOAD, "ease_of_use": bad_value}
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 400
    assert "error" in res.get_json()


@pytest.mark.parametrize("good_value", [1, 2, 3, 4, 5])
def test_feedback_boundary_values_accepted(teacher_client, good_value):
    payload = {**VALID_PAYLOAD, "classroom_experience": good_value}
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 200


def test_feedback_float_coerces_or_rejects(teacher_client):
    # 3.7 → int(3.7) = 3, which is valid — route casts with int()
    payload = {**VALID_PAYLOAD, "classroom_experience": 3.7}
    res = post_feedback(teacher_client, payload)
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# rate limiting
# ---------------------------------------------------------------------------


def test_feedback_rate_limit_enforced(teacher_client):
    for _ in range(10):
        res = post_feedback(teacher_client, VALID_PAYLOAD)
        assert res.status_code == 200
    res = post_feedback(teacher_client, VALID_PAYLOAD)
    assert res.status_code == 429


def test_feedback_rate_limit_resets_between_tests(teacher_client):
    res = post_feedback(teacher_client, VALID_PAYLOAD)
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# model unit tests
# ---------------------------------------------------------------------------


def test_feedback_model_submit_and_retrieve(app):
    user_id = _make_user(app)
    with app.app_context():
        submit_feedback(
            user_id=user_id,
            page_url="/test",
            page_context="Test Page",
            classroom_experience=5,
            student_engagement=4,
            ease_of_use=3,
            assignment_workflow=4,
            safety_moderation=5,
            open_suggestions="Good stuff",
        )
        rows = get_all_feedback()
    assert len(rows) == 1
    assert rows[0]["classroom_experience"] == 5
    assert rows[0]["open_suggestions"] == "Good stuff"


def test_feedback_model_multiple_submissions_ordered_newest_first(app):
    user_id = _make_user(app)
    with app.app_context():
        for rating in [2, 4]:
            submit_feedback(
                user_id=user_id,
                page_url="/",
                page_context="",
                classroom_experience=rating,
                student_engagement=rating,
                ease_of_use=rating,
                assignment_workflow=rating,
                safety_moderation=rating,
                open_suggestions="",
            )
        rows = get_all_feedback()
    assert rows[0]["classroom_experience"] == 4
    assert rows[1]["classroom_experience"] == 2


def test_feedback_model_summary_empty_db(app):
    with app.app_context():
        summary = get_feedback_summary()
    assert summary["total"] == 0


def test_feedback_model_summary_averages_multiple(app):
    user_id = _make_user(app)
    with app.app_context():
        for rating in [2, 4]:
            submit_feedback(
                user_id=user_id,
                page_url="/",
                page_context="",
                classroom_experience=rating,
                student_engagement=rating,
                ease_of_use=rating,
                assignment_workflow=rating,
                safety_moderation=rating,
                open_suggestions="",
            )
        summary = get_feedback_summary()
    assert summary["total"] == 2
    assert summary["avg_classroom"] == 3.0


def test_feedback_model_open_suggestions_stripped(app, teacher_client):
    payload = {**VALID_PAYLOAD, "open_suggestions": "  needs work  "}
    post_feedback(teacher_client, payload)
    with app.app_context():
        rows = get_all_feedback()
    assert rows[0]["open_suggestions"] == "needs work"
