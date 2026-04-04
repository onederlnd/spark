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


def get_blocks_for_assignment(assignment_id):
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


def get_choices_for_blocks(block_ids):
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


def delete_choices_for_block(block_id):
    db = get_db()
    db.execute(
        "DELETE FROM block_choices WHERE block_id = ?",
        (block_id,),
    )
    db.execute()


def save_block_response(submission_id, block_id, choice_id=None, body=None, score=0):
    db = get_db()
    existing = db.execute(
        """
        SELECT id FROM block_responses
        WHERE submission_id = ? AND block_id = ?
        """,
        (submission_id, block_id),
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE block_responses
            SET choice_id = ?, body = ?, score = ?
            WHERE id = ?
            """,
            (choice_id, body, score, existing["id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO block_responses (submission_id, block_id, choice_id, body, score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (submission_id, block_id, choice_id, body, score),
        )
        db.commit()


def get_responses_for_submission(submission_id):
    db = get_db()
    return db.execute(
        """
        SELECT block_responses.*, lesson_blocks.type, lesson_blocks.body as question,
            lesson_blocks.points as max_points
        FROM block_responses
        JOIN lesson_blocks ON block_responses.block_id = lesson_blocks.id
        WHERE block_responses.submission_id = ?
        ORDER BY lesson_blocks.position ASC
        """,
        (submission_id,),
    ).fetchall()


def auto_grade_submission(submission_id):
    db = get_db()
    responses = get_responses_for_submission(submission_id)
    total = 0

    for r in responses:
        if r["type"] not in ("multple_choice", "true_false"):
            continue
        if not r["choice_id"]:
            continue
        choice = db.execute(
            "SELECT is_correct FROM block_choices WHERE id = ?", (r["choice_id"],)
        ).fetchone()
        if not choice:
            continue
        score = r["max_points"] if choice["is_correct"] else 0
        db.execute(
            "UPDATE block_responses SET score = ? WHERE id = ?",
            (score, r["id"]),
        )
        total += score

    db.commit()
    return total


def get_block_stats(assignment_id):
    db = get_db()
    return db.execute(
        """
        SELECT
            lesson_blocks.id as block_id,
            lesson_blocks.body as question,
            lesson_blocks.points as max_points,
            COUNT(block_responses.id) as total_responses,
            SUM(CASE WHEN block_choices.is_correct = 1 THEN 1
                ELSE 0 END) as correct_count
        FROM lesson_blocks
        LEFT JOIN block_responses ON block_responses.block_id = lesson_blocks.id
        LEFT JOIN block_choices ON block_responses.choice_id = block_choices.id
        WHERE lesson_blocks.assignment_id = ?
        AND lesson_blocks.type IN ('multiple_choice', 'true_false')
        GROUP BY lesson_blocks.id
        ORDER BY lesson_blocks.position ASC
        """,
        (assignment_id,),
    ).fetchall()
