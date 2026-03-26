import time
from flask import Blueprint, jsonify
from app.models import get_db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    start = time.monotonic()
    db_ok = True
    db_error = None

    try:
        db = get_db()
        db.execute("SELECT 1").fetchone()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    elapsed_ms = round((time.monotonic() - start) * 1000, 2)
    status = "ok" if db_ok else "degraded"
    payload = {
        "status": status,
        "db": "ok" if db_ok else f"error: {db_error}",
        "response_ms": elapsed_ms,
    }
    return jsonify(payload), 200 if db_ok else 503
