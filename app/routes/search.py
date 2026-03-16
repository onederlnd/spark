from flask import Blueprint, render_template, request
from app.models.post import search_posts
from app.models.topic import search_topics
from app.models.user import coppa_required
from app.routes.feed import login_required

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
@login_required
@coppa_required
def search():
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "posts")
    page = request.args.get("page", 1, type=int)

    posts = []
    topics = []
    has_next = False

    if query:
        if search_type == "topics":
            topics = search_topics(query)
        else:
            posts, has_next = search_posts(query, page=page)

    return render_template(
        "search.html",
        query=query,
        search_type=search_type,
        posts=posts,
        topics=topics,
        page=page,
        has_next=has_next,
    )
