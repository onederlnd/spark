import logging
import sys

"""
add functionality for logging

from app.utils.logger import get_logger
log = get_logger(__name__)

log.info("Resource attached: resource_id=%s assignment_id=%s", resource_id, assignment_id)
log.warning("Failed login attempt: user_id=%s", user_id)
log.error("DB error during submission upload: %s", e)

"""


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def init_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        root.addHandler(handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)
