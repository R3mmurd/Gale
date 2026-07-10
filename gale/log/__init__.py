"""
gale.log: logging for gale games, configured to print to the terminal
and write to a plain-text file by default, and extensible to send
records anywhere else (Graylog, Sentry, a Discord channel, and
friends) by attaching another logging.Handler — each handler is
itself the "where do records go" strategy, so a game only ever
composes handlers, never writes a new one unless it needs a
destination gale/the standard library doesn't already ship.

See docs/examples/log.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .config import add_handler, configure, get_logger, remove_handler
from .discord_webhook_handler import DiscordWebhookHandler
from .graylog_handler import GraylogHandler
from .level import LogLevel
from .sentry_handler import SentryHandler

__all__ = [
    "DiscordWebhookHandler",
    "GraylogHandler",
    "LogLevel",
    "SentryHandler",
    "add_handler",
    "configure",
    "get_logger",
    "remove_handler",
]
