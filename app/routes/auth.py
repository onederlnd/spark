# app/routes/auth.py

from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.models.user import create_user, check_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    from app.utils.sanitize import sanitize_username, sanitize_plain

    if request.method == "POST":
        username = sanitize_username(request.form.get("username"))
        password = request.form["password"]
        bio = sanitize_plain(request.form.get("bio", ""), max_length=300)

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("auth/register.html")

        success, error = create_user(username, password, bio)
        if success:
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(error, "error")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = check_password(username, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("feed.index"))
        else:
            flash("Invalid username or password", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("feed.index"))
