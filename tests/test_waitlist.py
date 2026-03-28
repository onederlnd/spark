from app.models import get_db


# --- route: thank-you page ---


def test_thankyou_page_loads(client):
    response = client.get("/waitlist/thank-you")
    assert response.status_code == 200


# --- route: POST /waitlist happy path ---


def test_waitlist_signup_redirects_to_thankyou(client):
    response = client.post(
        "/waitlist",
        data={"email": "newuser@example.com"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/waitlist/thank-you" in response.headers["Location"]


def test_waitlist_signup_follow_redirect(client):
    response = client.post(
        "/waitlist",
        data={"email": "newuser@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200


# --- db: row actually inserted ---


def test_waitlist_stores_email_in_db(client, app):
    client.post("/waitlist", data={"email": "stored@example.com"})
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM waitlist WHERE email = ?", ("stored@example.com",)
        ).fetchone()
    assert row is not None
    assert row["email"] == "stored@example.com"


def test_waitlist_email_stored_lowercase(client, app):
    client.post("/waitlist", data={"email": "UPPER@EXAMPLE.COM"})
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM waitlist WHERE email = ?", ("upper@example.com",)
        ).fetchone()
    assert row is not None


def test_waitlist_joined_at_is_populated(client, app):
    client.post("/waitlist", data={"email": "ts@example.com"})
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT joined_at FROM waitlist WHERE email = ?", ("ts@example.com",)
        ).fetchone()
    assert row is not None
    assert row["joined_at"] is not None


# --- validation: invalid email ---


def test_waitlist_rejects_missing_email(client):
    response = client.post(
        "/waitlist",
        data={"email": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid email" in response.data.lower()


def test_waitlist_rejects_email_without_at_sign(client):
    response = client.post(
        "/waitlist",
        data={"email": "notanemail"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid email" in response.data.lower()


# --- duplicate email handling ---


def test_waitlist_duplicate_email_still_redirects(client):
    client.post("/waitlist", data={"email": "dupe@example.com"})
    response = client.post(
        "/waitlist",
        data={"email": "dupe@example.com"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/waitlist/thank-you" in response.headers["Location"]


def test_waitlist_duplicate_email_not_inserted_twice(client, app):
    client.post("/waitlist", data={"email": "dupe2@example.com"})
    client.post("/waitlist", data={"email": "dupe2@example.com"})
    with app.app_context():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM waitlist WHERE email = ?", ("dupe2@example.com",)
        ).fetchall()
    assert len(rows) == 1
