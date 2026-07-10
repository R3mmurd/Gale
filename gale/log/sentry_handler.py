"""
This file contains the implementation of the class SentryHandler: a
logging.Handler that sends each log record to Sentry as an event
through its HTTP Store API, using only the standard library.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import logging
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

_SENTRY_LEVELS = {
    logging.CRITICAL: "fatal",
    logging.ERROR: "error",
    logging.WARNING: "warning",
    logging.INFO: "info",
    logging.DEBUG: "debug",
}


class SentryHandler(logging.Handler):
    """
    Sends every log record to Sentry (sentry.io or a self-hosted
    instance) as an event through its HTTP Store API, using only the
    standard library — no sentry-sdk dependency. It's a lightweight
    "at least get pinged about errors" integration; for full Sentry
    features (breadcrumbs, releases, performance tracing, offline
    queuing/retry...) use sentry-sdk directly instead.

    Usage example:

        from gale.log import add_handler
        from gale.log.sentry_handler import SentryHandler

        add_handler(SentryHandler("https://<public_key>@<host>/<project_id>"))
    """

    def __init__(self, dsn: str, timeout: float = 2.0) -> None:
        """
        :param dsn: A Sentry DSN, as shown in a project's "Client Keys" settings ("https://<public_key>@<host>/<project_id>").
        :param timeout: How long, in seconds, to wait for Sentry's response before giving up on a record. The default value is 2.0.
        """
        super().__init__()
        parsed = urllib.parse.urlparse(dsn)
        self._public_key = parsed.username
        project_id = parsed.path.strip("/")
        netloc = parsed.hostname or ""

        if parsed.port:
            netloc += f":{parsed.port}"

        self._url = f"{parsed.scheme}://{netloc}/api/{project_id}/store/"
        self._timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = json.dumps(self._build_event(record)).encode("utf-8")
            request = urllib.request.Request(
                self._url,
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-Sentry-Auth": (
                        "Sentry sentry_version=7, "
                        f"sentry_key={self._public_key}, "
                        "sentry_client=gale-log/1.0"
                    ),
                },
            )
            urllib.request.urlopen(request, timeout=self._timeout)
        except Exception:
            self.handleError(record)

    def _build_event(self, record: logging.LogRecord) -> dict:
        return {
            "event_id": uuid.uuid4().hex,
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "logger": record.name,
            "level": _SENTRY_LEVELS.get(record.levelno, "info"),
            "platform": "python",
            "message": record.getMessage(),
        }
