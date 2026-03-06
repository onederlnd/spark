# app/routes/profile.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from app.models.user import get_user_by_username
from app.models.post import get_posts_by_user, get_bookmarks, toggle_bookmark
from app.routes.feed import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile/<username>")
@login_required
def view_profile(username):
    user = get_user_by_username(username)
    if not user:
        return "User not found", 404

    posts = get_posts_by_user(user["id"])
    bookmarks = []

    if session["username"] == username:
        bookmarks = get_bookmarks(user["id"])

    return render_template(
        "profile.html", profile_user=user, posts=posts, bookmarks=bookmarks
    )


@profile_bp.route("/posts/<int:post_id>/bookmark", methods=["POST"])
@login_required
def bookmark(post_id):
    toggle_bookmark(session["user_id"], post_id)
    return redirect(request.referrer or url_for("feed.index"))
