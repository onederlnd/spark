# app/cli.py
import click
from app.models import get_db
import bcrypt
from datetime import datetime, timezone, timedelta
from flask import current_app
from flask.cli import with_appcontext

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _now(offset_days=0, offset_hours=0):
    dt = datetime.now(timezone.utc) + timedelta(days=offset_days, hours=offset_hours)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _hash(password: str) -> str:
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def _already_seeded(db) -> bool:
    row = db.execute("SELECT id FROM users WHERE username = 'demo-teacher'").fetchone()
    return row is not None


def _wipe_demo(db):
    """Remove all demo data cleanly, in FK-safe order."""
    teacher = db.execute(
        "SELECT id FROM users WHERE username = 'demo-teacher'"
    ).fetchone()
    if not teacher:
        return
    teacher_id = teacher["id"]

    classroom = db.execute(
        "SELECT id FROM classrooms WHERE teacher_id = ?", (teacher_id,)
    ).fetchone()

    if classroom:
        cid = classroom["id"]
        # submissions / block_responses
        assignment_ids = [
            r["id"]
            for r in db.execute(
                "SELECT id FROM assignments WHERE classroom_id = ?", (cid,)
            ).fetchall()
        ]
        for aid in assignment_ids:
            sub_ids = [
                r["id"]
                for r in db.execute(
                    "SELECT id FROM submissions WHERE assignment_id = ?", (aid,)
                ).fetchall()
            ]
            for sid in sub_ids:
                db.execute(
                    "DELETE FROM block_responses WHERE submission_id = ?", (sid,)
                )
            db.execute("DELETE FROM submissions WHERE assignment_id = ?", (aid,))
            block_ids = [
                r["id"]
                for r in db.execute(
                    "SELECT id FROM lesson_blocks WHERE assignment_id = ?", (aid,)
                ).fetchall()
            ]
            for bid in block_ids:
                db.execute("DELETE FROM block_choices WHERE block_id = ?", (bid,))
            db.execute("DELETE FROM lesson_blocks WHERE assignment_id = ?", (aid,))
        db.execute("DELETE FROM assignments WHERE classroom_id = ?", (cid,))

        # posts
        post_ids = [
            r["id"]
            for r in db.execute(
                "SELECT id FROM posts WHERE classroom_id = ?", (cid,)
            ).fetchall()
        ]
        for pid in post_ids:
            db.execute("DELETE FROM reactions WHERE post_id = ?", (pid,))
            db.execute("DELETE FROM posts WHERE parent_id = ?", (pid,))
        db.execute("DELETE FROM posts WHERE classroom_id = ?", (cid,))

        db.execute("DELETE FROM classroom_members WHERE classroom_id = ?", (cid,))
        db.execute("DELETE FROM classrooms WHERE id = ?", (cid,))

    # remove all demo user accounts
    demo_users = db.execute(
        "SELECT id FROM users WHERE username LIKE 'demo%'"
    ).fetchall()
    for u in demo_users:
        db.execute("DELETE FROM notifications WHERE user_id = ?", (u["id"],))
        db.execute(
            "DELETE FROM follows WHERE follower_id = ? OR followed_id = ?",
            (u["id"], u["id"]),
        )
    db.execute("DELETE FROM users WHERE username LIKE 'demo%'")
    db.commit()
    click.echo("  Wiped existing demo data.")


# ---------------------------------------------------------------------------
# main seed
# ---------------------------------------------------------------------------


