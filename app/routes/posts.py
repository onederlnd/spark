# app/routes/posts.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
)
from app.models.post import create_post, get_post, get_replies, vote_post, is_bookmarked
from app.models.topic import get_all_topics
from app.routes.feed import login_required

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_post():
    topics = get_all_topics()
    if request.method == "POST":
        title = request.form["title"].strip()
        body = request.form["body"].strip()
        topic_id = request.form.get("topic_id") or None

        if not title or not body:
            return render_template(
                "new_post.html", topic=topics, error="Title and body required"
            )

        post_id = create_post(session["user_id"], title, body, topic_id)
        return redirect(url_for("posts.view_post", post_id=post_id))

    return render_template("new_post.html", topics=topics)


@posts_bp.route("/<int:post_id>")
@login_required
def view_post(post_id):
    post = get_post(post_id)
    if not post:
        return "Post not found", 404
    replies = get_replies(post_id)
    topics = get_all_topics()
    bookmarked = is_bookmarked(session["user_id"], post_id)
    return render_template(
        "post.html", post=post, replies=replies, topics=topics, bookmarked=bookmarked
    )


@posts_bp.route("/<int:post_id>/reply", methods=["POST"])
@login_required
def reply(post_id):
    body = request.form["body"].strip()
    if body:
        create_post(session["user_id"], "re: reply", body, parent_id=post_id)
    return redirect(url_for("posts.view_post", post_id=post_id))


@posts_bp.route("/<int:post_id>/vote", methods=["POST"])
@login_required
def vote(post_id):
    value = int(request.form.get("value", 1))
    vote_post(session["user_id"], post_id, value)
    return redirect(request.referrer or url_for("feed.index"))
