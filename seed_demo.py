"""
SparK Demo Seed — Teacher Walkthrough (5th Grade, 25 Students)
===============================================================
Seeds a realistic 5th-grade classroom demo for presenting SparK to a teacher.

Includes:
  - 1 teacher account
  - 25 students (provisioned, QR-ready)
  - 1 classroom with join code
  - 5 topic channels
  - ~55 posts and replies across topics
  - 3 assignments (graded/past-due, active, upcoming)
  - submissions with grades and feedback
  - 2 flagged posts in the moderation queue (one auto-hidden)
  - 3 custom filtered words
  - reactions, bookmarks, follows, notifications

Usage:
    python seed_demo.py
    (run from the project root — same level as run.py)

The script is safe to re-run: it cleans all demo.* accounts before reseeding.
"""

import os
import sys
import sqlite3
import secrets
import random
from datetime import datetime, timedelta, timezone
from bcrypt import hashpw, gensalt

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = os.environ.get("DATABASE_URL", "spark_database.db")
if DB_PATH.startswith("sqlite:///"):
    DB_PATH = DB_PATH[len("sqlite:///") :]

NOW = datetime.now(timezone.utc)

REACTION_KEYS = ["love", "idea", "thinking", "nailed_it", "lit", "star", "fire"]


def ts(offset_hours=0, offset_days=0):
    dt = NOW - timedelta(hours=offset_hours, days=offset_days)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def make_hash(password: str) -> str:
    return hashpw(password.encode(), gensalt()).decode()


def make_qr_token():
    return secrets.token_urlsafe(32)


# ── Teacher ───────────────────────────────────────────────────────────────────
TEACHER = {
    "username": "demo.mspatel",
    "password": "SparKDemo2025!",
    "role": "teacher",
    "dob": "1988-04-12",
    "bio": "5th grade science & language arts @ Lincoln Elementary. Coffee-powered.",
}

# ── 25 Students ───────────────────────────────────────────────────────────────
STUDENTS = [
    {"first": "Aiden", "last": "Brooks", "dob": "2014-03-15", "pw": "sunnybird42"},
    {"first": "Maya", "last": "Chen", "dob": "2014-07-22", "pw": "happycloud81"},
    {"first": "Jordan", "last": "Davis", "dob": "2013-11-30", "pw": "brightstar56"},
    {"first": "Sofia", "last": "Garcia", "dob": "2014-01-08", "pw": "blueriver29"},
    {"first": "Elijah", "last": "Harris", "dob": "2013-09-17", "pw": "greenmoon73"},
    {"first": "Priya", "last": "Patel", "dob": "2014-05-03", "pw": "coolwind44"},
    {"first": "Noah", "last": "Robinson", "dob": "2013-12-21", "pw": "fastcloud67"},
    {"first": "Zoe", "last": "Thompson", "dob": "2014-08-14", "pw": "redleaf91"},
    {"first": "Liam", "last": "Walker", "dob": "2013-10-05", "pw": "quietlake35"},
    {"first": "Aaliyah", "last": "Young", "dob": "2014-02-28", "pw": "softpine58"},
    {"first": "Caleb", "last": "Moore", "dob": "2014-04-11", "pw": "boldwave19"},
    {"first": "Isabella", "last": "Martinez", "dob": "2013-08-25", "pw": "tinyrock63"},
    {"first": "Ethan", "last": "Anderson", "dob": "2014-06-18", "pw": "wildgrass77"},
    {"first": "Amara", "last": "Jackson", "dob": "2013-12-04", "pw": "deepblue31"},
    {"first": "Lucas", "last": "White", "dob": "2014-02-09", "pw": "quietfern48"},
    {"first": "Nadia", "last": "Taylor", "dob": "2013-10-30", "pw": "goldenoak52"},
    {"first": "Owen", "last": "Lee", "dob": "2014-07-07", "pw": "swiftrain84"},
    {"first": "Fatima", "last": "Ahmed", "dob": "2013-09-14", "pw": "clearsky27"},
    {"first": "Callie", "last": "Scott", "dob": "2014-03-29", "pw": "longpath66"},
    {"first": "Marcus", "last": "Turner", "dob": "2013-11-11", "pw": "ironleaf39"},
    {"first": "Lily", "last": "Nelson", "dob": "2014-05-20", "pw": "softcloud71"},
    {"first": "Darius", "last": "Hill", "dob": "2013-08-08", "pw": "redstone55"},
    {"first": "Elena", "last": "Rivera", "dob": "2014-01-17", "pw": "brightmoss43"},
    {"first": "Tobias", "last": "Mitchell", "dob": "2013-10-22", "pw": "swiftpeak88"},
    {"first": "Jasmine", "last": "Cooper", "dob": "2014-06-03", "pw": "coolbrook22"},
]

