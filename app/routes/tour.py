# app/routes/tour.py

from flask import Blueprint, session
from app.models import get_db

tour_bp = Blueprint("tour", __name__, url_prefix="/tour")


@tour_bp.route("/complete", methods=["POST"])
def complete():
    user_id = session.get("user_id")
    if user_id:
        db = get_db()
        db.execute("UPDATE users SET tour_seen = 1 WHERE id = ?", (user_id,))
        db.commit()
    return "", 204
