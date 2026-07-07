"""
gale.log: logging for gale games, configured to print to the terminal
and write to a plain-text file by default, and extensible to send
records anywhere else (Graylog and friends) by attaching another
logging.Handler — each handler is itself the "where do records go"
strategy, so a game only ever composes handlers, never writes a new
one unless it needs a destination gale/the standard library doesn't
already ship.

See docs/examples/log.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .config import add_handler, configure, get_logger, remove_handler
from .graylog_handler import GraylogHandler
from .level import LogLevel

__all__ = [
    "GraylogHandler",
    "LogLevel",
    "add_handler",
    "configure",
    "get_logger",
    "remove_handler",
]
