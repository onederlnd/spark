# app/routes/curiosity.py

import os
import json
import anthropic
from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    render_template,
    Response,
    stream_with_context,
)
from app.utils.auth import student_required, teacher_required
from app.utils.curiosity_helpers import (
    normalize_question,
    build_topic_key,
    hash_question,
    build_enriched_prompt,
    check_response_quality,
)
from app.models.curiosity_cache import (
    get_cached_response,
    get_cache_entries_by_topic,
    save_cached_response,
    get_feedback_summary,
    invalidate_cache_entry,
)
from app.models.curiosity_topic_prompts import get_topic_prompt
from app.models.curiosity import (
    get_or_create_conversation,
    save_message,
    get_messages,
    update_conversation_topic,
    get_conversation as fetch_conversation,
    get_conversations as fetch_conversations,
    delete_conversation as remove_conversation,
)

curiosity_bp = Blueprint("curiosity", __name__, url_prefix="/curiosity")

BASE_PROMPT = (
    "You are Curiosity, a friendly and enthusiastic study buddy for students of all ages. "
    "You sit beside the student like a trusted friend who genuinely loves learning. "
    "You are warm, encouraging, and excited about ideas — but never condescending. "
    "If a student asks about something outside these topics, kindly redirect them back. "
    "You never do the work for the student — instead you ask guiding questions, "
    "celebrate their thinking, and help them discover answers themselves. "
    "Keep your language age-appropriate and always encouraging. "
    "If a student seems upset or distressed, gently encourage them to talk to a trusted adult."
)

SUBJECT_FILE = os.path.abspath("app/data/curiosity/subjects.json")

client = anthropic.Anthropic()


@curiosity_bp.route("/", methods=["GET"])
@student_required
def index():
    return render_template("curiosity/chat.html")


@curiosity_bp.route("/subjects", methods=["GET"])
@student_required
def get_subjects():
    with open(SUBJECT_FILE, "r", encoding="utf-8") as f:
        subjects = json.load(f)
    return jsonify(subjects)


