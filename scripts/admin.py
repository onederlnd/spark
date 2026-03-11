# scripts/admin.py

import sys
import os
import bcrypt
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import get_db

app = create_app()

current_user_id = None
current_username = None


# --- seed data
def _seed_users(db, seed_users):
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
    return user_ids


def _seed_follows(db, pairs):
    for follower, followed in pairs:
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
    print("  follows set.")


def _seed_topics(db, topic_data):
    topic_ids = {}
    for name, description in topic_data:
        row = db.execute("SELECT id FROM topics WHERE name=?", (name,)).fetchone()
        if row:
            topic_ids[name] = row["id"]
            print(f"  topic '{name}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO topics (name, description) VALUES (?,?)",
                (name, description),
            )
            db.commit()
            topic_ids[name] = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"  created topic '{name}'.")
    return topic_ids


def _seed_posts(db, seed_posts, topic_ids):
    post_ids = {}
    for user_id, topic, title, body in seed_posts:
        existing = db.execute(
            "SELECT id FROM posts WHERE user_id=? AND title=?", (user_id, title)
        ).fetchone()
        if existing:
            post_ids[title] = existing["id"]
            print(f"  post '{title[:45]}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO posts (user_id, title, body, topic_id) VALUES (?,?,?,?)",
                (user_id, title, body, topic_ids.get(topic)),
            )
            db.commit()
            pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            post_ids[title] = pid
            print(f"  created post '{title[:45]}'.")
    return post_ids


def _seed_replies(db, replies):
    for user_id, parent_id, body in replies:
        if not parent_id:
            continue
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
            print(f"  reply added to post {parent_id}.")


def _seed_votes(db, voters, post_ids):
    for voter in voters:
        for pid in post_ids:
            exists = db.execute(
                "SELECT 1 FROM votes WHERE user_id=? AND post_id=?", (voter, pid)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO votes (user_id, post_id, value) VALUES (?,?,1)",
                    (voter, pid),
                )
                db.execute("UPDATE posts SET votes = votes + 1 WHERE id = ?", (pid,))
    db.commit()
    print("  votes added.")


def clear_seed_data(db):
    confirm = input(
        "clear all seed data? this deletes ALL users, posts, topics. type 'clear' to confirm: "
    ).strip()
    if confirm != "clear":
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
    print("seed data cleared.")


def menu():
    user_label = f" (acting as: {current_username})" if current_username else ""
    print(f"\n== SparK admin{user_label} ==")
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
    print("15. seed data")
    print("--- testing ---")
    print("16. testing submenu")
    print("0.  exit")
    return input("\n> ").strip()


def testing_menu():
    while True:
        print("\n== testing submenu ==")
        print("1.  auto follow/unfollow with delay")
        print("2.  spam posts (bulk create)")
        print("3.  spam replies (bulk reply to post)")
        print("4.  bulk vote posts")
        print("5.  simulate notification flood")
        print("6.  create users with varied activity levels")
        print("7.  stress test: create N posts rapidly")
        print("0.  back")
        choice = input("\n> ").strip()

        with app.app_context():
            db = get_db()
            if choice == "1":
                test_follow_unfollow(db)
            elif choice == "2":
                test_spam_posts(db)
            elif choice == "3":
                test_spam_replies(db)
            elif choice == "4":
                test_bulk_vote(db)
            elif choice == "5":
                test_notification_flood(db)
            elif choice == "6":
                test_varied_users(db)
            elif choice == "7":
                test_stress_posts(db)
            elif choice == "0":
                break
            else:
                print("invalid option.")


def test_follow_unfollow(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    users = db.execute(
        "SELECT id, username FROM users WHERE id != ?", (current_user_id,)
    ).fetchall()
    if not users:
        print("no other users.")
        return
    for u in users:
        print(f"  [{u['id']}] {u['username']}")
    target_id = input("enter user id to follow/unfollow: ").strip()
    if not target_id.isdigit():
        print("invalid id.")
        return
    target_id = int(target_id)
    cycles = input("how many follow/unfollow cycles? (default 3): ").strip()
    cycles = int(cycles) if cycles.isdigit() else 3
    delay = input("delay between actions in seconds? (default 1): ").strip()
    delay = float(delay) if delay.replace(".", "").isdigit() else 1.0

    for i in range(cycles):
        print(f"  cycle {i + 1}/{cycles}: following...")
        db.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?,?)",
            (current_user_id, target_id),
        )
        db.commit()
        time.sleep(delay)
        print(f"  cycle {i + 1}/{cycles}: unfollowing...")
        db.execute(
            "DELETE FROM follows WHERE follower_id=? AND followed_id=?",
            (current_user_id, target_id),
        )
        db.commit()
        time.sleep(delay)
    print(f"done. {cycles} follow/unfollow cycles completed.")


