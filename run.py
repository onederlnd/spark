# run.py

from app import create_app
from app.sockets import socketio

app = create_app()

if __name__ == "__main__":
    print("Config loaded:")
    print(f"    DATABASE_URL = {app.config.get('DATABASE_URL')}")
    print(f"    SECRET_KEY set = {bool(app.config.get('SECRET_KEY'))}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
