# app/models/post.py

from app.models import get_db

PER_PAGE = 20


# --- feed
def get_feed(page=1, topic_id=None, blocked_ids=None, user_id=None):
    offset = (page - 1) * PER_PAGE
    db = get_db()
    blocked_ids = blocked_ids or []

    membership_filter = """
        AND (
            posts.classroom_id IS NULL
            OR EXISTS (
                SELECT 1 FROM classroom_members cm
                WHERE cm.classroom_id = posts.classroom_id
                AND cm.user_id = ?
            )
        )
    """

    if topic_id:
        if blocked_ids:
            placeholders = ",".join("?" * len(blocked_ids))
            rows = db.execute(
                f"""
                SELECT posts.*, users.username, topics.name as topic_name,
                    (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
                FROM posts
                JOIN users ON posts.user_id = users.id
                LEFT JOIN topics ON posts.topic_id = topics.id
                WHERE posts.parent_id IS NULL
                    AND (posts.post_type = 'post' OR posts.post_type IS NULL)
                    AND posts.is_hidden = 0
                    AND posts.user_id NOT IN ({placeholders})
                    AND posts.topic_id = ?
                    {membership_filter}
                ORDER BY posts.reply_count DESC
                LIMIT ? OFFSET ?
                """,
                (*blocked_ids, topic_id, user_id, PER_PAGE + 1, offset),
            ).fetchall()
        else:
            rows = db.execute(
                f"""
                SELECT posts.*, users.username, topics.name as topic_name,
                    (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
                FROM posts
                JOIN users ON posts.user_id = users.id
                LEFT JOIN topics on posts.topic_id = topics.id
                WHERE posts.parent_id IS NULL
                    AND (posts.post_type = 'post' OR posts.post_type IS NULL)
                    AND posts.is_hidden = 0
                    AND posts.topic_id = ?
                    {membership_filter}
                ORDER BY posts.reply_count DESC
                LIMIT ? OFFSET ?
                """,
                (topic_id, user_id, PER_PAGE + 1, offset),
            ).fetchall()
    else:
        if blocked_ids:
            placeholder = ",".join("?" * len(blocked_ids))
            rows = db.execute(
                f"""
                SELECT posts.*, users.username, topics.name as topic_name,
                    (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
                FROM posts
                JOIN users ON posts.user_id = users.id
                LEFT JOIN topics ON posts.topic_id = topics.id
                WHERE posts.parent_id IS NULL
                    AND (posts.post_type = 'post' OR posts.post_type IS NULL)
                    AND posts.is_hidden = 0
                    AND posts.user_id NOT IN ({placeholder})
                    {membership_filter}
                ORDER BY posts.reply_count DESC
                LIMIT ? OFFSET ?
                """,
                (*blocked_ids, user_id, PER_PAGE + 1, offset),
            ).fetchall()
        else:
            rows = db.execute(
                f"""
                SELECT posts.*, users.username, topics.name as topic_name,
                    (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
                FROM posts
                JOIN users ON posts.user_id = users.id
                LEFT JOIN topics ON posts.topic_id = topics.id
                WHERE posts.parent_id IS NULL
                  AND (posts.post_type = 'post' OR posts.post_type IS NULL)
                  AND posts.is_hidden = 0
                  {membership_filter}
                ORDER BY posts.reply_count DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, PER_PAGE + 1, offset),
            ).fetchall()

    has_next = len(rows) > PER_PAGE
    return rows[:PER_PAGE], has_next


# --- posting
def create_post(
    user_id,
    title,
    body,
    author_username=None,
    topic_id=None,
    classroom_id=None,
    parent_id=None,
    post_type="post",
):
    from app.utils.content_filter import check_content
    from app.models.report import auto_flag_post
    from app.models.notifications import notify_mentions

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, parent_id, classroom_id, post_type)
        VALUES (?,?,?,?,?,?,?)""",
        (user_id, topic_id, title, body, parent_id, classroom_id, post_type),
    )
    db.commit()

    post_id = cursor.lastrowid

    db.execute(
        "INSERT INTO posts_fts(rowid, title, body) VALUES (?, ?, ?)",
        (cursor.lastrowid, title, body),
    )
    db.commit()

    if parent_id:
        db.execute(
            "UPDATE posts SET reply_count = reply_count + 1 WHERE id = ?", (parent_id,)
        )
        db.commit()

    matched = check_content(f"{title} {body}")
    if matched:
        auto_flag_post(post_id, matched)

    notify_mentions(body, post_id, user_id, author_username)
    return post_id


