# app/routes/feedback.py

from flask import Blueprint, request, session, jsonify
from app.models.feedback import submit_feedback
from app.utils.auth import login_required, teacher_required
from app.utils.rate_limit import rate_limit

feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback_bp.route("/submit", methods=["POST"])
@login_required
@teacher_required
@rate_limit(max_requests=10, window_seconds=60)
def submit():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_ratings = [
        "classroom_experience",
        "student_engagement",
        "ease_of_use",
        "assignment_workflow",
        "safety_moderation",
    ]

    ratings = {}
    for field in required_ratings:
        val = data.get(field)
        if val is None:
            return jsonify({"error": f"Missing field: {field}"}), 400
        try:
            val = int(val)
            if val < 1 or val > 5:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid value for {field} - must be 1-5"}), 400

        ratings[field] = val

    submit_feedback(
        user_id=session["user_id"],
        page_url=data.get("page_url", ""),
        page_context=data.get("page_context", ""),
        classroom_experience=ratings["classroom_experience"],
        student_engagement=ratings["student_engagement"],
        ease_of_use=ratings["ease_of_use"],
        assignment_workflow=ratings["assignment_workflow"],
        safety_moderation=ratings["safety_moderation"],
        open_suggestions=data.get("open_suggestions", "").strip(),
    )
    return jsonify({"ok": True}), 200
