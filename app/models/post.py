# app/models/post.py

from app.models import get_db


# --- feed
def get_feed(limit=50, topic_id=None):
    db = get_db()
    if topic_id:
        return db.execute(
            """
            SELECT posts.*, users.username, topics.name as topic_name
                          FROM posts
                          JOIN users ON posts.user_id = user_id
                          LEFT JOIN topics ON posts.topic_id = topics.id
                          WHERE posts.parent_id IS NULL
                          AND posts.topic_id = ?
                          ORDER BY posts.votes DESC, posts.created_at DESC
                          LIMIT ?
        """,
            (topic_id, limit),
        ).fetchall()
    return db.execute(
        """
    SELECT posts.*, users.username, topics.name as topic_name
                      FROM posts
                      JOIN users ON posts.user_id = users.id
                      LEFT JOIN topics on posts.topic_id = topics.id
                      WHERE posts.parent_id IS NULL
                      ORDER BY posts.votes DESC, posts.created_at DESC
                      LIMIT ?
    """,
        (limit,),
    ).fetchall()


# --- posting
def create_post(user_id, title, body, topic_id=None, parent_id=None):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, parent_id)
                        VALUES (?,?,?,?,?)""",
        (user_id, topic_id, title, body, parent_id),
    )
    db.commit()
    if parent_id:
        db.execute(
            "UPDATE posts SET reply_count = reply_count + 1 WHERE id = ?", (parent_id,)
        )
        db.commit()
    return cursor.lastrowid


def get_post(post_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name
                     FROM posts
                     JOIN users ON posts.user_id = user_id
                     LEFT JOIN topics ON posts.topic_id = topics.id
                     WHERE posts.id = ?
        """,
        (post_id,),
    ).fetchone()


def get_posts_by_user(user_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name
                      FROM posts
                      JOIN users ON posts.user_id = users.id
                      LEFT JOIN topics ON posts.topic_id = topics.id
                      WHERE posts.user_id = ?
                      AND posts.parent_id IS NULL
                      ORDER BY posts.created_at DESC
    """,
        (user_id,),
    ).fetchall()


def update_post(post_id, title, body):
    db = get_db()
    db.execute("UPDATE posts SET title=?, body=? WHERE id=?", (title, body, post_id))
    db.commit()


def delete_post(post_id):
    db = get_db()
    # delete voters and bookmarks (key cleanup), then post
    db.execute("DELETE FROM votes WHERE post_id=?", (post_id,))
    db.execute("DELETE FROM bookmarks WHERE post_id=?", (post_id,))
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()


# --- replies
def get_replies(post_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username
                      FROM posts
                      JOIN users ON posts.user_id = users.id
                      WHERE posts.parent_id = ?
                      ORDER BY posts.votes DESC, posts.created_at ASC
    """,
        (post_id,),
    ).fetchall()


# --- voting
def vote_post(user_id, post_id, value):
    """value: 1 for upvote, -1 for downvote"""
    db = get_db()
    existing = db.execute(
        "SELECT value FROM votes WHERE user_id=? AND post_id=?", (user_id, post_id)
    ).fetchone()

    if existing:
        if existing["value"] == value:
            # clicking vote again undoes it
            db.execute(
                "DELETE FROM votes WHERE user_id = ? AND post_id = ?",
                (user_id, post_id),
            )
            db.execute(
                "UPDATE posts SET votes = votes - ? WHERE id = ?", (value, post_id)
            )
        else:
            # Switching vote directoin
            db.execute(
                "UPDATE votes SET value=? WHERE user_id=? AND post_id=?",
                (value, user_id, post_id),
            )
            db.execute(
                "UPDATE posts SET votes = votes + ? WHERE id = ?", (value * 2, post_id)
            )
    else:
        db.execute(
            "INSERT INTO votes (user_id, post_id, value) VALUES (?, ?, ?)",
            (user_id, post_id, value),
        )
        db.execute("UPDATE posts SET votes = votes + ? WHERE id = ?", (value, post_id))
    db.commit()


# --- bookmarks
def toggle_bookmark(user_id, post_id):
    db = get_db()
    print(f"DEBUG toggle_bookmark: user_id={user_id}, post_id={post_id}")
    existing = db.execute(
        "SELECT user_id FROM bookmarks WHERE user_id=? AND post_id=?",
        (user_id, post_id),
    ).fetchone()
    print(f"DEBUG existing={existing}")

    if existing:
        db.execute(
            "DELETE FROM bookmarks WHERE user_id=? AND post_id=?", (user_id, post_id)
        )
        db.commit()
        return False
    else:
        result = db.execute(
            "INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id)
        )
        db.commit()
        print(f"DEBUG inserted rowid={result.lastrowid}")
        return True


def get_bookmarks(user_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name
        FROM bookmarks
        JOIN posts ON bookmarks.post_id = posts.id
        JOIN users ON posts.user_id = users.id
        LEFT JOIN topics ON posts.topic_id = topics.id
        WHERE bookmarks.user_id = ?
        ORDER BY bookmarks.created_at DESC
    """,
        (user_id,),
    ).fetchall()


def is_bookmarked(user_id, post_id):
    db = get_db()
    result = db.execute(
        "SELECT user_id FROM bookmarks WHERE user_id=? AND post_id=?",
        (user_id, post_id),
    ).fetchone()
    return result is not None
