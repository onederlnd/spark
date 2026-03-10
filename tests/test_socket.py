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
