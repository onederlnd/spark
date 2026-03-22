from app.models import get_db


# --- usage & activity
def get_user_counts():
    db = get_db()
    return db.execute(
        """
        SELECT COUNT(*) AS total,
        SUM(CASE WHEN created_at >= datetime('now', '-7 days' THEN 1 ELSE 0 END) as last_7,
        SUM(CASE WHEN created_at >= datetime('now', '-30 days' THEN 1 ELSE 0 END) as last_30,
        FROM users
        """
    ).fetchone()


def get_daily_new_users(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS count
        FROM users
        WHERE created_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_daily_posts(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) as day, COUNT(*) as count
        FROM posts
        WHERE created_at >= datetime('now', ?)
        AND parent_id IS NULL
        GROUP BY day
        ORDER BY day ASC
    """,
        (f"-{days} days",),
    ).fetchall()


def get_daily_replies(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS count
        FROM posts
        WHERE created_at >= datetime('now', ?)
        AND parent_id IS NOT NULL
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"{days} days",),
    ).fetchall()


def get_daily_submissions(days=14):
    db = get_db()

    return db.execute(
        """
        SELECT date(submitted_at) AS day, COUNT(*) AS count
        FROM submissions
        WHERE submitted_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_daily_logins(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS count
        FROM login_events
        WHERE created_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_top_active_students_by_posts(limit=10):
    db = get_db()
    return db.execute(
        """
        SELECT users.username, COUNT(posts.id) AS post_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE users.role = 'student'
        AND posts.parent_id IS NULL
        GROUP BY users.id
        ORDER BY posts_count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_top_active_students_by_submissions(limit=10):
    db = get_db()
    return db.execute(
        """
        SELECT users.username, COUNT(submissions.id) AS submissions_count
        FROM submissions
        JOIN users ON submissions.user_id = users.id
        GROUP BY users.id
        ORDER BY submission_count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_login_method_counts():
    db = get_db()
    return db.execute("""
        SELECT method, COUNT(*) as count
        FROM login_events
        GROUP BY method
    """).fetchall()


# --- safety & moderation
def get_report_counts():
    db = get_db()
    return db.execute(
        """
        SELECT COUNT(*) AS TOTAL
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS open,
            SUM(CASE WHEN status != 'pending' THEN 1 ELSE 0 END) AS resolved
        FROM
        """
    ).fetchone()


def get_daily_reports(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS COUNT
        FROM reports
        WHERE created_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_avg_report_resolution_hours():
    db = get_db()
    row = db.execute(
        """
        SELECT AVG(
            (julianday(reviewed_at) - julianday(created_at)) * 24
            ) AS avg_hours
            FROM reports
            WHERE reviewed_at IS NOT NULL
        """
    ).fetchone()
    return round(row["avg_hours"], 1) if row and row["avg_hours"] else None


def get_top_filter_words(limit=10):
    db = get_db()
    return db.execute(
        """
        SELECT word, COUNT(*) AS hit_count
        FROM filter_hits
        GROUP BY word
        ORDER BY hit_count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_daily_filter_hits(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) AS day, COUNT(*) AS count
        FROM filter_hits
        WHERE created_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_coppa_pending():
    db = get_db()
    return db.execute(
        """
        SELECT username, dob, created_at,
            ROUND((julianday('now') - julianday(created_at)) * 24) AS hours_waiting
            FROM users
            WHERE coppa_status = 'pending'
            ORDER BY created_at ASC
        """
    ).fetchall()


# --- classroom health


def get_classroom_counts():
    db = get_db()
    return db.execute(
        """
        SELECT
            COUNT(DISTINCT classrooms.id) AS total_classrooms,
            COUNT(DISTINCT assignments.id) AS total_assignments,
            COUNT(DISTINCT submissions.id) AS total_submissions
        FROM classrooms
        LEFT JOIN assignments ON assignments.classroom_id = classrooms.id
        LEFT JOIN submissions ON submissions.assignment_id = assignments.id
        """
    ).fetchone()


def get_classroom_completion_rates():
    db = get_db()
    return db.execute("""
        SELECT
            classrooms.name AS classroom_name,
            COUNT(DISTINCT assignments.id) AS assignment_count,
            COUNT(DISTINCT classroom_members.user_id) AS student_count,
            COUNT(DISTINCT submissions.id) AS submission_count
        FROM classrooms
        LEFT JOIN assignments ON assignments.classroom_id = classrooms.id
        LEFT JOIN classroom_members ON classroom_members.classroom_id = classrooms.id
            AND classroom_members.role = 'student'
        LEFT JOIN submissions ON submissions.assignment_id = assignments.id
            AND submissions.user_id = classroom_members.user_id
        GROUP BY classrooms.id
        ORDER BY classrooms.name ASC
    """).fetchall()


def get_ungraded_submissions_by_teacher():
    db = get_db()
    return db.execute(
        """
        SELECT users.username AS teacher,
            COUNT(submissions.id) AS ungraded_count
        FROM submissions
        JOIN assignments ON submissions.assignment_id = assignments.id
        JOIN classrooms ON assignments.classroom_id = classrooms.id
        JOIN users ON classrooms.teacher_id = users.id
        WHERE (submissions.grade IS NULL OR submissions.grade = '')
        GROUP BY classrooms.teacher_id
        ORDER BY ungraded_count DESC
        """
    ).fetchall()


def get_inactive_students(days=7):
    """Students who have not logged in within the last N days"""
    db = get_db()
    return db.execute(
        """
        SELECT users.username,
            MAX(login_events.created_at) AS last_login,
            ROUND((julianday('now') - julianday(MAX(login_events.created_at))) * 24) AS hours_since_login
            FROM users
            LEFT JOIN login_events ON login_events.user_id = users.id
            WHERE users.role = 'student'
            GROUP BY users.id
            HAVING last_login IS NULL
                OR last_login < datetime('now', ?)
            ORDER BY last_login ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_students_with_zero_submissions():
    db = get_db()
    return db.execute(
        """
        SELECT users.username,
            COUNT(DISTINCT classroom_members. classroom_id) AS classroom_count
            FROM users
            JOIN classroom_members ON classroom_members.user_id = users.id
                AND classroom_members.role = 'student'
            LEFT JOIN submissions ON submissions.user_id = users.id
            WHERE usres.role = 'student'
            GROUP BY users.id
            HAVING COUNT(submissions.id) = 0
            ORDER BY users.username ASC
        """
    ).fetchall()


def get_daily_rate_limit_hits(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT day(created_at) AS day, COUNT(*) AS count
        FROM rate_limit_hits
        WHERE created_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_top_rate_limited_routes(limit=10):
    db = get_db()
    return db.execute(
        """
        SELECT route, COUNT(*) AS hit_count
        FROM rate_limit_hits
        GROUP BY route
        ORDER BY hit_count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_daily_session_events(days=14):
    db = get_db()
    return db.execute(
        """
        SELECT date(created_at) as day, event_type, COUNT(*) AS COUNT
        FROM session_events
        WHERE created_at >= datetime('now', ?)
        GROUP BY day, event_type
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()


def get_session_event_counts():
    db = get_db()
    return db.execute(
        """
        SELECT event_type, COUNT(*) AS COUNT
        FROM session_events
        GROUP BY event_type
        """
    ).fetchall()
