from app.models import get_db


def create_block(assignment_id, block_type, body, position, points=0, required=1):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?,?,?,?,?,?)
        """,
        (assignment_id, block_type, body, position, points, required),
    )
    db.commit()
    return cursor.lastrowid


def get_blocks_for_assignments(assignment_id):
    db = get_db()
    return db.execute(
        """
        SELECT * FROM lesson_blocks
        WHERE assignment_id = ?
        ORDER BY position ASC
        """,
        (assignment_id,),
    ).fetchall()


def update_block(block_id, body, points, required):
    db = get_db()
    db.execute(
        """
        UPDATE lesson_blocks SET body = ?, points = ?, required = ?
        WHERE id = ?
        """,
        (body, points, required, block_id),
    )
    db.commit()


def delete_block(block_id):
    db = get_db()
    db.execute("DELETE FROM lesson_blocks WHERE id = ?", (block_id,))
    db.commit()


def reorder_blocks(block_positions):
    db = get_db()
    for block_id, position in block_positions:
        db.execute(
            "UPDATE lesson_blocks SET position = ? WHERE id = ?",
            (position, block_id),
        )
    db.commit()


def get_block(block_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM lesson_blocks WHERE id = ?", (block_id,)
    ).fetchone()


def create_choice(block_id, body, is_correct=0):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO blocks_choices (block_id, body, is_correct)
        VALUES (?, ?, ?)
        """,
        (block_id, body, is_correct),
    )
    db.commit()
    return cursor.lastrowid


def get_choices_for_block(block_id):
    db = get_db()
    db.execute(
        "DELETE FROM block_choices WHERE block_id = ?",
        (block_id),
    )
    db.commit()


def get_choces_for_blocks(block_ids):
    if not block_ids:
        return {}
    db = get_db()
    placeholders = ",".join("?" * len(block_ids))
    rows = db.execute(
        f"SELECT * FROM block_choices WHERE block_id IN ({placeholders}) ORDER BY id ASC",
        block_ids,
    ).fetchall()
    result = {}
    for row in rows:
        result.setdefault(row["block_id"], []).append(row)
    return result


def save_block_response(submission_id, block_id, choice_id=None, body=None, score=0):
    pass