def _seed(db):
    pw = _hash("password123")

    # ── users ────────────────────────────────────────────────────────────

    db.execute(
        """
        INSERT INTO users (username, email, display_name, password_hash, dob,
                           bio, role, tour_seen, coppa_status, onboarded,
                           avatar_emoji, avatar_bg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "demo-teacher",
            "demo-teacher@spark.dev",
            "Ms. Rivera",
            pw,
            "1985-06-15",
            "Python teacher and CS enthusiast. Here to help you learn!",
            "teacher",
            1,
            "approved",
            1,
            "👩‍🏫",
            "#E6F1FB",
        ),
    )
    teacher_id = db.execute(
        "SELECT id FROM users WHERE username = 'demo-teacher'"
    ).fetchone()["id"]

    db.execute(
        """
        INSERT INTO users (username, email, display_name, password_hash, dob,
                           bio, role, tour_seen, coppa_status, onboarded,
                           avatar_emoji, avatar_bg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "demo-student",
            "demo-student@spark.dev",
            "Alex Kim",
            pw,
            "2009-03-20",
            "Learning Python. Likes games and building stuff.",
            "student",
            0,
            "approved",
            1,
            "⚡",
            "#E1F5EE",
        ),
    )
    student_id = db.execute(
        "SELECT id FROM users WHERE username = 'demo-student'"
    ).fetchone()["id"]

    db.execute(
        """
        INSERT INTO users (username, email, display_name, password_hash, dob,
        bio, role, tour_seen, coppa_status, onboarded,
        avatar_emoji, avatar_bg)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "demo-parent",
            "demo-parent@go-spark.app",
            "Parent Demo",
            pw,
            "1980-01-01",
            "Parent of Alex Kim.",
            "parent",
            1,
            "approved",
            1,
            "👨‍👩‍👧",
            "#FFF8E7",
        ),
    )

    parent_id = db.execute(
        "SELECT id FROM users WHERE username = 'demo-parent'"
    ).fetchone()["id"]

    db.execute(
        "INSERT INTO parent_student (parent_id, student_id) VALUES (?, ?)",
        (parent_id, student_id),
    )

    # ghost students — realistic classroom population, no login needed
    ghosts = [
        ("demo-ghost-1", "Jordan Lee", "🎮", "#FAEEDA", "2009-07-01"),
        ("demo-ghost-2", "Sam Patel", "🚀", "#FCEBEB", "2009-11-12"),
        ("demo-ghost-3", "Riley Nguyen", "🌊", "#EAF3DE", "2010-01-30"),
        ("demo-ghost-4", "Casey Brown", "🎸", "#EEEDFE", "2009-08-08"),
        ("demo-ghost-5", "Morgan Diaz", "🦊", "#FAEEDA", "2010-03-14"),
        ("demo-ghost-6", "Taylor Wu", "🌙", "#E1F5EE", "2009-05-22"),
    ]
    ghost_ids = []
    for username, display_name, emoji, bg, dob in ghosts:
        db.execute(
            """
            INSERT INTO users (username, display_name, password_hash, dob,
                               role, tour_seen, coppa_status, onboarded,
                               avatar_emoji, avatar_bg)
            VALUES (?, ?, ?, ?, 'student', 1, 'approved', 1, ?, ?)
        """,
            (username, display_name, pw, dob, emoji, bg),
        )
        ghost_ids.append(
            db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()["id"]
        )

    click.echo("  ✓ Users created.")

    # ── classroom ────────────────────────────────────────────────────────

    db.execute(
        """
        INSERT INTO classrooms (teacher_id, name, description, join_code, messaging_enabled)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            teacher_id,
            "Intro to Python — Period 3",
            "A beginner Python course for curious minds. No experience needed.",
            "DEMO01",
            1,
        ),
    )
    classroom_id = db.execute(
        "SELECT id FROM classrooms WHERE join_code = 'DEMO01'"
    ).fetchone()["id"]

    # enroll teacher + demo student + ghosts
    db.execute(
        """
        INSERT INTO classroom_members (classroom_id, user_id, role)
        VALUES (?, ?, 'teacher')
    """,
        (classroom_id, teacher_id),
    )

    db.execute(
        """
        INSERT INTO classroom_members (classroom_id, user_id, role)
        VALUES (?, ?, 'student')
    """,
        (classroom_id, student_id),
    )

    for gid in ghost_ids:
        db.execute(
            """
            INSERT INTO classroom_members (classroom_id, user_id, role)
            VALUES (?, ?, 'student')
        """,
            (classroom_id, gid),
        )

    click.echo("  ✓ Classroom created (join code: DEMO01).")

    # ── topics ───────────────────────────────────────────────────────────

    for name, desc in [
        ("Python Basics", "Core language concepts"),
        ("Debugging Help", "Something broken? Ask here"),
        ("Project Showcase", "Show off what you built"),
        ("Community Chat", "Off-topic friendly chat"),
    ]:
        db.execute(
            """
            INSERT OR IGNORE INTO topics (name, description) VALUES (?, ?)
        """,
            (name, desc),
        )

    def topic(name):
        return db.execute("SELECT id FROM topics WHERE name = ?", (name,)).fetchone()[
            "id"
        ]

    click.echo("  ✓ Topics inserted.")

    # ── announcements ────────────────────────────────────────────────────

    db.execute(
        """
        INSERT INTO posts (post_type, user_id, topic_id, title, body,
                           classroom_id, created_at)
        VALUES ('announcement', ?, NULL, ?, ?, ?, ?)
    """,
        (
            teacher_id,
            "Welcome to Intro to Python!",
            "Hi everyone — so glad you're here. Read the syllabus pinned below "
            "and make sure you've joined the class with code [b]DEMO01[/b]. "
            "First assignment is due Friday. Ask questions any time!",
            classroom_id,
            _now(-5),
        ),
    )

    db.execute(
        """
        INSERT INTO posts (post_type, user_id, topic_id, title, body,
                           classroom_id, created_at)
        VALUES ('announcement', ?, NULL, ?, ?, ?, ?)
    """,
        (
            teacher_id,
            "Quiz next Thursday — loops & functions",
            "Just a reminder: we'll have a short quiz on while loops and "
            "function definitions next Thursday. Review your notes and "
            "ask questions on the feed if anything is confusing.",
            classroom_id,
            _now(-1),
        ),
    )

    click.echo("  ✓ Announcements posted.")

    # ── feed posts ───────────────────────────────────────────────────────

    # post 1 — ghost student asks a question, teacher + demo student reply
    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, classroom_id,
                           reply_count, created_at)
        VALUES (?, ?, ?, ?, ?, 2, ?)
    """,
        (
            ghost_ids[0],
            topic("Python Basics"),
            "Why doesn't my loop print anything?",
            "I wrote [code]for i in range(5):\nprint(i)[/code] but nothing shows up. "
            "What am I doing wrong?",
            classroom_id,
            _now(-3, -2),
        ),
    )
    p1 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, parent_id,
                           classroom_id, created_at)
        VALUES (?, ?, '', ?, ?, ?, ?)
    """,
        (
            ghost_ids[1],
            topic("Python Basics"),
            "Check your indentation! The print needs to be inside the loop.",
            p1,
            classroom_id,
            _now(-3, -1),
        ),
    )

    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, parent_id,
                           classroom_id, created_at)
        VALUES (?, ?, '', ?, ?, ?, ?)
    """,
        (
            teacher_id,
            topic("Python Basics"),
            "Great catch @demo-ghost-2! Exactly right — Python uses indentation "
            "to show what's inside a block. Indent the [code]print(i)[/code] "
            "line by 4 spaces and it will work.",
            p1,
            classroom_id,
            _now(-3),
        ),
    )

    # post 2 — demo student asks a question (so it shows in their feed)
    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, classroom_id,
                           reply_count, created_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
    """,
        (
            student_id,
            topic("Debugging Help"),
            "Getting a ZeroDivisionError — how do I handle it?",
            "My calculator crashes when I type 0 for division. "
            "I know I need to check for it but not sure how.\n\n"
            "[code]def divide(a, b):\n    return a / b[/code]",
            classroom_id,
            _now(-2),
        ),
    )
    p2 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, parent_id,
                           classroom_id, created_at)
        VALUES (?, ?, '', ?, ?, ?, ?)
    """,
        (
            teacher_id,
            topic("Debugging Help"),
            "Good instinct to check! Try wrapping in an if statement:\n\n"
            "[code]def divide(a, b):\n    if b == 0:\n        return "
            "'Error: cannot divide by zero'\n    return a / b[/code]\n\n"
            "You could also use a try/except — we'll cover that next week.",
            p2,
            classroom_id,
            _now(-1, -18),
        ),
    )

    # post 3 — project showcase from ghost
    db.execute(
        """
        INSERT INTO posts (user_id, topic_id, title, body, classroom_id,
                           reply_count, created_at)
        VALUES (?, ?, ?, ?, ?, 3, ?)
    """,
        (
            ghost_ids[2],
            topic("Project Showcase"),
            "I built a number guessing game!",
            "Finished my calculator assignment early so I kept going. "
            "Made a number guessing game with a while loop — it gives hints "
            "like 'too high' or 'too low'. Really proud of it!\n\n"
            "[code]import random\nnumber = random.randint(1, 100)\nguess = None\n"
            "while guess != number:\n    guess = int(input('Guess: '))\n    if guess "
            "< number:\n        print('Too low!')\n    elif guess > number:\n"
            "        print('Too high!')\nprint('You got it!')[/code]",
            classroom_id,
            _now(-4),
        ),
    )
    p3 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    for uid, body in [
        (ghost_ids[3], "This is so cool! I want to try making one too."),
        (student_id, "Love this — the hint feature is a great idea."),
        (
            teacher_id,
            "Excellent work @demo-ghost-3! Clean loop logic and good use of random. "
            "Show this to the class on Friday.",
        ),
    ]:
        db.execute(
            """
            INSERT INTO posts (user_id, topic_id, title, body, parent_id,
                               classroom_id, created_at)
            VALUES (?, ?, '', ?, ?, ?, ?)
        """,
            (uid, topic("Project Showcase"), body, p3, classroom_id, _now(-3)),
        )

    # reactions on p3
    for uid, emoji in [
        (student_id, "❤️"),
        (ghost_ids[0], "🎯"),
        (ghost_ids[1], "💡"),
        (teacher_id, "🎯"),
    ]:
        db.execute(
            """
            INSERT OR IGNORE INTO reactions (post_id, user_id, reaction, created_at)
            VALUES (?, ?, ?, ?)
        """,
            (p3, uid, emoji, _now(-3)),
        )

    click.echo("  ✓ Feed posts and replies seeded.")

    # ── assignments ──────────────────────────────────────────────────────

    # Assignment 1: Hello World (graded — demo student has an A)
    db.execute(
        """
        INSERT INTO assignments (classroom_id, title, instructions, due_date,
                                 attempts_allowed, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """,
        (
            classroom_id,
            "Hello World",
            "Write a Python program that prints 'Hello, World!' to the screen. "
            "Then modify it to ask for the user's name and greet them personally.",
            _now(-10),
            _now(-10),
        ),
    )
    a1 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # all students submitted a1
    submissions_a1 = [
        (
            student_id,
            "print('Hello, World!')\nname = input('What is your name? ')\nprint(f'Hello, {name}!')",
            "A",
            "Perfect — clean and personal. Great start!",
            _now(-9),
        ),
        (
            ghost_ids[0],
            "print('Hello, World!')\nname = input('Name: ')\nprint('Hello ' + name)",
            "A",
            "Good work! Try using an f-string next time.",
            _now(-9),
        ),
        (
            ghost_ids[1],
            "print('Hello World')",
            "C",
            "Missing the comma and the personalised greeting — reread the instructions.",
            _now(-9),
        ),
        (
            ghost_ids[2],
            "print('Hello, World!')\nname = input('Enter name: ')\nprint('Hello, ' + name + '!')",
            "A",
            "Excellent!",
            _now(-9),
        ),
        (
            ghost_ids[3],
            "print('Hello, World!')\nprint('Hello, friend!')",
            "B",
            "Good start, but the name should come from input(), not be hardcoded.",
            _now(-9),
        ),
        (
            ghost_ids[4],
            "print('Hello, World!')\nname = input('Your name: ')\nprint(f'Hey {name}, welcome!')",
            "A",
            "Love the enthusiasm in the greeting!",
            _now(-9),
        ),
        (
            ghost_ids[5],
            "print('hello world')",
            "B-",
            "Watch your capitalisation — Python strings are case-sensitive.",
            _now(-9),
        ),
    ]
    for uid, body, grade, feedback, ts in submissions_a1:
        db.execute(
            """
            INSERT INTO submissions (assignment_id, user_id, body, grade,
                                     feedback, submitted_at, graded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (a1, uid, body, grade, feedback, ts, _now(-8)),
        )

    # Assignment 2: Build a Calculator (submitted, not yet graded)
    db.execute(
        """
        INSERT INTO assignments (classroom_id, title, instructions, due_date,
                                 attempts_allowed, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """,
        (
            classroom_id,
            "Build a Calculator",
            "Write a Python calculator using functions for each operation "
            "(add, subtract, multiply, divide). Your calculator should:\n\n"
            "1. Loop so the user can keep calculating without restarting\n"
            "2. Handle division by zero gracefully\n"
            "3. Let the user type 'quit' to exit\n\n"
            "Use at least 4 functions and a while loop.",
            _now(3),
            _now(-7),
        ),
    )
    a2 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # demo student and a few ghosts submitted, some haven't
    submissions_a2 = [
        (
            student_id,
            "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a -"
            "b\n\ndef multiply(a, b):\n    return a * b\n\ndef divide(a, b):\n    if b == 0:\n"
            "        return 'Error: cannot divide by zero'\n    return a / b\n\ndef calculator():"
            "\n    while True:\n        op = input('Operation (+, -, *, /) or quit: ')\n        "
            "if op == 'quit':\n            break\n        a = float(input('First number: '))\n"
            "        b = float(input('Second number: '))\n        if op == '+':\n            "
            "print(add(a, b))\n        elif op == '-':\n            print(subtract(a, b))\n        "
            "elif op == '*':\n            print(multiply(a, b))\n        elif op == '/':\n            "
            "print(divide(a, b))\n\ncalculator()",
        ),
        (
            ghost_ids[0],
            "def add(a,b): return a+b\ndef sub(a,b): return a-b\ndef mul(a,b): return a*b\ndef div(a,b):\n"
            "    if b==0: return 'nope'\n    return a/b\nwhile True:\n    op=input('op: ')\n    if op=='quit':"
            " break\n    a=float(input('a: '))\n    b=float(input('b: '))\n    if op=='+': print(add(a,b))",
        ),
        (
            ghost_ids[2],
            "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n\nwhile True:\n    "
            "choice = input('+ or - or quit: ')\n    if choice == 'quit':\n        break\n    x = float(input('x: "
            "'))\n    y = float(input('y: '))\n    if choice == '+':\n        print(add(x, y))\n    else:\n        "
            "print(subtract(x, y))",
        ),
    ]
    for uid, body in submissions_a2:
        db.execute(
            """
            INSERT INTO submissions (assignment_id, user_id, body,
                                     submitted_at)
            VALUES (?, ?, ?, ?)
        """,
            (a2, uid, body, _now(-1)),
        )

    # Assignment 3: FizzBuzz Quiz (open — not yet submitted by demo student)
    db.execute(
        """
        INSERT INTO assignments (classroom_id, title, instructions, due_date,
                                 attempts_allowed, auto_grade, created_at)
        VALUES (?, ?, ?, ?, 1, 1, ?)
    """,
        (
            classroom_id,
            "FizzBuzz Quiz",
            "Answer the questions below about loops and conditionals. "
            "Multiple choice questions are graded automatically.",
            _now(7),
            _now(-2),
        ),
    )
    a3 = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # lesson blocks for the quiz
    db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?, 'text', ?, 0, 0, 0)
    """,
        (
            a3,
            "Read the following questions carefully. Select the best answer for each.",
        ),
    )

    db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?, 'multiple_choice', ?, 1, 2, 1)
    """,
        (a3, "What does FizzBuzz print when the number is divisible by both 3 and 5?"),
    )
    b1 = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    for body, correct in [("Fizz", 0), ("Buzz", 0), ("FizzBuzz", 1), ("Nothing", 0)]:
        db.execute(
            """
            INSERT INTO block_choices (block_id, body, is_correct) VALUES (?, ?, ?)
        """,
            (b1, body, correct),
        )

    db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?, 'true_false', ?, 2, 1, 1)
    """,
        (
            a3,
            "True or False: A while loop can run zero times if its condition starts as False.",
        ),
    )
    b2 = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    for body, correct in [("True", 1), ("False", 0)]:
        db.execute(
            """
            INSERT INTO block_choices (block_id, body, is_correct) VALUES (?, ?, ?)
        """,
            (b2, body, correct),
        )

    db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?, 'short_answer', ?, 3, 3, 1)
    """,
        (
            a3,
            "In your own words, explain what 'modulo' (%) does and why it's useful for FizzBuzz.",
        ),
    )

    db.execute(
        """
        INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
        VALUES (?, 'short_answer', ?, 4, 5, 1)
    """,
        (a3, "Write a for loop that prints FizzBuzz for numbers 1 to 20."),
    )

    click.echo("  ✓ Assignments and quiz blocks seeded.")

    # ── notifications for demo-student ───────────────────────────────────

    db.execute(
        """
        INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
        VALUES (?, 'grade', ?, ?, 0, ?)
    """,
        (
            student_id,
            "Your submission for 'Hello World' has been graded — Grade: A",
            f"/classrooms/{classroom_id}/assignments/{a1}",
            _now(-8),
        ),
    )

    db.execute(
        """
        INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
        VALUES (?, 'reply', ?, ?, 0, ?)
    """,
        (
            student_id,
            "Ms. Rivera replied to your post: 'Getting a ZeroDivisionError'",
            f"/posts/{p2}",
            _now(-1, -18),
        ),
    )

    db.execute(
        """
        INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
        VALUES (?, 'announcement', ?, ?, 0, ?)
    """,
        (
            student_id,
            "New announcement: Quiz next Thursday — loops & functions",
            f"/classrooms/{classroom_id}/",
            _now(-1),
        ),
    )

    click.echo("  ✓ Notifications seeded.")

    db.commit()
    click.echo("")
    click.echo("  Demo accounts ready:")
    click.echo("    Teacher  →  demo-teacher / password123")
    click.echo("    Student  →  demo-student / password123")
    click.echo("    Classroom join code: DEMO01")


def register_commands(app):
    @app.cli.command("set-role")
    @click.argument("username")
    @click.argument("role")
    def set_role(username, role):
        if role not in ("teacher", "student", "admin"):
            click.echo("Invalid role")
            return
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user:
            click.echo("User not found")
            return
        db.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        db.commit()
        click.echo(f"Updated {username} to {role}")

    @app.cli.command("seed-demo")
    @click.option(
        "--reset",
        is_flag=True,
        default=False,
        help="Wipe existing demo data before seeding.",
    )
    @with_appcontext
    def seed_demo(reset):
        """Seed demo accounts and classroom for the live site."""
        db = get_db()
        if reset:
            click.echo("Resetting demo data...")
            _wipe_demo(db)
        elif _already_seeded(db):
            click.echo("Demo data already seeded. Use --reset to re-seed.")
            return
        click.echo("Seeding demo data...")
        _seed(db)
        click.echo("Done.")
