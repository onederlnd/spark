# scripts/test_socket.py
# Manual test client for WebSocket connections
# Usage: python scripts/test_socket.py
import requests
import socketio
from bs4 import BeautifulSoup

# create a session to maintain cookies
session = requests.Session()
login_page = session.get("http://localhost:5000/auth/login")
soup = BeautifulSoup(login_page.text, "html.parser")
csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

# login with CSRF token
session.post(
    "http://localhost:5000/auth/login",
    data={"username": "rchristenhusz", "password": "pass123", "csrf_token": csrf_token},
)

sio = socketio.Client()
cookies = "; ".join([f"{k}={v}" for k, v in session.cookies.items()])


@sio.event
def connect():
    print("== connected to devstack socket")


@sio.event
def disconnect():
    print("== disconnected")


@sio.on("notification")
def on_notification(data):
    print("== notification received:")
    print(f"    type:    {data.get('type')}")
    print(f"    message: {data.get('message')}")
    print(f"    link:    {data.get('link')}")


if __name__ == "__main__":
    print("connecting to http://localhost:5000 ...")
    try:
        sio.connect(
            "http://localhost:5000", transports=["polling"], headers={"Cookie": cookies}
        )
        print("listening for notifications... (ctrl+c to stop)")
        sio.wait()
    except KeyboardInterrupt:
        print("\nstopping.")
        sio.disconnect()
    except Exception as e:
        print(f"error: {e}")
        print("make sure devstack is running: python run.py")
