# tests/test_curiosity.py
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------


def _make_student(app, *, username="curiousstudent", password="pass123"):
    """Register and log in a student, return the test client."""
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": password,
            "bio": "",
            "role": "student",
            "dob": "2010-04-15",
        },
    )
    client.post("/auth/login", data={"username": username, "password": password})
    return client


def _make_teacher(app, *, username="curiosityteacher", password="pass123"):
    """Register and log in a teacher, return the test client."""
    client = app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": password,
            "bio": "",
            "role": "teacher",
            "dob": "1985-06-20",
        },
    )
    client.post("/auth/login", data={"username": username, "password": password})
    return client


def _chat_payload(
    *,
    message="What is photosynthesis?",
    history=None,
    subject="Science",
    area="Biology",
    category="Plants",
    topic="Photosynthesis",
    description="How plants make food from sunlight.",
):
    """Build a minimal valid JSON payload for the /curiosity/chat endpoint."""
    return {
        "message": message,
        "history": history if history is not None else [],
        "subject": subject,
        "area": area,
        "category": category,
        "topic": topic,
        "description": description,
    }


def _fake_anthropic_response(text="Great question! Let me guide you."):
    """Return a mock that mimics anthropic.Anthropic().messages.create(...)."""
    mock_content = MagicMock()
    mock_content.text = text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


# ---------------------------------------------------------------------------
# GET /curiosity/subjects
# ---------------------------------------------------------------------------


def test_get_subjects_requires_login(client):
    """Unauthenticated GET to /curiosity/subjects redirects to login."""
    response = client.get("/curiosity/subjects")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_get_subjects_returns_200_for_student(app):
    """Authenticated student can retrieve subjects."""
    student = _make_student(app)
    response = student.get("/curiosity/subjects")
    assert response.status_code == 200


def test_get_subjects_returns_json_for_student(app):
    """Subjects response is valid JSON for an authenticated student."""
    student = _make_student(app)
    response = student.get("/curiosity/subjects")
    assert response.content_type.startswith("application/json")
    assert response.get_json() is not None


def test_get_subjects_returns_nonempty_list_for_student(app):
    """Subjects list has at least one entry for an authenticated student."""
    student = _make_student(app)
    response = student.get("/curiosity/subjects")
    data = response.get_json()
    assert isinstance(data, (list, dict))
    assert len(data) > 0


def test_get_subjects_forbidden_for_teacher(app):
    """Teachers cannot access the subjects endpoint."""
    teacher = _make_teacher(app)
    response = teacher.get("/curiosity/subjects")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /curiosity/chat — authentication & authorisation
# ---------------------------------------------------------------------------


def test_chat_unauthenticated_user_is_rejected(client):
    """Unauthenticated POST to /curiosity/chat is redirected or forbidden."""
    response = client.post(
        "/curiosity/chat",
        json=_chat_payload(),
    )
    assert response.status_code in (302, 401, 403)


def test_chat_teacher_is_forbidden(app):
    """Teachers are not students and must not access the chat endpoint."""
    teacher = _make_teacher(app)
    response = teacher.post("/curiosity/chat", json=_chat_payload())
    assert response.status_code == 403


def test_chat_student_is_allowed(app):
    """Authenticated students receive a 200 from the chat endpoint."""
    student = _make_student(app)
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        response = student.post("/curiosity/chat", json=_chat_payload())
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /curiosity/chat — request validation
# ---------------------------------------------------------------------------


def test_chat_missing_message_field_returns_error(app):
    """Omitting the 'message' field results in a 4xx response."""
    pytest.skip("validation not yet implemented in chat()")


def test_chat_empty_message_returns_error(app):
    """Sending an empty string for 'message' returns a 4xx."""
    pytest.skip("validation not yet implemented in chat()")


def test_chat_missing_subject_context_returns_error(app):
    """Omitting subject/topic context fields returns a 4xx."""
    pytest.skip("validation not yet implemented in chat()")


