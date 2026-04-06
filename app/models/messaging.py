# app/models/messaging.py

from app.models import get_db
from datetime import date


def _is_under_13(dob_str):
    """Return True if the user's dob_str indicates they are under 13."""
    if not dob_str:
        return False
    try:
        dob = date.fromisoformat(dob_str[:10])
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age < 13
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# permission helpers
# ---------------------------------------------------------------------------


def can_message(sender_id, recipient_ids, classroom_id):
    """
    Return (True, None) if the sender is allowed to start/join a conversation
    with all recipient_ids in the given classroom, or (False, reason) if not.

    Rules:
    - All participants must share the classroom.
    - Parent <-> student conversations are forbidden.
    - Student <-> student requires messaging_enabled on the classroom.
    - Teachers can always message students and parents in their classroom.
    - Parents can only message teachers.
    """
    db = get_db()

    classroom = db.execute(
        "SELECT * FROM classrooms WHERE id = ?", (classroom_id,)
    ).fetchone()
    if not classroom:
        return False, "Classroom not found."

    all_ids = [sender_id] + list(recipient_ids)

    # verify everyone is a member of the classroom
    for uid in all_ids:
        member = db.execute(
            "SELECT role FROM classroom_members WHERE classroom_id = ? AND user_id = ?",
            (classroom_id, uid),
        ).fetchone()
        if not member:
            return False, f"User {uid} is not a member of this classroom."

    def get_role(uid):
        user = db.execute("SELECT role FROM users WHERE id = ?", (uid,)).fetchone()
        return user["role"] if user else None

    sender_role = get_role(sender_id)
    recipient_roles = [get_role(rid) for rid in recipient_ids]

    # block parent <-> student entirely
    if sender_role == "parent" and any(r == "student" for r in recipient_roles):
        return False, "Parents cannot message students directly."
    if sender_role == "student" and any(r == "parent" for r in recipient_roles):
        return False, "Students cannot message parents."

    # student <-> student requires messaging_enabled
    if sender_role == "student" and any(r == "student" for r in recipient_roles):
        if not classroom["messaging_enabled"]:
            return False, "Student messaging is not enabled in this classroom."

    return True, None


def is_teacher_of_classroom(user_id, classroom_id):
    db = get_db()
    row = db.execute(
        "SELECT role FROM classroom_members WHERE classroom_id = ? AND user_id = ?",
        (classroom_id, user_id),
    ).fetchone()
    return row and row["role"] == "teacher"