# ── Topics ────────────────────────────────────────────────────────────────────
TOPICS = [
    ("Science", "Ask questions and share discoveries about the natural world."),
    ("Reading", "Book discussions, reading responses, and literary debates."),
    ("Math", "Problem solving, tips, and math talk."),
    ("Current Events", "Age-appropriate news and world discussions."),
    ("Free Time", "Hobbies, games, fun stuff — keep it kind!"),
]

# ── Classroom ─────────────────────────────────────────────────────────────────
CLASSROOM = {
    "name": "Ms. Patel — Period 2 Science",
    "description": "Our class hub for discussions, assignments, and sharing cool science stuff.",
    "join_code": "XP4TYM",
}

# ── Posts ─────────────────────────────────────────────────────────────────────
POSTS = [
    # ── Science ──────────────────────────────────────────────────────────────
    (
        "Science",
        "Why is the sky blue?",
        "I was staring out the window during lunch and started wondering — why is the sky blue and not like, green or purple? Anyone know?",
        0,
        48,
    ),
    (
        "Science",
        "Re: Why is the sky blue?",
        "It has to do with how sunlight scatters! Blue light bounces around more in the atmosphere. Ms. Patel taught us this last week.",
        2,
        47,
    ),
    (
        "Science",
        "Re: Why is the sky blue?",
        "Also at sunset the light has to travel through more atmosphere so you get reds and oranges. I looked it up after class!",
        4,
        46,
    ),
    (
        "Science",
        "Re: Why is the sky blue?",
        "This is called Rayleigh scattering. The shorter the wavelength, the more it scatters — blue has a short wavelength!",
        11,
        45,
    ),
    (
        "Science",
        "Cool experiment — growing crystals",
        "Has anyone tried growing salt or sugar crystals at home? I watched a video and it looks super easy. Would love to try it for the science fair.",
        1,
        72,
    ),
    (
        "Science",
        "Re: Cool experiment — growing crystals",
        "I did this last summer! You need a string, hot water, and a lot of patience. The borax ones look the coolest.",
        6,
        71,
    ),
    (
        "Science",
        "Re: Cool experiment — growing crystals",
        "I tried sugar crystals and they worked! Took about 5 days. Just don't put them somewhere your little sibling can find them lol.",
        14,
        70,
    ),
    (
        "Science",
        "The water cycle blew my mind",
        "I never realized the water I drink might have been drunk by a dinosaur. The water cycle is kind of wild when you think about it.",
        3,
        36,
    ),
    (
        "Science",
        "Re: The water cycle blew my mind",
        "That fact lives rent-free in my head now. Thanks for the existential crisis.",
        7,
        35,
    ),
    (
        "Science",
        "Re: The water cycle blew my mind",
        "What if the water was once inside a volcano. We're basically drinking volcano water.",
        20,
        34,
    ),
    (
        "Science",
        "Re: The water cycle blew my mind",
        "Okay I am never drinking water again.",
        22,
        33,
    ),
    (
        "Science",
        "Eclipse next month — can we watch it?",
        "There's supposed to be a partial solar eclipse visible from our state next month. Can we watch it from the school yard?",
        7,
        30,
    ),
    (
        "Science",
        "Re: Eclipse next month — can we watch it?",
        "We need those special glasses though. My mom said regular sunglasses won't work and you can hurt your eyes.",
        2,
        29,
    ),
    (
        "Science",
        "Re: Eclipse next month — can we watch it?",
        "I really hope we can do this. Watching science happen in real life is so much better than a YouTube video.",
        "teacher",
        28,
    ),
    (
        "Science",
        "Why do leaves change color in fall?",
        "We just talked about photosynthesis and now I'm wondering — why do leaves turn red and orange in fall? Is it related?",
        16,
        55,
    ),
    (
        "Science",
        "Re: Why do leaves change color in fall?",
        "Yes! When there's less sunlight the tree stops making chlorophyll (the green stuff) and the other colors that were always there start to show.",
        5,
        54,
    ),
    (
        "Science",
        "Re: Why do leaves change color in fall?",
        "So the orange and red were always hiding under the green? That's actually really cool.",
        23,
        53,
    ),
    # ── Reading ───────────────────────────────────────────────────────────────
    (
        "Reading",
        "Hatchet — best survival moment?",
        "We're reading Hatchet and I want to know what everyone thinks is the coolest survival move Brian makes. Mine is when he figures out fire.",
        2,
        96,
    ),
    (
        "Reading",
        "Re: Hatchet — best survival moment?",
        "When he makes the bow and arrow! That takes so much patience. I would have given up after five minutes.",
        5,
        95,
    ),
    (
        "Reading",
        "Re: Hatchet — best survival moment?",
        "Honestly just surviving the first night. No food, no shelter, no idea what to do. I'd be crying the whole time.",
        9,
        94,
    ),
    (
        "Reading",
        "Re: Hatchet — best survival moment?",
        "When he finally catches a fish. I read that part really slowly because I wanted him to succeed so badly.",
        13,
        93,
    ),
    (
        "Reading",
        "Re: Hatchet — best survival moment?",
        "When he figures out the foolbirds. He keeps missing and then realizes he has to aim at the body not the head. That's real problem solving.",
        18,
        92,
    ),
    (
        "Reading",
        "Words I had to look up in Hatchet",
        "Making a list: 'morose', 'gnawed', 'perimeter'. Anyone else keeping track? It's actually kind of fun.",
        8,
        60,
    ),
    (
        "Reading",
        "Re: Words I had to look up in Hatchet",
        "I do this too! I use a little notebook. My word was 'gambit' — it means a clever opening move.",
        1,
        59,
    ),
    (
        "Reading",
        "Re: Words I had to look up in Hatchet",
        "'Tundra' confused me for a second. I kept imagining it wrong.",
        21,
        58,
    ),
    (
        "Reading",
        "Should Brian have stayed near the crash site?",
        "Would Brian have been rescued faster if he stayed where the plane went down instead of wandering? What do you think?",
        12,
        40,
    ),
    (
        "Reading",
        "Re: Should Brian have stayed near the crash site?",
        "He couldn't stay because the plane sank. But near the lake was smart because rescuers would follow water.",
        3,
        39,
    ),
    (
        "Reading",
        "Re: Should Brian have stayed near the crash site?",
        "I think he made the best decisions he could with zero information. That's what impressed me most about the book.",
        17,
        38,
    ),
    # ── Math ──────────────────────────────────────────────────────────────────
    (
        "Math",
        "Long division is evil",
        "Can someone explain long division again? I get lost right after the first subtraction step every time.",
        6,
        84,
    ),
    (
        "Math",
        "Re: Long division is evil",
        "The trick that helped me: Does McDonald's Sell Cheeseburgers — Divide, Multiply, Subtract, Check, Bring down. Silly but it works!",
        3,
        83,
    ),
    (
        "Math",
        "Re: Long division is evil",
        "Khan Academy has a really good video on it. Search 'long division for beginners'. Saved my homework last Tuesday.",
        0,
        82,
    ),
    (
        "Math",
        "Re: Long division is evil",
        "My dad showed me to just go one digit at a time and not look at the whole number. Total game changer.",
        15,
        81,
    ),
    (
        "Math",
        "Fractions tip that actually helped me",
        "When adding fractions, always find the least common denominator FIRST before doing anything else. My dad showed me and now it clicks.",
        4,
        55,
    ),
    (
        "Math",
        "Re: Fractions tip that actually helped me",
        "This is the step everyone skips and then wonders why the answer is wrong. Great tip.",
        10,
        54,
    ),
    (
        "Math",
        "Is there a faster way to do multiplication?",
        "My older sister showed me something called the lattice method and it looks weird but she says it's faster. Has anyone tried it?",
        19,
        62,
    ),
    (
        "Math",
        "Re: Is there a faster way to do multiplication?",
        "I tried lattice and it confused me more. The area model makes more sense to me visually.",
        24,
        61,
    ),
    (
        "Math",
        "Re: Is there a faster way to do multiplication?",
        "I just memorized everything up to 12x12 and now big multiplication is easier. Old fashioned but it works.",
        8,
        60,
    ),
    # ── Current Events ────────────────────────────────────────────────────────
    (
        "Current Events",
        "Did you hear about the new space mission?",
        "There's a new mission going to the moon planned for next year. A crew of astronauts will land and do experiments. So cool.",
        11,
        72,
    ),
    (
        "Current Events",
        "Re: Did you hear about the new space mission?",
        "They're going to the south pole of the moon where there might be frozen water. That connects to our water cycle unit!",
        5,
        71,
    ),
    (
        "Current Events",
        "Re: Did you hear about the new space mission?",
        "If they find water on the moon does that mean people could live there someday? I have so many questions.",
        22,
        70,
    ),
    (
        "Current Events",
        "Should kids have less homework?",
        "I read an article that said too much homework doesn't help learning for elementary students. Thoughts? Asking for a friend.",
        16,
        50,
    ),
    (
        "Current Events",
        "Re: Should kids have less homework?",
        "I think some homework is good because it helps me remember stuff. But hours and hours is too much.",
        9,
        49,
    ),
    (
        "Current Events",
        "Re: Should kids have less homework?",
        "The research actually supports shorter focused practice over lots of homework. Quality over quantity.",
        "teacher",
        48,
    ),
    # ── Free Time ─────────────────────────────────────────────────────────────
    (
        "Free Time",
        "What's everyone playing right now?",
        "I've been really into Minecraft survival mode lately. Building an underground city. What are you all playing?",
        5,
        120,
    ),
    (
        "Free Time",
        "Re: What's everyone playing right now?",
        "Mostly reading lol. But also Blooket for math practice.",
        8,
        119,
    ),
    (
        "Free Time",
        "Re: What's everyone playing right now?",
        "Chess club after school on Tuesdays! Mr. Kim runs it and he's really patient with beginners.",
        3,
        118,
    ),
    (
        "Free Time",
        "Re: What's everyone playing right now?",
        "I got really into building model rockets with my dad. We launched one last weekend and it went SO high.",
        20,
        117,
    ),
    (
        "Free Time",
        "Re: What's everyone playing right now?",
        "Coding! I've been learning Scratch and I made a little game with a cat that avoids falling blocks.",
        14,
        116,
    ),
    (
        "Free Time",
        "Book recommendations?",
        "Finished our class book early and need something new. I like adventure and mystery. Any suggestions?",
        9,
        45,
    ),
    (
        "Free Time",
        "Re: Book recommendations?",
        "Try 'The Mysterious Benedict Society' — adventure and mystery and the characters are amazing.",
        1,
        44,
    ),
    (
        "Free Time",
        "Re: Book recommendations?",
        "Percy Jackson if you haven't already. You'll read the whole series in a week.",
        0,
        43,
    ),
    (
        "Free Time",
        "Re: Book recommendations?",
        "'Holes' by Louis Sachar. It's short but everything connects at the end.",
        23,
        42,
    ),
    (
        "Free Time",
        "Re: Book recommendations?",
        "The Ranger's Apprentice series. It's long but every book is better than the last.",
        17,
        41,
    ),
    # ── Posts to be flagged ───────────────────────────────────────────────────
    (
        "Free Time",
        "This app is so dumb",
        "Why do we even have to use this. It's stupid and boring. Nobody cares about any of this.",
        6,
        10,
    ),
    (
        "Free Time",
        "Re: This app is so dumb",
        "That's kind of rude. Some of us actually like it and work hard on our posts.",
        2,
        9,
    ),
]

