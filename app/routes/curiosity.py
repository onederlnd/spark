# curiosity.py
import os
import json
import anthropic
from flask import Blueprint, request, jsonify
from app.utils.auth import login_required, student_required

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


@curiosity_bp.route("/subjects", methods=["GET"])
@login_required
@student_required
def get_subjects():
    with open(SUBJECT_FILE, "r", encoding="utf-8") as f:
        subjects = json.load(f)
    return jsonify(subjects)


@curiosity_bp.route("/chat", methods=["POST"])
@login_required
@student_required
def chat():
    """Returns Curiosity's reply to question or statement"""
    data = request.get_json()

    message = data.get("message")
    history = data.get("history", [])
    subject = data.get("subject")
    area = data.get("area")
    category = data.get("category")
    topic = data.get("topic")
    description = data.get("description")

    TOPIC_PROMPT = (
        "The student would like to discuss the following information: "
        f"{subject} > {area} > {category} > {topic}: {description}."
    )
    system_prompt = BASE_PROMPT + "\n\n" + TOPIC_PROMPT

    history.append({"role": "user", "content": message})

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=history,
    )

    reply = response.content[0].text

    history.append({"role": "assistant", "content": reply})

    return reply
