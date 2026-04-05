# app/routes/api.py

from flask import Blueprint, jsonify, request, session
from app.models import get_db
from app.models.post import (
    get_feed,
    get_post,
    get_replies,
    create_post,
    get_posts_by_user,
)
from app.models.topic import get_all_topics
from app.models.user import get_user_by_username
from functools import wraps
from app.utils.sanitize import sanitize_bbcode
from app.utils.bbcode import render_bbcode

api_bp = Blueprint("api", __name__, url_prefix="/api")


def api_login_required(f):
    """Return 401 JSON instead of redirecting to login page"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


# --- GET /api/posts


@api_bp.route("/posts")
@api_login_required
def get_posts():
    page = request.args.get("page", 1, type=int)
    rows, has_next = get_feed(page=page, user_id=session.get("user_id"))
    return jsonify([dict(row) for row in rows])


@api_bp.route("/posts/<int:post_id>")
@api_login_required
def get_single_post(post_id):
    post = get_post(post_id)
    if not post:
        return jsonify({"error": "not found"}), 404
    if post["classroom_id"]:
        from app.models.classroom import get_member_role

        role = get_member_role(post["classroom_id"], session["user_id"])
        if not role:
            return jsonify({"error": "Forbidden"}), 403
    replies = get_replies(post_id)
    return jsonify({"post": dict(post), "replies": [dict(r) for r in replies]})


# --- POST /api/posts
@api_bp.route("/posts", methods=["POST"])
@api_login_required
def create_new_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    topic_id = data.get("topic_id")

    if not title or not body:
        return jsonify({"error": "Title and body are required"}), 400

    post_id = create_post(
        session["user_id"], session["username"], title, body, topic_id=topic_id
    )

    return jsonify({"post_id": post_id}), 201


# --- GET /api/topics
@api_bp.route("/topics")
def get_topics():
    """Retrieve all topics"""
    rows = get_all_topics()
    return jsonify([dict(row) for row in rows])


# --- GET /api/profile/<username>
@api_bp.route("/profile/<username>")
@api_login_required
def get_profile(username):
    """Retrieve user profile and their posts"""
    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = get_posts_by_user(user["id"], viewer_id=session["user_id"])
    return jsonify(
        {
            "username": user["username"],
            "bio": user["bio"],
            "posts": [dict(p) for p in posts],
        }
    )


@api_bp.route("/preview", methods=["POST"])
def preview():
    """Render BBCode body to html for live preview"""
    data = request.get_json(silent=True)
    body = data.get("body", "")
    if not isinstance(body, str):
        return jsonify({"html": ""}), 400

    # sanitize then render - sam pipeline as template filter
    clean = sanitize_bbcode(body)
    html = render_bbcode(clean)
    return jsonify({"html": html})


@api_bp.route("/users/search")
@api_login_required
def search_users():
    q = request.args.get("q", "").strip()
    if len(q) < 1:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        """
        SELECT username FROM users
        WHERE username LIKE ?
        AND coppa_status = 'approved'
        AND provisional = 0
        LIMIT 8
        """,
        (f"{q}%",),
    ).fetchall()

    return jsonify([r["username"] for r in rows])
