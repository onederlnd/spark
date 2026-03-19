from flask import session, redirect, url_for
from functools import wraps
from app.models.user import get_user_by_id
from app.models.classroom import get_member_role


def current_user():
    user_id = session.get("user_id")
    if user_id:
        return get_user_by_id(user_id)
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def is_teacher_global():
    user = current_user()
    return user and user["role"] == "teacher"


def is_teacher_in_classroom(classroom_id):
    user_id = session.get("user_id")
    if not user_id:
        return False

    role = get_member_role(classroom_id, user_id)
    return role == "teacher"
