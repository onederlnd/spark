# app/routes/profile.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from app.models.user import (
    get_user_by_username,
    is_following,
    unfollow_user,
    follow_user,
    get_following_count,
    get_followers_count,
    coppa_required,
)
from app.models.post import get_posts_by_user, get_bookmarks, toggle_bookmark
from app.models.notifications import create_notification
from app.routes.feed import login_required
from app.utils.rate_limit import rate_limit

profile_bp = Blueprint("profile", __name__)


# --- profile
@profile_bp.route("/profile/<username>")
@login_required
@rate_limit(max_requests=10, window_seconds=60)  # limit to 10 profile views per minute
@coppa_required
def view_profile(username):
    user = get_user_by_username(username)
    if not user:
        return "User not found", 404

    posts = get_posts_by_user(user["id"])
    bookmarks = get_bookmarks(user["id"]) if session["user_id"] == user["id"] else []
    following = is_following(session["user_id"], user["id"])
    followers_count = get_followers_count(user["id"])
    following_count = get_following_count(user["id"])
    bookmarks = get_bookmarks(user["id"])

    return render_template(
        "profile.html",
        profile_user=user,
        posts=posts,
        bookmarks=bookmarks,
        following=following,
        followers_count=followers_count,
        following_count=following_count,
    )


# --- follow/unfollow
@profile_bp.route("/profile/<username>/follow", methods=["POST"])
@login_required
@rate_limit(max_requests=20, window_seconds=60)
@coppa_required
def follow(username):
    """Toggle follow state for a user"""
    user = get_user_by_username(username)
    if not user:
        return "User not found", 404

    # prevent self following
    if user["id"] == session["user_id"]:
        return "Can't follow yourself", 400

    if is_following(session["user_id"], user["id"]):
        unfollow_user(session["user_id"], user["id"])
    else:
        follow_user(session["user_id"], user["id"])
        # --- notifications
        create_notification(
            user_id=user["id"],
            type="follow",
            message=f"@{session['username']} followed you",
            link=f"/profile/{session['username']}",
        )

    return redirect(url_for("profile.view_profile", username=username))


@profile_bp.route("/posts/<int:post_id>/bookmark", methods=["POST"])
@login_required
@rate_limit(max_requests=30, window_seconds=60)
def bookmark(post_id):
    toggle_bookmark(session["user_id"], post_id)
    return redirect(request.referrer or url_for("feed.index"))
