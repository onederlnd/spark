import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


def time_ago(dt_str):
    if not dt_str:
        return ""
    try:
        if isinstance(dt_str, str):
            dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
        else:
            dt = dt_str
        dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        elif seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        elif seconds < 604800:
            d = seconds // 86400
            return f"{d}d ago"
        else:
            return dt.strftime("%b %d, %Y")
    except Exception:
        return str(dt_str)


def create_app(config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "2ejfof2jf2ojwfxasf")
    app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL", "devstack.db")
    app.config["TESTING"] = False

    if config:
        app.config.update(config)

    # Initialize database
    from app.models import init_db

    init_db(app)

    # import blueprints
    from app.routes.auth import auth_bp
    from app.routes.feed import feed_bp
    from app.routes.posts import posts_bp
    from app.routes.profile import profile_bp
    from app.routes.topics import topics_bp
    from app.routes.search import search_bp
    from app.routes.notifications import notifications_bp

    # register app
    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)

    # register other
    app.jinja_env.filters["time_ago"] = time_ago

    # @app.context_processor
    # def inject_unread_count():
    #     """Inject unread notification count into all templates."""
    #     from flask import session
    #     from app.models.notifications import get_unread_count
    #
    #     if "user_id" in session:
    #         return {"unread_count": get_unread_count(session["user_id"])}
    #     return {"unread_count": 0}

    return app
