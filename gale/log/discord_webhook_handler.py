"""
This file contains the implementation of the class DiscordWebhookHandler.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import logging
import urllib.request
from typing import Optional

# Discord rejects any message body over 2000 characters.
_MAX_CONTENT_LENGTH = 2000


class DiscordWebhookHandler(logging.Handler):
    """
    Posts every log record to a Discord channel through an incoming
    webhook — a common, zero-infrastructure way for a small/solo team
    to get pinged about errors and warnings without standing up a full
    log aggregation stack. Uses only the standard library.

    Since pinging a channel for every single INFO line would be noisy,
    this is typically attached with a raised level, e.g. only
    WARNING/ERROR and above:

    Usage example:

        from gale.log import add_handler
        from gale.log.level import LogLevel
        from gale.log.discord_webhook_handler import DiscordWebhookHandler

        handler = DiscordWebhookHandler(
            "https://discord.com/api/webhooks/<id>/<token>", username="space_trip"
        )
        handler.setLevel(LogLevel.WARNING)
        add_handler(handler)
    """

    def __init__(
        self,
        webhook_url: str,
        username: Optional[str] = None,
        timeout: float = 2.0,
    ) -> None:
        """
        :param webhook_url: A Discord incoming webhook URL, as created in a channel's Integrations settings.
        :param username: Overrides the webhook's default display name for these messages. The default value is None (use the webhook's configured name).
        :param timeout: How long, in seconds, to wait for Discord's response before giving up on a record. The default value is 2.0.
        """
        super().__init__()
        self._webhook_url = webhook_url
        self._username = username
        self._timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            content = self.format(record) if self.formatter else record.getMessage()
            body = {"content": content[:_MAX_CONTENT_LENGTH]}

            if self._username is not None:
                body["username"] = self._username

            payload = json.dumps(body).encode("utf-8")
            request = urllib.request.Request(
                self._webhook_url,
                data=payload,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(request, timeout=self._timeout)
        except Exception:
            self.handleError(record)
