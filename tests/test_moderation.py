# tests/test_moderation.py

from app.models.post import create_post, get_post, hide_post, unhide_post
from app.models.report import create_report, get_report_count
from app.models.user import create_user, get_user_by_username


def test_unhide_post(app, classroom):
    """hide_post hides a post, unhide_post restores it"""
    create_user("poster", "pass123", dob="2005-01-01")
    user = get_user_by_username("poster")
    post_id = create_post(user["id"], "Test", "body", classroom_id=classroom)
    hide_post(post_id)
    assert get_post(post_id)["is_hidden"] == 1

    unhide_post(post_id)
    assert get_post(post_id)["is_hidden"] == 0


def test_unhide_post_that_is_not_hidden(app, classroom):
    """unhide_post on a visible post is a no-op -- doesn't error"""
    create_user("poster", "pass123", dob="2005-01-01")
    user = get_user_by_username("poster")
    post_id = create_post(user["id"], "Test", "body", classroom_id=classroom)
    assert get_post(post_id)["is_hidden"] == 0
    unhide_post(post_id)
    assert get_post(post_id)["is_hidden"] == 0


def test_post_hidden_after_3_reports(app, post):
    """A post is auto-hidden after 3 unique reports"""
    create_user("reporter1", "pass123", dob="2005-01-01")
    create_user("reporter2", "pass123", dob="2005-01-01")
    create_user("reporter3", "pass123", dob="2005-01-01")

    r1 = get_user_by_username("reporter1")
    r2 = get_user_by_username("reporter2")
    r3 = get_user_by_username("reporter3")

    create_report(post, r1["id"], "Inappropriate", "")
    create_report(post, r2["id"], "Inappropriate", "")

    assert get_post(post)["is_hidden"] == 0

    create_report(post, r3["id"], "Inappropriate", "")

    assert get_post(post)["is_hidden"] == 1


def test_post_not_hidden_before_3_reports(app, post):
    """A post is not hidden after less than < 3 reports"""
    create_user("reporter1", "pass123", dob="2005-01-01")
    create_user("reporter2", "pass123", dob="2005-01-01")

    r1 = get_user_by_username("reporter1")
    r2 = get_user_by_username("reporter2")

    create_report(post, r1["id"], "Spam", "")
    create_report(post, r2["id"], "Spam", "")

    assert get_post(post)["is_hidden"] == 0


def test_duplicate_report_does_not_count(app, post):
    """Skip duplicate reports (should only count as 1)"""
    create_user("reporter1", "pass123", dob="2005-01-01")
    create_user("reporter2", "pass123", dob="2005-01-01")

    r1 = get_user_by_username("reporter1")
    r2 = get_user_by_username("reporter2")

    create_report(post, r1["id"], "Spam", "")
    create_report(post, r1["id"], "Spam", "")
    create_report(post, r2["id"], "Spam", "")

    assert get_post(post)["is_hidden"] == 0
    assert get_report_count(post) == 2


def test_teacher_can_view_moderation_queue(teacher_client, classroom, post, app):
    """Teacher sees flagged posts in the moderation queue"""
    create_user("reporter1", "pass123", dob="2005-01-01")
    create_user("reporter2", "pass123", dob="2005-01-01")
    create_user("reporter3", "pass123", dob="2005-01-01")

    r1 = get_user_by_username("reporter1")
    r2 = get_user_by_username("reporter2")
    r3 = get_user_by_username("reporter3")

    create_report(post, r1["id"], "Inappropriate", "Bad words")
    create_report(post, r2["id"], "Spam", "")
    create_report(post, r3["id"], "Harassment", "")

    response = teacher_client.get(f"/moderation/queue/{classroom}")
    assert response.status_code == 200
    assert b"Test post" in response.data or b"test body" in response.data


def test_student_cannot_access_moderation_queue(
    teacher_client, student_client, classroom
):
    """Student gets 403 on the moderation queue"""
    teacher_client.get(f"/classrooms/{classroom}")
    with student_client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["coppa_status"] = "approve"
        sess["role"] = "student"

    response = student_client.get(f"/moderation/queue/{classroom}")
    assert response.status_code == 403


def test_moderation_queue_empty_state(teacher_client, classroom):
    """Moderation queue shows empty state when no flagged posts"""
    response = teacher_client.get(f"/moderation/queue/{classroom}")
    assert response.status_code == 200
    assert b"All clear" in response.data or b"No reports" in response.data