@curiosity_bp.route("/chat", methods=["POST"])
@student_required
def chat():
    data = request.get_json()

    message = data.get("message")
    subject = data.get("subject")
    area = data.get("area")
    category = data.get("category")
    topic = data.get("topic")
    description = data.get("description")

    user_id = session["user_id"]

    normalized = normalize_question(message)
    topic_key = build_topic_key(subject, area, category, topic)
    question_hash = hash_question(normalized)

    conversation = get_or_create_conversation(
        user_id, subject, area, category, topic, description
    )
    conv_id = conversation["id"]

    cached = get_cached_response(topic_key, question_hash)
    if cached:

        def generate_cached():
            yield f'data: {{"conversation_id": {conv_id}}}\n\n'
            chunk = cached["response_text"].replace("\\", "\\\\").replace("\n", "\\n")
            yield f'data: {{"chunk": "{chunk}"}}\n\n'
            yield 'data: {"done": true}\n\n'

        return Response(
            stream_with_context(generate_cached()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    topic_prompt_row = get_topic_prompt(topic_key)
    topic_prompt_text = topic_prompt_row["prompt_text"] if topic_prompt_row else None
    system_prompt = build_enriched_prompt(
        BASE_PROMPT,
        topic_prompt_text,
        None,
        subject,
        area,
        category,
        topic,
        description,
    )

    messages = get_messages(conversation["id"])
    history = [{"role": m["role"], "content": m["content"]} for m in messages]
    history.append({"role": "user", "content": message})

    def generate():
        full_reply = []
        try:
            with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=system_prompt,
                messages=history,
            ) as stream:
                yield f'data: {{"conversation_id": {conv_id}}}\n\n'

                for text in stream.text_stream:
                    full_reply.append(text)
                    chunk = text.replace("\\", "\\\\").replace("\n", "\\n")
                    yield f'data: {{"chunk": "{chunk}"}}\n\n'

            complete_reply = "".join(full_reply)
            save_message(conv_id, "user", message)
            save_message(conv_id, "assistant", complete_reply)

            quality = check_response_quality(complete_reply)
            if not quality["passed"]:
                pass  # TODO: log flags, optionally hold for teacher review

            save_cached_response(topic_key, question_hash, message, complete_reply)

            yield 'data: {"done": true}\n\n'

        except Exception:
            yield 'data: {{"error": "Something went wrong"}}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@curiosity_bp.route("/conversations", methods=["GET"])
@student_required
def get_conversations():
    """Returns all conversations for the current user, ordered by most recent."""
    user_id = session["user_id"]

    return jsonify([dict(c) for c in fetch_conversations(user_id)])


@curiosity_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
@student_required
def get_conversation(conversation_id):
    """Returns a single conversation with its full message history."""
    conversation = fetch_conversation(conversation_id)

    if conversation is None:
        return "Not Found", 404

    if conversation["user_id"] != session["user_id"]:
        return "Forbidden", 403

    messages = get_messages(conversation_id)

    return jsonify(
        {"conversation": dict(conversation), "messages": [dict(m) for m in messages]}
    )


@curiosity_bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@student_required
def get_conversation_messages(conversation_id):
    """Returns all messages for a conversation in chronological order."""
    conversation = fetch_conversation(conversation_id)

    if conversation is None:
        return "Not Found", 404

    if conversation["user_id"] != session["user_id"]:
        return "Forbidden", 403
    messages = get_messages(conversation_id)

    return jsonify({"messages": [dict(m) for m in messages]})


@curiosity_bp.route("/conversations/<int:conversation_id>/topic", methods=["PATCH"])
@student_required
def update_topic(conversation_id):
    """Updates the subject, area, category, and topic for an existing conversation."""
    conversation = fetch_conversation(conversation_id)

    if conversation is None:
        return "Not Found", 404

    if conversation["user_id"] != session["user_id"]:
        return "Forbidden", 403

    data = request.get_json()
    subject = data.get("subject")
    area = data.get("area")
    category = data.get("category")
    topic = data.get("topic")
    description = data.get("description")

    updated = update_conversation_topic(
        conversation_id, subject, area, category, topic, description
    )

    return jsonify(dict(updated))


@curiosity_bp.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@student_required
def delete_conversation(conversation_id):
    """Deletes a conversation and all its messages."""
    conversation = fetch_conversation(conversation_id)

    if conversation is None:
        return "Not Found", 404

    if conversation["user_id"] != session["user_id"]:
        return "Forbidden", 403

    remove_conversation(conversation_id)

    return "No Content", 204


@curiosity_bp.route("/review/<topic_key>", methods=["GET"])
@teacher_required
def review_topic(topic_key):
    raw_entries = get_cache_entries_by_topic(topic_key)
    entries = []
    for entry in raw_entries:
        e = dict(entry)
        e["feedback"] = get_feedback_summary(entry["id"])
        entries.append(e)

    return render_template(
        "curiosity/review.html", topic_key=topic_key, entries=entries
    )


@curiosity_bp.route("/review/<topic_key>/invalidate/<int:cache_id>", methods=["POST"])
@teacher_required
def invalidate_entry(topic_key, cache_id):
    invalidate_cache_entry(cache_id)
    flash(
        "Cached response removed. The next matching question will go live to Claude.",
        "success",
    )
    return redirect(url_for("curiosity.review_topic", topic_key=topic_key))


@curiosity_bp.route("/starters/<topic_key>", methods=["GET"])
@teacher_required
def list_starters(topic_key):
    from app.models.social_suggestions import get_discussion_starters

    starters = get_discussion_starters(topic_key)
    return render_template(
        "curiosity/starters.html",
        topic_key=topic_key,
        starters=starters,
    )


@curiosity_bp.route("/starters/<topic_key>/new", methods=["POST"])
@teacher_required
def create_starter(topic_key):
    from app.models.social_suggestions import save_discussion_starter

    prompt_text = request.form.get("prompt_text", "").strip()
    classroom_id = request.form.get("classroom_id") or None
    if not prompt_text:
        flash("Prompt text is required.", "error")
        return redirect(url_for("curiosity.list_starters", topic_key=topic_key))
    save_discussion_starter(
        topic_key=topic_key,
        prompt_text=prompt_text,
        created_by=session["user_id"],
        classroom_id=int(classroom_id) if classroom_id else None,
    )
    flash("Discussion starter added.", "success")
    return redirect(url_for("curiosity.list_starters", topic_key=topic_key))


@curiosity_bp.route("/starters/<topic_key>/delete/<int:starter_id>", methods=["POST"])
@teacher_required
def delete_starter(topic_key, starter_id):
    from app.models import get_db

    db = get_db()
    starter = db.execute(
        "SELECT * FROM curiosity_social_starters WHERE id = ?", (starter_id,)
    ).fetchone()
    if not starter:
        return "Not Found", 404
    if starter["created_by"] != session["user_id"]:
        return "Forbidden", 403
    db.execute("DELETE FROM curiosity_social_starters WHERE id = ?", (starter_id,))
    db.commit()
    flash("Starter removed.", "success")
    return redirect(url_for("curiosity.list_starters", topic_key=topic_key))
