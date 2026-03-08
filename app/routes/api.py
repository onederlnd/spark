# app/routes/api.py

from flask import Blueprint, jsonify, request, session
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
def get_posts():
    """Retrieve posts with optional pagination and topic filter"""
    page = request.args.get("page", 1, type=int)
    rows = get_feed(page=page)
    return jsonify([dict(row) for row in rows])


# --- GET /api/posts/<id>
@api_bp.route("/posts/<int:post_id>")
def get_single_post(post_id):
    """Retrieve a single post by ID, including its replies"""
    post = get_post(post_id)
    if not post:
        return jsonify({"error": "not found"}), 404
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

    post_id = create_post(session["user_id"], title, body, topic_id)
    return jsonify({"post_id": post_id}), 201


# --- GET /api/topics
@api_bp.route("/topics")
def get_topics():
    """Retrieve all topics"""
    rows = get_all_topics()
    return jsonify([dict(row) for row in rows])


# --- GET /api/profile/<username>
@api_bp.route("/profile/<username>")
def get_profile(username):
    """Retrieve user profile and their posts"""
    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = get_posts_by_user(user["id"])
    return jsonify(
        {
            "username": user["username"],
            "bio": user["bio"],
            "posts": [dict(p) for p in posts],
        }
    )
