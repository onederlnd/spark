# tests/test_socket.py
from app.sockets import socketio
from app.models.notifications import create_notification


def test_socket_connect(app):
    """Test that a socket connection can be established"""
    client = socketio.test_client(app)
    assert client.is_connected()
    client.disconnect()


def test_socket_notification(app):
    """Test that creating a notification emits a socket event"""
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    create_notification(user_id=1, type="follow", message="test", link="/")
    received = client.get_received()
    assert any(e["name"] == "notification" for e in received)
    client.disconnect()


# tests/test_socket.py

from app.sockets import socketio
from app.models.notifications import create_notification
from app.models.user import create_user


def _make_client(app, user_id=None, username="testuser"):
    """Helper: create a socket client with optional session."""
    if user_id:
        with app.test_request_context():
            client = socketio.test_client(
                app,
                headers={"Cookie": f"session=test"},
            )
            # inject session manually
            with client.session_transaction() as sess:
                sess["user_id"] = user_id
                sess["username"] = username
        return client
    return socketio.test_client(app)


# --- connection ---


def test_socket_connect(app):
    client = socketio.test_client(app)
    assert client.is_connected()
    client.disconnect()


def test_socket_disconnect(app):
    client = socketio.test_client(app)
    assert client.is_connected()
    client.disconnect()
    assert not client.is_connected()


def test_socket_unauthenticated_connects_but_no_room(app):
    """Unauthenticated clients connect but don't join a user room."""
    client = socketio.test_client(app)
    assert client.is_connected()
    # no user_id in session means no room joined — just verify no crash
    client.disconnect()


def test_multiple_clients_connect(app):
    c1 = socketio.test_client(app)
    c2 = socketio.test_client(app)
    assert c1.is_connected()
    assert c2.is_connected()
    c1.disconnect()
    c2.disconnect()


def test_client_reconnect(app):
    client = socketio.test_client(app)
    client.disconnect()
    client.connect()
    assert client.is_connected()
    client.disconnect()


# --- room joining ---


def test_authenticated_client_joins_user_room(app):
    """Authenticated socket client should join user_{id} room on connect."""
    with app.test_request_context():
        with app.test_client() as http_client:
            with http_client.session_transaction() as sess:
                sess["user_id"] = 1  # simulate a logged-in user

            client = socketio.test_client(
                app,
                flask_test_client=http_client,  # shares the session
            )

            assert client.is_connected()
            # emit a notification to the room the handler should have joined
            socketio.emit("notification", {"message": "hi"}, room="user_1")
            received = client.get_received()
            assert any(r["name"] == "notification" for r in received)


# --- notifications ---


def test_socket_notification(app):
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    create_notification(user_id=1, type="follow", message="test", link="/")
    received = client.get_received()
    assert any(e["name"] == "notification" for e in received)
    client.disconnect()


def test_notification_payload_fields(app):
    """Notification event should carry expected fields."""
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    create_notification(
        user_id=1, type="follow", message="Alice followed you", link="/profile/alice"
    )
    received = client.get_received()
    notif_events = [e for e in received if e["name"] == "notification"]
    assert len(notif_events) > 0
    payload = notif_events[0]["args"][0]
    assert "message" in payload
    assert "link" in payload
    assert "type" in payload


def test_notification_correct_message(app):
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    create_notification(
        user_id=1, type="follow", message="@bob followed you", link="/profile/bob"
    )
    received = client.get_received()
    notif_events = [e for e in received if e["name"] == "notification"]
    payload = notif_events[0]["args"][0]
    assert payload["message"] == "@bob followed you"


def test_notification_correct_type(app):
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    create_notification(
        user_id=1, type="mention", message="you were mentioned", link="/posts/1"
    )
    received = client.get_received()
    notif_events = [e for e in received if e["name"] == "notification"]
    payload = notif_events[0]["args"][0]
    assert payload["type"] == "mention"


def test_notification_not_received_by_other_user(app):
    """Notification for user_1 should not be received by user_2's client."""
    with app.test_client() as http_client_1:
        with http_client_1.session_transaction() as sess:
            sess["user_id"] = 1
        c1 = socketio.test_client(app, flask_test_client=http_client_1)

    with app.test_client() as http_client_2:
        with http_client_2.session_transaction() as sess:
            sess["user_id"] = 2
        c2 = socketio.test_client(app, flask_test_client=http_client_2)

    c1.get_received()
    c2.get_received()

    create_notification(user_id=1, type="follow", message="for user 1 only", link="/")

    assert any(e["name"] == "notification" for e in c1.get_received())
    assert not any(e["name"] == "notification" for e in c2.get_received())

    c1.disconnect()
    c2.disconnect()


def test_no_notification_received_before_room_join(app):
    """Events emitted before joining a room should not be received."""
    # client connects with no session — handle_connect won't join any room
    client = socketio.test_client(app)
    create_notification(user_id=1, type="follow", message="too early", link="/")
    received = client.get_received()
    assert len([e for e in received if e["name"] == "notification"]) == 0
    client.disconnect()


def test_multiple_notifications_received(app):
    client = socketio.test_client(app)
    sid = list(socketio.server.manager.rooms["/"][None].keys())[0]
    socketio.server.enter_room(sid, "user_1", namespace="/")
    client.get_received()  # clear

    create_notification(user_id=1, type="follow", message="first", link="/")
    create_notification(user_id=1, type="mention", message="second", link="/")

    received = client.get_received()
    notif_events = [e for e in received if e["name"] == "notification"]
    assert len(notif_events) == 2
    client.disconnect()


def test_notification_for_nonexistent_user_no_crash(app):
    """Emitting to a room with no subscribers should not raise."""
    try:
        create_notification(user_id=99999, type="follow", message="ghost", link="/")
    except Exception as e:
        assert False, f"create_notification raised unexpectedly: {e}"