def test_spam_posts(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    count = input("how many posts to create? (default 5): ").strip()
    count = int(count) if count.isdigit() else 5
    topic = input("topic name (optional): ").strip()
    topic_id = None
    if topic:
        row = db.execute("SELECT id FROM topics WHERE name=?", (topic,)).fetchone()
        if row:
            topic_id = row["id"]
        else:
            print(f"topic '{topic}' not found, posting without topic.")

    for i in range(1, count + 1):
        title = f"[test] spam post {i} — {int(time.time())}"
        body = f"this is automated test post #{i}. created at {time.time()}."
        db.execute(
            "INSERT INTO posts (user_id, title, body, topic_id) VALUES (?,?,?,?)",
            (current_user_id, title, body, topic_id),
        )
        db.commit()
        print(f"  created post {i}/{count}")
    print(f"done. {count} posts created.")


def test_spam_replies(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    posts = db.execute("""
        SELECT posts.id, users.username, posts.title FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.parent_id IS NULL ORDER BY posts.id DESC LIMIT 20
    """).fetchall()
    if not posts:
        print("no posts found.")
        return
    for p in posts:
        print(f"  [{p['id']}] {p['username']}: {p['title'][:50]}")
    post_id = input("enter post id to spam replies on: ").strip()
    if not post_id.isdigit():
        print("invalid id.")
        return
    count = input("how many replies? (default 5): ").strip()
    count = int(count) if count.isdigit() else 5
    for i in range(1, count + 1):
        body = f"[test] automated reply #{i} at {time.time()}"
        db.execute(
            "INSERT INTO posts (user_id, title, body, parent_id) VALUES (?,?,?,?)",
            (current_user_id, "", body, int(post_id)),
        )
        db.commit()
        print(f"  reply {i}/{count} posted")
    print(f"done. {count} replies created.")


def test_bulk_vote(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    posts = db.execute(
        """
        SELECT posts.id, users.username, posts.title, posts.votes FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.parent_id IS NULL AND posts.user_id != ?
        ORDER BY posts.id DESC LIMIT 20
    """,
        (current_user_id,),
    ).fetchall()
    if not posts:
        print("no posts found.")
        return
    for p in posts:
        print(f"  [{p['id']}] {p['username']}: {p['title'][:40]} (votes: {p['votes']})")
    value = input("vote value: 1 (upvote) or -1 (downvote)? (default 1): ").strip()
    value = -1 if value == "-1" else 1
    confirm = input(f"vote {value} on all {len(posts)} posts above? (y/n): ")
    if confirm.lower() != "y":
        print("cancelled.")
        return
    for p in posts:
        existing = db.execute(
            "SELECT value FROM votes WHERE user_id=? AND post_id=?",
            (current_user_id, p["id"]),
        ).fetchone()
        if existing:
            print(f"  post {p['id']}: already voted, skipping.")
            continue
        db.execute(
            "INSERT INTO votes (user_id, post_id, value) VALUES (?,?,?)",
            (current_user_id, p["id"], value),
        )
        db.execute("UPDATE posts SET votes = votes + ? WHERE id = ?", (value, p["id"]))
        db.commit()
        print(f"  voted {value} on post {p['id']}")
    print("done.")


def test_notification_flood(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    users = db.execute(
        "SELECT id, username FROM users WHERE id != ?", (current_user_id,)
    ).fetchall()
    if not users:
        print("no other users.")
        return
    for u in users:
        print(f"  [{u['id']}] {u['username']}")
    target_id = input("send notifications to user id: ").strip()
    if not target_id.isdigit():
        print("invalid id.")
        return
    count = input("how many notifications? (default 5): ").strip()
    count = int(count) if count.isdigit() else 5
    for i in range(1, count + 1):
        db.execute(
            "INSERT INTO notifications (user_id, type, message, link) VALUES (?,?,?,?)",
            (int(target_id), "test", f"[test] notification {i} of {count}", "/"),
        )
        db.commit()
        print(f"  notification {i}/{count} sent")
    print(f"done. {count} notifications created.")


def test_varied_users(db):
    seed = [
        ("ms_johnson", "pass123", "5th grade math teacher. Love making learning fun!"),
        ("student_alex", "pass123", "6th grader. Into coding and science experiments."),
        ("parent_mike", "pass123", "Dad of two, keeping an eye on things."),
        ("mr_patel", "pass123", "High school biology teacher. Science is life."),
        ("student_priya", "pass123", "8th grade. I love reading and creative writing."),
    ]
    for username, password, bio in seed:
        existing = db.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()
        if existing:
            print(f"  user '{username}' already exists, skipping.")
            continue
        password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt(rounds=12)
        ).decode()
        db.execute(
            "INSERT INTO users (username, password_hash, bio) VALUES (?,?,?)",
            (username, password_hash, bio),
        )
        db.commit()
        print(f"  created user '{username}'.")
    print("done.")


def test_stress_posts(db):
    if not current_user_id:
        print("no active user. switch first.")
        return
    count = input("how many posts to create rapidly? (default 20): ").strip()
    count = int(count) if count.isdigit() else 20
    confirm = input(f"create {count} posts as {current_username}? (y/n): ")
    if confirm.lower() != "y":
        print("cancelled.")
        return
    start = time.time()
    for i in range(1, count + 1):
        db.execute(
            "INSERT INTO posts (user_id, title, body) VALUES (?,?,?)",
            (
                current_user_id,
                f"[stress] post {i}",
                f"stress test body {i} — {time.time()}",
            ),
        )
        db.commit()
    elapsed = time.time() - start
    print(f"done. {count} posts created in {elapsed:.2f}s.")


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
        (current_user_id, "", body, int(post_id)),
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


def seed_menu():
    while True:
        print("\n== seed data ==")
        print("1. dev seed        — your users, technical, stress-testable")
        print("2. demo seed")
        print("   3. 3rd grade    — early readers, parent-heavy, icon-friendly")
        print("   4. 5th grade    — math/science/reading, parent involvement")
        print("   5. 7th grade    — complex topics, peer discussion")
        print("   6. 8th grade    — high order thinking, pre-high school")
        print("7. clear all seed data")
        print("0. back")
        choice = input("\n> ").strip()

        with app.app_context():
            db = get_db()
            if choice == "1":
                auto_seed_dev(db)
            elif choice == "3":
                auto_seed_demo(db, grade=3)
            elif choice == "4":
                auto_seed_demo(db, grade=5)
            elif choice == "5":
                auto_seed_demo(db, grade=7)
            elif choice == "6":
                auto_seed_demo(db, grade=8)
            elif choice == "7":
                clear_seed_data(db)
            elif choice == "0":
                break
            else:
                print("invalid option.")


# --- developer demos
def auto_seed_demo(db, grade):
    if grade == 3:
        _seed_grade_3(db)
    elif grade == 5:
        _seed_grade_5(db)
    elif grade == 7:
        _seed_grade_7(db)
    elif grade == 8:
        _seed_grade_8(db)


def auto_seed_dev(db):
    confirm = input(
        "seed dev users, topics, posts, follows, votes, and replies? (y/n): "
    )
    if confirm.lower() != "y":
        print("cancelled.")
        return

    seed_users = [
        ("rchristenhusz", "pass123", "Admin and platform builder."),
        ("ms_johnson", "pass123", "5th grade math teacher."),
        ("mr_patel", "pass123", "High school biology teacher."),
        ("student_alex", "pass123", "6th grader. Into coding."),
        ("student_priya", "pass123", "8th grade. Into writing."),
        ("parent_mike", "pass123", "Dad of two SparK users."),
    ]

    user_ids = _seed_users(db, seed_users)
    rc_id = user_ids["rchristenhusz"]
    ms_j_id = user_ids["ms_johnson"]
    mr_p_id = user_ids["mr_patel"]
    alex_id = user_ids["student_alex"]
    priya_id = user_ids["student_priya"]
    mike_id = user_ids["parent_mike"]

    follow_pairs = [
        (alex_id, ms_j_id),
        (alex_id, mr_p_id),
        (priya_id, ms_j_id),
        (priya_id, mr_p_id),
        (mike_id, ms_j_id),
        (mike_id, mr_p_id),
        (ms_j_id, mr_p_id),
        (mr_p_id, ms_j_id),
        (alex_id, priya_id),
        (priya_id, alex_id),
        (rc_id, ms_j_id),
        (rc_id, mr_p_id),
    ]
    _seed_follows(db, follow_pairs)

    topic_data = [
        ("math", "Numbers, equations, geometry, and problem solving."),
        ("science", "Biology, chemistry, physics, and experiments."),
        ("reading", "Books, stories, poetry, and creative writing."),
        ("coding", "Programming, projects, and tech questions."),
        ("general", "Anything that doesn't fit elsewhere."),
    ]
    topic_ids = _seed_topics(db, topic_data)

    seed_posts = [
        (
            ms_j_id,
            "math",
            "How to find the least common multiple — explained simply",
            "The LCM is the smallest number that two numbers both divide into evenly. "
            "Start by listing multiples of each number until you find one they share. "
            "For 4 and 6: multiples of 4 are 4, 8, 12... multiples of 6 are 6, 12... "
            "so the LCM is 12. There's also a faster method using prime factorization!",
        ),
        (
            ms_j_id,
            "math",
            "Why does order of operations matter? (PEMDAS explained)",
            "Without a standard order of operations, the same equation could give "
            "different answers depending on who solves it. PEMDAS (Parentheses, "
            "Exponents, Multiplication/Division, Addition/Subtraction) is the agreed "
            "rule everyone follows. Try this: what is 2 + 3 × 4? It's 14, not 20!",
        ),
        (
            mr_p_id,
            "science",
            "What actually happens during photosynthesis?",
            "Plants use sunlight, water, and carbon dioxide to make glucose and oxygen. "
            "The chlorophyll in leaves absorbs light energy to power this reaction. "
            "The equation is: 6CO2 + 6H2O + light → C6H12O6 + 6O2. "
            "Essentially, plants are making their own food while cleaning our air!",
        ),
        (
            alex_id,
            "coding",
            "I built my first Python program — a number guessing game!",
            "After a few weeks in our school coding club I finally built something "
            "that actually works. You guess a number between 1 and 100 and it tells "
            "you if you're too high or too low. Used a while loop and if/elif/else. "
            "Really proud of this one. Happy to share the code if anyone wants to see it!",
        ),
        (
            priya_id,
            "reading",
            "Book review: The Giver by Lois Lowry",
            "I just finished The Giver for English class and I can't stop thinking "
            "about it. The idea of a society that removes all pain but also all choice "
            "is really unsettling. Jonas seeing colour for the first time felt magical. "
            "The ending left me with so many questions. Has anyone else read it?",
        ),
        (
            mike_id,
            "general",
            "How do I help my kid who's struggling with fractions?",
            "My daughter is in 5th grade and really struggling with adding fractions "
            "with different denominators. We've tried a few YouTube videos but nothing "
            "has clicked yet. Any teachers or students here have advice?",
        ),
        (
            rc_id,
            "general",
            "Welcome to SparK — a few things to know",
            "Hi everyone, welcome to SparK! Be kind, be helpful, and stay on topic. "
            "If you see something that doesn't belong, use the report button. "
            "We're glad you're here — now go explore the topics and jump in!",
        ),
    ]
    post_ids = _seed_posts(db, seed_posts, topic_ids)

    seed_replies = [
        (
            alex_id,
            post_ids.get("How to find the least common multiple — explained simply"),
            "This actually helped a lot! The multiples list method makes way more sense "
            "to me than what my textbook showed.",
        ),
        (
            priya_id,
            post_ids.get("How to find the least common multiple — explained simply"),
            "We just covered this in class! Great explanation Ms. Johnson!",
        ),
        (
            ms_j_id,
            post_ids.get("How do I help my kid who's struggling with fractions?"),
            "Try using physical objects — pizza slices, Lego bricks, or paper folding. "
            "Seeing fractions visually before working with numbers makes a big difference.",
        ),
        (
            alex_id,
            post_ids.get("How do I help my kid who's struggling with fractions?"),
            "Khan Academy fraction videos helped me a lot! They go at your own pace.",
        ),
        (
            mr_p_id,
            post_ids.get("Book review: The Giver by Lois Lowry"),
            "Excellent review Priya! The ending is intentionally ambiguous. "
            "There's actually a sequel called Gathering Blue set in the same world.",
        ),
    ]
    _seed_replies(db, seed_replies)

    vote_targets = [
        v
        for v in [
            post_ids.get("How to find the least common multiple — explained simply"),
            post_ids.get("Why does order of operations matter? (PEMDAS explained)"),
            post_ids.get("What actually happens during photosynthesis?"),
            post_ids.get("Welcome to SparK — a few things to know"),
        ]
        if v
    ]
    _seed_votes(db, [alex_id, priya_id, mike_id], vote_targets)
    print("\ndev seed complete.")


def auto_seed(db):
    confirm = input(
        "seed test users, topics, posts, follows, votes, and replies? (y/n): "
    )
    if confirm.lower() != "y":
        print("cancelled.")
        return

    # --- users ---
    seed_users = [
        (
            "rchristenhusz",
            "pass123",
            "Admin and platform builder. Here to keep things running.",
        ),
        ("ms_johnson", "pass123", "5th grade math teacher. Love making numbers fun!"),
        ("mr_patel", "pass123", "High school biology teacher. Science is everywhere."),
        ("student_alex", "pass123", "6th grader. I love coding and building things."),
        ("student_priya", "pass123", "8th grade. Into creative writing and reading."),
        ("parent_mike", "pass123", "Dad of two SparK users. Love seeing them learn."),
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
    ms_j_id = user_ids["ms_johnson"]
    mr_p_id = user_ids["mr_patel"]
    alex_id = user_ids["student_alex"]
    priya_id = user_ids["student_priya"]
    mike_id = user_ids["parent_mike"]

    # --- follows: students follow teachers, teachers follow each other ---
    follow_pairs = [
        (alex_id, ms_j_id),
        (alex_id, mr_p_id),
        (priya_id, ms_j_id),
        (priya_id, mr_p_id),
        (mike_id, ms_j_id),
        (mike_id, mr_p_id),
        (ms_j_id, mr_p_id),
        (mr_p_id, ms_j_id),
        (alex_id, priya_id),
        (priya_id, alex_id),
        (rc_id, ms_j_id),
        (rc_id, mr_p_id),
    ]
    for follower, followed in follow_pairs:
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
    print("  follows set.")

    # --- topics ---
    topic_data = [
        ("math", "Numbers, equations, geometry, and problem solving."),
        ("science", "Biology, chemistry, physics, and experiments."),
        ("reading", "Books, stories, poetry, and creative writing."),
        ("coding", "Programming, projects, and tech questions."),
        ("general", "Anything that doesn't fit elsewhere."),
    ]
    topic_ids = {}
    for name, description in topic_data:
        row = db.execute("SELECT id FROM topics WHERE name=?", (name,)).fetchone()
        if row:
            topic_ids[name] = row["id"]
            print(f"  topic '{name}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO topics (name, description) VALUES (?,?)",
                (name, description),
            )
            db.commit()
            topic_ids[name] = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"  created topic '{name}'.")

    # --- posts ---
    seed_posts = [
        (
            ms_j_id,
            "math",
            "How to find the least common multiple — explained simply",
            "The LCM is the smallest number that two numbers both divide into evenly. "
            "Start by listing multiples of each number until you find one they share. "
            "For 4 and 6: multiples of 4 are 4, 8, 12... multiples of 6 are 6, 12... "
            "so the LCM is 12. There's also a faster method using prime factorization!",
        ),
        (
            ms_j_id,
            "math",
            "Why does order of operations matter? (PEMDAS explained)",
            "Without a standard order of operations, the same equation could give "
            "different answers depending on who solves it. PEMDAS (Parentheses, "
            "Exponents, Multiplication/Division, Addition/Subtraction) is the agreed "
            "rule everyone follows. Try this: what is 2 + 3 × 4? It's 14, not 20!",
        ),
        (
            mr_p_id,
            "science",
            "What actually happens during photosynthesis?",
            "Plants use sunlight, water, and carbon dioxide to make glucose and oxygen. "
            "The chlorophyll in leaves absorbs light energy to power this reaction. "
            "The equation is: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. "
            "Essentially, plants are making their own food while cleaning our air!",
        ),
        (
            mr_p_id,
            "science",
            "The difference between a hypothesis and a theory",
            "A hypothesis is an educated guess you can test. A theory is a well-tested "
            "explanation supported by a lot of evidence. In science, a theory isn't "
            "just a guess — it's one of the strongest conclusions we can make. "
            "Evolution and gravity are both theories. That means they're extremely "
            "well supported, not uncertain!",
        ),
        (
            alex_id,
            "coding",
            "I built my first Python program — a number guessing game!",
            "After a few weeks in our school coding club I finally built something "
            "that actually works. You guess a number between 1 and 100 and it tells "
            "you if you're too high or too low. Used a while loop and if/elif/else. "
            "Really proud of this one. Happy to share the code if anyone wants to see it!",
        ),
        (
            alex_id,
            "coding",
            "Can someone explain what a variable is in plain English?",
            "I know what variables are in math class but in coding it feels different. "
            "Like in Python when I write x = 5, is x actually storing the number 5 "
            "somewhere? Or is it more like a label? My teacher tried to explain it "
            "but I'm still a little confused. Any help appreciated!",
        ),
        (
            priya_id,
            "reading",
            "Book review: The Giver by Lois Lowry",
            "I just finished The Giver for English class and I can't stop thinking "
            "about it. The idea of a society that removes all pain but also all choice "
            "is really unsettling. Jonas seeing colour for the first time felt magical. "
            "The ending left me with so many questions. Has anyone else read it? "
            "What did you think Jonas found at the end?",
        ),
        (
            priya_id,
            "reading",
            "Tips for writing a strong story opening?",
            "I'm working on a short story for class and my teacher said my opening "
            "is too slow. She said to 'start in the action' but I don't really know "
            "what that means. Do I just skip the background info entirely? "
            "How do you hook the reader from the very first sentence?",
        ),
        (
            mike_id,
            "general",
            "How do I help my kid who's struggling with fractions?",
            "My daughter is in 5th grade and really struggling with adding fractions "
            "with different denominators. She understands same-denominator fractions "
            "fine but gets totally lost when they're different. We've tried a few "
            "YouTube videos but nothing has clicked yet. Any teachers or students "
            "here have advice or resources that worked for you?",
        ),
        (
            rc_id,
            "general",
            "Welcome to SparK — a few things to know",
            "Hi everyone, welcome to SparK! This is a community built for students, "
            "teachers, and parents to learn and connect safely. A few guidelines: "
            "be kind, be helpful, and stay on topic. Teachers have a blue badge. "
            "If you see something that doesn't belong, use the report button. "
            "We're glad you're here — now go explore the topics and jump in!",
        ),
    ]

    post_ids = {}
    for user_id, topic, title, body in seed_posts:
        existing = db.execute(
            "SELECT id FROM posts WHERE user_id=? AND title=?", (user_id, title)
        ).fetchone()
        if existing:
            post_ids[title] = existing["id"]
            print(f"  post '{title[:45]}' already exists, skipping.")
        else:
            db.execute(
                "INSERT INTO posts (user_id, title, body, topic_id) VALUES (?,?,?,?)",
                (user_id, title, body, topic_ids[topic]),
            )
            db.commit()
            pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            post_ids[title] = pid
            print(f"  created post '{title[:45]}'.")

    # --- replies ---
    seed_replies = [
        (
            alex_id,
            post_ids["How to find the least common multiple — explained simply"],
            "This actually helped a lot! I was always confused about why we needed "
            "the LCM. The multiples list method makes way more sense to me than "
            "what my textbook showed.",
        ),
        (
            priya_id,
            post_ids["How to find the least common multiple — explained simply"],
            "We just covered this in class! The prime factorization method is faster "
            "once you get the hang of it. Great explanation Ms. Johnson!",
        ),
        (
            ms_j_id,
            post_ids["Can someone explain what a variable is in plain English?"],
            "Great question Alex! Think of a variable like a labelled box. The box "
            "has a name (like x) and you can put a value inside it. When you write "
            "x = 5, you're putting 5 into the box called x. You can change what's "
            "inside anytime — that's why it's called a variable!",
        ),
        (
            mr_p_id,
            post_ids["Can someone explain what a variable is in plain English?"],
            "To add to Ms. Johnson's explanation — in science we use variables too! "
            "In an experiment, the variable is what you're measuring or changing. "
            "Same idea: a container for a value that can change.",
        ),
        (
            priya_id,
            post_ids["I built my first Python program — a number guessing game!"],
            "That's so cool Alex! I want to try coding. What app do you use to write "
            "Python? Is it hard to get started?",
        ),
        (
            ms_j_id,
            post_ids["How do I help my kid who's struggling with fractions?"],
            "Hi! One thing that really helps is using physical objects — pizza slices, "
            "Lego bricks, or even paper folding. Seeing fractions visually before "
            "working with numbers abstractly makes a big difference. Feel free to "
            "reach out if you'd like some printable resources!",
        ),
        (
            alex_id,
            post_ids["How do I help my kid who's struggling with fractions?"],
            "Khan Academy fraction videos helped me a lot! They have practice problems "
            "too and it goes at your own pace.",
        ),
        (
            mr_p_id,
            post_ids["Book review: The Giver by Lois Lowry"],
            "Excellent review Priya! The ending is intentionally ambiguous — Lowry "
            "wanted readers to decide for themselves. What do you think Jonas found? "
            "There's actually a sequel called Gathering Blue set in the same world.",
        ),
        (
            alex_id,
            post_ids["Tips for writing a strong story opening?"],
            "My English teacher said to imagine the reader is standing outside the "
            "story looking in through a window. Your first line should make them "
            "want to open the door. Start with something happening, not explaining.",
        ),
    ]

    for user_id, parent_id, body in seed_replies:
        if not parent_id:
            continue
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
            print(f"  reply added to post {parent_id}.")

    # --- votes: upvote teacher posts from students/parents ---
    vote_targets = [
        post_ids["How to find the least common multiple — explained simply"],
        post_ids["Why does order of operations matter? (PEMDAS explained)"],
        post_ids["What actually happens during photosynthesis?"],
        post_ids["The difference between a hypothesis and a theory"],
        post_ids["Welcome to SparK — a few things to know"],
    ]
    voters = [alex_id, priya_id, mike_id]
    for voter in voters:
        for pid in vote_targets:
            exists = db.execute(
                "SELECT 1 FROM votes WHERE user_id=? AND post_id=?", (voter, pid)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO votes (user_id, post_id, value) VALUES (?,?,1)",
                    (voter, pid),
                )
                db.execute("UPDATE posts SET votes = votes + 1 WHERE id = ?", (pid,))
    db.commit()
    print("  votes added.")
    print("\nauto-seed complete.")


# -- grade specific demos
def _seed_grade_3(db):
    print("\n== seeding 3rd grade demo ==")
    seed_users = [
        (
            "mrs_chen",
            "pass123",
            "3rd grade teacher. Reading and storytelling are my passion!",
        ),
        ("tommy_k", "pass123", "I am 8 years old. I like dinosaurs and drawing."),
        ("lily_r", "pass123", "I like cats and painting pictures."),
        ("marcus_b", "pass123", "I like soccer and building with Lego."),
        ("sofia_m", "pass123", "I like reading and my dog Biscuit."),
        ("parent_chen", "pass123", "Mom of Tommy. Love seeing what he's learning!"),
        ("parent_riley", "pass123", "Lily's dad. Checking in on her class."),
    ]
    user_ids = _seed_users(db, seed_users)
    teacher = user_ids["mrs_chen"]
    tommy = user_ids["tommy_k"]
    lily = user_ids["lily_r"]
    marcus = user_ids["marcus_b"]
    sofia = user_ids["sofia_m"]
    parent1 = user_ids["parent_chen"]
    parent2 = user_ids["parent_riley"]

    _seed_follows(
        db,
        [
            (tommy, teacher),
            (lily, teacher),
            (marcus, teacher),
            (sofia, teacher),
            (parent1, teacher),
            (parent2, teacher),
            (tommy, lily),
            (lily, sofia),
            (marcus, tommy),
        ],
    )

    topic_data = [
        ("reading", "Books, stories, and reading fun!"),
        ("science", "Animals, plants, and cool experiments."),
        ("math", "Numbers and counting."),
        ("art", "Drawing, painting, and creating."),
        ("general", "Anything you want to share!"),
    ]
    topic_ids = _seed_topics(db, topic_data)

    seed_posts = [
        (
            teacher,
            "reading",
            "Our class book this week: Charlotte's Web!",
            "We started reading Charlotte's Web today! Wilbur the pig makes a new friend "
            "named Charlotte who is a spider. What do you think so far? "
            "Write one thing you noticed about Wilbur in the comments!",
        ),
        (
            teacher,
            "science",
            "We learned about butterflies today!",
            "Did you know a caterpillar turns into a butterfly inside a chrysalis? "
            "That change is called metamorphosis. Can you draw the four stages? "
            "Share what you remember!",
        ),
        (
            teacher,
            "math",
            "Let's practice skip counting!",
            "Skip counting means counting by 2s, 5s, or 10s instead of 1s. "
            "Try this: count by 5s starting from 0. How far can you go? "
            "Write your answer below!",
        ),
        (
            tommy,
            "reading",
            "My favorite part of Charlotte's Web",
            "My favorite part was when Wilbur won a prize at the fair. "
            "I did not expect that to happen! Charlotte is really smart.",
        ),
        (
            lily,
            "art",
            "I drew a picture of Charlotte!",
            "I drew Charlotte the spider with all her legs. "
            "It was hard to draw 8 legs but I did it! "
            "Mrs Chen said it was really good.",
        ),
        (
            marcus,
            "science",
            "I saw a caterpillar outside!",
            "I found a green caterpillar on a leaf in my yard. "
            "My dad said it might turn into a monarch butterfly. "
            "I am going to watch it every day.",
        ),
        (
            sofia,
            "reading",
            "I already read Charlotte's Web before!",
            "I read this book last year with my mom. "
            "The ending made me cry a little bit. "
            "Has anyone else read it before?",
        ),
        (
            parent1,
            "general",
            "Tommy is loving this class!",
            "Just wanted to say thank you Mrs Chen. Tommy comes home every day "
            "talking about what he learned. The butterfly lesson was his favourite. "
            "He's been looking for caterpillars in the backyard all week!",
        ),
    ]
    post_ids = _seed_posts(db, seed_posts, topic_ids)

    seed_replies = [
        (
            tommy,
            post_ids.get("Our class book this week: Charlotte's Web!"),
            "Wilbur was scared at the beginning. I felt bad for him.",
        ),
        (
            lily,
            post_ids.get("Our class book this week: Charlotte's Web!"),
            "I think Charlotte is the best character. She is very kind.",
        ),
        (
            marcus,
            post_ids.get("Our class book this week: Charlotte's Web!"),
            "Wilbur is funny. I like when he plays in the mud.",
        ),
        (
            teacher,
            post_ids.get("I saw a caterpillar outside!"),
            "How exciting Marcus! If you can, take a photo and bring it in. "
            "We can look up what kind it is together!",
        ),
        (
            teacher,
            post_ids.get("My favorite part of Charlotte's Web"),
            "Great observation Tommy! Charlotte worked very hard to help her friend. "
            "What does that tell us about what kind of friend she is?",
        ),
        (
            sofia,
            post_ids.get("My favorite part of Charlotte's Web"),
            "I agree! I also liked that part. Wilbur was so happy.",
        ),
        (
            teacher,
            post_ids.get("Tommy is loving this class!"),
            "Thank you so much! Tommy is a wonderful student. "
            "His enthusiasm in class makes everyone smile.",
        ),
        (
            lily,
            post_ids.get("I already read Charlotte's Web before!"),
            "The ending is so sad. I cried too. Don't tell anyone.",
        ),
    ]
    _seed_replies(db, seed_replies)

    vote_targets = [
        v
        for v in [
            post_ids.get("Our class book this week: Charlotte's Web!"),
            post_ids.get("We learned about butterflies today!"),
            post_ids.get("Let's practice skip counting!"),
        ]
        if v
    ]
    _seed_votes(db, [tommy, lily, marcus, sofia, parent1, parent2], vote_targets)
    print("\n3rd grade demo seed complete.")


def _seed_grade_5(db):
    print("\n== seeding 5th grade demo ==")
    seed_users = [
        (
            "ms_johnson",
            "pass123",
            "5th grade teacher. Math and science are everywhere!",
        ),
        ("alex_w", "pass123", "5th grader. I love coding and soccer."),
        ("priya_s", "pass123", "5th grade. I like writing stories and reading."),
        ("jordan_t", "pass123", "5th grade. Into Minecraft and building things."),
        ("maya_l", "pass123", "5th grade. I love animals and want to be a vet."),
        ("sam_r", "pass123", "5th grade. Math is my favourite subject."),
        ("parent_walsh", "pass123", "Alex's mom. Glad to see what they're up to!"),
        ("parent_singh", "pass123", "Priya's dad. Love this platform."),
    ]
    user_ids = _seed_users(db, seed_users)
    teacher = user_ids["ms_johnson"]
    alex = user_ids["alex_w"]
    priya = user_ids["priya_s"]
    jordan = user_ids["jordan_t"]
    maya = user_ids["maya_l"]
    sam = user_ids["sam_r"]
    p1 = user_ids["parent_walsh"]
    p2 = user_ids["parent_singh"]

    _seed_follows(
        db,
        [
            (alex, teacher),
            (priya, teacher),
            (jordan, teacher),
            (maya, teacher),
            (sam, teacher),
            (p1, teacher),
            (p2, teacher),
            (alex, priya),
            (priya, alex),
            (jordan, alex),
            (maya, priya),
            (sam, alex),
        ],
    )

    topic_data = [
        ("math", "Numbers, fractions, geometry, and problem solving."),
        ("science", "Plants, animals, earth science, and experiments."),
        ("reading", "Books, stories, and creative writing."),
        ("coding", "Programming, games, and tech projects."),
        ("general", "Anything that doesn't fit elsewhere."),
    ]
    topic_ids = _seed_topics(db, topic_data)

    seed_posts = [
        (
            teacher,
            "math",
            "Fractions don't have to be scary — here's how I think about them",
            "A fraction is just a way of showing part of a whole. "
            "Think of a pizza cut into 8 slices. If you eat 3 slices, you ate 3/8 of the pizza. "
            "The bottom number (denominator) tells you how many equal pieces total. "
            "The top number (numerator) tells you how many you have. "
            "Once that clicks, everything else gets easier!",
        ),
        (
            teacher,
            "science",
            "Why do leaves change colour in fall?",
            "Leaves are actually yellow and orange all year — we just can't see it! "
            "Green chlorophyll covers those colours during spring and summer. "
            "In fall, trees stop making chlorophyll, so the green fades "
            "and the hidden colours finally show through. Pretty cool right?",
        ),
        (
            teacher,
            "reading",
            "Writing tip: show don't tell",
            "Instead of writing 'she was scared', try showing it. "
            "Her hands were shaking. She pressed against the wall and held her breath. "
            "See the difference? Showing puts the reader inside the scene. "
            "Try rewriting a sentence from your story using this technique!",
        ),
        (
            alex,
            "coding",
            "I made a quiz game in Scratch!",
            "I spent the whole weekend making a maths quiz in Scratch. "
            "It asks you 10 questions and gives you a score at the end. "
            "I used variables to keep track of the score and if/else blocks for right and wrong. "
            "Let me know if you want me to share the link!",
        ),
        (
            priya,
            "reading",
            "Has anyone read Wonder by R.J. Palacio?",
            "I just finished Wonder and I think it might be my favourite book ever. "
            "Auggie is so brave and the story made me think about how I treat people. "
            "The part from Julian's point of view surprised me the most. "
            "What was your favourite character's perspective?",
        ),
        (
            jordan,
            "coding",
            "Is Minecraft actually coding?",
            "My parents say Minecraft is just a game but I read that "
            "people use it to learn coding with something called command blocks. "
            "Has anyone tried that? Is it real coding or just pretend coding?",
        ),
        (
            maya,
            "science",
            "I want to be a vet — where do I start?",
            "I love animals and want to be a vet when I grow up. "
            "My teacher said I should learn about biology. "
            "Does anyone know what subjects I should be good at? "
            "Are there any books or videos about being a vet?",
        ),
        (
            sam,
            "math",
            "I figured out a shortcut for multiplying by 9!",
            "Here's a trick my grandpa taught me. To multiply any number by 9, "
            "multiply it by 10 first then subtract the number. "
            "So 9 x 7 = (10 x 7) - 7 = 70 - 7 = 63. "
            "It works every time! Does anyone else have maths tricks?",
        ),
        (
            parent_walsh := p1,
            "general",
            "Question about the homework posting feature",
            "Hi Ms Johnson — Alex mentioned that homework gets posted here sometimes. "
            "Is there a way to get notified when something new is posted? "
            "I want to make sure I don't miss anything. Thanks!",
        ),
    ]
    post_ids = _seed_posts(db, seed_posts, topic_ids)

    seed_replies = [
        (
            alex,
            post_ids.get(
                "Fractions don't have to be scary — here's how I think about them"
            ),
            "The pizza example actually helped me. I always got confused by the numbers.",
        ),
        (
            jordan,
            post_ids.get(
                "Fractions don't have to be scary — here's how I think about them"
            ),
            "I like thinking of it as slices. That makes more sense than the textbook.",
        ),
        (
            sam,
            post_ids.get(
                "Fractions don't have to be scary — here's how I think about them"
            ),
            "Fractions are my favourite part of maths this year!",
        ),
        (
            teacher,
            post_ids.get("I made a quiz game in Scratch!"),
            "Alex this is amazing! Would you be willing to share it with the class? "
            "I'd love to show everyone what you built.",
        ),
        (
            priya,
            post_ids.get("I made a quiz game in Scratch!"),
            "Yes please share the link! I want to try it.",
        ),
        (
            teacher,
            post_ids.get("Has anyone read Wonder by R.J. Palacio?"),
            "Priya I love that you read Wonder! It's one of my favourite books to recommend. "
            "The lesson about kindness is something I think about all the time.",
        ),
        (
            maya,
            post_ids.get("Has anyone read Wonder by R.J. Palacio?"),
            "I started reading it after you mentioned it. I'm only on chapter 3 but I already love it.",
        ),
        (
            teacher,
            post_ids.get("Is Minecraft actually coding?"),
            "Great question Jordan! Command blocks in Minecraft do teach real logic skills — "
            "conditions, loops, sequences. It counts! There's also something called "
            "Education Edition with proper coding lessons built in.",
        ),
        (
            alex,
            post_ids.get("Is Minecraft actually coding?"),
            "Yes! I use command blocks all the time. You're basically writing programs "
            "just without the typing. Tell your parents that!",
        ),
        (
            teacher,
            post_ids.get("I want to be a vet — where do I start?"),
            "Maya that's a wonderful goal! Focus on science especially biology. "
            "Reading books about animals is a great start. "
            "The local library might have a vet career section — worth checking!",
        ),
        (
            teacher,
            post_ids.get("I figured out a shortcut for multiplying by 9!"),
            "Sam this is exactly right and it's called the distributive property! "
            "You discovered a real maths concept on your own. Well done!",
        ),
        (
            alex,
            post_ids.get("I figured out a shortcut for multiplying by 9!"),
            "Wait this actually works. I just tried it with 9 x 8 and got 72. Mind blown.",
        ),
        (
            teacher,
            post_ids.get("Question about the homework posting feature"),
            "Hi! Notifications are coming soon. For now the best way is to check the feed "
            "each evening. I always post under the general or subject topic. "
            "Thanks for asking — this is great feedback!",
        ),
    ]
    _seed_replies(db, seed_replies)

    vote_targets = [
        v
        for v in [
            post_ids.get(
                "Fractions don't have to be scary — here's how I think about them"
            ),
            post_ids.get("Why do leaves change colour in fall?"),
            post_ids.get("Writing tip: show don't tell"),
            post_ids.get("I figured out a shortcut for multiplying by 9!"),
        ]
        if v
    ]
    _seed_votes(db, [alex, priya, jordan, maya, sam, p1, p2], vote_targets)
    print("\n5th grade demo seed complete.")


def _seed_grade_7(db):
    print("\n== seeding 7th grade demo ==")
    seed_users = [
        ("mr_okonkwo", "pass123", "7th grade English and social studies teacher."),
        ("dev_k", "pass123", "7th grade. Into gaming, coding, and debate."),
        ("zara_h", "pass123", "7th grade. I write poetry and love history."),
        ("liam_p", "pass123", "7th grade. Soccer, science, and bad jokes."),
        ("nina_v", "pass123", "7th grade. Art, music, and current events."),
        ("kai_b", "pass123", "7th grade. Into tech, environmental stuff, and chess."),
        ("parent_okafor", "pass123", "Dev's dad. Keeping an eye on things."),
    ]
    user_ids = _seed_users(db, seed_users)
    teacher = user_ids["mr_okonkwo"]
    dev = user_ids["dev_k"]
    zara = user_ids["zara_h"]
    liam = user_ids["liam_p"]
    nina = user_ids["nina_v"]
    kai = user_ids["kai_b"]
    parent = user_ids["parent_okafor"]

    _seed_follows(
        db,
        [
            (dev, teacher),
            (zara, teacher),
            (liam, teacher),
            (nina, teacher),
            (kai, teacher),
            (parent, teacher),
            (dev, kai),
            (kai, dev),
            (zara, nina),
            (nina, zara),
            (liam, dev),
        ],
    )

    topic_data = [
        ("english", "Writing, reading, grammar, and literature."),
        ("social-studies", "History, geography, civics, and current events."),
        ("science", "Earth science, life science, and experiments."),
        ("coding", "Programming and technology projects."),
        ("general", "Anything that doesn't fit elsewhere."),
    ]
    topic_ids = _seed_topics(db, topic_data)

    seed_posts = [
        (
            teacher,
            "english",
            "Why does writing with evidence actually matter?",
            "Anyone can have an opinion. What separates a strong argument from a weak one "
            "is evidence — specific facts, quotes, or examples that back up your claim. "
            "This week we're working on the PEEL structure: Point, Evidence, Explain, Link. "
            "Try applying it to your response journal today.",
        ),
        (
            teacher,
            "social-studies",
            "The difference between primary and secondary sources",
            "A primary source is created by someone who was there — a diary, a letter, a photo. "
            "A secondary source is created later by someone analysing what happened — a textbook, a documentary. "
            "Both are useful but for different reasons. "
            "Can you name one primary source from our current unit?",
        ),
        (
            dev,
            "coding",
            "I'm learning Python — anyone else?",
            "I started learning Python on my own using freeCodeCamp. "
            "I've done variables, loops, and functions so far. "
            "It's harder than Scratch but way more powerful. "
            "Anyone else learning on their own outside of school?",
        ),
        (
            zara,
            "english",
            "Is it okay to write poetry that doesn't rhyme?",
            "I've been writing poetry for a while and I almost never rhyme. "
            "My poems are more about imagery and rhythm than rhyming. "
            "Some people say it's not 'real' poetry if it doesn't rhyme. "
            "I disagree. What do you think?",
        ),
        (
            kai,
            "science",
            "Should we be more worried about climate change?",
            "I've been reading about climate change for a project and honestly it's stressing me out. "
            "Some sources say we have time to fix it and others say it's already too late. "
            "How do you know which sources to trust? "
            "And what can a 7th grader actually do about it?",
        ),
        (
            liam,
            "general",
            "Unpopular opinion: homework on weekends should be illegal",
            "I know this is controversial but I feel like weekends are supposed to be a break. "
            "My brain literally doesn't work the same way on Saturdays. "
            "Is there actual research about whether weekend homework helps?",
        ),
        (
            nina,
            "social-studies",
            "We visited the history museum — here's what surprised me",
            "Our class went to the history museum last week and the exhibit about the civil rights "
            "movement was not what I expected. There were so many people involved that I'd never "
            "heard of. History class always focuses on the same few names. "
            "I think we need to learn more stories.",
        ),
    ]
    post_ids = _seed_posts(db, seed_posts, topic_ids)

    seed_replies = [
        (
            dev,
            post_ids.get("Why does writing with evidence actually matter?"),
            "I always thought evidence was just for science. Didn't realise it applied to English too.",
        ),
        (
            zara,
            post_ids.get("Why does writing with evidence actually matter?"),
            "PEEL actually helped me structure my last essay. My argument felt way stronger.",
        ),
        (
            teacher,
            post_ids.get("Is it okay to write poetry that doesn't rhyme?"),
            "Zara this is a great question. Free verse poetry is a legitimate and respected form. "
            "Walt Whitman, Maya Angelou, and many of the most celebrated poets wrote without rhyme. "
            "Don't let anyone tell you it's not real poetry.",
        ),
        (
            nina,
            post_ids.get("Is it okay to write poetry that doesn't rhyme?"),
            "Agree completely. Forcing a rhyme usually makes the poem worse not better.",
        ),
        (
            teacher,
            post_ids.get("Should we be more worried about climate change?"),
            "Kai this is exactly the kind of critical thinking I want to see. "
            "On evaluating sources: look for peer-reviewed research, government science agencies, "
            "and established universities. Be cautious of single news articles or opinion pieces. "
            "And yes — local action matters more than you might think.",
        ),
        (
            dev,
            post_ids.get("Should we be more worried about climate change?"),
            "I've been looking into this too. The IPCC reports are supposed to be the most reliable. "
            "They're written by hundreds of scientists.",
        ),
        (
            teacher,
            post_ids.get("Unpopular opinion: homework on weekends should be illegal"),
            "There is actually research on this Liam. Studies suggest diminishing returns on homework "
            "beyond a certain amount, especially for middle schoolers. "
            "I'll look for the paper and share it.",
        ),
        (
            kai,
            post_ids.get("Unpopular opinion: homework on weekends should be illegal"),
            "I would cite this as a primary source: my grades go down after a stressful weekend.",
        ),
        (
            teacher,
            post_ids.get("We visited the history museum — here's what surprised me"),
            "Nina I'm really glad that resonated with you. "
            "History has traditionally centred certain voices over others. "
            "One of our goals this semester is to actively seek out those untold stories.",
        ),
        (
            zara,
            post_ids.get("We visited the history museum — here's what surprised me"),
            "The Fannie Lou Hamer exhibit was the part that got me. I'd never heard of her before.",
        ),
    ]
    _seed_replies(db, seed_replies)

    vote_targets = [
        v
        for v in [
            post_ids.get("Why does writing with evidence actually matter?"),
            post_ids.get("The difference between primary and secondary sources"),
            post_ids.get("Should we be more worried about climate change?"),
        ]
        if v
    ]
    _seed_votes(db, [dev, zara, liam, nina, kai, parent], vote_targets)
    print("\n7th grade demo seed complete.")


def _seed_grade_8(db):
    print("\n== seeding 8th grade demo ==")
    seed_users = [
        (
            "ms_reyes",
            "pass123",
            "8th grade science and STEM teacher. College prep starts now.",
        ),
        ("omar_a", "pass123", "8th grade. Into robotics, debate, and astrophysics."),
        (
            "claire_m",
            "pass123",
            "8th grade. Environmental science, writing, and track.",
        ),
        ("theo_b", "pass123", "8th grade. Music production, maths, and philosophy."),
        (
            "aisha_d",
            "pass123",
            "8th grade. Pre-med interest, biology nerd, chess club.",
        ),
        ("felix_n", "pass123", "8th grade. Software dev, game design, and jazz."),
        ("parent_ahmed", "pass123", "Omar's mom. Watching from a distance."),
    ]
    user_ids = _seed_users(db, seed_users)
    teacher = user_ids["ms_reyes"]
    omar = user_ids["omar_a"]
    claire = user_ids["claire_m"]
    theo = user_ids["theo_b"]
    aisha = user_ids["aisha_d"]
    felix = user_ids["felix_n"]
    parent = user_ids["parent_ahmed"]

    _seed_follows(
        db,
        [
            (omar, teacher),
            (claire, teacher),
            (theo, teacher),
            (aisha, teacher),
            (felix, teacher),
            (parent, teacher),
            (omar, felix),
            (felix, omar),
            (aisha, claire),
            (claire, aisha),
            (theo, omar),
        ],
    )

    topic_data = [
        ("science", "Biology, chemistry, physics, and STEM projects."),
        ("maths", "Algebra, geometry, and problem solving."),
        ("english", "Writing, literature, and critical analysis."),
        ("coding", "Software, robotics, and technology."),
        ("general", "Discussion, questions, and everything else."),
    ]
    topic_ids = _seed_topics(db, topic_data)

    seed_posts = [
        (
            teacher,
            "science",
            "How to read a scientific paper (yes, in 8th grade)",
            "Reading primary research papers might sound intimidating but there's a strategy. "
            "Start with the abstract for the summary. Then skip to the discussion and conclusion. "
            "Only go back to the methods and results if you need specifics. "
            "This week I want each of you to find one paper related to your project topic "
            "and post what you found in the replies.",
        ),
        (
            teacher,
            "general",
            "High school is closer than you think — let's talk about it",
            "Some of you are thinking about high school electives, AP courses, or even college already. "
            "That's not too early. The habits you build this year — how you manage work, "
            "ask for help, and push through hard problems — those travel with you. "
            "What's one thing you want to get better at before September?",
        ),
        (
            omar,
            "science",
            "I want to study astrophysics — is that realistic?",
            "I've wanted to study astrophysics since I was about 9. "
            "Everyone tells me it's too hard or there are no jobs. "
            "But I've been reading about careers at NASA and ESA and there seem to be plenty. "
            "Has anyone done research on STEM career paths? "
            "I'd also love to know what high school courses to take.",
        ),
        (
            claire,
            "science",
            "My project on microplastics in local water sources",
            "For my science fair project I collected water samples from three local sites "
            "and tested them for microplastic particles. All three had detectable levels. "
            "The highest was downstream from the industrial area. "
            "I'm writing up the methodology now. Happy to share it if anyone wants to peer review.",
        ),
        (
            theo,
            "maths",
            "Is there beauty in mathematics or is that just something teachers say?",
            "My maths teacher keeps talking about the beauty of equations and I'm trying to understand it. "
            "I get that some proofs are elegant but is there something deeper? "
            "I play music and there are patterns there that feel beautiful. "
            "Is maths like that? Or is beauty just a metaphor?",
        ),
        (
            aisha,
            "science",
            "Question about the ethics of animal testing in medicine",
            "We're doing a unit on medical research and I keep thinking about animal testing. "
            "I want to be a doctor and I understand why it's done but it still feels wrong. "
            "Are there alternatives that are becoming more common? "
            "I read something about organoids but I'm not sure I understood it correctly.",
        ),
        (
            felix,
            "coding",
            "I'm building a mobile app — here's what I've learned so far",
            "I've been working on a simple habit tracking app using React Native for about two months. "
            "Things I've learned: state management is hard, APIs are confusing at first, "
            "and debugging on a physical device is very different from the simulator. "
            "If anyone wants to pair on a project or just talk about dev stuff, I'm around.",
        ),
    ]
    post_ids = _seed_posts(db, seed_posts, topic_ids)

    seed_replies = [
        (
            omar,
            post_ids.get("How to read a scientific paper (yes, in 8th grade)"),
            "I found a paper on exoplanet atmospheres from the James Webb telescope team. "
            "The abstract alone took me 20 minutes but I got through it.",
        ),
        (
            aisha,
            post_ids.get("How to read a scientific paper (yes, in 8th grade)"),
            "I found one on CRISPR gene editing in cancer treatment. "
            "The methods section was basically a different language but the conclusion was clear.",
        ),
        (
            teacher,
            post_ids.get("I want to study astrophysics — is that realistic?"),
            "Omar it is absolutely realistic. The field is growing, not shrinking. "
            "For high school: take the most advanced maths and physics available to you. "
            "AP Physics and AP Calculus are the ones that matter most. "
            "I'll send you some links to summer STEM programmes too.",
        ),
        (
            felix,
            post_ids.get("I want to study astrophysics — is that realistic?"),
            "There are also software roles at space agencies. "
            "A lot of telescope and satellite work is basically software engineering.",
        ),
        (
            teacher,
            post_ids.get("My project on microplastics in local water sources"),
            "Claire this is genuinely impressive research. "
            "I'd like to nominate this for the district science fair if you're open to it. "
            "Please share your methodology — I'd love the class to see your process.",
        ),
        (
            aisha,
            post_ids.get("My project on microplastics in local water sources"),
            "I'd love to peer review this. Send it over whenever it's ready.",
        ),
        (
            teacher,
            post_ids.get(
                "Is there beauty in mathematics or is that just something teachers say?"
            ),
            "Theo this might be my favourite question anyone has ever posted here. "
            "Look up Euler's identity: e^(iπ) + 1 = 0. Five fundamental constants, one equation. "
            "Many mathematicians consider it the most beautiful equation ever written. "
            "Your music instinct is exactly right — it is like that.",
        ),
        (
            omar,
            post_ids.get(
                "Is there beauty in mathematics or is that just something teachers say?"
            ),
            "The Fibonacci sequence appearing in nature always gets me. "
            "Sunflower seeds, galaxy spirals, nautilus shells. Same pattern everywhere.",
        ),
        (
            teacher,
            post_ids.get("Question about the ethics of animal testing in medicine"),
            "Aisha you understood the organoids reference correctly. "
            "Organoids are lab-grown miniature organs used to test drugs. "
            "They're not yet a full replacement but they're reducing animal use significantly. "
            "This is an active and important area of bioethics — worth pursuing.",
        ),
        (
            claire,
            post_ids.get("Question about the ethics of animal testing in medicine"),
            "I wrote a paper on this last year. The three Rs framework — Replace, Reduce, Refine — "
            "is the standard ethical guideline for research involving animals.",
        ),
        (
            omar,
            post_ids.get("I'm building a mobile app — here's what I've learned so far"),
            "I'd love to pair on something. I've been learning Python but want to get into app dev.",
        ),
    ]
    _seed_replies(db, seed_replies)

    vote_targets = [
        v
        for v in [
            post_ids.get("How to read a scientific paper (yes, in 8th grade)"),
            post_ids.get("High school is closer than you think — let's talk about it"),
            post_ids.get("My project on microplastics in local water sources"),
            post_ids.get(
                "Is there beauty in mathematics or is that just something teachers say?"
            ),
        ]
        if v
    ]
    _seed_votes(db, [omar, claire, theo, aisha, felix, parent], vote_targets)
    print("\n8th grade demo seed complete.")


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
            seed_menu()
        elif choice == "16":
            testing_menu()
        elif choice == "0":
            print("bye.")
            break
        else:
            print("invalid option.")
