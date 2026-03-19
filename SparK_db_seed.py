#!/usr/bin/env python3

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


# --------------------------
# Time helpers (school hours realism)
# --------------------------
def school_time(day):
    hour = random.choice([8, 9, 10, 11, 12, 13, 14, 15])
    minute = random.randint(0, 59)
    return day.replace(hour=hour, minute=minute)


def rand_between(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


# --------------------------
# DB helpers
# --------------------------
def insert_user(db, username, role, dob):
    row = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if row:
        return row[0]

    pw = bcrypt.hashpw("pass123".encode(), bcrypt.gensalt()).decode()
    db.execute(
        "INSERT INTO users (username, password_hash, role, dob, coppa_status) VALUES (?, ?, ?, ?, ?)",
        (username, pw, role, dob.isoformat(), "approved"),
    )
    db.commit()
    return db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[
        0
    ]


def insert_classroom(db, teacher_id):
    row = db.execute("SELECT id FROM classrooms WHERE name=?", ("Room 5A",)).fetchone()
    if row:
        return row[0]

    db.execute(
        "INSERT INTO classrooms (teacher_id, name, description, join_code) VALUES (?, ?, ?, ?)",
        (teacher_id, "Room 5A", "5th Grade Homeroom", "JOIN5A"),
    )
    db.commit()
    return db.execute(
        "SELECT id FROM classrooms WHERE name=?", ("Room 5A",)
    ).fetchone()[0]


def add_member(db, cid, uid, role="student"):
    if not db.execute(
        "SELECT 1 FROM classroom_members WHERE classroom_id=? AND user_id=?",
        (cid, uid),
    ).fetchone():
        db.execute(
            "INSERT INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, ?)",
            (cid, uid, role),
        )
        db.commit()


def insert_topic(db, name):
    row = db.execute("SELECT id FROM topics WHERE name=?", (name,)).fetchone()
    if row:
        return row[0]
    db.execute("INSERT INTO topics (name) VALUES (?)", (name,))
    db.commit()
    return db.execute("SELECT id FROM topics WHERE name=?", (name,)).fetchone()[0]


def insert_post(db, user_id, topic_id, title, body, created_at, parent_id=None):
    db.execute(
        "INSERT INTO posts (user_id, topic_id, title, body, parent_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, topic_id, title, body, parent_id, created_at),
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_assignment(db, cid, title, instructions, due):
    db.execute(
        "INSERT INTO assignments (classroom_id, title, instructions, due_date) VALUES (?, ?, ?, ?)",
        (cid, title, instructions, due),
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_submission(db, aid, uid, body, submitted_at):
    db.execute(
        "INSERT INTO submissions (assignment_id, user_id, body, submitted_at) VALUES (?, ?, ?, ?)",
        (aid, uid, body, submitted_at),
    )
    db.commit()


def grade_submission(db, aid, uid):
    score = random.randint(72, 100)
    db.execute(
        "UPDATE submissions SET grade=?, graded_at=? WHERE assignment_id=? AND user_id=?",
        (score, datetime.now(timezone.utc), aid, uid),
    )
    db.commit()


# --------------------------
# SAFETY: prevent demo posting
# --------------------------
def safe_insert_post(db, user_id, *args, **kwargs):
    row = db.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()

    if row and "demo" in row["username"].lower():
        return None

    return insert_post(db, user_id, *args, **kwargs)


# --------------------------
# Natural language helpers (FULL)
# --------------------------
AGREEMENTS = [
    "yeah that makes sense",
    "ohhh I get it now",
    "same I thought that too",
    "yeah I agree with you",
    "that actually helps a lot",
    "ok that cleared it up",
    "wait that’s actually smart",
    "yeah that’s what I got too",
    "oh we did that in class",
    "that’s what I wrote",
    "same answer here",
    "yeah I think you’re right",
    "ok yeah that checks out",
    "that makes way more sense now",
    "yeah I remember that",
    "that’s a good point",
    "ok yeah I see it now",
    "that helped thanks",
    "yeah that’s how I did it",
    "ohhh ok got it",
    "yeah that’s what I meant too",
    "same I was confused at first",
    "yeah I agree",
    "ok that makes sense now",
    "yeah that worked for me",
    "I think you’re right",
    "yeah that matches mine",
    "ok yeah I understand now",
    "that explains it",
    "yeah that’s better",
    "same here",
    "yeah I like that answer",
    "that actually helped me",
    "ok that’s clearer",
    "yeah that’s true",
    "that makes sense now",
    "ok yeah thanks",
    "yeah I got that too",
    "same answer",
    "yeah that works",
    "that’s what I thought",
    "ok that helps",
    "yeah that’s right",
    "same idea",
    "yeah that’s good",
    "ok I see now",
    "yeah makes sense",
    "that works",
    "yeah I get it now",
    "ok yeah cool",
]

CONFUSED = [
    "wait what does that mean",
    "I don’t get this part",
    "can someone explain this",
    "why is it like that",
    "I’m confused",
    "how did you get that",
    "what are we supposed to do",
    "I don’t understand the directions",
    "this is confusing",
    "can you show steps",
    "what did you do first",
    "where did that number come from",
    "I’m stuck on this",
    "can someone help",
    "what does the question mean",
    "I don’t get the last part",
    "how do you start this",
    "this doesn’t make sense to me",
    "what are we solving for",
    "I’m lost",
    "can you explain it simpler",
    "I don’t understand the example",
    "what do we write",
    "how do you know that",
    "I’m confused about step 2",
    "what is the answer supposed to look like",
    "I don’t get it",
    "can someone explain again",
    "why is that the answer",
    "I don’t see how that works",
    "what do we do next",
    "this is hard",
    "can you break it down",
    "what did the teacher say about this",
    "I missed that part",
    "how do you know when to do that",
    "I don’t understand this problem",
    "can someone show me",
    "I’m not sure what to do",
    "what does this mean",
    "I don’t get the instructions",
    "why do we do that",
    "what is happening here",
    "I’m confused about this one",
    "can someone explain step by step",
    "I don’t get how you got that",
    "what’s the first step",
    "this part is confusing",
    "I need help with this",
    "can you explain it again",
]

CASUAL = [
    "lol",
    "that was funny",
    "same 😂",
    "wait what lol",
    "ok that’s kinda cool",
    "that’s funny",
    "lol yeah",
    "haha",
    "that’s weird",
    "ok but why",
    "that’s kinda confusing",
    "same lol",
    "that’s cool",
    "wait really",
    "ok I didn’t know that",
    "that’s interesting",
    "lol true",
    "that’s wild",
    "ok that’s good",
    "same here lol",
    "that’s nice",
    "ok cool",
    "that’s awesome",
    "lol I thought that too",
    "that’s kinda funny",
    "ok that makes sense",
    "that’s strange",
    "lol yeah same",
    "that’s cool though",
    "ok I like that",
    "that’s pretty good",
    "lol ok",
    "that’s interesting though",
    "same haha",
    "ok that works",
    "that’s actually funny",
    "lol I get it now",
    "ok yeah",
    "that’s cool I guess",
    "same lol",
    "ok nice",
    "that’s kinda cool",
    "lol alright",
    "that’s good",
    "ok that’s fine",
    "same here",
    "that’s interesting",
    "lol ok got it",
    "that’s funny though",
    "ok cool thanks",
]

THOUGHTFUL = [
    "I think the reason is because we learned that last week and it connects to this",
    "I think it works because you have to add before you multiply in this problem",
    "I remember the teacher said to check your work after solving it",
    "I think the answer is right because it follows the same pattern as the example",
    "I tried it a different way but got the same answer",
    "I think you have to break it into smaller parts first",
    "I noticed that if you change one number it changes the whole answer",
    "I think it makes sense because the steps match what we did in class",
    "I checked mine twice and got the same result",
    "I think the mistake is in the second step",
    "I tried solving it again and got something different",
    "I think we’re supposed to explain our thinking too",
    "I remember doing something like this before",
    "I think the important part is showing the work",
    "I tried using another method and it still worked",
    "I think we should double check the instructions",
    "I noticed the pattern repeats every time",
    "I think we need to write more detail in the answer",
    "I tried to explain it in my own words",
    "I think the answer is correct but the steps might be off",
    "I think it’s asking for more explanation",
    "I remember the example looked similar to this",
    "I think we should compare answers",
    "I tried solving it slower and it helped",
    "I think the key step is the middle part",
    "I noticed I made a small mistake earlier",
    "I think it’s easier if you draw it out",
    "I tried writing it differently and it made sense",
    "I think we should check the units too",
    "I remember the teacher said to be careful with that part",
    "I think the answer works because it follows the rule",
    "I noticed something different in this problem",
    "I think we should go step by step",
    "I tried explaining it to myself and it helped",
    "I think we might be overthinking it",
    "I noticed the numbers are similar to the example",
    "I think we should reread the question",
    "I tried it again and got the same answer",
    "I think it’s correct but we should check",
    "I noticed a pattern in the answers",
    "I think that’s the right idea",
    "I tried solving it a second time",
    "I think the explanation matters more here",
    "I noticed something small I missed before",
    "I think we should slow down on this one",
    "I tried comparing it to another problem",
    "I think the steps are correct",
    "I noticed the answer makes sense",
    "I think we’re close to the answer",
    "I tried fixing my mistake and it worked",
]


# --------------------------
# Personality + behavior
# --------------------------
PERSONALITIES = {
    "helper": ["THOUGHTFUL", "AGREEMENTS"],
    "confused": ["CONFUSED"],
    "social": ["CASUAL", "AGREEMENTS"],
    "quiet": ["AGREEMENTS"],
    "curious": ["CONFUSED", "THOUGHTFUL"],
    "class_clown": ["CASUAL"],
}


def generate_message(personality):
    style = random.choice(PERSONALITIES[personality])
    if style == "AGREEMENTS":
        return random.choice(AGREEMENTS)
    if style == "CONFUSED":
        return random.choice(CONFUSED)
    if style == "CASUAL":
        return random.choice(CASUAL)
    if style == "THOUGHTFUL":
        return random.choice(THOUGHTFUL)
    return "ok"


# --------------------------
# Seed start
# --------------------------
with sqlite3.connect(DB_PATH) as db:
    db.row_factory = sqlite3.Row

    teacher_id = insert_user(db, "Carter", "teacher", datetime(1985, 6, 1))

    names = [
        "Ava",
        "Liam-L",
        "Noah",
        "Emma",
        "Olivia",
        "Elijah",
        "Lucas",
        "Mia",
        "Amelia",
        "Harper",
        "Ethan",
        "Logan",
        "James",
        "Ella",
        "Abigail",
        "Henry",
        "Sofia",
        "Jackson",
        "Aiden",
        "Scarlett",
        "Grace",
        "Chloe",
        "Daniel",
        "Wyatt",
        "Lily",
    ]

    student_ids = []
    student_profiles = {}

    for n in names:
        uid = insert_user(
            db,
            n,
            "student",
            datetime(2011, random.randint(1, 12), random.randint(1, 28)),
        )
        student_ids.append(uid)
        student_profiles[uid] = random.choice(list(PERSONALITIES.keys()))

    cid = insert_classroom(db, teacher_id)

    for sid in student_ids:
        add_member(db, cid, sid)
    add_member(db, cid, teacher_id, "teacher")

    subjects = ["Math", "ELA", "Science", "Social Studies", "Gym"]
    topic_ids = {s: insert_topic(db, s) for s in subjects}

    start = datetime.now(timezone.utc) - timedelta(weeks=16)

    # inside joke that repeats
    inside_joke = "did anyone understand the homework or just me lol"

    for week in range(16):
        week_start = start + timedelta(weeks=week)

        safe_insert_post(
            db,
            teacher_id,
            topic_ids["Math"],
            "Weekly Update",
            f"Reminder: we’re working on {random.choice(['fractions', 'reading', 'experiments'])}. Ask questions!",
            school_time(week_start),
        )

        for subject in subjects:
            for _ in range(random.randint(3, 5)):
                author = random.choice(student_ids)

                personality = student_profiles[author]

                body = generate_message(personality)

                # occasional inside joke reuse
                if random.random() < 0.1:
                    body += " " + inside_joke

                post_id = safe_insert_post(
                    db,
                    author,
                    topic_ids[subject],
                    f"{subject} question",
                    body,
                    school_time(week_start),
                )

                # threaded conversation
                for _ in range(random.randint(4, 8)):
                    replier = random.choice(student_ids)
                    reply_personality = student_profiles[replier]

                    msg = generate_message(reply_personality)

                    # class clown behavior
                    if reply_personality == "class_clown" and random.random() < 0.4:
                        msg = random.choice(CASUAL) + " 😂"

                    safe_insert_post(
                        db,
                        replier,
                        topic_ids[subject],
                        f"Re: {subject}",
                        msg,
                        school_time(week_start),
                        parent_id=post_id,
                    )

        # --------------------------
        # Weekly assignments + submissions
        # --------------------------

        social_studies_responses = [
            "Sacagawea helped guide Lewis and Clark across the land. She traveled through rivers and mountains. One challenge was carrying her baby while helping the group. Her help mattered because they needed her to survive. A fun fact is she was really young.",
            "Henry Hudson was an explorer looking for a route to Asia. He traveled by ship through North America. His crew got mad and left him behind. His journey mattered because it helped map new places. The Hudson River is named after him.",
            "Pocahontas lived in Virginia and helped English settlers. She brought them food when they were struggling. One important event is when she helped keep peace. Her actions mattered because it helped both groups. Her real name was Matoaka.",
            "Hernan Cortes explored Mexico and fought the Aztecs. He had to battle a strong empire. His journey mattered because it changed history. One interesting thing is he burned his ships. That meant no one could leave.",
            "Lewis and Clark explored the west with help from Sacagawea. They traveled really far. It was hard because they didn’t know the land. Their journey mattered because they learned about new areas. They also made maps.",
            "Sacagawea helped them find food and talk to tribes. She went with them on a long trip. One challenge was surviving outside. Her role mattered because she helped guide them. She also had a baby with her.",
            "Henry Hudson went on a ship to explore. He wanted to find a faster way to Asia. His crew got mad at him. They left him on the water. His trip helped people learn about new places.",
            "Pocahontas helped settlers survive. She gave them food and helped them. One important moment is when she helped stop fighting. That mattered because it kept peace. She later went to England.",
            "Cortes went to Mexico and met the Aztecs. He fought them and took over. That was a big event. It mattered because it changed who controlled the land. He made big decisions.",
            "Lewis and Clark went west to explore land. They had to cross rivers and mountains. It was hard because it was unknown. Their journey helped map the country. They also met new tribes.",
            "Sacagawea helped guide an expedition. She knew the land better than them. One challenge was helping them survive. She mattered because they trusted her. She was very important.",
            "Henry Hudson explored by boat. He went through cold areas. His crew turned against him. That was a big problem. His name is now used for places.",
            "Pocahontas helped settlers and her people. She made peace between them. That was important. It helped both sides. She is still remembered today.",
            "Cortes was a Spanish explorer. He went to Mexico. He fought the Aztecs and won. That changed history. It affected many people.",
            "Lewis and Clark explored new land. They went far west. It was difficult to travel. Their journey helped America grow. They wrote things down.",
            "Sacagawea helped find safe paths. She traveled with explorers. It was hard because of weather. She helped them survive. She was very helpful.",
            "Henry Hudson looked for a route to Asia. He traveled by ship. His crew got upset. They left him. His trip helped with maps.",
            "Pocahontas helped settlers survive winter. She brought food. That helped them live. It mattered because they needed help. She is important in history.",
            "Cortes explored and fought in Mexico. He defeated the Aztecs. That was a big event. It changed the region. He was determined.",
            "Lewis and Clark traveled across land. They explored new places. It was dangerous. Their journey mattered because it helped others. They discovered a lot.",
            "Sacagawea guided explorers safely. She knew where to go. One challenge was the long journey. She mattered because she helped them succeed. She was brave.",
            "Henry Hudson explored rivers. He wanted a new route. His crew mutinied. That means they turned on him. His name is still used today.",
            "Pocahontas helped create peace. She helped settlers and her tribe. That was important. It stopped fighting. She is remembered in history.",
            "Cortes went to Mexico. He fought the Aztecs. That changed things a lot. It mattered because it changed power. He was an explorer.",
            "Lewis and Clark explored the west. They went on a long trip. It was hard work. Their journey helped map land. They are famous explorers.",
        ]
        for subject in subjects:
            due = week_start + timedelta(days=5)

            # Example: richer Social Studies assignment
            if subject == "Social Studies":
                instructions = (
                    "For this week’s assignment, choose a historical figure we studied "
                    "(such as Sacagawea, Pocahontas, Henry Hudson, or Hernán Cortés).\n\n"
                    "Write 3–5 sentences that include:\n"
                    "- Who they were\n"
                    "- Where they traveled or lived\n"
                    "- One challenge they faced\n"
                    "- Why they are important\n\n"
                    "Try to include one interesting or fun fact!"
                )
            else:
                instructions = (
                    f"Complete this week's {subject.lower()} work and try your best."
                )

            aid = insert_assignment(
                db,
                cid,
                f"{subject} Assignment Week {week + 1}",
                instructions,
                due,
            )

            for sid in student_ids:
                # 10% chnace student doesn't submit
                if random.random() < 0.1:
                    continue

                submit_time = rand_between(
                    week_start, due + timedelta(days=random.randint(0, 2))
                )

                # More natural student submissions
                if subject == "Social Studies":
                    submission_text = random.choice(social_studies_responses)
                else:
                    submission_text = random.choice(
                        [
                            f"I worked on this during class and finished the rest at home. {subject} is getting easier.",
                            f"This assignment was kind of hard but I tried my best. I think I understand it more now.",
                            f"I wasn’t sure at first but after looking at my notes it made more sense.",
                            f"I liked this one more than last week. It was actually kinda interesting.",
                            f"I had to redo part of this but I think it’s better now.",
                        ]
                    )

                insert_submission(
                    db,
                    aid,
                    sid,
                    submission_text,
                    submit_time,
                )
                if random.random() > 0.15:
                    grade_submission(db, aid, sid)
    print("Ultra-realistic semester seed complete ✔")
