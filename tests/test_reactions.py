from app.models.reactions import get_reaction, get_reaction_counts
from app.models import get_db

# --- route: react ---


def test_react_happy_path(auth_client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user0", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user0",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Happy Path Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    response = auth_client.post(
        f"/posts/{post_id}/react",
        data={"reaction": "lit"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_react_stores_reaction(auth_client, app):
    with app.app_context():
        db = get_db()
        # create a second user's post to react to
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Test Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    auth_client.post(
        f"/posts/{post_id}/react",
        data={"reaction": "love"},
    )

    with app.app_context():
        user_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", ("testuser",))
            .fetchone()["id"]
        )
        result = get_reaction(post_id, user_id)
    assert result == "love"


def test_react_toggle_off(auth_client, app):
    """Tapping same reaction twice removes it."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user2", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user2",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Toggle Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "lit"})
    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "lit"})

    with app.app_context():
        user_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", ("testuser",))
            .fetchone()["id"]
        )
        result = get_reaction(post_id, user_id)
    assert result is None


def test_react_swap_reaction(auth_client, app):
    """Tapping a different reaction replaces the first."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user3", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user3",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Swap Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "lit"})
    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "thinking"})

    with app.app_context():
        user_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", ("testuser",))
            .fetchone()["id"]
        )
        result = get_reaction(post_id, user_id)
    assert result == "thinking"


def test_invalid_reaction_rejected(auth_client, app):
    """Invalid reaction string is ignored."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user4", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user4",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Invalid React Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "downvote"})

    with app.app_context():
        user_id = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", ("testuser",))
            .fetchone()["id"]
        )
        result = get_reaction(post_id, user_id)
    assert result is None


# --- reaction counts for teacher dashboard ---


def test_reaction_counts_correct(auth_client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user5", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user5",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Count Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]

    auth_client.post(f"/posts/{post_id}/react", data={"reaction": "love"})

    with app.app_context():
        counts = get_reaction_counts(post_id)
    assert counts["love"] == 1
    assert counts["idea"] == 0
    assert counts["thinking"] == 0
    assert counts["nailed_it"] == 0
    assert counts["lit"] == 0
    assert counts["star"] == 0
    assert counts["fire"] == 0


def test_reaction_counts_empty_post(app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("other.user6", "x", "student"),
        )
        db.commit()
        other_id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("other.user6",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO posts (user_id, title, body, classroom_id) VALUES (?,?,?,?)",
            (other_id, "Empty Count Post", "body", None),
        )
        db.commit()
        post_id = db.execute(
            "SELECT id FROM posts WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]
        counts = get_reaction_counts(post_id)
    assert all(v == 0 for v in counts.values())
