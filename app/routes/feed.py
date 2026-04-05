# app/routes/feed.py

from flask import Blueprint, request, render_template, session, redirect, url_for
from app.models.post import get_feed, get_following_feed
from app.models.topic import get_all_topics, get_topic_by_name
from app.models.user import coppa_required
from app.models.block import get_blocked_ids
from app.models.announcement import get_announcements
from app.models.assignments import get_assignments
from app.utils.auth import login_required


feed_bp = Blueprint("feed", __name__, url_prefix="")


@feed_bp.before_request
def block_parents():
    if session.get("role") == "parent":
        return redirect(url_for("parent.dashboard"))


# --- auth decorator
@feed_bp.route("/feed/", strict_slashes=False)
@login_required
@coppa_required
def index():
    page = request.args.get("page", 1, type=int)
    feed_type = request.args.get("feed", "all")
    topics = get_all_topics()
    blocked = get_blocked_ids(session["user_id"])

    if feed_type == "following":
        posts, has_next = get_following_feed(
            user_id=session["user_id"], page=page, blocked_ids=blocked
        )
    else:
        posts, has_next = get_feed(
            user_id=session["user_id"],
            page=page,
            blocked_ids=blocked,
        )
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
    posts, has_next = get_feed(
        page=page,
        topic_id=t["id"],
        blocked_ids=blocked,
        user_id=session["user_id"],
    )
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


@feed_bp.route("/feed/following")
@login_required
@coppa_required
def following_feed():
    page = request.args.get("page", 1, type=int)
    topics = get_all_topics()
    blocked = get_blocked_ids(session["user_id"])
    posts, has_next = get_following_feed(
        page=page,
        blocked_ids=blocked,
        user_id=session["user_id"],
    )
    return render_template(
        "feed.html",
        posts=posts,
        topics=topics,
        page=page,
        has_next=has_next,
        feed_type="following",
    )


@feed_bp.route("/feed/announcements")
@login_required
@coppa_required
def announcement_feed():
    page = request.args.get("page", 1, type=int)
    topics = get_all_topics()
    announcements, has_next = get_announcements(session["user_id"], page=page)
    return render_template(
        "feed.html",
        announcements=announcements,
        topics=topics,
        page=page,
        has_next=has_next,
        feed_type="announcements",
    )


@feed_bp.route("/feed/assignments")
@login_required
@coppa_required
def assignments_feed():
    page = request.args.get("page", 1, type=int)
    topics = get_all_topics()
    assignments, has_next = get_assignments(session["user_id"], page=page)
    return render_template(
        "feed.html",
        assignments=assignments,
        topics=topics,
        page=page,
        has_next=has_next,
        feed_type="assignments",
    )
