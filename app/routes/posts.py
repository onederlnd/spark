# app/routes/posts.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from app.models.post import (
    create_post,
    get_post,
    get_replies,
    is_bookmarked,
    update_post,
    delete_post,
)
from app.models.user import coppa_required
from app.models.topic import get_all_topics
from app.models.notifications import create_notification
from app.models.reactions import (
    add_or_update_reaction,
    get_reaction,
    get_reaction_counts,
    get_reaction_users,
    format_reactor_names,
    REACTION_EMOJI,
)
from app.utils.auth import login_required
from app.utils.rate_limit import rate_limit
from app.utils.sanitize import sanitize_plain, sanitize_bbcode
from app.utils.content_filter import get_all_words

# define blueprint
posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


# --- posts
TITLE_MAX = 200
BODY_MAX = 10000


def _contains_blocked_word(text):
    words = [row["word"].lower() for row in get_all_words()]
    text_lower = text.lower()
    return any(word in text_lower for word in words)


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)  # limit to  posts per minute
@coppa_required
def new_post():
    topics = get_all_topics()
    if request.method == "POST":
        title = sanitize_plain(request.form.get("title", ""), max_length=TITLE_MAX)
        body = sanitize_plain(request.form.get("body", ""), max_length=BODY_MAX)
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

        if _contains_blocked_word(title) or _contains_blocked_word(body):
            return render_template(
                "new_post.html",
                topics=topics,
                error="Your post contains a word that is not allowed.",
            )
        post_id = create_post(session["user_id"], title, body, topic_id)
        return redirect(url_for("posts.view_post", post_id=post_id))

    return render_template("new_post.html", topics=topics)


@posts_bp.route("/<int:post_id>")
@login_required
@coppa_required
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
    user_reaction = get_reaction(post_id, session["user_id"])
    reaction_counts = get_reaction_counts(post_id)
    reaction_user_raw = get_reaction_users(post_id)
    reaction_tooltips = {
        key: ", ".join(format_reactor_names(usernames))
        for key, usernames in reaction_user_raw.items()
    }
    return render_template(
        "post.html",
        post=post,
        replies=replies,
        topics=topics,
        bookmarked=bookmarked,
        user_reaction=user_reaction,
        reaction_emoji=REACTION_EMOJI,
        reaction_counts=reaction_counts,
        reaction_tooltips=reaction_tooltips,
    )


@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@coppa_required
@rate_limit(max_requests=10, window_seconds=60)
def edit_post(post_id):
    post = get_post(post_id)
    if not post:
        return "Post not found", 404

    # only the author can edit
    if post["user_id"] != session["user_id"]:
        return "Forbidden", 403

    if request.method == "POST":
        title = sanitize_plain(request.form.get("title", ""), max_length=TITLE_MAX)
        body = sanitize_bbcode(request.form.get("body", ""), max_length=BODY_MAX)

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
@coppa_required
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
@coppa_required
def reply(post_id):
    body = sanitize_bbcode(request.form.get("body", ""), max_length=BODY_MAX)
    parent = get_post(post_id)

    if not body:
        return redirect(url_for("post.view_post", post_id=post_id))

    if _contains_blocked_word(body):
        flash("Your reply contains a word that is not allowed.", "error")
        return redirect(url_for("posts.view_post", post_id=post_id))

    if parent:
        create_post(
            session["user_id"],
            "re: reply",
            body,
            classroom_id=parent["classroom_id"],
            parent_id=post_id,
        )
        if parent and parent["user_id"] != session["user_id"]:
            create_notification(
                user_id=parent["user_id"],
                type="reply",
                message=f"@{session['username']} replied to your post",
                link=f"/posts/{post_id}",
            )
    return redirect(url_for("posts.view_post", post_id=post_id))


@posts_bp.route("/<int:post_id>/react", methods=["POST"])
@login_required
@rate_limit(max_requests=30, window_seconds=60)
@coppa_required
def react(post_id):
    post = get_post(post_id)
    if not post:
        return "Post not found", 404
    reaction = request.form.get("reaction", "").strip()
    add_or_update_reaction(post_id, session["user_id"], reaction)
    return redirect(request.referrer or url_for("feed.index"))
