# scripts/admin.py

import sys
import os
import bcrypt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import get_db

app = create_app()

current_user_id = None
current_username = None


def menu():
    user_label = f" (acting as: {current_username})" if current_username else ""
    print(f"\n== devstack admin{user_label} ==")
    print("--- users ---")
    print("1.  list users & their posts")
    print("2.  create user")
    print("3.  delete user")
    print("4.  switch active user")
    print("--- posts ---")
    print("5.  create post")
    print("6.  delete post")
    print("7.  reply to post")
    print("--- social ---")
    print("8.  follow user")
    print("9.  unfollow user")
    print("10. list followers/following")
    print("--- topics ---")
    print("11. list topics")
    print("12. create topic")
    print("13. delete topic")
    print("--- db ---")
    print("14. reset database")
    print("15. auto-seed test data")
    print("==== need to add ===")
    print("#. submenu for testing")
    print("#. - test actions (e.g. auto (un)follow/delay/(un)follow)")

    print("0.  exit")
    return input("\n> ").strip()


def list_users_and_posts(db):
    users = db.execute("SELECT id, username, bio FROM users ORDER BY id").fetchall()
    if not users:
        print("no users found.")
        return
    for u in users:
        marker = " *" if u["id"] == current_user_id else ""
        followers = db.execute(
            "SELECT COUNT(*) FROM follows WHERE followed_id=?", (u["id"],)
        ).fetchone()[0]
        following = db.execute(
            "SELECT COUNT(*) FROM follows WHERE follower_id=?", (u["id"],)
        ).fetchone()[0]
        print(f"\n┌─ [{u['id']}] {u['username']}{marker}")
        print(f"│  bio: {u['bio'] or '(none)'}")
        print(f"│  followers: {followers}  following: {following}")
        posts = db.execute(
            """
            SELECT id, title FROM posts
            WHERE user_id=? AND parent_id IS NULL
            ORDER BY id DESC LIMIT 10
        """,
            (u["id"],),
        ).fetchall()
        if posts:
            for p in posts:
                print(f"│    post [{p['id']}] {p['title'][:50]}")
        else:
            print("│    (no posts)")
    print()


def create_user(db):
    username = input("username: ").strip()
    if not username:
        print("username cannot be empty.")
        return
    password = input("password: ").strip()
    if not password:
        print("password cannot be empty.")
        return
    bio = input("bio (optional): ").strip()
    existing = db.execute(
        "SELECT id FROM users WHERE username=?", (username,)
    ).fetchone()
    if existing:
        print(f"user '{username}' already exists.")
        return
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    db.execute(
        "INSERT INTO users (username, password_hash, bio) VALUES (?,?,?)",
        (username, password_hash, bio),
    )
    db.commit()
    print(f"user '{username}' created.")


def delete_user(db):
    list_users_and_posts(db)
    user_id = input("enter user id to delete: ").strip()
    if not user_id.isdigit():
        print("invalid id.")
        return
    confirm = input(f"delete user {user_id} and all their data? (y/n): ")
    if confirm.lower() != "y":
        print("cancelled.")
        return
    for table in ("votes", "bookmarks", "follows", "notifications", "posts"):
        db.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM follows WHERE followed_id=?", (user_id,))
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    print(f"user {user_id} deleted.")


