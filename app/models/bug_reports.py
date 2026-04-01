from app.models import get_db


def create_bug_report(user_id, title, description, severity):
    db = get_db()
    db.execute(
        "INSERT INTO bug_reports (reported_by, title, description, severity) VALUES (?, ?, ?, ?)",
        (user_id, title, description, severity),
    )
    db.commit()


def get_all_bug_reports():
    db = get_db()
    return db.execute(
        """
        SELECT br.*, u.username
        FROM bug_reports br JOIN users u ON br.reported_by = u.id
        ORDER BY CASE severity WHEN 'high' then 1 WHEN 'medium' THEN 2 ELSE 3 END,
        created_at DESC
        """
    ).fetchall()


def get_bug_reports_by_user(user_id):
    db = get_db()
    return db.execute(
        """
        SELECT br.*, u.username
        FROM bug_reports br JOIN users u ON br.reported_by = u.id
        WHERE br.reported_by = ?
        ORDER BY br.created_at DESC
        """,
        (user_id,),
    ).fetchall()


def update_bug_report(report_id, status, admin_notes, severity=None):
    db = get_db()
    if severity:
        db.execute(
            """UPDATE bug_reports
               SET status = ?, admin_notes = ?, severity = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, admin_notes, severity, report_id),
        )
    else:
        db.execute(
            """UPDATE bug_reports
               SET status = ?, admin_notes = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, admin_notes, report_id),
        )
    db.commit()


def get_bug_report_counts():
    db = get_db()
    return db.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open,
            SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN severity='high' AND status ='open' THEN 1 ELSE 0 END) as open_high
        FROM bug_reports
        """
    ).fetchone()
