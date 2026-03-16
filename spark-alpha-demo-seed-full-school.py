#!/usr/bin/env python3
"""
Full SparK development seed script
Creates a realistic classroom environment with demo accounts and COPPA logic.
Safe to run multiple times.
"""

import sqlite3
import os
import bcrypt
import random
from datetime import datetime, timedelta, timezone
from app import create_app
from app.models import init_db

app = create_app()

with app.app_context():
    init_db(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "spark-alpha-demo-seed-full-school.db")


def random_past_date(days_back=30):
    now = datetime.now(timezone.utc)
    random_days = random.randint(0, days_back)
    random_seconds = random.randint(0, 86400)
    return now - timedelta(days=random_days, seconds=random_seconds)


def insert_user(db, username, password="pass123", bio="", role="student", dob=None):
    # check if exists
    row = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row:
        return row[0]

    # hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    # calculate COPPA
    coppa_status = "approved"
    if dob:
        age = (
            datetime.now().year
            - dob.year
            - ((datetime.now().month, datetime.now().day) < (dob.month, dob.day))
        )
        coppa_status = "pending" if age < 13 else "approved"
        dob_str = dob.isoformat()
    else:
        dob_str = None

    db.execute(
        "INSERT INTO users (username, password_hash, bio, role, dob, coppa_status) VALUES (?, ?, ?, ?, ?, ?)",
        (username, hashed.decode(), bio, role, dob_str, coppa_status),
    )
    db.commit()

    return db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()[0]


def insert_classroom(db, teacher_ids, name, description, join_code):
    row = db.execute(
        "SELECT id FROM classrooms WHERE join_code = ?", (join_code,)
    ).fetchone()
    if row:
        return row[0]
    # assign first teacher as classroom teacher
    db.execute(
        "INSERT INTO classrooms (teacher_id, name, description, join_code) VALUES (?, ?, ?, ?)",
        (teacher_ids[0], name, description, join_code),
    )
    db.commit()
    return db.execute(
        "SELECT id FROM classrooms WHERE join_code = ?", (join_code,)
    ).fetchone()[0]


def add_member(db, classroom_id, user_id, role="student"):
    if not db.execute(
        "SELECT 1 FROM classroom_members WHERE classroom_id=? AND user_id=?",
        (classroom_id, user_id),
    ).fetchone():
        db.execute(
            "INSERT INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, ?)",
            (classroom_id, user_id, role),
        )
        db.commit()


def insert_topic(db, name, description=""):
    row = db.execute("SELECT id FROM topics WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    db.execute(
        "INSERT INTO topics (name, description) VALUES (?, ?)", (name, description)
    )
    db.commit()
    return db.execute("SELECT id FROM topics WHERE name = ?", (name,)).fetchone()[0]