# ── Assignments ───────────────────────────────────────────────────────────────
ASSIGNMENTS = [
    {
        "title": "Water Cycle Diagram",
        "instructions": (
            "Draw and label a diagram of the water cycle. "
            "Your diagram must include: evaporation, condensation, precipitation, and collection. "
            "Write 2-3 sentences explaining each stage in your own words. "
            "You may submit a photo of a hand-drawn diagram or a digital version."
        ),
        "due_offset_days": -3,
    },
    {
        "title": "Hatchet — Survival Reflection",
        "instructions": (
            "Write a short reflection (150-200 words) answering: "
            "If you were Brian in Hatchet, what would be the hardest part of surviving alone? "
            "Use at least one specific detail from the book to support your answer."
        ),
        "due_offset_days": 2,
    },
    {
        "title": "Math Problem Set — Fractions",
        "instructions": (
            "Complete problems 1-15 on the fractions worksheet. "
            "Show all your work — answers without work shown will not receive full credit. "
            "If you get stuck, write down what step you got to and what confused you."
        ),
        "due_offset_days": 7,
    },
]

# ── Submissions — Water Cycle ─────────────────────────────────────────────────
SUBMISSIONS_WATER_CYCLE = [
    (
        0,
        "Evaporation is when water turns into vapor from heat. Condensation is when vapor cools into clouds. Precipitation is rain or snow falling down. Collection is when water gathers in oceans and lakes and the cycle starts again. I drew arrows showing each stage. [diagram attached]",
        "A",
        "Excellent work Aiden! Your labels are clear and your explanations show real understanding. Great detail on the collection phase.",
    ),
    (
        1,
        "I drew the water cycle and labeled all four parts. Evaporation goes up, condensation makes clouds, precipitation is rain, and collection is rivers and oceans.",
        "B+",
        "Good job Maya! Your diagram is well-organized. Next time try to expand your written explanations — aim for 2-3 full sentences per stage.",
    ),
    (
        2,
        "Evaporation: water heats up and becomes gas. Condensation: gas cools and becomes water droplets in clouds. Precipitation: water falls as rain snow or hail. Collection: water gathers in lakes rivers and oceans and the cycle starts again.",
        "A-",
        "Great explanations Jordan! Very clear and in your own words. One small note — your condensation arrow is pointing the wrong direction on the diagram.",
    ),
    (
        3,
        "I did the diagram but I'm not sure if I got condensation right. Is it when the clouds form? I drew it that way.",
        None,
        None,
    ),
    (
        4,
        "Here is my water cycle. Evaporation is heat making water go up. Condensation makes clouds. Precipitation is weather. Collection is oceans.",
        "B",
        "Good effort Elijah! Your core understanding is there. 'Precipitation is weather' is a little vague — it specifically means water falling from clouds. See me if you want to talk through it.",
    ),
    (
        5,
        "Evaporation happens when the sun heats water and turns it into water vapor. Condensation is when vapor cools and forms clouds. Precipitation is when water falls as rain, snow, or sleet. Collection is when water returns to lakes and oceans.",
        "A",
        "Perfect Priya! Clear, complete, and well-written. Your diagram was also very neat.",
    ),
    (
        7,
        "The water cycle has four main steps. Evaporation turns water to vapor. Condensation forms clouds. Precipitation means rain and snow. Collection is lakes and oceans.",
        "B+",
        "Solid work Zoe! Good understanding of all four stages. Adding a little more detail to each explanation would push this to an A.",
    ),
    (
        10,
        "Evaporation: when the sun heats water and it rises as vapor. Condensation: vapor cools and becomes clouds. Precipitation: water falls back to earth. Collection: water collects in bodies of water.",
        "A-",
        "Well done Caleb! Accurate and clear throughout. Nice diagram too.",
    ),
    (
        11,
        "Water evaporates from oceans and lakes when it gets warm. Then it condenses into clouds up high. Then it rains or snows back down. Then it collects again and the whole thing repeats.",
        "B",
        "Good Isabella! You have the main idea. Try to use the scientific vocabulary words more — evaporation, condensation, precipitation.",
    ),
    (
        12,
        "I drew a mountain with a river. Evaporation is at the ocean, condensation is the clouds over the mountain, precipitation is rain on the mountain, and collection is the river going back to the ocean.",
        "A",
        "Really creative diagram Ethan! Using a landscape to show the full cycle was smart. Excellent work.",
    ),
    (
        13,
        "Evaporation is when water goes into the air. Condensation is clouds forming. Precipitation is rain. Collection is puddles and lakes.",
        "B-",
        "You've got the basics Amara! Your explanations are a bit short — try to write 2-3 sentences for each stage to show more of your thinking.",
    ),
    (
        15,
        "I really liked learning about the water cycle. Evaporation is water becoming vapor when heated. Condensation is vapor becoming droplets in clouds. Precipitation is water falling from clouds as rain or snow. Collection is water returning to oceans, lakes, and rivers.",
        "A",
        "Excellent Nadia! Thorough, accurate, and clearly explained. Your enthusiasm for the topic comes through.",
    ),
    (
        16,
        "The water cycle is how water moves through Earth. First it evaporates from heat. Then it condenses into clouds. Then precipitation brings it back down. Then it collects in water bodies.",
        "B+",
        "Good work Owen! Logical flow and accurate descriptions. Just a touch more detail would make this an A.",
    ),
    (
        17,
        "Evaporation happens at the surface of water when it's heated. Condensation happens when water vapor rises and cools. Precipitation is rain, sleet, or snow. Collection is when water returns to lakes and oceans.",
        "A-",
        "Very well done Fatima! Accurate and well-described. Your diagram was one of the clearest I received.",
    ),
    (
        19,
        "The sun heats the water and makes it evaporate. The vapor goes up and gets cold and condenses into clouds. Then it falls down as precipitation. Then it collects and evaporates again.",
        "B+",
        "Nice work Marcus! Good explanation of the continuous nature of the cycle. Try to include more detail on the collection stage.",
    ),
]

