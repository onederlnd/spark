from app.models import get_db
from app.models.attachments import save_file, delete_file

MAX_RESOURCE_TOTAL = 100 * 1024 * 1024  #


def get_resources_for_classroom(classroom_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM resources WHERE classroom_id = ? ORDER BY created_at DESC",
        (classroom_id,),
    ).fetchall()


def get_resource(resource_id):
    db = get_db()
    return db.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()


def add_resource_link(classroom_id, teacher_id, title, url):
    if not title or not url:
        raise ValueError("Title and URL are required.")
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO resources (classroom_id, teacher_id, type, title, url)
        VALUES (?, ?, 'link', ?, ?)
        """,
        (classroom_id, teacher_id, title, url),
    )
    db.commit()
    return cursor.lastrowid


def add_resource_file(classroom_id, teacher_id, title, file, app):
    if not title:
        raise ValueError("Title is required.")
    existing = get_resources_for_classroom(classroom_id)
    total = sum(r["file_size"] for r in existing if r["file_size"])
    if total >= MAX_RESOURCE_TOTAL:
        raise ValueError("Resource library storage limit reached (100mb total)")

    stored, original, size, mime = save_file(file, f"resources/{classroom_id}", app)

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO resources (classroom_id, teacher_id, type, title, filename, original_filename, file_size, mime_type)
        VALUES (?, ?, 'file', ?, ?, ?, ?, ?)
        """,
        (classroom_id, teacher_id, title, stored, original, size, mime),
    )
    db.commit()
    return cursor.lastrowid


def delete_resource(resource_id, app):
    db = get_db()
    row = get_resource(resource_id)
    if not row:
        return False

    if row["type"] == "file" and row["filename"]:
        delete_file(row["filename"], f"resources/{row['classroom_id']}", app)

    db.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    db.commit()
    return True


def attach_resources_to_assignment(assignment_id, resource_ids):
    """Attach a list of resource IDs to an assignment. Skips duplicate."""
    if not resource_ids:
        return
    db = get_db()
    for rid in resource_ids:
        db.execute(
            """
            INSERT OR IGNORE INTO assignment_resources (assignment_id, resource_id)
            VALUES (?, ?)
            """,
            (assignment_id, rid),
        )
    db.commit()


def detach_resource_from_assignment(assignment_id, resource_id):
    db = get_db()
    db.execute(
        "DELETE FROM assignment_resources WHERE assignment_id = ? AND resource_id = ?",
        (assignment_id, resource_id),
    )
    db.commit()


def get_resources_for_assignment(assignment_id):
    """Return all resources attached to an assignment"""
    db = get_db()
    return db.execute(
        """
        SELECT resources.*
        FROM assignment_resources
        JOIN resources ON assignment_resources.resource_id = resources.id
        WHERE assignment_resources.assignment_id = ?
        ORDER BY resources.type ASC, resources.title ASC
    """,
        (assignment_id,),
    ).fetchall()