def can_read_conversation(user_id, conversation_id):
    """
    Return True if user_id is a member of the conversation, OR if they are a
    teacher in the classroom and at least one member is under 13.
    """
    db = get_db()

    # direct member
    member = db.execute(
        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if member:
        return True

    # teacher oversight for under-13 members
    conv = db.execute(
        "SELECT classroom_id FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    if not conv:
        return False

    if is_teacher_of_classroom(user_id, conv["classroom_id"]):
        under_13_member = db.execute(
            """
            SELECT 1 FROM conversation_members cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.conversation_id = ?
            AND u.role = 'student'
            AND u.coppa_status != 'approved'
            """,
            (conversation_id,),
        ).fetchone()

        if not under_13_member:
            # also check by dob for approved-but-under-13
            members = db.execute(
                """
                SELECT u.dob FROM conversation_members cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.conversation_id = ? AND u.role = 'student'
                """,
                (conversation_id,),
            ).fetchall()
            under_13_member = any(_is_under_13(m["dob"]) for m in members)

        if under_13_member:
            return True

    return False


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------


def create_conversation(classroom_id, created_by, member_ids, title=None):
    """
    Create a conversation and add all members. Returns conversation_id.
    member_ids should include created_by.
    """
    db = get_db()
    cursor = db.execute(
        "INSERT INTO conversations (classroom_id, created_by, title) VALUES (?, ?, ?)",
        (classroom_id, created_by, title),
    )
    db.commit()
    conversation_id = cursor.lastrowid

    all_members = list({created_by} | set(member_ids))
    for uid in all_members:
        db.execute(
            "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id) VALUES (?, ?)",
            (conversation_id, uid),
        )
    db.commit()
    return conversation_id


def get_conversation(conversation_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()


def get_conversations_for_user(user_id):
    """
    Return all conversations the user is a member of, with the latest message
    preview and unread count, ordered by most recent activity.
    """
    db = get_db()
    return db.execute(
        """
        SELECT
            c.id,
            c.title,
            c.classroom_id,
            cl.name as classroom_name,
            cm.last_read_at,
            (
                SELECT body FROM messages
                WHERE conversation_id = c.id AND is_hidden = 0
                ORDER BY created_at DESC LIMIT 1
            ) as last_message_body,
            (
                SELECT created_at FROM messages
                WHERE conversation_id = c.id AND is_hidden = 0
                ORDER BY created_at DESC LIMIT 1
            ) as last_message_at,
            (
                SELECT COUNT(*) FROM messages m
                WHERE m.conversation_id = c.id
                AND m.is_hidden = 0
                AND (cm.last_read_at IS NULL OR m.created_at > cm.last_read_at)
            ) as unread_count
        FROM conversations c
        JOIN conversation_members cm ON cm.conversation_id = c.id AND cm.user_id = ?
        JOIN classrooms cl ON c.classroom_id = cl.id
        ORDER BY last_message_at DESC NULLS LAST, c.created_at DESC
        """,
        (user_id,),
    ).fetchall()


def get_conversation_members(conversation_id):
    db = get_db()
    return db.execute(
        """
        SELECT u.id, u.username, u.display_name, u.avatar_emoji, u.avatar_bg,
               u.role, cm.last_read_at
        FROM conversation_members cm
        JOIN users u ON cm.user_id = u.id
        WHERE cm.conversation_id = ?
        ORDER BY u.username ASC
        """,
        (conversation_id,),
    ).fetchall()


def get_or_create_dm(classroom_id, user_a, user_b):
    """
    Find an existing one-on-one conversation between two users in a classroom,
    or create one. Returns conversation_id.
    """
    db = get_db()
    row = db.execute(
        """
        SELECT c.id FROM conversations c
        JOIN conversation_members cma ON cma.conversation_id = c.id AND cma.user_id = ?
        JOIN conversation_members cmb ON cmb.conversation_id = c.id AND cmb.user_id = ?
        WHERE c.classroom_id = ?
        AND (
            SELECT COUNT(*) FROM conversation_members
            WHERE conversation_id = c.id
        ) = 2
        LIMIT 1
        """,
        (user_a, user_b, classroom_id),
    ).fetchone()

    if row:
        return row["id"]

    return create_conversation(classroom_id, user_a, [user_b])


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------


def send_message(conversation_id, sender_id, body):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO messages (conversation_id, sender_id, body) VALUES (?, ?, ?)",
        (conversation_id, sender_id, body),
    )
    db.commit()
    return cursor.lastrowid


# ─── REPLACE get_messages in app/models/messaging.py with this version ───────
# Adds after_id support for the floating messenger's polling loop.


def get_messages(conversation_id, limit=50, before_id=None, after_id=None):
    """
    Return messages for a conversation, oldest first (newest last).
    - before_id: paginate backwards (load older messages)
    - after_id:  poll for new messages (used by floating messenger)
    """
    db = get_db()

    if after_id:
        # Return messages newer than after_id, oldest first
        return db.execute(
            """
            SELECT m.*, u.username, u.display_name, u.avatar_emoji, u.avatar_bg
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            AND m.is_hidden = 0
            AND m.id > ?
            ORDER BY m.created_at ASC
            LIMIT ?
            """,
            (conversation_id, after_id, limit),
        ).fetchall()

    if before_id:
        # Paginate backwards — fetch older, return in chronological order
        return db.execute(
            """
            SELECT m.*, u.username, u.display_name, u.avatar_emoji, u.avatar_bg
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            AND m.is_hidden = 0
            AND m.id < ?
            ORDER BY m.created_at DESC
            LIMIT ?
            """,
            (conversation_id, before_id, limit),
        ).fetchall()[::-1]

    # Default: most recent N messages, oldest first
    return db.execute(
        """
        SELECT m.*, u.username, u.display_name, u.avatar_emoji, u.avatar_bg
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.conversation_id = ?
        AND m.is_hidden = 0
        ORDER BY m.created_at DESC
        LIMIT ?
        """,
        (conversation_id, limit),
    ).fetchall()[::-1]


def mark_read(conversation_id, user_id):
    db = get_db()
    db.execute(
        """
        UPDATE conversation_members
        SET last_read_at = CURRENT_TIMESTAMP
        WHERE conversation_id = ? AND user_id = ?
        """,
        (conversation_id, user_id),
    )
    db.commit()


def hide_message(message_id):
    db = get_db()
    db.execute("UPDATE messages SET is_hidden = 1 WHERE id = ?", (message_id,))
    db.commit()


def get_total_unread_count(user_id):
    db = get_db()
    row = db.execute(
        """
        SELECT COALESCE(SUM(
            (SELECT COUNT(*) FROM messages m
             WHERE m.conversation_id = cm.conversation_id
             AND m.is_hidden = 0
             AND (cm.last_read_at IS NULL OR m.created_at > cm.last_read_at))
        ), 0) as total
        FROM conversation_members cm
        WHERE cm.user_id = ?
        """,
        (user_id,),
    ).fetchone()
    return row["total"] if row else 0


# ---------------------------------------------------------------------------
# teacher controls
# ---------------------------------------------------------------------------


def toggle_messaging(classroom_id, enabled: bool):
    db = get_db()
    db.execute(
        "UPDATE classrooms SET messaging_enabled = ? WHERE id = ?",
        (1 if enabled else 0, classroom_id),
    )
    db.commit()


def get_conversations_for_teacher_oversight(classroom_id):
    """
    Return all conversations in a classroom involving under-13 students,
    for teacher moderation view.
    """
    db = get_db()
    return db.execute(
        """
        SELECT DISTINCT c.id, c.title, c.created_at,
            u.username as created_by_username
        FROM conversations c
        JOIN users u ON c.created_by = u.id
        JOIN conversation_members cm ON cm.conversation_id = c.id
        JOIN users mu ON cm.user_id = mu.id
        WHERE c.classroom_id = ?
        AND mu.role = 'student'
        AND (
            mu.coppa_status != 'approved'
            OR (
                CAST(strftime('%Y', 'now') AS INTEGER) -
                CAST(strftime('%Y', mu.dob) AS INTEGER) -
                (strftime('%m-%d', 'now') < strftime('%m-%d', mu.dob)) < 13
            )
        )
        ORDER BY c.created_at DESC
        """,
        (classroom_id,),
    ).fetchall()