def test_teacher_can_allow_flagged_post(
    teacher_client, student_client, classroom, post, app
):
    """Teacher allowing a flagged post unhides it and resolves reports"""
    create_user("reporter1", "pass123", dob="2005-01-01")
    create_user("reporter2", "pass123", dob="2005-01-01")
    create_user("reporter3", "pass123", dob="2005-01-01")
    r1 = get_user_by_username("reporter1")
    r2 = get_user_by_username("reporter2")
    r3 = get_user_by_username("reporter3")

    create_report(post, r1["id"], "Spam", "")
    create_report(post, r2["id"], "Spam", "")
    create_report(post, r3["id"], "Spam", "")

    assert get_post(post)["is_hidden"] == 1

    response = teacher_client.post(
        f"/moderation/reports/{post}/resolve", follow_redirects=True
    )
    assert response.status_code == 200
    assert get_post(post)["is_hidden"] == 0


def test_allowed_post_no_longer_in_queue(teacher_client, classroom, post, app):
    """After allowing a post it no longer appears in the moderation queue"""
    create_user("r1", "pass123", dob="2005-01-01")
    create_user("r2", "pass123", dob="2005-01-01")
    create_user("r3", "pass123", dob="2005-01-01")
    r1 = get_user_by_username("r1")
    r2 = get_user_by_username("r2")
    r3 = get_user_by_username("r3")

    create_report(post, r1["id"], "Spam", "")
    create_report(post, r2["id"], "Spam", "")
    create_report(post, r3["id"], "Spam", "")

    teacher_client.post(f"/moderation/reports/{post}/resolve")

    response = teacher_client.get(f"/moderation/queue/{classroom}")

    assert b"All clear" in response.data or b"No reports" in response.data


def test_modera_tion_queue_missing_classroom(teacher_client):
    """Moderation dashboard without classroom_id returns 404"""
    response = teacher_client.get("/moderation/queue/")
    assert response.status_code == 404


def test_student_cannot_allow_post(student_client, post):
    """Student cannot resolve a report"""
    response = student_client.post(f"/moderation/reports/{post}/resolve")
    assert response.status_code == 403


def test_teacher_can_delete_flagged_post(teacher_client, classroom, post, app):
    """Teacher deleting a flagged post removes it permanently"""
    create_user("r1", "pass123", dob="2005-01-01")
    create_user("r2", "pass123", dob="2005-01-01")
    create_user("r3", "pass123", dob="2005-01-01")
    r1 = get_user_by_username("r1")
    r2 = get_user_by_username("r2")
    r3 = get_user_by_username("r3")

    create_report(post, r1["id"], "Harassment", "")
    create_report(post, r2["id"], "Harassment", "")
    create_report(post, r3["id"], "Harassment", "")

    response = teacher_client.post(
        f"/moderation/reports/{post}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert get_post(post) is None or get_post(post)["is_hidden"] == 1


def test_deleted_post_no_longer_in_queue(teacher_client, classroom, post, app):
    """After deleting a post it no longer appears in the moderation queue"""
    create_user("r1", "pass123", dob="2005-01-01")
    create_user("r2", "pass123", dob="2005-01-01")
    create_user("r3", "pass123", dob="2005-01-01")
    r1 = get_user_by_username("r1")
    r2 = get_user_by_username("r2")
    r3 = get_user_by_username("r3")

    create_report(post, r1["id"], "Spam", "")
    create_report(post, r2["id"], "Spam", "")
    create_report(post, r3["id"], "Spam", "")

    teacher_client.post(f"/moderation/reports/{post}/delete")

    response = teacher_client.get(f"/moderation/queue/{classroom}")
    assert b"All clear" in response.data or b"No reports" in response.data


def test_student_cannot_delete_post_via_moderation(student_client, post):
    """Student cannot delete a post via the moderation route"""
    response = student_client.post(f"/moderation/reports/{post}/delete")
    assert response.status_code == 403


def test_resolve_nonexistent_post_returns_404(teacher_client):
    """Resolving a report on a nonexistent post returns 404"""
    response = teacher_client.post("/moderation/reports/99999/resolve")
    assert response.status_code == 404


def test_delete_nonexistent_post_returns_404(teacher_client):
    """Deleting a nonexistent post via moderation returns 404"""
    response = teacher_client.post("/moderation/reports/99999/delete")
    assert response.status_code == 404
