# app/routes/messaging.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify,
)
from app.utils.auth import login_required
from app.utils.sanitize import sanitize_plain
from app.models.messaging import (
    can_message,
    can_read_conversation,
    create_conversation,
    get_conversation,
    get_conversation_members,
    get_conversations_for_user,
    get_or_create_dm,
    send_message,
    get_messages,
    mark_read,
    hide_message,
    toggle_messaging,
    get_conversations_for_teacher_oversight,
)
from app.models.classroom import (
    get_classroom,
    get_member_role,
    get_classroom_members,
    get_classrooms_for_user,
)
from app.models.user import get_user_by_username


messaging_bp = Blueprint("messaging", __name__, url_prefix="/messages")


# --- helpers
def _current_user_id():
    return session["user_id"]


def _current_role():
    return session.get("role")


@messaging_bp.route("/")
@login_required
def index():
    threads = get_conversations_for_user(_current_user_id())
    active_thread = request.args.get("thread", type=int)
    return render_template(
        "messaging/inbox.html",
        threads=threads,
        active_thread=active_thread,
    )


@messaging_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_conversation():
    classroom_id = request.args.get("classroom_id") or request.form.get("classroom_id")
    preselect_user = request.args.get("user_id")

    if request.method == "POST":
        classroom_id = request.form.get("classroom_id", type=int)
        title = sanitize_plain(request.form.get("title", ""), max_length=100) or None
        body = sanitize_plain(request.form.get("body", ""), max_length=2000)
        recipient_ids = request.form.getlist("recipient_ids", type=int)

        if not classroom_id:
            flash("Classroom is required.", "error")
            return redirect(url_for("messaging.new_conversation"))

        if not recipient_ids:
            flash("Please select at least one recipient.", "error")
            return redirect(
                url_for("messaging.new_conversation", classroom_id=classroom_id)
            )

        if not body:
            flash("Message body cannot be empty.", "error")
            return redirect(
                url_for("messaging.new_conversation", classroom_id=classroom_id)
            )

        ok, reason = can_message(_current_user_id(), recipient_ids, classroom_id)
        if not ok:
            flash(reason, "error")
            return redirect(
                url_for("messaging.new_conversation", classroom_id=classroom_id)
            )

        if len(recipient_ids) == 1:
            conversation_id = get_or_create_dm(
                classroom_id, _current_user_id(), recipient_ids[0]
            )
        else:
            conversation_id = create_conversation(
                classroom_id, _current_user_id(), recipient_ids, title=title
            )

        send_message(conversation_id, _current_user_id(), body)
        return redirect(
            url_for("messaging.conversation", conversation_id=conversation_id)
        )

    # --- GET ---
    classroom = get_classroom(classroom_id) if classroom_id else None
    members = get_classroom_members(classroom_id) if classroom_id else []
    user_classrooms = get_classrooms_for_user(_current_user_id())

    current_role = _current_role()
    current_id = _current_user_id()
    eligible = []

    for m in members:
        if m["id"] == current_id:
            continue
        if current_role == "parent" and m["role"] != "teacher":
            continue
        if current_role == "student" and m["role"] == "parent":
            continue
        if (
            current_role == "student"
            and m["role"] == "student"
            and classroom
            and not classroom["messaging_enabled"]
        ):
            continue
        eligible.append(m)

    return render_template(
        "messaging/new_conversation.html",
        classroom=classroom,
        eligible=eligible,
        preselect_user=preselect_user,
        user_classrooms=user_classrooms,
    )


@messaging_bp.route("/<int:conversation_id>")
@login_required
def conversation(conversation_id):
    if not can_read_conversation(_current_user_id(), conversation_id):
        flash("You don't have access to this conversation.", "error")
        return redirect(url_for("messaging.index"))

    conv = get_conversation(conversation_id)
    members = get_conversation_members(conversation_id)
    messages = get_messages(conversation_id)
    mark_read(conversation_id, _current_user_id())

    is_member = any(m["id"] == _current_user_id() for m in members)

    return render_template(
        "messaging/conversation.html",
        conv=conv,
        members=members,
        messages=messages,
        is_member=is_member,
    )


@messaging_bp.route("/<int:conversation_id>/send", methods=["POST"])
@login_required
def send(conversation_id):
    if not can_read_conversation(_current_user_id(), conversation_id):
        return jsonify({"error", "Forbidden"}), 403

    members = get_conversation_members(conversation_id)
    is_member = any(m["id"] == _current_user_id() for m in members)
    if not is_member:
        flash("You are not a member of this conversation.", "error")
        return redirect(
            url_for("messaging.conversation", conversation_id=conversation_id)
        )

    body = sanitize_plain(request.form.get("body", ""), max_length=2000)
    if not body:
        flash("Message cannot be empty.", "error")
        return redirect(
            url_for("messaging.conversation", conversation_id=conversation_id)
        )
    send_message(conversation_id, _current_user_id(), body)
    mark_read(conversation_id, _current_user_id())
    return redirect(url_for("messaging.conversation", conversation_id=conversation_id))


