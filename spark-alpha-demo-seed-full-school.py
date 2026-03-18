#!/usr/bin/env python3
"""
Full SparK 5th-grade classroom seed script – semester simulation with realistic student content
Simulates three classrooms over a 16-week semester, realistic student content,
multi-level conversations, assignments, submissions, votes, bookmarks, and notifications.
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


def random_past_date(start_date, end_date):
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)


def insert_user(db, username, password="pass123", bio="", role="student", dob=None):
    row = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row:
        return row[0]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    coppa_status = "approved"
    dob_str = dob.isoformat() if dob else None
    if dob:
        age = (
            datetime.now().year
            - dob.year
            - ((datetime.now().month, datetime.now().day) < (dob.month, dob.day))
        )
        coppa_status = "pending" if age < 13 else "approved"
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


def insert_post(db, user_id, topic_id, title, body, created_at, parent_id=None):
    db.execute(
        "INSERT INTO posts (user_id, topic_id, title, body, parent_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, topic_id, title, body, parent_id, created_at),
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_assignment(db, classroom_id, title, instructions, due_date):
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


def insert_submission(db, assignment_id, user_id, body, submitted_at):
    if db.execute(
        "SELECT 1 FROM submissions WHERE assignment_id=? AND user_id=?",
        (assignment_id, user_id),
    ).fetchone():
        return
    db.execute(
        "INSERT INTO submissions (assignment_id, user_id, body, submitted_at) VALUES (?, ?, ?, ?)",
        (assignment_id, user_id, body, submitted_at),
    )
    db.commit()


def grade_submission(db, assignment_id, user_id):
    score = random.randint(70, 100)
    db.execute(
        "UPDATE submissions SET grade=?, graded_at=? WHERE assignment_id=? AND user_id=?",
        (score, datetime.now(timezone.utc), assignment_id, user_id),
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
    # Teachers
    # --------------------------
    teacher_names = ["Mr Smith", "Mrs Johnson", "Ms Lee", "Mr Garcia", "Mrs Patel"]
    teacher_ids = []
    for t in teacher_names:
        dob = datetime(
            random.randint(1975, 1985), random.randint(1, 12), random.randint(1, 28)
        )
        tid = insert_user(db, t, "pass123", t, "teacher", dob)
        teacher_ids.append(tid)

    # --------------------------
    # Students (5th grade)
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
            random.randint(2011, 2012), random.randint(1, 12), random.randint(1, 28)
        )
        uname = f"{name} {name[0]}"
        uid = insert_user(
            db, uname, "pass123", f"{name} is a curious student", "student", dob
        )
        student_ids.append(uid)

    # --------------------------
    # Classrooms
    # --------------------------
    classroom_ids = []
    classroom_data = [
        ("Math", teacher_ids[:2], "Math classroom", "MATH101"),
        ("Science", teacher_ids[2:4], "Science classroom", "SCI101"),
        ("English", teacher_ids[1:3], "English classroom", "ENG101"),
    ]
    for name, t_ids, desc, code in classroom_data:
        cid = insert_classroom(db, t_ids, name, desc, code)
        classroom_ids.append(cid)
        for sid in student_ids:
            add_member(db, cid, sid)
        for tid in t_ids:
            add_member(db, cid, tid, "teacher")

    # --------------------------
    # Topics
    # --------------------------
    topics = ["General", "Homework Help", "Announcements", "Off Topic"]
    topic_ids = [insert_topic(db, t) for t in topics]

    # --------------------------
    # Semester simulation: 16 weeks
    # --------------------------
    semester_start = datetime.now(timezone.utc) - timedelta(weeks=16)
    week_delta = timedelta(days=7)

    post_ids = []

    for week in range(16):
        week_start = semester_start + week * week_delta
        for cid in classroom_ids:
            for _ in range(5):  # 5 posts per week
                student_id = random.choice(student_ids)
                topic_id = random.choice(topic_ids)
                title = f"{random.choice(['Homework', 'Project', 'Question', 'Discussion'])} by {first_names[student_ids.index(student_id) % len(first_names)]}"

                # Generate unique body content per student
                body_lines = [
                    f"{first_names[student_ids.index(student_id) % len(first_names)]} asks: How do you solve problem {random.randint(1, 10)}?",
                    f"I tried this method, but {random.choice(['it didn’t work', 'I am confused', 'I need help'])}.",
                    f"Does anyone have tips on {random.choice(['fractions', 'science experiment', 'reading comprehension', 'spelling'])}?",
                ]
                body = " ".join(body_lines)
                created_at = random_past_date(week_start, week_start + week_delta)
                post_id = insert_post(db, student_id, topic_id, title, body, created_at)
                post_ids.append(post_id)

                # First-level replies
                first_level_ids = []
                for _ in range(random.randint(2, 4)):
                    replier_id = random.choice(student_ids)
                    reply_body = f"{first_names[student_ids.index(replier_id) % len(first_names)]} replies: {random.choice(['I found that using a diagram helps', 'Try reading the instructions carefully', 'You can ask the teacher for clarification', 'I solved it by breaking it into steps'])}."
                    reply_created = random_past_date(
                        created_at, week_start + week_delta
                    )
                    reply_id = insert_post(
                        db,
                        replier_id,
                        topic_id,
                        f"Re: {title}",
                        reply_body,
                        reply_created,
                        parent_id=post_id,
                    )
                    first_level_ids.append(reply_id)

                # Second-level replies
                for parent_reply_id in first_level_ids:
                    for _ in range(random.randint(0, 2)):
                        replier_id = random.choice(student_ids)
                        reply_body = f"{first_names[student_ids.index(replier_id) % len(first_names)]} adds: {random.choice(['That worked for me too', 'I have a different approach', 'Thanks for sharing!', 'Interesting idea!'])}"
                        reply_created = random_past_date(
                            created_at, week_start + week_delta
                        )
                        insert_post(
                            db,
                            replier_id,
                            topic_id,
                            f"Re: {title}",
                            reply_body,
                            reply_created,
                            parent_id=parent_reply_id,
                        )

    # --------------------------
    # Assignments & Submissions
    # --------------------------
    assignment_titles = ["Reading Response", "Math Practice", "Science Observation"]
    for week in range(16):
        week_start = semester_start + week * week_delta
        for cid in classroom_ids:
            for title in assignment_titles:
                due_date = week_start + timedelta(days=random.randint(4, 6))
                aid = insert_assignment(
                    db, cid, title, f"{title} instructions", due_date
                )
                for sid in student_ids:
                    submitted_at = random_past_date(week_start, due_date)
                    insert_submission(
                        db,
                        aid,
                        sid,
                        f"{first_names[student_ids.index(sid) % len(first_names)]}'s submission for {title}",
                        submitted_at,
                    )
                    grade_submission(db, aid, sid)

    # --------------------------
    # Votes, Bookmarks, Notifications
    # --------------------------
    for pid in post_ids:
        for v in random.sample(student_ids, random.randint(3, 8)):
            insert_vote(db, v, pid, random.choice([1, 1, -1]))

    for sid in student_ids[:10]:
        insert_bookmark(db, sid, random.choice(post_ids))
        insert_notification(db, sid, "Your assignment was graded.")

    print("Semester seeding complete!")
    print("Students:", len(student_ids))
    print("Teachers:", len(teacher_ids))
    print("Classrooms:", len(classroom_ids))
    print("Posts:", len(post_ids))