def insert_post(db, user_id, topic_id, title, body, parent_id=None):
    db.execute(
        "INSERT INTO posts (user_id, topic_id, title, body, parent_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, topic_id, title, body, parent_id, random_past_date()),
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_assignment(db, classroom_id, title, instructions, due_date=None):
    row = db.execute(
        "SELECT id FROM assignments WHERE classroom_id=? AND title=?",
        (classroom_id, title),
    ).fetchone()
    if row:
        return row[0]
    db.execute(
        "INSERT INTO assignments (classroom_id, title, instructions, due_date) VALUES (?, ?, ?, ?)",
        (classroom_id, title, instructions, due_date),
    )
    db.commit()
    return db.execute(
        "SELECT id FROM assignments WHERE classroom_id=? AND title=?",
        (classroom_id, title),
    ).fetchone()[0]


def insert_submission(db, assignment_id, user_id, body):
    if db.execute(
        "SELECT 1 FROM submissions WHERE assignment_id=? AND user_id=?",
        (assignment_id, user_id),
    ).fetchone():
        return
    db.execute(
        "INSERT INTO submissions (assignment_id, user_id, body, submitted_at) VALUES (?, ?, ?, ?)",
        (assignment_id, user_id, body, random_past_date()),
    )
    db.commit()


def grade_submission(db, assignment_id, user_id):
    score = random.randint(70, 100)
    db.execute(
        "UPDATE submissions SET grade=?, graded_at=? WHERE assignment_id=? AND user_id=?",
        (score, random_past_date(), assignment_id, user_id),
    )
    db.commit()


def insert_vote(db, user_id, post_id, value):
    if not db.execute(
        "SELECT 1 FROM votes WHERE user_id=? AND post_id=?", (user_id, post_id)
    ).fetchone():
        db.execute(
            "INSERT INTO votes (user_id, post_id, value) VALUES (?, ?, ?)",
            (user_id, post_id, value),
        )
        db.commit()


def insert_bookmark(db, user_id, post_id):
    if not db.execute(
        "SELECT 1 FROM bookmarks WHERE user_id=? AND post_id=?", (user_id, post_id)
    ).fetchone():
        db.execute(
            "INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id)
        )
        db.commit()


def insert_notification(db, user_id, message, ntype="system", link=None):
    db.execute(
        "INSERT INTO notifications (user_id, type, message, link, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, ntype, message, link, datetime.now(timezone.utc)),
    )
    db.commit()


# --------------------------
# Begin seeding
# --------------------------

with sqlite3.connect(DB_PATH) as db:
    db.row_factory = sqlite3.Row

    # --------------------------
    # Demo users
    # --------------------------
    demo_student = insert_user(
        db,
        "Demo-Student",
        "pass123",
        "Demo student account",
        "student",
        datetime(2012, 5, 10),
    )
    demo_parent = insert_user(
        db,
        "Demo-Parent",
        "pass123",
        "Demo parent account",
        "parent",
        datetime(1984, 1, 3),
    )
    demo_teacher = insert_user(
        db,
        "Demo-Teacher",
        "pass123",
        "Demo teacher account",
        "teacher",
        datetime(1985, 4, 12),
    )
    dev = insert_user(
        db,
        "Dev",
        "pass123",
        "Developer teacher account",
        "teacher",
        datetime(1990, 9, 2),
    )
    demo_under13 = insert_user(
        db,
        "Demo-Under13",
        "pass123",
        "Under 13 student",
        "student",
        datetime(2015, 7, 22),
    )

    # --------------------------
    # Teachers
    # --------------------------
    teacher_names = ["Mr Smith", "Mrs Johnson"]
    teacher_ids = []
    for t in teacher_names:
        dob = datetime(
            random.randint(1975, 1985), random.randint(1, 12), random.randint(1, 28)
        )
        tid = insert_user(db, t, "pass123", t, "teacher", dob)
        teacher_ids.append(tid)

    # --------------------------
    # Students 6th grade 12-14
    # --------------------------
    first_names = [
        "Alice",
        "Ben",
        "Cara",
        "David",
        "Emma",
        "Finn",
        "Grace",
        "Henry",
        "Ivy",
        "Jack",
        "Kara",
        "Liam",
        "Maya",
        "Noah",
        "Olivia",
        "Paul",
        "Quinn",
        "Rosa",
        "Sam",
        "Tina",
        "Uma",
        "Victor",
        "Willa",
        "Xander",
        "Yara",
    ]
    student_ids = []
    for name in first_names:
        dob = datetime(
            random.randint(2009, 2011), random.randint(1, 12), random.randint(1, 28)
        )
        uname = f"{name} {name[0]}"  # first name + last initial
        uid = insert_user(db, uname, "pass123", f"{name} student", "student", dob)
        student_ids.append(uid)

    # --------------------------
    # Classroom
    # --------------------------
    classroom_id = insert_classroom(
        db, teacher_ids[:2], "6th Grade Homeroom", "6th grade classroom", "DEMO123"
    )
    for sid in student_ids + [demo_student, demo_under13]:
        add_member(db, classroom_id, sid, "student")
    for tid in teacher_ids + [demo_teacher, dev]:
        add_member(db, classroom_id, tid, "teacher")

    # --------------------------
    # Topics
    # --------------------------
    topics = ["General", "Homework Help", "Announcements", "Off Topic"]
    topic_ids = [insert_topic(db, t) for t in topics]

    # --------------------------
    # Posts & Replies
    # --------------------------
    post_ids = []
    discussion_topics = [
        "Homework help",
        "Science project ideas",
        "Math questions",
        "Favorite books",
        "Study tips",
    ]
    for _ in range(30):
        student_id = random.choice(student_ids + [demo_student])
        post_id = insert_post(
            db,
            student_id,
            topic_ids[0],
            random.choice(discussion_topics),
            "What do you think?",
        )
        post_ids.append(post_id)
        for _ in range(random.randint(1, 5)):
            insert_post(
                db,
                random.choice(student_ids),
                None,
                "Re:",
                "I think this works.",
                parent_id=post_id,
            )

    # --------------------------
    # Assignments & Submissions
    # --------------------------
    assignment_templates = [
        ("Reading Response", "Read chapter 3 and summarize."),
        ("Math Practice", "Complete worksheet pages 12–15."),
        ("Science Observation", "Observe weather patterns."),
    ]
    assignment_ids = []
    for title, text in assignment_templates:
        aid = insert_assignment(db, classroom_id, title, text, random_past_date())
        assignment_ids.append(aid)

    # Submissions
    for aid in assignment_ids:
        for sid in student_ids[:20]:
            insert_submission(db, aid, sid, "Here is my completed assignment.")

    # Grades
    for aid in assignment_ids:
        for sid in student_ids[:20]:
            grade_submission(db, aid, sid)

    # Votes
    for pid in post_ids:
        for v in random.sample(student_ids, random.randint(3, 10)):
            insert_vote(db, v, pid, random.choice([1, 1, 1, -1]))

    # Bookmarks
    for sid in student_ids[:10]:
        insert_bookmark(db, sid, random.choice(post_ids))

    # Notifications
    for sid in student_ids[:10]:
        insert_notification(db, sid, "Your assignment was graded.")

    print("Seeding complete!")
    print("Students:", len(student_ids))
    print("Teachers:", len(teacher_ids) + 2)
    print("Classroom ID:", classroom_id)
    print("Assignments:", len(assignment_ids))
    print("Posts:", len(post_ids))
