"""Telegram notification provider."""

import logging
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json

from .base import Notifier

logger = logging.getLogger(__name__)

# Telegram message limit
MAX_MESSAGE_LENGTH = 4096


class TelegramNotifier(Notifier):
    """Send notifications via Telegram Bot API.

    Args:
        bot_token: Telegram bot token from @BotFather.
        chat_id: Target chat/channel ID.
    """

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str, title: str = "") -> bool:
        """Send a single message via Telegram."""
        text = f"*{title}*\n\n{message}" if title else message
        text = text[:MAX_MESSAGE_LENGTH]
        return self._send_message(text)

    def send_long(self, message: str, title: str = "") -> bool:
        """Send a long message, splitting into chunks at line boundaries."""
        full_text = f"*{title}*\n\n{message}" if title else message
        chunks = self._split_message(full_text)

        success = True
        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                header = f"[{i + 1}/{len(chunks)}]\n"
                chunk = header + chunk
            if not self._send_message(chunk):
                success = False
        return success

    def _send_message(self, text: str) -> bool:
        """Send a single message via the Telegram Bot API."""
        url = f"{self._base_url}/sendMessage"
        payload = json.dumps({
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }).encode("utf-8")

        req = Request(url, data=payload, headers={"Content-Type": "application/json"})

        try:
            with urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                if result.get("ok"):
                    return True
                logger.error("Telegram API error: %s", result)
                return False
        except Exception:
            logger.exception("Failed to send Telegram message")
            return False

    @staticmethod
    def _split_message(text: str, max_len: int = MAX_MESSAGE_LENGTH - 20) -> list[str]:
        """Split a long message at line boundaries."""
        if len(text) <= max_len:
            return [text]

        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break

            # Find the last newline within the limit
            split_at = text.rfind("\n", 0, max_len)
            if split_at <= 0:
                split_at = max_len

            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")

        return chunks
