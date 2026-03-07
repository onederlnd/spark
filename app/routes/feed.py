# app/routes/feed.py

from flask import Blueprint, request, render_template, session, redirect, url_for
from app.models.post import get_feed, get_following_feed
from app.models.topic import get_all_topics, get_topic_by_name
from functools import wraps

feed_bp = Blueprint("feed", __name__)


def login_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


# --- auth decorator
@feed_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    feed_type = request.args.get("feed", "all")
    topics = get_all_topics()

    if feed_type == "following":
        posts, has_next = get_following_feed(session["user_id"], page=page)
    else:
        posts, has_next = get_feed(page=page)
    return render_template(
        "feed.html",
        posts=posts,
        topics=topics,
        page=page,
        has_next=has_next,
        feed_type=feed_type,
    )


@feed_bp.route("/t/<topic_name>")
@login_required
def topic(topic_name):
    t = get_topic_by_name(topic_name)
    if not t:
        return "Topic not found", 404

    page = request.args.get("page", 1, type=int)
    posts, has_next = get_feed(page=page, topic_id=t["id"])
    topics = get_all_topics()
    return render_template(
        "feed.html",
        posts=posts,
        topics=topics,
        page=page,
        has_next=has_next,
        active_topic=t,
        feed_type="all",
    )
