# app/routes/posts.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
)
from app.models.post import (
    create_post,
    get_post,
    get_replies,
    vote_post,
    is_bookmarked,
    update_post,
    delete_post,
)
from app.models.topic import get_all_topics
from app.models.notifications import create_notification
from app.routes.feed import login_required
from app.utils.rate_limit import rate_limit

# define blueprint
posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


# --- posts
TITLE_MAX = 200
BODY_MAX = 10000


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)  # limit to  posts per minute
def new_post():
    topics = get_all_topics()
    if request.method == "POST":
        title = request.form["title"].strip()
        body = request.form["body"].strip()
        if len(title) > TITLE_MAX:
            error = f"Title must be under {TITLE_MAX} characters"
            return render_template("new_post.html", topics=topics, error=error)
        if len(body) > BODY_MAX:
            error = f"Body must be under {BODY_MAX} character"
            return render_template("new_post.html", topics=topics, error=error)

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
@rate_limit(
    max_requests=10, window_seconds=60
)  # limit to 10 views per minute to prevent abuse
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


@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def edit_post(post_id):
    post = get_post(post_id)
    if not post:
        return "Post not found", 404

    # only the author can edit
    if post["user_id"] != session["user_id"]:
        return "Forbidden", 403

    if request.method == "POST":
        title = request.form["title"].strip()
        body = request.form["body"].strip()

        # if title or body are empty
        if not title or not body:
            return render_template(
                "edit_post.html", post=post, error="Title and body required"
            )

        update_post(post_id, title, body)
        return redirect(url_for("posts.view_post", post_id=post_id))

    return render_template("edit_post.html", post=post)


@posts_bp.route("/<int:post_id>/delete", methods=["POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def delete(post_id):
    post = get_post(post_id)
    if not post:
        return "Post not found", 404

    # check if author (only author can delete)
    if post["user_id"] != session["user_id"]:
        return "Forbidden", 403

    delete_post(post_id)
    return redirect(url_for("feed.index"))


# --- reply
@posts_bp.route("/<int:post_id>/reply", methods=["POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def reply(post_id):
    body = request.form["body"].strip()
    if body:
        create_post(session["user_id"], "re: reply", body, parent_id=post_id)
        parent = get_post(post_id)
        if parent and parent["user_id"] != session["user_id"]:
            create_notification(
                user_id=parent["user_id"],
                type="reply",
                message=f"@{session['username']} replied to your post",
                link=f"/posts/{post_id}",
            )
    return redirect(url_for("posts.view_post", post_id=post_id))


@posts_bp.route("/<int:post_id>/vote", methods=["POST"])
@login_required
@rate_limit(max_requests=30, window_seconds=60)
def vote(post_id):
    value = int(request.form.get("value", 1))
    vote_post(session["user_id"], post_id, value)
    return redirect(request.referrer or url_for("feed.index"))
