# app/routes/feed.py

from flask import Blueprint, request, render_template, session
from app.models.post import get_feed, get_following_feed
from app.models.topic import get_all_topics, get_topic_by_name
from app.models.user import coppa_required
from app.models.block import get_blocked_ids
from app.utils.auth import login_required


feed_bp = Blueprint("feed", __name__, url_prefix="/feed")


# --- auth decorator
@feed_bp.route("/", strict_slashes=False)
@login_required
@coppa_required
def index():
    page = request.args.get("page", 1, type=int)
    feed_type = request.args.get("feed", "all")
    topics = get_all_topics()
    blocked = get_blocked_ids(session["user_id"])

    if feed_type == "following":
        posts, has_next = get_following_feed(
            session["user_id"], page=page, blocked_ids=blocked
        )
    else:
        posts, has_next = get_feed(page=page, blocked_ids=blocked)
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
    blocked = get_blocked_ids(session["user_id"])
    posts, has_next = get_feed(page=page, topic_id=t["id"], blocked_ids=blocked)
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
