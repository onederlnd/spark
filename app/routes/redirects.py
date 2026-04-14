# app/routes/redirect.py

from flask import Blueprint, redirect, url_for

redirects_bp = Blueprint("redirects", __name__)


@redirects_bp.route("/register")
def register():
    return redirect(url_for("auth.register"), 301)


@redirects_bp.route("/login")
def login():
    return redirect(url_for("auth.login"), 301)
