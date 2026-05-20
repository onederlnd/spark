from flask import session, redirect, url_for, abort, flash
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


def teacher_required(f):
    """Restricts route to users with role='teacher'. Must be used after @login_required"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "teacher":
            abort(403)
        return f(*args, **kwargs)

    return decorated


def student_required(f):
    """Restrictrs routes to SparK students with role = 'student'"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "student":
            abort(403)

        return f(*args, **kwargs)

    return decorated


def teacher_or_admin_required(f):
    """
    Restricts route to users with role='teacher' or role='org_admin'.
    Uses for shared routes such as COPPA approval
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user["role"] not in ("teacher", "org_admin"):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def org_admin_required(f):
    """Restricts routes to organizational admins with role='org_admin'"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "org_admin":
            abort(403)
        return f(*args, **kwargs)

    return decorated


def staff_required(f):
    """Restricts routes to SparK staff with role = 'spark_staff'"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "spark_staff":
            abort(403)
        return f(*args, **kwargs)

    return decorated


def subscription_required(f):
    """
    Restricts a route to teachers with an active subscription
    either through personal or org-level -- unless FREEMIUM_ENABLED
    is True in app config.

    Must be used AFTER @login_required and @teacher_required

    On failure: redirects to /billing/plan with a flash message.

    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        from app.models.billing import teacher_has_access

        user = current_user()
        if not user:
            return redirect(url_for("auth.login"))

        freemium_enabled = current_app.config.get("FREEMIUM_ENABLED", True)

        if not teacher_has_access(user, freemium_enabled):
            flash("This feature requires an active SparK subscription", "error")
            return redirect(url_for("billing.plan"))

        return f(*args, **kwargs)

    return decorated
