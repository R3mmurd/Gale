"""
This file contains the implementation of the class GraylogHandler: a
logging.Handler that sends each log record to a Graylog server as a
GELF (Graylog Extended Log Format) datagram over UDP.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import logging
import socket
from typing import Optional

# Attributes every LogRecord already has, per the standard library's
# own documentation — anything else set on a record (typically via
# logging.info(msg, extra={...})) is treated as a custom GELF field.
_RESERVED_RECORD_ATTRIBUTES = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)

# GELF's "level" field is a syslog severity, not a Python logging level.
_SYSLOG_SEVERITY = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


class GraylogHandler(logging.Handler):
    """
    Sends every log record to a Graylog server as a GELF
    (Graylog Extended Log Format) datagram over UDP — one strategy
    among possibly several; register it with gale.log.add_handler to
    start sending records there in addition to (or, with
    gale.log.configure(console=False, log_file=None), instead of) the
    console/file defaults. Any other logging.Handler works exactly
    the same way, GraylogHandler is just the one gale ships since the
    standard library doesn't have one.

    Usage example:

        from gale.log import add_handler
        from gale.log.graylog_handler import GraylogHandler

        add_handler(GraylogHandler("graylog.example.com", 12201))
    """

    def __init__(self, host: str, port: int, source: Optional[str] = None) -> None:
        """
        :param host: The Graylog server's address.
        :param port: The Graylog server's GELF UDP input port.
        :param source: The "host" field GELF records are tagged with, identifying which machine/process sent them. The default value is None, so the local machine's hostname is used.
        """
        super().__init__()
        self._address = (host, port)
        self._source: str = source or socket.gethostname()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = json.dumps(self._build_payload(record)).encode("utf-8")
            self._socket.sendto(payload, self._address)
        except Exception:
            self.handleError(record)

    def _build_payload(self, record: logging.LogRecord) -> dict:
        payload = {
            "version": "1.1",
            "host": self._source,
            "short_message": record.getMessage(),
            "timestamp": record.created,
            "level": _SYSLOG_SEVERITY.get(record.levelno, 7),
            "_logger": record.name,
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRIBUTES and not key.startswith("_"):
                payload[f"_{key}"] = value

        return payload

    def close(self) -> None:
        self._socket.close()
        super().close()
