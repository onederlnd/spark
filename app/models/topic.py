# app/models/topic.py

from app.models import get_db


def get_all_topics():
    db = get_db()
    return db.execute("SELECT * FROM topics ORDER BY name").fetchall()


def get_topic_by_name(name):
    db = get_db()
    return db.execute("SELECT * FROM topics WHERE name = ?", (name,)).fetchone()


def create_topic(name, description=""):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO topics (name, description) VALUES(?, ?)", (name, description)
        )
        db.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def get_topic_with_count(name):
    db = get_db()
    return db.execute(
        """
        SELECT topics.*, COUNT(posts.id) as post_count
                      FROM topics
                      LEFT JOIN posts ON posts.topic_id = topics.id
                      WHERE topics.name = ?
                      GROUP BY topics.id                  
    """,
        (name,),
    ).fetchone()


def get_all_topics_with_counts():
    db = get_db()
    return db.execute("""
        SELECT topics.*, COUNT(posts.id) as post_count
                      FROM topics
                      LEFT JOIN posts ON posts.topic_id = topics.id
                      GROUP BY topics.id
                      ORDER BY post_count DESC, topics.name ASC
    """).fetchall()