def switch_user(db):
    global current_user_id, current_username
    users = db.execute("SELECT id, username FROM users ORDER BY id").fetchall()
    if not users:
        print("no users found.")
        return
    print()
    for u in users:
        marker = " *" if u["id"] == current_user_id else ""
        print(f"  [{u['id']}] {u['username']}{marker}")
    print()
    user_id = input("enter user id (or 0 to clear): ").strip()
    if user_id == "0":
        current_user_id = None
        current_username = None
        print("active user cleared.")
        return
    if not user_id.isdigit():
        print("invalid id.")
        return
    row = db.execute("SELECT id, username FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        print("user not found.")
        return
    current_user_id = row["id"]
    current_username = row["username"]
    print(f"switched to '{current_username}'.")


def create_post(db):
    if not current_user_id:
        print("no active user. use option 4 to switch user first.")
        return
    print(f"creating post as: {current_username}")
    title = input("title: ").strip()
    if not title:
        print("title cannot be empty.")
        return
    body = input("body: ").strip()
    if not body:
        print("body cannot be empty.")
        return
    topic = input("topic name (optional): ").strip()
    topic_id = None
    if topic:
        row = db.execute("SELECT id FROM topics WHERE name=?", (topic,)).fetchone()
        if row:
            topic_id = row["id"]
        else:
            create = input(f"topic '{topic}' not found. create it? (y/n): ")
            if create.lower() == "y":
                db.execute(
                    "INSERT INTO topics (name, description) VALUES (?,?)", (topic, "")
                )
                db.commit()
                topic_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                print(f"topic '{topic}' created.")
    db.execute(
        "INSERT INTO posts (user_id, title, body, topic_id) VALUES (?,?,?,?)",
        (current_user_id, title, body, topic_id),
    )
    db.commit()
    print(f"post '{title}' created.")


def delete_post(db):
    posts = db.execute("""
        SELECT posts.id, users.username, posts.title
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.parent_id IS NULL
        ORDER BY users.username, posts.id DESC
        LIMIT 50
    """).fetchall()
    if not posts:
        print("no posts found.")
        return
    current_author = None
    for p in posts:
        if p["username"] != current_author:
            current_author = p["username"]
            print(f"\n  {current_author}")
        print(f"    [{p['id']}] {p['title'][:50]}")
    print()
    post_id = input("enter post id to delete: ").strip()
    if not post_id.isdigit():
        print("invalid id.")
        return
    confirm = input(f"delete post {post_id} and all its replies? (y/n): ")
    if confirm.lower() != "y":
        print("cancelled.")
        return
    db.execute("DELETE FROM posts WHERE id=? OR parent_id=?", (post_id, post_id))
    db.commit()
    print(f"post {post_id} deleted.")


def reply_to_post(db):
    if not current_user_id:
        print("no active user. use option 4 to switch user first.")
        return
    posts = db.execute("""
        SELECT posts.id, users.username, posts.title
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.parent_id IS NULL
        ORDER BY posts.id DESC LIMIT 20
    """).fetchall()
    if not posts:
        print("no posts found.")
        return
    for p in posts:
        print(f"  [{p['id']}] {p['username']}: {p['title'][:50]}")
    print()
    post_id = input("enter post id to reply to: ").strip()
    if not post_id.isdigit():
        print("invalid id.")
        return
    body = input("reply: ").strip()
    if not body:
        print("reply cannot be empty.")
        return
    db.execute(
        "INSERT INTO posts (user_id, title, body, parent_id) VALUES (?,?,?,?)",
        (current_user_id, "re: reply", body, int(post_id)),
    )
    db.commit()
    print("reply posted.")


def follow_user(db):
    if not current_user_id:
        print("no active user. use option 4 to switch user first.")
        return
    users = db.execute(
        "SELECT id, username FROM users WHERE id != ? ORDER BY username",
        (current_user_id,),
    ).fetchall()
    if not users:
        print("no other users found.")
        return
    already_following = [
        r["followed_id"]
        for r in db.execute(
            "SELECT followed_id FROM follows WHERE follower_id=?", (current_user_id,)
        ).fetchall()
    ]
    for u in users:
        status = " (following)" if u["id"] in already_following else ""
        print(f"  [{u['id']}] {u['username']}{status}")
    print()
    user_id = input("enter user id to follow: ").strip()
    if not user_id.isdigit():
        print("invalid id.")
        return
    user_id = int(user_id)
    if user_id == current_user_id:
        print("can't follow yourself.")
        return
    existing = db.execute(
        "SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?",
        (current_user_id, user_id),
    ).fetchone()
    if existing:
        print("already following.")
        return
    db.execute(
        "INSERT INTO follows (follower_id, followed_id) VALUES (?,?)",
        (current_user_id, user_id),
    )
    db.commit()
    print("followed.")


def unfollow_user(db):
    if not current_user_id:
        print("no active user. use option 4 to switch user first.")
        return
    following = db.execute(
        """
        SELECT users.id, users.username FROM follows
        JOIN users ON follows.followed_id = users.id
        WHERE follows.follower_id=?
        ORDER BY users.username
    """,
        (current_user_id,),
    ).fetchall()
    if not following:
        print("not following anyone.")
        return
    for u in following:
        print(f"  [{u['id']}] {u['username']}")
    print()
    user_id = input("enter user id to unfollow: ").strip()
    if not user_id.isdigit():
        print("invalid id.")
        return
    db.execute(
        "DELETE FROM follows WHERE follower_id=? AND followed_id=?",
        (current_user_id, int(user_id)),
    )
    db.commit()
    print("unfollowed.")


def list_follows(db):
    if not current_user_id:
        print("no active user. use option 4 to switch user first.")
        return
    followers = db.execute(
        """
        SELECT users.username FROM follows
        JOIN users ON follows.follower_id = users.id
        WHERE follows.followed_id=?
    """,
        (current_user_id,),
    ).fetchall()
    following = db.execute(
        """
        SELECT users.username FROM follows
        JOIN users ON follows.followed_id = users.id
        WHERE follows.follower_id=?
    """,
        (current_user_id,),
    ).fetchall()
    print(f"\nfollowers of {current_username}:")
    for f in followers:
        print(f"  {f['username']}")
    if not followers:
        print("  (none)")
    print(f"\n{current_username} is following:")
    for f in following:
        print(f"  {f['username']}")
    if not following:
        print("  (none)")


def list_topics(db):
    topics = db.execute("""
        SELECT topics.id, topics.name, topics.description, COUNT(posts.id) as post_count
        FROM topics
        LEFT JOIN posts ON posts.topic_id = topics.id AND posts.parent_id IS NULL
        GROUP BY topics.id
        ORDER BY topics.name
    """).fetchall()
    if not topics:
        print("no topics found.")
        return
    print(f"\n{'id':<6} {'name':<20} {'posts':<8} {'description'}")
    print("-" * 60)
    for t in topics:
        print(
            f"{t['id']:<6} {t['name']:<20} {t['post_count']:<8} {t['description'] or ''}"
        )


def create_topic(db):
    name = input("topic name: ").strip()
    if not name:
        print("name cannot be empty.")
        return
    existing = db.execute("SELECT id FROM topics WHERE name=?", (name,)).fetchone()
    if existing:
        print(f"topic '{name}' already exists.")
        return
    description = input("description (optional): ").strip()
    db.execute(
        "INSERT INTO topics (name, description) VALUES (?,?)", (name, description)
    )
    db.commit()
    print(f"topic '{name}' created.")


def delete_topic(db):
    list_topics(db)
    topic_id = input("\nenter topic id to delete: ").strip()
    if not topic_id.isdigit():
        print("invalid id.")
        return
    confirm = input(
        f"delete topic {topic_id}? posts will keep their content but lose the topic. (y/n): "
    )
    if confirm.lower() != "y":
        print("cancelled.")
        return
    db.execute("UPDATE posts SET topic_id=NULL WHERE topic_id=?", (topic_id,))
    db.execute("DELETE FROM topics WHERE id=?", (topic_id,))
    db.commit()
    print(f"topic {topic_id} deleted.")


def reset_database(db):
    confirm = input("this will delete ALL data. type 'reset' to confirm: ").strip()
    if confirm != "reset":
        print("cancelled.")
        return
    for table in (
        "votes",
        "bookmarks",
        "follows",
        "notifications",
        "posts",
        "topics",
        "users",
    ):
        db.execute(f"DELETE FROM {table}")
    db.commit()
    print("database reset.")


def auto_seed(db):
    confirm = input("seed test users, posts, follows, votes, and replies? (y/n): ")
    if confirm.lower() != "y":
        print("cancelled.")
        return

    # --- users ---
    seed_users = [
        ("rchristenhusz", "pass123", "Just a dev who loves Python and travel."),
        ("testuser", "pass123", "Here to test things and cause chaos."),
    ]

    user_ids = {}
    for username, password, bio in seed_users:
        existing = db.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()
        if existing:
            user_ids[username] = existing["id"]
            print(f"  user '{username}' already exists, skipping.")
        else:
            password_hash = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt(rounds=12)
            ).decode()
            db.execute(
                "INSERT INTO users (username, password_hash, bio) VALUES (?,?,?)",
                (username, password_hash, bio),
            )
            db.commit()
            user_ids[username] = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"  created user '{username}'.")

    rc_id = user_ids["rchristenhusz"]
    test_id = user_ids["testuser"]

    # --- mutual follows ---
    for follower, followed in [(rc_id, test_id), (test_id, rc_id)]:
        exists = db.execute(
            "SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?",
            (follower, followed),
        ).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO follows (follower_id, followed_id) VALUES (?,?)",
                (follower, followed),
            )
    db.commit()
    print("  mutual follows set.")

    # --- topics ---
    topic_ids = {}
    for topic_name, description in [
        ("python", "Anything Python related."),
        ("vacation", "Travel, trips, and time off."),
    ]:
        row = db.execute("SELECT id FROM topics WHERE name=?", (topic_name,)).fetchone()
        if row:
            topic_ids[topic_name] = row["id"]
            print(f"  topic '{topic_name}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO topics (name, description) VALUES (?,?)",
                (topic_name, description),
            )
            db.commit()
            topic_ids[topic_name] = db.execute("SELECT last_insert_rowid()").fetchone()[
                0
            ]
            print(f"  created topic '{topic_name}'.")

    # --- posts ---
    seed_posts = [
        (
            rc_id,
            "Getting started with Python decorators",
            "Decorators are one of Python's most powerful features. "
            "Here's a quick breakdown of how they work and when to use them.",
            "python",
        ),
        (
            rc_id,
            "My trip to Portugal",
            "Spent two weeks in Lisbon and Porto. The food, the trams, the views "
            "— absolutely worth it. Here are my highlights.",
            "vacation",
        ),
        (
            test_id,
            "Python virtual environments explained",
            "If you're not using venv or pyenv yet, you're making your life harder "
            "than it needs to be. Let me walk you through it.",
            "python",
        ),
        (
            test_id,
            "Best budget destinations in Southeast Asia",
            "Thailand, Vietnam, and Cambodia are all incredible and surprisingly "
            "affordable. Here's what I wish I'd known before going.",
            "vacation",
        ),
    ]

    post_ids = []
    for user_id, title, body, topic in seed_posts:
        existing = db.execute(
            "SELECT id FROM posts WHERE user_id=? AND title=?", (user_id, title)
        ).fetchone()
        if existing:
            post_ids.append(existing["id"])
            print(f"  post '{title[:45]}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO posts (user_id, title, body, topic_id) VALUES (?,?,?,?)",
                (user_id, title, body, topic_ids[topic]),
            )
            db.commit()
            pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            post_ids.append(pid)
            print(f"  created post '{title[:45]}'.")

    rc_posts = [post_ids[0], post_ids[1]]  # rchristehusz's posts
    test_posts = [post_ids[2], post_ids[3]]  # testuser's posts

    # --- cross-votes (each user upvotes the other's posts) ---
    for voter_id, targets in [(test_id, rc_posts), (rc_id, test_posts)]:
        for pid in targets:
            exists = db.execute(
                "SELECT 1 FROM votes WHERE user_id=? AND post_id=?", (voter_id, pid)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO votes (user_id, post_id, value) VALUES (?,?,1)",
                    (voter_id, pid),
                )
    db.commit()
    print("  votes added.")

    # --- cross-replies (each user replies to the other's posts) ---
    replies = [
        (
            test_id,
            rc_posts[0],
            "Great write-up! Decorators finally clicked for me after reading this.",
        ),
        (
            test_id,
            rc_posts[1],
            "Portugal is on my list! Did you make it down to the Algarve coast?",
        ),
        (
            rc_id,
            test_posts[0],
            "Pyenv changed my workflow completely. Solid recommendation.",
        ),
        (
            rc_id,
            test_posts[1],
            "Southeast Asia is incredible. Vietnam was my favourite stop by far.",
        ),
    ]

    for user_id, parent_id, body in replies:
        exists = db.execute(
            "SELECT 1 FROM posts WHERE user_id=? AND parent_id=? AND body=?",
            (user_id, parent_id, body),
        ).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO posts (user_id, title, body, parent_id) VALUES (?,?,?,?)",
                (user_id, "", body, parent_id),
            )
    db.commit()
    print("  replies added.")
    print("\nauto-seed complete.")


with app.app_context():
    db = get_db()
    while True:
        choice = menu()
        if choice == "1":
            list_users_and_posts(db)
        elif choice == "2":
            create_user(db)
        elif choice == "3":
            delete_user(db)
        elif choice == "4":
            switch_user(db)
        elif choice == "5":
            create_post(db)
        elif choice == "6":
            delete_post(db)
        elif choice == "7":
            reply_to_post(db)
        elif choice == "8":
            follow_user(db)
        elif choice == "9":
            unfollow_user(db)
        elif choice == "10":
            list_follows(db)
        elif choice == "11":
            list_topics(db)
        elif choice == "12":
            create_topic(db)
        elif choice == "13":
            delete_topic(db)
        elif choice == "14":
            reset_database(db)
        elif choice == "15":
            auto_seed(db)
        elif choice == "0":
            print("bye.")
            break
        else:
            print("invalid option.")
