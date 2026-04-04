# app/utils/password_reset.py

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

_SALT = "spark-password-reset"
_MAX_AGE = 3600  # 1 hour


def generate_reset_token(user_id):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(user_id, salt=_SALT)


def verify_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt=_SALT, max_age=_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return None
