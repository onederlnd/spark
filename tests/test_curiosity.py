# tests/test_curiosity.py
import json
from unittest.mock import MagicMock
import pytest
from app.utils.curiosity_helpers import (
    normalize_question,
    build_topic_key,
    hash_question,
    check_response_quality,
    build_enriched_prompt,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _parse_sse(response_data):
    """Parse SSE response and reconstruct the reply and conversation_id."""
    result = {}
    chunks = []
    for line in response_data.decode().splitlines():
        if line.startswith("data: "):
            payload = json.loads(line[6:])
            if "conversation_id" in payload:
                result["conversation_id"] = payload["conversation_id"]
            if "chunk" in payload:
                chunks.append(payload["chunk"].replace("\\n", "\n"))
    result["reply"] = "".join(chunks)
    return result


def _make_student(app, username="curiosity_student", password="pass123"):
    """Register and log in a student, return their client and user_id."""
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": password,
            "bio": "",
            "dob": "2005-06-01",
            "role": "student",
        },
    )
    client.post("/auth/login", data={"username": username, "password": password})
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", (username,))
            .fetchone()
        )
    return client, user["id"]


def _make_conversation(
    app,
    user_id,
    *,
    subject="Math",
    area="Algebra",
    category="Equations",
    topic="Linear",
    description="Solve for x",
):
    """Insert a conversation directly into the DB and return its id."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        conversation_id = db.execute(
            """
            INSERT INTO curiosity_conversations
                (user_id, subject, area, category, topic, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, subject, area, category, topic, description),
        ).lastrowid
        db.commit()
    return conversation_id


def _make_message(app, conversation_id, role="user", content="Hello"):
    """Insert a message directly into the DB."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute(
            "INSERT INTO curiosity_messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )
        db.commit()


def _chat_payload(**kwargs):
    """Return a minimal valid chat POST payload."""
    defaults = {
        "message": "What is a variable?",
        "subject": "Math",
        "area": "Algebra",
        "category": "Equations",
        "topic": "Linear",
        "description": "Solve for x",
    }
    defaults.update(kwargs)
    return defaults


def _configure_mock_reply(app, text="Great question! Let's think about it."):
    import app.routes.curiosity as curiosity_module

    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = [text]

    curiosity_module.client.messages.stream = MagicMock(return_value=mock_stream)