@messaging_bp.route("/<int:conversation_id>/messages")
@login_required
def load_messages(conversation_id):
    if not can_read_conversation(_current_user_id(), conversation_id):
        return jsonify({"error": "Forbidden"}), 403

    before_id = request.args.get("before_id", type=int)
    after_id = request.args.get("after_id", type=int)  # <── new param for polling
    messages = get_messages(
        conversation_id, limit=50, before_id=before_id, after_id=after_id
    )

    return jsonify(
        [
            {
                "id": m["id"],
                "body": m["body"],
                "sender_id": m["sender_id"],
                "username": m["username"],
                "display_name": m["display_name"],
                "avatar_emoji": m["avatar_emoji"],
                "created_at": m["created_at"],
            }
            for m in messages
        ]
    )


@messaging_bp.route("/messages/<int:message_id>/hide", methods=["POST"])
@login_required
def hide(message_id):
    if _current_role() != "teacher":
        return "Forbidden", 403

    db_msg = None
    from app.models import get_db

    db = get_db()
    db_msg = db.execute(
        "SELECT m.*, c.classroom_id FROM messages m JOIN conversation c ON m.conversation_id = c.id WHERE m.id = ?",
        (message_id,),
    ).fetchone()

    if not db_msg:
        return "Not found", 404

    if not get_member_role(db_msg["classroom_id"], _current_user_id()):
        return "Forbidden", 403

    hide_message(message_id)
    flash("Message hidden.", "success")
    return redirect(
        request.referrer
        or url_for("messaging.conversation", conversation_id=db_msg["conversation_id"])
    )


@messaging_bp.route("/classroom/<int:classroom_id>/toggle-messaging", methods=["POST"])
@login_required
def toggle_student_messaging(classroom_id):
    if _current_role() != "teacher":
        return "Forbidden", 403

    role = get_member_role(classroom_id, _current_user_id())
    if role != "teacher":
        return "Forbidden", 403

    enabled = request.form.get("enabled") == "1"
    toggle_messaging(classroom_id, enabled)
    state = "enabled" if enabled else "disabled"
    flash(f"Student messaging {state}.", "success")
    return redirect(
        request.referrer
        or url_for("classrooms.classroom_home", classroom_id=classroom_id)
    )


@messaging_bp.route("/classroom/<int:classroom_id>/oversight")
@login_required
def oversight(classroom_id):
    if _current_role() != "teacher":
        return "Forbidden", 403

    role = get_member_role(classroom_id, _current_user_id())
    if role != "teacher":
        return "Forbidden", 403

    conversations = get_conversations_for_teacher_oversight(classroom_id)
    classroom = get_classroom(classroom_id)
    return render_template(
        "messaging/oversight.html",
        conversations=conversations,
        classroom=classroom,
    )


@messaging_bp.route("/dm/<username>")
@login_required
def dm(username):
    classroom_id = request.args.get("classroom_id", type=int)
    if not classroom_id:
        flash("Please specify a classroom.", "error")
        return redirect(url_for("messaging.index"))

    target = get_user_by_username(username)
    if not target:
        return "User not found", 404

    ok, reason = can_message(_current_user_id(), [target["id"]], classroom_id)
    if not ok:
        flash(reason, "error")
        return redirect(url_for("messaging.index"))

    conversation_id = get_or_create_dm(classroom_id, _current_user_id(), target["id"])
    return redirect(url_for("messaging.conversation", conversation_id=conversation_id))


# ─── ADD THESE ROUTES TO app/routes/messaging.py ────────────────────────────
# The floating messenger JS calls these two endpoints.
# Paste them into messaging_bp alongside the existing routes.


@messaging_bp.route("/api/conversations")
@login_required
def api_conversations():
    """
    JSON list of conversations for the floating messenger inbox.
    Returns the same data as get_conversations_for_user but as JSON.
    """
    rows = get_conversations_for_user(_current_user_id())
    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "title": r["title"],
                "classroom_id": r["classroom_id"],
                "classroom_name": r["classroom_name"],
                "last_message_body": r["last_message_body"],
                "last_message_at": r["last_message_at"],
                "unread_count": r["unread_count"],
            }
        )
    return jsonify(result)


@messaging_bp.route("/<int:conversation_id>/mark-read", methods=["POST"])
@login_required
def mark_read_api(conversation_id):
    """
    AJAX mark-read endpoint for the floating messenger.
    """
    if not can_read_conversation(_current_user_id(), conversation_id):
        return jsonify({"error": "Forbidden"}), 403
    mark_read(conversation_id, _current_user_id())
    return jsonify({"ok": True})
