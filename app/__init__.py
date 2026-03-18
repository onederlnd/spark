import os
from flask import Flask, render_template
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask_wtf.csrf import CSRFProtect
from app.sockets import init_socketio
from app.utils.bbcode import render_bbcode
from markupsafe import Markup

load_dotenv()
csrf = CSRFProtect()


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

    init_socketio(app)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "2ejfof2jf2ojwfxasf")
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL", "spark-alpha-demo-seed-full-school.db"
    )
    app.config["TESTING"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get(
        "WTF_CSRF_SECRET_KEY", "dev-csrf-secret"
    )
    app.config["SESSION_TIMEOUT_MINUTES"] = int(
        os.environ.get("SESSION_TIMEOUT_MINUTES", 30)
    )

    if config:
        app.config.update(config)

    # Initialize database
    from app.models import init_db

    init_db(app)
    csrf.init_app(app)

    # import blueprints
    from app.routes.auth import auth_bp
    from app.routes.feed import feed_bp
    from app.routes.posts import posts_bp
    from app.routes.profile import profile_bp
    from app.routes.topics import topics_bp
    from app.routes.search import search_bp
    from app.routes.notifications import notifications_bp
    from app.routes.api import api_bp
    from app.routes.settings import settings_bp
    from app.routes.classrooms import classrooms_bp
    from app.routes.reports import reports_bp

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(classrooms_bp)
    app.register_blueprint(reports_bp)
    app.jinja_env.filters["time_ago"] = time_ago

    csrf.exempt(api_bp)

    # ---- Session timeout ----
    @app.before_request
    def check_session_timeout():
        from flask import session, request, redirect, url_for, flash

        if not session.get("user_id"):
            return
        if request.endpoint == "static":
            return

        timeout_minutes = app.config["SESSION_TIMEOUT_MINUTES"]
        last_active = session.get("last_active")

        if last_active:
            last_dt = datetime.fromisoformat(last_active)
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
            if elapsed > timeout_minutes * 60:
                session.clear()
                flash("You were logged out due to inactivity.", "error")
                return redirect(url_for("auth.login"))

        session["last_active"] = datetime.now(timezone.utc).isoformat()

    @app.context_processor
    def inject_unread_count():
        """Inject unread notification count into all templates."""
        from flask import session
        from app.models.notifications import get_unread_count

        if "user_id" in session:
            return {"unread_count": get_unread_count(session["user_id"])}
        return {"unread_count": 0}

    @app.errorhandler(400)
    def bad_request(e):
        return render_template(
            "error.html",
            code=400,
            name="Bad Request",
            message="the server could not understand the request due to invalid syntax.",
        ), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return render_template(
            "error.html",
            code=401,
            name="Unauthorized",
            message="you must be logged in to access this resource.",
        ), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "error.html",
            code=403,
            name="Forbidden",
            message="you don't have permission to access this resource.",
        ), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "error.html",
            code=404,
            name="Not Found",
            message="the requested resource could not be found on this server.",
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template(
            "error.html",
            code=405,
            name="Method Not Allowed",
            message="the server is rate limited due to too many requests from your IP. Please try again later.",
        ), 405

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template(
            "error.html",
            code=429,
            name="Rate Limited",
            message="the server is rate limited due to too many requests from your IP. Please try again later.",
        ), 429

    @app.errorhandler(500)
    def internal_error(e):
        return render_template(
            "error.html",
            code=500,
            name="Internal Server Error",
            message="the server encountered an internal error and was unable to complete your request.",
        ), 500

    @app.template_filter("bbcode")
    def bbcode_filter(text):
        return Markup(render_bbcode(text or ""))

    return app
