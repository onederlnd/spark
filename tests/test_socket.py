# tests/test_socket.py
import pytest
from datetime import datetime, timezone, timedelta
from app.sockets import socketio
from app.models.notifications import create_notification


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_socket_client(app, user_id=None):
    """Create a socket test client, optionally with an authenticated session."""
    http_client = app.test_client()
    if user_id is not None:
        with http_client.session_transaction() as sess:
            sess["user_id"] = user_id
    return socketio.test_client(app, flask_test_client=http_client), http_client


def enter_user_room(sc, user_id):
    """Manually place a socket client into a user room (for tests that skip handle_connect)."""
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, f"user_{user_id}", namespace="/")


# ---------------------------------------------------------------------------
# connection
# ---------------------------------------------------------------------------


def test_socket_connects(app):
    sc, _ = make_socket_client(app)
    assert sc.is_connected()
    sc.disconnect()


def test_socket_disconnects(app):
    sc, _ = make_socket_client(app)
    sc.disconnect()
    assert not sc.is_connected()


def test_socket_reconnects(app):
    sc, _ = make_socket_client(app)
    sc.disconnect()
    sc.connect()
    assert sc.is_connected()
    sc.disconnect()


def test_multiple_clients_connect_independently(app):
    sc1, _ = make_socket_client(app)
    sc2, _ = make_socket_client(app)
    assert sc1.is_connected()
    assert sc2.is_connected()
    sc1.disconnect()
    sc2.disconnect()


def test_unauthenticated_client_connects_without_crash(app):
    sc, _ = make_socket_client(app)
    assert sc.is_connected()
    sc.disconnect()


# ---------------------------------------------------------------------------
# room joining
# ---------------------------------------------------------------------------


def test_authenticated_client_joins_user_room(app):
    sc, _ = make_socket_client(app, user_id=1)
    assert sc.is_connected()
    sc.get_received()  # clear connect noise
    socketio.emit(
        "notification", {"message": "hi", "type": "follow", "link": "/"}, room="user_1"
    )
    received = sc.get_received()
    assert any(r["name"] == "notification" for r in received)
    sc.disconnect()


def test_unauthenticated_client_does_not_join_user_room(app):
    sc, _ = make_socket_client(app)
    sc.get_received()
    create_notification(user_id=1, type="follow", message="no room", link="/")
    received = sc.get_received()
    assert not any(e["name"] == "notification" for e in received)
    sc.disconnect()


def test_reconnected_client_rejoins_room(app):
    sc, _ = make_socket_client(app, user_id=1)
    sc.disconnect()
    sc.connect()
    assert sc.is_connected()
    sc.get_received()
    socketio.emit(
        "notification",
        {"message": "after reconnect", "type": "follow", "link": "/"},
        room="user_1",
    )
    received = sc.get_received()
    assert any(e["name"] == "notification" for e in received)
    sc.disconnect()


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------


def test_notification_received_in_room(app):
    sc, _ = make_socket_client(app)
    enter_user_room(sc, 1)
    sc.get_received()
    create_notification(user_id=1, type="follow", message="test", link="/")
    received = sc.get_received()
    assert any(e["name"] == "notification" for e in received)
    sc.disconnect()


def test_notification_payload_has_required_fields(app):
    sc, _ = make_socket_client(app)
    enter_user_room(sc, 1)
    sc.get_received()
    create_notification(
        user_id=1, type="follow", message="Alice followed you", link="/profile/alice"
    )
    events = [e for e in sc.get_received() if e["name"] == "notification"]
    assert len(events) > 0
    payload = events[0]["args"][0]
    assert "message" in payload
    assert "link" in payload
    assert "type" in payload
    sc.disconnect()


def test_notification_message_content(app):
    sc, _ = make_socket_client(app)
    enter_user_room(sc, 1)
    sc.get_received()
    create_notification(
        user_id=1, type="follow", message="@bob followed you", link="/profile/bob"
    )
    events = [e for e in sc.get_received() if e["name"] == "notification"]
    assert events[0]["args"][0]["message"] == "@bob followed you"
    sc.disconnect()