def test_chat_non_json_body_returns_error(app):
    """Posting form-encoded data instead of JSON returns a 4xx."""
    student = _make_student(app, username="formbody_student")
    response = student.post(
        "/curiosity/chat",
        data={"message": "hello"},
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code in (400, 415, 422)


# ---------------------------------------------------------------------------
# POST /curiosity/chat — response shape
# ---------------------------------------------------------------------------


def test_chat_response_contains_reply_text(app):
    """Successful chat returns the AI reply text in the response body."""
    student = _make_student(app, username="replystudent")
    expected_reply = "That's a great question — what do you think happens to light?"
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response(
            expected_reply
        )
        response = student.post("/curiosity/chat", json=_chat_payload())
    assert (
        expected_reply.encode() in response.data
        or expected_reply in response.get_data(as_text=True)
    )


def test_chat_response_is_not_empty(app):
    """The reply from the chat endpoint is not an empty string."""
    student = _make_student(app, username="nonempty_student")
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response(
            "Think about what the sun does for plants!"
        )
        response = student.post("/curiosity/chat", json=_chat_payload())
    assert len(response.get_data(as_text=True).strip()) > 0


# ---------------------------------------------------------------------------
# POST /curiosity/chat — Anthropic API integration
# ---------------------------------------------------------------------------


def test_chat_passes_user_message_to_anthropic(app):
    """The student's message is forwarded to the Anthropic API."""
    student = _make_student(app, username="msgcheck_student")
    user_message = "Can you help me understand gravity?"
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        student.post("/curiosity/chat", json=_chat_payload(message=user_message))
        call_kwargs = mock_client.messages.create.call_args
    messages_sent = call_kwargs.kwargs.get("messages", [])
    sent_texts = [
        m["content"] for m in messages_sent if isinstance(m.get("content"), str)
    ]
    assert any(user_message in t for t in sent_texts)


def test_chat_includes_base_prompt_in_system(app):
    """The system prompt sent to Anthropic includes the Curiosity persona."""
    student = _make_student(app, username="systemprompt_student")
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        student.post("/curiosity/chat", json=_chat_payload())
        call_kwargs = mock_client.messages.create.call_args
    system = call_kwargs.kwargs.get("system", "")
    assert "Curiosity" in system


def test_chat_includes_topic_context_in_system_prompt(app):
    """The topic and description are embedded in the system prompt."""
    student = _make_student(app, username="topicprompt_student")
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        student.post(
            "/curiosity/chat",
            json=_chat_payload(
                topic="Photosynthesis",
                description="How plants make food from sunlight.",
            ),
        )
        call_kwargs = mock_client.messages.create.call_args
    system = call_kwargs.kwargs.get("system", "")
    assert "Photosynthesis" in system


def test_chat_passes_conversation_history_to_anthropic(app):
    """Prior conversation history is forwarded to the Anthropic API."""
    student = _make_student(app, username="history_student")
    prior_history = [
        {"role": "user", "content": "What is a cell?"},
        {
            "role": "assistant",
            "content": "Great question! What do you think it could be?",
        },
    ]
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        student.post(
            "/curiosity/chat",
            json=_chat_payload(history=prior_history, message="Is a cell alive?"),
        )
        call_kwargs = mock_client.messages.create.call_args
    messages_sent = call_kwargs.kwargs.get("messages", [])
    contents = [m["content"] for m in messages_sent]
    assert "What is a cell?" in contents


def test_chat_uses_correct_anthropic_model(app):
    """The Anthropic call targets the claude-sonnet-4-5 model."""
    student = _make_student(app, username="model_student")
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response()
        student.post("/curiosity/chat", json=_chat_payload())
        call_kwargs = mock_client.messages.create.call_args
    model = call_kwargs.kwargs.get("model", "")
    assert model == "claude-sonnet-4-5"


def test_chat_anthropic_api_error_propagates(app):
    """If Anthropic raises an exception it propagates (PROPAGATE_EXCEPTIONS=True)."""
    student = _make_student(app, username="apierror_student")
    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.side_effect = Exception("API unavailable")
        with pytest.raises(Exception, match="API unavailable"):
            student.post("/curiosity/chat", json=_chat_payload())


# ---------------------------------------------------------------------------
# POST /curiosity/chat — multi-turn behaviour
# ---------------------------------------------------------------------------


def test_chat_second_turn_appends_new_message_to_history(app):
    """Sending a second message with the updated history includes both turns."""
    student = _make_student(app, username="multiturn_student")
    first_reply = "Think about where plants get their energy!"

    with patch("app.routes.curiosity.client") as mock_client:
        mock_client.messages.create.return_value = _fake_anthropic_response(first_reply)
        # first turn
        student.post(
            "/curiosity/chat", json=_chat_payload(message="What is photosynthesis?")
        )

        # simulate the client including first exchange in history
        history_with_first_turn = [
            {"role": "user", "content": "What is photosynthesis?"},
            {"role": "assistant", "content": first_reply},
        ]
        mock_client.messages.create.return_value = _fake_anthropic_response(
            "Exactly! The sun is a clue."
        )
        student.post(
            "/curiosity/chat",
            json=_chat_payload(
                message="Is it the sun?",
                history=history_with_first_turn,
            ),
        )
        second_call_kwargs = mock_client.messages.create.call_args
    messages_sent = second_call_kwargs.kwargs.get("messages", [])
    contents = [m["content"] for m in messages_sent]
    assert "What is photosynthesis?" in contents
    assert first_reply in contents
    assert "Is it the sun?" in contents
