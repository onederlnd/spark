import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


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

    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.feed import feed_bp
    from app.routes.posts import posts_bp
    from app.routes.profile import profile_bp
    from app.routes.topics import topics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(topics_bp)

    return app
