from flask import session
from app.models.user import get_user_by_id


def current_user():
    user_id = session.get("user_id")
    if user_id:
        return get_user_by_id(user_id)
    return None