# ── Submissions — Hatchet ─────────────────────────────────────────────────────
SUBMISSIONS_HATCHET = [
    (
        0,
        "If I were Brian the hardest part would be finding food. In the book Brian spends days figuring out how to eat and even when he finds berries some of them make him sick. I think hunger is scarier than being cold because it affects how clearly you can think. Brian almost gave up several times and I completely understand why.",
    ),
    (
        7,
        "The loneliness would be the hardest part for me. Brian doesn't have anyone to talk to and that has to be mentally exhausting. In the book he starts talking to himself just to hear a voice. I think humans need other people around them and being totally alone with no end in sight would be the scariest thing of all.",
    ),
    (
        11,
        "I think the hardest part would be not knowing if anyone is coming to rescue you. Brian has no way to send a message or know if people are searching for him. In the book he almost gives up hope after the first plane flies over without seeing him. That uncertainty would break me.",
    ),
    (
        15,
        "Not knowing what is dangerous would scare me the most. Brian has to figure out which berries won't make him sick and which animals to avoid. He gets porcupine quills in his leg just because he didn't know. Every mistake has real consequences and there's no one to ask for help.",
    ),
]

FILTERED_WORDS = ["stupid", "dumb", "hate"]


# ── Database helpers ──────────────────────────────────────────────────────────


