# app/sockets.py

from flask_socketio import SocketIO, join_room, leave_room
from flask import session

socketio = SocketIO()


"""Initializeation SOcketIO with the Flask app."""


def init_socketio(app):
    socketio.init_app(
        app, async_mode="threading", cors_allowed_origins="*", manage_session=False
    )


@socketio.on("connect")
def handle_connect():
    """Join a personal room when user connects"""
    user_id = session.get("user_id")
    if user_id:
        join_room(f"user_{user_id}")


@socketio.on("disconnect")
def handle_disconnect():
    """Leave personal room on disconnect"""
    if "user_id" in session:
        leave_room(f"user_{session['user_id']}")
