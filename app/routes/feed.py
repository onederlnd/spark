# app/routes/feed.py

from flask import Blueprint, render_template, session, redirect, url_for
from app.models.post import get_feed
from app.models.topic import get_all_topics, get_topic_by_name

feed_bp = Blueprint("feed", __name__)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@feed_bp.route("/")
@login_required
def index():
    posts = get_feed()
    topics = get_all_topics()
    return render_template("feed.html", posts=posts, topics=topics)


@feed_bp.route("/t/<topic_name>")
@login_required
def topic(topic_name):
    t = get_topic_by_name(topic_name)
    if not t:
        return "Topic not found", 404
    posts = get_feed(topic_id=t["id"])
    topics = get_all_topics()
    return render_template("feed.html", posts=posts, topics=topics, active_topic=t)
