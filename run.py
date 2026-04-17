# run.py

from app import create_app
from app.sockets import socketio
from app.utils.logger import init_logging, get_logger
from dotenv import load_dotenv


init_logging(debug=False)
log = get_logger(__name__)
load_dotenv()
app = create_app()

if __name__ == "__main__":
    log.info("Config loaded:")
    log.info(f"    DATABASE_URL = {app.config.get('DATABASE_URL')}")
    log.info(f"    SECRET_KEY set = {bool(app.config.get('SECRET_KEY'))}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