def get_post(post_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name
                     FROM posts
                     JOIN users ON posts.user_id == users.id
                     LEFT JOIN topics ON posts.topic_id = topics.id
                     WHERE posts.id = ?
        """,
        (post_id,),
    ).fetchone()


def get_posts_by_user(user_id, viewer_id=None):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name,
            (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN topics ON posts.topic_id = topics.id
        WHERE posts.user_id = ?
        AND posts.parent_id IS NULL
        AND (
            posts.classroom_id IS NULL
            OR EXISTS (
                SELECT 1 FROM classroom_members cm
                WHERE cm.classroom_id = posts.classroom_id
                AND cm.user_id = ?
            )
        )
        ORDER BY posts.created_at DESC
        """,
        (user_id, viewer_id),
    ).fetchall()


def update_post(post_id, title, body):
    db = get_db()
    db.execute("UPDATE posts SET title=?, body=? WHERE id=?", (title, body, post_id))
    db.commit()


def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM reactions WHERE post_id=?", (post_id,))
    db.execute("DELETE FROM bookmarks WHERE post_id=?", (post_id,))
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()


def hide_post(post_id):
    db = get_db()
    db.execute(
        "UPDATE posts SET is_hidden = 1 WHERE id=?",
        (post_id,),
    )
    db.commit()


def unhide_post(post_id):
    db = get_db()
    db.execute(
        "UPDATE posts SET is_hidden = 0 WHERE id=?",
        (post_id,),
    )
    db.commit()


# --- search
def search_posts(query, page=1, user_id=None):
    if not query or not query.strip():
        return [], False

    query = query.strip().replace('"', "").replace("(", "").replace(")", "")
    if not query:
        return [], False

    offset = (page - 1) * PER_PAGE
    db = get_db()

    rows = db.execute(
        """
        SELECT posts.*, users.username, topics.name as topic_name,
            (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
        FROM posts_fts
        JOIN posts ON posts_fts.rowid = posts.id
        JOIN users ON posts.user_id = users.id
        LEFT JOIN topics on posts.topic_id = topics.id
        WHERE posts_fts MATCH ?
        AND posts.parent_id IS NULL
        AND (
            posts.classroom_id IS NULL
            OR EXISTS (
                SELECT 1 FROM classroom_members cm
                WHERE cm.classroom_id = posts.classroom_id
                AND cm.user_id = ?
            )
        )
        ORDER BY rank
        LIMIT ? OFFSET ?
        """,
        (query, user_id, PER_PAGE + 1, offset),
    ).fetchall()
    has_next = len(rows) > PER_PAGE
    return rows[:PER_PAGE], has_next


# --- replies
def get_replies(post_id):
    db = get_db()
    return db.execute(
        """
        SELECT posts.*, users.username
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.parent_id = ?
            ORDER BY posts.reply_count ASC
    """,
        (post_id,),
    ).fetchall()


# --- bookmarks
def toggle_bookmark(user_id, post_id):
    db = get_db()
    existing = db.execute(
        "SELECT user_id FROM bookmarks WHERE user_id=? AND post_id=?",
        (user_id, post_id),
    ).fetchone()

    if existing:
        db.execute(
            "DELETE FROM bookmarks WHERE user_id=? AND post_id=?", (user_id, post_id)
        )
        db.commit()
        return False
    else:
        db.execute(
            "INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id)
        )
        db.commit()
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


# --- following feed
def get_following_feed(user_id, page=1, blocked_ids=None):
    """Return paginated feed of followe list"""
    offset = (page - 1) * PER_PAGE
    db = get_db()
    blocked_ids = blocked_ids or []

    if blocked_ids:
        placeholders = ",".join("?" * len(blocked_ids))
        rows = db.execute(
            f"""
            SELECT posts.*, users.username, topics.name as topic_name,
                (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
            FROM posts
            JOIN users ON posts.user_id = users.id
            LEFT JOIN topics ON posts.topic_id = topics.id
            WHERE posts.user_id IN (
                SELECT followed_id FROM follows WHERE follower_id = ?
            )
            AND (posts.post_type = 'post' OR posts.post_type IS NULL)
            AND posts.parent_id IS NULL
            AND posts.is_hidden = 0
            AND posts.user_id NOT IN ({placeholders})
            ORDER BY posts.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, *blocked_ids, PER_PAGE + 1, offset),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT posts.*, users.username, topics.name as topic_name,
                (SELECT COUNT(*) FROM reactions WHERE reactions.post_id = posts.id) as reaction_count
            FROM posts
            JOIN users ON posts.user_id = users.id
            LEFT JOIN topics ON posts.topic_id = topics.id
            WHERE posts.user_id IN (
                SELECT followed_id FROM follows WHERE follower_id = ?
            )
            AND (posts.post_type = 'post' OR posts.post_type IS NULL)
            AND posts.parent_id IS NULL
            AND posts.is_hidden = 0
            ORDER BY posts.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, PER_PAGE + 1, offset),
        ).fetchall()

    has_next = len(rows) > PER_PAGE
    return rows[:PER_PAGE], has_next
