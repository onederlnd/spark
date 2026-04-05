# app/routes/settings.py

from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from app.models.user import (
    get_db_followers,
    get_db_following,
    get_user_by_id,
    update_user_bio,
    check_password,
    update_user_password,
)

from app.utils.auth import login_required

settings_bp = Blueprint("settings", __name__, url_prefix="/profile")


# GET /settings - render settings page
@settings_bp.route("/settings")
@login_required
def show_settings():
    user = get_user_by_id(session["user_id"])
    followers = get_db_followers(session["user_id"])
    following = get_db_following(session["user_id"])
    return render_template(
        "settings.html", user=user, followers=followers, following=following
    )


# POST /settings/bio - update bio
@settings_bp.route("/settings/bio", methods=["POST"])
@login_required
def update_bio():
    "Update the user's bio"
    # get bio values title body in posts
    bio = request.form["bio"]
    update_user_bio(session["user_id"], bio)
    return redirect(url_for("settings.show_settings"))


# POST /settings/password - verify current password then update
@settings_bp.route("/settings/password", methods=["POST"])
@login_required
def update_password():
    """Updates the users password"""
    # verify current pass
    current_password = request.form["current_password"]
    new_password = request.form["new_password"]

    username = check_password(session["username"], current_password)
    if not username:
        flash("Current password is incorrect", "error")
        return redirect(url_for("settings.show_settings"))

    if len(new_password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("settings.show_settings"))

    update_user_password(session["user_id"], new_password)
    flash("Password updated", "success")
    return redirect(url_for("settings.show_settings"))