def connect(path):
    db = sqlite3.connect(
        path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = OFF")
    return db


def clean(db):
    all_usernames = [TEACHER["username"]] + [
        f"demo.{s['first'].lower()}.{s['last'].lower()}" for s in STUDENTS
    ]
    placeholders = ",".join("?" * len(all_usernames))
    rows = db.execute(
        f"SELECT id FROM users WHERE username IN ({placeholders})", all_usernames
    ).fetchall()
    user_ids = [r[0] for r in rows]
    if not user_ids:
        return

    up = ",".join("?" * len(user_ids))

    db.execute(f"DELETE FROM reactions WHERE user_id IN ({up})", user_ids)
    db.execute(f"DELETE FROM bookmarks WHERE user_id IN ({up})", user_ids)
    db.execute(
        f"DELETE FROM follows WHERE follower_id IN ({up}) OR followed_id IN ({up})",
        user_ids + user_ids,
    )
    db.execute(f"DELETE FROM notifications WHERE user_id IN ({up})", user_ids)
    db.execute(f"DELETE FROM classroom_members WHERE user_id IN ({up})", user_ids)

    teacher_rows = db.execute(
        "SELECT id FROM users WHERE username = ?", (TEACHER["username"],)
    ).fetchall()
    if teacher_rows:
        tid = teacher_rows[0][0]
        classroom_rows = db.execute(
            "SELECT id FROM classrooms WHERE teacher_id = ?", (tid,)
        ).fetchall()
        if classroom_rows:
            cids = [r[0] for r in classroom_rows]
            cp = ",".join("?" * len(cids))
            arows = db.execute(
                f"SELECT id FROM assignments WHERE classroom_id IN ({cp})", cids
            ).fetchall()
            if arows:
                aids = [r[0] for r in arows]
                ap = ",".join("?" * len(aids))
                db.execute(
                    f"DELETE FROM submissions WHERE assignment_id IN ({ap})", aids
                )
            db.execute(f"DELETE FROM assignments WHERE classroom_id IN ({cp})", cids)
            db.execute(
                f"DELETE FROM classroom_members WHERE classroom_id IN ({cp})", cids
            )
            db.execute(f"DELETE FROM classrooms WHERE id IN ({cp})", cids)

    post_rows = db.execute(
        f"SELECT id FROM posts WHERE user_id IN ({up})", user_ids
    ).fetchall()
    if post_rows:
        pids = [r[0] for r in post_rows]
        pp = ",".join("?" * len(pids))
        db.execute(f"DELETE FROM reports WHERE post_id IN ({pp})", pids)
        db.execute(f"DELETE FROM reactions WHERE post_id IN ({pp})", pids)
        db.execute(f"DELETE FROM bookmarks WHERE post_id IN ({pp})", pids)
        db.execute(f"DELETE FROM posts WHERE id IN ({pp})", pids)

    fw_p = ",".join("?" * len(FILTERED_WORDS))
    db.execute(f"DELETE FROM filtered_words WHERE word IN ({fw_p})", FILTERED_WORDS)
    db.execute(f"DELETE FROM users WHERE id IN ({up})", user_ids)
    db.commit()


# ── Seeder ────────────────────────────────────────────────────────────────────


def seed(db):
    # Topics
    topic_ids = {}
    for name, desc in TOPICS:
        row = db.execute("SELECT id FROM topics WHERE name = ?", (name,)).fetchone()
        if row:
            topic_ids[name] = row[0]
        else:
            cur = db.execute(
                "INSERT INTO topics (name, description) VALUES (?, ?)", (name, desc)
            )
            topic_ids[name] = cur.lastrowid

    # Teacher
    teacher_id = db.execute(
        """INSERT INTO users (username, password_hash, dob, bio, role, coppa_status, provisional, onboarded, created_at)
           VALUES (?, ?, ?, ?, 'teacher', 'approved', 0, 1, ?)""",
        (
            TEACHER["username"],
            make_hash(TEACHER["password"]),
            TEACHER["dob"],
            TEACHER["bio"],
            ts(300),
        ),
    ).lastrowid

    # Students
    student_ids = []
    for s in STUDENTS:
        uname = f"demo.{s['first'].lower()}.{s['last'].lower()}"
        sid = db.execute(
            """INSERT INTO users
               (username, password_hash, dob, role, coppa_status, provisional, onboarded, qr_token, created_by, created_at)
               VALUES (?, ?, ?, 'student', 'approved', 1, 1, ?, ?, ?)""",
            (uname, make_hash(s["pw"]), s["dob"], make_qr_token(), teacher_id, ts(168)),
        ).lastrowid
        student_ids.append(sid)

    # Classroom
    classroom_id = db.execute(
        """INSERT INTO classrooms (teacher_id, name, description, join_code, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (
            teacher_id,
            CLASSROOM["name"],
            CLASSROOM["description"],
            CLASSROOM["join_code"],
            ts(168),
        ),
    ).lastrowid

    db.execute(
        "INSERT INTO classroom_members (classroom_id, user_id, role, joined_at) VALUES (?, ?, 'teacher', ?)",
        (classroom_id, teacher_id, ts(168)),
    )
    for sid in student_ids:
        db.execute(
            "INSERT INTO classroom_members (classroom_id, user_id, role, joined_at) VALUES (?, ?, 'student', ?)",
            (classroom_id, sid, ts(160)),
        )

    # Posts
    post_id_map = {}
    reply_targets = {}

    for topic_name, title, body, author, hours in POSTS:
        uid = teacher_id if author == "teacher" else student_ids[author]
        parent_id = None
        if title.startswith("Re: "):
            parent_id = reply_targets.get(title[4:])

        pid = db.execute(
            """INSERT INTO posts (user_id, topic_id, title, body, parent_id, classroom_id, created_at, is_hidden)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                uid,
                topic_ids[topic_name],
                title,
                body,
                parent_id,
                classroom_id,
                ts(hours),
            ),
        ).lastrowid

        post_id_map[title] = pid
        if not title.startswith("Re: "):
            reply_targets[title] = pid
        if parent_id:
            db.execute(
                "UPDATE posts SET reply_count = reply_count + 1 WHERE id = ?",
                (parent_id,),
            )

    # Reactions
    popular = [
        "Why is the sky blue?",
        "Cool experiment — growing crystals",
        "The water cycle blew my mind",
        "Hatchet — best survival moment?",
        "Long division is evil",
        "What's everyone playing right now?",
        "Book recommendations?",
        "Why do leaves change color in fall?",
        "Should kids have less homework?",
        "Is there a faster way to do multiplication?",
    ]
    for title in popular:
        if title not in post_id_map:
            continue
        pid = post_id_map[title]
        shuffled = list(student_ids)
        random.shuffle(shuffled)
        count = random.randint(6, 16)
        for reactor in shuffled[:count]:
            reaction = random.choice(REACTION_KEYS)
            try:
                db.execute(
                    "INSERT INTO reactions (post_id, user_id, reaction, created_at) VALUES (?, ?, ?, ?)",
                    (pid, reactor, reaction, ts(random.randint(1, 48))),
                )
            except sqlite3.IntegrityError:
                pass

    # Bookmarks
    for title in [
        "Cool experiment — growing crystals",
        "Words I had to look up in Hatchet",
        "Fractions tip that actually helped me",
    ]:
        if title in post_id_map:
            try:
                db.execute(
                    "INSERT INTO bookmarks (user_id, post_id, created_at) VALUES (?, ?, ?)",
                    (student_ids[0], post_id_map[title], ts(24)),
                )
            except sqlite3.IntegrityError:
                pass

    # Follows
    pairs = [
        (0, 1),
        (0, 2),
        (1, 0),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 11),
        (11, 12),
        (12, 13),
        (13, 14),
        (14, 15),
        (15, 16),
        (16, 17),
        (17, 18),
        (18, 19),
        (19, 20),
        (20, 21),
        (21, 22),
        (22, 23),
        (23, 24),
        (24, 0),
        (0, 5),
        (1, 10),
        (2, 15),
        (3, 20),
        (4, 9),
        (5, 14),
        (6, 19),
        (7, 24),
        (8, 3),
    ]
    for a, b in pairs:
        try:
            db.execute(
                "INSERT INTO follows (follower_id, followed_id, create_at) VALUES (?, ?, ?)",
                (student_ids[a], student_ids[b], ts(72)),
            )
        except sqlite3.IntegrityError:
            pass

    # Moderation
    flagged_pid = post_id_map.get("This app is so dumb")
    if flagged_pid:
        for reporter in [student_ids[2], student_ids[7], student_ids[9]]:
            db.execute(
                """INSERT INTO reports (post_id, reported_by_user_id, reason, description, status, created_at)
                   VALUES (?, ?, 'mean_language', 'This post is being unkind about our class platform.', 'pending', ?)""",
                (flagged_pid, reporter, ts(8)),
            )
        db.execute("UPDATE posts SET is_hidden = 1 WHERE id = ?", (flagged_pid,))

    reply_flagged = post_id_map.get("Re: This app is so dumb")
    if reply_flagged:
        db.execute(
            """INSERT INTO reports (post_id, reported_by_user_id, reason, description, status, created_at)
               VALUES (?, ?, 'mean_language', 'Follow-up also seems unkind.', 'pending', ?)""",
            (reply_flagged, student_ids[3], ts(7)),
        )

    # Filtered words
    for word in FILTERED_WORDS:
        try:
            db.execute(
                "INSERT INTO filtered_words (word, added_by, created_at) VALUES (?, ?, ?)",
                (word, teacher_id, ts(120)),
            )
        except sqlite3.IntegrityError:
            pass

    # Assignments
    assignment_ids = []
    for asn in ASSIGNMENTS:
        due = (NOW + timedelta(days=asn["due_offset_days"])).strftime("%Y-%m-%d")
        aid = db.execute(
            """INSERT INTO assignments (classroom_id, title, instructions, due_date, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (classroom_id, asn["title"], asn["instructions"], due, ts(200)),
        ).lastrowid
        assignment_ids.append(aid)

    water_cycle_aid, hatchet_aid, _ = assignment_ids

    # Submissions — Water Cycle
    for s_idx, body, grade, feedback in SUBMISSIONS_WATER_CYCLE:
        db.execute(
            """INSERT INTO submissions (assignment_id, user_id, body, grade, feedback, submitted_at, graded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                water_cycle_aid,
                student_ids[s_idx],
                body,
                grade,
                feedback or "",
                ts(72),
                ts(24) if grade else None,
            ),
        )

    # Submissions — Hatchet
    for s_idx, body in SUBMISSIONS_HATCHET:
        db.execute(
            """INSERT INTO submissions (assignment_id, user_id, body, grade, feedback, submitted_at, graded_at)
               VALUES (?, ?, ?, NULL, '', ?, NULL)""",
            (hatchet_aid, student_ids[s_idx], body, ts(10)),
        )

    # Notifications
    graded_indices = [0, 1, 2, 4, 5, 7, 10, 11, 12, 13, 15, 16, 17, 19]
    for s_idx in graded_indices:
        db.execute(
            """INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
               VALUES (?, 'grade', 'Your Water Cycle Diagram has been graded!', '/classroom/assignments', 0, ?)""",
            (student_ids[s_idx], ts(23)),
        )
    db.execute(
        """INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
           VALUES (?, 'reply', 'Maya replied to your post in Science.', '/posts/1', 0, ?)""",
        (student_ids[0], ts(47)),
    )
    db.execute(
        """INSERT INTO notifications (user_id, type, message, link, is_read, created_at)
           VALUES (?, 'reply', 'Someone replied to your post in Free Time.', '/posts/free-time', 1, ?)""",
        (student_ids[5], ts(119)),
    )

    db.commit()
    return {
        "teacher": TEACHER["username"],
        "teacher_password": TEACHER["password"],
        "classroom_join_code": CLASSROOM["join_code"],
        "student_count": len(student_ids),
        "post_count": len(POSTS),
        "assignment_count": len(assignment_ids),
        "graded_submissions": len([s for s in SUBMISSIONS_WATER_CYCLE if s[2]]),
        "pending_submissions": len([s for s in SUBMISSIONS_WATER_CYCLE if not s[2]])
        + len(SUBMISSIONS_HATCHET),
        "missing_count": 25 - len(SUBMISSIONS_WATER_CYCLE),
        "students": [
            f"demo.{s['first'].lower()}.{s['last'].lower()} / {s['pw']}"
            for s in STUDENTS
        ],
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    if not os.path.exists(DB_PATH) and DB_PATH != ":memory:":
        print(f"\n⚠️  Database not found at: {DB_PATH}")
        print("   Run from your project root, or set DATABASE_URL.\n")
        sys.exit(1)

    db = connect(DB_PATH)

    print("🧹  Cleaning existing demo data...")
    clean(db)

    print("🌱  Seeding demo data...")
    r = seed(db)
    db.close()

    print("\n✅  Demo seed complete!\n")
    print(f"  Teacher:          {r['teacher']}  /  {r['teacher_password']}")
    print(f"  Classroom code:   {r['classroom_join_code']}")
    print(f"  Students:         {r['student_count']}")
    print(f"  Posts:            {r['post_count']}")
    print(f"  Assignments:      {r['assignment_count']}")
    print(
        f"  Graded:           {r['graded_submissions']}  |  Pending grade: {r['pending_submissions']}  |  Missing: {r['missing_count']}"
    )
    print("\n  Student logins:")
    for s in r["students"]:
        print(f"    {s}")
    print()


if __name__ == "__main__":
    main()
