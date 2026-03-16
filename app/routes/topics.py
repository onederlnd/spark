from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.topic import get_all_topics_with_counts, create_topic
from app.models.user import coppa_required
from app.routes.feed import login_required
from app.utils.sanitize import sanitize_plain

topics_bp = Blueprint("topics", __name__, url_prefix="/topics")


@topics_bp.route("/", strict_slashes=False)
@login_required
@coppa_required
def index():
    topics = get_all_topics_with_counts()
    return render_template("topics.html", topics=topics)


@topics_bp.route("/new", methods=["GET", "POST"])
@login_required
@coppa_required
def new_topic():
    import re

    if request.method == "POST":
        name = sanitize_plain(request.form.get("name", "")).lower()
        description = sanitize_plain(
            request.form.get("description", ""), max_length=300
        )
        if not re.match(r"^[a-z0-9-]+$", name):
            flash("Topic name can only contain letters, numbers, and hyphens", "error")
            return render_template("new_topic.html")

        if len(name) < 2 or len(name) > 30:
            flash("Topic length must be between 2 and 30 characters.")
            return render_template("new_topic.html")

        success, error = create_topic(name, description)
        if success:
            flash(f"/t/{name} created!", "success")
            return redirect(url_for("feed.topic", topic_name=name))
        else:
            flash("Topic already exists", "error")

    return render_template("new_topic.html")