def test_notification_type_content(app):
    sc, _ = make_socket_client(app)
    enter_user_room(sc, 1)
    sc.get_received()
    create_notification(
        user_id=1, type="mention", message="you were mentioned", link="/posts/1"
    )
    events = [e for e in sc.get_received() if e["name"] == "notification"]
    assert events[0]["args"][0]["type"] == "mention"
    sc.disconnect()


def test_multiple_notifications_all_received(app):
    sc, _ = make_socket_client(app)
    enter_user_room(sc, 1)
    sc.get_received()
    create_notification(user_id=1, type="follow", message="first", link="/")
    create_notification(user_id=1, type="mention", message="second", link="/")
    events = [e for e in sc.get_received() if e["name"] == "notification"]
    assert len(events) == 2
    sc.disconnect()


def test_notification_for_nonexistent_user_does_not_crash(app):
    try:
        create_notification(user_id=99999, type="follow", message="ghost", link="/")
    except Exception as e:
        pytest.fail(f"create_notification raised unexpectedly: {e}")


# ---------------------------------------------------------------------------
# isolation between users
# ---------------------------------------------------------------------------


def test_notification_not_received_by_other_user(app):
    sc1, _ = make_socket_client(app, user_id=1)
    sc2, _ = make_socket_client(app, user_id=2)
    sc1.get_received()
    sc2.get_received()

    create_notification(user_id=1, type="follow", message="for user 1 only", link="/")

    assert any(e["name"] == "notification" for e in sc1.get_received())
    assert not any(e["name"] == "notification" for e in sc2.get_received())
    sc1.disconnect()
    sc2.disconnect()


def test_notification_room_isolated_per_user(app):
    sc1, _ = make_socket_client(app, user_id=1)
    sc2, _ = make_socket_client(app, user_id=2)
    sc1.get_received()
    sc2.get_received()

    create_notification(user_id=2, type="follow", message="only for user 2", link="/")

    assert not any(e["name"] == "notification" for e in sc1.get_received())
    assert any(e["name"] == "notification" for e in sc2.get_received())
    sc1.disconnect()
    sc2.disconnect()


def test_no_notification_before_room_join(app):
    sc, _ = make_socket_client(app)  # no user_id — no room joined
    create_notification(user_id=1, type="follow", message="too early", link="/")
    received = sc.get_received()
    assert len([e for e in received if e["name"] == "notification"]) == 0
    sc.disconnect()


# ---------------------------------------------------------------------------
# session stability
# ---------------------------------------------------------------------------


def test_socket_stays_connected_across_http_requests(app):
    sc, http_client = make_socket_client(app, user_id=1)
    assert sc.is_connected()
    http_client.get("/", follow_redirects=True)
    http_client.get("/", follow_redirects=True)
    assert sc.is_connected()
    sc.disconnect()


def test_socket_disconnects_cleanly_after_logout(app):
    sc, http_client = make_socket_client(app, user_id=1)
    assert sc.is_connected()
    http_client.get("/auth/logout", follow_redirects=True)
    sc.disconnect()
    assert not sc.is_connected()


def test_expired_session_http_redirects_to_login(app):
    http_client = app.test_client()
    timeout = app.config["SESSION_TIMEOUT_MINUTES"]
    expired = datetime.now(timezone.utc) - timedelta(minutes=timeout + 1)
    with http_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["last_active"] = expired.isoformat()
    res = http_client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert "login" in res.headers["Location"]


@pytest.mark.xfail(
    reason="Socket rooms are not cleared on HTTP session expiry — known gap"
)
def test_no_notification_after_session_expiry(app):
    sc, http_client = make_socket_client(app, user_id=1)
    timeout = app.config["SESSION_TIMEOUT_MINUTES"]
    expired = datetime.now(timezone.utc) - timedelta(minutes=timeout + 1)
    with http_client.session_transaction() as sess:
        sess["last_active"] = expired.isoformat()
    http_client.get("/", follow_redirects=True)
    sc.get_received()
    create_notification(user_id=1, type="follow", message="post-expiry", link="/")
    events = [e for e in sc.get_received() if e["name"] == "notification"]
    assert len(events) == 0
    sc.disconnect()
