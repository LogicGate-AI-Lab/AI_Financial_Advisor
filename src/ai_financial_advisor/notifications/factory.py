"""Factory for creating notification providers."""

from .base import Notifier
from .telegram import TelegramNotifier


def create_notifier(provider: str, **kwargs: str) -> Notifier:
    """Create a notifier instance by provider name.

    Args:
        provider: Provider name ("telegram").
        **kwargs: Provider-specific configuration.

    Returns:
        A configured Notifier instance.

    Raises:
        ValueError: If the provider is unknown.
    """
    if provider == "telegram":
        bot_token = kwargs.get("bot_token", "")
        chat_id = kwargs.get("chat_id", "")
        if not bot_token or not chat_id:
            raise ValueError("Telegram requires 'bot_token' and 'chat_id'")
        return TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

    raise ValueError(f"Unknown notification provider: {provider}")
